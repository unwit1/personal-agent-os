import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

import json
import os
import tempfile
import unittest
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest import mock

import agent_os.executive.window.actions_mail_organize as mo
from agent_os.executive.window.confirm import ENV_HOME, PendingStore
from agent_os.executive.window.registry import Registry


def make_plan():
    return dict(
        plan_id="p1", scope="work", generated_at=datetime.now(timezone.utc).isoformat(),
        folders=dict(newsletters_promotions="Agent/Newsletters"),
        spam_filtered=dict(total=2, by_account=dict(a1=dict(spam=2))),
        accounts=dict(a1=dict(scope="work", inbox_total=1, categories=dict(
            newsletters_promotions=dict(count=1, samples=["Sale"], message_ids=["m1"],
                                        target_folder="Agent/Newsletters")))),
        sources=dict(a1=dict(m1=dict(mailbox="INBOX", uid="7", uidvalidity="5",
                                     rfc_message_id="<x@example.com>"))),
    )


class FakeMover:
    def __init__(self):
        self.moved = []

    def capabilities(self, mailbox):
        return dict(move=True, permanent_flags=[])

    def ensure_folder(self, name):
        return name

    def select(self, mailbox):
        return "5"

    def message_ids(self, uids):
        return {u: "<x@example.com>" for u in uids}

    def move(self, uids, target):
        self.moved.append((list(uids), target))
        return {u: "70" for u in uids}

    def copy_flag(self, uids, target):
        raise AssertionError("not expected")

    def unflag(self, uids):
        pass

    def find(self, mailbox, rfc):
        return "70"

    def close(self):
        pass


class MailOrganizeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        env = mock.patch.dict(os.environ, {ENV_HOME: self.tmp.name})
        env.start()
        self.addCleanup(env.stop)
        self.mover = FakeMover()
        account = SimpleNamespace(id="a1", allow_organize=True, mail_scope="work")
        hooks = (("BUILD_PLAN", make_plan), ("MOVERS", lambda acct: self.mover),
                 ("ACCOUNTS", [account]), ("JOURNAL_PATH", Path(self.tmp.name) / "journal.jsonl"))
        for name, value in hooks:
            patcher = mock.patch.object(mo, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        self.registry = Registry()
        mo.register(self.registry)
        self.registry.register_provider("mail_cleanup", mo.mail_cleanup_items)
        self.pending = PendingStore(self.tmp.name)

    def item(self, tab="work"):
        return next(i for i in mo.mail_cleanup_items() if i["tab"] == tab)

    def test_item_without_plan(self):
        items = mo.mail_cleanup_items()
        self.assertEqual([i["id"] for i in items], ["mail:cleanup:work", "mail:cleanup:personal"])
        for i in items:
            self.assertEqual(i["kind"], "mail_cleanup")
            self.assertEqual(i["title"], "Organize inbox")
            self.assertIsNone(i["context"]["plan"])
        out = self.registry.outstanding("work")
        self.assertEqual({o["action_id"] for o in out["items"][0]["options"]},
                         {"mail.organize_inbox", "mail.organize_apply"})

    def test_organize_inbox_writes_cache(self):
        res = self.registry.invoke("mail.organize_inbox", self.item(), {}, self.pending)
        self.assertEqual(res["status"], "done")
        cache = Path(self.tmp.name) / mo.PLAN_FILE
        self.assertEqual(json.loads(cache.read_text(encoding="utf-8"))["plan_id"], "p1")
        work, personal = self.item("work"), self.item("personal")
        self.assertIn("a1", work["context"]["plan"])
        self.assertEqual(personal["context"]["plan"], {})
        self.assertEqual(work["context"]["spam_filtered"]["total"], 2)

    def test_apply_needs_confirmation_with_preview(self):
        self.registry.invoke("mail.organize_inbox", self.item(), {}, self.pending)
        res = self.registry.invoke("mail.organize_apply", self.item(),
                                   dict(account="a1", category="newsletters_promotions"), self.pending)
        self.assertEqual(res["status"], "needs_confirmation")
        self.assertTrue(res["preview"]["dry_run"])
        self.assertEqual(res["preview"]["accounts"]["a1"]["would_move"], 1)
        self.assertEqual(self.mover.moved, [])

    def test_confirm_moves_and_returns_undo(self):
        self.registry.invoke("mail.organize_inbox", self.item(), {}, self.pending)
        res = self.registry.invoke("mail.organize_apply", self.item(),
                                   dict(account="a1", category="newsletters_promotions"), self.pending)
        out = self.registry.confirm(res["confirm_token"], self.pending)
        self.assertEqual(self.mover.moved, [(["7"], "Agent/Newsletters")])
        self.assertTrue(out["move_id"])
        self.assertIn(out["move_id"], out["undo_command"])
        self.assertEqual(out["accounts"]["a1"]["moved"], 1)


if __name__ == "__main__":
    unittest.main()
