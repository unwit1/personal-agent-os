import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

import json
import os
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from unittest import mock

from agent_os.executive import outbox
from agent_os.executive.window import confirm
from agent_os.executive.window.confirm import ItemState, PendingStore, window_home

ITEM = {"id": "work:test-1", "tab": "work", "title": "Synthetic item"}


class WindowHomeTests(unittest.TestCase):
    def test_explicit_home_wins(self):
        with mock.patch.dict(os.environ, {confirm.ENV_HOME: "/env/home"}):
            self.assertEqual(window_home(Path("/explicit")), Path("/explicit"))

    def test_env_home(self):
        with mock.patch.dict(os.environ, {confirm.ENV_HOME: "/env/home"}):
            self.assertEqual(window_home(), Path("/env/home"))

    def test_default_home_beside_outbox(self):
        env = {k: v for k, v in os.environ.items() if k != confirm.ENV_HOME}
        with mock.patch.dict(os.environ, env, clear=True):
            self.assertEqual(window_home(), outbox.DEFAULT_DIR.parent / "executive-window")


class PendingStoreTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.home = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_create_writes_record_and_token_is_single_use(self):
        store = PendingStore(self.home)
        token = store.create("send_email", ITEM, {"to": "a@example.test"}, {"subject": "Hi"})
        path = self.home / "pending" / f"{token}.json"
        self.assertTrue(path.is_file())
        stored = json.loads(path.read_text(encoding="utf-8"))
        self.assertIn("created_at", stored)
        record = store.take(token)
        self.assertEqual(record["action_id"], "send_email")
        self.assertEqual(record["item"], ITEM)
        self.assertEqual(record["params"], {"to": "a@example.test"})
        self.assertEqual(record["preview"], {"subject": "Hi"})
        self.assertFalse(path.exists())
        with self.assertRaises(KeyError):
            store.take(token)

    def test_unknown_and_malformed_tokens_rejected(self):
        store = PendingStore(self.home)
        with self.assertRaises(KeyError):
            store.take("x" * 32)
        with self.assertRaises(KeyError):
            store.take("../state")

    def test_expired_token_rejected(self):
        store = PendingStore(self.home, ttl_seconds=900)
        token = store.create("send_email", ITEM, {}, {})
        later = datetime.now(timezone.utc) + timedelta(seconds=901)
        self.assertEqual(store.list(now=later), [])
        with self.assertRaises(KeyError):
            store.take(token, now=later)
        # An expired take still consumes the record.
        with self.assertRaises(KeyError):
            store.take(token)

    def test_expired_by_stored_created_at(self):
        store = PendingStore(self.home, ttl_seconds=60)
        token = store.create("approve_gate", ITEM, {}, {})
        path = self.home / "pending" / f"{token}.json"
        record = json.loads(path.read_text(encoding="utf-8"))
        record["created_at"] = (datetime.now(timezone.utc) - timedelta(seconds=120)).isoformat()
        path.write_text(json.dumps(record), encoding="utf-8")
        self.assertEqual(store.list(), [])
        with self.assertRaises(KeyError):
            store.take(token)

    def test_list_returns_unexpired_with_tokens(self):
        store = PendingStore(self.home)
        t1 = store.create("a", ITEM, {}, {})
        t2 = store.create("b", ITEM, {}, {})
        tokens = {r["token"] for r in store.list()}
        self.assertEqual(tokens, {t1, t2})

    def test_two_instances_share_records(self):
        first = PendingStore(self.home)
        second = PendingStore(self.home)
        token = first.create("reach_out", ITEM, {"ref": "app-1"}, {"body": "x"})
        self.assertEqual([r["token"] for r in second.list()], [token])
        self.assertEqual(second.take(token)["action_id"], "reach_out")
        with self.assertRaises(KeyError):
            first.take(token)
        self.assertEqual(first.list(), [])

    def test_audit_appends_lines(self):
        store = PendingStore(self.home)
        store.audit({"event": "confirm", "action_id": "send_email"})
        PendingStore(self.home).audit({"event": "reject", "action_id": "approve_gate"})
        lines = (self.home / "audit.jsonl").read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(lines), 2)
        rows = [json.loads(line) for line in lines]
        self.assertEqual([r["event"] for r in rows], ["confirm", "reject"])
        for row in rows:
            ts = datetime.fromisoformat(row["ts"])
            self.assertEqual(ts.utcoffset(), timedelta(0))


class ItemStateTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.home = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_unknown_item_visible(self):
        self.assertFalse(ItemState(self.home).is_hidden("work:none"))

    def test_dismiss_hides_and_persists(self):
        ItemState(self.home).dismiss("work:1")
        self.assertTrue((self.home / "state.json").is_file())
        state = ItemState(self.home)
        self.assertTrue(state.is_hidden("work:1"))
        self.assertFalse(state.is_hidden("work:2"))

    def test_snooze_hides_until_time_passes(self):
        state = ItemState(self.home)
        now = datetime(2026, 10, 2, 12, 0, tzinfo=timezone.utc)
        state.snooze("personal:t1", (now + timedelta(hours=2)).isoformat())
        other = ItemState(self.home)
        self.assertTrue(other.is_hidden("personal:t1", now=now))
        self.assertTrue(other.is_hidden("personal:t1", now=now + timedelta(hours=1)))
        self.assertFalse(other.is_hidden("personal:t1", now=now + timedelta(hours=2, seconds=1)))


if __name__ == "__main__":
    unittest.main()
