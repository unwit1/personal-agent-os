from __future__ import annotations

import json
import sqlite3
import tempfile
import unittest
from unittest import mock
from email.message import EmailMessage
from pathlib import Path

from agent_os.mail import config
from agent_os.mail.attachments import Exporter
from agent_os.mail.attachment_analysis import analyze_recovered, classify_for_review
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
            self.assertTrue(result["coverage_complete"])
            self.assertTrue(result["analysis_complete"])
            self.assertEqual(result["attachment_records_accounted_for"], 1)
            self.assertEqual(result["attachment_records_recovered"], 1)
            records = (output / "records.jsonl").read_text(encoding="utf-8")
            self.assertIn("src_test", records)
            self.assertIn(message_id, records)
            self.assertIn('"promotion_eligible": false', records)
            with sqlite3.connect(db) as conn:
                text = conn.execute("SELECT text FROM mail_attachments").fetchone()[0]
            self.assertIn("relationship notes", text)
            queue = (output / "review-queue.jsonl").read_text(encoding="utf-8")
            self.assertIn('"promotion_eligible": false', queue)

    def test_resume_triage_is_high_priority_but_not_promotion(self) -> None:
        review = classify_for_review(
            "Jacob Resume.docx",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "Education\nEmployment Experience\nSkills",
        )
        self.assertEqual(review["review_category"], "resume_or_cv")
        self.assertEqual(review["review_priority"], "high")
        self.assertFalse(review["promotion_eligible"])
        self.assertIn("education", review["candidate_destinations"])

    def test_privacy_findings_raise_attachment_sensitivity(self) -> None:
        review = classify_for_review(
            "application.pdf",
            "application/pdf",
            "Contact test.person@example.com and SSN 123-45-6789.",
        )
        self.assertEqual(review["sensitivity_hint"], "restricted_high")
        self.assertEqual(review["review_priority"], "high")
        self.assertIn("email", review["privacy_findings"])
        self.assertIn("ssn", review["privacy_findings"])
        self.assertFalse(review["promotion_eligible"])


    def test_multiple_source_occurrences_do_not_inflate_attachment_count(self) -> None:
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
            msg["Subject"] = "Same logical message in two folders"
            msg["Message-ID"] = "<same@example.test>"
            msg.set_content("Attached.")
            msg.add_attachment(b"one attachment\n", maintype="text", subtype="plain", filename="one.txt")
            raw = msg.as_bytes()
            parsed = parse(raw)

            with Store(db) as store:
                first = store.record(parsed, {
                    "id": "src_inbox", "source_kind": "live_imap", "provider": "icloud",
                    "account_id": "personal-icloud", "mailbox": "INBOX", "uidvalidity": "1", "uid": "1",
                })
                second = store.record(parsed, {
                    "id": "src_archive", "source_kind": "live_imap", "provider": "icloud",
                    "account_id": "personal-icloud", "mailbox": "Archive", "uidvalidity": "2", "uid": "9",
                })
                store.conn.commit()
                self.assertEqual(first["message_id"], second["message_id"])

            with mock.patch.object(config, "scope_dir", return_value=manifest_dir):
                with Exporter("personal", downloads) as exporter:
                    exporter.export(raw, "src_inbox")
                    exporter.export(raw, "src_archive")

            result = analyze_recovered("personal", manifest_path=manifest, mail_db=db, output_dir=output)
            self.assertEqual(result["attachment_records_accounted_for"], 1)
            self.assertEqual(result["attachment_records_recovered"], 1)
            self.assertEqual(result["occurrence_records_written"], 2)
            queue = [json.loads(line) for line in (output / "review-queue.jsonl").read_text(encoding="utf-8").splitlines()]
            self.assertEqual(len(queue), 1)
            self.assertEqual(queue[0]["occurrence_count"], 2)
            self.assertEqual(set(queue[0]["source_ids"]), {"src_inbox", "src_archive"})


if __name__ == "__main__":
    unittest.main()
