"""Deterministic synthetic measurements for prompt and context economy."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

from agent_os import economy

from . import context_economy, prompt_measure


SCHEMA = "personal-agent/orchestrator-context-bench/v1"


def build(
    corpus_path: Path,
    handoffs_path: Path,
    *,
    project: str = "personal-agent-os",
    token_budget: int = 1200,
    run_dirs: Iterable[Path] = (),
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

    directories = tuple(run_dirs)
    return {
        "schema": SCHEMA,
        "model_calls": 0,
        "compiler": compiler,
        "prompts": prompt_measure.measure(run, nodes),
        "handoffs": economy.handoff_compaction_report(handoffs),
        "telemetry": context_economy.build(directories)["coverage"] if directories else None,
    }
