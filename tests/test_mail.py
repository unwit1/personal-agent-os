from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os import mail  # noqa: E402


def _message(subject: str, body: str) -> bytes:
    return (f"From: sender@example.test\nTo: recipient@example.test\nSubject: {subject}\n"
            "Message-ID: <fixture@example.test>\nContent-Type: text/plain; charset=utf-8\n\n"
            f"{body}").encode("utf-8")


class MailTests(unittest.TestCase):
    def test_decode_header(self) -> None:
        self.assertEqual(mail._decode("Hello"), "Hello")

    def test_body_plain_text(self) -> None:
        import email
        msg = email.message_from_string("Content-Type: text/plain; charset=utf-8\n\nhello")
        self.assertEqual(mail._body(msg), "hello")

    def test_mail_paths_are_local_and_gitignored(self) -> None:
        ignore = (Path(__file__).resolve().parents[1] / ".gitignore").read_text(encoding="utf-8")
        self.assertIn(".agent-local", str(mail.LOCAL_DIR))
        self.assertIn(".agent-local/", ignore)

    def test_fixture_sync_is_idempotent_and_uses_the_ledger(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            records = [("1", _message("One", "first")), ("2", _message("Two", "second"))]
            first = mail.sync_records(records, db_path=root / "mail.sqlite3")
            second = mail.sync_records(records, db_path=root / "mail.sqlite3")

            self.assertEqual(first["indexed_new"], 2)
            self.assertEqual(second["indexed_new"], 0)
            self.assertEqual(second["skipped"], 2)
            self.assertEqual([item["subject"] for item in mail.search("", db_path=root / "mail.sqlite3")], ["Two", "One"])

    def test_public_sync_delegates_fixture_records_through_the_ledger(self) -> None:
        class FixtureClient:
            def select(self, mailbox: str, readonly: bool = True):
                return "OK", []

            def uid(self, operation: str, value, query: str | None = None):
                if operation == "search":
                    return "OK", [b"1"]
                return "OK", [(b"RFC822", _message("One", "first"))]

            def logout(self) -> None:
                return None

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            original_connect, original_db = mail._connect, mail.DB
            mail._connect = lambda: FixtureClient()
            mail.DB = root / "mail.sqlite3"
            try:
                result = mail.sync()
            finally:
                mail._connect, mail.DB = original_connect, original_db
            self.assertEqual(result["indexed_new"], 1)
            self.assertEqual(mail.search("One", db_path=root / "mail.sqlite3")[0]["subject"], "One")

    def test_fixture_sync_reprocesses_changed_content_for_the_same_uid(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            db_path = root / "mail.sqlite3"
            mail.sync_records([("1", _message("Original", "before"))], db_path=db_path)
            result = mail.sync_records([("1", _message("Updated", "after"))], db_path=db_path)

            self.assertEqual(result["reprocessed"], 1)
            self.assertEqual(mail.search("Updated", db_path=db_path)[0]["subject"], "Updated")
            ledger = json.loads((root / "ingestion.json").read_text(encoding="utf-8"))
            item = next(iter(ledger["items"].values()))
            self.assertEqual(item["status"], "processed")
            self.assertEqual(item["revision"], 2)

    def test_fixture_sync_recovers_an_interrupted_claim(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            db_path = root / "mail.sqlite3"
            records = [("1", _message("One", "first")), ("2", _message("Two", "second"))]
            calls = 0

            def interrupt_on_second(uid: str, mailbox: str, raw: bytes) -> mail.MailMessage:
                nonlocal calls
                calls += 1
                if calls == 2:
                    raise KeyboardInterrupt()
                return mail._parse_record(uid, mailbox, raw)

            with self.assertRaises(KeyboardInterrupt):
                mail.sync_records(records, db_path=db_path, parser=interrupt_on_second)

            interrupted = json.loads((root / "ingestion.json").read_text(encoding="utf-8"))
            self.assertEqual(sorted(item["status"] for item in interrupted["items"].values()), ["processed", "processing"])
            resumed = mail.sync_records(records, db_path=db_path)
            self.assertEqual(resumed["skipped"], 1)
            self.assertEqual(resumed["resumed"], 1)
            self.assertEqual(resumed["indexed_new"], 0)
            self.assertEqual(resumed["errors"], 0)

    def test_fixture_sync_checkpoint_continues_after_interruption(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            db_path = root / "mail.sqlite3"
            records = [("10", _message("Ten", "ten")), ("11", _message("Eleven", "eleven"))]

            def interrupt_after_first(uid: str, mailbox: str, raw: bytes) -> mail.MailMessage:
                if uid == "11":
                    raise KeyboardInterrupt()
                return mail._parse_record(uid, mailbox, raw)

            with self.assertRaises(KeyboardInterrupt):
                mail.sync_records(records, db_path=db_path, parser=interrupt_after_first)
            interrupted = json.loads((root / "ingestion.json").read_text(encoding="utf-8"))
            self.assertEqual(interrupted["checkpoint"]["cursor"], "10")

            mail.sync_records(records, db_path=db_path)
            resumed = json.loads((root / "ingestion.json").read_text(encoding="utf-8"))
            self.assertEqual(resumed["checkpoint"]["cursor"], "11")
            self.assertGreater(resumed["checkpoint"]["sequence"], interrupted["checkpoint"]["sequence"])


if __name__ == "__main__":
    unittest.main()
