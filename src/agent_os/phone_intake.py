"""3CX phone intake: voicemail audio, a phone log and a work queue.

The browser extension syncs the 3CX web client every five minutes and sends
calls and voicemails to the local bridge (source ``3cx``); voicemail audio
arrives separately. Everything here stays on this computer: callers are
employees and applicants.

    .agent-os/intake/3cx/
        voicemails/<date>_<time>_<caller>_<id>.wav (+ .json)
        calls.json, voicemails.json     latest snapshot of each call/voicemail
        phone-log.jsonl                 every call, oldest first
        phone-log.md                    readable log, newest first
        queue.json                      items for the Executive window

Recordings and transcripts from the audio capturer can later be attached to
phone-log entries by call id.
"""

from __future__ import annotations

import base64
import binascii
import json
import re
import sqlite3
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from .paths import INDEX_DIR

DEFAULT_INTAKE_DIR = INDEX_DIR / "intake" / "3cx"
MAX_AUDIO_BYTES = 30 * 1024 * 1024
QUEUE_VOICEMAIL_DAYS = 7
QUEUE_MISSED_CALL_DAYS = 2
_lock = threading.Lock()


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _parse(ts: Any) -> datetime | None:
    try:
        return datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
    except ValueError:
        return None


def _slug(text: str, fallback: str) -> str:
    value = re.sub(r"[^A-Za-z0-9._-]+", "-", str(text or "").strip()).strip("-._")
    return value[:40] or fallback


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.replace(path)


# -- voicemail audio --------------------------------------------------------------

def save_voicemail_audio(voicemail: dict[str, Any], audio_base64: str, intake_dir: Path = DEFAULT_INTAKE_DIR) -> dict[str, Any]:
    if not isinstance(voicemail, dict):
        raise ValueError("voicemail must be an object")
    try:
        vm_id = int(voicemail.get("id"))
    except (TypeError, ValueError):
        raise ValueError("voicemail id must be a number") from None
    try:
        audio = base64.b64decode(str(audio_base64 or ""), validate=True)
    except (binascii.Error, ValueError):
        raise ValueError("audio_base64 is not valid base64") from None
    if not audio or len(audio) > MAX_AUDIO_BYTES:
        raise ValueError("audio is empty or too large")
    received = _parse(voicemail.get("received_at")) or _now()
    caller = voicemail.get("caller_name") or voicemail.get("caller_number") or "unknown"
    folder = intake_dir / "voicemails"
    folder.mkdir(parents=True, exist_ok=True)
    existing = sorted(folder.glob(f"*_{vm_id}.wav"))
    path = existing[0] if existing else folder / f"{received:%Y-%m-%d_%H%M}_{_slug(caller, 'caller')}_{vm_id}.wav"
    path.write_bytes(audio)
    meta = {key: voicemail.get(key) for key in (
        "id", "extension", "caller_name", "caller_number", "caller_company", "received_at",
        "duration_seconds", "is_new", "transcription", "heard_by", "group_box", "filename")}
    meta["audio_path"] = str(path)
    meta["audio_bytes"] = len(audio)
    meta["saved_at"] = _now().isoformat()
    _write_json(path.with_suffix(".json"), meta)
    return {"path": str(path), "bytes": len(audio)}


# -- phone log, voicemail log and queue ----------------------------------------------

def _load_events(store_path: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    connection = sqlite3.connect(store_path, timeout=20.0)
    connection.row_factory = sqlite3.Row
    try:
        rows = connection.execute(
            "SELECT event_type, occurred_at, payload_json FROM browser_events WHERE source='3cx'"
        ).fetchall()
    finally:
        connection.close()
    calls, voicemails, chats = [], [], []
    for row in rows:
        try:
            payload = json.loads(row["payload_json"])
        except (TypeError, ValueError):
            continue
        if row["event_type"] == "call":
            calls.append(payload)
        elif row["event_type"] == "voicemail":
            voicemails.append(payload)
        elif row["event_type"] == "chat_unread":
            chats.append({**payload, "at": row["occurred_at"]})
    calls.sort(key=lambda c: c.get("started_at") or "")
    voicemails.sort(key=lambda v: v.get("received_at") or "")
    chats.sort(key=lambda c: c.get("at") or "")
    return calls, voicemails, chats


def _audio_index(intake_dir: Path) -> dict[str, str]:
    out = {}
    for path in (intake_dir / "voicemails").glob("*.wav"):
        out[path.stem.rsplit("_", 1)[-1]] = str(path)
    return out


def _who(name: str, number: str) -> str:
    name, number = str(name or "").strip(), str(number or "").strip()
    if name and number and number not in name:
        return f"{name} ({number})"
    return name or number or "unknown caller"


def _local(ts: str) -> str:
    parsed = _parse(ts)
    return parsed.astimezone().strftime("%Y-%m-%d %I:%M %p") if parsed else ""


def _render_log(calls: list[dict[str, Any]], voicemails: list[dict[str, Any]]) -> str:
    lines = ["# Phone log", "", f"Updated {_now().astimezone():%Y-%m-%d %I:%M %p}. Newest first. Times are local.", ""]
    entries = [("call", c.get("started_at") or "", c) for c in calls] + [("voicemail", v.get("received_at") or "", v) for v in voicemails]
    entries.sort(key=lambda e: e[1], reverse=True)
    day = None
    for kind, ts, item in entries:
        parsed = _parse(ts)
        this_day = parsed.astimezone().strftime("%A, %B %d, %Y") if parsed else "Undated"
        if this_day != day:
            lines += ["", f"## {this_day}", "", "| Time | Type | Who | Outcome | Length | Notes |", "|---|---|---|---|---|---|"]
            day = this_day
        when = parsed.astimezone().strftime("%I:%M %p") if parsed else ""
        if kind == "call":
            who = _who(item.get("other_name"), item.get("other_number"))
            outcome = item.get("outcome", "")
            length = f"{item.get('duration_seconds', 0)}s" if item.get("duration_seconds") else ""
            notes = f"via {item['via']}" if item.get("via") else ""
            lines.append(f"| {when} | {item.get('direction', 'call')} call | {who} | {outcome} | {length} | {notes} |")
        else:
            who = _who(item.get("caller_name"), item.get("caller_number"))
            text = str(item.get("transcription") or "").replace("|", "/").replace("\n", " ")
            audio = item.get("audio_path") or ""
            notes = " ".join(part for part in (f"\"{text[:300]}\"" if text else "", f"[audio]({Path(audio).as_uri()})" if audio else "") if part)
            state = "new" if item.get("is_new") else "heard"
            lines.append(f"| {when} | voicemail | {who} | {state} | {item.get('duration_seconds', 0)}s | {notes} |")
    return "\n".join(lines) + "\n"


def _update_queue(queue: dict[str, Any], calls: list[dict[str, Any]], voicemails: list[dict[str, Any]], chats: list[dict[str, Any]]) -> dict[str, Any]:
    now = _now()
    items = queue.setdefault("items", {})
    queue.setdefault("created_at", now.isoformat())

    def add(item_id: str, item: dict[str, Any]) -> None:
        if item_id in items:
            items[item_id].update({k: v for k, v in item.items() if k not in ("status", "created_at")})
        else:
            items[item_id] = {**item, "status": "open", "created_at": now.isoformat()}

    vm_numbers = []
    for vm in voicemails:
        received = _parse(vm.get("received_at"))
        if not received:
            continue
        vm_numbers.append((vm.get("caller_number") or "", received))
        recent = now - received <= timedelta(days=QUEUE_VOICEMAIL_DAYS)
        if f"voicemail:{vm.get('id')}" in items or (recent and vm.get("is_new")):
            add(f"voicemail:{vm.get('id')}", {
                "kind": "voicemail",
                "title": f"Voicemail from {_who(vm.get('caller_name'), vm.get('caller_number'))}",
                "at": vm.get("received_at"),
                "caller_name": vm.get("caller_name"),
                "caller_number": vm.get("caller_number"),
                "duration_seconds": vm.get("duration_seconds"),
                "transcription": vm.get("transcription") or "",
                "audio_path": vm.get("audio_path") or "",
                "heard": not vm.get("is_new"),
            })
    for call in calls:
        if call.get("outcome") != "missed":
            continue
        started = _parse(call.get("started_at"))
        if not started or now - started > timedelta(days=QUEUE_MISSED_CALL_DAYS):
            continue
        number = call.get("other_number") or ""
        # A voicemail left by the same caller covers the missed call, and so
        # does any later answered or outgoing call with them.
        if any(n == number and timedelta(0) <= t - started <= timedelta(minutes=15) for n, t in vm_numbers):
            continue
        if any((c.get("other_number") == number) and (_parse(c.get("started_at")) or started) > started
               and c.get("outcome") == "answered" for c in calls):
            continue
        add(f"missed:{call.get('id')}", {
            "kind": "missed_call",
            "title": f"Missed call from {_who(call.get('other_name'), number)}",
            "at": call.get("started_at"),
            "caller_name": call.get("other_name"),
            "caller_number": number,
        })
    for chat in chats:
        at = _parse(chat.get("at"))
        if not at or now - at > timedelta(days=1):
            continue
        add(f"chat:{chat.get('at')}", {
            "kind": "chat",
            "title": f"New 3CX message ({chat.get('unread')} unread)",
            "at": chat.get("at"),
        })
    queue["updated_at"] = now.isoformat()
    return queue


def export(store_path: Path, intake_dir: Path = DEFAULT_INTAKE_DIR) -> dict[str, Any]:
    with _lock:
        intake_dir.mkdir(parents=True, exist_ok=True)
        calls, voicemails, chats = _load_events(store_path)
        audio = _audio_index(intake_dir)
        for vm in voicemails:
            vm["audio_path"] = audio.get(str(vm.get("id")), vm.get("audio_path") or "")
        _write_json(intake_dir / "calls.json", calls)
        _write_json(intake_dir / "voicemails.json", voicemails)
        with (intake_dir / "phone-log.jsonl.tmp").open("w", encoding="utf-8") as handle:
            for call in calls:
                handle.write(json.dumps({"schema": "phone-log-v1", **call}, ensure_ascii=False) + "\n")
        (intake_dir / "phone-log.jsonl.tmp").replace(intake_dir / "phone-log.jsonl")
        (intake_dir / "phone-log.md").write_text(_render_log(calls, voicemails), encoding="utf-8")
        queue_path = intake_dir / "queue.json"
        try:
            queue = json.loads(queue_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            queue = {"schema": "phone-queue-v1"}
        queue = _update_queue(queue, calls, voicemails, chats)
        _write_json(queue_path, queue)
        open_items = sum(1 for item in queue["items"].values() if item.get("status") == "open")
        return {"calls": len(calls), "voicemails": len(voicemails), "audio": len(audio), "open": open_items, "intake_dir": str(intake_dir)}


def load_queue(intake_dir: Path = DEFAULT_INTAKE_DIR) -> dict[str, Any]:
    try:
        return json.loads((intake_dir / "queue.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"items": {}}


def mark_done(item_id: str, intake_dir: Path = DEFAULT_INTAKE_DIR) -> bool:
    with _lock:
        queue = load_queue(intake_dir)
        item = queue.get("items", {}).get(item_id)
        if not item:
            return False
        item["status"] = "done"
        item["done_at"] = _now().isoformat()
        _write_json(intake_dir / "queue.json", queue)
        return True


def run_periodically(store_path: Path, intake_dir: Path = DEFAULT_INTAKE_DIR, interval_seconds: float = 60.0) -> threading.Thread:
    def loop() -> None:
        while True:
            try:
                export(store_path, intake_dir)
            except (OSError, sqlite3.Error) as exc:
                print(json.dumps({"phone_intake_error": str(exc)}), flush=True)
            stop.wait(interval_seconds)

    stop = threading.Event()
    thread = threading.Thread(target=loop, name="phone-intake", daemon=True)
    thread.start()
    return thread
