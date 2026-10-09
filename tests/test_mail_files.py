"""Loose mail files (.eml, zip exports, mbox) import into the work index with message-level dedupe."""

import email
import sqlite3
import zipfile
from email.message import EmailMessage

from agent_os.mail import files


def _eml(n: int) -> bytes:
    msg = EmailMessage()
    msg["From"] = "a@example.org"
    msg["To"] = "b@example.org"
    msg["Subject"] = f"Synthetic {n}"
    msg["Date"] = "Mon, 05 Oct 2026 10:00:00 -0400"
    msg["Message-ID"] = f"<synthetic-{n}@example.org>"
    msg.set_content(f"Body {n}")
    return msg.as_bytes()


def _counts(db):
    with sqlite3.connect(db) as conn:
        return (conn.execute("SELECT COUNT(*) FROM mail_messages").fetchone()[0],
                conn.execute("SELECT COUNT(*) FROM mail_sources").fetchone()[0])


def test_eml_zip_and_mbox_copies_merge(tmp_path):
    src = tmp_path / "src"
    (src / "Inbox").mkdir(parents=True)
    for n in range(3):
        (src / "Inbox" / f"{n}.eml").write_bytes(_eml(n))
    (src / "notes.ics").write_text("BEGIN:VCALENDAR\nEND:VCALENDAR\n")
    with zipfile.ZipFile(src / "export.zip", "w") as archive:
        for n in range(4):  # 3 duplicates + 1 new
            archive.writestr(f"Outlook/Inbox/{n}.eml", _eml(n))
    mbox = src / "Thunderbird" / "INBOX"
    mbox.parent.mkdir()
    mbox.write_bytes(b"".join(b"From MAILER-DAEMON Mon Oct  5 10:00:00 2026\n" + _eml(n) + b"\n" for n in (0, 5, 5)))  # Thunderbird can hold identical copies
    (mbox.parent / "INBOX.msf").write_text("")
    db, ledgers = tmp_path / "index.sqlite3", tmp_path / "ledgers"

    results = files.import_path(src, db_path=db, ledger_dir=ledgers)
    kinds = {r["source_kind"]: r for r in results}
    assert set(kinds) == {"mail_file", "zip_export", "mbox"}
    assert kinds["mail_file"]["other_items"] == 1
    assert kinds["zip_export"]["deduplicated"] == 3
    assert kinds["mbox"]["deduplicated"] == 1
    assert _counts(db) == (5, 9)  # five distinct emails, nine observed copies

    again = files.import_path(src, db_path=db, ledger_dir=ledgers)
    assert all(r["indexed_new"] == 0 and r["skipped"] == r["checked"] for r in again)
    assert _counts(db) == (5, 9)


def test_near_duplicate_export_copy_merges_into_original(tmp_path):
    from agent_os.mail import dedupe, sync_archive_records

    db, ledgers = tmp_path / "index.sqlite3", tmp_path / "ledgers"
    original = _eml(1)
    sync_archive_records([{"folder": "Inbox", "record_key": "1", "raw": original}], archive_id="pst-test",
                         db_path=db, ledger_dir=ledgers)
    parsed = email.message_from_bytes(original)
    copy = EmailMessage()
    for name in ("From", "To", "Subject", "Date"):
        copy[name] = parsed[name]
    copy.set_content("Body 1\n\n-- converted by export tool")  # re-rendered body, no Message-ID
    other = EmailMessage()
    for name in ("From", "To", "Subject", "Date"):
        other[name] = copy[name]
    other.set_content("A completely different message about payroll deadlines")
    src = tmp_path / "export"
    src.mkdir()
    (src / "copy.eml").write_bytes(copy.as_bytes())
    (src / "other.eml").write_bytes(other.as_bytes())
    files.import_path(src, db_path=db, ledger_dir=ledgers)
    assert _counts(db) == (3, 3)
    result = dedupe.merge_near_duplicates("work", db_path=db)
    assert result["merged"] == 1
    assert _counts(db) == (2, 3)  # the copy's source now belongs to the original; the different text stays separate
