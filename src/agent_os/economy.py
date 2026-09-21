"""Deterministic, privacy-safe economy measurements for regression tests."""

from __future__ import annotations

from typing import Any

from .compiler import compile_context


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
