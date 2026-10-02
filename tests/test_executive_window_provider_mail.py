import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

import unittest
from datetime import datetime, timedelta, timezone
from unittest import mock

from agent_os import mail
from agent_os.executive.window.providers_mail import mail_items

NOW = datetime(2026, 10, 2, 12, tzinfo=timezone.utc)
ME = "me@example.com"


def msg(i, thread, sender, days, subject="Hello", to=ME, snippet=""):
    return dict(id=i, thread_id=thread, subject=subject, sender=sender, recipients=to,
                date=(NOW - timedelta(days=days)).isoformat(), message_id="<%s@x>" % i, snippet=snippet)


ROWS = [
    msg("1", "t-reply", "Pat <pat@corp.com>", 2, "Lunch?"),
    msg("2", "t-own", "Pat <pat@corp.com>", 3),
    msg("3", "t-own", "Me <%s>" % ME, 1),
    msg("4", "t-noreply", "noreply@shop.com", 1, "Receipt?"),
    msg("5", "t-stale", "Old <old@corp.com>", 60, "Still there?"),
]


class MailProviderTests(unittest.TestCase):
    def test_reply_needed_returned_and_excluded(self):
        calls = []

        def fake(query, **kw):
            calls.append(kw)
            return list(ROWS)

        with mock.patch.object(mail, "sync", side_effect=AssertionError("sync called")):
            items = mail_items(own_addresses=[ME], search=fake, now=NOW)
        self.assertEqual([i["id"] for i in items], ["mail:t-reply"])
        item = items[0]
        self.assertEqual(item["tab"], "personal")
        self.assertEqual(item["kind"], "mail_thread")
        self.assertEqual(item["age_days"], 2)
        self.assertEqual(item["context"], {"thread_id": "t-reply", "message_id": "<1@x>",
                                           "sender": "Pat <pat@corp.com>", "subject": "Lunch?"})
        self.assertNotIn("body", item)
        self.assertEqual(len(calls), 1)

    def test_default_search_is_local_index_only(self):
        with mock.patch.object(mail, "sync", side_effect=AssertionError("sync called")), \
             mock.patch.object(mail, "search", return_value=list(ROWS)) as s:
            items = mail_items(own_addresses=[ME], now=NOW)
        s.assert_called_once()
        self.assertEqual(len(items), 1)


if __name__ == "__main__":
    unittest.main()
