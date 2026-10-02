"""Shadow route calibration (IMP-0015, RouteLLM-style, measurement first).

Deterministic, offline, advice-only: this module makes no model or network
calls, writes nothing, and is never imported by dispatch. It estimates, from
existing orchestrator telemetry, whether the cheaper route would have passed
validation and review, and never changes routing.

``node_outcomes`` reduces the event dicts of one run's telemetry.jsonl
(keys ``type``, ``node``, ``seq``, ``data``) to one outcome per non-reviewer
node.
"""

from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

from .context_economy import RUN_ID, _Labels, _scan, assert_aggregate_only
from .ledger import read_events
from .store import orchestrator_home

SCHEMA = "personal-agent/orchestrator-route-calibration/v1"
MODE = "shadow"

_MODEL_EVENTS = ("model_completed", "model_failed")


def _seq(event: Mapping[str, Any]) -> int:
    value = event.get("seq")
    return value if isinstance(value, int) and not isinstance(value, bool) else 0


def _subject_node(subject: Any) -> Any:
    return subject.split(".repair")[0] if isinstance(subject, str) else subject


def _review_clean(reviews: list[Mapping[str, Any]]) -> bool | None:
    if not reviews:
        return None
    return all(
        r.get("material_findings") == 0 and r.get("verdict") != "blocked" for r in reviews
    )


def node_outcomes(events: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Return one outcome dict per non-reviewer node, sorted by node id."""
    by_node: dict[Any, list[Mapping[str, Any]]] = {}
    reviews: dict[Any, list[Mapping[str, Any]]] = {}
    for event in events:
        if not isinstance(event, dict) or not isinstance(event.get("data"), dict):
            continue
        if event.get("type") == "review_completed":
            subject = _subject_node(event["data"].get("subject"))
            reviews.setdefault(subject, []).append(event["data"])
        node = event.get("node")
        if node is not None:
            by_node.setdefault(node, []).append(event)

    outcomes: list[dict[str, Any]] = []
    for node in sorted(by_node, key=str):
        evs = sorted(by_node[node], key=_seq)
        models = [e for e in evs if e.get("type") in _MODEL_EVENTS]
        if not models:
            continue
        first = models[0]["data"]
        role = first.get("role")
        if role == "reviewer":
            continue
        escalated = [e for e in evs if e.get("type") == "model_escalated"]
        initial_class = first.get("capability_class")
        final_class = initial_class
        if escalated:
            to = escalated[-1]["data"].get("to")
            if isinstance(to, str):
                final_class = to.split("/")[0]
        tests = [e for e in evs if e.get("type") == "tests_completed"]
        validation = tests[-1]["data"].get("passed") if tests else None
        matched = reviews.get(node, [])
        clean = _review_clean(matched)
        if escalated or validation is False or clean is False:
            cheap: bool | None = False
        elif validation is True or clean is True:
            cheap = True
        else:
            cheap = None
        outcomes.append({
            "node": node,
            "role": role,
            "family": f"orchestrator-{role}",
            "initial_class": initial_class,
            "initial_effort": first.get("effort"),
            "provider": first.get("provider"),
            "escalations": len(escalated),
            "final_class": final_class,
            "retries": sum(1 for e in evs if e.get("type") == "retry"),
            "fallbacks": sum(1 for e in evs if e.get("type") == "fallback"),
            "validation_passed": validation,
            "reviewed": bool(matched),
            "review_clean": clean,
            "cheap_route_passed": cheap,
        })
    return outcomes


def _wilson_lower(passes: int, n: int) -> float:
    if n == 0:
        return 0.0
    z = 1.96
    z_sq = z * z
    p_hat = passes / n
    denominator = 1 + z_sq / n
    center = (p_hat + z_sq / (2 * n)) / denominator
    margin = (z / denominator) * math.sqrt(p_hat * (1 - p_hat) / n + z_sq / (4 * n * n))
    return max(0.0, center - margin)


def estimate_cells(outcomes: list[dict[str, Any]], min_samples: int = 5) -> dict[str, dict[str, dict[str, Any]]]:
    """Estimate statistics for each (family, capability_class) cell.

    Groups outcomes by family and initial_class, computing pass rates with
    Beta(1,1) posterior means and 95% Wilson score lower bounds.
    """
    by_family_class: dict[str, dict[str, list[dict[str, Any]]]] = {}

    for outcome in outcomes:
        family = outcome.get("family")
        initial_class = outcome.get("initial_class") or "unknown"

        if family not in by_family_class:
            by_family_class[family] = {}
        if initial_class not in by_family_class[family]:
            by_family_class[family][initial_class] = []

        by_family_class[family][initial_class].append(outcome)

    result: dict[str, dict[str, dict[str, Any]]] = {}

    for family in sorted(by_family_class.keys()):
        result[family] = {}
        for class_name in sorted(by_family_class[family].keys()):
            outcomes_in_cell = by_family_class[family][class_name]

            labeled = [o for o in outcomes_in_cell if o.get("cheap_route_passed") is not None]

            n = len(labeled)
            passes = sum(1 for o in labeled if o.get("cheap_route_passed") is True)
            escalated_count = sum(1 for o in outcomes_in_cell if o.get("escalations", 0) > 0)
            retries_total = sum(o.get("retries", 0) for o in outcomes_in_cell)
            review_required_count = sum(1 for o in outcomes_in_cell if o.get("review_clean") is False)

            p_pass = (passes + 1) / (n + 2)
            wilson_lower = _wilson_lower(passes, n)
            sufficient = n >= min_samples

            by_effort: dict[str, int] = {}
            by_provider: dict[str, int] = {}
            for o in outcomes_in_cell:
                effort = o.get("initial_effort") or "unknown"
                provider = o.get("provider") or "unknown"
                by_effort[effort] = by_effort.get(effort, 0) + 1
                by_provider[provider] = by_provider.get(provider, 0) + 1

            result[family][class_name] = {
                "n": n,
                "passes": passes,
                "unlabeled": len(outcomes_in_cell) - n,
                "escalated": escalated_count,
                "retries": retries_total,
                "review_required": review_required_count,
                "p_pass": round(p_pass, 4),
                "wilson_lower": round(wilson_lower, 4),
                "sufficient": sufficient,
                "by_effort": dict(sorted(by_effort.items())),
                "by_provider": dict(sorted(by_provider.items())),
            }

    return result


def calibrate(cells: dict[str, dict[str, dict[str, Any]]], target: float = 0.9, grid: list[float] | None = None) -> dict[str, Any]:
    """Calibrate escalation thresholds using Wilson score lower bounds.

    Finds a threshold that balances keeping cheap routes that pass with
    escalating those that are risky, targeting a minimum pass rate.
    """
    if grid is None:
        grid = [0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95]

    all_cells = [c for fam in cells.values() for c in fam.values()]
    total_labeled = sum(c["n"] for c in all_cells)

    curve: list[dict[str, Any]] = []

    for threshold in sorted(grid):
        keep_cheap_cells = [c for c in all_cells if c["sufficient"] and c["wilson_lower"] >= threshold]

        labeled_in_keep_cheap = sum(c["n"] for c in keep_cheap_cells)
        cheap_share = labeled_in_keep_cheap / total_labeled if total_labeled > 0 else 0.0

        if keep_cheap_cells:
            total_passes = sum(c["passes"] for c in keep_cheap_cells)
            total_n = sum(c["n"] for c in keep_cheap_cells)
            kept_pass_rate = total_passes / total_n if total_n > 0 else None
        else:
            kept_pass_rate = None

        escalations_avoided = sum(c["escalated"] for c in all_cells if not (c["sufficient"] and c["wilson_lower"] >= threshold))

        curve.append({
            "threshold": round(threshold, 2),
            "cheap_share": round(cheap_share, 4),
            "kept_pass_rate": round(kept_pass_rate, 4) if kept_pass_rate is not None else None,
            "escalations_avoided": escalations_avoided,
        })

    recommended_threshold = None
    reason = "insufficient_evidence"

    any_sufficient = any(cells[f][c]["sufficient"] for f in cells for c in cells[f])

    for point in curve:
        if point["kept_pass_rate"] is not None and point["kept_pass_rate"] >= target:
            recommended_threshold = point["threshold"]
            reason = "threshold_selected"
            break

    if recommended_threshold is None and any_sufficient:
        reason = "no_threshold_meets_target"

    return {
        "curve": curve,
        "target": target,
        "recommended_threshold": recommended_threshold,
        "reason": reason,
    }


def advise(cells: dict[str, dict[str, dict[str, Any]]], threshold: float) -> dict[str, dict[str, str]]:
    """Advise on routing for each cell given a threshold.

    Returns a nested dict with same structure as cells, with each cell
    assigned a recommendation.
    """
    result: dict[str, dict[str, str]] = {}

    for family in cells:
        result[family] = {}
        for class_name in cells[family]:
            cell = cells[family][class_name]
            if not cell["sufficient"]:
                result[family][class_name] = "insufficient_data"
            elif cell["wilson_lower"] >= threshold:
                result[family][class_name] = "keep_cheap"
            else:
                result[family][class_name] = "escalate_earlier"

    return result


# -- offline report ----------------------------------------------------------


def build(run_dirs: Iterable[Path], min_samples: int = 5, target: float = 0.9) -> dict[str, Any]:
    """Build route calibration report from run directories.

    Processes telemetry from each run, estimates pass rates per (family, class) cell,
    calibrates a threshold targeting the desired pass rate, and advises on routing.
    """
    labels = _Labels()
    forbidden: set[str] = set()
    cov: dict[str, Any] = {
        "runs": 0,
        "malformed_runs": 0,
        "malformed_lines": 0,
        "nodes": 0,
        "labeled": 0,
        "unlabeled": 0,
        "reviewer_nodes_excluded": 0,
        "sanitized_labels": 0,
    }
    runs: list[tuple[str, list[dict[str, Any]]]] = []

    for run_dir in sorted(Path(p) for p in run_dirs):
        if not RUN_ID.match(run_dir.name):
            cov["malformed_runs"] += 1
            continue

        telemetry_path = run_dir / "telemetry.jsonl"
        events, malformed_count = read_events(telemetry_path)
        cov["malformed_lines"] += malformed_count
        cov["runs"] += 1

        outcomes = node_outcomes(events)
        cov["reviewer_nodes_excluded"] += len({e['node'] for e in events if isinstance(e, dict) and isinstance(e.get('data'), dict) and e.get('type') in _MODEL_EVENTS and e.get('node') is not None}) - len(outcomes)
        for outcome in outcomes:
            node = outcome.get("node")
            if node:
                forbidden.add(str(node))
                cov["nodes"] += 1
            if outcome.get("cheap_route_passed") is not None:
                cov["labeled"] += 1
            else:
                cov["unlabeled"] += 1

        runs.append((run_dir.name, outcomes))

    all_outcomes: list[dict[str, Any]] = []
    for _, outcomes in runs:
        for outcome in outcomes:
            sanitized = dict(outcome)
            sanitized["family"] = labels(sanitized.get("family"))
            sanitized["initial_class"] = labels(sanitized.get("initial_class"))
            sanitized["initial_effort"] = labels(sanitized.get("initial_effort"))
            sanitized["provider"] = labels(sanitized.get("provider"))
            all_outcomes.append(sanitized)

    cov["sanitized_labels"] = labels.sanitized

    cells = estimate_cells(all_outcomes, min_samples=min_samples)
    calibration = calibrate(cells, target=target)
    recommended_threshold = calibration.get("recommended_threshold") or 0.95
    advice = advise(cells, recommended_threshold)

    result = {
        "schema": SCHEMA,
        "mode": MODE,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "routing_changed": False,
        "runs": [run_id for run_id, _ in runs],
        "coverage": cov,
        "cells": cells,
        "calibration": calibration,
        "advice": advice,
        "method": {
            "estimator": "beta_binomial_laplace",
            "bound": "wilson_95",
            "prior_art": "PA-routellm",
            "decision": "BORROW",
        },
    }

    _scan(result, forbidden - labels.seen)
    assert_aggregate_only(result, forbidden - labels.seen)
    return result


def report(home: Path | None = None, out: Path | None = None) -> dict[str, Any]:
    """Generate route calibration report from orchestrator home directory.

    Reads all run directories under home/runs, builds the report, and optionally
    writes it to the specified output file.
    """
    root = Path(home or orchestrator_home())
    run_dirs = [p for p in sorted((root / "runs").glob("*")) if p.is_dir()] if (root / "runs").is_dir() else []
    result = build(run_dirs)
    assert_aggregate_only(result)
    if out:
        target = Path(out)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    return result
