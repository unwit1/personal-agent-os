"""Per-task-family specialization records for free OpenRouter models.

Derived deterministically from capability observations, restricted to models
in a given free catalog snapshot. See docs/free-compute-broker.md.
"""
from __future__ import annotations

import hashlib
from typing import Any, Iterable

from . import capability

SCHEMA_VERSION = "agent-os/free-specialization/v1"
DEFAULT_FLOOR = 0.9
DEFAULT_MIN_SAMPLES = 5


def _catalog_models(catalog: Any) -> dict[str, dict[str, Any]]:
    models = catalog.get("models") if isinstance(catalog, dict) else catalog
    result = {}
    for item in models or []:
        slug = item if isinstance(item, str) else (item or {}).get("slug")
        if slug:
            result[slug] = item if isinstance(item, dict) else {"slug": slug}
    return result


def _resolve_floor(floor: Any, task_family: str) -> float:
    if isinstance(floor, dict):
        floor = floor.get(task_family, floor.get("default"))
    return DEFAULT_FLOOR if floor is None else float(floor)


def _num(value: Any) -> float | None:
    return float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else None


def _percentile(values: list[float], q: float) -> int | None:
    if not values:
        return None
    ordered = sorted(values)
    return int(round(ordered[min(len(ordered) - 1, int(q * len(ordered)))]))


def _rate(items: list[dict[str, Any]], field: str) -> float | None:
    flags = [bool(item[field]) for item in items if isinstance(item.get(field), bool)]
    return round(sum(flags) / len(flags), 3) if flags else None


def _latency_ms(item: dict[str, Any]) -> float | None:
    millis = _num(item.get("latency_ms"))
    if millis is None and _num(item.get("seconds")) is not None:
        millis = _num(item.get("seconds")) * 1000
    return millis


def _status(n: int, low: float | None, floor: float, min_samples: int) -> str:
    if low is not None and low >= floor:
        return "proven"
    return "canary" if n < min_samples else "unproven"


def build_records(observations: Iterable[dict[str, Any]] | None, catalog: Any, *, floor: Any = None,
                  min_samples: int = DEFAULT_MIN_SAMPLES) -> list[dict[str, Any]]:
    """One record per (task_family, model, revision) for free catalog models.

    ``floor`` is a number or a per-family map (policy ``routing.reliability_floor``)."""
    free = _catalog_models(catalog)
    groups: dict[tuple, list[dict[str, Any]]] = {}
    for item in capability.read_observations() if observations is None else observations:
        if item.get("status") == "unroutable":
            continue
        provider = str(item.get("provider") or "")
        if provider and not provider.startswith("openrouter"):
            continue
        slug = item.get("model_resolved") or item.get("model")
        if slug not in free or not item.get("task_family"):
            continue
        revision = item.get("model_revision") or free[slug].get("revision")
        groups.setdefault((item["task_family"], slug, revision), []).append(item)
    records = []
    for (family, slug, revision), items in sorted(groups.items(), key=lambda pair: [str(p) for p in pair[0]]):
        counted = [i for i in items if not str(i.get("failure_type") or "").startswith(capability.AVAILABILITY_FAILURES)]
        n = len(counted)
        passed = sum(1 for i in counted if i.get("validator_passed"))
        low, high = capability.wilson(passed, n)
        requests = sum(max(1, int(_num(i.get("requests")) or 1)) for i in counted)
        latencies = [v for v in (_latency_ms(i) for i in counted) if v]
        stamps = sorted(str(i.get("at")) for i in counted if i.get("at"))
        records.append({
            "schema_version": SCHEMA_VERSION,
            "task_family": family,
            "model": slug,
            "revision": revision,
            "key": capability.model_key({"model_resolved": slug, "model_revision": revision}),
            "n": n,
            "passed": passed,
            "pass_rate": round(passed / n, 3) if n else None,
            "wilson95": [low, high],
            "retries": sum(int(_num(i.get("retries")) or _num(i.get("repairs")) or 0) for i in counted),
            "latency_ms": {"p50": _percentile(latencies, 0.5), "p90": _percentile(latencies, 0.9)},
            "structured_output_reliability": _rate(counted, "structured_output_ok"),
            "tool_reliability": _rate(counted, "tool_ok"),
            "useful_progress_per_request": round(passed / requests, 3) if requests else None,
            "review_acceptance_rate": _rate(counted, "review_accepted"),
            "context_failures": sum(1 for i in counted if str(i.get("failure_type") or "").startswith("context")),
            "availability_failures": len(items) - n,
            "status": _status(n, low, _resolve_floor(floor, family), min_samples),
            "first_observed": stamps[0] if stamps else None,
            "last_observed": stamps[-1] if stamps else None,
            "evidence": [f"local:capability/observations.jsonl#{i.get('call_id')}" for i in counted][-20:],
        })
    return records


def rank(records: Iterable[dict[str, Any]], task_family: str) -> list[str]:
    """Models for the family: proven first by Wilson lower bound, then canary."""
    def order(record: dict[str, Any]) -> tuple:
        return (-(record["wilson95"][0] or 0.0), -record["n"], record["model"])

    mine = [r for r in records if r.get("task_family") == task_family]
    chosen = sorted((r for r in mine if r["status"] == "proven"), key=order) + sorted((r for r in mine if r["status"] == "canary"), key=order)
    return [r["model"] for r in chosen]


def _roll(*parts: Any) -> float:
    digest = hashlib.sha256("|".join(str(p) for p in parts).encode()).digest()
    return int.from_bytes(digest[:8], "big") / 2**64


def canary_pick(records: Iterable[dict[str, Any]], task_family: str, catalog: Any, rate: float, seed: Any,
                *, min_samples: int = DEFAULT_MIN_SAMPLES) -> str | None:
    """Deterministically route ``rate`` of traffic to a new/under-sampled free
    model; None otherwise, so proven models keep all other traffic."""
    sampled = {r["model"]: r["n"] for r in records if r.get("task_family") == task_family}
    candidates = sorted(slug for slug in _catalog_models(catalog) if sampled.get(slug, 0) < min_samples)
    if not candidates or rate <= 0 or _roll("explore", task_family, seed) >= rate:
        return None
    least = min(sampled.get(slug, 0) for slug in candidates)
    pool = [slug for slug in candidates if sampled.get(slug, 0) == least]
    return pool[int(_roll("pick", task_family, seed) * len(pool)) % len(pool)]
