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


PROVIDER_USAGE_FORMATS = ("anthropic", "openai-chat", "openai-responses", "normalized")

REPORT_SCHEMA = "personal-agent/telemetry-report/v1"
REPORT_GROUP_FIELDS = {
    "project": "project_id",
    "category": "task_category",
    "provider": "provider",
    "model": "model",
    "capability": "capability_class",
    "path": "execution_path",
}


def token_counts_from_provider_usage(
    usage: Mapping[str, Any] | None, usage_format: str
) -> dict[str, int | None]:
    """Extract and normalize token counts from provider usage data.

    Extracts token counts from provider-specific usage dictionaries and normalizes
    them to a standard schema. Returns a dict with exactly the keys:
    input_tokens, cached_tokens, reasoning_tokens, output_tokens.

    Args:
        usage: Provider usage dict, or None. If it contains a "usage" key with a
            Mapping value, that inner dict is used and all other keys are ignored.
        usage_format: One of PROVIDER_USAGE_FORMATS. Determines the mapping rules.

    Returns:
        Dict with keys: input_tokens, cached_tokens, reasoning_tokens, output_tokens.
        Values are non-negative integers or None. Missing, invalid, boolean, or
        negative values become None. The function never estimates.

    Raises:
        TelemetryPrivacyError: If usage_format is not in PROVIDER_USAGE_FORMATS.
    """
    if usage_format not in PROVIDER_USAGE_FORMATS:
        raise TelemetryPrivacyError(
            f"unsupported provider usage format {usage_format!r}; "
            f"must be one of {', '.join(PROVIDER_USAGE_FORMATS)}"
        )

    if not usage or not isinstance(usage, Mapping):
        return {
            "input_tokens": None,
            "cached_tokens": None,
            "reasoning_tokens": None,
            "output_tokens": None,
        }

    def _valid_int(value: Any) -> int | None:
        return value if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else None

    payload = usage
    if isinstance(usage.get("usage"), Mapping):
        payload = usage["usage"]

    if usage_format == "normalized":
        if payload.get("accuracy") != "exact":
            return {
                "input_tokens": None,
                "cached_tokens": None,
                "reasoning_tokens": None,
                "output_tokens": None,
            }

        cached = _valid_int(payload.get("cache_read_tokens"))
        if cached is None:
            cached = _valid_int(payload.get("cached_tokens"))

        return {
            "input_tokens": _valid_int(payload.get("input_tokens")),
            "cached_tokens": cached,
            "reasoning_tokens": _valid_int(payload.get("reasoning_tokens")),
            "output_tokens": _valid_int(payload.get("output_tokens")),
        }

    if usage_format == "anthropic":
        base = _valid_int(payload.get("input_tokens"))
        if base is None:
            input_tokens = None
            cached_tokens = None
        else:
            cache_read = _valid_int(payload.get("cache_read_input_tokens")) or 0
            cache_creation = _valid_int(payload.get("cache_creation_input_tokens")) or 0
            input_tokens = base + cache_read + cache_creation
            cached = _valid_int(payload.get("cache_read_input_tokens"))
            cached_tokens = cached if cached is not None else 0

        return {
            "input_tokens": input_tokens,
            "cached_tokens": cached_tokens,
            "reasoning_tokens": None,
            "output_tokens": _valid_int(payload.get("output_tokens")),
        }

    if usage_format == "openai-chat":
        return {
            "input_tokens": _valid_int(payload.get("prompt_tokens")),
            "cached_tokens": _valid_int(
                payload.get("prompt_tokens_details", {}).get("cached_tokens")
                if isinstance(payload.get("prompt_tokens_details"), Mapping)
                else None
            ),
            "reasoning_tokens": _valid_int(
                payload.get("completion_tokens_details", {}).get("reasoning_tokens")
                if isinstance(payload.get("completion_tokens_details"), Mapping)
                else None
            ),
            "output_tokens": _valid_int(payload.get("completion_tokens")),
        }

    if usage_format == "openai-responses":
        return {
            "input_tokens": _valid_int(payload.get("input_tokens")),
            "cached_tokens": _valid_int(
                payload.get("input_tokens_details", {}).get("cached_tokens")
                if isinstance(payload.get("input_tokens_details"), Mapping)
                else None
            ),
            "reasoning_tokens": _valid_int(
                payload.get("output_tokens_details", {}).get("reasoning_tokens")
                if isinstance(payload.get("output_tokens_details"), Mapping)
                else None
            ),
            "output_tokens": _valid_int(payload.get("output_tokens")),
        }

    return {
        "input_tokens": None,
        "cached_tokens": None,
        "reasoning_tokens": None,
        "output_tokens": None,
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


def _aggregate(
    events: list[TelemetryEvent], *, oversized_input_tokens: int | None = None
) -> dict[str, Any]:
    """Compute ungrouped aggregates from validated events."""

    if oversized_input_tokens is not None:
        if not isinstance(oversized_input_tokens, int) or isinstance(oversized_input_tokens, bool):
            raise ValueError("oversized_input_tokens must be an int, not bool")
        if oversized_input_tokens < 1:
            raise ValueError("oversized_input_tokens must be >= 1")

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
    input_tokens_max: int | None = None

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

        if event.input_tokens is not None:
            if input_tokens_max is None or event.input_tokens > input_tokens_max:
                input_tokens_max = event.input_tokens

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
        "input_tokens_max": input_tokens_max,
    }


def aggregate_report(
    events: Iterable[TelemetryEvent | Mapping[str, Any]],
    group_by: str | None = None,
    *,
    oversized_input_tokens: int | None = None,
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
        oversized_input_tokens: Optional validation threshold. Must be an int >= 1
            if provided. Raises ValueError if not an int or if < 1.

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
    - input_tokens_max: largest non-None input_tokens value, or None
    - group_rankings: (only when group_by is not None) dict with three keys:
      - model_tokens: list of {group, value} dicts sorted by value desc, then label asc
      - retries_and_escalations: list of {group, value} dicts sorted by value desc, then label asc
      - model_path_events: list of {group, value} dicts sorted by value desc, then label asc
      Groups with value 0 are excluded.
    """

    validated_events: list[TelemetryEvent] = []
    for item in events:
        event = item if isinstance(item, TelemetryEvent) else TelemetryEvent.from_mapping(item)
        validated_events.append(event)

    if group_by is None:
        return _aggregate(validated_events, oversized_input_tokens=oversized_input_tokens)

    if group_by not in REPORT_GROUP_FIELDS:
        raise ValueError(f"unsupported telemetry report grouping: {group_by}")

    field_name = REPORT_GROUP_FIELDS[group_by]
    groups_dict: dict[str | None, list[TelemetryEvent]] = {}
    for event in validated_events:
        label = getattr(event, field_name) or "unknown"
        if label not in groups_dict:
            groups_dict[label] = []
        groups_dict[label].append(event)

    top_level_report = _aggregate(validated_events, oversized_input_tokens=oversized_input_tokens)
    groups_report = {}
    group_rankings_data = {
        "model_tokens": {},
        "retries_and_escalations": {},
        "model_path_events": {},
    }

    for label in sorted(groups_dict.keys()):
        group_events = groups_dict[label]
        group_aggregate = _aggregate(group_events, oversized_input_tokens=oversized_input_tokens)
        group_aggregate.pop("schema", None)
        groups_report[label] = group_aggregate

        # Compute ranking metrics
        model_tokens = (
            group_aggregate["token_totals"]["input_tokens"]
            + group_aggregate["token_totals"]["reasoning_tokens"]
            + group_aggregate["token_totals"]["output_tokens"]
        )
        if model_tokens > 0:
            group_rankings_data["model_tokens"][label] = model_tokens

        retries_and_escalations = (
            group_aggregate["retry_total"] + group_aggregate["escalation_total"]
        )
        if retries_and_escalations > 0:
            group_rankings_data["retries_and_escalations"][label] = retries_and_escalations

        model_path_events = group_aggregate["execution_path_counts"].get("model", 0)
        if model_path_events > 0:
            group_rankings_data["model_path_events"][label] = model_path_events

    # Sort rankings
    group_rankings = {}
    for key in ("model_tokens", "retries_and_escalations", "model_path_events"):
        items = group_rankings_data[key]
        sorted_items = sorted(items.items(), key=lambda x: (-x[1], x[0]))
        group_rankings[key] = [{"group": label, "value": value} for label, value in sorted_items]

    top_level_report["group_by"] = group_by
    top_level_report["groups"] = groups_report
    top_level_report["group_rankings"] = group_rankings

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

    def aggregate_report(
        self, group_by: str | None = None, *, oversized_input_tokens: int | None = None
    ) -> dict[str, Any]:
        """Summarize local events without exposing the underlying records."""

        return aggregate_report(
            self.read_events(), group_by=group_by, oversized_input_tokens=oversized_input_tokens
        )
