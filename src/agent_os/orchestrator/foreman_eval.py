"""Foreman judgement and efficiency eval: does the planner pick the right model per task?

The foreman's routing judgement is the ``capability_class`` (and ``effort``)
it assigns each planned task; the router maps the class to a concrete model
(``fast`` -> the cheapest registered model ... ``reasoning`` -> the strongest
the planner may choose). This eval sends the foreman the **exact** prompt the
engine sends a planner (prompts.build_measured + the local repository map +
the tool-less note) for a fixed set of labeled goals, then scores each answer
deterministically:

* **valid** -- planner.expand accepts the plan (ids, scopes, DAG, commands);
* **over** -- tasks given a stronger class than the case's ``ceiling``
  (wasted spend: a cheaper model would have done it);
* **under** -- the case needs at least one task at ``floor_any`` (design,
  concurrency, security) and none got it (likely failure and escalation);
* **task count** within the case's range;
* **efficiency** -- input/output tokens, seconds, and the plan's routing cost
  relative to the cheapest plan with the same task count that satisfies the
  labels (``cost_ratio`` 1.0 = as cheap as the labels allow).

A case passes when the plan is valid, has no over- or under-provisioning and
its task count is in range. Scoring is pure; only ``run`` calls a model.
Labels follow the planner rules in prompts.py (fast for mechanical fully
specified work, balanced for multi-file features or investigation, reasoning
only for design, concurrency, security or cross-cutting refactors).
"""

from __future__ import annotations

import copy
import json
import statistics
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from ..capabilities import rank
from . import planner, prompts
from .model import PlanError, merge_policy

# Relative routing cost per class (the registry's codex ratios; only ratios matter).
CLASS_COST = {"deterministic": 0.0, "fast": 1.0, "balanced": 2.9, "reasoning": 6.5, "frontier": 10.0}
# Every model task also pays the agent's fixed context overhead (~15k input
# tokens per coding-CLI call, docs/simple-mode.md): about half a fast task.
TASK_OVERHEAD = 0.5

CASES: list[dict[str, Any]] = [
    {"id": "docs-typo", "goal": "Fix the misspelling 'recieve' -> 'receive' everywhere it appears in docs/simple-mode.md. Nothing else changes.",
     "ceiling": "fast", "floor_any": None, "tasks": [1, 1]},
    {"id": "cli-flag", "goal": "Add a --json flag to `agent-os orchestrate foreman status` in src/agent_os/orchestrator/cli.py that prints compact one-line JSON instead of the indented default, with a unit test in tests/test_foreman_deploy.py.",
     "ceiling": "fast", "floor_any": None, "tasks": [1, 2]},
    {"id": "tests-existing", "goal": "Write unit tests in tests/test_foreman_deploy.py for the existing parse_hf_link function in src/agent_os/orchestrator/foreman_deploy.py: hf.co links, /tree/<revision> links, bare org/name ids and rejected dataset links. Do not change the function.",
     "ceiling": "fast", "floor_any": None, "tasks": [1, 2]},
    {"id": "multi-file-feature", "goal": "Show each run's total dollar spend in the GUI run panel: add the figure to the run summary returned by the orchestrator engine's summary(), render it in gui/simple.js next to the progress line, and cover it with a unit test.",
     "ceiling": "balanced", "floor_any": None, "tasks": [1, 4]},
    {"id": "flaky-investigation", "goal": "tests/test_orchestrator.py intermittently fails on Windows with PermissionError while removing worktrees. Find the root cause in the worktree cleanup code and fix it so the test is reliable.",
     "ceiling": "reasoning", "floor_any": "balanced", "tasks": [1, 3]},
    {"id": "concurrency-design", "goal": "Design and implement cross-process locking so two orchestrator driver processes can never drive the same run at once, including safe recovery when a driver crashes and leaves a stale lock.",
     "ceiling": "reasoning", "floor_any": "reasoning", "tasks": [2, 6]},
    {"id": "security-audit", "goal": "Guarantee that secret values resolved from secrets:// references can never be written to run records, event logs or telemetry: audit every write path, add a central redaction guard, and add tests that fail if a secret leaks.",
     "ceiling": "reasoning", "floor_any": "reasoning", "tasks": [2, 6]},
]

# Held out: written before any guard or playbook was tuned, and never used to
# tune them. Improvements must show here too, or they are overfitting the
# dev cases above. Run with ``--split holdout``.
HOLDOUT: list[dict[str, Any]] = [
    {"id": "ho-version-bump", "split": "holdout", "goal": "Change the version in pyproject.toml from 0.3.0 to 0.4.0 and add a matching 0.4.0 heading to CHANGELOG.md. Nothing else changes.",
     "ceiling": "fast", "floor_any": None, "tasks": [1, 1]},
    {"id": "ho-list-limit", "split": "holdout", "goal": "Add a --limit N option to `agent-os orchestrate list` in src/agent_os/orchestrator/cli.py that shows at most N runs (newest first), with a unit test.",
     "ceiling": "fast", "floor_any": None, "tasks": [1, 2]},
    {"id": "ho-blocked-badge", "split": "holdout", "goal": "In the GUI run panel (gui/simple.js, gui/simple-core.js) show a warning badge with the wait reason when a run is BLOCKED, and cover the badge text with a test in tests/gui/simple_core.test.js.",
     "ceiling": "balanced", "floor_any": None, "tasks": [1, 3]},
    {"id": "ho-double-release", "split": "holdout", "goal": "budget.spent() can go wrong when a reservation is released twice. Find out exactly how in src/agent_os/orchestrator/budget.py and fix it so spend is never under-counted, with a regression test.",
     "ceiling": "reasoning", "floor_any": "balanced", "tasks": [1, 2]},
    {"id": "ho-rate-limit", "split": "holdout", "goal": "Design and implement request rate limiting for the control GUI API in src/agent_os/orchestrator/server.py so a runaway browser tab cannot flood the orchestrator, including how the token bucket is shared safely across the server's threads.",
     "ceiling": "reasoning", "floor_any": "reasoning", "tasks": [2, 5]},
    {"id": "ho-secret-retention", "split": "holdout", "goal": "Harden src/agent_os/orchestrator/secret_refs.py so resolved secret values are never kept in module state or caches, document the threat model, and add tests that fail if a value is retained.",
     "ceiling": "reasoning", "floor_any": "reasoning", "tasks": [2, 5]},
]

NO_TOOLS_NOTE = ("\n\nYou have no file or shell tools in this call: plan from the goal and the repository map above, "
                 "and name only files the map lists. Answer with the fenced result block only.\n")


def build_prompt(goal: str, repo: Path, *, project: str | None = None, run_id: str = "foreman-eval") -> tuple[str, dict[str, Any], dict[str, Any]]:
    """The planner prompt the engine would send for ``goal`` (map included)."""
    from .repomap import build as build_map

    policy = merge_policy({"planning": "auto"})
    nodes = planner.planner_plan(goal, policy["planner_capability_class"], policy["planner_effort"])
    record = {"run_id": run_id, "goal": goal, "project": project, "policy": policy, "nodes": nodes, "order": list(nodes)}
    repo_map = build_map(repo, goal)["text"] if policy.get("planner_repo_map") else None
    prompt, _ = prompts.build_measured(record, nodes[planner.PLANNER_ID], repo_map=repo_map, cwd=str(repo))
    return prompt + NO_TOOLS_NOTE, record, policy


def _ideal_cost(case: dict[str, Any], count: int) -> float:
    """Cheapest routing for ``count`` tasks that still satisfies the labels."""
    count = max(min(count, case["tasks"][1]), case["tasks"][0])  # splitting beyond the labelled range is not "ideal"
    floor = case.get("floor_any")
    classes = CLASS_COST[floor] + CLASS_COST["fast"] * (count - 1) if floor else CLASS_COST["fast"] * count
    return classes + TASK_OVERHEAD * count


def score(case: dict[str, Any], structured: dict[str, Any] | None, record: dict[str, Any], policy: dict[str, Any]) -> dict[str, Any]:
    """Deterministic verdict for one foreman answer."""
    row: dict[str, Any] = {"case": case["id"], "valid": False, "passed": False}
    nodes = copy.deepcopy(record["nodes"])
    try:
        added, notes = planner.expand(nodes, planner.PLANNER_ID, structured, policy["max_planned_tasks"],
                                      approved_commands=list(policy.get("approved_commands") or []), project_commands=[])
    except (PlanError, TypeError, ValueError, KeyError) as exc:
        row["error"] = f"{type(exc).__name__}: {str(exc)[:200]}"
        return row
    tasks = [nodes[node_id] for node_id in added]
    classes = [task["capability_class"] for task in tasks]
    ceiling, floor = case["ceiling"], case.get("floor_any")
    over = [task["id"] for task in tasks if task["capability_class"] != "deterministic" and rank(task["capability_class"]) > rank(ceiling)]
    under = bool(floor) and not any(cls != "deterministic" and rank(cls) >= rank(floor) for cls in classes)
    low, high = case["tasks"]
    cost = sum(CLASS_COST.get(cls, 0.0) + (TASK_OVERHEAD if cls != "deterministic" else 0.0) for cls in classes)
    ideal = _ideal_cost(case, len(tasks))
    row.update(
        valid=True, notes=notes, tasks=len(tasks), classes=classes, efforts=[task["effort"] for task in tasks],
        over=over, under=under, count_ok=low <= len(tasks) <= high,
        routing_cost=round(cost, 2), ideal_cost=round(ideal, 2), cost_ratio=round(cost / ideal, 2) if ideal else None,
        plan=[{"id": task["id"], "class": task["capability_class"], "effort": task["effort"], "scope": task["scope"], "goal": task["goal"][:160]} for task in tasks],
    )
    row["passed"] = not over and not under and row["count_ok"]
    return row


def summarize(rows: list[dict[str, Any]], hourly_usd: float | None = None) -> dict[str, Any]:
    n = len(rows) or 1
    # after the deterministic strategy; a case the guard left alone keeps its raw result
    guarded = [row.get("guarded") or row for row in rows]
    seconds = [row["seconds"] for row in rows if row.get("seconds") is not None]
    tokens_in = [row["usage"].get("input_tokens") or 0 for row in rows if row.get("usage")]
    tokens_out = [row["usage"].get("output_tokens") or 0 for row in rows if row.get("usage")]
    ratios = [row["cost_ratio"] for row in rows if row.get("cost_ratio")]
    total_seconds = sum(seconds)
    return {
        "cases": len(rows),
        "judgement_accuracy": round(sum(1 for row in rows if row.get("passed")) / n, 3),
        "guarded_accuracy": round(sum(1 for row in guarded if row.get("passed")) / n, 3) if rows else None,
        "guarded_median_cost_ratio": round(statistics.median([row["cost_ratio"] for row in guarded if row.get("cost_ratio")]), 2) if guarded else None,
        "valid_plans": round(sum(1 for row in rows if row.get("valid")) / n, 3),
        "over_provisioned_tasks": sum(len(row.get("over") or []) for row in rows),
        "under_provisioned_cases": sum(1 for row in rows if row.get("under")),
        "task_count_ok": round(sum(1 for row in rows if row.get("count_ok")) / n, 3),
        "median_cost_ratio": round(statistics.median(ratios), 2) if ratios else None,
        "median_seconds": round(statistics.median(seconds), 1) if seconds else None,
        "mean_input_tokens": round(statistics.mean(tokens_in)) if tokens_in else None,
        "mean_output_tokens": round(statistics.mean(tokens_out)) if tokens_out else None,
        "gpu_usd_for_calls": round(hourly_usd * total_seconds / 3600, 4) if hourly_usd else None,
        "failed_cases": [row["case"] for row in rows if not row.get("passed")],
    }


def adapter_runner(provider_id: str, *, timeout: int = 900) -> Callable[[str, Path], dict[str, Any]]:
    """Call the provider exactly as the engine launches a planner."""
    from .adapters import ADAPTERS
    from .adapters.base import AgentLaunchRequest
    from .router import ProviderRegistry

    from .router import select

    registry = ProviderRegistry()
    entry = registry.get(provider_id)
    if entry is None:
        raise ValueError(f"provider {provider_id} is not registered")
    adapter = ADAPTERS[entry["adapter"]](entry)
    # the model and effort the engine would give a planner on this provider
    choice = select(registry, capability_class="reasoning", effort="medium", role="planner", override={"provider": provider_id})
    if not choice.get("resolved"):
        raise ValueError(f"{provider_id} cannot serve a planner: {choice.get('reason')}")
    model, provider_effort = choice["model"], choice.get("provider_effort")

    def run(prompt: str, workdir: Path) -> dict[str, Any]:
        workdir.mkdir(parents=True, exist_ok=True)
        (workdir / "prompt.md").write_text(prompt, encoding="utf-8")
        request = AgentLaunchRequest(run_id="foreman-eval", node_id="plan", role="planner", cwd=str(workdir), prompt_path=str(workdir / "prompt.md"),
                                     output_dir=str(workdir), capability_class=choice["capability_class"], effort="medium", model=model, provider_effort=provider_effort,
                                     read_only=True, timeout_seconds=timeout)
        started = time.monotonic()
        handle = adapter.start(request)
        while adapter.poll(handle).running:
            if time.monotonic() - started > timeout:
                adapter.cancel(handle)
                return {"outcome": "failed", "detail": "timeout", "seconds": round(time.monotonic() - started, 1), "usage": {}, "structured": None}
            time.sleep(0.5)
        result = adapter.collect(handle)
        if result.failure_kind == "invalid_model" and registry.path != "<inline>":
            from .provider_health import record_unavailable_model

            record_unavailable_model(Path(registry.path).parent, provider_id, model, result.detail or "invalid_model")
        return {"outcome": result.outcome, "failure_kind": result.failure_kind, "model": model, "detail": result.detail, "structured": result.structured, "usage": result.usage or {},
                "seconds": round(time.monotonic() - started, 1)}

    return run


def run(provider_id: str | None = None, *, repo: Path | None = None, cases: list[str] | None = None, runner=None,
        hourly_usd: float | None = None, out_dir: Path | None = None, strategy_override: dict[str, Any] | None = None,
        split: str = "dev") -> dict[str, Any]:
    """Evaluate the foreman (default: the live session foreman) on every case."""
    from ..paths import ROOT
    from .store import orchestrator_home

    if provider_id is None and runner is None:
        from .foreman_deploy import load_state

        state = load_state()
        if state.get("status") != "ready":
            raise ValueError("no session foreman is ready; deploy one or pass a provider id")
        provider_id, hourly_usd = state["provider_id"], hourly_usd or state.get("hourly_usd")
    repo = Path(repo or ROOT)
    runner = runner or adapter_runner(str(provider_id))
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    root = Path(out_dir or orchestrator_home() / "foreman-eval") / f"{stamp}-{uuid.uuid4().hex[:4]}"
    from .foreman_strategy import apply as apply_strategy

    from .foreman_strategy import strategy_for

    rows = []
    strategy = strategy_override  # None: the evaluated model's own strategy, once its model is known
    model_used = None
    pool = {"dev": CASES, "holdout": HOLDOUT, "all": CASES + HOLDOUT}[split]
    for case in pool:
        if cases and case["id"] not in cases:
            continue
        prompt, record, policy = build_prompt(case["goal"], repo)
        answer = runner(prompt, root / case["id"])
        model_used = model_used or answer.get("model") or (answer.get("usage") or {}).get("model_resolved")
        if strategy is None and model_used:
            from .router import ProviderRegistry

            strategy = strategy_for(model_used, provider=ProviderRegistry().get(str(provider_id)) if provider_id else None)
        if answer.get("failure_kind") in {"invalid_model", "quota", "auth"}:
            # every later case would fail the same way: stop and say why
            rows.append({"case": case["id"], "valid": False, "passed": False, "error": f"{answer['failure_kind']}: {str(answer.get('detail'))[:200]}"})
            break
        if answer.get("outcome") == "completed":
            row = score(case, answer.get("structured"), record, policy)
            fixed, notes = apply_strategy(case["goal"], answer.get("structured"), strategy)
            if notes:  # what the engine would actually run after the deterministic guard
                row["guarded"] = {**{key: value for key, value in score(case, fixed, record, policy).items() if key != "plan"}, "notes": notes}
        else:
            row = {"case": case["id"], "valid": False, "passed": False, "error": answer.get("detail") or "call failed"}
        row.update(seconds=answer.get("seconds"), usage={key: answer.get("usage", {}).get(key) for key in ("input_tokens", "output_tokens", "model_resolved")},
                   prompt_chars=len(prompt))
        rows.append(row)
    aborted = len(rows) < len([case for case in pool if not cases or case["id"] in cases])
    report = {"created_at": stamp, "provider": provider_id, "model": model_used, "split": split,
              "strategy": {key: (strategy or {}).get(key) for key in ("band", "source", "guard")}, "aborted": rows[-1]["error"] if aborted and rows else None, "repository": str(repo), "summary": summarize(rows, hourly_usd), "cases": rows}
    root.mkdir(parents=True, exist_ok=True)
    (root / "report.json").write_text(json.dumps(report, indent=1), encoding="utf-8")
    report["file"] = str(root / "report.json")
    return report
