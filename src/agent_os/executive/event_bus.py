"""Append-only local Event Bus for executive events."""

from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

from . import contracts
from ..paths import ROOT

DEFAULT_DIR = ROOT / ".agent-local" / "executive" / "events"


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

        kwargs are passed to contracts.make_event (occurred_at, domain, sensitivity,
        subject, provenance).

        If event with same id already exists, returns (existing_event, False).
        Otherwise appends and returns (event, True).
        """
        event = contracts.make_event(event_type, source, dedup_key, payload, **kwargs)

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
            except (ValueError, AttributeError):
                since_dt = None

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

    def _append_line(self, event: dict[str, Any]) -> None:
        """Append one JSON line to the log, creating directory if needed."""
        self.directory.mkdir(parents=True, exist_ok=True)

        # Atomic append using temp file
        fd, tmp = tempfile.mkstemp(
            dir=self.directory,
            prefix=".tmp-",
            suffix=".jsonl",
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
                handle.write(json.dumps(event, sort_keys=True))
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())

            # Append temp file to main log
            with open(self.path, "ab") as f_main:
                with open(tmp, "rb") as f_tmp:
                    f_main.write(f_tmp.read())
                f_main.flush()
                os.fsync(f_main.fileno())
        finally:
            try:
                os.unlink(tmp)
            except OSError:
                pass
