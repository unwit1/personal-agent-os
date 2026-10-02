"""Apply an organization plan: reversible IMAP moves, journal and undo.

Moves only: nothing here deletes, expunges or closes a mailbox. A mailbox is
reached only through the ``Mover`` protocol (``imap_write.ImapMover`` in
production, a fake in tests). Dry-run is the default and never connects.
"""
from __future__ import annotations

import itertools
import json
import os
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Protocol

from . import accounts as accounts_mod
from . import config
from .message import normalize_message_id

CATEGORIES = ("action_needed", "waiting_on_others", "receipts_finance", "newsletters_promotions",
              "notifications", "hr_applicants", "personal", "spam", "archive_old")
KEYWORD = "$AgentOSOrganized"
PLAN_MAX_AGE = timedelta(hours=24)
BATCH = 100
JOURNAL_NAME = "organize-journal.jsonl"
STALE = "plan is stale, run Organize inbox again"
UIDVALIDITY_CHANGED = "uidvalidity changed; run Organize inbox again"
CHANGED = "message changed or gone"
UNVERIFIED = "identity could not be verified"
NO_KEYWORD = "server supports neither MOVE nor keyword flags"


class OrganizeError(ValueError):
    pass


class UndoError(OrganizeError):
    pass


class Mover(Protocol):
    def capabilities(self, mailbox: str) -> dict[str, Any]: ...        # {"move": bool, "permanent_flags": [str]}
    def ensure_folder(self, logical_name: str) -> str: ...            # create + subscribe if missing; real name
    def select(self, mailbox: str) -> str: ...                         # SELECT read-write; returns UIDVALIDITY
    def message_ids(self, uids: list[str]) -> dict[str, str]: ...      # uid -> Message-ID header
    def move(self, uids: list[str], target: str) -> dict[str, str | None]: ...
    def copy_flag(self, uids: list[str], target: str) -> dict[str, str | None]: ...
    def unflag(self, uids: list[str]) -> None: ...
    def find(self, mailbox: str, rfc_message_id: str) -> str | None: ...
    def close(self) -> None: ...                                       # LOGOUT only


# ---------------------------------------------------------------------------
# Journal
# ---------------------------------------------------------------------------


def default_journal_path(scope: str = "work") -> Path:
    """Journal under the mail config home, one per scope (never used by tests)."""
    return config.scope_dir(scope) / JOURNAL_NAME


def read_journal(journal_path: Path) -> list[dict[str, Any]]:
    path = Path(journal_path)
    if not path.exists():
        return []
    lines = []
    for text in path.read_text(encoding="utf-8").splitlines():
        if text.strip():
            try:
                lines.append(json.loads(text))
            except json.JSONDecodeError:
                continue
    return lines


def _append_many(journal_path: Path, entries: list[dict[str, Any]]) -> None:
    """Append entries in one open and one fsync."""
    path = Path(journal_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        for entry in entries:
            handle.write(json.dumps(entry, sort_keys=True) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def _append(journal_path: Path, entry: dict[str, Any]) -> None:
    _append_many(journal_path, [entry])


def _now(now: datetime | None) -> datetime:
    return (now or datetime.now(timezone.utc)).astimezone(timezone.utc)


def _undo_command(journal_id: str, seq: int) -> str:
    return f"agent-os mail organize-undo --journal {journal_id} --seq {seq}"


def _final_lines(lines: list[dict[str, Any]]) -> dict[tuple[str, int], dict[str, Any]]:
    """Last non-pending line per (journal_id, seq)."""
    final: dict[tuple[str, int], dict[str, Any]] = {}
    for line in lines:
        if line.get("status") not in ("pending", "undone"):
            final[(line["journal_id"], int(line["seq"]))] = line
    return final


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _accounts_by_id(accounts: Any) -> dict[str, Any]:
    if accounts is None:
        accounts = accounts_mod.load_accounts()
    if isinstance(accounts, dict):
        return dict(accounts)
    return {account.id: account for account in accounts}


def _connect(connect: Callable[[Any], Mover] | None) -> Callable[[Any], Mover]:
    if connect is not None:
        return connect
    from . import imap_write  # imported lazily: only a real apply needs it
    return imap_write.connect_write


def _check_fresh(plan: dict[str, Any], now: datetime) -> None:
    try:
        generated = datetime.fromisoformat(str(plan.get("generated_at")))
    except ValueError as exc:
        raise OrganizeError(STALE) from exc
    if generated.tzinfo is None:
        generated = generated.replace(tzinfo=timezone.utc)
    if now - generated > PLAN_MAX_AGE:
        raise OrganizeError(STALE)


def _target_folder(plan: dict[str, Any], category: str) -> str | None:
    folders = plan.get("folders")
    if isinstance(folders, dict) and category in folders:
        return folders[category]
    for account in (plan.get("accounts") or {}).values():
        bucket = (account.get("categories") or {}).get(category)
        if bucket is not None:
            return bucket.get("target_folder")
    return None


def _verified(source: dict[str, Any], fetched: str | None, uidvalidity: str) -> str | None:
    """None when the message is the planned one, else the skip reason (R5-1).

    Compared through ``message.normalize_message_id``, the index's own
    normalization. Without a Message-ID the identity is the planned
    (mailbox, UIDVALIDITY, UID) from mail_sources, which must match the server.
    """
    planned = normalize_message_id(source.get("rfc_message_id"))
    if str(source.get("uidvalidity") or "") not in ("", str(uidvalidity)):
        return UIDVALIDITY_CHANGED
    if planned:
        seen = normalize_message_id(fetched)
        return None if seen == planned else CHANGED
    if fetched and normalize_message_id(fetched):
        return CHANGED
    if source.get("uidvalidity") in (None, "") or source.get("uid") in (None, ""):
        return UNVERIFIED
    return None


def _chunks(items: list[Any], size: int):
    for start in range(0, len(items), size):
        yield items[start:start + size]


def _next_seq(journal_path: Path, journal_id: str) -> int:
    return 1 + max([int(l["seq"]) for l in read_journal(journal_path) if l.get("journal_id") == journal_id] or [0])


# ---------------------------------------------------------------------------
# Apply
# ---------------------------------------------------------------------------


def apply_plan(plan: dict[str, Any], category: str, *, accounts: Any = None, only_accounts: list[str] | None = None,
               dry_run: bool = True, now: datetime | None = None, connect: Callable[[Any], Mover] | None = None,
               journal_path: Path | None = None, max_moves: int = 500, store: Any = None) -> dict[str, Any]:
    """Move one category's INBOX mail into its target folder, per enabled account.

    ``dry_run`` (default) reads only the plan and the account settings.
    ``store`` is an optional object with ``mark_source_moved(source_id)``.
    """
    if category not in CATEGORIES:
        raise OrganizeError(f"unknown category {category!r}")
    moment = _now(now)
    _check_fresh(plan, moment)
    target = _target_folder(plan, category)
    result: dict[str, Any] = {"dry_run": bool(dry_run), "plan_id": plan.get("plan_id"), "category": category,
                              "journal_id": None, "skipped_reason": None, "accounts": {}}
    if not target:
        result.update(skipped_reason=f"{category} stays in the INBOX (no target folder)", noop=True)
        return result
    known = _accounts_by_id(accounts)
    wanted = set(only_accounts) if only_accounts else None
    journal_id = None if dry_run else f"org_{moment:%Y%m%dT%H%M%S}_{secrets.token_hex(2)}"
    result["journal_id"] = journal_id
    path = Path(journal_path) if journal_path else default_journal_path(str(plan.get("scope") or "work"))
    budget = max(0, int(max_moves))
    counter = itertools.count(1)  # journal_id is fresh, so numbering starts at 1
    opener = None if dry_run else _connect(connect)
    for account_id, entry in (plan.get("accounts") or {}).items():
        if wanted is not None and account_id not in wanted:
            continue
        bucket = (entry.get("categories") or {}).get(category) or {}
        ids = list(bucket.get("message_ids") or [])
        sources = (plan.get("sources") or {}).get(account_id) or {}
        row = {"status": "dry_run" if dry_run else "moved", "method": None, "target_folder": target, "would_move": 0,
               "moved": 0, "failed": 0, "remaining": 0, "samples": list(bucket.get("samples") or [])[:5],
               "skipped": [], "error": None}
        result["accounts"][account_id] = row
        account = known.get(account_id)
        if account is None:
            row.update(status="error", error="account is not configured")
            continue
        if not getattr(account, "allow_organize", False):
            row.update(status="skipped_not_enabled", skipped_reason="allow_organize is off for this account")
            continue
        planned = []
        for message_id in ids:
            if message_id in sources:
                planned.append(message_id)
            else:
                row["skipped"].append({"message_id": message_id, "reason": "no source recorded in the plan"})
        row["remaining"] = max(0, len(planned) - budget)
        planned = planned[:budget]
        if dry_run:
            row["would_move"] = len(planned)
            continue
        budget -= _apply_account(account, plan, category, target, planned, sources, row, opener, path,
                                 journal_id, moment, store, counter)
    return result


def _apply_account(account, plan, category, target, ids, sources, row, opener, path, journal_id, moment, store,
                   counter) -> int:
    scope = plan.get("scope") or getattr(account, "mail_scope", None)
    by_mailbox: dict[str, list[str]] = {}
    for message_id in ids:
        by_mailbox.setdefault(sources[message_id].get("mailbox") or "INBOX", []).append(message_id)
    mover = None
    try:
        mover = opener(account)
        real_target = mover.ensure_folder(target)
        target_validity = mover.select(real_target)
        for mailbox, message_ids in by_mailbox.items():
            validity = mover.select(mailbox)
            caps = mover.capabilities(mailbox) or {}
            use_move = bool(caps.get("move"))
            flags = {str(f).lower() for f in (caps.get("permanent_flags") or [])}
            if not use_move and not ("\\*" in flags or KEYWORD.lower() in flags):
                row.update(status="error", error=NO_KEYWORD)
                return 0
            row["method"] = "move" if use_move else "copy_flag"
            for batch in _chunks(message_ids, BATCH):
                mover.select(mailbox)
                _apply_batch(mover, batch, sources, mailbox, validity, real_target, target_validity, use_move,
                             account, category, plan, scope, row, path, journal_id, moment, store, counter)
    except Exception as exc:  # per account: one connection error never stops the others
        row.update(status="error", error=f"{type(exc).__name__}: {str(exc)[:200]}")
    finally:
        if mover is not None:
            try:
                mover.close()
            except Exception:
                pass
    return row["moved"]


def _apply_batch(mover, batch, sources, mailbox, validity, real_target, target_validity, use_move, account,
                 category, plan, scope, row, path, journal_id, moment, store, counter) -> None:
    uids = [str(sources[m]["uid"]) for m in batch if sources[m].get("uid") not in (None, "")]
    fetched = mover.message_ids(uids) if uids else {}
    ready = []
    for message_id in batch:
        source = sources[message_id]
        uid = str(source.get("uid") or "")
        reason = _verified(source, fetched.get(uid), validity) if uid else UNVERIFIED
        if reason == UIDVALIDITY_CHANGED:
            row["skipped"].extend({"message_id": m, "reason": reason} for m in batch if m not in
                                  [s["message_id"] for s in row["skipped"]])
            return
        if reason:
            row["skipped"].append({"message_id": message_id, "reason": reason})
        else:
            ready.append((message_id, source, uid))
    if not ready:
        return
    seqs = {}
    pending = []
    for message_id, source, uid in ready:
        seq = seqs[message_id] = next(counter)
        pending.append(_line(journal_id, seq, "pending", moment, plan, category, account, scope, message_id, source,
                             mailbox, validity, real_target, target_validity, None,
                             "move" if use_move else "copy_flag", None))
    _append_many(path, pending)
    error = None
    mapping: dict[str, str | None] = {}
    try:
        uid_list = [uid for _, _, uid in ready]
        mapping = (mover.move if use_move else mover.copy_flag)(uid_list, real_target) or {}
    except Exception as exc:
        error = f"{type(exc).__name__}: {str(exc)[:200]}"
    for message_id, source, uid in ready:
        status, new_uid = "failed", None
        rfc = source.get("rfc_message_id")
        if error is None:
            new_uid = mapping.get(uid)
            found = mover.find(real_target, rfc) if rfc else None
            new_uid = new_uid or found
            ok = bool(found) if rfc else bool(new_uid)
            status = "moved" if ok else "unverified"
            mover.select(mailbox)
        elif rfc:
            # the call raised, but it may have moved some messages first: probe so those stay undoable
            try:
                found = mover.find(real_target, rfc)
                mover.select(mailbox)
            except Exception:
                found = None
            if found:
                status, new_uid = "moved", found
        line = _line(journal_id, seqs[message_id], status, moment, plan, category, account, scope, message_id, source,
                     mailbox, validity, real_target, target_validity, new_uid, "move" if use_move else "copy_flag",
                     error)
        _append(path, line)
        if status == "moved":
            row["moved"] += 1
            if store is not None and source.get("source_id") is not None:
                store.mark_source_moved(source["source_id"])
        elif status == "failed":
            row["failed"] += 1
            row["skipped"].append({"message_id": message_id, "reason": error or "move failed"})
        else:
            row["failed"] += 1
            row["skipped"].append({"message_id": message_id, "reason": "unverified: not found in target after move"})


def _line(journal_id, seq, status, moment, plan, category, account, scope, message_id, source, mailbox, validity,
          real_target, target_validity, new_uid, method, error) -> dict[str, Any]:
    entry = {"journal_id": journal_id, "seq": seq, "ts": moment.isoformat(), "status": status,
             "plan_id": plan.get("plan_id"), "category": category, "account_id": account.id, "scope": scope,
             "message_id": message_id, "rfc_message_id": source.get("rfc_message_id"),
             "source_id": source.get("source_id"),
             "from": {"mailbox": mailbox, "uidvalidity": str(validity), "uid": str(source.get("uid"))},
             "to": {"mailbox": real_target, "uidvalidity": str(target_validity), "uid": new_uid},
             "method": method, "error": error}
    if status in ("moved", "unverified"):
        verb = "UID MOVE" if method == "move" else "UID COPY"
        back = (f"{verb} {new_uid or '?'} from {real_target} back to {mailbox}" if method == "move"
                else f"clear {KEYWORD} on UID {source.get('uid')} in {mailbox} (the copy in {real_target} remains)")
        entry["undo"] = {"command": _undo_command(journal_id, seq), "steps": [back]}
    return entry


# ---------------------------------------------------------------------------
# Undo
# ---------------------------------------------------------------------------


def _locate_journal(journal_id: str, journal_path: Path | None, scope: str | None) -> Path:
    """Explicit path, else the given scope's journal, else whichever scope journal holds the id."""
    if journal_path:
        return Path(journal_path)
    if scope:
        return default_journal_path(scope)
    for candidate in ("work", "personal"):
        path = default_journal_path(candidate)
        if any(line.get("journal_id") == journal_id for line in read_journal(path)):
            return path
    return default_journal_path("work")


def undo(journal_id: str, *, seq: int | None = None, dry_run: bool = True, accounts: Any = None,
         connect: Callable[[Any], Mover] | None = None, journal_path: Path | None = None,
         now: datetime | None = None, store: Any = None, scope: str | None = None) -> dict[str, Any]:
    """Reverse one move (``seq``) or a whole journal batch; journaled as ``undone``.

    Raises ``UndoError`` when everything asked for was already undone.
    """
    path = _locate_journal(journal_id, journal_path, scope)
    lines = read_journal(path)
    counter = itertools.count(1 + max([int(l["seq"]) for l in lines if l.get("journal_id") == journal_id] or [0]))
    finals = _final_lines(lines)
    done = {int(l["undone_of"]) for l in lines if l.get("status") == "undone" and l.get("journal_id") == journal_id}
    pending_seqs = {int(l["seq"]) for l in lines if l.get("journal_id") == journal_id and l.get("status") == "pending"}
    wanted = [seq] if seq is not None else sorted({s for (j, s) in finals if j == journal_id} | pending_seqs)
    if not wanted or not any(l.get("journal_id") == journal_id for l in lines):
        raise UndoError(f"no journal entry for {journal_id}")
    result: dict[str, Any] = {"dry_run": bool(dry_run), "journal_id": journal_id, "undone": [], "would_undo": [],
                              "skipped": []}
    todo = []
    for number in wanted:
        entry = finals.get((journal_id, number))
        if number in done:
            result["skipped"].append({"seq": number, "reason": "already undone"})
        elif entry is None:
            result["skipped"].append({"seq": number, "reason": "no final journal line"})
        elif entry["status"] == "failed":
            result["skipped"].append({"seq": number, "reason": "move had failed; nothing to undo"})
        else:
            todo.append(entry)
    if not todo and wanted and all(n in done for n in wanted):
        raise UndoError(f"{journal_id} is already undone")
    if dry_run:
        result["would_undo"] = [e["seq"] for e in todo]
        return result
    known = _accounts_by_id(accounts)
    opener = _connect(connect)
    by_account: dict[str, list[dict[str, Any]]] = {}
    for entry in todo:
        by_account.setdefault(entry["account_id"], []).append(entry)
    moment = _now(now)
    for account_id, entries in by_account.items():
        account = known.get(account_id)
        if account is None or not getattr(account, "allow_organize", False):
            result["skipped"].extend({"seq": e["seq"], "reason": "account not enabled for organizing"} for e in entries)
            continue
        mover = None
        try:
            mover = opener(account)
            for entry in entries:
                reason = _undo_one(mover, entry)
                if reason:
                    result["skipped"].append({"seq": entry["seq"], "reason": reason})
                    continue
                _append(path, {"journal_id": journal_id, "seq": next(counter), "ts": moment.isoformat(),
                               "status": "undone", "undone_of": entry["seq"], "plan_id": entry.get("plan_id"),
                               "category": entry.get("category"), "account_id": account_id,
                               "scope": entry.get("scope"), "message_id": entry.get("message_id"),
                               "rfc_message_id": entry.get("rfc_message_id"), "from": entry["to"],
                               "to": entry["from"], "method": entry.get("method"), "error": None})
                result["undone"].append(entry["seq"])
                if store is not None and entry.get("source_id") is not None:
                    store.mark_source_present(entry["source_id"])
        except Exception as exc:
            result["skipped"].extend({"seq": e["seq"], "reason": f"{type(exc).__name__}: {str(exc)[:200]}"}
                                     for e in entries if e["seq"] not in result["undone"])
        finally:
            if mover is not None:
                try:
                    mover.close()
                except Exception:
                    pass
    return result


def _undo_one(mover: Mover, entry: dict[str, Any]) -> str | None:
    source, target = entry["from"], entry["to"]
    rfc = entry.get("rfc_message_id")
    if entry.get("method") == "copy_flag":
        validity = mover.select(source["mailbox"])
        if str(validity) != str(source["uidvalidity"]):
            return UIDVALIDITY_CHANGED
        mover.unflag([str(source["uid"])])  # the copy in the target stays: Agent OS never deletes
        return None
    validity = mover.select(target["mailbox"])
    uid = None
    if target.get("uid") and str(validity) == str(target.get("uidvalidity")):
        uid = str(target["uid"])
        if rfc and normalize_message_id(mover.message_ids([uid]).get(uid)) != normalize_message_id(rfc):
            uid = None
    if uid is None and rfc:
        uid = mover.find(target["mailbox"], rfc)
        mover.select(target["mailbox"])
    if uid is None:
        if rfc and mover.find(source["mailbox"], rfc):
            return "already back in source folder"
        return CHANGED
    mover.move([uid], source["mailbox"])
    if rfc and not mover.find(source["mailbox"], rfc):
        return "unverified: not found in source after undo"
    return None
