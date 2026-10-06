from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.executive.window import actions_brain_dump as mod
from agent_os.executive.window.brain_dump_store import BrainDumpStore
from agent_os.executive.window.confirm import PendingStore
from agent_os.executive.window.registry import Registry


class BrainDumpActionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.store = BrainDumpStore(self.tmp.name)
        self.store.add({"records": [{"id": "bd-1", "text": "Keep notes concise", "confidence": 0.8}]}, tab="work")
        self.staged = []
        mod.STORE_FACTORY = lambda: self.store
        mod.PROJECT_EXISTS = lambda pid: pid in {"alpha", "beta"}
        mod.STAGE = lambda project, source, items: self.staged.append((project, source, items)) or {"created": [{"id": "candidate-1"}], "duplicates": []}
        self.addCleanup(setattr, mod, "STORE_FACTORY", None)
        self.addCleanup(setattr, mod, "PROJECT_EXISTS", None)
        self.addCleanup(setattr, mod, "STAGE", None)

    def test_clarify_sets_project_and_rejects_unknown(self):
        item = {"context": {"record_id": "bd-1"}}
        self.assertEqual(mod._clarify(item, {"project": "alpha"}, confirm=False), {"record_id": "bd-1", "project": "alpha"})
        self.assertEqual(self.store.get("bd-1")["project"], "alpha")
        with self.assertRaisesRegex(ValueError, "unknown project: missing"):
            mod._clarify(item, {"project": "missing"}, confirm=False)

    def test_preview_then_confirm_stages_once_and_marks_record(self):
        reg = Registry()
        mod.register(reg)
        item = {"id": "brain-dump:bd-1", "kind": "brain_dump_record", "context": {"record_id": "bd-1"}}
        pending = PendingStore(self.tmp.name)
        result = reg.invoke("brain_dump.stage_candidate", item, {"project": "alpha"}, pending)
        candidate = {"kind": "preference_candidate", "statement": "Keep notes concise", "evidence": ["executive:brain-dump", "brain-dump:bd-1"], "confidence": 0.8}
        preview = {"record_id": "bd-1", "project": "alpha", "candidate": candidate, "note": "Stages a candidate for review; nothing is promoted."}
        self.assertEqual(result, {"status": "needs_confirmation", "confirm_token": result["confirm_token"], "preview": preview})
        self.assertEqual(self.staged, [])
        done = reg.confirm(result["confirm_token"], pending)
        self.assertEqual(len(self.staged), 1)
        self.assertEqual(self.staged[0], ("alpha", "Executive brain dump", [candidate]))
        self.assertEqual(done, {"record_id": "bd-1", "project": "alpha", "staging": {"created": [{"id": "candidate-1"}], "duplicates": []}})
        self.assertEqual(self.store.get("bd-1")["status"], "staged")

    def test_stage_requires_project(self):
        item = {"context": {"record_id": "bd-1"}}
        with self.assertRaisesRegex(ValueError, "resolve the project first"):
            mod._stage_candidate(item, {}, confirm=False)


if __name__ == "__main__":
    unittest.main()
