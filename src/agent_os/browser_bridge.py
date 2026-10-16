"""Local browser bridge for Personal Agent OS.

Receives browser activity on loopback and durably stages it in a gitignored
SQLite database before returning acknowledgements. The store is deliberately
local high-frequency state; downstream Knowledge Engine workers can consume
stored events without generating noisy Git commits.
"""

from __future__ import annotations

import json
import re
import sqlite3
import uuid
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from .fingerprints import text_sha256
from .paths import INDEX_DIR


DEFAULT_DB_PATH = INDEX_DIR / "browser-bridge.sqlite"


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _payload_hash(payload_json: str) -> str:
    return text_sha256(payload_json)


def normalize_capture_key(value: Any) -> str:
    """Comparable form of a capture key: source ids as-is, URLs without
    fragment, trailing slash or ``www.`` (matches the browser extension)."""
    text = str(value or "").strip()
    if not re.match(r"^https?://", text, re.IGNORECASE):
        return text
    parts = urlsplit(text)
    origin = f"{parts.scheme.lower()}://{parts.netloc.lower()}".replace("://www.", "://", 1)
    return origin + parts.path.rstrip("/") + (f"?{parts.query}" if parts.query else "")


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

                CREATE TABLE IF NOT EXISTS browser_sessions (
                    session_id TEXT PRIMARY KEY,
                    url TEXT,
                    title TEXT,
                    site TEXT,
                    visibility TEXT,
                    focused INTEGER NOT NULL DEFAULT 0,
                    user_agent TEXT,
                    capabilities_json TEXT NOT NULL DEFAULT '{}',
                    registered_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    last_seen TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                CREATE INDEX IF NOT EXISTS browser_sessions_seen_idx
                    ON browser_sessions(last_seen);

                CREATE TABLE IF NOT EXISTS browser_commands (
                    command_id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    actions_json TEXT NOT NULL,
                    issued_by TEXT,
                    approved_consequential INTEGER NOT NULL DEFAULT 0,
                    state TEXT NOT NULL DEFAULT 'queued',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    claimed_at TEXT,
                    completed_at TEXT,
                    result_json TEXT,
                    error TEXT
                );
                CREATE INDEX IF NOT EXISTS browser_commands_session_idx
                    ON browser_commands(session_id, state, created_at);
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

    def saved_capture_keys(self, keys: list[Any]) -> list[str]:
        """Return the given keys that match a stored browser capture, by
        source id (``nexus:game:id``) or by the capture's URL."""
        wanted: list[str] = []
        for key in keys[:500]:
            normalized = normalize_capture_key(key)
            if normalized and normalized not in wanted:
                wanted.append(normalized)
        if not wanted:
            return []
        found: set[str] = set()
        with self._connect() as connection:
            for start in range(0, len(wanted), 200):
                chunk = wanted[start:start + 200]
                marks = ",".join("?" for _ in chunk)
                found.update(
                    row["source_key"]
                    for row in connection.execute(
                        f"SELECT source_key FROM browser_events "
                        f"WHERE source='browser-capture' AND source_key IN ({marks})",
                        chunk,
                    )
                )
            urls = {key for key in wanted if key.startswith("http") and key not in found}
            if urls:
                for row in connection.execute(
                    "SELECT payload_json FROM browser_events WHERE source='browser-capture'"
                ):
                    try:
                        payload = json.loads(row["payload_json"])
                    except (TypeError, ValueError):
                        continue
                    for field in ("url", "canonical_url"):
                        normalized = normalize_capture_key(payload.get(field))
                        if normalized in urls:
                            found.add(normalized)
        return [key for key in wanted if key in found]

    def find_discord_author_matches(
        self,
        aliases: list[str],
        *,
        limit: int = 20,
        scan_limit: int = 50000,
    ) -> list[dict[str, Any]]:
        """Find Discord authors whose rendered-message names match creator aliases.

        This is deliberately evidence-only. Matching Discord display names are
        surfaced as identity candidates rather than silently promoted into a
        confirmed cross-provider account.
        """
        wanted = {
            re.sub(r"[^a-z0-9]+", "", str(alias or "").casefold().removeprefix("@"))
            for alias in aliases
            if str(alias or "").strip()
        }
        wanted.discard("")
        if not wanted:
            return []

        scan_limit = max(1, min(int(scan_limit), 250000))
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT occurred_at, received_at, payload_json
                FROM browser_events
                WHERE source='discord'
                ORDER BY received_at DESC
                LIMIT ?
                """,
                (scan_limit,),
            ).fetchall()

        grouped: dict[str, dict[str, Any]] = {}
        for row in rows:
            try:
                payload = json.loads(row["payload_json"])
            except (TypeError, ValueError):
                continue
            author = str(payload.get("author") or "").strip()
            normalized = re.sub(r"[^a-z0-9]+", "", author.casefold().removeprefix("@"))
            if not normalized or normalized not in wanted:
                continue
            current = grouped.setdefault(normalized, {
                "author": author,
                "message_count": 0,
                "last_seen": None,
                "sample_message_url": None,
                "confidence": "candidate",
            })
            current["message_count"] += 1
            seen = payload.get("timestamp") or row["occurred_at"] or row["received_at"]
            if seen and (not current["last_seen"] or str(seen) > str(current["last_seen"])):
                current["last_seen"] = seen
            if not current["sample_message_url"] and payload.get("message_url"):
                current["sample_message_url"] = payload.get("message_url")

        return sorted(
            grouped.values(),
            key=lambda item: (-int(item.get("message_count") or 0), str(item.get("author") or "").casefold()),
        )[: max(1, min(int(limit), 100))]

    @staticmethod
    def _validate_session(session: Any) -> dict[str, Any]:
        if not isinstance(session, dict):
            raise ValueError("browser session must be an object")
        session_id = str(session.get("session_id") or "").strip()
        if not session_id or len(session_id) > 200:
            raise ValueError("session_id must be 1-200 characters")
        capabilities = session.get("capabilities") or {}
        if not isinstance(capabilities, dict):
            raise ValueError("capabilities must be an object")
        return {
            "session_id": session_id,
            "url": str(session.get("url") or "")[:4000],
            "title": str(session.get("title") or "")[:1000],
            "site": str(session.get("site") or "")[:300],
            "visibility": str(session.get("visibility") or "")[:40],
            "focused": 1 if session.get("focused") else 0,
            "user_agent": str(session.get("user_agent") or "")[:1000],
            "capabilities": capabilities,
        }

    def register_session(self, session: dict[str, Any]) -> dict[str, Any]:
        item = self._validate_session(session)
        capabilities_json = _canonical_json(item["capabilities"])
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO browser_sessions(
                    session_id, url, title, site, visibility, focused,
                    user_agent, capabilities_json, registered_at, last_seen
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                ON CONFLICT(session_id) DO UPDATE SET
                    url=excluded.url,
                    title=excluded.title,
                    site=excluded.site,
                    visibility=excluded.visibility,
                    focused=excluded.focused,
                    user_agent=excluded.user_agent,
                    capabilities_json=excluded.capabilities_json,
                    last_seen=CURRENT_TIMESTAMP
                """,
                (
                    item["session_id"],
                    item["url"],
                    item["title"],
                    item["site"],
                    item["visibility"],
                    item["focused"],
                    item["user_agent"],
                    capabilities_json,
                ),
            )
        return {"ok": True, "session_id": item["session_id"]}

    def list_sessions(self, active_within_seconds: int = 90) -> list[dict[str, Any]]:
        active_within_seconds = max(5, min(int(active_within_seconds), 86400))
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT session_id, url, title, site, visibility, focused,
                       user_agent, capabilities_json, registered_at, last_seen,
                       MAX(
                           0,
                           CAST(strftime('%s','now') - strftime('%s', last_seen) AS INTEGER)
                       ) AS age_seconds
                FROM browser_sessions
                ORDER BY focused DESC, last_seen DESC, session_id
                """
            ).fetchall()
        result: list[dict[str, Any]] = []
        for row in rows:
            item = dict(row)
            try:
                item["capabilities"] = json.loads(item.pop("capabilities_json"))
            except (TypeError, ValueError):
                item["capabilities"] = {}
                item.pop("capabilities_json", None)
            item["focused"] = bool(item["focused"])
            item["active"] = int(item.get("age_seconds") or 0) <= active_within_seconds
            result.append(item)
        return result

    @staticmethod
    def _validate_actions(actions: Any) -> list[dict[str, Any]]:
        if not isinstance(actions, list) or not actions or len(actions) > 25:
            raise ValueError("actions must be a non-empty list of at most 25 items")
        allowed = {
            "inspect", "extract", "wait", "click", "type", "key", "select_option", "scroll",
            "navigate", "back", "forward", "reload", "open_tab", "close_tab",
        }
        normalized: list[dict[str, Any]] = []
        for raw in actions:
            if not isinstance(raw, dict):
                raise ValueError("each browser action must be an object")
            action = dict(raw)
            op = str(action.get("op") or "").strip()
            if op not in allowed:
                raise ValueError(f"unsupported browser action: {op}")
            action["op"] = op
            if "selector" in action:
                action["selector"] = str(action["selector"])[:2000]
            if "text" in action:
                action["text"] = str(action["text"])[:50000]
            if "url" in action:
                url = str(action["url"]).strip()
                if not re.match(r"^https?://", url, re.I):
                    raise ValueError("browser navigation/open_tab URLs must use http or https")
                action["url"] = url[:4000]
            if "timeout_ms" in action:
                action["timeout_ms"] = max(0, min(int(action["timeout_ms"]), 15000))
            normalized.append(action)
        return normalized

    def enqueue_command(
        self,
        session_id: str,
        actions: list[dict[str, Any]],
        *,
        issued_by: str = "agent-os",
        approved_consequential: bool = False,
    ) -> dict[str, Any]:
        session_id = str(session_id or "").strip()
        if not session_id:
            raise ValueError("session_id is required")
        normalized = self._validate_actions(actions)
        with self._connect() as connection:
            session = connection.execute(
                "SELECT session_id FROM browser_sessions WHERE session_id=?",
                (session_id,),
            ).fetchone()
            if session is None:
                raise KeyError(f"unknown browser session: {session_id}")
            command_id = "bcmd-" + uuid.uuid4().hex[:20]
            connection.execute(
                """
                INSERT INTO browser_commands(
                    command_id, session_id, actions_json, issued_by,
                    approved_consequential, state
                ) VALUES (?, ?, ?, ?, ?, 'queued')
                """,
                (
                    command_id,
                    session_id,
                    _canonical_json(normalized),
                    str(issued_by or "agent-os")[:200],
                    1 if approved_consequential else 0,
                ),
            )
        return {
            "command_id": command_id,
            "session_id": session_id,
            "state": "queued",
            "actions": normalized,
            "approved_consequential": bool(approved_consequential),
        }

    def claim_commands(self, session_id: str, limit: int = 3) -> list[dict[str, Any]]:
        session_id = str(session_id or "").strip()
        limit = max(1, min(int(limit), 10))
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            rows = connection.execute(
                """
                SELECT command_id, session_id, actions_json, issued_by,
                       approved_consequential, state, created_at
                FROM browser_commands
                WHERE session_id=? AND state='queued'
                ORDER BY created_at, command_id
                LIMIT ?
                """,
                (session_id, limit),
            ).fetchall()
            commands: list[dict[str, Any]] = []
            for row in rows:
                connection.execute(
                    """
                    UPDATE browser_commands
                    SET state='running', claimed_at=CURRENT_TIMESTAMP
                    WHERE command_id=? AND state='queued'
                    """,
                    (row["command_id"],),
                )
                item = dict(row)
                item["actions"] = json.loads(item.pop("actions_json"))
                item["approved_consequential"] = bool(item["approved_consequential"])
                item["state"] = "running"
                commands.append(item)
            connection.commit()
            return commands
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def complete_command(
        self,
        command_id: str,
        *,
        state: str,
        result: Any = None,
        error: str | None = None,
    ) -> dict[str, Any]:
        if state not in {"completed", "failed", "approval_required", "cancelled"}:
            raise ValueError("invalid browser command completion state")
        command_id = str(command_id or "").strip()
        with self._connect() as connection:
            current = connection.execute(
                "SELECT command_id FROM browser_commands WHERE command_id=?",
                (command_id,),
            ).fetchone()
            if current is None:
                raise KeyError(f"unknown browser command: {command_id}")
            connection.execute(
                """
                UPDATE browser_commands
                SET state=?, completed_at=CURRENT_TIMESTAMP, result_json=?, error=?
                WHERE command_id=?
                """,
                (
                    state,
                    _canonical_json(result) if result is not None else None,
                    str(error or "")[:4000] or None,
                    command_id,
                ),
            )
        return self.command_status(command_id)

    @classmethod
    def actions_hash(cls, actions: Any) -> str:
        """Stable fingerprint of a normalized action list (approval binding)."""
        return text_sha256(_canonical_json(cls._validate_actions(actions)))

    def commands_by_issuer(self, issued_by: str, limit: int = 200) -> list[dict[str, Any]]:
        with self._connect() as connection:
            ids = [
                row["command_id"]
                for row in connection.execute(
                    "SELECT command_id FROM browser_commands WHERE issued_by=? "
                    "ORDER BY created_at, command_id LIMIT ?",
                    (str(issued_by), max(1, min(int(limit), 1000))),
                )
            ]
        return [self.command_status(command_id) for command_id in ids]

    def command_status(self, command_id: str) -> dict[str, Any]:
        command_id = str(command_id or "").strip()
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT command_id, session_id, actions_json, issued_by,
                       approved_consequential, state, created_at, claimed_at,
                       completed_at, result_json, error
                FROM browser_commands
                WHERE command_id=?
                """,
                (command_id,),
            ).fetchone()
        if row is None:
            raise KeyError(f"unknown browser command: {command_id}")
        item = dict(row)
        item["actions"] = json.loads(item.pop("actions_json"))
        item["approved_consequential"] = bool(item["approved_consequential"])
        if item.get("result_json"):
            try:
                item["result"] = json.loads(item.pop("result_json"))
            except (TypeError, ValueError):
                item["result"] = None
                item.pop("result_json", None)
        else:
            item["result"] = None
            item.pop("result_json", None)
        return item

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
