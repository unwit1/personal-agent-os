import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

import unittest
from datetime import datetime, timezone

from agent_os.mail import organize

NOW = datetime(2026, 10, 2, tzinfo=timezone.utc)
OWN = {"me@work.test", "me@home.test"}


def row(i, subject, sender, *, scope="work", account="acct-w", mailbox="INBOX", date="2026-09-20T00:00:00+00:00",
        thread=None, recipients="me@work.test", **extra):
    base = {"id": f"msg_{i}", "thread_id": thread or f"t{i}", "subject": subject, "sender": sender,
            "recipients": recipients, "date": date, "snippet": "", "scope": scope, "account_id": account,
            "mailbox": mailbox, "uid": i}
    base.update(extra)
    return base


WORK = [
    # known correspondent (operator wrote to bob) + own sent
    row(1, "Re: plan", "me@work.test", mailbox="Sent", recipients="bob@client.test", thread="tb"),
    row(2, "Can you send the deck?", "bob@client.test", thread="t2"),
    row(3, "Quick update", "bob@client.test", date="2026-09-01T00:00:00+00:00", thread="tw"),
    row(4, "Re: Quick update", "me@work.test", mailbox="Sent", recipients="bob@client.test",
        date="2026-09-02T00:00:00+00:00", thread="tw"),
    row(5, "Your invoice 104", "billing@vendor.test", list_unsubscribe="<mailto:u@vendor.test>"),
    row(6, "Interview schedule", "jobs@indeed.com", list_id="<jobs.indeed.com>"),
    row(7, "Weekly digest", "news@letters.test", list_unsubscribe="<mailto:u@l.test>", list_id="<l>"),
    row(8, "Weekly digest old", "news@letters.test", list_unsubscribe="<mailto:u@l.test>", list_id="<l>",
        date="2025-06-01T00:00:00+00:00"),
    row(9, "Build 55 passed", "noreply@ci.test", auto_submitted="auto-generated"),
    row(10, "WIN a FREE prize!!! 50% off", "deals@promo.test", list_unsubscribe="<u>"),
    row(11, "Cheap pills", "x@junk.test", mailbox="Junk", account="acct-w"),
    row(12, "Old chat", "bob@client.test", date="2024-01-01T00:00:00+00:00", thread="t12",
        recipients="me@work.test, z@x.test"),
]
WORK.append(row(20, "Limited time sale: 50% off, act now", "deals@shop-x.test"))
for n in range(13, 20):
    WORK.append(row(n, f"Digest {n}", "news@letters.test", list_unsubscribe="<u>", list_id="<l>"))

PERSONAL = [
    row(30, "Photos from the trip", "mom@family.test", scope="personal", account="acct-p",
        recipients="dad@family.test"),
    row(31, "Dinner?", "friend@family.test", scope="personal", account="acct-p", recipients="me@home.test"),
    row(32, "Order confirmation", "orders@shop.test", scope="personal", account="acct-p",
        list_unsubscribe="<u>", recipients="me@home.test"),
    row(33, "Your statement", "noreply@bank.test", scope="personal", account="acct-p",
        auto_submitted="auto-generated", recipients="me@home.test"),
]


def iter_rows(scope):
    return {"work": WORK, "personal": PERSONAL}.get(scope)


class OrganizeTests(unittest.TestCase):
    def setUp(self):
        self.plan = organize.build_plan(iter_rows=iter_rows, own=OWN, now=NOW)

    def cat(self, acct, name):
        return self.plan["accounts"][acct]["categories"][name]

    def test_constants(self):
        self.assertEqual(len(organize.CATEGORIES), 9)
        self.assertEqual(set(organize.TARGET_FOLDERS), set(organize.CATEGORIES))
        self.assertIsNone(organize.TARGET_FOLDERS["action_needed"])
        self.assertIsNone(organize.TARGET_FOLDERS["waiting_on_others"])

    def test_categorize_each(self):
        known = {"bob@client.test"}

        def c(r, **kw):
            return organize.categorize(r, own=OWN, known=known, now=NOW, **kw)[0]

        self.assertEqual(c(WORK[1]), "action_needed")
        self.assertEqual(c(WORK[2], thread_last_own=True), "waiting_on_others")
        self.assertEqual(c(WORK[4]), "receipts_finance")
        self.assertEqual(c(WORK[5]), "hr_applicants")
        self.assertEqual(c(WORK[6]), "newsletters_promotions")
        self.assertEqual(c(WORK[7]), "archive_old")
        self.assertEqual(c(WORK[8]), "notifications")
        self.assertEqual(c(PERSONAL[0]), "personal")
        self.assertEqual(c(WORK[0]), "own_sent")
        cat, reason = organize.categorize(WORK[4], own=OWN, known=known, now=NOW)
        self.assertTrue(reason)

    def test_spam_category(self):
        cat, reason = organize.categorize(next(r for r in WORK if r["id"] == "msg_20"), own=OWN, known=set(), now=NOW)
        self.assertEqual(cat, "spam")
        self.assertTrue(reason)
        self.assertEqual(self.cat("acct-w", "spam")["count"], 1)
        self.assertEqual(self.cat("acct-w", "spam")["target_folder"], "Agent OS/Spam")

    def test_counts_per_account(self):
        self.assertEqual(set(self.plan["accounts"]), {"acct-w", "acct-p"})
        self.assertEqual(self.plan["accounts"]["acct-w"]["scope"], "work")
        self.assertEqual(self.plan["accounts"]["acct-p"]["scope"], "personal")
        self.assertEqual(self.cat("acct-w", "action_needed")["count"], 2)
        self.assertEqual(self.cat("acct-w", "waiting_on_others")["count"], 1)
        self.assertEqual(self.cat("acct-w", "receipts_finance")["count"], 1)
        self.assertEqual(self.cat("acct-w", "hr_applicants")["count"], 1)
        self.assertEqual(self.cat("acct-w", "notifications")["count"], 1)
        self.assertEqual(self.cat("acct-w", "archive_old")["count"], 1)
        self.assertEqual(self.cat("acct-p", "personal")["count"], 1)
        self.assertEqual(self.cat("acct-p", "action_needed")["count"], 1)
        for name, entry in self.plan["accounts"].items():
            total = sum(c["count"] for c in entry["categories"].values())
            self.assertEqual(total, entry["inbox_total"], name)

    def test_samples_capped_and_refs(self):
        news = self.cat("acct-w", "newsletters_promotions")
        self.assertGreater(news["count"], 5)
        self.assertEqual(len(news["samples"]), 5)
        self.assertEqual(len(news["messages"]), news["count"])
        ref = news["messages"][0]
        self.assertEqual(set(ref) & {"id", "uid", "mailbox"}, {"id", "uid", "mailbox"})
        self.assertEqual(ref["mailbox"], "INBOX")
        plan = organize.build_plan(iter_rows=iter_rows, own=OWN, now=NOW, sample=50)
        self.assertLessEqual(len(plan["accounts"]["acct-w"]["categories"]["newsletters_promotions"]["samples"]), 5)

    def test_target_folders(self):
        for entry in self.plan["accounts"].values():
            for name, bucket in entry["categories"].items():
                self.assertEqual(bucket["target_folder"], organize.TARGET_FOLDERS[name])
        self.assertEqual(self.cat("acct-w", "receipts_finance")["target_folder"], "Agent OS/Receipts")

    def test_archive_old_needs_over_365_days(self):
        def plan_for(date):
            rows = [row(50, "Weekly digest", "news@letters.test", list_unsubscribe="<u>", list_id="<l>", date=date)]
            return organize.build_plan(scopes=("work",), iter_rows=lambda s: rows, own=OWN, now=NOW)

        young = plan_for("2025-10-03T00:00:00+00:00")["accounts"]["acct-w"]["categories"]
        self.assertEqual(young["newsletters_promotions"]["count"], 1)
        self.assertEqual(young["archive_old"]["count"], 0)
        old = plan_for("2025-10-01T00:00:00+00:00")["accounts"]["acct-w"]["categories"]
        self.assertEqual(old["archive_old"]["count"], 1)
        # action_needed is never archived
        old_ask = self.cat("acct-w", "action_needed")
        self.assertIn("Old chat", old_ask["samples"])

    def test_spam_filtered_counts(self):
        sf = self.plan["spam_filtered"]
        self.assertGreaterEqual(sf["spam"], 1)  # Junk folder row
        self.assertGreaterEqual(sf["own_sent"], 2)
        self.assertGreater(sf["bulk"], 0)
        self.assertIn("acct-w", sf["by_account"])
        self.assertEqual(sf["total"], sf["spam"] + sf["bulk"])

    def test_non_inbox_never_categorized(self):
        refs = [m["id"] for e in self.plan["accounts"].values()
                for b in e["categories"].values() for m in b["messages"]]
        self.assertNotIn("msg_1", refs)
        self.assertNotIn("msg_11", refs)

    def test_missing_scope(self):
        plan = organize.build_plan(iter_rows=lambda s: PERSONAL if s == "personal" else None, own=OWN, now=NOW)
        self.assertEqual(plan["scopes"], ["personal"])
        self.assertEqual(plan["skipped"]["missing_scopes"], ["work"])
        self.assertEqual(set(plan["accounts"]), {"acct-p"})
        both = organize.build_plan(iter_rows=lambda s: None, own=OWN, now=NOW)
        self.assertEqual(both["accounts"], {})

    def test_unknown_account(self):
        rows = [row(60, "Hello?", "bob@client.test", account=None)]
        plan = organize.build_plan(scopes=("work",), iter_rows=lambda s: rows, own=OWN, now=NOW)
        self.assertIn("unknown", plan["accounts"])


if __name__ == "__main__":
    unittest.main()
