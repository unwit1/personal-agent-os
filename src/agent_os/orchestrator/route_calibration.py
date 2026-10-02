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

from typing import Any, Iterable, Mapping

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
