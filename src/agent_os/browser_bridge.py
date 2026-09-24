"""Local browser bridge for Personal Agent OS.

Receives browser activity on loopback and durably stages it in a gitignored
SQLite database before returning acknowledgements. The store is deliberately
local high-frequency state; downstream Knowledge Engine workers can consume
stored events without generating noisy Git commits.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Any

from .paths import INDEX_DIR


DEFAULT_DB_PATH = INDEX_DIR / "browser-bridge.sqlite"


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _payload_hash(payload_json: str) -> str:
    return hashlib.sha256(payload_json.encode("utf-8")).hexdigest()


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
                    source_key TEXT,
                    occurred_at TEXT,
                    device TEXT,
                    received_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    payload_sha256 TEXT,
                    payload_json TEXT NOT NULL,
                    state TEXT NOT NULL DEFAULT 'stored'
                );
                CREATE INDEX IF NOT EXISTS browser_events_state_idx
                    ON browser_events(state, received_at);
                CREATE INDEX IF NOT EXISTS browser_events_source_idx
                    ON browser_events(source, received_at);
                CREATE INDEX IF NOT EXISTS browser_events_occurred_idx
                    ON browser_events(occurred_at);
                """
            )
            columns = {
                row["name"]
                for row in connection.execute("PRAGMA table_info(browser_events)")
            }
            migrations = {
                "source_key": "ALTER TABLE browser_events ADD COLUMN source_key TEXT",
                "device": "ALTER TABLE browser_events ADD COLUMN device TEXT",
                "payload_sha256": "ALTER TABLE browser_events ADD COLUMN payload_sha256 TEXT",
            }
            for name, statement in migrations.items():
                if name not in columns:
                    connection.execute(statement)

            rows = connection.execute(
                "SELECT event_id, payload_json FROM browser_events WHERE payload_sha256 IS NULL OR payload_sha256=''"
            ).fetchall()
            for row in rows:
                connection.execute(
                    "UPDATE browser_events SET payload_sha256=? WHERE event_id=?",
                    (_payload_hash(row["payload_json"]), row["event_id"]),
                )

    @staticmethod
    def _validate(event: Any) -> dict[str, Any]:
        if not isinstance(event, dict):
            raise ValueError("each event must be an object")
        event_id = str(event.get("event_id") or "").strip()
        source = str(event.get("source") or "").strip()
        event_type = str(event.get("event_type") or "event").strip()
        if not event_id or len(event_id) > 300:
            raise ValueError("event_id must be 1-300 characters")
        if not source or len(source) > 80:
            raise ValueError("source must be 1-80 characters")
        if not event_type or len(event_type) > 80:
            raise ValueError("event_type must be 1-80 characters")
        return {
            "event_id": event_id,
            "source": source,
            "event_type": event_type,
            "source_key": str(event.get("source_key") or "")[:500] or None,
            "occurred_at": str(event.get("occurred_at") or "")[:80] or None,
            "device": str(event.get("device") or "")[:200] or None,
            "payload": event.get("payload", {}),
        }

    def ingest(self, events: list[dict[str, Any]]) -> dict[str, Any]:
        if not isinstance(events, list) or len(events) > 500:
            raise ValueError("events must be a list of at most 500 items")

        validated = [self._validate(event) for event in events]
        acknowledged: list[str] = []
        stored: list[str] = []
        updated: list[str] = []
        duplicates: list[str] = []

        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            for event in validated:
                payload_json = _canonical_json(event["payload"])
                payload_sha256 = _payload_hash(payload_json)
                existing = connection.execute(
                    "SELECT payload_sha256 FROM browser_events WHERE event_id=?",
                    (event["event_id"],),
                ).fetchone()

                if existing is None:
                    connection.execute(
                        """
                        INSERT INTO browser_events(
                            event_id, source, event_type, source_key, occurred_at,
                            device, payload_sha256, payload_json, state
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'stored')
                        """,
                        (
                            event["event_id"],
                            event["source"],
                            event["event_type"],
                            event["source_key"],
                            event["occurred_at"],
                            event["device"],
                            payload_sha256,
                            payload_json,
                        ),
                    )
                    stored.append(event["event_id"])
                elif existing["payload_sha256"] == payload_sha256:
                    duplicates.append(event["event_id"])
                else:
                    connection.execute(
                        """
                        UPDATE browser_events
                        SET source=?, event_type=?, source_key=?, occurred_at=?,
                            device=?, received_at=CURRENT_TIMESTAMP,
                            payload_sha256=?, payload_json=?, state='stored'
                        WHERE event_id=?
                        """,
                        (
                            event["source"],
                            event["event_type"],
                            event["source_key"],
                            event["occurred_at"],
                            event["device"],
                            payload_sha256,
                            payload_json,
                            event["event_id"],
                        ),
                    )
                    updated.append(event["event_id"])
                acknowledged.append(event["event_id"])
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

        return {
            "schema": "agent-os/browser-bridge-ack/v1",
            "durable": True,
            "acknowledged": acknowledged,
            "stored": stored,
            "updated": updated,
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
            by_state = {
                row["state"]: row["count"]
                for row in connection.execute(
                    "SELECT state, COUNT(*) AS count FROM browser_events GROUP BY state"
                )
            }
        return {
            "database": str(self.path),
            "events": int(total),
            "by_source": by_source,
            "by_state": by_state,
        }

    def pending(self, limit: int = 500) -> list[dict[str, Any]]:
        limit = max(1, min(int(limit), 5000))
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT event_id, source, event_type, source_key, occurred_at,
                       device, received_at, payload_json
                FROM browser_events
                WHERE state='stored'
                ORDER BY received_at, event_id
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        result = []
        for row in rows:
            item = dict(row)
            item["payload"] = json.loads(item.pop("payload_json"))
            result.append(item)
        return result

    def mark_ingested(self, event_ids: list[str]) -> int:
        ids = [str(value) for value in dict.fromkeys(event_ids) if str(value)]
        if not ids:
            return 0
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            changed = 0
            for event_id in ids:
                cursor = connection.execute(
                    "UPDATE browser_events SET state='ingested' WHERE event_id=? AND state='stored'",
                    (event_id,),
                )
                changed += cursor.rowcount
            connection.commit()
            return changed
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()
