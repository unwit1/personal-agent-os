"""Local mail index (SQLite, gitignored): logical messages, source
observations, threads, attachments, mailbox sync state and full-text search.

Two separate concepts:

* a **source observation** is one place a message was seen: a live IMAP
  record (provider/account/mailbox/UIDVALIDITY/UID) or an archive record
  (archive/folder/record key);
* a **logical message** is the email itself. Several observations can point
  at one logical message (the same mail in two accounts, a folder copy, a live
  copy and a PST copy). Deduplication links observations; it never deletes
  them.

Dedup evidence, strongest first: the RFC Message-ID with a compatible sender
and date; an exact normalized content hash; a composite date/sender/recipient/subject/
body key (content evidence never merges two different Message-IDs). A shared
Message-ID with incompatible content is kept as a separate
message. Nothing fuzzier merges automatically.

Threads use References, then In-Reply-To, then the message's own Message-ID.
Messages with none of these are single-message threads: equal subjects alone
never merge.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable

from ..timestamps import utc_now_iso as now
from .message import Attachment, ParsedMessage, normalize_message_id, normalize_subject

SCHEMA_VERSION = 2
SNIPPET_CHARS = 400
MAX_LIMIT = 50

SCHEMA = """
CREATE TABLE IF NOT EXISTS mail_messages (
  id TEXT PRIMARY KEY, rfc_message_id TEXT, subject TEXT, sender TEXT, recipients TEXT, cc TEXT,
  date_header TEXT, date_utc TEXT, in_reply_to TEXT, refs TEXT, thread_key TEXT, thread_id TEXT,
  body TEXT, content_hash TEXT, composite_key TEXT, attachment_count INTEGER DEFAULT 0,
  created_at TEXT, updated_at TEXT);
CREATE INDEX IF NOT EXISTS idx_mail_msg_rfc ON mail_messages(rfc_message_id);
CREATE INDEX IF NOT EXISTS idx_mail_msg_content ON mail_messages(content_hash);
CREATE INDEX IF NOT EXISTS idx_mail_msg_composite ON mail_messages(composite_key);
CREATE INDEX IF NOT EXISTS idx_mail_msg_thread ON mail_messages(thread_id);
CREATE INDEX IF NOT EXISTS idx_mail_msg_threadkey ON mail_messages(thread_key);
CREATE INDEX IF NOT EXISTS idx_mail_msg_date ON mail_messages(date_utc);
CREATE TABLE IF NOT EXISTS mail_sources (
  id TEXT PRIMARY KEY, message_id TEXT NOT NULL, source_kind TEXT NOT NULL, provider TEXT, account_id TEXT,
  mailbox TEXT, uidvalidity TEXT, uid TEXT, archive_id TEXT, record_key TEXT, raw_hash TEXT, size INTEGER,
  internal_date TEXT, flags TEXT, state TEXT DEFAULT 'present', legacy INTEGER DEFAULT 0,
  first_seen TEXT, last_seen TEXT);
CREATE INDEX IF NOT EXISTS idx_mail_src_message ON mail_sources(message_id);
CREATE INDEX IF NOT EXISTS idx_mail_src_box ON mail_sources(account_id, mailbox, uidvalidity, uid);
CREATE TABLE IF NOT EXISTS mail_attachments (
  id TEXT PRIMARY KEY, message_id TEXT NOT NULL, filename TEXT, mime_type TEXT, size INTEGER,
  content_hash TEXT, text TEXT, extraction TEXT);
CREATE INDEX IF NOT EXISTS idx_mail_att_message ON mail_attachments(message_id);
CREATE TABLE IF NOT EXISTS mail_mailboxes (
  account_id TEXT NOT NULL, mailbox TEXT NOT NULL, uidvalidity TEXT, uidnext INTEGER, highestmodseq INTEGER,
  high_water_uid INTEGER, backfill_low_uid INTEGER, server_count INTEGER, capability_mode TEXT,
  last_started TEXT, last_completed TEXT, last_status TEXT, last_error TEXT, counts TEXT,
  PRIMARY KEY(account_id, mailbox));
"""
FTS = "CREATE VIRTUAL TABLE IF NOT EXISTS mail_fts USING fts5(message_id UNINDEXED, subject, sender, recipients, body, attachments, tokenize='unicode61')"


def _id(prefix: str, *parts: Any) -> str:
    joined = "\x1f".join("" if part is None else str(part) for part in parts)
    return f"{prefix}_{hashlib.sha256(joined.encode('utf-8')).hexdigest()[:24]}"


def live_source_id(provider: str, account_id: str, mailbox: str, uidvalidity: str | None, uid: str) -> str:
    return _id("src", "live_imap", provider, account_id, mailbox, uidvalidity or "legacy", uid)


def archive_source_id(archive_id: str, folder: str, record_key: str) -> str:
    return _id("src", "archive", archive_id, folder, record_key)


def thread_id_for(key: str) -> str:
    return _id("thr", key)


# ---------------------------------------------------------------------------
# Open / migrate
# ---------------------------------------------------------------------------


class Store:
    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.migration = migrate(self.conn, self.path)
        self.conn.executescript(SCHEMA)
        try:
            self.conn.execute(FTS)
            self.fts = True
        except sqlite3.OperationalError:
            self.fts = False
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()

    def __enter__(self) -> "Store":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    # -- observations ------------------------------------------------------

    def find_source(self, source_id: str) -> sqlite3.Row | None:
        return self.conn.execute("SELECT * FROM mail_sources WHERE id=?", (source_id,)).fetchone()

    def record(self, parsed: ParsedMessage, source: dict[str, Any]) -> dict[str, Any]:
        """Index one observation. Caller commits. Returns what happened."""
        stamp = now()
        existing = self.find_source(source["id"])
        if existing is not None and existing["raw_hash"] == parsed.raw_hash:
            self.conn.execute("UPDATE mail_sources SET last_seen=?, state='present', flags=COALESCE(?, flags) WHERE id=?", (stamp, source.get("flags"), source["id"]))
            return {"action": "unchanged", "source_id": source["id"], "message_id": existing["message_id"]}
        if existing is not None:
            # This source's own content changed. If nothing else shares its old
            # logical message, that version is gone: drop it first so the new
            # content cannot be matched back onto the stale copy.
            others = self.conn.execute("SELECT 1 FROM mail_sources WHERE message_id=? AND id<>? LIMIT 1", (existing["message_id"], source["id"])).fetchone()
            if others is None:
                self.conn.execute("UPDATE mail_sources SET message_id='' WHERE id=?", (source["id"],))
                self._drop_if_orphan(existing["message_id"])
        message_id, merged = self._logical(parsed)
        if existing is not None:
            old = existing["message_id"]
            self.conn.execute(
                "UPDATE mail_sources SET message_id=?, raw_hash=?, size=?, internal_date=?, flags=?, state='present', last_seen=? WHERE id=?",
                (message_id, parsed.raw_hash, source.get("size"), source.get("internal_date"), source.get("flags"), stamp, source["id"]),
            )
            if old != message_id:
                self._drop_if_orphan(old)
            action = "updated"
        else:
            self.conn.execute(
                "INSERT INTO mail_sources (id,message_id,source_kind,provider,account_id,mailbox,uidvalidity,uid,archive_id,record_key,raw_hash,size,internal_date,flags,state,legacy,first_seen,last_seen) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?, 'present', ?, ?, ?)",
                (source["id"], message_id, source["source_kind"], source.get("provider"), source.get("account_id"), source.get("mailbox"), source.get("uidvalidity"),
                 source.get("uid"), source.get("archive_id"), source.get("record_key"), parsed.raw_hash, source.get("size"), source.get("internal_date"),
                 source.get("flags"), int(bool(source.get("legacy"))), stamp, stamp),
            )
            action = "merged" if merged else "new"
        if source.get("uidvalidity") and source.get("uid"):
            # A live resync has confirmed a pre-migration record.
            self.conn.execute(
                "UPDATE mail_sources SET state='superseded' WHERE legacy=1 AND account_id=? AND mailbox=? AND uid=? AND message_id=? AND id<>?",
                (source.get("account_id"), source.get("mailbox"), source.get("uid"), message_id, source["id"]),
            )
        return {"action": action, "source_id": source["id"], "message_id": message_id}

    def _logical(self, parsed: ParsedMessage) -> tuple[str, bool]:
        """(logical message id, merged into an existing message?)"""
        match = self._match(parsed)
        if match:
            return match, True
        message_id = _id("msg", parsed.content_hash, parsed.rfc_message_id)
        while self.conn.execute("SELECT 1 FROM mail_messages WHERE id=?", (message_id,)).fetchone():
            message_id = _id("msg", message_id, "collision")
        self._insert_message(message_id, parsed)
        return message_id, False

    def _match(self, parsed: ParsedMessage) -> str | None:
        if parsed.rfc_message_id:
            for row in self.conn.execute("SELECT id, sender, subject, date_utc, content_hash FROM mail_messages WHERE rfc_message_id=?", (parsed.rfc_message_id,)):
                if row["content_hash"] == parsed.content_hash or _compatible(row, parsed):
                    return row["id"]
        # Content evidence never merges two emails that both carry different
        # Message-IDs (the same text sent twice is two emails).
        for column, value in (("content_hash", parsed.content_hash), ("composite_key", parsed.composite_key)):
            for row in self.conn.execute(f"SELECT id, rfc_message_id FROM mail_messages WHERE {column}=?", (value,)):
                if not row["rfc_message_id"] or not parsed.rfc_message_id or row["rfc_message_id"] == parsed.rfc_message_id:
                    return row["id"]
        return None

    def _insert_message(self, message_id: str, parsed: ParsedMessage) -> None:
        addresses = parsed.addresses()
        key = self._thread_key(parsed, message_id)
        stamp = now()
        self.conn.execute(
            "INSERT INTO mail_messages (id,rfc_message_id,subject,sender,recipients,cc,date_header,date_utc,in_reply_to,refs,thread_key,thread_id,body,content_hash,composite_key,attachment_count,created_at,updated_at) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (message_id, parsed.rfc_message_id, parsed.subject, parsed.sender, parsed.to, parsed.cc, parsed.date_header, parsed.date_utc, parsed.in_reply_to,
             json.dumps(parsed.references), key, thread_id_for(key), parsed.body, parsed.content_hash, parsed.composite_key, len(parsed.attachments), stamp, stamp),
        )
        for attachment in parsed.attachments:
            self._insert_attachment(message_id, attachment)
        if self.fts:
            self.conn.execute(
                "INSERT INTO mail_fts (message_id, subject, sender, recipients, body, attachments) VALUES (?,?,?,?,?,?)",
                (message_id, parsed.subject, f"{parsed.sender} {addresses['sender']}", f"{parsed.to} {parsed.cc}", parsed.body,
                 "\n".join(filter(None, [a.filename + " " + (a.text or "") for a in parsed.attachments]))),
            )
        if parsed.rfc_message_id:
            # Replies indexed before this message used its Message-ID as their
            # thread key; move them into this message's thread.
            self.conn.execute("UPDATE mail_messages SET thread_key=?, thread_id=? WHERE thread_key=? AND id<>?", (key, thread_id_for(key), parsed.rfc_message_id, message_id))

    def _insert_attachment(self, message_id: str, attachment: Attachment) -> None:
        self.conn.execute(
            "INSERT OR REPLACE INTO mail_attachments (id,message_id,filename,mime_type,size,content_hash,text,extraction) VALUES (?,?,?,?,?,?,?,?)",
            (_id("att", message_id, attachment.content_hash, attachment.filename), message_id, attachment.filename, attachment.mime_type, attachment.size,
             attachment.content_hash, attachment.text, "text" if attachment.text is not None else "metadata-only"),
        )

    def _thread_key(self, parsed: ParsedMessage, message_id: str) -> str:
        if parsed.references:
            return parsed.references[0]
        if parsed.in_reply_to:
            parent = self.conn.execute("SELECT thread_key FROM mail_messages WHERE rfc_message_id=?", (parsed.in_reply_to,)).fetchone()
            return parent["thread_key"] if parent else parsed.in_reply_to
        return parsed.rfc_message_id or f"solo:{message_id}"

    def _drop_if_orphan(self, message_id: str) -> None:
        if self.conn.execute("SELECT 1 FROM mail_sources WHERE message_id=?", (message_id,)).fetchone():
            return
        self.conn.execute("DELETE FROM mail_messages WHERE id=?", (message_id,))
        self.conn.execute("DELETE FROM mail_attachments WHERE message_id=?", (message_id,))
        if self.fts:
            self.conn.execute("DELETE FROM mail_fts WHERE message_id=?", (message_id,))

    def update_flags(self, source_id: str, flags: str) -> None:
        self.conn.execute("UPDATE mail_sources SET flags=? WHERE id=?", (flags, source_id))

    def known_uids(self, account_id: str, mailbox: str, uidvalidity: str) -> dict[int, sqlite3.Row]:
        rows = self.conn.execute(
            "SELECT id, uid, size, internal_date, flags, state FROM mail_sources WHERE source_kind='live_imap' AND account_id=? AND mailbox=? AND uidvalidity=?",
            (account_id, mailbox, uidvalidity),
        )
        return {int(row["uid"]): row for row in rows if str(row["uid"]).isdigit()}

    def mark_missing(self, account_id: str, mailbox: str, uidvalidity: str, present: set[int]) -> int:
        """After a complete server listing: known UIDs the server no longer has."""
        known = self.known_uids(account_id, mailbox, uidvalidity)
        gone = [row["id"] for uid, row in known.items() if uid not in present and row["state"] == "present"]
        self.conn.executemany("UPDATE mail_sources SET state='missing' WHERE id=?", [(item,) for item in gone])
        return len(gone)

    def retire_namespace(self, account_id: str, mailbox: str, old_uidvalidity: str) -> int:
        """UIDVALIDITY changed: old UIDs no longer identify anything on the
        server. Keep the observations (provenance), marked stale."""
        cursor = self.conn.execute(
            "UPDATE mail_sources SET state='stale_uidvalidity' WHERE source_kind='live_imap' AND account_id=? AND mailbox=? AND uidvalidity=?",
            (account_id, mailbox, old_uidvalidity),
        )
        return cursor.rowcount

    # -- mailbox state ------------------------------------------------------

    def mailbox_state(self, account_id: str, mailbox: str) -> dict[str, Any]:
        row = self.conn.execute("SELECT * FROM mail_mailboxes WHERE account_id=? AND mailbox=?", (account_id, mailbox)).fetchone()
        return dict(row) if row else {"account_id": account_id, "mailbox": mailbox}

    def save_mailbox_state(self, state: dict[str, Any]) -> None:
        columns = ["account_id", "mailbox", "uidvalidity", "uidnext", "highestmodseq", "high_water_uid", "backfill_low_uid", "server_count",
                   "capability_mode", "last_started", "last_completed", "last_status", "last_error", "counts"]
        values = [state.get(column) if column != "counts" else json.dumps(state.get("counts") or {}) if not isinstance(state.get("counts"), str) else state["counts"] for column in columns]
        self.conn.execute(f"INSERT OR REPLACE INTO mail_mailboxes ({','.join(columns)}) VALUES ({','.join('?' * len(columns))})", values)

    def mailboxes(self, account_id: str | None = None) -> list[dict[str, Any]]:
        query = "SELECT * FROM mail_mailboxes" + (" WHERE account_id=?" if account_id else "") + " ORDER BY account_id, mailbox"
        rows = [dict(row) for row in self.conn.execute(query, (account_id,) if account_id else ())]
        for row in rows:
            row["counts"] = json.loads(row["counts"]) if row.get("counts") else {}
        return rows

    def counts(self) -> dict[str, Any]:
        per_account = {row["account_id"] or row["archive_id"] or "archive": row["n"] for row in self.conn.execute(
            "SELECT account_id, archive_id, COUNT(*) AS n FROM mail_sources WHERE state IN ('present','missing') GROUP BY account_id, archive_id")}
        return {
            "logical_messages": self.conn.execute("SELECT COUNT(*) FROM mail_messages").fetchone()[0],
            "source_observations": self.conn.execute("SELECT COUNT(*) FROM mail_sources").fetchone()[0],
            "observations_by_account": per_account,
        }

    # -- reads ----------------------------------------------------------------

    def search(
        self,
        query: str = "",
        *,
        limit: int = 10,
        accounts: Iterable[str] | None = None,
        providers: Iterable[str] | None = None,
        mailboxes: Iterable[str] | None = None,
        source_kinds: Iterable[str] | None = None,
        sender: str | None = None,
        recipient: str | None = None,
        after: str | None = None,
        before: str | None = None,
    ) -> list[dict[str, Any]]:
        where, params = [], []
        text = (query or "").strip()
        use_fts = bool(text) and self.fts
        if text and not use_fts:
            like = f"%{text}%"
            where.append("(m.subject LIKE ? OR m.sender LIKE ? OR m.recipients LIKE ? OR m.cc LIKE ? OR m.body LIKE ?)")
            params += [like] * 5
        source_filters = []
        for column, values in (("account_id", accounts), ("provider", providers), ("mailbox", mailboxes), ("source_kind", source_kinds)):
            items = [str(item) for item in values or [] if item]
            if items:
                source_filters.append(f"s.{column} IN ({','.join('?' * len(items))})")
                params_source = items
                params += params_source
        if source_filters:
            where.append("EXISTS (SELECT 1 FROM mail_sources s WHERE s.message_id=m.id AND s.state<>'superseded' AND " + " AND ".join(source_filters) + ")")
        if sender:
            where.append("m.sender LIKE ?")
            params.append(f"%{sender}%")
        if recipient:
            where.append("(m.recipients LIKE ? OR m.cc LIKE ?)")
            params += [f"%{recipient}%"] * 2
        if after:
            where.append("m.date_utc >= ?")
            params.append(_date_bound(after))
        if before:
            where.append("m.date_utc < ?")
            params.append(_date_bound(before))
        limit = max(1, min(int(limit or 10), MAX_LIMIT))
        if use_fts:
            sql = ("SELECT m.* FROM mail_fts f JOIN mail_messages m ON m.id=f.message_id WHERE mail_fts MATCH ?"
                   + "".join(f" AND {clause}" for clause in where) + " ORDER BY bm25(mail_fts), m.date_utc DESC LIMIT ?")
            rows = self.conn.execute(sql, [fts_query(text), *params, limit]).fetchall()
        else:
            sql = "SELECT m.* FROM mail_messages m" + (" WHERE " + " AND ".join(where) if where else "") + " ORDER BY m.date_utc DESC, m.rowid DESC LIMIT ?"
            rows = self.conn.execute(sql, [*params, limit]).fetchall()
        return [self._summary(row) for row in rows]

    def sources_for(self, message_id: str) -> list[dict[str, Any]]:
        return [dict(row) for row in self.conn.execute(
            "SELECT id, source_kind, provider, account_id, mailbox, uidvalidity, uid, archive_id, record_key, flags, state, legacy, first_seen, last_seen FROM mail_sources WHERE message_id=? ORDER BY first_seen",
            (message_id,))]

    def _summary(self, row: sqlite3.Row) -> dict[str, Any]:
        sources = [item for item in self.sources_for(row["id"]) if item["state"] != "superseded"]
        primary = next((item for item in sources if item["source_kind"] == "live_imap"), sources[0] if sources else {})
        return {
            "id": row["id"],
            "thread_id": row["thread_id"],
            "subject": row["subject"],
            "sender": row["sender"],
            "recipients": row["recipients"],
            "date": row["date_utc"] or row["date_header"],
            "message_id": row["rfc_message_id"],
            "snippet": (row["body"] or "")[:SNIPPET_CHARS],
            "attachments": row["attachment_count"],
            "sources": [source_label(item) for item in sources][:6],
            "source_count": len(sources),
            # legacy fields for existing callers
            "uid": primary.get("uid"),
            "mailbox": primary.get("mailbox"),
            "account_id": primary.get("account_id"),
            "provider": primary.get("provider"),
        }

    def message(self, message_id: str, *, include_body: bool = False, include_sources: bool = True, include_attachments: bool = True) -> dict[str, Any]:
        row = self.conn.execute("SELECT * FROM mail_messages WHERE id=?", (message_id,)).fetchone()
        if row is None:
            raise KeyError("Message not found in local index.")
        result = self._summary(row)
        result.update(cc=row["cc"], in_reply_to=row["in_reply_to"], references=json.loads(row["refs"] or "[]")[:20])
        if include_body:
            result["body"] = row["body"] or ""
        if include_sources:
            result["source_observations"] = [{key: value for key, value in item.items() if key != "id"} | {"source_id": item["id"]} for item in self.sources_for(message_id)]
        if include_attachments:
            result["attachment_list"] = [dict(item) for item in self.conn.execute(
                "SELECT filename, mime_type, size, content_hash, extraction FROM mail_attachments WHERE message_id=?", (message_id,))]
        return result

    def message_by_uid(self, uid: str, mailbox: str = "INBOX", account_id: str | None = None) -> str | None:
        query = "SELECT message_id FROM mail_sources WHERE uid=? AND mailbox=?" + (" AND account_id=?" if account_id else "") + " ORDER BY (state='present') DESC, last_seen DESC LIMIT 1"
        row = self.conn.execute(query, (uid, mailbox, account_id) if account_id else (uid, mailbox)).fetchone()
        return row["message_id"] if row else None

    def thread(self, thread_or_message_id: str, *, include_body: bool = False, limit: int = 50) -> dict[str, Any]:
        thread_id = thread_or_message_id
        if thread_or_message_id.startswith("msg_"):
            row = self.conn.execute("SELECT thread_id FROM mail_messages WHERE id=?", (thread_or_message_id,)).fetchone()
            if row is None:
                raise KeyError("Message not found in local index.")
            thread_id = row["thread_id"]
        rows = self.conn.execute("SELECT * FROM mail_messages WHERE thread_id=? ORDER BY date_utc, rowid LIMIT ?", (thread_id, max(1, min(limit, 200)))).fetchall()
        if not rows:
            raise KeyError("Thread not found in local index.")
        messages = []
        for row in rows:
            item = self._summary(row)
            if include_body:
                item["body"] = row["body"] or ""
            messages.append(item)
        return {"thread_id": thread_id, "count": len(messages), "subject": normalize_subject(rows[0]["subject"] or "") or rows[0]["subject"], "messages": messages}


def source_label(source: dict[str, Any]) -> str:
    if source["source_kind"] == "live_imap":
        label = f"{source.get('account_id')}:{source.get('mailbox')}"
    else:
        label = f"{source['source_kind']}:{source.get('archive_id')}/{source.get('mailbox')}"
    if source.get("state") not in (None, "present"):
        label += f" ({source['state']})"
    return label


def _compatible(row: sqlite3.Row, parsed: ParsedMessage) -> bool:
    """Same Message-ID and plausibly the same email: same sender, same
    subject (ignoring Re:/Fwd:), dates within two days (or unknown). Copies of
    one email agree on all three; a reused Message-ID rarely does."""
    if (row["sender"] or "").casefold().strip() != parsed.sender.casefold().strip():
        return False
    if normalize_subject(row["subject"] or "") != normalize_subject(parsed.subject):
        return False
    if not row["date_utc"] or not parsed.date_utc:
        return True
    try:
        return abs(datetime.fromisoformat(row["date_utc"]) - datetime.fromisoformat(parsed.date_utc)) <= timedelta(days=2)
    except ValueError:
        return False


def fts_query(text: str) -> str:
    """Each word as a quoted term (implicit AND): user text never becomes FTS
    syntax."""
    terms = [word.replace('"', "") for word in text.split() if word.replace('"', "")]
    return " ".join(f'"{term}"' for term in terms) or '""'


def _date_bound(value: str) -> str:
    text = str(value).strip()
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"dates must be ISO format like 2026-09-01: {value!r}") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Migration from schema v1 (single iCloud table keyed by mailbox+uid)
# ---------------------------------------------------------------------------


def migrate(conn: sqlite3.Connection, path: Path, legacy_account_id: str = "icloud") -> dict[str, Any] | None:
    version = conn.execute("PRAGMA user_version").fetchone()[0]
    if version >= SCHEMA_VERSION:
        return None
    tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    if "messages" not in tables:
        conn.execute(f"PRAGMA user_version={SCHEMA_VERSION}")
        conn.commit()
        return None
    columns = {row[1] for row in conn.execute("PRAGMA table_info(messages)")}
    if not {"uid", "mailbox", "body"} <= columns:
        raise ValueError("unrecognized legacy mail table; not migrating")
    backup = path.with_name(f"{path.name}.v1-backup-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}")
    conn.commit()
    shutil.copy2(path, backup)
    old_rows = conn.execute("SELECT uid, mailbox, subject, sender, recipients, date, message_id, body FROM messages").fetchall()
    store_like = _MigrationStore(conn)
    try:
        conn.execute("BEGIN")
        for statement in SCHEMA.strip().split(";"):
            if statement.strip():
                conn.execute(statement)
        try:
            conn.execute(FTS)
            store_like.fts = True
        except sqlite3.OperationalError:
            store_like.fts = False
        for uid, mailbox, subject, sender, recipients, date, message_id, body in old_rows:
            parsed = _parsed_from_row(subject, sender, recipients, date, message_id, body)
            Store.record(store_like, parsed, {  # type: ignore[arg-type]
                "id": live_source_id("icloud", legacy_account_id, mailbox, None, uid), "source_kind": "live_imap", "provider": "icloud",
                "account_id": legacy_account_id, "mailbox": mailbox, "uidvalidity": None, "uid": uid, "legacy": True,
            })
        migrated = conn.execute("SELECT COUNT(*) FROM mail_sources WHERE legacy=1").fetchone()[0]
        if migrated != len(old_rows):
            raise ValueError(f"migration count mismatch: {migrated} observations for {len(old_rows)} rows")
        conn.execute("ALTER TABLE messages RENAME TO legacy_messages_v1")
        conn.execute(f"PRAGMA user_version={SCHEMA_VERSION}")
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    return {"migrated_rows": len(old_rows), "backup": str(backup), "legacy_account_id": legacy_account_id}


class _MigrationStore:
    """Just enough of Store for record() during migration."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn
        self.conn.row_factory = sqlite3.Row
        self.fts = False

    find_source = Store.find_source
    _logical = Store._logical
    _match = Store._match
    _insert_message = Store._insert_message
    _insert_attachment = Store._insert_attachment
    _thread_key = Store._thread_key
    _drop_if_orphan = Store._drop_if_orphan


def _parsed_from_row(subject: str, sender: str, recipients: str, date: str, message_id: str, body: str) -> ParsedMessage:
    from email.message import EmailMessage

    from .message import parse

    msg = EmailMessage()
    msg["Subject"] = subject or ""
    msg["From"] = sender or ""
    msg["To"] = recipients or ""
    if date:
        msg["Date"] = date
    if message_id:
        msg["Message-ID"] = message_id
    msg.set_content(body or "")
    parsed = parse(bytes(msg))
    parsed.raw_hash = hashlib.sha256(f"legacy\x1f{subject}\x1f{sender}\x1f{date}\x1f{message_id}\x1f{body}".encode("utf-8")).hexdigest()
    return parsed
