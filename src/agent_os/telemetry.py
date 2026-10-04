"""Privacy-safe local telemetry for Agent-OS-controlled work.

This first telemetry slice deliberately accepts only compact labels, counts,
booleans, and timestamps. It does not provide a generic metadata escape hatch:
raw prompts, documents, OCR, messages, identities, and credentials are rejected
before they can reach the local event log.
"""

from __future__ import annotations

import json
import os
import re
import uuid
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

from .local_paths import is_gitignored_local_path
from .paths import ROOT
from .timestamps import utc_now_iso as _utc_now


SCHEMA_VERSION = 1
LOCAL_RUNTIME_DIR = ROOT / ".agent-local"
TELEMETRY_DIR = LOCAL_RUNTIME_DIR / "telemetry"
DEFAULT_PATH = TELEMETRY_DIR / "events.jsonl"

_LABEL = re.compile(r"^[a-z0-9][a-z0-9_.-]{0,63}$")
_EVENT_ID = re.compile(r"^[a-z0-9][a-z0-9_.-]{0,95}$")
_SENSITIVE_FIELD = re.compile(
    r"(?:prompt|document|ocr|message|password|secret|credential|access[_-]?token|"
    r"api[_-]?key|email|address|employee|applicant|payroll|raw|body|text|content)",
    re.IGNORECASE,
)
_SECRET_VALUE = re.compile(
    r"(?:api[_-]?key|access[_-]?token|password|secret)\s*[:=]|"
    r"(?:gh[pousr]_|github_pat_|sk-[A-Za-z0-9])",
    re.IGNORECASE,
)

_COUNT_FIELDS = frozenset(
    {
        "input_tokens",
        "cached_tokens",
        "reasoning_tokens",
        "output_tokens",
        "duration_ms",
        "retries",
        "items_processed",
        "escalations",
    }
)
_LABEL_FIELDS = frozenset(
    {
        "event_id",
        "project_id",
        "task_category",
        "capability_class",
        "execution_path",
        "provider",
        "model",
    }
)
_OPTIONAL_FIELDS = _COUNT_FIELDS | _LABEL_FIELDS | {
    "validator_passed",
    "correction_or_override",
}
_ALLOWED_FIELDS = {"schema_version", "occurred_at"} | _OPTIONAL_FIELDS
_SERIALIZED_OPTIONAL_FIELDS = (
    "capability_class",
    "execution_path",
    "provider",
    "model",
    "input_tokens",
    "cached_tokens",
    "reasoning_tokens",
    "output_tokens",
    "duration_ms",
    "retries",
    "items_processed",
    "validator_passed",
    "escalations",
    "correction_or_override",
)


class TelemetryPrivacyError(ValueError):
    """Raised when an event is not representable as safe metadata."""


REPORT_SCHEMA = "personal-agent/telemetry-report/v1"
REPORT_GROUP_FIELDS = {
    "project": "project_id",
    "category": "task_category",
    "provider": "provider",
    "model": "model",
    "capability": "capability_class",
    "path": "execution_path",
}


def _check_string(field_name: str, value: str, *, event_id: bool = False) -> str:
    if not isinstance(value, str) or not value:
        raise TelemetryPrivacyError(f"telemetry {field_name} must be a non-empty string")
    if _SECRET_VALUE.search(value) or any(character.isspace() for character in value):
        raise TelemetryPrivacyError(f"telemetry {field_name} must be a compact non-sensitive label")
    pattern = _EVENT_ID if event_id else _LABEL
    if not pattern.fullmatch(value.casefold()):
        raise TelemetryPrivacyError(f"telemetry {field_name} is not a permitted label")
    return value


def _check_timestamp(value: str) -> str:
    if not isinstance(value, str):
        raise TelemetryPrivacyError("telemetry occurred_at must be an ISO timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise TelemetryPrivacyError("telemetry occurred_at must be an ISO timestamp") from exc
    if parsed.tzinfo is None:
        raise TelemetryPrivacyError("telemetry occurred_at must include a timezone")
    return value


def _check_count(field_name: str, value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise TelemetryPrivacyError(f"telemetry {field_name} must be a non-negative integer")
    return value


@dataclass(frozen=True)
class TelemetryEvent:
    """One metadata-only usage event.

    ``task_category`` is a category such as ``workflow-stage`` rather than a
    free-form task description. Optional fields are omitted from the serialized
    record when unavailable; unavailable provider/model usage is never guessed.
    """

    project_id: str
    task_category: str
    event_id: str = field(default_factory=lambda: f"event-{uuid.uuid4().hex}")
    occurred_at: str = field(default_factory=_utc_now)
    capability_class: str | None = None
    execution_path: str | None = None
    provider: str | None = None
    model: str | None = None
    input_tokens: int | None = None
    cached_tokens: int | None = None
    reasoning_tokens: int | None = None
    output_tokens: int | None = None
    duration_ms: int | None = None
    retries: int | None = None
    items_processed: int | None = None
    validator_passed: bool | None = None
    escalations: int | None = None
    correction_or_override: bool | None = None

    def __post_init__(self) -> None:
        _check_string("project_id", self.project_id)
        _check_string("task_category", self.task_category)
        _check_string("event_id", self.event_id, event_id=True)
        _check_timestamp(self.occurred_at)
        for name in ("capability_class", "execution_path", "provider", "model"):
            value = getattr(self, name)
            if value is not None:
                _check_string(name, value)
        for name in _COUNT_FIELDS:
            value = getattr(self, name)
            if value is not None:
                _check_count(name, value)
        for name in ("validator_passed", "correction_or_override"):
            value = getattr(self, name)
            if value is not None and not isinstance(value, bool):
                raise TelemetryPrivacyError(f"telemetry {name} must be boolean")

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "TelemetryEvent":
        """Build an event while rejecting unknown or privacy-sensitive fields."""

        if not isinstance(value, Mapping):
            raise TelemetryPrivacyError("telemetry event must be an object")
        sensitive = sorted(key for key in value if _SENSITIVE_FIELD.search(str(key)))
        if sensitive:
            raise TelemetryPrivacyError(
                "telemetry rejects private fields: " + ", ".join(sensitive)
            )
        unknown = sorted(set(value) - _ALLOWED_FIELDS)
        if unknown:
            raise TelemetryPrivacyError(
                "telemetry rejects unsupported fields: " + ", ".join(map(str, unknown))
            )
        payload = dict(value)
        payload.setdefault("schema_version", SCHEMA_VERSION)
        if payload["schema_version"] != SCHEMA_VERSION:
            raise TelemetryPrivacyError("unsupported telemetry schema version")
        payload.pop("schema_version", None)
        return cls(**payload)

    def as_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "schema_version": SCHEMA_VERSION,
            "event_id": self.event_id,
            "occurred_at": self.occurred_at,
            "project_id": self.project_id,
            "task_category": self.task_category,
        }
        for name in _SERIALIZED_OPTIONAL_FIELDS:
            value = getattr(self, name)
            if value is not None:
                payload[name] = value
        return payload


def _aggregate(events: list[TelemetryEvent]) -> dict[str, Any]:
    """Compute ungrouped aggregates from validated events."""

    execution_paths: Counter[str] = Counter()
    validator_outcomes: Counter[str] = Counter()
    capability_classes: Counter[str] = Counter()
    deterministic_path_classes: Counter[str] = Counter()
    token_totals = {
        "input_tokens": 0,
        "cached_tokens": 0,
        "reasoning_tokens": 0,
        "output_tokens": 0,
    }
    token_unknown_counts = {
        "input_tokens": 0,
        "cached_tokens": 0,
        "reasoning_tokens": 0,
        "output_tokens": 0,
    }
    total = 0
    retry_total = 0
    escalation_total = 0
    events_with_retries = 0
    events_with_escalations = 0
    retry_unknown_count = 0
    escalation_unknown_count = 0
    duration_ms_total = 0
    duration_unknown_count = 0
    items_processed_total = 0
    items_processed_unknown_count = 0
    correction_or_override_counts = {"false": 0, "true": 0, "unknown": 0}

    for event in events:
        total += 1
        execution_paths[event.execution_path or "unknown"] += 1
        capability_classes[event.capability_class or "unknown"] += 1

        if event.validator_passed is True:
            validator_outcomes["passed"] += 1
        elif event.validator_passed is False:
            validator_outcomes["failed"] += 1
        else:
            validator_outcomes["unknown"] += 1

        if event.retries is not None:
            retry_total += event.retries
            if event.retries > 0:
                events_with_retries += 1
        else:
            retry_unknown_count += 1

        if event.escalations is not None:
            escalation_total += event.escalations
            if event.escalations > 0:
                events_with_escalations += 1
        else:
            escalation_unknown_count += 1

        if event.duration_ms is not None:
            duration_ms_total += event.duration_ms
        else:
            duration_unknown_count += 1

        if event.items_processed is not None:
            items_processed_total += event.items_processed
        else:
            items_processed_unknown_count += 1

        if event.correction_or_override is True:
            correction_or_override_counts["true"] += 1
        elif event.correction_or_override is False:
            correction_or_override_counts["false"] += 1
        else:
            correction_or_override_counts["unknown"] += 1

        for token_field in ("input_tokens", "cached_tokens", "reasoning_tokens", "output_tokens"):
            value = getattr(event, token_field)
            if value is not None:
                token_totals[token_field] += value
            else:
                token_unknown_counts[token_field] += 1

        if (
            event.execution_path in ("deterministic", "cache")
            and event.capability_class is not None
            and event.capability_class != "deterministic"
        ):
            deterministic_path_classes[event.capability_class] += 1

    return {
        "schema": REPORT_SCHEMA,
        "event_count": total,
        "execution_path_counts": dict(sorted(execution_paths.items())),
        "validator_outcome_counts": dict(sorted(validator_outcomes.items())),
        "capability_class_counts": dict(sorted(capability_classes.items())),
        "retry_total": retry_total,
        "escalation_total": escalation_total,
        "events_with_retries": events_with_retries,
        "events_with_escalations": events_with_escalations,
        "retry_unknown_count": retry_unknown_count,
        "escalation_unknown_count": escalation_unknown_count,
        "duration_ms_total": duration_ms_total,
        "duration_unknown_count": duration_unknown_count,
        "items_processed_total": items_processed_total,
        "items_processed_unknown_count": items_processed_unknown_count,
        "correction_or_override_counts": correction_or_override_counts,
        "deterministic_path_model_class_counts": dict(sorted(deterministic_path_classes.items())),
        "token_totals": token_totals,
        "token_unknown_counts": token_unknown_counts,
    }


def aggregate_report(
    events: Iterable[TelemetryEvent | Mapping[str, Any]], group_by: str | None = None
) -> dict[str, Any]:
    """Return count-only usage findings from validated metadata events.

    The report intentionally excludes event IDs, timestamps, projects,
    categories, providers, models, and all other per-event fields. ``None``
    means the source did not expose a metric and is counted as ``unknown``;
    it is never converted into a guessed value.

    Args:
        events: Validated metadata events to aggregate.
        group_by: Optional grouping field. None for ungrouped report. Must be
            a key of REPORT_GROUP_FIELDS if provided.

    New aggregates:
    - capability_class_counts: Counter of event.capability_class or 'unknown'
    - retry_total: sum of event.retries (None not counted)
    - escalation_total: sum of event.escalations (None not counted)
    - events_with_retries: count of events with retries > 0
    - events_with_escalations: count of events with escalations > 0
    - retry_unknown_count: count of events where retries is None
    - escalation_unknown_count: count of events where escalations is None
    - duration_ms_total: sum of event.duration_ms (None not counted, 0 when none)
    - duration_unknown_count: count of events where duration_ms is None
    - items_processed_total: sum of event.items_processed (None not counted)
    - items_processed_unknown_count: count of events where items_processed is None
    - correction_or_override_counts: dict with keys 'false', 'true', 'unknown' counting event.correction_or_override values
    - deterministic_path_model_class_counts: Counter of capability_class for events with
      execution_path in ('deterministic', 'cache') and capability_class set and not 'deterministic'
    - token_totals: dict of field -> int (sum of non-None values, 0 when nothing reported)
    - token_unknown_counts: dict of field -> int (count of None values)
    """

    validated_events: list[TelemetryEvent] = []
    for item in events:
        event = item if isinstance(item, TelemetryEvent) else TelemetryEvent.from_mapping(item)
        validated_events.append(event)

    if group_by is None:
        return _aggregate(validated_events)

    if group_by not in REPORT_GROUP_FIELDS:
        raise ValueError(f"unsupported telemetry report grouping: {group_by}")

    field_name = REPORT_GROUP_FIELDS[group_by]
    groups_dict: dict[str | None, list[TelemetryEvent]] = {}
    for event in validated_events:
        label = getattr(event, field_name) or "unknown"
        if label not in groups_dict:
            groups_dict[label] = []
        groups_dict[label].append(event)

    top_level_report = _aggregate(validated_events)
    groups_report = {}
    for label in sorted(groups_dict.keys()):
        group_events = groups_dict[label]
        group_aggregate = _aggregate(group_events)
        group_aggregate.pop("schema", None)
        groups_report[label] = group_aggregate

    top_level_report["group_by"] = group_by
    top_level_report["groups"] = groups_report

    return top_level_report


def assert_private_location(path: Path) -> None:
    """Reject canonical repository paths outside the gitignored local tree."""

    if not is_gitignored_local_path(path):
        raise TelemetryPrivacyError(
            "telemetry must remain outside canonical Git state or under .agent-local"
        )


class LocalTelemetryStore:
    """Append-only local JSONL store for validated metadata events."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = Path(path or DEFAULT_PATH).expanduser()
        assert_private_location(self.path)

    def record(self, event: TelemetryEvent | Mapping[str, Any]) -> TelemetryEvent:
        validated = event if isinstance(event, TelemetryEvent) else TelemetryEvent.from_mapping(event)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(validated.as_dict(), ensure_ascii=False, separators=(",", ":")) + "\n"
        with self.path.open("a", encoding="utf-8", newline="") as handle:
            handle.write(line)
            handle.flush()
            os.fsync(handle.fileno())
        return validated

    def read_events(self) -> list[TelemetryEvent]:
        if not self.path.exists():
            return []
        events: list[TelemetryEvent] = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                events.append(TelemetryEvent.from_mapping(json.loads(line)))
        return events

    def aggregate_report(self, group_by: str | None = None) -> dict[str, Any]:
        """Summarize local events without exposing the underlying records."""

        return aggregate_report(self.read_events(), group_by=group_by)
