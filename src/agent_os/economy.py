"""Deterministic, privacy-safe economy measurements for regression tests."""

from __future__ import annotations

from typing import Any, Iterable

from .compiler import compile_context
from .skills import Skill, match


def context_economy_report(project_id: str, task: str, token_budget: int = 1200) -> dict[str, Any]:
    """Compare the compiled selective packet with its known naive upper bound.

    This is intentionally not usage telemetry: it makes no provider call and
    reports only deterministic context-size diagnostics already produced by the
    compiler.
    """
    packet = compile_context(project_id, task, token_budget=token_budget)
    measurement = packet["context_measurement"]
    selected = packet.get("matched_skills") or []
    return {
        "project": project_id,
        "task": task,
        "selective_tokens": measurement["estimated_packet_tokens"],
        "naive_tokens": measurement["naive_all_registered_context_tokens"],
        "tokens_avoided": measurement["estimated_tokens_avoided"],
        "within_budget": measurement["within_budget"],
        "matched_skill_count": len(selected),
        "full_skill_bodies_loaded": packet["context_policy"]["full_skill_bodies_loaded"],
        "model_calls": 0,
    }


CAPABILITY_ORDER = ("deterministic", "fast", "balanced", "reasoning", "frontier")


def evaluate_skill_corpus(cases: Iterable[dict[str, Any]], skills: list[Skill], minimum_score: int = 2) -> list[dict[str, Any]]:
    """Return compact, deterministic skill-match evidence for fixed fixtures.

    Corpus fixtures hold task labels and expected public skill names only; they
    never need repository diffs, task history, or model/provider data.
    """
    results = []
    for case in cases:
        selected = [skill.name for skill in match(str(case["task"]), skills, minimum_score=minimum_score)]
        results.append(
            {
                "case_id": case["case_id"],
                "complexity": case["complexity"],
                "selected": selected,
                "expected_active": list(case["expected_active"]),
                "expected_dormant": list(case["expected_dormant"]),
            }
        )
    return results


def compare_economy_paths(baseline: dict[str, Any], economy: dict[str, Any]) -> dict[str, Any]:
    """Compare privacy-safe benchmark measurements without provider telemetry.

    A reduction is a success only when the economy path validates at least as
    well as the baseline. A validating stronger route is reported explicitly
    as justified instead of being mislabeled as a saving.
    """
    baseline_valid = bool(baseline.get("validation_passed"))
    economy_valid = bool(economy.get("validation_passed"))
    quality_parity = economy_valid or not baseline_valid
    deltas = {
        key: int(baseline.get(key, 0)) - int(economy.get(key, 0))
        for key in ("context_tokens", "model_calls", "repeated_work", "retries", "escalations", "wall_clock_ms")
    }
    baseline_class = str(baseline.get("highest_capability", "deterministic"))
    economy_class = str(economy.get("highest_capability", "deterministic"))
    baseline_rank = CAPABILITY_ORDER.index(baseline_class) if baseline_class in CAPABILITY_ORDER else len(CAPABILITY_ORDER)
    economy_rank = CAPABILITY_ORDER.index(economy_class) if economy_class in CAPABILITY_ORDER else len(CAPABILITY_ORDER)
    has_saving = any(value > 0 for value in deltas.values()) or economy_rank < baseline_rank
    if economy_valid and quality_parity and has_saving:
        outcome = "savings_with_validation"
    elif economy_valid:
        outcome = "stronger_route_justified"
    else:
        outcome = "validation_regression"
    return {
        "quality_parity": quality_parity,
        "baseline_validation_passed": baseline_valid,
        "economy_validation_passed": economy_valid,
        "deltas": deltas,
        "capability_rank_delta": baseline_rank - economy_rank,
        "outcome": outcome,
    }
