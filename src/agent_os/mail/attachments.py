"""Save email attachments as files, named and dated.

Layout (the user's choice, 2026-09-23)::

    Downloads\\Mail Attachments\\Work\\2019\\2019-05-01 - Shirley Cummings - W4 2019.pdf
    Downloads\\Mail Attachments\\Personal\\2024\\2024-07-02 - Apple - Receipt.pdf

* Name: ``<email date> - <sender> - <original file name>``; the file's
  modified time is set to the email's date.
* Work and personal stay apart, like the mail indexes.
* Inline logos and signature pictures (images under 20 KB, or inline images
  referenced by the message body), calendar invites and signature blobs
  (.p7s) are skipped.
* A file whose exact bytes were already saved (same attachment in several
  emails, or in a live mailbox and a PST) is saved once.

Enabled by ``export_attachments`` in ``.agent-local/mail/settings.json``.
Progress is kept in ``<scope>/attachments.sqlite3``: which content hashes
were written where, and which message sources were already handled, so
reruns do no repeated work. Never deletes or overwrites a file.
"""

from __future__ import annotations

import email
import hashlib
import json
import os
import re
import sqlite3
from datetime import datetime, timezone
from email.policy import default as default_policy
from email.utils import getaddresses, parsedate_to_datetime
from pathlib import Path
from typing import Any

from . import config

SCOPE_FOLDERS = {"work": "Work", "personal": "Personal"}
SMALL_IMAGE_BYTES = 20 * 1024
SKIP_TYPES = {"text/calendar", "application/ics", "application/pkcs7-signature", "application/x-pkcs7-signature", "application/ms-tnef"}
SKIP_EXTENSIONS = {".ics", ".p7s", ".vcs"}
MAX_NAME = 150
_BAD = re.compile(r'[<>:"/\\|?*\x00-\x1f]+')
_SPACE = re.compile(r"\s+")


def settings() -> dict[str, Any]:
    try:
        return json.loads((config.LOCAL_DIR / "settings.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def default_root() -> Path:
    return Path(settings().get("attachments_dir") or Path.home() / "Downloads" / "Mail Attachments")


def enabled() -> bool:
    return bool(settings().get("export_attachments"))


def clean(text: str, limit: int) -> str:
    text = _SPACE.sub(" ", _BAD.sub(" ", text or "")).strip(" .")
    return text[:limit].strip(" .")


def sender_label(from_header: str) -> str:
    from .message import decode

    text = decode(str(from_header or ""))
    pairs = getaddresses([text])
    name, address = pairs[-1] if pairs else ("", "")
    if "<" in text:  # also handles an unquoted "Last, First <x@y>"
        name = text.split("<", 1)[0]
    name = name.strip().strip('"').strip("'")
    if "," in name:  # "Last, First" -> "First Last"
        last, _, first = name.partition(",")
        name = f"{first.strip()} {last.strip()}".strip()
    return clean(name or address.split("@")[0] or "Unknown sender", 40) or "Unknown sender"


def email_date(date_header: str) -> datetime | None:
    try:
        parsed = parsedate_to_datetime(date_header)
    except (TypeError, ValueError, IndexError):
        return None
    if parsed is None:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone()


def file_name(when: datetime | None, sender: str, original: str) -> str:
    stem, dot, extension = original.rpartition(".")
    if not dot or len(extension) > 8 or " " in extension:
        stem, extension = original, ""
    extension = clean(extension, 8).lower()
    prefix = f"{when:%Y-%m-%d} - {sender} - " if when else f"Undated - {sender} - "
    stem = clean(stem, max(10, MAX_NAME - len(prefix) - len(extension) - 1)) or "attachment"
    return prefix + stem + (f".{extension}" if extension else "")


def skip_reason(part: Any, data: bytes, filename: str) -> str | None:
    kind = part.get_content_type()
    extension = os.path.splitext(filename)[1].lower()
    if kind in SKIP_TYPES or extension in SKIP_EXTENSIONS:
        return "invite_or_signature"
    if kind.startswith("image/"):
        disposition = (part.get("Content-Disposition") or "").lower()
        if len(data) < SMALL_IMAGE_BYTES:
            return "small_image"
        if part.get("Content-ID") and not disposition.startswith("attachment"):
            return "inline_image"
    return None


class Exporter:
    def __init__(self, scope: str, root: Path | None = None) -> None:
        self.scope = config.check_scope(scope)
        self.root = Path(root or default_root()) / SCOPE_FOLDERS[scope]
        manifest = config.scope_dir(scope) / "attachments.sqlite3"
        manifest.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(manifest)
        self.conn.executescript(
            "CREATE TABLE IF NOT EXISTS files (sha256 TEXT PRIMARY KEY, path TEXT, source_id TEXT, saved_at TEXT);"
            "CREATE TABLE IF NOT EXISTS done (source_id TEXT PRIMARY KEY, saved INTEGER, at TEXT);"
        )
        self.counts = {"saved": 0, "duplicates": 0, "skipped": 0, "messages": 0}

    def close(self) -> None:
        self.conn.commit()
        self.conn.close()

    def __enter__(self) -> "Exporter":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    def is_done(self, source_id: str) -> bool:
        return self.conn.execute("SELECT 1 FROM done WHERE source_id=?", (source_id,)).fetchone() is not None

    def export(self, raw: bytes, source_id: str) -> int:
        """Save this message's attachments; returns how many new files."""
        if self.is_done(source_id):
            return 0
        message = email.message_from_bytes(raw, policy=default_policy)
        when = email_date(str(message.get("Date") or ""))
        sender = sender_label(str(message.get("From") or ""))
        saved = 0
        for part in message.walk():
            if part.is_multipart() or part.get_content_type() == "message/rfc822":
                continue
            filename = part.get_filename()
            disposition = (part.get("Content-Disposition") or "").lower()
            if not filename and not disposition.startswith("attachment"):
                continue
            try:
                data = part.get_payload(decode=True) or b""
            except Exception:
                continue
            filename = str(filename or f"attachment.{part.get_content_subtype()}")
            if not data or skip_reason(part, data, filename):
                self.counts["skipped"] += 1
                continue
            digest = hashlib.sha256(data).hexdigest()
            if self.conn.execute("SELECT 1 FROM files WHERE sha256=?", (digest,)).fetchone():
                self.counts["duplicates"] += 1
                continue
            folder = self.root / (f"{when:%Y}" if when else "Undated")
            folder.mkdir(parents=True, exist_ok=True)
            first = folder / file_name(when, sender, filename)
            target, number = first, 2
            while target.exists():  # same name, different content: keep both
                target = first.with_name(f"{first.stem} ({number}){first.suffix}")
                number += 1
            with open(target, "xb") as handle:
                handle.write(data)
            if when:
                stamp = when.timestamp()
                os.utime(target, (stamp, stamp))
            self.conn.execute("INSERT INTO files VALUES (?,?,?,?)", (digest, str(target), source_id, datetime.now(timezone.utc).isoformat()))
            saved += 1
            self.counts["saved"] += 1
        self.conn.execute("INSERT OR REPLACE INTO done VALUES (?,?,?)", (source_id, saved, datetime.now(timezone.utc).isoformat()))
        self.counts["messages"] += 1
        self.conn.commit()
        return saved


def export_missing_live(scope: str, *, connect_factory: Any = None, batch: int = 50, root: Path | None = None) -> dict[str, Any]:
    """Download attachments for mail that was indexed before exporting was on:
    re-reads (read-only) only messages the index says carry attachments."""
    from .accounts import get_secret
    from .imap import connect
    from .scopes import accounts_in
    from .store import Store

    results = []
    with Exporter(scope, root) as exporter, Store(config.db_for(scope)) as store:
        for account in accounts_in(scope):
            rows = store.conn.execute(
                "SELECT s.id, s.mailbox, s.uidvalidity, s.uid FROM mail_sources s JOIN mail_messages m ON m.id=s.message_id "
                "WHERE s.account_id=? AND s.source_kind='live_imap' AND s.state='present' AND m.attachment_count>0",
                (account.id,)).fetchall()
            pending: dict[tuple[str, str], list[tuple[int, str]]] = {}
            for row in rows:
                if not exporter.is_done(row["id"]):
                    pending.setdefault((row["mailbox"], row["uidvalidity"]), []).append((int(row["uid"]), row["id"]))
            summary = {"account_id": account.id, "messages": sum(len(items) for items in pending.values()), "errors": 0}
            if pending:
                client = connect(account.host, account.port, security=account.tls, factory=connect_factory)
                try:
                    client.login(account.login_name, get_secret(account))
                    for (mailbox, uidvalidity), items in pending.items():
                        info = client.examine(mailbox)
                        if str(info.uidvalidity) != str(uidvalidity):
                            summary["errors"] += len(items)
                            continue
                        by_uid = dict(items)
                        uids = sorted(by_uid)
                        for start in range(0, len(uids), batch):
                            try:
                                for record in client.fetch(uids[start:start + batch], body=True):
                                    if record.raw is not None and record.uid in by_uid:
                                        exporter.export(record.raw, by_uid[record.uid])
                            except Exception:
                                summary["errors"] += len(uids[start:start + batch])
                finally:
                    client.logout()
            results.append(summary)
        counts = dict(exporter.counts)
    return {"scope": scope, "accounts": results, **counts, "folder": str(Path(root or default_root()) / SCOPE_FOLDERS[scope])}
