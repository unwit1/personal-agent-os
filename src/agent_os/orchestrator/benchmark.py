"""Repeatable token-efficiency benchmark: ``agent-os orchestrate benchmark``.

Each scenario runs the *real* orchestration path -- engine, router, Git
worktrees, validators, review, integration, telemetry -- against a throwaway
fixture repository. Offline (the default), model workers are scripted
synthetic workers: they cost nothing and report **no** token usage, so the
benchmark never presents invented token counts. What it measures offline:

* model calls, by tier and role, and calls avoided;
* local/deterministic operations, cache hits, escalations, retries;
* prompt size Orchestrator wrote (exact characters, tokens estimated);
* candidate vs selected context (characters, tokens estimated);
* runtime and pass/fail.

``--live`` runs the small-code-change scenario with the machine's real
providers instead, and then token counts are the providers' exact numbers.

The baseline is a *modeled estimate*, labelled as such: a naive strategy that
sends the whole candidate context with every model call, runs every call on
the highest configured tier, answers repository questions with a model, and
re-runs identical tests. Its numbers are derived from measured sizes; they
are never presented as a measured run.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from ..telemetry import LocalTelemetryStore
from .adapters import synthetic
from .adapters.base import AgentLaunchRequest
from .engine import Orchestrator
from .ledger import summarize
from .router import ProviderRegistry
from .store import RunStore, orchestrator_home
from .usage import ESTIMATE_METHOD, estimate_tokens
from . import roadmap


SCHEMA = "personal-agent/orchestrator-benchmark/v1"
TEST_COMMAND = [sys.executable, "-m", "unittest", "discover", "-s", "tests"]
CLASSES = ("fast", "balanced", "reasoning", "frontier")

ROADMAP = """# Demo Roadmap

## P0 — Basics

### P0.1 — Greeting helper

Status: **complete** (2026-09-01). `app/greet.py` has `greet(name)`.

### P0.2 — Farewell helper

Add `farewell(name)` to `app/greet.py` returning `"Goodbye, <name>!"`, with a
unit test in `tests/test_greet.py`.

### P0.3 — Usage docs

Document both helpers in `docs/usage.md`.

## P1 — Later

### P1.1 — Localisation

Translate greetings. Not started.
"""

GREET = 'def greet(name):\n    return f"Hello, {name}!"\n'
FAREWELL = GREET + '\n\ndef farewell(name):\n    return f"Goodbye, {name}!"\n'
BROKEN_FAREWELL = GREET + '\n\ndef farewell(name):\n    return f"Bye, {name}."\n'
TESTS = (
    "import unittest\n\nfrom app.greet import greet\n\n\n"
    "class GreetTests(unittest.TestCase):\n"
    "    def test_greet(self):\n        self.assertEqual(greet('Ada'), 'Hello, Ada!')\n"
)
FAREWELL_TESTS = TESTS.replace("from app.greet import greet", "from app.greet import farewell, greet") + (
    "\n    def test_farewell(self):\n        self.assertEqual(farewell('Ada'), 'Goodbye, Ada!')\n"
)
# Background documents make the candidate context realistic: a naive agent
# "reads the project"; Orchestrator hands over only the relevant slice.
FILLER = "This design note records background decisions for the demo project. " * 40


def build_fixture(root: Path) -> Path:
    repo = root / "demo-project"
    (repo / "app").mkdir(parents=True)
    (repo / "tests").mkdir()
    (repo / "docs").mkdir()
    (repo / "ROADMAP.md").write_text(ROADMAP, encoding="utf-8")
    (repo / "app" / "__init__.py").write_text("", encoding="utf-8")
    (repo / "app" / "greet.py").write_text(GREET, encoding="utf-8")
    (repo / "tests" / "__init__.py").write_text("", encoding="utf-8")
    (repo / "tests" / "test_greet.py").write_text(TESTS, encoding="utf-8")
    (repo / "docs" / "usage.md").write_text("# Usage\n\nTODO\n", encoding="utf-8")
    for index in range(1, 7):
        (repo / "docs" / f"design-{index}.md").write_text(f"# Design note {index}\n\n{FILLER}\n", encoding="utf-8")
    for args in (["init", "-b", "main"], ["add", "-A"], ["commit", "-m", "fixture"]):
        subprocess.run(["git", "-c", "user.name=benchmark", "-c", "user.email=bench@local", *args], cwd=repo, check=True, capture_output=True)
    return repo


def tracked_text_chars(repo: Path) -> tuple[int, int]:
    """(files, characters) of every tracked text file: the "whole project"."""
    output = subprocess.run(["git", "ls-files"], cwd=repo, capture_output=True, text=True, check=True).stdout.split()
    total = 0
    count = 0
    for name in output:
        path = repo / name
        try:
            total += len(path.read_text(encoding="utf-8"))
            count += 1
        except (OSError, UnicodeDecodeError):
            continue
    return count, total


# ---------------------------------------------------------------------------
# Scripted workers
# ---------------------------------------------------------------------------


def make_script(scenario: str) -> Callable[[AgentLaunchRequest, int], dict[str, Any]]:
    attempts: dict[str, int] = {}

    def script(request: AgentLaunchRequest, call: int) -> dict[str, Any]:
        attempts[request.node_id] = attempts.get(request.node_id, 0) + 1
        attempt = attempts[request.node_id]
        base = {"usage": None}  # synthetic workers report no usage: never invent tokens
        if request.role == "planner":
            tasks = [{
                "id": "farewell", "goal": "Add farewell(name) to app/greet.py with a unit test",
                "scope": ["app/greet.py", "tests/test_greet.py"], "capability_class": "fast", "effort": "low",
                "validators": ["python -m unittest tests.test_greet"],
            }]
            return {**base, "structured": {"status": "done", "summary": "one bounded task", "tasks": tasks}}
        if request.role == "reviewer":
            if scenario == "cross_agent_review" and request.node_id.endswith("review1"):
                finding = {"id": "1", "severity": "medium", "path": "app/greet.py", "summary": "farewell has no docstring", "evidence": "public helper", "recommended_action": "add a one-line docstring"}
                return {**base, "structured": {"status": "done", "verdict": "changes_requested", "findings": [finding]}}
            return {**base, "structured": {"status": "done", "verdict": "approved", "findings": []}}
        if request.role == "repairer":
            fixed = FAREWELL.replace('def farewell(name):\n', 'def farewell(name):\n    """Say goodbye."""\n')
            return {**base, "edits": {"app/greet.py": fixed}, "structured": {"status": "done", "dispositions": [{"id": "R1-1", "disposition": "fixed"}]}}
        if scenario == "documentation_change":
            return {**base, "edits": {"docs/usage.md": "# Usage\n\n`greet(name)` returns a greeting.\n"}, "structured": {"status": "done"}}
        if scenario == "test_failure_repair" and attempt == 1:
            return {**base, "edits": {"app/greet.py": BROKEN_FAREWELL, "tests/test_greet.py": FAREWELL_TESTS}, "structured": {"status": "done"}}
        return {**base, "edits": {"app/greet.py": FAREWELL, "tests/test_greet.py": FAREWELL_TESTS}, "structured": {"status": "done"}}

    return script


def synthetic_registry() -> ProviderRegistry:
    def entry(pid: str) -> dict[str, Any]:
        return {
            "id": pid, "adapter": "synthetic", "options": {"script": "benchmark"},
            "models": {cls: f"{pid}-{cls}" for cls in CLASSES},
            "costs": {"fast": 1, "balanced": 3, "reasoning": 6, "frontier": 10},
            "effort_map": {"none": "low", "low": "low", "medium": "medium", "high": "high"}, "max_concurrency": 3,
        }

    return ProviderRegistry(providers=[entry("synthetic-a"), entry("synthetic-b")])


# ---------------------------------------------------------------------------
# Scenarios
# ---------------------------------------------------------------------------


def _engine(home: Path, registry: ProviderRegistry | None) -> Orchestrator:
    return Orchestrator(
        RunStore(home / "orchestrator"),
        registry=registry,
        telemetry_store=LocalTelemetryStore(home / "telemetry" / "events.jsonl"),
        claims_path=home / "claims.json",
        sleep=lambda seconds: time.sleep(min(seconds, 0.2)),
    )


def _policy(**extra: Any) -> dict[str, Any]:
    return {"auto_continue": True, "poll_interval_seconds": 0.05, "announce_claims": False, **extra}


TEST_VALIDATOR = {"kind": "command", "command": TEST_COMMAND, "name": "unit-tests"}


def scenario_repository_inspection(engine: Orchestrator, repo: Path) -> dict[str, Any]:
    """Question: how many roadmap stages are left? Answered locally."""
    run_id = f"bench-inspect-{int(time.time() * 1000)}"
    scanned = roadmap.scan(None, repo)
    remaining = sum(1 for stage in scanned["stages"] if stage["status"] in roadmap.ELIGIBLE)
    engine.ledger.emit(run_id, "local_execution", what="answered from repository metadata", answer=f"{remaining} stage(s) remaining")
    engine.ledger.emit(run_id, "work_avoided", category="deterministic", model_calls_avoided=1, reason="a repository question answered by the roadmap parser", tokens_avoided_estimate=None)
    return {"run_id": run_id, "passed": remaining == 3, "answer": remaining, "state": "COMPLETE"}


def scenario_roadmap_continuation(engine: Orchestrator, repo: Path) -> dict[str, Any]:
    result = roadmap.continue_roadmap(engine, None, repo, policy=_policy(default_validators=[TEST_VALIDATOR], final_integration="branch"))
    if result["action"] != "started":
        return {"run_id": None, "passed": False, "state": result["action"], "detail": result["message"]}
    final = engine.run_loop(result["run_id"], max_seconds=300)
    return {"run_id": result["run_id"], "passed": result["stage"]["id"] == "P0.2" and _delivered(repo, final, *CHECKS["farewell"]), "state": final["state"], "stage": result["stage"]["id"]}


def _delivered(repo: Path, final: dict[str, Any], path: str, needle: str) -> bool:
    """The change really exists on the run's integration branch. A COMPLETE
    state alone is not proof: a worker can report done having changed nothing."""
    branch = (final.get("integration") or {}).get("branch")
    if final["state"] != "COMPLETE" or not branch:
        return False
    shown = subprocess.run(["git", "show", f"{branch}:{path}"], cwd=repo, capture_output=True, text=True)
    return shown.returncode == 0 and needle in shown.stdout


CHECKS = {"docs": ("docs/usage.md", "greet("), "farewell": ("app/greet.py", "def farewell")}


def _explicit(engine: Orchestrator, repo: Path, goal: str, task: dict[str, Any]) -> dict[str, Any]:
    summary = engine.create_run(goal, repository=repo, tasks=[task], policy=_policy(default_validators=[TEST_VALIDATOR]))
    engine.start(summary["run_id"], True)
    final = engine.run_loop(summary["run_id"], max_seconds=300)
    return {"run_id": summary["run_id"], "passed": _delivered(repo, final, *CHECKS[task["id"]]), "state": final["state"]}


def scenario_documentation_change(engine: Orchestrator, repo: Path) -> dict[str, Any]:
    return _explicit(engine, repo, "Document greet() in docs/usage.md", {"id": "docs", "goal": "Document greet() in docs/usage.md", "scope": ["docs/usage.md"], "capability_class": "fast", "effort": "low"})


def scenario_small_code_change(engine: Orchestrator, repo: Path) -> dict[str, Any]:
    return _explicit(engine, repo, "Add farewell(name)", {"id": "farewell", "goal": "Add farewell(name) to app/greet.py returning 'Goodbye, <name>!' and a unit test", "scope": ["app/greet.py", "tests/test_greet.py"], "capability_class": "fast", "effort": "low"})


def scenario_test_failure_repair(engine: Orchestrator, repo: Path) -> dict[str, Any]:
    return _explicit(engine, repo, "Add farewell(name)", {"id": "farewell", "goal": "Add farewell(name) to app/greet.py returning 'Goodbye, <name>!' and a unit test", "scope": ["app/greet.py", "tests/test_greet.py"], "capability_class": "fast", "effort": "low"})


def scenario_cross_agent_review(engine: Orchestrator, repo: Path) -> dict[str, Any]:
    return _explicit(engine, repo, "Add farewell(name)", {"id": "farewell", "goal": "Add farewell(name) to app/greet.py returning 'Goodbye, <name>!' and a unit test", "scope": ["app/greet.py", "tests/test_greet.py"], "capability_class": "fast", "effort": "low"})


def scenario_context_retrieval(engine: Orchestrator, repo: Path) -> dict[str, Any]:
    """Agent OS context packet for the real registered project, when present."""
    run_id = f"bench-context-{int(time.time() * 1000)}"
    try:
        from ..compiler import compile_context
        from ..registry import projects

        project = next((item["id"] for item in projects() if item["id"] == "personal-agent-os"), None) or (projects() or [{}])[0].get("id")
        packet = compile_context(project, "continue the roadmap: next unfinished stage", token_budget=2200)
    except Exception as exc:
        return {"run_id": run_id, "passed": False, "state": "SKIPPED", "detail": f"no registered project: {exc}"}
    measurement = packet["context_measurement"]
    candidate = measurement["naive_all_registered_context_tokens"]
    selected = measurement["estimated_packet_tokens"]
    engine.ledger.emit(
        run_id, "context_selected", "context-packet",
        method=f"Agent OS compile_context; candidate = all registered context files + skills; {ESTIMATE_METHOD}",
        candidate_items=measurement.get("naive_all_registered_context_items") or 0, selected_items=1,
        candidate_tokens_estimate=candidate, selected_tokens_estimate=selected,
        reduction_pct=round(100.0 * (candidate - selected) / candidate, 1) if candidate else None,
    )
    engine.ledger.emit(run_id, "local_execution", what="compiled a context packet without a model")
    return {"run_id": run_id, "passed": selected <= measurement["token_budget"], "state": "COMPLETE", "project": project}


SCENARIOS: dict[str, Callable[[Orchestrator, Path], dict[str, Any]]] = {
    "repository_inspection": scenario_repository_inspection,
    "documentation_change": scenario_documentation_change,
    "small_code_change": scenario_small_code_change,
    "test_failure_repair": scenario_test_failure_repair,
    "roadmap_continuation": scenario_roadmap_continuation,
    "context_retrieval": scenario_context_retrieval,
    "cross_agent_review": scenario_cross_agent_review,
}
DESCRIPTIONS = {
    "repository_inspection": "How many roadmap stages remain? (repository metadata)",
    "documentation_change": "Edit docs/usage.md (fast tier) + cross-review",
    "small_code_change": "Add a function + test (fast tier) + cross-review",
    "test_failure_repair": "First attempt fails its test; validator-driven escalation repairs it",
    "roadmap_continuation": "Continue Roadmap on the fixture: scan, plan, implement, test, review, integrate",
    "context_retrieval": "Agent OS context packet vs all registered project context (real project)",
    "cross_agent_review": "Reviewer requests a change; repair; re-review",
}


# ---------------------------------------------------------------------------
# Measurement
# ---------------------------------------------------------------------------


def _costs(registry: ProviderRegistry) -> dict[tuple[str, str], float]:
    table = {}
    for provider in registry.providers:
        for cls, value in (provider.get("costs") or {}).items():
            try:
                table[(provider["id"], cls)] = float(value)
            except (TypeError, ValueError):
                continue
    return table


def measure(engine: Orchestrator, outcome: dict[str, Any], repo: Path, runtime: float, registry: ProviderRegistry, live: bool) -> dict[str, Any]:
    run_id = outcome.get("run_id")
    events = engine.ledger.read(run_id)[0] if run_id else []
    report = summarize(events)
    calls = report["model_calls"]
    counts = report["counts"]
    files, whole_chars = tracked_text_chars(repo)
    completions = [event for event in events if event["type"] in {"model_completed", "model_failed"}]
    prompt_chars = sum(int(event["data"].get("prompt_chars") or 0) for event in completions)
    costs = _costs(registry)
    top = max((value for (pid, cls), value in costs.items() if cls == "frontier"), default=10.0)
    orchestrated_units = sum(costs.get((event["data"].get("provider"), event["data"].get("capability_class")), 0.0) for event in completions)
    avoided_calls = report["avoided"]["model_calls"]
    # Modeled naive baseline (estimate): every orchestrated call, plus every
    # avoided one, on the highest tier with the whole project in the prompt.
    baseline_calls = calls["total"] + avoided_calls
    baseline_prompt_chars = prompt_chars + baseline_calls * whole_chars
    tokens = report["tokens"]
    return {
        "scenario_passed": bool(outcome.get("passed")),
        "state": outcome.get("state"),
        "run_id": run_id,
        "runtime_s": round(runtime, 2),
        "model_calls": calls["total"],
        "model_calls_by_class": calls["by_class"],
        "model_calls_by_role": calls["roles"],
        "providers": calls["by_provider"],
        "highest_cost_calls": calls["expensive"],
        "local_operations": counts["local_operations"],
        "cache_hits": counts["cache_hits"],
        "skill_reuse": counts["skill_reuse"],
        "escalations": counts["escalations"],
        "retries": counts["retries"],
        "loop_guards": counts["loop_guards"],
        "tests": report["tests"],
        "model_calls_avoided": avoided_calls,
        "tokens": {
            "accuracy": "exact" if live and tokens["exact"]["calls"] else "unavailable",
            "input": tokens["exact"]["input"] if live else None,
            "output": tokens["exact"]["output"] if live else None,
            "cache_read": tokens["exact"]["cache_read"] if live else None,
            "calls_without_report": tokens["unavailable_calls"],
            "note": None if live else "synthetic workers: token usage deliberately not reported",
        },
        "prompt": {"chars_exact": prompt_chars, "tokens_estimate": estimate_tokens(prompt_chars)},
        "context": {
            "candidate_items": report["context"]["candidate_items"],
            "selected_items": report["context"]["selected_items"],
            "candidate_tokens_estimate": report["context"]["candidate_tokens_estimate"],
            "selected_tokens_estimate": report["context"]["selected_tokens_estimate"],
            "reduction_pct_estimate": report["context"]["reduction_pct"],
        },
        "relative_cost_units": {"orchestrated": orchestrated_units, "note": "registry `costs` weights (configured, not measured prices)"},
        "baseline_modeled": {
            "label": "ESTIMATED (modeled naive strategy, not a measured run)",
            "model_calls": baseline_calls,
            "all_calls_on_tier": "frontier",
            "prompt_tokens_estimate": estimate_tokens(baseline_prompt_chars),
            "whole_project": {"files": files, "tokens_estimate": estimate_tokens(whole_chars)},
            "relative_cost_units": baseline_calls * top,
            "tests_rerun_instead_of_reused": report["tests"]["reused"],
        },
        "estimated_prompt_tokens_avoided_vs_baseline": estimate_tokens(baseline_prompt_chars) - estimate_tokens(prompt_chars),
    }


def run_benchmark(scenarios: list[str] | None = None, *, live: bool = False, out_dir: Path | None = None, keep: bool = False) -> dict[str, Any]:
    chosen = scenarios or list(SCENARIOS)
    if live:
        chosen = [name for name in chosen if name in {"small_code_change", "repository_inspection", "context_retrieval"}]
    unknown = [name for name in chosen if name not in SCENARIOS]
    if unknown:
        raise ValueError(f"unknown scenario(s): {unknown}; choose from {sorted(SCENARIOS)}")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    target = (Path(out_dir) if out_dir else orchestrator_home() / "benchmarks" / stamp).resolve()
    target.mkdir(parents=True, exist_ok=True)
    # Live runs keep their state and transcripts for inspection, and work
    # outside %TEMP%: Codex's Windows sandbox refuses workspaces under it.
    keep = keep or live
    scratch = (orchestrator_home() / "benchmarks" / f"{stamp}-work") if live else Path(tempfile.mkdtemp(prefix="agent-os-bench-"))
    scratch.mkdir(parents=True, exist_ok=True)
    results = []
    try:
        for name in chosen:
            synthetic.reset()
            synthetic.SCRIPTS["benchmark"] = make_script(name)
            workdir = scratch / name
            workdir.mkdir()
            repo = build_fixture(workdir)
            registry = None if live else synthetic_registry()
            engine = _engine(target / "state" / name if keep else workdir / "state", registry)
            started = time.monotonic()
            try:
                outcome = SCENARIOS[name](engine, repo)
            except Exception as exc:  # a failing scenario is a result, not a crash
                outcome = {"run_id": None, "passed": False, "state": "ERROR", "detail": f"{type(exc).__name__}: {exc}"[:300]}
            runtime = time.monotonic() - started
            measured = measure(engine, outcome, repo, runtime, engine.registry(), live)
            if keep and outcome.get("run_id"):
                measured["files"] = {name: str(path) for name, path in zip(("telemetry", "transcript"), engine.ledger.paths(outcome["run_id"]))}
            if outcome.get("detail"):
                measured["detail"] = outcome["detail"]
            results.append({"scenario": name, "description": DESCRIPTIONS[name], **measured})
    finally:
        synthetic.reset()
        if not live:
            shutil.rmtree(scratch, ignore_errors=True)
    totals = _totals(results)
    report = {
        "schema": SCHEMA,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "mode": "live providers" if live else "offline (real engine, scripted synthetic workers)",
        "methodology": METHODOLOGY,
        "scenarios": results,
        "totals": totals,
    }
    (target / "results.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    (target / "report.md").write_text(render_markdown(report), encoding="utf-8")
    report["files"] = {"json": str(target / "results.json"), "markdown": str(target / "report.md")}
    return report


def _totals(results: list[dict[str, Any]]) -> dict[str, Any]:
    keys = ("model_calls", "highest_cost_calls", "local_operations", "cache_hits", "skill_reuse", "escalations", "retries", "model_calls_avoided", "loop_guards")
    totals: dict[str, Any] = {key: sum(item[key] for item in results) for key in keys}
    totals["passed"] = sum(1 for item in results if item["scenario_passed"])
    totals["scenarios"] = len(results)
    totals["runtime_s"] = round(sum(item["runtime_s"] for item in results), 2)
    totals["prompt_tokens_estimate"] = sum(item["prompt"]["tokens_estimate"] for item in results)
    totals["baseline_modeled_calls"] = sum(item["baseline_modeled"]["model_calls"] for item in results)
    totals["baseline_modeled_prompt_tokens_estimate"] = sum(item["baseline_modeled"]["prompt_tokens_estimate"] for item in results)
    totals["orchestrated_relative_cost_units"] = sum(item["relative_cost_units"]["orchestrated"] for item in results)
    totals["baseline_relative_cost_units"] = sum(item["baseline_modeled"]["relative_cost_units"] for item in results)
    totals["tests_reused"] = sum(item["tests"]["reused"] for item in results)
    return totals


METHODOLOGY = {
    "model_calls": "counted from model_completed/model_failed telemetry events (measured)",
    "tokens": "exact only when a provider reports them (live mode); synthetic workers report none, so offline token usage is 'unavailable'",
    "prompt_tokens_estimate": f"exact prompt characters written by Orchestrator, converted with {ESTIMATE_METHOD} (estimate). Excludes the agent CLI's own system prompt and any files the agent reads itself, which live runs show can dominate usage",
    "context_reduction": "(candidate - selected) / candidate, where candidate = every registered context source that could be handed to a model and selected = what was put in the prompt; characters measured, tokens estimated",
    "baseline": "modeled naive strategy: every call (including avoided ones) on the highest configured tier with the whole tracked project text in the prompt, no test-result reuse; derived from measured sizes; ESTIMATED",
    "relative_cost_units": "sum of the provider registry's configured `costs` weights per call; relative weights, not prices",
    "avoided_calls": "work_avoided telemetry events: roadmap/repository questions answered locally, no-change reviews skipped, resumed plans",
}


def render_markdown(report: dict[str, Any]) -> str:
    lines = [f"# Orchestrator efficiency benchmark", "", f"- Created: {report['created_at']}", f"- Mode: {report['mode']}", ""]
    lines += ["| Scenario | Pass | Model calls (by tier) | Avoided | Local ops | Cache hits | Escalations | Prompt tok (est.) | Baseline prompt tok (modeled est.) | Context reduction (est.) | Runtime |", "|---|---|---|---|---|---|---|---|---|---|---|"]
    for item in report["scenarios"]:
        tiers = ", ".join(f"{key} {value}" for key, value in sorted(item["model_calls_by_class"].items())) or "0"
        reduction = item["context"]["reduction_pct_estimate"]
        lines.append(
            f"| {item['scenario']} | {'yes' if item['scenario_passed'] else 'NO'} | {item['model_calls']} ({tiers}) | {item['model_calls_avoided']} | {item['local_operations']} | {item['cache_hits']} | {item['escalations']} | "
            f"{item['prompt']['tokens_estimate']:,} | {item['baseline_modeled']['prompt_tokens_estimate']:,} | {'—' if reduction is None else f'{reduction}%'} | {item['runtime_s']}s |"
        )
    totals = report["totals"]
    lines += ["", "## Totals", ""]
    lines += [f"- {key.replace('_', ' ')}: {value}" for key, value in totals.items()]
    lines += ["", "## Methodology", ""]
    lines += [f"- **{key}**: {value}" for key, value in report["methodology"].items()]
    return "\n".join(lines) + "\n"
