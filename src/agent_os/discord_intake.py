"""Export Discord messages captured by the browser bridge to a local intake.

The Firefox extension indexes rendered Discord messages into the bridge's
SQLite store. This module copies them, incrementally, into plain JSONL files
that Agent OS (and anything else) can analyze or ingest later:

    .agent-os/intake/discord/<server>/<channel>/<YYYY-MM>.jsonl

One line per message (discord-intake-v1). A checkpoint keeps the last
exported bridge row, so each run only writes new messages; edits that the
bridge records as revisions are appended again with the same ``key`` and a
later ``exported_at`` (readers keep the last line per key).
"""

from __future__ import annotations

import json
import re
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .paths import INDEX_DIR

DEFAULT_INTAKE_DIR = INDEX_DIR / "intake" / "discord"
SCHEMA = "discord-intake-v1"
_CHECKPOINT = ".checkpoint.json"
_lock = threading.Lock()


def _slug(text: str, fallback: str) -> str:
    value = re.sub(r"[^A-Za-z0-9._-]+", "-", str(text or "").strip()).strip("-._")
    return (value[:60] or fallback).lower()


def _guild_name(payload: dict[str, Any]) -> str:
    name = str(payload.get("guild_name") or "")
    # Discord prefixes unread state to the rendered name: "2 mentions, Server".
    name = re.sub(r"^(?:(?:unread messages|\d+ mentions?),\s*)+", "", name, flags=re.IGNORECASE)
    if not name:
        title = str(payload.get("page_title") or "")
        parts = [part.strip() for part in title.split("|")]
        name = parts[-1] if len(parts) >= 3 else ""
    return name.strip() or ("Direct Messages" if payload.get("guild_id") == "@me" else "")


def _channel_name(payload: dict[str, Any]) -> str:
    name = str(payload.get("channel_name") or "").strip()
    if name:
        return name.lstrip("#")
    match = re.search(r"\|\s*#?([^|]+?)\s*\|", str(payload.get("page_title") or ""))
    return match.group(1).lstrip("#") if match else ""


def _json_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    try:
        parsed = json.loads(value) if isinstance(value, str) and value else []
    except ValueError:
        return []
    return parsed if isinstance(parsed, list) else []


def intake_record(payload: dict[str, Any], *, exported_at: str) -> dict[str, Any]:
    author = re.sub(r",?\s*Server Tag:.*$", "", str(payload.get("author") or "")).strip().rstrip(":").strip()
    return {
        "schema": SCHEMA,
        "key": payload.get("key") or "",
        "message_id": payload.get("message_id") or "",
        "timestamp": payload.get("timestamp") or payload.get("captured_at") or "",
        "server_id": payload.get("guild_id") or "",
        "server": _guild_name(payload),
        "channel_id": payload.get("channel_id") or "",
        "channel": _channel_name(payload),
        "author": author,
        "author_raw": payload.get("author") or "",
        "text": payload.get("text") or "",
        "reply_to_message_id": payload.get("reply_to_message_id") or "",
        "urls": _json_list(payload.get("urls")),
        "attachments": _json_list(payload.get("attachments")),
        "message_url": payload.get("message_url") or "",
        "captured_at": payload.get("first_captured_at") or payload.get("captured_at") or "",
        "exported_at": exported_at,
    }


def _target(intake_dir: Path, record: dict[str, Any]) -> Path:
    server = _slug(record["server"], "server") + "-" + _slug(record["server_id"], "unknown")
    channel = _slug(record["channel"], "channel") + "-" + _slug(record["channel_id"], "unknown")
    month = str(record["timestamp"])[:7] or "undated"
    return intake_dir / server / channel / f"{month}.jsonl"


def export_new(store_path: Path, intake_dir: Path = DEFAULT_INTAKE_DIR, *, limit: int = 50000) -> dict[str, Any]:
    """Append Discord messages stored since the last run to the intake."""
    with _lock:
        intake_dir.mkdir(parents=True, exist_ok=True)
        checkpoint_path = intake_dir / _CHECKPOINT
        try:
            checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            checkpoint = {}
        last_rowid = int(checkpoint.get("last_rowid") or 0)
        connection = sqlite3.connect(store_path, timeout=20.0)
        connection.row_factory = sqlite3.Row
        try:
            rows = connection.execute(
                "SELECT rowid, payload_json FROM browser_events "
                "WHERE source='discord' AND rowid > ? ORDER BY rowid LIMIT ?",
                (last_rowid, max(1, int(limit))),
            ).fetchall()
        finally:
            connection.close()
        exported_at = datetime.now(timezone.utc).isoformat()
        batches: dict[Path, list[str]] = {}
        for row in rows:
            try:
                payload = json.loads(row["payload_json"])
            except (TypeError, ValueError):
                continue
            if not isinstance(payload, dict):
                continue
            record = intake_record(payload, exported_at=exported_at)
            batches.setdefault(_target(intake_dir, record), []).append(json.dumps(record, ensure_ascii=False))
        for path, lines in batches.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("a", encoding="utf-8") as handle:
                handle.write("\n".join(lines) + "\n")
        if rows:
            checkpoint = {
                "schema": "discord-intake-checkpoint/v1",
                "last_rowid": rows[-1]["rowid"],
                "updated_at": exported_at,
                "exported_total": int(checkpoint.get("exported_total") or 0) + len(rows),
            }
            checkpoint_path.write_text(json.dumps(checkpoint, indent=2) + "\n", encoding="utf-8")
        return {
            "exported": len(rows),
            "files": len(batches),
            "intake_dir": str(intake_dir),
            "last_rowid": checkpoint.get("last_rowid", last_rowid),
        }


def run_periodically(store_path: Path, intake_dir: Path = DEFAULT_INTAKE_DIR, interval_seconds: float = 60.0) -> threading.Thread:
    """Export now and then every ``interval_seconds`` on a daemon thread."""
    stop = threading.Event()

    def loop() -> None:
        while True:
            try:
                while export_new(store_path, intake_dir)["exported"]:
                    pass
            except (OSError, sqlite3.Error) as exc:
                print(json.dumps({"discord_intake_error": str(exc)}), flush=True)
            if stop.wait(interval_seconds):
                return

    thread = threading.Thread(target=loop, name="discord-intake", daemon=True)
    thread.stop = stop  # type: ignore[attr-defined]
    thread.start()
    return thread
