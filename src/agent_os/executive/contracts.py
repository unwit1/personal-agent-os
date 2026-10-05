"""Executive Core contracts: typed entities, events, and queue items.

Validates and generates stable identifiers for executive objects following
schemas in schemas/executive-*-v1.schema.json.
"""

from __future__ import annotations

import hashlib
import re
from datetime import datetime
from typing import Any

ENTITY_SCHEMA = "personal-agent/executive-entity/v1"
EVENT_SCHEMA = "personal-agent/executive-event/v1"
QUEUE_ITEM_SCHEMA = "personal-agent/executive-queue-item/v1"

ENTITY_KINDS = {
    "task",
    "commitment",
    "project",
    "next_action",
    "blocker",
    "waiting_on",
    "decision_request",
    "question",
    "idea",
    "appointment",
    "communication",
    "attention_state",
    "outcome",
}

EVENT_TYPES = {
    "conversation.completed",
    "idea.captured",
    "task.created",
    "task.completed",
    "task.deferred",
    "project.modified",
    "project.stalled",
    "decision.required",
    "decision.made",
    "agent.blocked",
    "agent.completed",
    "appointment.created",
    "appointment.approaching",
    "communication.received",
    "communication.needs_response",
    "preference.observed",
    "skill.used",
    "skill.failed",
    "outcome.recorded",
    "context.changed",
}

AUTONOMY_LEVELS = {"OBSERVE", "SUGGEST", "PREPARE", "ASK_THEN_ACT", "AUTO_ACT"}

SENSITIVITIES = {"public", "personal", "sensitive", "secret"}

ENTITY_STATUSES = {"open", "active", "waiting", "deferred", "done", "cancelled", "superseded"}

QUEUE_STATUSES = {"queued", "presented", "accepted", "rejected", "deferred", "completed", "cancelled"}

_ENTITY_ID = re.compile(r"^ex-[a-z_]+-[0-9a-f]{16}$")
_EVENT_ID = re.compile(r"^evt-[0-9a-f]{16}$")
_QUEUE_ITEM_ID = re.compile(r"^qi-[0-9a-f]{16}$")


def stable_id(prefix: str, *parts: str) -> str:
    """Generate stable ID from prefix and parts."""
    joined = "\x1f".join(parts)
    digest = hashlib.sha256(joined.encode()).hexdigest()[:16]
    return f"{prefix}-{digest}"


def entity_id(kind: str, source: str, key: str) -> str:
    """Generate entity ID, raising ValueError for unknown kind."""
    if kind not in ENTITY_KINDS:
        raise ValueError(f"unknown entity kind: {kind}")
    return stable_id(f"ex-{kind}", source, key)


def event_id(event_type: str, source: str, dedup_key: str) -> str:
    """Generate event ID."""
    return stable_id("evt", event_type, source, dedup_key)


def queue_item_id(entity_id_val: str) -> str:
    """Generate queue item ID from entity ID."""
    return stable_id("qi", entity_id_val)


def requires_local_only(sensitivity: str) -> bool:
    """Check if sensitivity level requires local_only=true."""
    return sensitivity in {"sensitive", "secret"}


def _parse_timestamp(ts: Any) -> tuple[bool, str | None]:
    """Parse ISO 8601 timestamp, return (success, error_msg)."""
    if ts is None:
        return True, None
    if not isinstance(ts, str):
        return False, f"timestamp is not a string: {type(ts).__name__}"
    try:
        # Handle trailing 'Z' (UTC designator)
        normalized = ts.rstrip("Z") + "+00:00" if ts.endswith("Z") else ts
        datetime.fromisoformat(normalized)
        return True, None
    except (ValueError, TypeError) as e:
        return False, f"invalid timestamp {ts!r}: {e}"


def validate_entity(data: Any, label: str = "entity") -> list[str]:
    """Validate entity record, returning list of error strings."""
    if not isinstance(data, dict):
        return [f"{label}: not a JSON object"]

    errors = []
    required = {"schema", "id", "kind", "title", "status", "created_at", "updated_at", "source", "domain", "sensitivity", "provenance"}
    missing = sorted(required - data.keys())
    if missing:
        errors.append(f"{label}: missing {', '.join(missing)}")
        return errors  # Can't validate further without required fields

    if data.get("schema") != ENTITY_SCHEMA:
        errors.append(f"{label}: schema must be {ENTITY_SCHEMA}")

    # Validate ID format and kind consistency
    entity_id_str = data.get("id", "")
    if not _ENTITY_ID.match(str(entity_id_str)):
        errors.append(f"{label}: invalid id {entity_id_str!r}")
    else:
        # Extract kind from id: ex-{kind}-{hash}
        parts = str(entity_id_str).split("-", 2)
        if len(parts) >= 2:
            id_kind = parts[1]
            if id_kind != data.get("kind"):
                errors.append(f"{label}: id kind segment {id_kind!r} does not match kind {data.get('kind')!r}")

    if data.get("kind") not in ENTITY_KINDS:
        errors.append(f"{label}: unknown kind {data.get('kind')!r}")

    if not data.get("title"):
        errors.append(f"{label}: title must be non-empty")

    if data.get("status") not in ENTITY_STATUSES:
        errors.append(f"{label}: unknown status {data.get('status')!r}")

    # Validate timestamps
    for ts_field in ["created_at", "updated_at", "last_confirmed", "expires_at"]:
        if ts_field in data and data[ts_field] is not None:
            success, error_msg = _parse_timestamp(data[ts_field])
            if not success:
                errors.append(f"{label}: {ts_field} {error_msg}")

    if data.get("sensitivity") not in SENSITIVITIES:
        errors.append(f"{label}: unknown sensitivity {data.get('sensitivity')!r}")

    # Validate source and domain
    if not data.get("source"):
        errors.append(f"{label}: source must be non-empty")
    if not data.get("domain"):
        errors.append(f"{label}: domain must be non-empty")

    # Validate confidence in [0, 1] or None
    confidence = data.get("confidence")
    if confidence is not None:
        if not isinstance(confidence, (int, float)) or confidence < 0 or confidence > 1:
            errors.append(f"{label}: confidence must be in [0, 1] or None")

    # Validate provenance (non-empty list of strings)
    provenance = data.get("provenance", [])
    if not isinstance(provenance, list):
        errors.append(f"{label}: provenance must be a list")
    elif not provenance:
        errors.append(f"{label}: provenance must be non-empty")
    elif not all(isinstance(item, str) for item in provenance):
        errors.append(f"{label}: provenance must be a list of strings")

    # Validate superseded_by when status is superseded
    if data.get("status") == "superseded":
        if not data.get("superseded_by"):
            errors.append(f"{label}: status 'superseded' requires non-empty superseded_by")

    # Validate local_only requirement for sensitive/secret
    if requires_local_only(data.get("sensitivity", "")):
        if not data.get("local_only"):
            errors.append(f"{label}: sensitivity {data.get('sensitivity')!r} requires local_only=true")

    return errors


def validate_event(data: Any, label: str = "event") -> list[str]:
    """Validate event record, returning list of error strings."""
    if not isinstance(data, dict):
        return [f"{label}: not a JSON object"]

    errors = []
    required = {"schema", "id", "type", "occurred_at", "source", "domain", "sensitivity", "dedup_key", "payload"}
    missing = sorted(required - data.keys())
    if missing:
        errors.append(f"{label}: missing {', '.join(missing)}")
        return errors

    if data.get("schema") != EVENT_SCHEMA:
        errors.append(f"{label}: schema must be {EVENT_SCHEMA}")

    # Validate ID format
    event_id_str = data.get("id", "")
    if not _EVENT_ID.match(str(event_id_str)):
        errors.append(f"{label}: invalid id {event_id_str!r}")

    if data.get("type") not in EVENT_TYPES:
        errors.append(f"{label}: unknown type {data.get('type')!r}")

    # Validate timestamps
    success, error_msg = _parse_timestamp(data.get("occurred_at"))
    if not success:
        errors.append(f"{label}: occurred_at {error_msg}")

    if data.get("sensitivity") not in SENSITIVITIES:
        errors.append(f"{label}: unknown sensitivity {data.get('sensitivity')!r}")

    # Validate source and domain
    if not data.get("source"):
        errors.append(f"{label}: source must be non-empty")
    if not data.get("domain"):
        errors.append(f"{label}: domain must be non-empty")

    # Validate dedup_key
    if not data.get("dedup_key"):
        errors.append(f"{label}: dedup_key must be non-empty")

    # Validate payload is a dict
    if not isinstance(data.get("payload"), dict):
        errors.append(f"{label}: payload must be a JSON object")

    # Validate provenance (optional, but if present should be list of strings)
    if "provenance" in data:
        provenance = data.get("provenance", [])
        if not isinstance(provenance, list):
            errors.append(f"{label}: provenance must be a list")
        elif provenance and not all(isinstance(item, str) for item in provenance):
            errors.append(f"{label}: provenance must be a list of strings")

    # Validate local_only requirement for sensitive/secret
    if requires_local_only(data.get("sensitivity", "")):
        if not data.get("local_only"):
            errors.append(f"{label}: sensitivity {data.get('sensitivity')!r} requires local_only=true")

    return errors


def validate_queue_item(data: Any, label: str = "queue_item") -> list[str]:
    """Validate queue item record, returning list of error strings."""
    if not isinstance(data, dict):
        return [f"{label}: not a JSON object"]

    errors = []
    required = {"schema", "id", "entity_id", "queued_at", "source", "domain", "sensitivity"}
    missing = sorted(required - data.keys())
    if missing:
        errors.append(f"{label}: missing {', '.join(missing)}")
        return errors

    if data.get("schema") != QUEUE_ITEM_SCHEMA:
        errors.append(f"{label}: schema must be {QUEUE_ITEM_SCHEMA}")

    # Validate ID format
    queue_item_id_str = data.get("id", "")
    if not _QUEUE_ITEM_ID.match(str(queue_item_id_str)):
        errors.append(f"{label}: invalid id {queue_item_id_str!r}")

    # Validate entity_id format
    entity_id_str = data.get("entity_id", "")
    if not _ENTITY_ID.match(str(entity_id_str)):
        errors.append(f"{label}: invalid entity_id {entity_id_str!r}")

    # Validate timestamp
    success, error_msg = _parse_timestamp(data.get("queued_at"))
    if not success:
        errors.append(f"{label}: queued_at {error_msg}")

    if data.get("sensitivity") not in SENSITIVITIES:
        errors.append(f"{label}: unknown sensitivity {data.get('sensitivity')!r}")

    # Validate source and domain
    if not data.get("source"):
        errors.append(f"{label}: source must be non-empty")
    if not data.get("domain"):
        errors.append(f"{label}: domain must be non-empty")

    # Validate optional timestamps
    for ts_field in ["deadline"]:
        if ts_field in data and data[ts_field] is not None:
            success, error_msg = _parse_timestamp(data[ts_field])
            if not success:
                errors.append(f"{label}: {ts_field} {error_msg}")

    # Validate priority (optional, but if present should be >= 0)
    priority = data.get("priority")
    if priority is not None:
        if not isinstance(priority, (int, float)) or priority < 0:
            errors.append(f"{label}: priority must be >= 0 or None")

    # Validate importance in [0, 1] or None
    importance = data.get("importance")
    if importance is not None:
        if not isinstance(importance, (int, float)) or importance < 0 or importance > 1:
            errors.append(f"{label}: importance must be in [0, 1] or None")

    # Validate blocking_impact in [0, 1] or None
    blocking_impact = data.get("blocking_impact")
    if blocking_impact is not None:
        if not isinstance(blocking_impact, (int, float)) or blocking_impact < 0 or blocking_impact > 1:
            errors.append(f"{label}: blocking_impact must be in [0, 1] or None")

    # Validate urgency enum (optional)
    if "urgency" in data:
        urgency = data.get("urgency")
        if urgency is not None and urgency not in {"critical", "high", "normal", "low"}:
            errors.append(f"{label}: unknown urgency {urgency!r}")

    # Validate estimated_effort (optional string)
    if "estimated_effort" in data:
        estimated_effort = data.get("estimated_effort")
        if estimated_effort is not None and not isinstance(estimated_effort, str):
            errors.append(f"{label}: estimated_effort must be a string or None")

    # Validate repeated_deferrals (optional, >= 0 if present)
    if "repeated_deferrals" in data:
        repeated_deferrals = data.get("repeated_deferrals")
        if repeated_deferrals is not None:
            if not isinstance(repeated_deferrals, int) or repeated_deferrals < 0:
                errors.append(f"{label}: repeated_deferrals must be >= 0 or None")

    # Validate interruption_cost (optional, >= 0 if present)
    if "interruption_cost" in data:
        interruption_cost = data.get("interruption_cost")
        if interruption_cost is not None:
            if not isinstance(interruption_cost, (int, float)) or interruption_cost < 0:
                errors.append(f"{label}: interruption_cost must be >= 0 or None")

    # Validate status enum
    if data.get("status") not in QUEUE_STATUSES:
        errors.append(f"{label}: unknown status {data.get('status')!r}")

    # Validate provenance (optional)
    if "provenance" in data:
        provenance = data.get("provenance", [])
        if not isinstance(provenance, list):
            errors.append(f"{label}: provenance must be a list")
        elif provenance and not all(isinstance(item, str) for item in provenance):
            errors.append(f"{label}: provenance must be a list of strings")

    # Validate local_only requirement for sensitive/secret
    if requires_local_only(data.get("sensitivity", "")):
        if not data.get("local_only"):
            errors.append(f"{label}: sensitivity {data.get('sensitivity')!r} requires local_only=true")

    return errors
