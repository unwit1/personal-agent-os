from __future__ import annotations

import email
import imaplib
import json
import os
import sqlite3
import ssl
from dataclasses import asdict, dataclass
from email.header import decode_header
from email.message import Message
from pathlib import Path
from typing import Any, Callable, Iterable

from .ingestion import IngestionLedger, stable_stage_id, stable_work_id

ROOT = Path(__file__).resolve().parents[2]
LOCAL_DIR = ROOT / ".agent-local" / "mail"
CONFIG = LOCAL_DIR / "icloud.json"
DB = LOCAL_DIR / "index.sqlite3"
INGESTION_PROCESSOR_VERSION = "mail-index@1"


@dataclass
class MailMessage:
    uid: str
    mailbox: str
    subject: str
    sender: str
    recipients: str
    date: str
    message_id: str
    body: str


def _decode(value: str | None) -> str:
    if not value:
        return ""
    parts = []
    for chunk, charset in decode_header(value):
        if isinstance(chunk, bytes):
            parts.append(chunk.decode(charset or "utf-8", errors="replace"))
        else:
            parts.append(chunk)
    return "".join(parts)


def _body(msg: Message) -> str:
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain" and "attachment" not in (part.get("Content-Disposition") or "").lower():
                data = part.get_payload(decode=True) or b""
                return data.decode(part.get_content_charset() or "utf-8", errors="replace")
        return ""
    if msg.get_content_type() == "text/plain":
        data = msg.get_payload(decode=True) or b""
        return data.decode(msg.get_content_charset() or "utf-8", errors="replace")
    return ""


def _config() -> dict[str, str]:
    if not CONFIG.exists():
        raise ValueError("iCloud Mail is not configured; run: agent-os mail setup icloud")
    return json.loads(CONFIG.read_text(encoding="utf-8"))


def _password() -> str:
    value = os.environ.get("ICLOUD_APP_PASSWORD")
    if value:
        return value
    try:
        import keyring  # type: ignore
        value = keyring.get_password("personal-agent-os/icloud-mail", _config()["email"])
        if value:
            return value
    except ImportError:
        pass
    raise ValueError("No iCloud app-specific password found. Set ICLOUD_APP_PASSWORD locally or install keyring and rerun setup.")


def setup_icloud(address: str, password: str) -> dict[str, Any]:
    address = address.strip()
    if "@" not in address:
        raise ValueError("Enter the full iCloud email address.")
    health = _health(address, password)
    LOCAL_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG.write_text(json.dumps({"email": address}, indent=2), encoding="utf-8")
    stored = False
    try:
        import keyring  # type: ignore
        keyring.set_password("personal-agent-os/icloud-mail", address, password)
        stored = True
    except ImportError:
        pass
    return {"configured": True, "authenticated": health["ok"], "credential_stored": stored,
            "next": "Credential stored in OS keyring." if stored else "keyring is not installed; set ICLOUD_APP_PASSWORD in your local environment before sync."}


def _health(address: str, password: str) -> dict[str, Any]:
    try:
        with imaplib.IMAP4_SSL("imap.mail.me.com", 993, ssl_context=ssl.create_default_context()) as client:
            client.login(address, password)
            return {"ok": True, "provider": "icloud"}
    except imaplib.IMAP4.error:
        return {"ok": False, "provider": "icloud", "error": "Authentication failed."}


def health() -> dict[str, Any]:
    cfg = _config()
    return _health(cfg["email"], _password())


def _connect() -> imaplib.IMAP4_SSL:
    cfg = _config()
    client = imaplib.IMAP4_SSL("imap.mail.me.com", 993, ssl_context=ssl.create_default_context())
    try:
        client.login(cfg["email"], _password())
    except Exception:
        client.logout()
        raise ValueError("iCloud authentication failed.")
    return client


def _db(db_path: Path | None = None) -> sqlite3.Connection:
    target = db_path or DB
    target.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(target)
    conn.execute("""CREATE TABLE IF NOT EXISTS messages (
      uid TEXT NOT NULL, mailbox TEXT NOT NULL, subject TEXT, sender TEXT, recipients TEXT,
      date TEXT, message_id TEXT, body TEXT, PRIMARY KEY(mailbox, uid))""")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_mail_subject ON messages(subject)")
    return conn


def _ledger_path(db_path: Path) -> Path:
    return db_path.parent / "ingestion.json"


def _parse_record(uid: str, mailbox: str, raw_message: bytes) -> MailMessage:
    msg = email.message_from_bytes(raw_message)
    return MailMessage(uid, mailbox, _decode(msg.get("Subject")), _decode(msg.get("From")),
                       _decode(msg.get("To")), _decode(msg.get("Date")), _decode(msg.get("Message-ID")), _body(msg))


def sync_records(
    records: Iterable[tuple[str, bytes]],
    *,
    mailbox: str = "INBOX",
    db_path: Path | None = None,
    ledger_path: Path | None = None,
    parser: Callable[[str, str, bytes], MailMessage] = _parse_record,
) -> dict[str, Any]:
    """Index fetched provider records through the restart-safe ledger.

    This is the local, fixture-friendly boundary used by :func:`sync`. The
    provider still owns mailbox enumeration and fetching; the ledger owns
    stable identity, deduplication, checkpointing, and recovery. SQLite is
    committed before a ledger item is marked processed, making a crash between
    those writes safe to repeat via ``INSERT OR REPLACE``.
    """
    target_db = db_path or DB
    work_id = stable_work_id("icloud-mail", mailbox)
    stage_id = stable_stage_id(work_id, "sync")
    ledger = IngestionLedger(
        ledger_path or _ledger_path(target_db),
        source="icloud-mail",
        work_id=work_id,
        stage_id=stage_id,
        processor_version=INGESTION_PROCESSOR_VERSION,
    )
    conn = _db(target_db)
    checked = newly_indexed = reprocessed = resumed = skipped = errors = 0
    try:
        for uid, raw_message in records:
            uid = str(uid)
            raw_message = bytes(raw_message)
            checked += 1
            result = ledger.enqueue(f"{mailbox}:{uid}", content=raw_message)
            if result["action"] == "queued":
                newly_indexed += 1
            elif result["action"] == "requeued":
                reprocessed += 1
            elif result["status"] == "queued":
                resumed += 1
            elif result["status"] == "processed":
                skipped += 1
                ledger.checkpoint(uid, checked=checked, processed=checked - skipped - errors)
                continue
            elif result["status"] == "error":
                errors += 1
                ledger.checkpoint(uid, checked=checked, processed=checked - skipped - errors)
                continue

            claimed = ledger.claim(1)
            if not claimed:
                continue
            item_id = claimed[0]["item_id"]
            try:
                record = parser(uid, mailbox, raw_message)
                conn.execute("INSERT OR REPLACE INTO messages VALUES (?,?,?,?,?,?,?,?)", tuple(asdict(record).values()))
                conn.commit()
                ledger.complete(item_id, [f"mail:{mailbox}:{uid}"])
                ledger.checkpoint(uid, checked=checked, processed=checked - skipped - errors)
            except Exception as exc:
                conn.rollback()
                ledger.fail(item_id, str(exc) or exc.__class__.__name__, retryable=True)
                errors += 1
                ledger.checkpoint(uid, checked=checked, processed=checked - skipped - errors)
    finally:
        conn.close()
    return {
        "mailbox": mailbox,
        "indexed_new": newly_indexed,
        "reprocessed": reprocessed,
        "resumed": resumed,
        "skipped": skipped,
        "errors": errors,
        "checked": checked,
        "read_only": True,
    }


def sync(limit: int = 500, mailbox: str = "INBOX") -> dict[str, Any]:
    client = _connect()
    try:
        status, _ = client.select(mailbox, readonly=True)
        if status != "OK":
            raise ValueError("Unable to open mailbox.")
        status, data = client.uid("search", None, "ALL")
        if status != "OK":
            raise ValueError("Unable to enumerate messages.")
        uids = (data[0] or b"").split()[-max(1, limit):]
        records: list[tuple[str, bytes]] = []
        for raw_uid in uids:
            uid = raw_uid.decode()
            status, payload = client.uid("fetch", raw_uid, "(RFC822)")
            if status != "OK" or not payload or not isinstance(payload[0], tuple):
                continue
            records.append((uid, payload[0][1]))
        return sync_records(records, mailbox=mailbox)
    finally:
        try:
            client.logout()
        except Exception:
            pass


def search(query: str, limit: int = 10, db_path: Path | None = None) -> list[dict[str, Any]]:
    target_db = db_path or DB
    if not target_db.exists():
        return []
    conn = _db(target_db)
    try:
        needle = f"%{query}%"
        rows = conn.execute("""SELECT uid,mailbox,subject,sender,recipients,date,message_id,body
          FROM messages WHERE subject LIKE ? OR sender LIKE ? OR recipients LIKE ? OR body LIKE ?
          ORDER BY rowid DESC LIMIT ?""", (needle, needle, needle, needle, max(1, min(limit, 50)))).fetchall()
        return [{"uid": r[0], "mailbox": r[1], "subject": r[2], "sender": r[3], "recipients": r[4],
                 "date": r[5], "message_id": r[6], "snippet": (r[7] or "")[:1200]} for r in rows]
    finally:
        conn.close()


def get_message(uid: str, mailbox: str = "INBOX", include_body: bool = False, db_path: Path | None = None) -> dict[str, Any]:
    conn = _db(db_path)
    try:
        row = conn.execute("SELECT uid,mailbox,subject,sender,recipients,date,message_id,body FROM messages WHERE uid=? AND mailbox=?", (uid, mailbox)).fetchone()
        if not row:
            raise KeyError("Message not found in local index.")
        result = {"uid": row[0], "mailbox": row[1], "subject": row[2], "sender": row[3],
                  "recipients": row[4], "date": row[5], "message_id": row[6]}
        result["body" if include_body else "snippet"] = (row[7] or "") if include_body else (row[7] or "")[:1200]
        return result
    finally:
        conn.close()


def status() -> dict[str, Any]:
    configured = CONFIG.exists()
    count = 0
    if DB.exists():
        conn = _db()
        try:
            count = conn.execute("SELECT COUNT(*) FROM messages").fetchone()[0]
        finally:
            conn.close()
    return {"provider": "icloud", "configured": configured, "indexed_messages": count, "read_only": True}
