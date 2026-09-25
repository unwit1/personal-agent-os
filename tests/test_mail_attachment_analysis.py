from __future__ import annotations

import sqlite3
import tempfile
import unittest
from unittest import mock
from email.message import EmailMessage
from pathlib import Path

from agent_os.mail import config
from agent_os.mail.attachments import Exporter
from agent_os.mail.attachment_analysis import analyze_recovered
from agent_os.mail.message import parse
from agent_os.mail.store import Store


class AttachmentAnalysisTests(unittest.TestCase):
    def test_local_analysis_links_source_message_and_attachment(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db = root / "mail.sqlite3"
            manifest_dir = root / "scope"
            manifest_dir.mkdir()
            manifest = manifest_dir / "attachments.sqlite3"
            output = root / "analysis"
            downloads = root / "Downloads"

            msg = EmailMessage()
            msg["From"] = "Me <me@icloud.test>"
            msg["To"] = "Other <other@example.test>"
            msg["Date"] = "Fri, 25 Sep 2026 12:00:00 -0400"
            msg["Subject"] = "Notes"
            msg["Message-ID"] = "<notes@example.test>"
            msg.set_content("Attached.")
            msg.add_attachment(b"relationship notes\n", maintype="text", subtype="plain", filename="notes.txt")
            raw = msg.as_bytes()
            parsed = parse(raw)

            with Store(db) as store:
                outcome = store.record(parsed, {
                    "id": "src_test", "source_kind": "live_imap", "provider": "icloud",
                    "account_id": "personal-icloud", "mailbox": "INBOX", "uidvalidity": "1", "uid": "1",
                })
                store.conn.commit()
                message_id = outcome["message_id"]

            with mock.patch.object(config, "scope_dir", return_value=manifest_dir):
                with Exporter("personal", downloads) as exporter:
                    exporter.export(raw, "src_test")

            result = analyze_recovered("personal", root=downloads, manifest_path=manifest, mail_db=db, output_dir=output)
            self.assertEqual(result["counts"]["parsed"], 1)
            records = (output / "records.jsonl").read_text(encoding="utf-8")
            self.assertIn("src_test", records)
            self.assertIn(message_id, records)
            self.assertIn('"promotion_eligible": false', records)
            with sqlite3.connect(db) as conn:
                text = conn.execute("SELECT text FROM mail_attachments").fetchone()[0]
            self.assertIn("relationship notes", text)


if __name__ == "__main__":
    unittest.main()
