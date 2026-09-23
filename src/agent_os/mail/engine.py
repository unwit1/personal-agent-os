"""Restart-safe, incremental, read-only sync of IMAP accounts into the index.

Per mailbox:

1. EXAMINE (read-only) and read UIDVALIDITY / UIDNEXT / HIGHESTMODSEQ.
2. If UIDVALIDITY changed, the old UID namespace is retired (observations kept,
   marked ``stale_uidvalidity``) and the mailbox is scanned again.
3. List all UIDs (a UID list is small; bodies are not fetched).
4. New work: on the first run the newest ``limit`` messages; afterwards UIDs
   above the high-water mark, oldest first, up to ``limit`` per run.
   ``backfill`` pulls up to that many older messages below the backfill mark.
5. Overlap check: the ``overlap`` most recent known UIDs get a metadata-only
   fetch (size, internal date, flags). IMAP message content is immutable for a
   UID within one UIDVALIDITY, so a size/date mismatch means a non-compliant
   server and triggers a full refetch; flags are updated in place. UIDNEXT is
   only a hint. With CONDSTORE and a known HIGHESTMODSEQ, flag changes for the
   whole mailbox come from ``CHANGEDSINCE``.
6. Known UIDs absent from the complete listing are marked ``missing``; nothing
   is deleted.
7. Full bodies are fetched in batches with ``BODY.PEEK[]``. Each batch: parse,
   index, commit SQLite, *then* mark ledger items processed and save the
   ledger once. A crash replays at most one batch, idempotently.

Progress (state, counts, marks) is saved after every batch, so an interrupted
sync resumes where it stopped. A mailbox is reported ``ok`` only when every
step succeeded; otherwise ``partial`` with a sanitized error category.
"""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any, Callable

from ..ingestion import IngestionLedger, stable_stage_id, stable_work_id
from ..timestamps import utc_now_iso as now
from . import config
from .accounts import Account, AccountError, get_secret
from .imap import MailError, ReadOnlyIMAP, categorize, connect
from .message import ParsedMessage, parse
from .store import Store, live_source_id

PROCESSOR_VERSION = "mail-index@2"
DEFAULT_LIMIT = 200
DEFAULT_BATCH = 25

Progress = Callable[[dict[str, Any]], None]


def ledger_for(account: Account, mailbox: str, ledger_dir: Path) -> IngestionLedger:
    scope = f"{account.provider}/{account.id}/{mailbox}"
    work_id = stable_work_id("mail-imap", scope)
    name = hashlib.sha256(mailbox.encode("utf-8")).hexdigest()[:16]
    return IngestionLedger(
        ledger_dir / account.id / f"{name}.json",
        source="mail-imap",
        work_id=work_id,
        stage_id=stable_stage_id(work_id, "sync"),
        processor_version=PROCESSOR_VERSION,
    )


def source_key(account: Account, mailbox: str, uidvalidity: str, uid: int | str) -> str:
    return f"{account.provider}/{account.id}/{mailbox}/{uidvalidity}/{uid}"


class Counter(dict):
    def bump(self, key: str, amount: int = 1) -> None:
        self[key] = self.get(key, 0) + amount


def index_records(
    records: list[Any],
    *,
    account: Account,
    mailbox: str,
    uidvalidity: str,
    store: Store,
    ledger: IngestionLedger,
    counts: Counter,
    parser: Callable[[bytes], ParsedMessage] = parse,
    exporter: Any = None,
) -> list[int]:
    """Index one batch; returns UIDs now durably indexed or already current."""
    done: list[int] = []
    completed: list[str] = []
    with ledger.deferred_saves():
        for record in records:
            if record.raw is None:
                continue
            key = source_key(account, mailbox, uidvalidity, record.uid)
            counts.bump("checked")
            result = ledger.enqueue(key, content=record.raw)
            if result["status"] == "processed":
                counts.bump("skipped")
                done.append(record.uid)
                continue
            if result["status"] == "error":
                counts.bump("errors")
                continue
            counts.bump({"queued": "indexed_new", "requeued": "reprocessed"}.get(result["action"], "resumed"))
            claimed = ledger.claim(1, item_ids=[result["item_id"]])
            if not claimed:
                continue
            item_id = claimed[0]["item_id"]
            store.conn.execute("SAVEPOINT mail_record")
            try:
                parsed = parser(record.raw)
                outcome = store.record(parsed, {
                    "id": live_source_id(account.provider, account.id, mailbox, uidvalidity, str(record.uid)),
                    "source_kind": "live_imap", "provider": account.provider, "account_id": account.id, "mailbox": mailbox,
                    "uidvalidity": uidvalidity, "uid": str(record.uid), "size": record.size, "internal_date": record.internal_date, "flags": record.flags,
                })
                store.conn.execute("RELEASE mail_record")
                if outcome["action"] == "merged":
                    counts.bump("deduplicated")
                completed.append(item_id)
                done.append(record.uid)
            except Exception as exc:
                store.conn.execute("ROLLBACK TO mail_record")
                store.conn.execute("RELEASE mail_record")
                ledger.fail(item_id, categorize(exc) if isinstance(exc, MailError) else type(exc).__name__, retryable=True)
                counts.bump("errors")
        store.conn.commit()
        # Only after the index is durable.
        for item_id in completed:
            ledger.complete(item_id, [f"mail:{account.id}:{mailbox}:{uidvalidity}"])
        if exporter is not None:
            for record in records:
                if record.raw is not None and record.uid in done:
                    try:
                        exporter.export(record.raw, live_source_id(account.provider, account.id, mailbox, uidvalidity, str(record.uid)))
                    except Exception:
                        counts.bump("attachment_errors")
        if records:
            ledger.checkpoint(str(max(record.uid for record in records)), checked=counts.get("checked", 0), errors=counts.get("errors", 0))
    return done


def sync_mailbox(
    client: ReadOnlyIMAP,
    account: Account,
    mailbox: str,
    store: Store,
    *,
    ledger_dir: Path,
    limit: int = DEFAULT_LIMIT,
    backfill: int = 0,
    batch: int = DEFAULT_BATCH,
    progress: Progress | None = None,
    exporter: Any = None,
) -> dict[str, Any]:
    started = time.monotonic()
    counts = Counter()
    state = store.mailbox_state(account.id, mailbox)
    state.update(last_started=now(), last_status="running", last_error=None)
    result: dict[str, Any] = {"account_id": account.id, "provider": account.provider, "mailbox": mailbox, "read_only": True}
    try:
        info = client.examine(mailbox)
        uidvalidity = info.uidvalidity or "unknown"
        if state.get("uidvalidity") and state["uidvalidity"] != uidvalidity:
            result["uidvalidity_changed"] = {"from": state["uidvalidity"], "to": uidvalidity, "retired_observations": store.retire_namespace(account.id, mailbox, state["uidvalidity"])}
            state.update(high_water_uid=None, backfill_low_uid=None, highestmodseq=None)
        state.update(uidvalidity=uidvalidity, uidnext=info.uidnext)
        store.save_mailbox_state(state)
        store.conn.commit()

        ledger = ledger_for(account, mailbox, ledger_dir)
        retried = ledger.retry_errors()
        if retried:
            counts.bump("retried_errors", retried)
        server = client.uid_search_all()
        present = set(server)
        known = store.known_uids(account.id, mailbox, uidvalidity)
        high = state.get("high_water_uid")
        if high is None:
            new = server[-max(limit, 0):] if limit else []
        else:
            new = [uid for uid in server if uid > high][: max(limit, 0)]
        low = state.get("backfill_low_uid") or (min(new) if new else (min(known) if known else None))
        older = [uid for uid in server if low is not None and uid < low and uid not in known][-backfill:] if backfill else []

        mode = "overlap"
        overlap_uids = sorted(uid for uid in known if uid in present)[-max(account.overlap, 0):] if account.overlap else []
        refetch: list[int] = []
        if "CONDSTORE" in client.capabilities and info.highestmodseq and state.get("highestmodseq"):
            mode = "condstore"
            for record in client.fetch(sorted(known.keys() & present), body=False, changed_since=int(state["highestmodseq"])) if known else []:
                row = known.get(record.uid)
                if row is not None and record.flags != (row["flags"] or ""):
                    store.update_flags(row["id"], record.flags)
                    counts.bump("flags_updated")
        for chunk in _chunks(overlap_uids, 200):
            for record in client.fetch(chunk, body=False):
                row = known.get(record.uid)
                if row is None:
                    continue
                if (row["size"] is not None and record.size is not None and row["size"] != record.size) or (row["internal_date"] and record.internal_date and row["internal_date"] != record.internal_date):
                    refetch.append(record.uid)
                elif mode == "overlap" and record.flags != (row["flags"] or ""):
                    store.update_flags(row["id"], record.flags)
                    counts.bump("flags_updated")
        counts.bump("missing", store.mark_missing(account.id, mailbox, uidvalidity, present))
        store.conn.commit()

        # New messages newest-first on the first run, oldest-first afterwards;
        # then refetches; then backfill (newest of the older ones first).
        wanted = [uid for uid in new if uid not in known] + refetch + sorted(older, reverse=True)
        counts.bump("to_fetch", len(wanted))
        for chunk in _chunks(wanted, max(batch, 1)):
            records = client.fetch(chunk, body=True)
            counts.bump("fetched", len(records))
            done = index_records(records, account=account, mailbox=mailbox, uidvalidity=uidvalidity, store=store, ledger=ledger, counts=counts, exporter=exporter)
            finished = [uid for uid in done if uid in set(chunk)]
            forward = [uid for uid in finished if high is None or uid > high]
            if forward:
                state["high_water_uid"] = max([state.get("high_water_uid") or 0, *forward])
            below = [uid for uid in finished if low is not None and uid < low] + ([min(finished)] if finished and state.get("backfill_low_uid") is None else [])
            if below:
                state["backfill_low_uid"] = min([uid for uid in [state.get("backfill_low_uid"), *below] if uid is not None])
            state["counts"] = dict(counts)
            store.save_mailbox_state(state)
            store.conn.commit()
            if progress:
                progress({"account_id": account.id, "mailbox": mailbox, "fetched": counts.get("fetched", 0), "to_fetch": len(wanted), "indexed_new": counts.get("indexed_new", 0)})
        if high is None and not wanted and server:
            state["high_water_uid"] = max(server)
        if state.get("backfill_low_uid") is None and server:
            state["backfill_low_uid"] = min(new) if new else min(server)
        remaining = [uid for uid in server if state.get("backfill_low_uid") and uid < state["backfill_low_uid"] and uid not in known and uid not in wanted]
        state.update(
            server_count=len(server),
            highestmodseq=info.highestmodseq,
            capability_mode=mode,
            last_status="ok" if not counts.get("errors") else "partial",
            last_error=None if not counts.get("errors") else f"{counts['errors']} message(s) failed; they are retried next sync",
            counts=dict(counts),
        )
        if not counts.get("errors"):
            state["last_completed"] = now()
        result.update(dict(counts), uidvalidity=uidvalidity, capability_mode=mode, server_messages=len(server), older_not_indexed=len(remaining), status=state["last_status"])
    except Exception as exc:
        category = categorize(exc)
        state.update(last_status="partial", last_error=category)
        result.update(dict(counts), status="partial", error=category)
    finally:
        state["counts"] = dict(counts)
        store.save_mailbox_state(state)
        store.conn.commit()
        result["seconds"] = round(time.monotonic() - started, 2)
    return result


def sync_account(
    account: Account,
    *,
    store_path: Path | None = None,
    ledger_dir: Path | None = None,
    limit: int = DEFAULT_LIMIT,
    backfill: int = 0,
    batch: int = DEFAULT_BATCH,
    mailboxes: list[str] | None = None,
    connect_factory: Any = None,
    progress: Progress | None = None,
    exporter: Any = None,
) -> dict[str, Any]:
    started = time.monotonic()
    result: dict[str, Any] = {"account_id": account.id, "provider": account.provider, "read_only": True, "mailboxes": []}
    if not account.enabled:
        return {**result, "status": "disabled"}
    try:
        secret = get_secret(account)
    except AccountError:
        record_auth(account.id, False, "credential_missing")
        return {**result, "status": "not_configured", "error": "credential_missing"}
    client = None
    try:
        client = connect(account.host, account.port, security=account.tls, factory=connect_factory)
        client.login(account.login_name, secret)
        record_auth(account.id, True, None)
        names = mailboxes or account.folders or ["INBOX"]
        if "*" in names:
            names = [name for name in client.list_mailboxes() if name not in set(account.exclude_folders)]
        with Store(store_path or config.DB) as store:
            for name in names:
                result["mailboxes"].append(sync_mailbox(client, account, name, store, ledger_dir=ledger_dir or config.LEDGER_DIR, limit=limit, backfill=backfill, batch=batch, progress=progress, exporter=exporter))
        statuses = {item.get("status") for item in result["mailboxes"]}
        result["status"] = "ok" if statuses <= {"ok"} else "partial"
    except MailError as exc:
        if exc.category in {"auth_failed"}:
            record_auth(account.id, False, exc.category)
        result.update(status="failed", error=exc.category)
    except Exception as exc:
        result.update(status="failed", error=categorize(exc))
    finally:
        if client is not None:
            client.logout()
        del secret
    result["seconds"] = round(time.monotonic() - started, 2)
    for key in ("indexed_new", "deduplicated", "reprocessed", "skipped", "errors", "fetched", "missing", "flags_updated"):
        result[key] = sum(item.get(key, 0) for item in result["mailboxes"])
    log_sync(result)
    return result


def health(account: Account, *, connect_factory: Any = None) -> dict[str, Any]:
    """Log in and out; no mailbox is opened."""
    try:
        secret = get_secret(account)
    except AccountError:
        return {"account_id": account.id, "provider": account.provider, "ok": False, "error": "credential_missing"}
    try:
        client = connect(account.host, account.port, security=account.tls, factory=connect_factory)
        client.login(account.login_name, secret)
        capabilities = sorted(item for item in client.capabilities if item in {"CONDSTORE", "QRESYNC", "IDLE", "UIDPLUS", "IMAP4REV1", "IMAP4REV2"})
        client.logout()
        record_auth(account.id, True, None)
        return {"account_id": account.id, "provider": account.provider, "ok": True, "capabilities": capabilities}
    except MailError as exc:
        record_auth(account.id, False, exc.category)
        return {"account_id": account.id, "provider": account.provider, "ok": False, "error": exc.category}


# ---------------------------------------------------------------------------
# Local state and log (counts only; no content, no secrets)
# ---------------------------------------------------------------------------


def _state_path() -> Path:
    return config.LOCAL_DIR / "account-state.json"


def account_state() -> dict[str, Any]:
    try:
        return json.loads(_state_path().read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def record_auth(account_id: str, ok: bool, category: str | None) -> None:
    state = account_state()
    state[account_id] = {"auth_ok": ok, "auth_error": category, "checked_at": now()}
    path = _state_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=1), encoding="utf-8")


def log_sync(result: dict[str, Any]) -> None:
    line = {
        "at": now(), "account_id": result.get("account_id"), "provider": result.get("provider"), "status": result.get("status"),
        "error": result.get("error"), "seconds": result.get("seconds"),
        "mailboxes": [{key: item.get(key) for key in ("mailbox", "status", "error", "capability_mode", "indexed_new", "deduplicated", "reprocessed", "skipped", "errors", "fetched", "missing", "flags_updated", "server_messages", "older_not_indexed", "seconds")} for item in result.get("mailboxes", [])],
    }
    try:
        config.LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with config.LOG_FILE.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(line) + "\n")
    except OSError:
        pass


def _chunks(items: list[int], size: int) -> list[list[int]]:
    return [items[index:index + size] for index in range(0, len(items), size)]
