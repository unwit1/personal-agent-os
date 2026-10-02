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
        self.assertEqual([i["id"] for i in items if i["kind"] == "mail_thread"], ["mail:t-reply"])
        item = items[0]
        self.assertEqual(item["tab"], "personal")
        self.assertEqual(item["kind"], "mail_thread")
        self.assertEqual(item["age_days"], 2)
        self.assertEqual(item["context"], {"thread_id": "t-reply", "message_id": "<1@x>",
                                           "sender": "Pat <pat@corp.com>", "subject": "Lunch?"})
        self.assertNotIn("body", item)
        self.assertEqual(sorted(c.get("scope") for c in calls), ["personal", "work"])  # one local query per scope index

    def test_default_search_is_local_index_only(self):
        with mock.patch.object(mail, "sync", side_effect=AssertionError("sync called")), \
             mock.patch.object(mail, "search", return_value=list(ROWS)) as s:
            items = mail_items(own_addresses=[ME], now=NOW)
        self.assertEqual(sorted(c.kwargs.get("scope") for c in s.call_args_list), ["personal", "work"])
        self.assertEqual([i["id"] for i in items if i["kind"] == "mail_thread"], ["mail:t-reply"])


if __name__ == "__main__":
    unittest.main()


class MailScopeTabTests(unittest.TestCase):
    def test_work_scope_threads_go_to_the_work_tab(self):
        from datetime import datetime, timezone
        from agent_os.executive.window.providers_mail import mail_items

        now = datetime(2026, 10, 2, 12, tzinfo=timezone.utc)

        def search(query, scope=None, **kw):
            sender = {"personal": "Friend <friend@example.org>", "work": "Vendor <vendor@example.com>"}[scope]
            return [{"thread_id": f"t-{scope}", "id": f"m-{scope}", "message_id": f"m-{scope}", "date": "2026-10-01T09:00:00+00:00",
                     "sender": sender, "recipients": "me@example.net", "subject": f"{scope} question?", "snippet": "can you reply?"}]

        items = mail_items(own_addresses=["me@example.net"], search=search, now=now)
        tabs = {item["context"]["thread_id"]: item["tab"] for item in items}
        self.assertEqual(tabs, {"t-personal": "personal", "t-work": "work"})

    def test_a_scope_without_an_index_is_skipped(self):
        from datetime import datetime, timezone
        from agent_os.executive.window.providers_mail import mail_items

        def search(query, scope=None, **kw):
            if scope == "work":
                raise ValueError("no work index")
            return []

        self.assertEqual(mail_items(own_addresses=[], search=search, now=datetime(2026, 10, 2, tzinfo=timezone.utc)), [])


class MailFilterTests(unittest.TestCase):
    def _items(self, rows):
        return mail_items(own_addresses=[ME], search=lambda q, **kw: list(rows) if kw.get("scope") != "work" else [], now=NOW)

    def test_newsletter_is_filtered_and_counted(self):
        rows = [dict(msg("n1", "t-news", "Weekly <hello@news.example.com>", 1, "This week?"), list_unsubscribe="<mailto:u@x>"),
                msg("h1", "t-human", "Pat <pat@corp.com>", 1, "Lunch?")]
        items = self._items(rows)
        self.assertEqual([i["id"] for i in items if i["kind"] == "mail_thread"], ["mail:t-human"])
        summary = next(i for i in items if i["kind"] == "mail_filtered")
        self.assertEqual(summary["id"], "mail:filtered:personal")
        self.assertEqual(summary["score"], 0)
        self.assertEqual(summary["title"], "1 mail thread filtered (bulk/spam)")
        entry = summary["context"]["filtered"][0]
        self.assertIn("has List-Unsubscribe header", entry["reasons"])
        self.assertEqual(sum(summary["context"]["counts"].values()), 1)

    def test_junk_folder_message_is_filtered(self):
        rows = [dict(msg("j1", "t-junk", "Pat <pat@corp.com>", 1, "Are you there?"), mailbox="Junk")]
        items = self._items(rows)
        self.assertEqual([i["kind"] for i in items], ["mail_filtered"])
        self.assertEqual(items[0]["context"]["filtered"][0]["verdict"], "spam")

    def test_borderline_message_yields_review(self):
        rows = [msg("r1", "t-border", "Shop <sales@store.example.com>", 1, "Order now?")]
        items = self._items(rows)
        review = [i for i in items if i["kind"] == "mail_review"]
        self.assertEqual([i["id"] for i in review], ["mail:review:t-border"])
        self.assertTrue(review[0]["context"]["reasons"])
        self.assertIn(review[0]["context"]["reasons"][0], review[0]["why"])

    def test_nothing_filtered_means_no_summary(self):
        items = self._items([msg("h1", "t-human", "Pat <pat@corp.com>", 1, "Lunch?")])
        self.assertEqual([i["kind"] for i in items], ["mail_thread"])
