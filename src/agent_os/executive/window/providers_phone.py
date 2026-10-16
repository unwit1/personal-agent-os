"""3CX phone items in the Executive window.

Outstanding items: new voicemails (with 3CX's transcription and the local
audio file), missed calls nobody followed up on, and new chat messages. They
come from the local phone queue (.agent-os/intake/3cx/queue.json) that the
browser bridge keeps current; nothing here leaves this computer.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from agent_os import phone_intake

KIND_VOICEMAIL = "phone_voicemail"
KIND_MISSED_CALL = "phone_missed_call"
KIND_CHAT = "phone_chat"
_KINDS = {"voicemail": KIND_VOICEMAIL, "missed_call": KIND_MISSED_CALL, "chat": KIND_CHAT}


def phone_items(load_queue: Callable[[], dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    queue = (load_queue or phone_intake.load_queue)()
    items: list[dict[str, Any]] = []
    for queue_id, entry in (queue.get("items") or {}).items():
        if entry.get("status") != "open":
            continue
        kind = _KINDS.get(entry.get("kind"))
        if not kind:
            continue
        why = ""
        if kind == KIND_VOICEMAIL:
            seconds = entry.get("duration_seconds") or 0
            why = (entry.get("transcription") or "No transcription from 3CX.") + f" ({seconds}s)"
        elif kind == KIND_MISSED_CALL:
            why = "No voicemail and no call back yet."
        items.append({
            "id": f"phone:{queue_id}",
            "queue_id": queue_id,
            "kind": kind,
            "tab": "work",
            "source": "3CX phone",
            "title": entry.get("title") or queue_id,
            "why": why,
            "due": None,
            "age": entry.get("at"),
            "context": {
                "caller": entry.get("caller_name"),
                "number": entry.get("caller_number"),
                "transcription": entry.get("transcription"),
                "audio": entry.get("audio_path") or None,
                "audio_exists": bool(entry.get("audio_path")) and Path(entry["audio_path"]).exists(),
                "heard_in_3cx": entry.get("heard"),
            },
        })
    items.sort(key=lambda item: item.get("age") or "", reverse=True)
    return items


def _done(item: dict[str, Any], params: dict[str, Any], *, confirm: bool) -> dict[str, Any]:
    return {"status": "done" if phone_intake.mark_done(item["queue_id"]) else "not found"}


def register(registry: Any) -> None:
    registry.register_action(
        "phone.done", "Done", [KIND_VOICEMAIL, KIND_MISSED_CALL, KIND_CHAT], _done, consequential=False,
        description="Mark this voicemail, missed call or message as handled",
    )
