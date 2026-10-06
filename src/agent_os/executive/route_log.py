"""Append-only local log of executive event routing decisions."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from . import routing
from .event_bus import DEFAULT_DIR


class RouteLog:
    """Persist routing decisions without storing event payloads."""

    def __init__(self, directory: Path | str | None = None) -> None:
        self.directory = Path(directory) if directory is not None else DEFAULT_DIR
        self.path = self.directory / "routes.jsonl"

    def _iter_records(self):
        """Yield valid route records in file order, skipping malformed lines."""
        if not self.path.exists():
            return
        with open(self.path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except (json.JSONDecodeError, ValueError):
                    continue
                if isinstance(record, dict):
                    yield record

    def get(self, event_id: str) -> dict | None:
        """Return the first route for an event id, or None if absent."""
        return next((r for r in self._iter_records() if r.get("event_id") == event_id), None)

    def records(self) -> list[dict]:
        """Return valid route records in file order."""
        return list(self._iter_records())

    def record(self, route: dict, routed_at: str | None = None) -> tuple[dict, bool]:
        """Validate and append a route once per event id."""
        keys = ("event_id", "event_type", "disposition", "rule", "reason")
        if not isinstance(route, dict) or any(key not in route for key in keys):
            raise ValueError("route must contain event_id, event_type, disposition, rule, and reason")
        if any(not isinstance(route[key], str) for key in keys):
            raise ValueError("route fields must be strings")
        if route["disposition"] not in routing.DISPOSITIONS:
            raise ValueError(f"unknown disposition: {route['disposition']!r}")

        existing = self.get(route["event_id"])
        if existing is not None:
            return existing, False

        record = {key: route[key] for key in keys}
        record["routed_at"] = routed_at or datetime.now(timezone.utc).isoformat()
        self.directory.mkdir(parents=True, exist_ok=True)
        with open(self.path, "a", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(record, sort_keys=True) + "\n")
        return record, True
