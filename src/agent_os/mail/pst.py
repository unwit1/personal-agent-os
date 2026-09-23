"""Import Outlook PST/OST backups into the **work** mail index.

Reads the file with libpff (``pip install libpff-python``, the libyal PST
reader; it opens the file read-only and never needs Outlook). Each message is
rebuilt as RFC822 (original transport headers when the PST kept them,
otherwise From/To/Cc/Subject/Date/Message-ID from the MAPI properties) and
recorded as a ``pst_archive`` observation, so a PST copy of a mail that is also
indexed live, or present in another PST, is the same logical message with
several sources: duplicates are merged, not repeated.

Restart-safe without a ledger: an observation's id is derived from
(archive, folder, message identifier), so a rerun skips everything already
recorded before reading its body. Progress is committed every ``batch``.
Damaged items are skipped and counted, never fatal.
"""

from __future__ import annotations

import hashlib
import json
import re
import time
from datetime import datetime, timezone
from email.message import EmailMessage
from email.parser import HeaderParser
from email.policy import default as default_policy
from email.utils import format_datetime
from pathlib import Path
from typing import Any, Callable, Iterator

from . import config
from .message import parse
from .store import Store, archive_source_id

MAX_ATTACHMENT_BYTES = 20 * 1024 * 1024
COPY_HEADERS = ("From", "To", "Cc", "Subject", "Date", "Message-ID", "In-Reply-To", "References", "Reply-To", "Sender")
# MAPI property tags
PR_SUBJECT, PR_SENDER_NAME, PR_SENDER_EMAIL, PR_SENDER_SMTP = 0x0037, 0x0C1A, 0x0C1F, 0x5D01
PR_DISPLAY_TO, PR_DISPLAY_CC = 0x0E04, 0x0E03
PR_MESSAGE_ID, PR_IN_REPLY_TO, PR_REFERENCES = 0x1035, 0x1042, 0x1039
PR_ATTACH_LONG_FILENAME, PR_ATTACH_FILENAME, PR_ATTACH_MIME = 0x3707, 0x3704, 0x370E


def archive_id_for(path: Path) -> str:
    stem = re.sub(r"[^a-z0-9]+", "-", path.stem.lower()).strip("-")[:30] or "archive"
    return f"pst-{stem}"


def file_fingerprint(path: Path, chunk: int = 32 * 1024 * 1024) -> str:
    """Size + first/last 32 MB: cheap and enough to spot a copied backup."""
    digest = hashlib.sha256(str(path.stat().st_size).encode())
    with path.open("rb") as handle:
        digest.update(handle.read(chunk))
        handle.seek(max(0, path.stat().st_size - chunk))
        digest.update(handle.read(chunk))
    return digest.hexdigest()


def _props(item: Any) -> dict[int, Any]:
    found: dict[int, Any] = {}
    try:
        sets = [item.get_record_set(i) for i in range(item.number_of_record_sets)]
    except Exception:
        return found
    for record_set in sets:
        try:
            count = record_set.number_of_entries
        except Exception:
            continue
        for index in range(count):
            try:
                entry = record_set.get_entry(index)
                if entry.entry_type in found:
                    continue
                if entry.value_type in (0x001F, 0x001E):
                    found[entry.entry_type] = entry.get_data_as_string()
                elif entry.value_type == 0x0102:
                    found[entry.entry_type] = entry.get_data()
            except Exception:
                continue
    return found


def _text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        for encoding in ("utf-8", "cp1252"):
            try:
                return value.decode(encoding)
            except UnicodeDecodeError:
                continue
        return value.decode("utf-8", errors="replace")
    return str(value)


def _safe(call: Callable[[], Any]) -> Any:
    try:
        return call()
    except Exception:
        return None


def _date(message: Any) -> datetime | None:
    for name in ("client_submit_time", "delivery_time", "creation_time"):
        value = _safe(lambda: getattr(message, name))
        if isinstance(value, datetime) and value.year > 1980:
            return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    return None


def to_rfc822(message: Any) -> tuple[bytes, dict[str, int]]:
    """Rebuild one PST message. Returns (raw, notes) where notes counts
    attachments skipped for size or damage."""
    notes = {"attachments_skipped": 0}
    props = _props(message)
    out = EmailMessage(policy=default_policy)
    headers_text = _safe(lambda: message.transport_headers) or ""
    if headers_text:
        original = HeaderParser(policy=default_policy).parsestr(_text(headers_text))
        for name in COPY_HEADERS:
            value = original.get(name)
            if value:
                try:
                    out[name] = str(value)
                except Exception:
                    pass
    if not out["From"]:
        name, address = _text(props.get(PR_SENDER_NAME)), _text(props.get(PR_SENDER_SMTP) or props.get(PR_SENDER_EMAIL))
        sender = f"{name} <{address}>" if "@" in address else (name or address)
        if sender:
            out["From"] = sender
    for header, tag in (("To", PR_DISPLAY_TO), ("Cc", PR_DISPLAY_CC)):
        if not out[header] and props.get(tag):
            out[header] = _text(props[tag]).replace("\x00", "").strip()
    if not out["Subject"]:
        out["Subject"] = _text(_safe(lambda: message.subject) or props.get(PR_SUBJECT)).replace("\r", " ").replace("\n", " ")
    if not out["Date"]:
        when = _date(message)
        if when:
            out["Date"] = format_datetime(when)
    for header, tag in (("Message-ID", PR_MESSAGE_ID), ("In-Reply-To", PR_IN_REPLY_TO), ("References", PR_REFERENCES)):
        if not out[header] and props.get(tag):
            out[header] = _text(props[tag]).strip()
    plain = _text(_safe(lambda: message.plain_text_body))
    html = _text(_safe(lambda: message.html_body))
    if plain:
        out.set_content(plain)
        if html:
            out.add_alternative(html, subtype="html")
    elif html:
        out.set_content(html, subtype="html")
    else:
        out.set_content("")
    count = _safe(lambda: message.number_of_attachments) or 0
    for index in range(count):
        attachment = _safe(lambda: message.get_attachment(index))
        if attachment is None:
            notes["attachments_skipped"] += 1
            continue
        size = _safe(lambda: attachment.size) or 0
        if not size or size > MAX_ATTACHMENT_BYTES:
            notes["attachments_skipped"] += 1
            continue
        data = _safe(lambda: attachment.read_buffer(size))
        if not data:
            notes["attachments_skipped"] += 1
            continue
        aprops = _props(attachment)
        filename = _text(aprops.get(PR_ATTACH_LONG_FILENAME) or aprops.get(PR_ATTACH_FILENAME)) or f"attachment-{index + 1}"
        mime = _text(aprops.get(PR_ATTACH_MIME)) or "application/octet-stream"
        main, _, sub = mime.partition("/")
        try:
            if out.get_content_type().startswith("text/") and not out.is_multipart():
                out.make_mixed()
            out.add_attachment(data, maintype=main or "application", subtype=sub or "octet-stream", filename=filename)
        except Exception:
            notes["attachments_skipped"] += 1
    return bytes(out), notes


def walk(pst_file: Any) -> Iterator[tuple[str, Any]]:
    """Yield (folder path, folder) for every folder under the root."""
    def visit(folder: Any, path: str) -> Iterator[tuple[str, Any]]:
        yield path, folder
        for index in range(_safe(lambda: folder.number_of_sub_folders) or 0):
            sub = _safe(lambda: folder.get_sub_folder(index))
            if sub is not None:
                name = (_safe(lambda: sub.name) or f"folder-{index}").strip()
                yield from visit(sub, f"{path}/{name}" if path else name)

    yield from visit(pst_file.get_root_folder(), "")


def _clean_folder(path: str) -> str:
    # Drop the store's own root labels ("Top of Personal Folders", "Root - Mailbox/IPM_SUBTREE").
    parts = [part for part in path.split("/") if part and part not in {"Top of Personal Folders", "Top of Outlook data file", "IPM_SUBTREE"} and not part.startswith("Root - ")]
    return "/".join(parts) or "(root)"


def import_pst(path: Path, *, archive_id: str | None = None, db_path: Path | None = None, batch: int = 500,
               progress: Callable[[dict[str, Any]], None] | None = None, opener: Callable[[], Any] | None = None) -> dict[str, Any]:
    import pypff  # type: ignore

    path = Path(path)
    archive_id = archive_id or archive_id_for(path)
    counts = {"messages_seen": 0, "indexed_new": 0, "deduplicated": 0, "already_imported": 0, "unreadable": 0, "attachments_skipped": 0, "folders": 0}
    started = time.perf_counter()
    pst_file = (opener or pypff.file)()
    pst_file.open(str(path))
    try:
        with Store(db_path or config.db_for("work")) as store:
            pending = 0
            for folder_path, folder in walk(pst_file):
                total = _safe(lambda: folder.number_of_sub_messages) or 0
                if not total:
                    continue
                counts["folders"] += 1
                label = _clean_folder(folder_path)
                for index in range(total):
                    counts["messages_seen"] += 1
                    message = _safe(lambda: folder.get_sub_message(index))
                    identifier = _safe(lambda: message.identifier) if message is not None else None
                    key = str(identifier if identifier is not None else f"index-{index}")
                    source_id = archive_source_id(archive_id, label, key)
                    if store.find_source(source_id) is not None:
                        counts["already_imported"] += 1
                        continue
                    if message is None:
                        counts["unreadable"] += 1
                        continue
                    try:
                        raw, notes = to_rfc822(message)
                        outcome = store.record(parse(raw), {"id": source_id, "source_kind": "pst_archive", "provider": "archive",
                                                            "archive_id": archive_id, "mailbox": label, "record_key": key})
                    except Exception:
                        store.conn.rollback()
                        counts["unreadable"] += 1
                        continue
                    counts["attachments_skipped"] += notes["attachments_skipped"]
                    counts["deduplicated" if outcome.get("action") == "merged" else "indexed_new"] += 1
                    pending += 1
                    if pending >= batch:
                        store.conn.commit()
                        pending = 0
                        if progress:
                            progress({"archive_id": archive_id, "folder": label, **counts})
            store.conn.commit()
    finally:
        _safe(pst_file.close)
    return {"archive_id": archive_id, "file": str(path), "seconds": round(time.perf_counter() - started, 1), **counts}


def import_directory(directory: Path, *, db_path: Path | None = None, progress: Callable[[dict[str, Any]], None] | None = None,
                     include_ost: bool = True) -> dict[str, Any]:
    """Every .pst (and .ost) under ``directory``; an exact copy of a file
    already imported in this run is skipped."""
    directory = Path(directory)
    patterns = ["*.pst", "*.ost"] if include_ost else ["*.pst"]
    files = sorted({item for pattern in patterns for item in directory.rglob(pattern)}, key=lambda item: item.stat().st_size)
    seen: dict[str, str] = {}
    results = []
    for path in files:
        fingerprint = file_fingerprint(path)
        if fingerprint in seen:
            results.append({"file": str(path), "skipped": f"identical copy of {seen[fingerprint]}"})
            continue
        seen[fingerprint] = path.name
        try:
            results.append(import_pst(path, db_path=db_path, progress=progress))
        except Exception as exc:
            results.append({"file": str(path), "error": f"{type(exc).__name__}: {str(exc)[:200]}"})
        if progress:
            progress({"file_done": str(path)})
    summary = {key: sum(item.get(key, 0) for item in results) for key in ("messages_seen", "indexed_new", "deduplicated", "already_imported", "unreadable")}
    report = {"directory": str(directory), "files": results, **summary, "at": datetime.now(timezone.utc).isoformat()}
    log = config.scope_dir("work") / "pst-imports.jsonl"
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps({key: value for key, value in report.items()}) + "\n")
    return report
