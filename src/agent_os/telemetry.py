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
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from .paths import ROOT


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


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


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


def assert_private_location(path: Path) -> None:
    """Reject canonical repository paths outside the gitignored local tree."""

    resolved = Path(path).expanduser().resolve()
    repository = ROOT.resolve()
    try:
        relative = resolved.relative_to(repository)
    except ValueError:
        return
    if not relative.parts or relative.parts[0] != ".agent-local":
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
