"""Append-only local Event Bus for executive events."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import contracts
from ..paths import ROOT

DEFAULT_DIR = ROOT / ".agent-local" / "executive" / "events"
_CONSUMER_NAME = re.compile(r"^[a-z0-9][a-z0-9_-]*$")


def _make_event(
    event_type: str,
    source: str,
    dedup_key: str,
    payload: dict[str, Any],
    occurred_at: str | None = None,
    domain: str = "personal-agent",
    sensitivity: str = "personal",
    subject: str | None = None,
    provenance: list[str] | None = None,
) -> dict[str, Any]:
    """Create an event dict."""
    if occurred_at is None:
        occurred_at = datetime.now(timezone.utc).isoformat()

    event: dict[str, Any] = {
        "schema": contracts.EVENT_SCHEMA,
        "id": contracts.event_id(event_type, source, dedup_key),
        "type": event_type,
        "occurred_at": occurred_at,
        "source": source,
        "domain": domain,
        "sensitivity": sensitivity,
        "dedup_key": dedup_key,
        "payload": payload,
    }

    if subject is not None:
        event["subject"] = subject

    if provenance is not None:
        event["provenance"] = provenance

    if contracts.requires_local_only(sensitivity):
        event["local_only"] = True

    return event


class EventBus:
    """Append-only event log with deduplication by event id."""

    def __init__(self, directory: Path | str | None = None) -> None:
        self.directory = Path(directory) if directory is not None else DEFAULT_DIR
        self.path = self.directory / "events.jsonl"

    def publish(
        self,
        event_type: str,
        source: str,
        dedup_key: str,
        payload: dict[str, Any],
        **kwargs: Any,
    ) -> tuple[dict[str, Any], bool]:
        """Publish an event, returning (event, created) tuple.

        kwargs are passed to _make_event (occurred_at, domain, sensitivity,
        subject, provenance).

        If event with same id already exists, returns (existing_event, False).
        Otherwise appends and returns (event, True).
        """
        event = _make_event(event_type, source, dedup_key, payload, **kwargs)

        # Validate before checking dedup or writing
        errors = contracts.validate_event(event)
        if errors:
            raise ValueError("\n".join(errors))

        event_id = event["id"]

        # Check if event already exists
        existing = self.get(event_id)
        if existing is not None:
            return existing, False

        # Append the event
        self._append_line(event)
        return event, True

    def append(self, event: dict[str, Any]) -> None:
        """Validate and append an event, raising ValueError if invalid.

        Deduplicates by id (skips if id already exists).
        """
        errors = contracts.validate_event(event)
        if errors:
            raise ValueError("\n".join(errors))

        event_id = event["id"]
        existing = self.get(event_id)
        if existing is not None:
            return

        self._append_line(event)

    def events(
        self,
        event_type: str | None = None,
        since: str | None = None,
        subject: str | None = None,
    ) -> list[dict[str, Any]]:
        """Return events in file order, filtered by type, since, and subject.

        Returns empty list if file doesn't exist.
        """
        if not self.path.exists():
            return []

        result = []
        since_dt = None
        if since is not None:
            try:
                since_dt = datetime.fromisoformat(since.replace("Z", "+00:00"))
            except (ValueError, AttributeError) as e:
                raise ValueError(f"invalid since: {e}")
            # Normalize naive datetime to UTC
            if since_dt.tzinfo is None:
                since_dt = since_dt.replace(tzinfo=timezone.utc)

        with open(self.path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                try:
                    event = json.loads(line)
                except (json.JSONDecodeError, ValueError):
                    continue

                # Filter by type
                if event_type is not None and event.get("type") != event_type:
                    continue

                # Filter by since (occurred_at >= since)
                if since_dt is not None:
                    try:
                        occurred_at_str = event.get("occurred_at", "")
                        occurred_at = datetime.fromisoformat(occurred_at_str.replace("Z", "+00:00"))
                        # Normalize naive datetime to UTC
                        if occurred_at.tzinfo is None:
                            occurred_at = occurred_at.replace(tzinfo=timezone.utc)
                        if occurred_at < since_dt:
                            continue
                    except (ValueError, AttributeError):
                        continue

                # Filter by subject
                if subject is not None and event.get("subject") != subject:
                    continue

                result.append(event)

        return result

    def get(self, event_id: str) -> dict[str, Any] | None:
        """Return event by id, or None if not found."""
        if not self.path.exists():
            return None

        with open(self.path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                try:
                    event = json.loads(line)
                    if event.get("id") == event_id:
                        return event
                except (json.JSONDecodeError, ValueError):
                    continue

        return None

    def _consumer_path(self, consumer: str) -> Path:
        """Return the acknowledgement log path for a valid consumer name."""
        if not _CONSUMER_NAME.fullmatch(consumer):
            raise ValueError(f"invalid consumer name: {consumer!r}")
        return self.directory / "consumers" / f"{consumer}.jsonl"

    def acknowledged(self, consumer: str) -> set[str]:
        """Return event ids acknowledged by a consumer."""
        path = self._consumer_path(consumer)
        if not path.exists():
            return set()
        result: set[str] = set()
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except (json.JSONDecodeError, ValueError):
                    continue
                if isinstance(record, dict) and isinstance(record.get("event_id"), str):
                    result.add(record["event_id"])
        return result

    def acknowledge(
        self, consumer: str, event_id: str, acknowledged_at: str | None = None
    ) -> bool:
        """Append an acknowledgement once for an existing event."""
        path = self._consumer_path(consumer)
        if self.get(event_id) is None:
            raise ValueError(f"unknown event id: {event_id!r}")
        if event_id in self.acknowledged(consumer):
            return False
        if acknowledged_at is None:
            acknowledged_at = datetime.now(timezone.utc).isoformat()
        record = {"event_id": event_id, "acknowledged_at": acknowledged_at}
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(record, sort_keys=True) + "\n")
        return True

    def pending(
        self, consumer: str, event_type: str | None = None
    ) -> list[dict[str, Any]]:
        """Return unacknowledged events in event log order."""
        acknowledged = self.acknowledged(consumer)
        return [
            event for event in self.events(event_type=event_type)
            if event.get("id") not in acknowledged
        ]

    def _append_line(self, event: dict[str, Any]) -> None:
        """Append one JSON line to the log, creating directory if needed."""
        self.directory.mkdir(parents=True, exist_ok=True)
        with open(self.path, "a", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(event, sort_keys=True) + "\n")
