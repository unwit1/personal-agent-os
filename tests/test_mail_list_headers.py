import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import sqlite3  # noqa: E402
import tempfile  # noqa: E402
import unittest  # noqa: E402
from email.message import EmailMessage  # noqa: E402

from agent_os.mail import message as message_lib  # noqa: E402
from agent_os.mail import store as store_lib  # noqa: E402


def raw(n: int = 0, **headers: str) -> bytes:
    msg = EmailMessage()
    msg["Subject"] = f"Subject {n}"
    msg["From"] = f"sender{n}@example.com"
    msg["To"] = "me@example.net"
    msg["Date"] = f"Mon, 01 Jun 2026 10:{n // 60:02d}:{n % 60:02d} +0000"
    msg["Message-ID"] = f"<m{n}@example.com>"
    for key, value in headers.items():
        msg[key.replace("_", "-")] = value
    msg.set_content(f"body number {n}")
    return bytes(msg)


def source(n: int) -> dict:
    return {"id": f"src{n}", "source_kind": "live_imap", "provider": "x", "account_id": "a", "mailbox": "INBOX", "uidvalidity": "1", "uid": str(n)}


class ListHeaderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "mail.db"

    def test_parse_headers(self) -> None:
        parsed = message_lib.parse(raw(1, List_Unsubscribe="<mailto:u@x.com>", List_Id=" News <news.example.com> ", Precedence="bulk", Auto_Submitted="auto-generated"))
        self.assertEqual(parsed.list_unsubscribe, "<mailto:u@x.com>")
        self.assertEqual(parsed.list_id, "News <news.example.com>")
        self.assertEqual(parsed.precedence, "bulk")
        self.assertEqual(parsed.auto_submitted, "auto-generated")
        plain = message_lib.parse(raw(2))
        self.assertIsNone(plain.list_unsubscribe)
        self.assertIsNone(plain.auto_submitted)

    def test_search_returns_headers(self) -> None:
        with store_lib.Store(self.path) as store:
            store.record(message_lib.parse(raw(1, List_Id="<l.example.com>", Precedence="list")), source(1))
            store.record(message_lib.parse(raw(2)), source(2))
            store.conn.commit()
            by_subject = {item["subject"]: item for item in store.search("", limit=10)}
        self.assertEqual(by_subject["Subject 1"]["list_id"], "<l.example.com>")
        self.assertEqual(by_subject["Subject 1"]["precedence"], "list")
        self.assertIsNone(by_subject["Subject 2"]["list_id"])
        self.assertIsNone(by_subject["Subject 2"]["list_unsubscribe"])

    def test_old_schema_upgraded_without_data_loss(self) -> None:
        with store_lib.Store(self.path) as store:
            store.record(message_lib.parse(raw(1)), source(1))
            store.conn.commit()
        conn = sqlite3.connect(self.path)
        for column in store_lib.LIST_HEADER_COLUMNS:
            conn.execute(f"ALTER TABLE mail_messages DROP COLUMN {column}")
        conn.commit()
        conn.close()
        with store_lib.Store(self.path) as store:
            columns = {row[1] for row in store.conn.execute("PRAGMA table_info(mail_messages)")}
            self.assertTrue(set(store_lib.LIST_HEADER_COLUMNS) <= columns)
            items = list(store.iter_messages())
            self.assertEqual([item["subject"] for item in items], ["Subject 1"])
            self.assertIsNone(items[0]["list_id"])
            store.record(message_lib.parse(raw(2, List_Id="<z.example.com>")), source(2))
            store.conn.commit()
            newest = {item["subject"]: item for item in store.iter_messages()}
            self.assertEqual(newest["Subject 2"]["list_id"], "<z.example.com>")

    def test_iter_messages_not_capped(self) -> None:
        with store_lib.Store(self.path) as store:
            for n in range(120):
                store.record(message_lib.parse(raw(n)), source(n))
            store.conn.commit()
            items = list(store.iter_messages(batch=25))
            self.assertGreater(len(items), store_lib.MAX_LIMIT)
            self.assertEqual(len(items), 120)
            self.assertEqual(len({item["id"] for item in items}), 120)
            dates = [item["date"] for item in items]
            self.assertEqual(dates, sorted(dates))


if __name__ == "__main__":
    unittest.main()
