"""Measure the fixed per-call context cost of each coding-agent CLI.

``agent-os orchestrate overhead`` sends the same trivial prompt ("reply OK,
use no tools") through the real adapter once per option variant, in two
different throwaway worktrees of the target repository. With a one-word
answer and no tool use, the provider-reported input tokens are almost
entirely what the CLI sends on its own with every call: system prompt, tool
definitions, skill/plugin listings, instruction files. The second worktree
shows whether that prefix is served from the prompt cache or written again.

Every number is the provider's exact report; nothing is estimated. Each probe
is a real (small) model call, so this command spends usage.
"""

from __future__ import annotations

import json
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .adapters import AgentLaunchRequest, get_adapter
from .router import ProviderRegistry
from .store import orchestrator_home
from .worktrees import git, repository_root

PROBE_PROMPT = "Reply with exactly the word OK and nothing else. Do not read files and do not use any tools.\n"

VARIANTS: dict[str, list[tuple[str, dict[str, Any]]]] = {
    "claude_code": [
        ("current", {"lean_tools": False, "disable_skills": False, "shared_prompt_cache": False, "setting_sources": None}),
        ("lean_tools", {"lean_tools": True, "disable_skills": False, "shared_prompt_cache": False, "setting_sources": None}),
        ("no_skills", {"lean_tools": False, "disable_skills": True, "shared_prompt_cache": False, "setting_sources": None}),
        ("shared_cache", {"lean_tools": False, "disable_skills": False, "shared_prompt_cache": True, "setting_sources": None}),
        ("project_settings_only", {"lean_tools": False, "disable_skills": False, "shared_prompt_cache": False, "setting_sources": "project,local"}),
        ("all_lean", {"lean_tools": True, "disable_skills": True, "shared_prompt_cache": True, "setting_sources": "project,local"}),
    ],
    "codex_cli": [
        ("current", {"use_user_config": True, "disable_features": []}),
        ("ignore_user_config", {"use_user_config": False, "disable_features": []}),
    ],
}


def _worktrees(repo: Path, root: Path, count: int) -> list[Path]:
    paths = []
    for index in range(count):
        path = root / f"wt{index}"
        git(["worktree", "add", "--detach", str(path), "HEAD"], repo)
        paths.append(path)
    return paths


def _probe(provider: dict[str, Any], options: dict[str, Any], cwd: Path, out: Path, capability_class: str, timeout: float) -> dict[str, Any]:
    entry = {**provider, "options": {**(provider.get("options") or {}), **options}}
    adapter = get_adapter(entry)
    out.mkdir(parents=True, exist_ok=True)
    prompt = out / "prompt.md"
    prompt.write_text(PROBE_PROMPT, encoding="utf-8")
    model = (provider.get("models") or {}).get(capability_class)
    request = AgentLaunchRequest(
        run_id="overhead", node_id=out.name, role="implementer", cwd=str(cwd), prompt_path=str(prompt),
        output_dir=str(out), capability_class=capability_class, effort="low", model=model,
        provider_effort=(provider.get("effort_map") or {}).get("low", "low"), read_only=False, timeout_seconds=int(timeout),
    )
    plan = adapter.resolve_invocation(request)
    started = time.monotonic()
    handle = adapter.start(request)
    while adapter.poll(handle).running:
        if time.monotonic() - started > timeout:
            adapter.cancel(handle)
            break
        time.sleep(0.5)
    result = adapter.collect(handle)
    return {
        "outcome": result.outcome,
        "failure_kind": result.failure_kind,
        "answer": (result.summary or "")[-80:],
        "seconds": round(time.monotonic() - started, 1),
        "usage": result.usage,
        "flags": [item for item in plan.argv if item.startswith("--") or item.startswith("-c")] + [item for item in plan.argv if item.startswith("mcp_") or "," in item],
    }


def measure(
    providers: list[str] | None = None,
    *,
    repository: str | Path = ".",
    capability_class: str = "fast",
    variants: list[str] | None = None,
    registry: ProviderRegistry | None = None,
    timeout: float = 300,
) -> dict[str, Any]:
    registry = registry or ProviderRegistry()
    repo = repository_root(Path(repository))
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    root = orchestrator_home() / "overhead" / f"{stamp}-{uuid.uuid4().hex[:4]}"
    root.mkdir(parents=True, exist_ok=True)
    trees = _worktrees(repo, root, 2)
    report: dict[str, Any] = {"created_at": stamp, "repository": str(repo), "capability_class": capability_class, "prompt": PROBE_PROMPT.strip(), "providers": {}}
    try:
        for provider in registry.providers:
            if providers and provider["id"] not in providers:
                continue
            if not provider.get("enabled", True):
                continue
            rows = []
            for name, options in VARIANTS.get(provider.get("adapter"), []):
                if variants and name not in variants:
                    continue
                calls = [_probe(provider, options, tree, root / "calls" / f"{provider['id']}-{name}-{index}", capability_class, timeout) for index, tree in enumerate(trees)]
                rows.append({"variant": name, "options": options, "calls": calls, "summary": _summary(calls)})
            report["providers"][provider["id"]] = {"model": (provider.get("models") or {}).get(capability_class), "variants": rows}
    finally:
        for tree in trees:
            git(["worktree", "remove", "--force", str(tree)], repo, check=False)
    path = root / "overhead.json"
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    report["file"] = str(path)
    return report


def _summary(calls: list[dict[str, Any]]) -> dict[str, Any]:
    usable = [call["usage"] for call in calls if call["outcome"] == "completed" and (call["usage"] or {}).get("accuracy") == "exact"]
    if not usable:
        return {"ok": False, "reason": "; ".join(f"{call['failure_kind']}: {call['answer']}" for call in calls)[:300]}
    return {
        "ok": len(usable) == len(calls),
        "input_tokens_per_call": [item["input_tokens"] for item in usable],
        "cache_write_tokens_per_call": [item.get("cache_write_tokens") for item in usable],
        "uncached_input_tokens_per_call": [item.get("uncached_input_tokens") for item in usable],
        "output_tokens_per_call": [item.get("output_tokens") for item in usable],
        "cost_usd_per_call": [item.get("cost_usd") for item in usable],
    }


# ---------------------------------------------------------------------------
# Planner exploration (P2.3)
# ---------------------------------------------------------------------------

# (name, run policy overrides, adapter option overrides)
PLANNER_VARIANTS: list[tuple[str, dict[str, Any], dict[str, Any]]] = [
    ("current", {"planner_repo_map": False, "planner_effort": "high"}, {"read_only_mode": "plan"}),
    ("read_only_tools", {"planner_repo_map": False, "planner_effort": "high"}, {"read_only_mode": "tools"}),
    ("map_and_budget", {"planner_repo_map": True, "planner_effort": "high"}, {"read_only_mode": "tools"}),
    ("map_budget_medium", {"planner_repo_map": True, "planner_effort": "medium"}, {"read_only_mode": "tools"}),
    ("tools_medium", {"planner_repo_map": False, "planner_effort": "medium"}, {"read_only_mode": "tools"}),
]


def measure_planner(
    repository: str | Path = ".",
    project: str | None = None,
    *,
    goal: str | None = None,
    provider: str = "claude-code",
    variants: list[str] | None = None,
    timeout: float = 1800,
) -> dict[str, Any]:
    """Run only the planner of a real orchestrated run, once per variant, and
    report exact usage plus objective plan-quality checks. Real model calls."""
    from ..telemetry import LocalTelemetryStore
    from . import roadmap
    from .engine import Orchestrator
    from .store import RunStore

    repo = repository_root(Path(repository))
    base = ProviderRegistry()
    entry = base.get(provider)
    if entry is None:
        raise ValueError(f"provider {provider} is not configured")
    if goal is None:
        scanned = roadmap.scan(project, repo)
        stage, _ = roadmap.choose_stage(scanned["stages"], roadmap.stage_branches(repo, scanned["stages"]))
        if stage is None:
            raise ValueError("no eligible roadmap stage to plan")
        goal = roadmap.build_goal(project, stage, scanned["relative_path"], roadmap._latest_handoff(project))
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    root = orchestrator_home() / "planner-bench" / f"{stamp}-{uuid.uuid4().hex[:4]}"
    root.mkdir(parents=True, exist_ok=True)
    tracked = set(git(["ls-files"], repo).stdout.splitlines())
    rows = []
    for name, policy, options in PLANNER_VARIANTS:
        if variants and name not in variants:
            continue
        providers = [dict(item, options={**(item.get("options") or {}), **options}) if item["id"] == provider else item for item in base.providers]
        engine = Orchestrator(
            RunStore(root / "state" / name),
            registry=ProviderRegistry(providers=providers, discover=False),
            telemetry_store=LocalTelemetryStore(root / "telemetry.jsonl"),
            claims_path=root / "claims.json",
        )
        run_policy = {"planning": "auto", "auto_continue": False, "announce_claims": False, "final_integration": "branch", "poll_interval_seconds": 2.0, **policy}
        summary = engine.create_run(goal, repository=repo, project=project, policy=run_policy, overrides={"roles": {"planner": {"provider": provider}}})
        run_id = summary["run_id"]
        started = time.monotonic()
        try:
            engine.run_loop(run_id, max_seconds=timeout)
        finally:
            record = engine.load(run_id)
            _cleanup(engine, record)
        rows.append({"variant": name, "policy": policy, "options": options, "seconds": round(time.monotonic() - started, 1), **_plan_quality(record, tracked), "all_planner_calls": _planner_calls(engine, run_id), "files": {"telemetry": str(engine.ledger.paths(run_id)[0]), "prompt": str(engine.store.run_dir(run_id) / "workers" / "plan-1" / "prompt.md")}})
    report = {"created_at": stamp, "repository": str(repo), "provider": provider, "goal_chars": len(goal), "goal_first_line": goal.splitlines()[0], "variants": rows}
    path = root / "planner.json"
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    report["file"] = str(path)
    return report


def _plan_quality(record: dict[str, Any], tracked: set[str]) -> dict[str, Any]:
    planner = record["nodes"].get("plan") or {}
    result = planner.get("result") or {}
    tasks = [node for node in record["nodes"].values() if node["role"] in {"implementer", "test_author"}]
    scoped = [path for node in tasks for path in node["scope"]]
    existing = [path for path in scoped if path in tracked or any(item.startswith(path.rstrip("/") + "/") for item in tracked)]
    return {
        "planner_state": planner.get("state"),
        "planner_failure": (planner.get("failures") or [{}])[-1].get("detail") if planner.get("state") != "PASSED" else None,
        "model": (planner.get("selection") or {}).get("model"),
        "effort": (planner.get("selection") or {}).get("provider_effort"),
        "usage": result.get("usage"),
        "tasks": len(tasks),
        "task_classes": {cls: sum(1 for node in tasks if node["capability_class"] == cls) for cls in {node["capability_class"] for node in tasks}},
        "scope_paths": len(scoped),
        "scope_paths_existing": len(existing),
        "tasks_with_targeted_test": sum(1 for node in tasks if any(item.get("kind") == "command" and "project-validation" not in str(item.get("name")) for item in node["validators"])),
        "summary": (result.get("summary") or "")[-500:],
        "plan": [{"id": node["id"], "goal": node["goal"][:300], "scope": node["scope"], "class": node["capability_class"]} for node in tasks],
    }


def _planner_calls(engine: Any, run_id: str) -> dict[str, Any]:
    """Every planner call of the run from its telemetry, retries and
    fallbacks included (the node keeps only its last result)."""
    calls = [event["data"] for event in engine.ledger.read(run_id)[0] if event["type"] in {"model_completed", "model_failed"} and event["node"] == "plan"]
    exact = [call["usage"] for call in calls if (call.get("usage") or {}).get("accuracy") == "exact"]
    return {
        "calls": len(calls),
        "providers": [call.get("provider") for call in calls],
        "input_tokens": sum(item.get("input_tokens") or 0 for item in exact),
        "output_tokens": sum(item.get("output_tokens") or 0 for item in exact),
        "claude_cost_usd": round(sum(item.get("cost_usd") or 0 for item in exact), 6),
        "calls_without_report": len(calls) - len(exact),
    }


def _cleanup(engine: Any, record: dict[str, Any]) -> None:
    """Remove the run's integration worktree and branch; planning edits nothing."""
    try:
        engine.stop(record["run_id"])
    except Exception:
        pass
    manager = engine._manager(record)
    integration = record.get("integration") or {}
    if integration.get("path"):
        manager.remove(integration["path"], None)
    if integration.get("branch"):
        git(["branch", "-D", integration["branch"]], record["repository"], check=False)
