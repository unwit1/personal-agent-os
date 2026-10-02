import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from agent_os.executive import outbox
from agent_os.executive.outbox import OutboxError, OutboxStore

SLOT = "2026-10-05T10:00:00"
SLOT2 = "2026-10-06T14:30:00"


def item(ref="app-1", **kw):
    base = {
        "applicant_ref": ref,
        "name": "Test Person",
        "opening": "Technician",
        "manager": "Mgr",
        "interview_type": "phone",
        "location": "HQ",
        "duration_minutes": 30,
        "proposed_slots": [SLOT, SLOT2],
        "subject": "Interview",
        "body": "Hello",
    }
    base.update(kw)
    return base


class OutboxTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.dir = Path(self._tmp.name) / "outbox"
        self.store = OutboxStore(self.dir)

    def test_create_and_reload(self):
        b = self.store.create([item("a"), item("b")])
        self.assertRegex(b["batch_id"], r"^ob-[0-9a-f]{16}$")
        self.assertEqual(b["state"], outbox.PENDING_APPROVAL)
        again = OutboxStore(self.dir).load(b["batch_id"])
        self.assertEqual(again, b)
        self.assertEqual([x["batch_id"] for x in self.store.list()], [b["batch_id"]])
        self.assertEqual(self.store.list(outbox.APPROVED), [])

    def test_ids_are_unique(self):
        ids = {self.store.create([item()])["batch_id"] for _ in range(5)}
        self.assertEqual(len(ids), 5)

    def test_rejects_malformed_input(self):
        for bad in (
            [],
            [item(ref="")],
            [item(ref="../x")],
            [item(proposed_slots=["nope"])],
            [item(duration_minutes="30")],
            [item(aa_pdf_path="x.pdf")],
            [item("a"), item("a")],
            [item(status="approved")],
            ["str"],
        ):
            with self.assertRaises(OutboxError, msg=repr(bad)):
                self.store.create(bad)
        self.assertEqual(self.store.list(), [])

    def test_malformed_files(self):
        b = self.store.create([item()])
        path = self.dir / f"{b['batch_id']}.json"
        path.write_text("{not json", encoding="utf-8")
        with self.assertRaises(OutboxError):
            self.store.load(b["batch_id"])
        self.assertEqual(self.store.list(), [])
        path.write_text(json.dumps({"batch_id": b["batch_id"], "state": "BOGUS"}), encoding="utf-8")
        with self.assertRaises(OutboxError):
            self.store.load(b["batch_id"])
        with self.assertRaises(OutboxError):
            self.store.load("../etc/passwd")
        with self.assertRaises(OutboxError):
            self.store.load("ob-" + "0" * 16)

    def test_approve_flow(self):
        b = self.store.create([item("a"), item("b")])
        bid = b["batch_id"]
        with self.assertRaises(OutboxError):
            self.store.approve(bid, {"a": [SLOT]})  # must cover all items
        with self.assertRaises(OutboxError):
            self.store.approve(bid, {"a": [], "b": None})
        with self.assertRaises(OutboxError):
            self.store.approve(bid, {"a": None, "b": None})
        self.assertEqual(self.store.load(bid)["state"], outbox.PENDING_APPROVAL)
        done = self.store.approve(bid, {"a": [SLOT2], "b": None})
        self.assertEqual(done["state"], outbox.APPROVED)
        loaded = self.store.load(bid)
        self.assertEqual(loaded["items"][0]["chosen_slots"], [SLOT2])
        self.assertEqual(loaded["items"][1]["status"], outbox.ITEM_DROPPED)
        with self.assertRaises(OutboxError):
            self.store.approve(bid, {"a": [SLOT], "b": None})

    def test_send_results(self):
        bid = self.store.create([item("a"), item("b"), item("c")])["batch_id"]
        with self.assertRaises(OutboxError):
            self.store.record_send_result(bid, "a", True, 1)  # not approved yet
        self.store.approve(bid, {"a": [SLOT], "b": [SLOT], "c": None})
        self.store.record_send_result(bid, "a", True, 7)
        self.assertEqual(self.store.load(bid)["state"], outbox.APPROVED)
        with self.assertRaises(OutboxError):
            self.store.record_send_result(bid, "a", True, 8)
        with self.assertRaises(OutboxError):
            self.store.record_send_result(bid, "c", True, 8)
        with self.assertRaises(OutboxError):
            self.store.record_send_result(bid, "zzz", True, 8)
        done = self.store.record_send_result(bid, "b", False, error="outlook down")
        self.assertEqual(done["state"], outbox.PARTIAL)
        with self.assertRaises(OutboxError):
            self.store.record_send_result(bid, "b", True, 9)

    def test_all_sent_and_all_failed(self):
        a = self.store.create([item("a")])["batch_id"]
        self.store.approve(a, {"a": [SLOT]})
        self.assertEqual(self.store.record_send_result(a, "a", True, "e1")["state"], outbox.SENT)
        f = self.store.create([item("a")])["batch_id"]
        self.store.approve(f, {"a": [SLOT]})
        self.assertEqual(self.store.record_send_result(f, "a", False, error="x")["state"], outbox.FAILED)

    def test_write_failure_keeps_previous_file(self):
        b = self.store.create([item()])
        bid = b["batch_id"]
        with mock.patch("agent_os.executive.outbox.os.replace", side_effect=OSError("disk")):
            with self.assertRaises(OSError):
                self.store.approve(bid, {"app-1": [SLOT]})
        self.assertEqual(self.store.load(bid)["state"], outbox.PENDING_APPROVAL)
        self.assertEqual(list(self.dir.glob(".tmp-*")), [])

    def test_recover_removes_stale_temp_files(self):
        b = self.store.create([item()])
        stale = self.dir / ".tmp-abc.json"
        stale.write_text("{partial", encoding="utf-8")
        self.assertEqual(self.store.recover(), 1)
        self.assertFalse(stale.exists())
        self.assertEqual(self.store.load(b["batch_id"])["state"], outbox.PENDING_APPROVAL)
        self.assertEqual(OutboxStore(self.dir / "missing").recover(), 0)


if __name__ == "__main__":
    unittest.main()
