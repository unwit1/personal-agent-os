from __future__ import annotations

from . import contracts

DISPOSITIONS = ("ignore", "defer", "process", "delegate", "surface")

DEFAULT_ROUTES: dict[str, str] = {
    "decision.required": "surface",
    "communication.needs_response": "surface",
    "appointment.approaching": "surface",
    "agent.blocked": "surface",
    "project.stalled": "surface",
    "skill.used": "ignore",
    "skill.failed": "delegate",
    "task.deferred": "defer",
    "context.changed": "defer",
    "conversation.completed": "process",
    "idea.captured": "process",
    "task.created": "process",
    "task.completed": "process",
    "project.modified": "process",
    "decision.made": "process",
    "agent.completed": "process",
    "appointment.created": "process",
    "communication.received": "process",
    "preference.observed": "process",
    "outcome.recorded": "process",
}


def route_event(event: dict, rules: dict[str, str] | None = None) -> dict:
    """Choose an event disposition without exposing its payload."""
    errors = contracts.validate_event(event)
    if errors:
        raise ValueError("\n".join(errors))

    if rules is not None:
        for event_type, disposition in rules.items():
            if event_type not in contracts.EVENT_TYPES:
                raise ValueError(f"unknown event type in rules: {event_type!r}")
            if disposition not in DISPOSITIONS:
                raise ValueError(f"unknown disposition in rules: {disposition!r}")

    event_type = event["type"]
    if rules is not None and event_type in rules:
        disposition = rules[event_type]
        rule = "override"
    else:
        disposition = DEFAULT_ROUTES[event_type]
        rule = "default"
    reason = f"{rule} route for {event_type}"

    if disposition == "delegate" and (
        event.get("local_only") is True or contracts.requires_local_only(event["sensitivity"])
    ):
        disposition = "surface"
        rule = "local_only"
        reason = "local-only event cannot be delegated; surfaced for the user"

    return {
        "event_id": event["id"],
        "event_type": event_type,
        "disposition": disposition,
        "rule": rule,
        "reason": reason,
    }


def dispatch_pending(
    bus, consumer: str = "router", rules: dict[str, str] | None = None,
    log=None, routed_at: str | None = None,
) -> list[dict]:
    """Persist and acknowledge each pending event's route, recovering prior writes."""
    from .route_log import RouteLog

    if log is None:
        log = RouteLog(bus.directory)
    results = []
    for event in bus.pending(consumer):
        record = log.get(event["id"])
        if record is None:
            record, _ = log.record(route_event(event, rules), routed_at=routed_at)
        bus.acknowledge(consumer, event["id"])
        results.append(record)
    return results


def route_reason(event_id: str, log=None, bus=None) -> dict | None:
    """Look up a persisted route decision by event id."""
    from .route_log import RouteLog

    if log is None:
        log = RouteLog(bus.directory) if bus is not None else RouteLog()
    return log.get(event_id)
