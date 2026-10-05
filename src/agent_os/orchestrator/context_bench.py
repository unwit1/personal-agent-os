"""Deterministic synthetic measurements for prompt and context economy."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

from agent_os import economy

from . import context_economy, prompt_measure
from .repomap import scope_map
from .usage import estimate_tokens


SCHEMA = "personal-agent/orchestrator-context-bench/v1"
COMPARE_SCHEMA = "personal-agent/orchestrator-context-bench-compare/v1"


def _read_path(value: dict[str, Any], path: str) -> Any:
    """Read a dotted path, returning None if any component is absent."""
    current: Any = value
    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def compare(baseline: dict, current: dict) -> dict:
    """Compare two context bench reports without performing I/O."""
    if baseline.get("schema") != SCHEMA:
        raise ValueError(f"baseline schema must be {SCHEMA}")

    metric_specs = [
        ("compiler.totals.selective_tokens", "lower_is_better"),
        ("prompts.totals.total_tokens", "lower_is_better"),
    ]
    roles = set((_read_path(baseline, "prompts.roles") or {}).keys())
    roles.update((_read_path(current, "prompts.roles") or {}).keys())
    metric_specs.extend(
        (f"prompts.roles.{role}.total_tokens", "lower_is_better")
        for role in sorted(roles)
    )
    metric_specs.extend([
        ("handoffs.compacted_tokens", "lower_is_better"),
        ("prompts.totals.cacheable_prefix_tokens", "higher_is_better"),
        ("handoffs.tokens_avoided", "higher_is_better"),
        ("compiler.totals.tokens_avoided", "higher_is_better"),
        ("scope_maps.overhead_tokens", "lower_is_better"),
    ])

    metrics: list[dict[str, Any]] = []
    for path, direction in metric_specs:
        before = _read_path(baseline, path)
        after = _read_path(current, path)
        if before is None or after is None:
            status, delta = "missing", None
        else:
            delta = after - before
            improved = delta < 0 if direction == "lower_is_better" else delta > 0
            regressed = delta > 0 if direction == "lower_is_better" else delta < 0
            status = "improved" if improved else "regressed" if regressed else "unchanged"
        metrics.append({
            "metric": path,
            "baseline": before,
            "current": after,
            "delta": delta,
            "direction": direction,
            "status": status,
        })

    path = "compiler.totals.all_within_budget"
    before, after = _read_path(baseline, path), _read_path(current, path)
    if before is None or after is None:
        status = "missing"
    elif before is True and after is False:
        status = "regressed"
    elif before is False and after is True:
        status = "improved"
    else:
        status = "unchanged"
    metrics.append({
        "metric": path,
        "baseline": before,
        "current": after,
        "delta": None,
        "direction": "must_stay_true",
        "status": status,
    })
    regressions = [item["metric"] for item in metrics if item["status"] == "regressed"]
    return {
        "schema": COMPARE_SCHEMA,
        "model_calls": 0,
        "metrics": metrics,
        "regressions": regressions,
        "regressed": bool(regressions),
    }


def build(
    corpus_path: Path,
    handoffs_path: Path,
    *,
    project: str = "personal-agent-os",
    token_budget: int = 1200,
    run_dirs: Iterable[Path] = (),
    scope_repo: Path | None = None,
) -> dict[str, Any]:
    """Measure fixed corpus, synthetic prompts, handoffs, and optional coverage."""
    cases = json.loads(Path(corpus_path).read_text(encoding="utf-8"))
    handoffs = json.loads(Path(handoffs_path).read_text(encoding="utf-8"))

    compiler_cases: list[dict[str, Any]] = []
    for case in cases:
        report = economy.context_economy_report(project, case["task"], token_budget)
        compiler_cases.append({
            "case_id": case["case_id"],
            "complexity": case["complexity"],
            "selective_tokens": report["selective_tokens"],
            "naive_tokens": report["naive_tokens"],
            "tokens_avoided": report["tokens_avoided"],
            "within_budget": report["within_budget"],
            "matched_skill_count": report["matched_skill_count"],
        })

    compiler = {
        "cases": compiler_cases,
        "totals": {
            "cases": len(compiler_cases),
            "selective_tokens": sum(item["selective_tokens"] for item in compiler_cases),
            "naive_tokens": sum(item["naive_tokens"] for item in compiler_cases),
            "tokens_avoided": sum(item["tokens_avoided"] for item in compiler_cases),
            "all_within_budget": all(item["within_budget"] for item in compiler_cases),
        },
    }

    run = {
        "run_id": "run-20000101T000000Z-000000",
        "goal": "synthetic context bench",
        "project": None,
        "policy": {"shared_prefix": True},
    }
    nodes = [{"id": "planner", "role": "planner", "goal": run["goal"], "scope": [], "validators": []}]
    for index, case in enumerate(cases):
        for role in ("implementer", "reviewer"):
            nodes.append({
                "id": f"{role}-{index}",
                "role": role,
                "goal": case["task"],
                "scope": [],
                "validators": [],
            })

    scope_maps_dict: dict[str, str] | None = None
    if scope_repo is not None:
        scope_maps_dict = {}
        scope_maps_data = {"cases": 0, "map_tokens": 0}
        for index, case in enumerate(cases):
            scope = case.get("scope", [])
            if scope:
                map_result = scope_map(scope_repo, scope)
                scope_maps_dict[f"implementer-{index}"] = map_result["text"]
                scope_maps_dict[f"reviewer-{index}"] = map_result["text"]
                scope_maps_data["cases"] += 1
                scope_maps_data["map_tokens"] += estimate_tokens(map_result["text"])

    directories = tuple(run_dirs)
    prompts_result = prompt_measure.measure(run, nodes, scope_maps=scope_maps_dict)
    report = {
        "schema": SCHEMA,
        "model_calls": 0,
        "compiler": compiler,
        "prompts": prompts_result,
        "handoffs": economy.handoff_compaction_report(handoffs),
        "telemetry": context_economy.build(directories)["coverage"] if directories else None,
    }

    if scope_repo is not None:
        report["scope_maps"] = {
            "cases": scope_maps_data["cases"],
            "map_tokens": scope_maps_data["map_tokens"],
            "prompt_tokens_without": 0,
            "prompt_tokens_with": prompts_result["totals"]["total_tokens"],
            "overhead_tokens": 0,
            "cacheable_prefix_tokens_with": prompts_result["totals"]["cacheable_prefix_tokens"],
        }
        # We need to do a measurement without scope_maps to get the comparison
        prompts_without = prompt_measure.measure(run, nodes, scope_maps=None)
        report["scope_maps"]["prompt_tokens_without"] = prompts_without["totals"]["total_tokens"]
        report["scope_maps"]["overhead_tokens"] = prompts_result["totals"]["total_tokens"] - prompts_without["totals"]["total_tokens"]
    else:
        report["scope_maps"] = None

    return report
