"""Window item to/from EXEC-0 queue item conversion and publishing."""

from __future__ import annotations

import copy
from datetime import datetime, timezone
from typing import Any

from . import contracts

DEFERRAL_THRESHOLD = 3


def queue_item_from_window_item(
    item: dict, provider: str, queued_at: str | None = None
) -> dict:
    """Convert a window item to an EXEC-0 queue item.

    Args:
        item: window item dict with id, title, kind, tab, why (optional),
              score (optional), sensitivity (optional), and other fields
        provider: provider name (used to construct source)
        queued_at: ISO timestamp for when queued (defaults to now)

    Returns:
        Valid EXEC-0 queue item dict with required schema, id, entity_id, etc.
    """
    if queued_at is None:
        queued_at = datetime.now(timezone.utc).isoformat()

    entity_id_val = contracts.entity_id("task", f"window:{provider}", str(item.get("id")))
    queue_item_id_val = contracts.queue_item_id(entity_id_val)

    sensitivity = item.get("sensitivity", "personal")
    if not isinstance(sensitivity, str) or sensitivity not in contracts.SENSITIVITIES:
        sensitivity = "personal"

    queue_item: dict[str, Any] = {
        "schema": contracts.QUEUE_ITEM_SCHEMA,
        "id": queue_item_id_val,
        "entity_id": entity_id_val,
        "queued_at": queued_at,
        "source": f"window:{provider}",
        "domain": "executive-window",
        "sensitivity": sensitivity,
        "status": "queued",
        "provider": provider,
        "window_item": copy.deepcopy(item),
    }

    if contracts.requires_local_only(sensitivity):
        queue_item["local_only"] = True

    reason = item.get("why")
    if isinstance(reason, str):
        queue_item["reason"] = reason

    score = item.get("score")
    if isinstance(score, (int, float)) and not isinstance(score, bool) and score >= 0:
        queue_item["priority"] = score

    errors = contracts.validate_queue_item(queue_item)
    if errors:
        raise ValueError("\n".join(errors))

    return queue_item


def window_item_from_queue_item(queue_item: dict) -> dict:
    """Convert an EXEC-0 queue item back to a window item.

    Args:
        queue_item: EXEC-0 queue item dict with window_item and optional reason

    Returns:
        Window item dict (deep copy from queue_item['window_item']).
        If queue_item has a reason, sets window_item['why'] to that reason.
    """
    out = copy.deepcopy(queue_item.get("window_item", {}))

    reason = queue_item.get("reason")
    if reason is not None:
        out["why"] = reason

    return out


def publish_window_item(
    bus: Any, item: dict, provider: str, queue_item: dict | None = None
) -> tuple[dict[str, Any], bool]:
    """Publish a window item as a task.created event with queue item payload.

    The event log persists on disk, so the payload carries identifiers only:
    never the item's title, why or other text, which can hold applicant names
    or mail subjects.

    Args:
        bus: EventBus instance with publish method
        item: window item dict
        provider: provider name
        queue_item: the item's already-built queue item, to avoid converting twice

    Returns:
        Tuple of (event dict, created bool) from bus.publish()
    """
    qi = queue_item if queue_item is not None else queue_item_from_window_item(item, provider)

    event, created = bus.publish(
        "task.created",
        f"window:{provider}",
        str(item.get("id")),
        payload={
            "queue_item_id": qi["id"],
            "entity_id": qi["entity_id"],
            "provider": provider,
            "item_id": str(item.get("id")),
            "kind": item.get("kind"),
            "tab": item.get("tab"),
        },
        domain=qi["domain"],
        sensitivity=qi["sensitivity"],
        subject=qi["entity_id"],
    )

    return event, created


def publish_deferral(
    bus: Any,
    entity_id: str,
    item_id: str,
    deferred_at: str | None = None,
    until: str | None = None,
) -> tuple[dict[str, Any], bool]:
    """Publish an identifier-only task deferral event."""
    if deferred_at is None:
        deferred_at = datetime.now(timezone.utc).isoformat()

    return bus.publish(
        "task.deferred",
        "window:snooze",
        f"{entity_id}:{deferred_at}",
        payload={
            "entity_id": entity_id,
            "item_id": item_id,
            "deferred_at": deferred_at,
            "until": until,
        },
        domain="executive-window",
        sensitivity="personal",
        subject=entity_id,
    )


def publish_status_change(
    bus: Any,
    entity_id: str,
    item_id: str,
    status: str,
    changed_at: str | None = None,
) -> tuple[dict[str, Any], bool]:
    """Publish an identifier-only completion or cancellation event."""
    if status not in ("completed", "cancelled"):
        raise ValueError("status must be 'completed' or 'cancelled'")
    if changed_at is None:
        changed_at = datetime.now(timezone.utc).isoformat()

    return bus.publish(
        f"task.{status}",
        "window:status",
        f"{entity_id}:{status}:{changed_at}",
        payload={
            "entity_id": entity_id,
            "item_id": item_id,
            "status": status,
            "changed_at": changed_at,
        },
        domain="executive-window",
        sensitivity="personal",
        subject=entity_id,
    )


def queue_statuses(bus: Any, now: datetime | None = None) -> dict[str, str]:
    """Return the latest deferred/completed/cancelled status per entity."""
    if bus is None:
        return {}
    if now is None:
        now = datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)

    statuses: dict[str, str] = {}
    event_statuses = {
        "task.deferred": "deferred",
        "task.completed": "completed",
        "task.cancelled": "cancelled",
    }
    for event in bus.events():
        status = event_statuses.get(event.get("type"))
        subject = event.get("subject")
        if status is None or not isinstance(subject, str) or not subject:
            continue
        if status == "deferred":
            until = event.get("payload", {}).get("until")
            if isinstance(until, str):
                try:
                    until_dt = datetime.fromisoformat(until)
                    if until_dt.tzinfo is None:
                        until_dt = until_dt.replace(tzinfo=timezone.utc)
                    if until_dt <= now:
                        status = "queued"
                except ValueError:
                    pass
        statuses[subject] = status
    return statuses


def deferral_counts(bus: Any) -> dict[str, int]:
    """Count task deferrals by non-empty event subject."""
    if bus is None:
        return {}

    counts: dict[str, int] = {}
    for event in bus.events(event_type="task.deferred"):
        subject = event.get("subject")
        if isinstance(subject, str) and subject:
            counts[subject] = counts.get(subject, 0) + 1
    return counts


def project_deferral_counts(bus: Any) -> dict[str, int]:
    """Count task deferrals by project id from project window item ids."""
    if bus is None:
        return {}

    counts: dict[str, int] = {}
    for event in bus.events(event_type="task.deferred"):
        payload = event.get("payload", {})
        if not isinstance(payload, dict):
            continue
        item_id = payload.get("item_id")
        if not isinstance(item_id, str):
            continue
        parts = item_id.split(":", 2)
        if len(parts) != 3 or parts[0] != "project" or not parts[1]:
            continue
        counts[parts[1]] = counts.get(parts[1], 0) + 1
    return counts
