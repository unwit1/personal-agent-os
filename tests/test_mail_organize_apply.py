import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

import tempfile
import unittest
from datetime import datetime, timedelta, timezone

from agent_os.mail import organize_apply as oa
from agent_os.mail.accounts import Account

NOW = datetime(2026, 10, 2, 12, 0, tzinfo=timezone.utc)


class FakeMover:
    def __init__(self, ids=None, move_support=True, flags=("\\*",), validity="100"):
        self.calls = []
        self.ids = ids or {}
        self.move_support = move_support
        self.flags = list(flags)
        self.validity = validity
        self.where = {}  # rfc id -> (mailbox, uid)
        self.uid_rfc = {}
        self.counter = 6

    def capabilities(self, mailbox):
        self.calls.append(("capabilities", mailbox))
        return {"move": self.move_support, "permanent_flags": self.flags}

    def ensure_folder(self, name):
        self.calls.append(("ensure_folder", name))
        return name.replace("/", ".")

    def select(self, mailbox):
        self.calls.append(("select", mailbox))
        return self.validity

    def message_ids(self, uids):
        self.calls.append(("message_ids", tuple(uids)))
        return {u: self.ids.get(u) or self.uid_rfc[u] for u in uids if u in self.ids or u in self.uid_rfc}

    def _relocate(self, uids, target):
        out = {}
        for uid in uids:
            rfc = (self.ids.get(uid) or self.uid_rfc.get(uid, "")).strip("<>").lower()
            self.counter += 1
            new = str(self.counter)
            self.where[rfc] = (target, new)
            self.uid_rfc[new] = rfc
            out[uid] = new
        return out

    def move(self, uids, target):
        self.calls.append(("move", tuple(uids), target))
        return self._relocate(uids, target)

    def copy_flag(self, uids, target):
        self.calls.append(("copy_flag", tuple(uids), target))
        return self._relocate(uids, target)

    def unflag(self, uids):
        self.calls.append(("unflag", tuple(uids)))

    def find(self, mailbox, rfc):
        self.calls.append(("find", mailbox, rfc))
        mailbox_uid = self.where.get(rfc.strip('<>').lower())
        return mailbox_uid[1] if mailbox_uid and mailbox_uid[0] == mailbox else None

    def close(self):
        self.calls.append(("close",))

    def verbs(self):
        return [c[0] for c in self.calls]


class FakeStore:
    def __init__(self):
        self.moved, self.present = [], []

    def mark_source_moved(self, source_id):
        self.moved.append(source_id)

    def mark_source_present(self, source_id):
        self.present.append(source_id)


def account(account_id="work-a", allow=True):
    return Account(id=account_id, provider="icloud", email="me@example.com", allow_organize=allow, scope="work")


def make_plan(target="Agent OS/Receipts", category="receipts_finance", generated=NOW, validity="100"):
    return {
        "plan_id": "plan_x", "generated_at": generated.isoformat(), "scope": "work",
        "folders": {"action_needed": None, category: target},
        "accounts": {
            "work-a": {"categories": {category: {"count": 2, "samples": ["Invoice 1"], "target_folder": target,
                                                  "message_ids": ["msg_1", "msg_2"]}}},
            "work-b": {"categories": {category: {"count": 1, "samples": ["Receipt"], "target_folder": target,
                                                  "message_ids": ["msg_3"]}}},
        },
        "sources": {
            "work-a": {
                "msg_1": {"source_id": 1, "mailbox": "INBOX", "uidvalidity": validity, "uid": "41", "rfc_message_id": "a1@x.com"},
                "msg_2": {"source_id": 2, "mailbox": "INBOX", "uidvalidity": validity, "uid": "42", "rfc_message_id": "a2@x.com"},
            },
            "work-b": {"msg_3": {"source_id": 3, "mailbox": "INBOX", "uidvalidity": validity, "uid": "9", "rfc_message_id": "b1@x.com"}},
        },
    }


IDS = {"41": "<A1@X.com>", "42": "<a2@x.com>", "9": "<b1@x.com>"}


class ApplyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.journal = Path(self.tmp.name) / "j" / "organize-journal.jsonl"

    def run_apply(self, plan=None, movers=None, accounts=None, **kwargs):
        movers = movers if movers is not None else {"work-a": FakeMover(IDS), "work-b": FakeMover(IDS)}
        opened = []

        def connect(acct):
            opened.append(acct.id)
            return movers[acct.id]

        kwargs.setdefault("journal_path", self.journal)
        result = oa.apply_plan(plan or make_plan(), "receipts_finance", accounts=accounts or [account("work-a"), account("work-b")],
                               now=NOW, connect=connect, **kwargs)
        return result, movers, opened

    def test_dry_run_is_default_and_never_connects(self):
        result, movers, opened = self.run_apply()
        self.assertTrue(result["dry_run"])
        self.assertIsNone(result["journal_id"])
        self.assertEqual(opened, [])
        self.assertEqual(result["accounts"]["work-a"]["would_move"], 2)
        self.assertEqual(result["accounts"]["work-a"]["status"], "dry_run")
        self.assertFalse(self.journal.exists())
        for mover in movers.values():
            self.assertEqual(mover.calls, [])

    def test_real_run_moves_and_journals(self):
        store = FakeStore()
        result, movers, opened = self.run_apply(dry_run=False, store=store)
        self.assertEqual(opened, ["work-a", "work-b"])
        row = result["accounts"]["work-a"]
        self.assertEqual((row["status"], row["moved"], row["method"]), ("moved", 2, "move"))
        self.assertIn(("move", ("41", "42"), "Agent OS.Receipts"), movers["work-a"].calls)
        self.assertEqual(sorted(store.moved), [1, 2, 3])
        lines = oa.read_journal(self.journal)
        a_lines = [l for l in lines if l["account_id"] == "work-a"]
        self.assertEqual([l["status"] for l in a_lines], ["pending", "pending", "moved", "moved"])
        # pending precedes the IMAP command
        self.assertEqual(lines[0]["status"], "pending")
        final = [l for l in a_lines if l["status"] == "moved"][0]
        self.assertEqual(final["undo"]["command"], f"agent-os mail organize-undo {result['journal_id']} --seq {final['seq']}")
        self.assertEqual(final["from"]["mailbox"], "INBOX")
        self.assertEqual(final["to"]["mailbox"], "Agent OS.Receipts")
        self.assertEqual(final["rfc_message_id"], "a1@x.com")
        self.assertNotIn("delete", " ".join(sum((m.verbs() for m in movers.values()), [])).lower())
        self.assertFalse({"expunge", "close_mailbox", "delete"} & set(sum((m.verbs() for m in movers.values()), [])))

    def test_undo_and_double_undo(self):
        result, movers, _ = self.run_apply(dry_run=False)
        jid = result["journal_id"]
        store = FakeStore()
        preview = oa.undo(jid, journal_path=self.journal)
        self.assertTrue(preview["dry_run"])
        self.assertEqual(len(preview["would_undo"]), 3)
        self.assertEqual(len([c for c in movers["work-a"].calls if c[0] == "move"]), 1)
        done = oa.undo(jid, dry_run=False, journal_path=self.journal, connect=lambda a: movers[a.id],
                       accounts=[account("work-a"), account("work-b")], store=store, now=NOW)
        self.assertEqual(len(done["undone"]), 3, done)
        self.assertIn(("move", ("7",), "INBOX"), movers["work-a"].calls)
        self.assertEqual(sorted(store.present), [1, 2, 3])
        undone = [l for l in oa.read_journal(self.journal) if l["status"] == "undone"]
        self.assertEqual(len(undone), 3)
        self.assertNotIn("undo", undone[0])
        with self.assertRaises(oa.UndoError):
            oa.undo(jid, dry_run=False, journal_path=self.journal, connect=lambda a: movers[a.id],
                    accounts=[account("work-a"), account("work-b")])

    def test_undo_skips_orphaned_pending(self):
        oa._append(self.journal, {"journal_id": "org_1", "seq": 1, "status": "pending", "account_id": "work-a"})
        result = oa.undo("org_1", dry_run=False, journal_path=self.journal, connect=lambda a: FakeMover(),
                         accounts=[account()])
        self.assertEqual(result["skipped"], [{"seq": 1, "reason": "no final journal line"}])

    def test_read_only_account_is_skipped_with_reason(self):
        movers = {"work-a": FakeMover(IDS), "work-b": FakeMover(IDS)}
        result, _, opened = self.run_apply(movers=movers, dry_run=False, accounts=[account("work-a", allow=False), account("work-b")])
        self.assertEqual(opened, ["work-b"])
        row = result["accounts"]["work-a"]
        self.assertEqual(row["status"], "skipped_not_enabled")
        self.assertIn("allow_organize", row["skipped_reason"])
        self.assertEqual(movers["work-a"].calls, [])
        dry, _, _ = self.run_apply(accounts=[account("work-a", allow=False), account("work-b")])
        self.assertEqual(dry["accounts"]["work-a"]["status"], "skipped_not_enabled")
        self.assertEqual(dry["accounts"]["work-a"]["would_move"], 0)

    def test_no_outlook_backend(self):
        self.assertFalse(hasattr(oa, "choose_backend"))

    def test_none_target_is_noop(self):
        plan = make_plan(target=None)
        result, movers, opened = self.run_apply(plan=plan, dry_run=False)
        self.assertEqual(opened, [])
        self.assertTrue(result["noop"])
        self.assertTrue(result["skipped_reason"])
        self.assertFalse(self.journal.exists())

    def test_unknown_category_and_stale_plan(self):
        with self.assertRaises(oa.OrganizeError):
            oa.apply_plan(make_plan(), "nope", accounts=[], now=NOW)
        old = make_plan(generated=NOW - timedelta(hours=25))
        with self.assertRaises(oa.OrganizeError):
            self.run_apply(plan=old)

    def test_message_id_mismatch_is_skipped(self):
        ids = dict(IDS, **{"42": "<other@x.com>"})
        movers = {"work-a": FakeMover(ids), "work-b": FakeMover(IDS)}
        result, _, _ = self.run_apply(movers=movers, dry_run=False)
        row = result["accounts"]["work-a"]
        self.assertEqual(row["moved"], 1)
        self.assertEqual(row["skipped"], [{"message_id": "msg_2", "reason": oa.CHANGED}])
        self.assertIn(("move", ("41",), "Agent OS.Receipts"), movers["work-a"].calls)

    def test_missing_message_id_uses_uid_identity(self):
        plan = make_plan()
        for source in plan["sources"]["work-a"].values():
            source["rfc_message_id"] = None
        plan["sources"]["work-a"]["msg_2"]["uidvalidity"] = None
        movers = {"work-a": FakeMover({}), "work-b": FakeMover(IDS)}
        result, _, _ = self.run_apply(plan=plan, movers=movers, dry_run=False)
        row = result["accounts"]["work-a"]
        self.assertEqual(row["skipped"], [{"message_id": "msg_2", "reason": oa.UNVERIFIED}])
        self.assertIn(("move", ("41",), "Agent OS.Receipts"), movers["work-a"].calls)

    def test_uidvalidity_change_moves_nothing(self):
        movers = {"work-a": FakeMover(IDS, validity="999"), "work-b": FakeMover(IDS)}
        result, _, _ = self.run_apply(movers=movers, dry_run=False)
        row = result["accounts"]["work-a"]
        self.assertEqual(row["moved"], 0)
        self.assertEqual({s["reason"] for s in row["skipped"]}, {oa.UIDVALIDITY_CHANGED})
        self.assertNotIn("move", movers["work-a"].verbs())

    def test_copy_fallback_and_keyword_refusal(self):
        movers = {"work-a": FakeMover(IDS, move_support=False), "work-b": FakeMover(IDS, move_support=False, flags=("\\Seen",))}
        result, _, _ = self.run_apply(movers=movers, dry_run=False)
        self.assertEqual(result["accounts"]["work-a"]["method"], "copy_flag")
        self.assertIn("copy_flag", movers["work-a"].verbs())
        refused = result["accounts"]["work-b"]
        self.assertEqual((refused["status"], refused["error"]), ("error", oa.NO_KEYWORD))
        self.assertNotIn("copy_flag", movers["work-b"].verbs())

    def test_connection_error_does_not_stop_other_accounts(self):
        def connect(acct):
            if acct.id == "work-a":
                raise OSError("down")
            return FakeMover(IDS)

        result = oa.apply_plan(make_plan(), "receipts_finance", accounts=[account("work-a"), account("work-b")],
                               now=NOW, connect=connect, dry_run=False, journal_path=self.journal)
        self.assertEqual(result["accounts"]["work-a"]["status"], "error")
        self.assertEqual(result["accounts"]["work-b"]["moved"], 1)

    def test_copy_flag_undo_unflags_and_keeps_copy(self):
        movers = {"work-a": FakeMover(IDS, move_support=False), "work-b": FakeMover(IDS, move_support=False)}
        result, _, _ = self.run_apply(movers=movers, dry_run=False)
        oa.undo(result["journal_id"], seq=1, dry_run=False, journal_path=self.journal, accounts=[account("work-a")],
                connect=lambda a: movers[a.id])
        self.assertIn(("unflag", ("41",)), movers["work-a"].calls)

    def test_undo_finds_personal_scope_journal_by_default(self):
        from unittest import mock
        paths = {"work": Path(self.tmp.name) / "work.jsonl", "personal": Path(self.tmp.name) / "personal.jsonl"}
        plan = make_plan()
        plan["scope"] = "personal"
        with mock.patch.object(oa, "default_journal_path", side_effect=lambda scope="work": paths[scope]):
            result, movers, _ = self.run_apply(plan=plan, dry_run=False, journal_path=None)
            self.assertTrue(paths["personal"].exists())
            self.assertFalse(paths["work"].exists())
            done = oa.undo(result["journal_id"], dry_run=False, connect=lambda a: movers[a.id],
                           accounts=[account("work-a"), account("work-b")], now=NOW)
            self.assertEqual(len(done["undone"]), 3, done)
            with self.assertRaises(oa.UndoError):
                oa.undo(result["journal_id"], scope="personal", dry_run=False, connect=lambda a: movers[a.id],
                        accounts=[account("work-a"), account("work-b")])

    def test_journal_is_read_once_per_apply_and_undo(self):
        from unittest import mock
        real = oa.read_journal
        with mock.patch.object(oa, "read_journal", side_effect=real) as spy:
            result, movers, _ = self.run_apply(dry_run=False)
            self.assertEqual(spy.call_count, 0)
            spy.reset_mock()
            oa.undo(result["journal_id"], dry_run=False, journal_path=self.journal, connect=lambda a: movers[a.id],
                    accounts=[account("work-a"), account("work-b")], now=NOW)
            self.assertEqual(spy.call_count, 1)
        seqs = [l["seq"] for l in real(self.journal) if l["status"] == "undone"]
        self.assertEqual(seqs, sorted(set(seqs)))

    def test_partial_move_then_raise_keeps_moved_messages_undoable(self):
        class Partial(FakeMover):
            def move(self, uids, target):
                if any(c[0] == "move" for c in self.calls):
                    return super().move(uids, target)
                self.calls.append(("move", tuple(uids), target))
                self._relocate(uids[:1], target)
                raise RuntimeError("connection dropped")

        movers = {"work-a": Partial(IDS), "work-b": FakeMover(IDS)}
        result, movers, _ = self.run_apply(movers=movers, dry_run=False)
        row = result["accounts"]["work-a"]
        self.assertEqual((row["moved"], row["failed"]), (1, 1))
        lines = [l for l in oa.read_journal(self.journal) if l["account_id"] == "work-a" and l["status"] != "pending"]
        self.assertEqual(sorted(l["status"] for l in lines), ["failed", "moved"])
        moved = [l for l in lines if l["status"] == "moved"][0]
        self.assertIn("undo", moved)
        done = oa.undo(result["journal_id"], seq=moved["seq"], dry_run=False, journal_path=self.journal,
                       connect=lambda a: movers[a.id], accounts=[account("work-a"), account("work-b")], now=NOW)
        self.assertEqual(len(done["undone"]), 1, done)

    def test_default_journal_path_is_under_mail_home(self):
        from agent_os.mail import config
        self.assertEqual(oa.default_journal_path("work").parent, config.scope_dir("work"))


if __name__ == "__main__":
    unittest.main()
