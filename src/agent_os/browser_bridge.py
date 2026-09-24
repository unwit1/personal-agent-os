"""Local browser bridge for Personal Agent OS.

Receives browser activity on loopback and durably stages it in a gitignored
SQLite database before returning acknowledgements.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from .paths import INDEX_DIR


DEFAULT_DB_PATH = INDEX_DIR / "browser-bridge.sqlite"


class BridgeStore:
    def __init__(self, path: Path = DEFAULT_DB_PATH) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=20.0)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA synchronous=NORMAL")
        connection.execute("PRAGMA busy_timeout=5000")
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS browser_events (
                    event_id TEXT PRIMARY KEY,
                    source TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    occurred_at TEXT,
                    received_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    payload_json TEXT NOT NULL,
                    state TEXT NOT NULL DEFAULT 'stored'
                );
                CREATE INDEX IF NOT EXISTS browser_events_state_idx
                    ON browser_events(state, received_at);
                CREATE INDEX IF NOT EXISTS browser_events_source_idx
                    ON browser_events(source, received_at);
                """
            )

    def ingest(self, events: list[dict[str, Any]]) -> dict[str, Any]:
        if not isinstance(events, list) or len(events) > 500:
            raise ValueError("events must be a list of at most 500 items")
        accepted: list[str] = []
        stored: list[str] = []
        duplicates: list[str] = []
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            for event in events:
                if not isinstance(event, dict):
                    raise ValueError("each event must be an object")
                event_id = str(event.get("event_id") or "").strip()
                source = str(event.get("source") or "").strip()
                event_type = str(event.get("event_type") or "event").strip()
                if not event_id or not source:
                    raise ValueError("event_id and source are required")
                payload = json.dumps(
                    event.get("payload", {}),
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                )
                exists = connection.execute(
                    "SELECT 1 FROM browser_events WHERE event_id=?",
                    (event_id,),
                ).fetchone()
                if exists:
                    duplicates.append(event_id)
                    accepted.append(event_id)
                    continue
                connection.execute(
                    """
                    INSERT INTO browser_events(
                        event_id, source, event_type, occurred_at, payload_json
                    ) VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        event_id,
                        source[:80],
                        event_type[:80],
                        str(event.get("occurred_at") or "")[:80] or None,
                        payload,
                    ),
                )
                stored.append(event_id)
                accepted.append(event_id)
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()
        return {
            "durable": True,
            "acknowledged": accepted,
            "stored": stored,
            "duplicates": duplicates,
        }

    def stats(self) -> dict[str, Any]:
        with self._connect() as connection:
            total = connection.execute(
                "SELECT COUNT(*) FROM browser_events"
            ).fetchone()[0]
            by_source = {
                row["source"]: row["count"]
                for row in connection.execute(
                    "SELECT source, COUNT(*) AS count FROM browser_events GROUP BY source"
                )
            }
        return {"database": str(self.path), "events": int(total), "by_source": by_source}
