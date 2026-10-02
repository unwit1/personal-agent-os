"""Shadow rotation advisor cost model (IMP-0019 phase 1).

Deterministic, offline, advice-only: this module makes no model or network
calls, writes nothing, and is never called by dispatch. It only estimates
whether ending an episode at a call boundary and restarting from a capped
structured handoff would have cost less input than continuing. Design:
docs/orchestrator-os/self-audit/rotation-advisor.md (sections 2 to 4).

Series are lists of call dicts ordered by (attempt or 0, seq) with the keys
``input``, ``output``, ``cache_read``, ``prompt``, ``attempt`` and ``role``.
``bootstrap`` is an int or a ``{role: int}`` mapping; ``retries`` and
``reviews`` are ints (or callables of ``k``) counted before the boundary,
where ``reviews`` is review rounds plus review-required rounds.
"""

from __future__ import annotations

import math
from typing import Any, Callable, Mapping

from .context_economy import _ratio, _stats  # noqa: F401  (_stats re-exported for reports)

SCHEMA = "personal-agent/orchestrator-rotation-advice/v1"
MODE = "shadow"
HANDOFF_FACTOR = 0.5
HANDOFF_CAP = 8000
REDISCOVERY_RATE = 0.25
MARGIN = 0.2
ROLE_FALLBACK_WEIGHT = 0.5


def _n(call: Mapping[str, Any], key: str) -> int:
    value = call.get(key)
    return value if isinstance(value, int) and not isinstance(value, bool) else 0


def _bootstrap_for(bootstrap: Any, role: Any) -> int | None:
    value = bootstrap.get(role) if isinstance(bootstrap, Mapping) else bootstrap
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def _count(value: Any, k: int) -> int:
    value = value(k) if callable(value) else value
    return max(0, value) if isinstance(value, int) and not isinstance(value, bool) else 0


def _semantic(series: list[Mapping[str, Any]], k: int) -> bool:
    return (series[k].get("attempt") or 0) != (series[k - 1].get("attempt") or 0)


def estimate_boundary(
    series: list[Mapping[str, Any]],
    k: int,
    bootstrap: Any,
    retries: Any,
    reviews: Any,
    retrieval_medians: Mapping[str, int] | None = None,
) -> dict[str, Any] | None:
    """Score the boundary before ``series[k]``; None when it cannot be scored."""
    n = len(series)
    if not 1 <= k < n:
        return None
    rest = series[k:]
    boots = [_bootstrap_for(bootstrap, c.get("role")) for c in rest]
    if any(b is None for b in boots):
        return None
    retrieval = []
    for c in rest:
        p = _n(c, "prompt")
        if p <= 0:
            p = (retrieval_medians or {}).get(c.get("role"), 0)
        if p <= 0:
            return None
        retrieval.append(p)
    continue_cost = sum(_n(c, "input") for c in rest)
    handoff = min(HANDOFF_CAP, math.ceil(HANDOFF_FACTOR * sum(_n(c, "output") for c in series[:k])))
    rework = _count(retries, k) + _count(reviews, k)
    penalty = math.ceil(REDISCOVERY_RATE * boots[0] * rework)
    bootstrap_overhead = sum(boots)
    handoff_overhead = handoff * len(rest)
    retrieval_tokens = sum(retrieval)
    rotate_cost = bootstrap_overhead + handoff_overhead + retrieval_tokens + penalty
    savings = continue_cost - rotate_cost
    rotate = _semantic(series, k) and savings > MARGIN * continue_cost
    return {
        "continue_cost": continue_cost,
        "rotate_cost": rotate_cost,
        "bootstrap_overhead": bootstrap_overhead,
        "handoff_overhead": handoff_overhead,
        "retrieval_tokens": retrieval_tokens,
        "rediscovery_penalty": penalty,
        "projected_savings": savings,
        "recommendation": "rotate" if rotate else "continue",
    }


def advise_worker(
    series: list[Mapping[str, Any]],
    bootstrap: Any,
    retries: Any,
    reviews: Any,
    retrieval_medians: Mapping[str, int] | None = None,
) -> dict[str, Any]:
    """Evaluate every boundary; pick the rotate boundary with most savings."""
    best_k: int | None = None
    best: dict[str, Any] | None = None
    for k in range(1, len(series)):
        est = estimate_boundary(series, k, bootstrap, retries, reviews, retrieval_medians)
        if est is None or est["recommendation"] != "rotate":
            continue
        if best is None or est["projected_savings"] > best["projected_savings"]:
            best_k, best = k, est
    if best is None:
        return {"boundary": None, "estimate": None, "recommendation": "continue"}
    return {"boundary": best_k, "estimate": best, "recommendation": "rotate"}
