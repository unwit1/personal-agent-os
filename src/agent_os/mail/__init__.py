"""Provider-neutral, read-only mail: accounts, sync, search, threads.

Supports several accounts of iCloud and EarthLink (and future IMAP
providers) plus archive records (e.g. a PST import) in one local index under
``.agent-local/mail``. See ``docs/integrations/mail.md``.

Phase 1 is read-only: there is no send, delete, move, flag or mark-read path,
and IMAP mailboxes are opened read-only through ``imap.ReadOnlyIMAP``.

The single-account iCloud API of schema v1 (``setup_icloud``, ``sync()``
without an account, ``get_message(uid, mailbox)``, ``sync_records``) keeps
working; an existing ``icloud.json`` becomes the ``icloud`` account and an
existing index is migrated in place (with a backup).
"""

from __future__ import annotations

import email
import imaplib
import ssl
from dataclasses import dataclass
from email.message import Message
from pathlib import Path
from typing import Any, Callable, Iterable

from ..ingestion import IngestionLedger, stable_stage_id, stable_work_id
from . import accounts as accounts_lib
from . import config
from .accounts import PROVIDERS, Account, AccountError
from .imap import FetchedRecord, MailError, ReadOnlyIMAP
from .message import ParsedMessage, body_text, decode, parse
from .store import Store, archive_source_id, live_source_id
from .engine import DEFAULT_LIMIT, account_state, index_records, sync_account, sync_mailbox
from .engine import health as account_health

LOCAL_DIR = config.LOCAL_DIR
CONFIG = config.LEGACY_CONFIG
DB = config.DB
INGESTION_PROCESSOR_VERSION = "mail-index@1"  # legacy sync_records ledgers keep their version


def _target(scope: str | None, db_path: Path | None) -> Path:
    """The index to use: an explicit path, a scope's index, or the older
    single combined index while it still exists (before the scope split)."""
    if db_path:
        return Path(db_path)
    if scope:
        return config.db_for(scope)
    if DB.exists():
        return DB
    raise ValueError("choose a mail scope: work or personal")


@dataclass
class MailMessage:
    """Schema v1 record shape, kept for existing importers."""

    uid: str
    mailbox: str
    subject: str
    sender: str
    recipients: str
    date: str
    message_id: str
    body: str


def _decode(value: str | None) -> str:
    return decode(value)


def _body(msg: Message) -> str:
    return body_text(msg)


def _parse_record(uid: str, mailbox: str, raw_message: bytes) -> ParsedMessage:
    return parse(raw_message)


# ---------------------------------------------------------------------------
# Accounts
# ---------------------------------------------------------------------------


def list_accounts(scope: str | None = None) -> dict[str, Any]:
    """``mail.accounts``: configured accounts, never a credential."""
    items = [item for item in accounts_lib.load_accounts() if scope is None or item.mail_scope == scope]
    auth = account_state()
    return {
        "accounts": [account.public() | {"auth": auth.get(account.id)} for account in items],
        "providers": {name: {"label": value["label"], "imap": f"{value['imap_host']}:{value['imap_port']}", "credential": value["credential_label"]} for name, value in PROVIDERS.items()},
        "read_only": True,
    }


def account_status(account_id: str, db_path: Path | None = None) -> dict[str, Any]:
    """``mail.account_status``: auth state, mailboxes, counts, last sync."""
    account = accounts_lib.get_account(account_id)
    target = db_path or (DB if DB.exists() else config.db_for(account.mail_scope))
    mailboxes: list[dict[str, Any]] = []
    indexed = 0
    if target.exists():
        with Store(target) as store:
            mailboxes = store.mailboxes(account.id)
            indexed = store.counts()["observations_by_account"].get(account.id, 0)
    return {
        **account.public(),
        "auth": account_state().get(account.id),
        "indexed_observations": indexed,
        "mailboxes": [_mailbox_view(item) for item in mailboxes],
        "caught_up": bool(mailboxes) and all(item.get("last_status") == "ok" for item in mailboxes),
    }


def _mailbox_view(item: dict[str, Any]) -> dict[str, Any]:
    counts = item.get("counts") or {}
    return {
        "mailbox": item["mailbox"],
        "status": item.get("last_status"),
        "error": item.get("last_error"),
        "last_started": item.get("last_started"),
        "last_completed": item.get("last_completed"),
        "server_messages": item.get("server_count"),
        "capability_mode": item.get("capability_mode"),
        "uidvalidity": item.get("uidvalidity"),
        "last_run": {key: counts.get(key, 0) for key in ("fetched", "indexed_new", "deduplicated", "skipped", "errors", "missing", "flags_updated")},
    }


def setup_icloud(address: str, password: str) -> dict[str, Any]:
    """Schema v1 entry point: add (or reuse) the ``icloud`` account, store the
    app-specific password in the keyring, and check it."""
    address = address.strip()
    if "@" not in address:
        raise ValueError("Enter the full iCloud email address.")
    try:
        account = accounts_lib.get_account(accounts_lib.LEGACY_ACCOUNT_ID)
    except AccountError:
        account = accounts_lib.add_account("icloud", accounts_lib.LEGACY_ACCOUNT_ID, address, label="iCloud")
    stored = False
    try:
        accounts_lib.set_secret(account.id, password)
        stored = True
    except AccountError:
        pass
    result = account_health(account) if stored else {"ok": False, "error": "credential_missing"}
    return {
        "configured": True, "account_id": account.id, "authenticated": bool(result.get("ok")), "credential_stored": stored,
        "next": "Credential stored in the OS keyring." if stored else f"keyring is not installed; set {accounts_lib.env_name(account.id)} locally before sync.",
    }


def health(account_id: str | None = None) -> dict[str, Any]:
    items = [accounts_lib.get_account(account_id)] if account_id else [item for item in accounts_lib.load_accounts() if item.enabled]
    if not items:
        raise ValueError("No mail account is configured; run: agent-os mail account add")
    return {"accounts": [account_health(item) for item in items], "read_only": True}


# ---------------------------------------------------------------------------
# Sync
# ---------------------------------------------------------------------------


def _connect() -> Any:
    """Schema v1 connection for the single iCloud account (kept for callers
    that inject a client). New code syncs through accounts."""
    account = accounts_lib.get_account(accounts_lib.LEGACY_ACCOUNT_ID)
    client = imaplib.IMAP4_SSL(account.host, account.port, ssl_context=ssl.create_default_context())
    try:
        client.login(account.login_name, accounts_lib.get_secret(account))
    except Exception:
        client.logout()
        raise ValueError("iCloud authentication failed.") from None
    return client


def sync(limit: int = DEFAULT_LIMIT, mailbox: str | None = None, account_id: str | None = None, backfill: int = 0, all_enabled: bool = True,
         scope: str | None = None) -> dict[str, Any]:
    """``mail.sync``: one account, or every enabled account.

    With no account configured, falls back to the schema v1 single-iCloud
    path through ``_connect``.
    """
    configured = accounts_lib.load_accounts()
    if not configured:
        return _legacy_sync(limit, mailbox or "INBOX")
    targets = [accounts_lib.get_account(account_id)] if account_id else [item for item in configured if item.enabled] if all_enabled else []
    if config.DB.exists() and DB == config.DB and not any(config.db_for(scope).exists() for scope in config.SCOPES):
        from .scopes import split_combined_index

        split_combined_index()
    if scope:
        targets = [item for item in targets if item.mail_scope == config.check_scope(scope)]
    from . import attachments

    exporters = {name: attachments.Exporter(name) for name in {item.mail_scope for item in targets}} if attachments.enabled() else {}
    try:
        results = [sync_account(item, store_path=config.db_for(item.mail_scope), ledger_dir=config.ledger_dir_for(item.mail_scope), limit=limit, backfill=backfill,
                                mailboxes=[mailbox] if mailbox else None, exporter=exporters.get(item.mail_scope)) for item in targets]
    finally:
        for exporter in exporters.values():
            exporter.close()
    totals = {key: sum(item.get(key, 0) for item in results) for key in ("indexed_new", "deduplicated", "reprocessed", "skipped", "errors", "fetched", "missing")}
    return {"accounts": results, **totals, "complete": all(item.get("status") == "ok" for item in results), "read_only": True}


def _legacy_sync(limit: int, mailbox: str) -> dict[str, Any]:
    client = ReadOnlyIMAP(_connect())
    legacy = Account(id=accounts_lib.LEGACY_ACCOUNT_ID, provider="icloud", email="", legacy=True, overlap=0)
    try:
        with Store(DB) as store:
            result = sync_mailbox(client, legacy, mailbox, store, ledger_dir=DB.parent / "ledgers", limit=limit)
    finally:
        client.logout()
    return result


def sync_records(
    records: Iterable[tuple[str, bytes]],
    *,
    mailbox: str = "INBOX",
    db_path: Path | None = None,
    ledger_path: Path | None = None,
    parser: Callable[[str, str, bytes], ParsedMessage] = _parse_record,
    account_id: str = accounts_lib.LEGACY_ACCOUNT_ID,
    provider: str = "icloud",
    uidvalidity: str | None = None,
) -> dict[str, Any]:
    """Index already-fetched ``(uid, raw RFC822)`` records one at a time.

    The fixture-friendly boundary kept from schema v1: SQLite commits before
    the ledger marks an item processed, so a crash between the two replays
    safely. Ledger identity and keys are unchanged from v1, so existing
    ledgers keep recognising their items.
    """
    target_db = db_path or DB
    work_id = stable_work_id("icloud-mail", mailbox)
    ledger = IngestionLedger(
        ledger_path or target_db.parent / "ingestion.json",
        source="icloud-mail",
        work_id=work_id,
        stage_id=stable_stage_id(work_id, "sync"),
        processor_version=INGESTION_PROCESSOR_VERSION,
    )
    counts = {"indexed_new": 0, "reprocessed": 0, "resumed": 0, "skipped": 0, "errors": 0, "checked": 0, "deduplicated": 0}
    with Store(target_db) as store:
        for uid, raw_message in records:
            uid, raw_message = str(uid), bytes(raw_message)
            counts["checked"] += 1
            result = ledger.enqueue(f"{mailbox}:{uid}", content=raw_message)
            if result["action"] == "queued":
                counts["indexed_new"] += 1
            elif result["action"] == "requeued":
                counts["reprocessed"] += 1
            elif result["status"] == "queued":
                counts["resumed"] += 1
            else:
                counts["skipped" if result["status"] == "processed" else "errors"] += 1
                ledger.checkpoint(uid, checked=counts["checked"], processed=counts["checked"] - counts["skipped"] - counts["errors"])
                continue
            claimed = ledger.claim(1, item_ids=[result["item_id"]])
            if not claimed:
                continue
            item_id = claimed[0]["item_id"]
            try:
                parsed = parser(uid, mailbox, raw_message)
                outcome = store.record(parsed, {
                    "id": live_source_id(provider, account_id, mailbox, uidvalidity, uid), "source_kind": "live_imap", "provider": provider,
                    "account_id": account_id, "mailbox": mailbox, "uidvalidity": uidvalidity, "uid": uid, "legacy": uidvalidity is None,
                })
                store.conn.commit()
                if outcome["action"] == "merged":
                    counts["deduplicated"] += 1
                ledger.complete(item_id, [f"mail:{mailbox}:{uid}"])
                ledger.checkpoint(uid, checked=counts["checked"], processed=counts["checked"] - counts["skipped"] - counts["errors"])
            except Exception as exc:
                store.conn.rollback()
                ledger.fail(item_id, type(exc).__name__, retryable=True)
                counts["errors"] += 1
                ledger.checkpoint(uid, checked=counts["checked"], processed=counts["checked"] - counts["skipped"] - counts["errors"])
    return {"mailbox": mailbox, **counts, "read_only": True}


def sync_archive_records(
    records: Iterable[dict[str, Any]],
    *,
    archive_id: str,
    source_kind: str = "pst_archive",
    db_path: Path | None = None,
    ledger_dir: Path | None = None,
) -> dict[str, Any]:
    """Index archive records (e.g. from a PST export) into the same index.

    Each record: ``{"folder": str, "record_key": str, "raw": bytes}`` with
    ``raw`` an RFC822 message. An archive copy of a mail that is also indexed
    live becomes a second observation of the same logical message; both stay
    searchable and attributable.
    """
    archive_id = accounts_lib.check_account_id(archive_id)
    work_id = stable_work_id("mail-archive", archive_id)
    ledger = IngestionLedger(
        (ledger_dir or config.ledger_dir_for("work")) / "archives" / f"{archive_id}.json",
        source="mail-archive", work_id=work_id, stage_id=stable_stage_id(work_id, "import"), processor_version="mail-archive@1",
    )
    counts = {"indexed_new": 0, "deduplicated": 0, "reprocessed": 0, "skipped": 0, "errors": 0, "checked": 0}
    # Archives are Outlook backups of work mail: always the work index.
    with Store(db_path or config.db_for("work")) as store, ledger.deferred_saves():
        completed = []
        for record in records:
            folder, key, raw = str(record["folder"]), str(record["record_key"]), bytes(record["raw"])
            counts["checked"] += 1
            result = ledger.enqueue(f"{archive_id}/{folder}/{key}", content=raw)
            if result["status"] == "processed":
                counts["skipped"] += 1
                continue
            counts["reprocessed" if result["action"] == "requeued" else "indexed_new"] += 1
            item_id = ledger.claim(1, item_ids=[result["item_id"]])[0]["item_id"]
            try:
                outcome = store.record(parse(raw), {"id": archive_source_id(archive_id, folder, key), "source_kind": source_kind, "provider": "archive",
                                                    "archive_id": archive_id, "mailbox": folder, "record_key": key})
                if outcome["action"] == "merged":
                    counts["deduplicated"] += 1
                completed.append(item_id)
            except Exception as exc:
                ledger.fail(item_id, type(exc).__name__, retryable=True)
                counts["errors"] += 1
        store.conn.commit()
        for item_id in completed:
            ledger.complete(item_id, [f"mail-archive:{archive_id}"])
    return {"archive_id": archive_id, "source_kind": source_kind, **counts}


# ---------------------------------------------------------------------------
# Reads
# ---------------------------------------------------------------------------


def search(
    query: str,
    limit: int = 10,
    db_path: Path | None = None,
    *,
    accounts: list[str] | None = None,
    providers: list[str] | None = None,
    mailboxes: list[str] | None = None,
    source_kinds: list[str] | None = None,
    sender: str | None = None,
    recipient: str | None = None,
    after: str | None = None,
    before: str | None = None,
    scope: str | None = None,
) -> list[dict[str, Any]]:
    """``mail.search``: compact results, each attributed to its sources."""
    target = _target(scope, db_path)
    if not target.exists():
        return []
    with Store(target) as store:
        return store.search(query, limit=limit, accounts=accounts, providers=providers, mailboxes=mailboxes, source_kinds=source_kinds,
                            sender=sender, recipient=recipient, after=after, before=before)


def get_message(
    uid: str | None = None,
    mailbox: str = "INBOX",
    include_body: bool = False,
    db_path: Path | None = None,
    *,
    id: str | None = None,
    account_id: str | None = None,
    include_sources: bool = True,
    include_attachments: bool = True,
    scope: str | None = None,
) -> dict[str, Any]:
    """``mail.get_message`` by stable id (``msg_...``), or by the v1
    ``uid`` + ``mailbox`` (optionally ``account_id``)."""
    target = _target(scope, db_path)
    if not target.exists():
        raise KeyError("Message not found in local index.")
    with Store(target) as store:
        message_id = id or (store.message_by_uid(str(uid), mailbox, account_id) if uid is not None else None)
        if not message_id:
            raise KeyError("Message not found in local index.")
        result = store.message(message_id, include_body=include_body, include_sources=include_sources, include_attachments=include_attachments)
    if not include_body:
        result.setdefault("snippet", "")
    return result


def get_thread(thread_id: str | None = None, message_id: str | None = None, include_body: bool = False, limit: int = 50, db_path: Path | None = None,
               *, scope: str | None = None) -> dict[str, Any]:
    """``mail.get_thread`` by thread id (``thr_...``) or any message id in it."""
    target = _target(scope, db_path)
    if not (thread_id or message_id):
        raise ValueError("give thread_id or message_id")
    if not target.exists():
        raise KeyError("Thread not found in local index.")
    with Store(target) as store:
        return store.thread(thread_id or message_id, include_body=include_body, limit=limit)


def status(account_id: str | None = None, db_path: Path | None = None, *, scope: str | None = None) -> dict[str, Any]:
    """``mail.sync_status``: per account, plus the v1 top-level fields.
    With ``scope``, only that scope's accounts and index."""
    if account_id:
        return account_status(account_id, db_path)
    configured = [item for item in accounts_lib.load_accounts() if scope is None or item.mail_scope == scope]
    if db_path or DB.exists():
        targets = {"all": Path(db_path or DB)}
    else:
        targets = {name: config.db_for(name) for name in ([scope] if scope else config.SCOPES)}
    counts = {"logical_messages": 0, "source_observations": 0, "observations_by_account": {}}
    migration = None
    by_scope = {}
    for name, target in targets.items():
        if not target.exists():
            continue
        with Store(target) as store:
            found = store.counts()
            migration = migration or store.migration
        by_scope[name] = {"indexed_messages": found["logical_messages"], "source_observations": found["source_observations"], "directory": str(target.parent)}
        counts["logical_messages"] += found["logical_messages"]
        counts["source_observations"] += found["source_observations"]
    return {
        "scopes": by_scope,
        "configured": bool(configured),
        "accounts": [account_status(item.id, db_path) for item in configured],
        "indexed_messages": counts["logical_messages"],
        "source_observations": counts["source_observations"],
        "migration": migration,
        "provider": ",".join(sorted({item.provider for item in configured})) or None,
        "read_only": True,
    }
