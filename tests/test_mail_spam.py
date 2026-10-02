import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import unittest

from agent_os.mail.spam import classify, known_correspondents

OWN = {"me@example.com"}
KNOWN = {"pat@corp.com"}
R_KNOWN = "known correspondent (you replied before)"
R_FIRST = "first contact (you never replied)"


def run(**kw):
    kw.setdefault("mailbox", "INBOX")
    return classify(kw, own=OWN, known=KNOWN)


class MailSpamTests(unittest.TestCase):
    def check(self, res, verdict, score, reasons):
        self.assertEqual(res["verdict"], verdict)
        self.assertEqual(res["score"], score)
        self.assertEqual(res["reasons"], reasons)

    def test_junk_folder(self):
        self.check(run(sender="Lee <lee@new.org>", subject="Lunch?", mailbox="Junk E-mail"),
                   "spam", 100, ["in server spam folder (Junk E-mail)"])
        self.assertEqual(run(sender="lee@new.org", mailbox="[Gmail]/Spam")["verdict"], "spam")
        self.assertEqual(run(sender="lee@new.org", mailbox="Junk Notes")["verdict"], "human")
        self.assertEqual(run(sender="pat@corp.com", mailbox="INBOX.Junk")["verdict"], "spam")

    def test_list_unsubscribe(self):
        self.check(run(sender="news@brand.com", subject="Spring SALE: 30% off",
                       list_unsubscribe="<mailto:u@brand.com>"),
                   "bulk", 12, ["has List-Unsubscribe header", "generic sender address (news@)",
                                "promotional subject (% off, sale)", R_FIRST])

    def test_list_id(self):
        self.check(run(sender="pat@corp.com", subject="Minutes from Tuesday",
                       list_id="<team.corp.com>"),
                   "review", 3, ["mailing list (List-Id)", R_KNOWN])

    def test_precedence_bulk(self):
        self.check(run(sender="lee@new.org", subject="Update", precedence="Bulk"),
                   "review", 5, ["Precedence: Bulk", R_FIRST])

    def test_auto_submitted(self):
        self.check(run(sender="pat@corp.com", subject="Out of office", auto_submitted="auto-replied"),
                   "bulk", 8, ["auto-generated (Auto-Submitted)"])
        self.assertEqual(run(sender="lee@new.org", auto_submitted="no")["verdict"], "human")

    def test_noreply_sender(self):
        self.check(run(sender="noreply@shop.com", subject="Your receipt"),
                   "bulk", 7, ["automated sender address", R_FIRST])
        self.assertEqual(run(sender="bouncer@x.org")["verdict"], "human")

    def test_promotional_subject(self):
        self.check(run(sender="deals@promo-mart.biz", subject="Limited time deal: 50% off"),
                   "spam", 7, ["generic sender address (deals@)",
                               "promotional subject (% off, deal, limited time)", R_FIRST,
                               "unsolicited promotion (no unsubscribe headers)"])

    def test_own_sent_mail(self):
        self.check(run(sender="Me <ME@example.com>", subject="Re: Lunch?"),
                   "bulk", 0, ["own sent mail"])

    def test_known_correspondent_weak_signal_stays_human(self):
        self.check(run(sender="Pat <pat@corp.com>", subject="Webinar notes"),
                   "human", 0, ["promotional subject (webinar)", R_KNOWN])
        self.check(run(sender="Pat <pat@corp.com>", subject="Lunch?"), "human", 0, [R_KNOWN])

    def test_first_contact_borderline_review(self):
        self.check(run(sender="Lee <lee@new.org>", subject="Webinar invite?"),
                   "review", 3, ["promotional subject (webinar)", R_FIRST])
        self.check(run(sender="info@smallbiz.example", subject="Your quote"),
                   "review", 3, ["generic sender address (info@)", R_FIRST])

    def test_plain_human_question(self):
        self.check(run(sender="Lee <lee@new.org>", subject="Lunch?"), "human", 1, [R_FIRST])

    def test_known_correspondents(self):
        rows = [
            {"sender": "me@example.com", "recipients": "Pat <pat@corp.com>, me@example.com",
             "cc": "kim@x.org"},
            {"sender": "lee@new.org", "recipients": "me@example.com, cc@y.org"},
        ]
        self.assertEqual(known_correspondents(rows, OWN), {"pat@corp.com", "kim@x.org"})

    def test_robust(self):
        self.assertEqual(classify({}, own=set(), known=set())["reasons"], ["no bulk signals"])
        with self.assertRaises(TypeError):
            classify([], own=set(), known=set())


if __name__ == "__main__":
    unittest.main()
