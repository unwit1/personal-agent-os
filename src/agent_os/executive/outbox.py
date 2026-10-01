from __future__ import annotations

import json
import os
import re
import secrets
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ..paths import ROOT

PENDING_APPROVAL = "PENDING_APPROVAL"
APPROVED = "APPROVED"
SENT = "SENT"
PARTIAL = "PARTIAL"
FAILED = "FAILED"

BATCH_STATES = (PENDING_APPROVAL, APPROVED, SENT, PARTIAL, FAILED)
ITEM_PENDING = "pending"
ITEM_APPROVED = "approved"
ITEM_DROPPED = "dropped"
ITEM_SENT = "sent"
ITEM_FAILED = "failed"
ITEM_STATES = (ITEM_PENDING, ITEM_APPROVED, ITEM_DROPPED, ITEM_SENT, ITEM_FAILED)

_TRANSITIONS = {
    PENDING_APPROVAL: {APPROVED},
    APPROVED: {SENT, PARTIAL, FAILED},
    SENT: set(),
    PARTIAL: set(),
    FAILED: set(),
}
_ITEM_TRANSITIONS = {
    ITEM_PENDING: {ITEM_APPROVED, ITEM_DROPPED},
    ITEM_APPROVED: {ITEM_SENT, ITEM_FAILED},
    ITEM_DROPPED: set(),
    ITEM_SENT: set(),
    ITEM_FAILED: set(),
}

_BATCH_ID_RE = re.compile(r"^ob-[0-9a-f]{16}$")
_REF_RE = re.compile(r"^[A-Za-z0-9_.:\-]{1,128}$")
_ITEM_FIELDS = (
    "applicant_ref",
    "name",
    "opening",
    "manager",
    "interview_type",
    "location",
    "duration_minutes",
    "proposed_slots",
    "chosen_slots",
    "subject",
    "body",
    "status",
    "email_id",
    "error",
)
_STR_FIELDS = ("name", "opening", "manager", "interview_type", "location", "subject", "body")

DEFAULT_DIR = ROOT / ".agent-local" / "executive" / "outbox"


class OutboxError(ValueError):
    """Raised for malformed input, unknown batches and illegal transitions."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def new_batch_id() -> str:
    return "ob-" + secrets.token_hex(8)


def _check_ref(ref: Any) -> str:
    if not isinstance(ref, str) or not _REF_RE.match(ref):
        raise OutboxError("invalid applicant_ref")
    return ref


def _check_slots(slots: Any, field: str) -> list[str]:
    if not isinstance(slots, (list, tuple)):
        raise OutboxError(f"{field} must be a list")
    out: list[str] = []
    for slot in slots:
        if isinstance(slot, datetime):
            slot = slot.isoformat()
        if not isinstance(slot, str):
            raise OutboxError(f"{field} entries must be ISO datetimes")
        try:
            datetime.fromisoformat(slot)
        except ValueError as exc:
            raise OutboxError(f"{field} entry is not an ISO datetime") from exc
        out.append(slot)
    return out


def _normalise_item(raw: Any) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise OutboxError("item must be an object")
    unknown = set(raw) - set(_ITEM_FIELDS)
    if unknown:
        raise OutboxError("unexpected item fields: " + ", ".join(sorted(unknown)))
    item: dict[str, Any] = {
        "applicant_ref": _check_ref(raw.get("applicant_ref")),
        "status": raw.get("status", ITEM_PENDING),
        "email_id": raw.get("email_id"),
        "error": raw.get("error"),
    }
    if item["status"] not in ITEM_STATES:
        raise OutboxError("invalid item status")
    for field in _STR_FIELDS:
        value = raw.get(field, "")
        if value is None:
            value = ""
        if not isinstance(value, str):
            raise OutboxError(f"{field} must be a string")
        item[field] = value
    duration = raw.get("duration_minutes", 0)
    if isinstance(duration, bool) or not isinstance(duration, int) or duration < 0:
        raise OutboxError("duration_minutes must be a non-negative integer")
    item["duration_minutes"] = duration
    item["proposed_slots"] = _check_slots(raw.get("proposed_slots", []), "proposed_slots")
    item["chosen_slots"] = _check_slots(raw.get("chosen_slots", []), "chosen_slots")
    for field in ("email_id", "error"):
        if item[field] is not None and not isinstance(item[field], (str, int)):
            raise OutboxError(f"{field} must be a string")
    return item


def _validate_batch(raw: Any) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise OutboxError("batch must be an object")
    batch_id = raw.get("batch_id")
    if not isinstance(batch_id, str) or not _BATCH_ID_RE.match(batch_id):
        raise OutboxError("invalid batch_id")
    state = raw.get("state")
    if state not in BATCH_STATES:
        raise OutboxError("invalid batch state")
    items = raw.get("items")
    if not isinstance(items, list) or not items:
        raise OutboxError("batch needs at least one item")
    norm = [_normalise_item(i) for i in items]
    refs = [i["applicant_ref"] for i in norm]
    if len(set(refs)) != len(refs):
        raise OutboxError("duplicate applicant_ref in batch")
    for key in ("created_at", "updated_at"):
        if not isinstance(raw.get(key), str):
            raise OutboxError(f"{key} missing")
    return {
        "batch_id": batch_id,
        "state": state,
        "created_at": raw["created_at"],
        "updated_at": raw["updated_at"],
        "items": norm,
    }


class OutboxStore:
    def __init__(self, directory: Path | str | None = None) -> None:
        self.directory = Path(directory) if directory is not None else DEFAULT_DIR

    def _path(self, batch_id: str) -> Path:
        if not isinstance(batch_id, str) or not _BATCH_ID_RE.match(batch_id):
            raise OutboxError("invalid batch_id")
        return self.directory / f"{batch_id}.json"

    def _write(self, batch: dict[str, Any]) -> None:
        """Atomic write: temp file in the same dir, fsync, then replace."""
        path = self._path(batch["batch_id"])
        self.directory.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=self.directory, prefix=".tmp-", suffix=".json")
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
                json.dump(batch, handle, indent=2, sort_keys=True)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(tmp, path)
        except BaseException:
            try:
                os.unlink(tmp)
            except OSError:
                pass
            raise

    def recover(self) -> int:
        """Remove temp files left by an interrupted write; batches are untouched."""
        if not self.directory.is_dir():
            return 0
        removed = 0
        for tmp in self.directory.glob(".tmp-*.json"):
            try:
                tmp.unlink()
                removed += 1
            except OSError:
                pass
        return removed

    def create(self, items: list[dict[str, Any]]) -> dict[str, Any]:
        if not isinstance(items, list) or not items:
            raise OutboxError("batch needs at least one item")
        norm = []
        for raw in items:
            item = _normalise_item(raw)
            if item["status"] != ITEM_PENDING or item["chosen_slots"]:
                raise OutboxError("new items must be pending with no chosen slots")
            norm.append(item)
        now = _now()
        batch = _validate_batch(
            {
                "batch_id": new_batch_id(),
                "state": PENDING_APPROVAL,
                "created_at": now,
                "updated_at": now,
                "items": norm,
            }
        )
        self._write(batch)
        return batch

    def load(self, batch_id: str) -> dict[str, Any]:
        path = self._path(batch_id)
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            raise OutboxError("unknown batch") from exc
        except (OSError, ValueError) as exc:
            raise OutboxError("batch file is unreadable or malformed") from exc
        batch = _validate_batch(raw)
        if batch["batch_id"] != batch_id:
            raise OutboxError("batch_id does not match file")
        return batch

    def list(self, state: str | None = None) -> list[dict[str, Any]]:
        if state is not None and state not in BATCH_STATES:
            raise OutboxError("invalid batch state")
        if not self.directory.is_dir():
            return []
        out = []
        for path in sorted(self.directory.glob("ob-*.json")):
            try:
                batch = self.load(path.stem)
            except OutboxError:
                continue
            if state is None or batch["state"] == state:
                out.append(batch)
        return out

    def _transition(self, batch: dict[str, Any], new_state: str) -> None:
        if new_state not in _TRANSITIONS[batch["state"]]:
            raise OutboxError(f"illegal transition {batch['state']} -> {new_state}")
        batch["state"] = new_state
        batch["updated_at"] = _now()

    def approve(self, batch_id: str, choices: dict[str, Any]) -> dict[str, Any]:
        """choices: applicant_ref -> list of ISO slots to offer, or None to drop.

        Every item must be addressed explicitly; nothing is approved by default.
        """
        batch = self.load(batch_id)
        if batch["state"] != PENDING_APPROVAL:
            raise OutboxError(f"illegal transition {batch['state']} -> {APPROVED}")
        if not isinstance(choices, dict):
            raise OutboxError("choices must be an object")
        refs = {i["applicant_ref"] for i in batch["items"]}
        if set(choices) != refs:
            raise OutboxError("choices must cover exactly the batch's items")
        for item in batch["items"]:
            choice = choices[item["applicant_ref"]]
            if choice is None:
                item["status"] = ITEM_DROPPED
                item["chosen_slots"] = []
                continue
            slots = _check_slots(choice, "chosen_slots")
            if not slots:
                raise OutboxError("approved item needs at least one slot (use None to drop)")
            item["status"] = ITEM_APPROVED
            item["chosen_slots"] = slots
        if not any(i["status"] == ITEM_APPROVED for i in batch["items"]):
            raise OutboxError("cannot approve a batch with every item dropped")
        self._transition(batch, APPROVED)
        self._write(_validate_batch(batch))
        return batch

    def record_send_result(
        self, batch_id: str, applicant_ref: str, ok: bool, email_id: Any = None, error: str = ""
    ) -> dict[str, Any]:
        """Record one item's outcome; the batch settles once all approved items resolve."""
        batch = self.load(batch_id)
        if batch["state"] != APPROVED:
            raise OutboxError("batch is not approved for sending")
        item = next((i for i in batch["items"] if i["applicant_ref"] == applicant_ref), None)
        if item is None:
            raise OutboxError("unknown applicant_ref in batch")
        target = ITEM_SENT if ok else ITEM_FAILED
        if target not in _ITEM_TRANSITIONS[item["status"]]:
            raise OutboxError(f"illegal item transition {item['status']} -> {target}")
        item["status"] = target
        item["email_id"] = str(email_id) if (ok and email_id is not None) else None
        item["error"] = None if ok else str(error)[:500]
        statuses = [i["status"] for i in batch["items"] if i["status"] != ITEM_DROPPED]
        if ITEM_APPROVED not in statuses:
            if all(s == ITEM_SENT for s in statuses):
                self._transition(batch, SENT)
            elif all(s == ITEM_FAILED for s in statuses):
                self._transition(batch, FAILED)
            else:
                self._transition(batch, PARTIAL)
        else:
            batch["updated_at"] = _now()
        self._write(_validate_batch(batch))
        return batch
