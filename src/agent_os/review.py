from __future__ import annotations

from typing import Any


HIGH_RISK_TERMS = {"security", "migration", "schema", "privacy", "delete", "credential", "memory", "policy"}


def assess(changed_files: list[str], tests_failed: bool = False, architecture_change: bool = False) -> dict[str, Any]:
    score = min(len(changed_files) / 40, 0.25)
    reasons: list[str] = []
    lowered = " ".join(changed_files).casefold()
    hits = sorted(term for term in HIGH_RISK_TERMS if term in lowered)
    if hits:
        score += min(0.1 * len(hits), 0.35)
        reasons.append(f"risk-sensitive paths: {', '.join(hits)}")
    if tests_failed:
        score += 0.35
        reasons.append("deterministic validation failed")
    if architecture_change:
        score += 0.35
        reasons.append("architecture change")
    score = min(score, 1.0)
    if score >= 0.75:
        level = 3
    elif score >= 0.4:
        level = 2
    elif score >= 0.15:
        level = 1
    else:
        level = 0
    return {
        "risk_score": round(score, 2),
        "review_level": level,
        "reasons": reasons or ["routine change; deterministic checks first"],
        "max_model_review_calls": 0 if level == 0 else (1 if level < 3 else 2),
    }
