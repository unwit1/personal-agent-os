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

import json
import math
import statistics
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

from .context_economy import (  # noqa: F401  (_stats re-exported for reports)
    BUCKETS, RUN_ID, _bucket_of, _Labels, _ratio, _read_run, _scan, _stats, assert_aggregate_only,
)
from .ledger import read_events
from .store import orchestrator_home

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


# -- offline report ----------------------------------------------------------

REVIEW_EVENTS = ("review_started", "review_completed", "review_required")
COUNTED = ("retry", "model_escalated", "fallback") + REVIEW_EVENTS


def _median_int(values: list[int]) -> int:
    return math.ceil(statistics.median(values))


def _node_events(run_dir: Path, forbidden: set[str]) -> dict[str, dict[str, list[int]]]:
    """Seqs of each counted event, keyed by node (or review subject)."""
    events, _ = read_events(run_dir / "telemetry.jsonl")
    found: dict[str, dict[str, list[int]]] = {kind: defaultdict(list) for kind in COUNTED}
    for event in events:
        kind, data = event.get("type"), event.get("data")
        if kind not in COUNTED[:5] or not isinstance(data, dict):
            continue
        key = data.get("subject") if kind in REVIEW_EVENTS else event.get("node")
        if not key:
            continue
        key = str(key)
        forbidden.add(key)
        seq = event.get("seq") if isinstance(event.get("seq"), int) else 0
        found[kind][key].append(seq)
        if kind == "review_completed":
            findings = data.get("material_findings")
            if (isinstance(findings, int) and not isinstance(findings, bool) and findings > 0) or data.get("verdict") == "blocked":
                found["review_required"][key].append(seq)
    return found


def _before(found: dict[str, dict[str, list[int]]], kinds: tuple[str, ...], keys: list[str], seq: int) -> int:
    return sum(1 for kind in kinds for key in keys for s in found[kind].get(key, ()) if s < seq)


def _rework(found: dict[str, dict[str, list[int]]], node: str, series: list[Mapping[str, Any]]):
    """Counters of events before the boundary; a repair node inherits its subject's reviews."""
    base = node.split(".repair")[0]
    subjects = [node] if base == node else [node, base]

    def retries(k: int) -> int:
        return _before(found, ("retry",), [node], series[k]["seq"])

    def reviews(k: int) -> int:
        rounds = max(_before(found, (kind,), subjects, series[k]["seq"]) for kind in ("review_started", "review_completed"))
        return rounds + _before(found, ("review_required",), subjects, series[k]["seq"])

    return retries, reviews


def _tally() -> dict[str, int]:
    return {"continue": 0, "rotate": 0}


def build(run_dirs: Iterable[Path]) -> dict[str, Any]:
    labels = _Labels()
    forbidden: set[str] = set()
    cov: dict[str, Any] = {
        "runs": 0, "malformed_runs": 0, "runs_without_run_started": 0, "events": 0, "malformed_lines": 0,
        "calls": 0, "exact_calls": 0, "unreported_calls": 0, "synthetic_calls_excluded": 0,
        "eligible_calls": 0, "calls_without_prompt_estimate": 0,
        "excluded": {"estimated": 0, "unavailable": 0, "synthetic": 0, "inconsistent": 0},
        "sanitized_labels": 0, "unparsed_worker_dirs": 0,
    }
    counters = {kind: 0 for kind in COUNTED}
    runs: list[tuple[str, dict[str, Any], dict[str, Any]]] = []
    for run_dir in sorted(Path(p) for p in run_dirs):
        if not RUN_ID.match(run_dir.name):
            cov["malformed_runs"] += 1
            continue
        run = _read_run(run_dir, labels, cov, forbidden)
        cov["runs"] += 1
        cov["runs_without_run_started"] += 0 if run["started"] else 1
        cov["unparsed_worker_dirs"] += sum(1 for w in run["workers"] if w is None)
        found = _node_events(run_dir, forbidden)
        for kind in COUNTED:
            counters[kind] += sum(len(v) for v in found[kind].values())
        runs.append((run_dir.name, run, found))
    cov["sanitized_labels"] = labels.sanitized

    firsts: dict[str, list[int]] = defaultdict(list)
    prompts: dict[str, list[int]] = defaultdict(list)
    for _, run, _ in runs:
        for series in run["nodes"].values():
            firsts[series[0]["role"]].append(series[0]["input"])
            for call in series:
                if call["prompt"]:
                    prompts[call["role"]].append(call["prompt"])
    bootstrap = {role: _median_int(v) for role, v in sorted(firsts.items())}
    retrieval = {role: _median_int(v) for role, v in sorted(prompts.items())}

    by_role: dict[str, dict[str, int]] = defaultdict(_tally)
    by_bucket: dict[str, dict[str, int]] = {b: _tally() for b in BUCKETS}
    by_role_bucket: dict[str, dict[str, dict[str, int]]] = defaultdict(lambda: {b: _tally() for b in BUCKETS})
    savings: list[float] = []
    boundaries: dict[str, list[int]] = defaultdict(list)
    sum_continue = sum_rotate = workers = 0
    for _, run, found in runs:
        for node, series in sorted(run["nodes"].items()):
            role = series[0]["role"]
            retries, reviews = _rework(found, node, series)
            advice = advise_worker(series, bootstrap, retries, reviews, retrieval)
            total = sum(c["input"] for c in series)
            workers += 1
            sum_continue += total
            rec = advice["recommendation"]
            bucket = _bucket_of(len(series))
            by_role[role][rec] += 1
            by_bucket[bucket][rec] += 1
            by_role_bucket[role][bucket][rec] += 1
            if rec == "rotate":
                est, k = advice["estimate"], advice["boundary"]
                savings.append(est["projected_savings"])
                boundaries[role].append(k)
                sum_rotate += sum(c["input"] for c in series[:k]) + est["rotate_cost"]
            else:
                sum_rotate += total
    rotating = sum(t["rotate"] for t in by_role.values())
    result = {
        "schema": SCHEMA,
        "mode": MODE,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "dispatch_changed": False,
        "runs": [run_id for run_id, _, _ in runs],
        "coverage": {**cov, "workers": workers, "event_counts": counters},
        "recommendations": {
            "by_role": {r: dict(t) for r, t in sorted(by_role.items())},
            "by_node_call_bucket": by_bucket,
            "by_role_and_bucket": dict(sorted(by_role_bucket.items())),
        },
        "would_rotate_share": _ratio(rotating, workers),
        "predicted_savings": _stats(savings),
        "break_even_boundary": {r: _stats(v) for r, v in sorted(boundaries.items())},
        "sum_continue_cost": sum_continue,
        "sum_rotate_cost_if_advised": sum_rotate,
    }
    _scan(result, forbidden - labels.seen)
    assert_aggregate_only(result, forbidden - labels.seen)
    return result


def report(home: Path | None = None, out: Path | None = None) -> dict[str, Any]:
    root = Path(home or orchestrator_home())
    run_dirs = [p for p in sorted((root / "runs").glob("*")) if p.is_dir()] if (root / "runs").is_dir() else []
    result = build(run_dirs)
    assert_aggregate_only(result)
    if out:
        target = Path(out)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    return result
