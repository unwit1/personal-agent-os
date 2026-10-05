import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

import json
import tempfile
import unittest

from agent_os.executive.window.confirm import ItemState, PendingStore
from agent_os.executive.window.registry import REGISTRY, Registry, register_action, register_provider


def setUpModule():
    """Keep these tests out of the repository's real Executive Event Bus log."""
    global _BUS_DIR, _PREVIOUS_BUS
    from agent_os.executive.event_bus import EventBus
    from agent_os.executive.window import builtin as _builtin, registry as _registry

    _builtin.default_registry()
    _BUS_DIR = tempfile.TemporaryDirectory()
    _PREVIOUS_BUS = _registry.REGISTRY.event_bus
    _registry.REGISTRY.attach_event_bus(EventBus(_BUS_DIR.name))


def tearDownModule():
    from agent_os.executive.window import registry as _registry

    _registry.REGISTRY.attach_event_bus(_PREVIOUS_BUS)
    _BUS_DIR.cleanup()


def item(i, tab="work", kind="note"):
    return {"id": i, "tab": tab, "kind": kind, "title": i, "why": "w", "source": "s", "context": {}}


class RegistryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.pending = PendingStore(self.tmp.name)
        self.reg = Registry()
        self.calls = []

        def safe(it, params, *, confirm):
            self.calls.append(("safe", confirm))
            return {"ok": True}

        def risky(it, params, *, confirm):
            self.calls.append(("risky", confirm))
            return {"sent": True} if confirm else {"preview": "x"}

        self.reg.register_action("safe", "Safe", ["note"], safe, False)
        self.reg.register_action("risky", "Risky", "*", risky, True)
        self.reg.register_provider("p", lambda: [item("a"), item("b", "personal", "mail")])

    def test_options_from_registry(self):
        out = self.reg.outstanding()
        by = {i["id"]: i for i in out["items"]}
        self.assertEqual([o["action_id"] for o in by["a"]["options"]], ["safe", "risky"])
        self.assertEqual([o["action_id"] for o in by["b"]["options"]], ["risky"])
        self.assertTrue(by["a"]["options"][1]["consequential"])
        self.assertEqual([i["id"] for i in self.reg.outstanding("personal")["items"]], ["b"])
        self.assertNotIn("handler", self.reg.actions()[0])

    def test_new_action_appears(self):
        self.reg.register_action("more", "More", ["mail"], lambda i, p, *, confirm: {}, False)
        by = {i["id"]: i for i in self.reg.outstanding()["items"]}
        self.assertIn("more", [o["action_id"] for o in by["b"]["options"]])
        self.assertNotIn("more", [o["action_id"] for o in by["a"]["options"]])

    def test_failing_provider_reported(self):
        def boom():
            raise RuntimeError("bad")
        self.reg.register_provider("boom", boom)
        out = self.reg.outstanding()
        self.assertEqual(len(out["items"]), 2)
        self.assertEqual(out["errors"][0]["provider"], "boom")
        self.assertIn("bad", out["errors"][0]["error"])

    def test_state_hides(self):
        state = ItemState(self.tmp.name)
        state.dismiss("a")
        self.assertEqual([i["id"] for i in self.reg.outstanding(state=state)["items"]], ["b"])

    def test_replace_same_id(self):
        self.reg.register_action("safe", "Other", ["note"], lambda i, p, *, confirm: {"n": 1}, False)
        self.assertEqual([a["label"] for a in self.reg.actions() if a["id"] == "safe"], ["Other"])
        self.assertEqual(len(self.reg.actions()), 2)

    def test_non_consequential_runs(self):
        r = self.reg.invoke("safe", item("a"), {}, self.pending)
        self.assertEqual(r, {"status": "done", "result": {"ok": True}})

    def test_consequential_needs_confirm_once(self):
        r = self.reg.invoke("risky", item("a"), {"to": "x"}, self.pending)
        self.assertEqual(r["status"], "needs_confirmation")
        self.assertEqual(r["preview"], {"preview": "x"})
        self.assertNotIn(("risky", True), self.calls)
        result = self.reg.confirm(r["confirm_token"], self.pending)
        self.assertEqual(result, {"sent": True})
        self.assertIn(("risky", True), self.calls)
        with self.assertRaises(KeyError):
            self.reg.confirm(r["confirm_token"], self.pending)
        self.assertEqual(self.calls.count(("risky", True)), 1)
        lines = self.pending.audit_path.read_text(encoding="utf-8").splitlines()
        rec = json.loads(lines[-1])
        self.assertEqual((rec["action_id"], rec["item_id"], rec["result"]), ("risky", "a", {"sent": True}))

    def test_confirm_error_audited(self):
        def bad(it, params, *, confirm):
            if confirm:
                raise ValueError("nope")
            return {}
        self.reg.register_action("bad", "Bad", "*", bad, True)
        r = self.reg.invoke("bad", item("a"), {}, self.pending)
        with self.assertRaises(ValueError):
            self.reg.confirm(r["confirm_token"], self.pending)
        rec = json.loads(self.pending.audit_path.read_text(encoding="utf-8").splitlines()[-1])
        self.assertIn("nope", rec["error"])

    def test_unknown_action_and_token(self):
        with self.assertRaises(KeyError):
            self.reg.invoke("nope", item("a"), {}, self.pending)
        with self.assertRaises(KeyError):
            self.reg.confirm("x" * 24, self.pending)

    def test_default_registry_functions(self):
        register_provider("t", lambda: [item("z")])
        register_action("t-act", "T", "*", lambda i, p, *, confirm: {}, False)
        try:
            out = REGISTRY.outstanding()
            self.assertIn("t-act", [o["action_id"] for o in out["items"][0]["options"]])
        finally:
            REGISTRY._providers.pop("t", None)
            REGISTRY._actions.pop("t-act", None)


if __name__ == "__main__":
    unittest.main()
