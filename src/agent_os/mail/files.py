"""Import loose mail files into the **work** mail index.

Handles what Outlook and conversion tools leave behind besides PSTs: ``.eml``
files, Outlook ``.msg`` files, and ``.zip`` exports of either. Every file goes
through :func:`agent_os.mail.sync_archive_records`, so a copy of a message that
is already indexed (from IMAP, a PST, or another export) becomes one more
source observation of the same logical message: nothing is stored twice and
every copy stays attributable.

Archive ids: a zip is one archive (``zip-`` + size/head/tail fingerprint, so
a renamed or moved copy of the same zip is recognised); the loose files under
one import root are one archive (``files-`` + hash of the root path). Record
keys are paths relative to the archive. Reruns skip what is already recorded.
Calendar items (.ics) and contacts (.vcf) are counted, not imported.
"""

from __future__ import annotations

import hashlib
import mimetypes
import zipfile
from email.message import EmailMessage
from email.policy import default as default_policy
from email.utils import format_datetime
from pathlib import Path
from typing import Any, Callable, Iterator

from . import sync_archive_records
from .pst import COPY_HEADERS, MAX_ATTACHMENT_BYTES, file_fingerprint

MAIL_SUFFIXES = {".eml", ".msg"}
OTHER_ITEM_SUFFIXES = {".ics", ".vcf"}


def _clean(value: Any) -> str:
    return " ".join(str(value or "").replace("\x00", "").split())


def msg_to_rfc822(source: str | bytes | Path) -> bytes:
    """Rebuild an Outlook .msg (path or bytes) as RFC822, like ``pst.to_rfc822``."""
    import extract_msg  # type: ignore

    msg = extract_msg.openMsg(str(source) if isinstance(source, Path) else source)
    try:
        out = EmailMessage(policy=default_policy)
        header = getattr(msg, "header", None)
        if header is not None:
            for name in COPY_HEADERS:
                value = header.get(name)
                if value:
                    try:
                        out[name] = _clean(value)
                    except Exception:
                        pass
        for name, attr in (("From", "sender"), ("To", "to"), ("Cc", "cc"), ("Subject", "subject"), ("Message-ID", "messageId")):
            if not out[name]:
                value = _clean(getattr(msg, attr, None))
                if value:
                    try:
                        out[name] = value
                    except Exception:
                        pass
        when = getattr(msg, "date", None)
        if not out["Date"] and when is not None and hasattr(when, "tzinfo"):
            try:
                out["Date"] = format_datetime(when)
            except Exception:
                pass
        plain = getattr(msg, "body", None) or ""
        html = getattr(msg, "htmlBody", None) or b""
        html = html.decode("utf-8", "replace") if isinstance(html, bytes) else str(html)
        if plain:
            out.set_content(plain)
            if html:
                out.add_alternative(html, subtype="html")
        elif html:
            out.set_content(html, subtype="html")
        else:
            out.set_content("")
        for index, attachment in enumerate(getattr(msg, "attachments", []) or []):
            data = getattr(attachment, "data", None)
            if not isinstance(data, bytes) or not data or len(data) > MAX_ATTACHMENT_BYTES:
                continue  # embedded messages, links, and oversized files stay listed in the source only
            filename = getattr(attachment, "longFilename", None) or getattr(attachment, "shortFilename", None) or f"attachment-{index + 1}"
            mime = getattr(attachment, "mimetype", None) or mimetypes.guess_type(filename)[0] or "application/octet-stream"
            main, _, sub = mime.partition("/")
            try:
                out.add_attachment(data, maintype=main or "application", subtype=sub or "octet-stream", filename=filename)
            except Exception:
                pass
        return out.as_bytes()
    finally:
        try:
            msg.close()
        except Exception:
            pass


def _raw(name: str, data: bytes) -> bytes:
    return msg_to_rfc822(data) if name.lower().endswith(".msg") else data


def _records(items: Iterator[tuple[str, Callable[[], bytes]]], counts: dict[str, int]) -> Iterator[dict[str, Any]]:
    yielded: set[str] = set()
    for rel, read in items:
        if rel in yielded:  # a zip may hold two entries with one name; the ledger keys on the name
            counts["duplicate_names"] = counts.get("duplicate_names", 0) + 1
            continue
        yielded.add(rel)
        suffix = Path(rel).suffix.lower()
        if suffix in OTHER_ITEM_SUFFIXES:
            counts["other_items"] += 1
            continue
        if suffix not in MAIL_SUFFIXES:
            continue
        counts["files"] += 1
        try:
            raw = _raw(rel, read())
        except Exception:
            counts["unreadable"] += 1
            continue
        folder, _, _ = rel.replace("\\", "/").rpartition("/")
        yield {"folder": folder or "(root)", "record_key": rel.replace("\\", "/"), "raw": raw}


def zip_archive_id(path: Path) -> str:
    return "zip-" + file_fingerprint(path)[:20]


def files_archive_id(root: Path) -> str:
    return "files-" + hashlib.sha256(str(root.resolve()).lower().encode("utf-8")).hexdigest()[:20]


def import_zip(path: Path, *, db_path: Path | None = None, ledger_dir: Path | None = None) -> dict[str, Any]:
    path = Path(path)
    counts = {"files": 0, "unreadable": 0, "other_items": 0}
    with zipfile.ZipFile(path) as archive:
        entries = ((info.filename, lambda info=info: archive.read(info)) for info in archive.infolist() if not info.is_dir())
        result = sync_archive_records(_records(entries, counts), archive_id=zip_archive_id(path), source_kind="zip_export",
                                      db_path=db_path, ledger_dir=ledger_dir)
    return {"path": str(path), **result, **counts}


def import_loose(root: Path, files: list[Path], *, db_path: Path | None = None, ledger_dir: Path | None = None) -> dict[str, Any]:
    root = Path(root)
    counts = {"files": 0, "unreadable": 0, "other_items": 0}
    entries = ((str(item.relative_to(root)) if item.is_relative_to(root) else item.name, item.read_bytes) for item in files)
    result = sync_archive_records(_records(entries, counts), archive_id=files_archive_id(root), source_kind="mail_file",
                                  db_path=db_path, ledger_dir=ledger_dir)
    return {"path": str(root), **result, **counts}


def is_mbox(path: Path) -> bool:
    """A Thunderbird/Unix mailbox: no suffix, and a .msf index beside it or a leading "From " line."""
    if path.suffix.lower() not in ("", ".mbox", ".mbx") or not path.is_file() or path.stat().st_size == 0:
        return False
    if path.with_name(path.name + ".msf").exists() or path.suffix.lower() in (".mbox", ".mbx"):
        return True
    with path.open("rb") as handle:
        return handle.read(5) == b"From "


def import_mbox(root: Path, files: list[Path], *, db_path: Path | None = None, ledger_dir: Path | None = None) -> dict[str, Any]:
    """Every message of every mbox under ``root``; record keys are content-addressed so compaction never re-adds."""
    import mailbox

    root = Path(root)
    counts = {"files": 0, "unreadable": 0, "other_items": 0}

    def records() -> Iterator[dict[str, Any]]:
        yielded: set[str] = set()
        for item in files:
            rel = (str(item.relative_to(root)) if item.is_relative_to(root) else item.name).replace("\\", "/")
            box = mailbox.mbox(str(item), create=False)
            try:
                for key in box.iterkeys():
                    try:
                        raw = box.get_bytes(key)
                    except Exception:
                        counts["unreadable"] += 1
                        continue
                    counts["files"] += 1
                    key = f"{rel}#{hashlib.sha256(raw).hexdigest()[:24]}"
                    if key in yielded:  # the same bytes twice in one mbox (Thunderbird keeps copies until compaction)
                        counts["identical_in_file"] = counts.get("identical_in_file", 0) + 1
                        continue
                    yielded.add(key)
                    yield {"folder": rel, "record_key": key, "raw": raw}
            finally:
                box.close()

    result = sync_archive_records(records(), archive_id="mbox-" + files_archive_id(root)[6:], source_kind="mbox",
                                  db_path=db_path, ledger_dir=ledger_dir)
    return {"path": str(root), **result, **counts}


def import_path(path: Path, *, db_path: Path | None = None, ledger_dir: Path | None = None,
                progress: Callable[[dict[str, Any]], None] | None = None) -> list[dict[str, Any]]:
    """Import one file, or every .eml/.msg/.zip/mbox under a folder (PSTs are left to ``import-pst``)."""
    path = Path(path)
    mboxes: list[Path] = []
    if path.is_file() and path.suffix.lower() == ".zip":
        zips, loose, root = [path], [], path.parent
    elif path.is_file() and is_mbox(path):
        zips, loose, root, mboxes = [], [], path.parent, [path]
    elif path.is_file():
        zips, loose, root = [], [path], path.parent
    else:
        root = path
        everything = sorted(item for item in path.rglob("*") if item.is_file())
        zips = [item for item in everything if item.suffix.lower() == ".zip"]
        loose = [item for item in everything if item.suffix.lower() in MAIL_SUFFIXES | OTHER_ITEM_SUFFIXES]
        mboxes = [item for item in everything if is_mbox(item)]
    results = []
    if loose:
        results.append(import_loose(root, loose, db_path=db_path, ledger_dir=ledger_dir))
        if progress:
            progress(results[-1])
    if mboxes:
        results.append(import_mbox(root, mboxes, db_path=db_path, ledger_dir=ledger_dir))
        if progress:
            progress(results[-1])
    for item in zips:
        try:
            with zipfile.ZipFile(item) as archive:
                if not any(Path(name).suffix.lower() in MAIL_SUFFIXES for name in archive.namelist()):
                    continue
        except (zipfile.BadZipFile, OSError):
            continue
        results.append(import_zip(item, db_path=db_path, ledger_dir=ledger_dir))
        if progress:
            progress(results[-1])
    return results
