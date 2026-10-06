from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.executive.window import actions_knowledge_gaps as mod
from agent_os.executive.window.confirm import PendingStore
from agent_os.executive.window.gap_store import GapStore
from agent_os.executive.window.registry import Registry


class KnowledgeGapActionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.store = GapStore(self.tmp.name)
        self.store.add([{"id": "gap-1", "question": "What is the release date?", "project": "alpha"}], tab="work")
        self.staged = []
        mod.STORE_FACTORY = lambda: self.store
        mod.PROJECT_EXISTS = lambda pid: pid in {"alpha", "beta"}
        mod.STAGE = lambda project, source, items: self.staged.append((project, source, items)) or {"created": [{"id": "candidate-1"}], "duplicates": []}
        self.addCleanup(setattr, mod, "STORE_FACTORY", None)
        self.addCleanup(setattr, mod, "PROJECT_EXISTS", None)
        self.addCleanup(setattr, mod, "STAGE", None)

    def test_preview_then_confirm_stages_once_and_marks_gap_answered(self):
        reg = Registry()
        mod.register(reg)
        item = {"id": "knowledge-gap:gap-1", "kind": "knowledge_gap_question", "context": {"gap_id": "gap-1"}}
        params = {"answer": "October 20", "project": "alpha"}
        pending = PendingStore(self.tmp.name)
        result = reg.invoke("knowledge_gap.answer", item, params, pending)
        candidate = {
            "kind": "preference_candidate",
            "statement": "What is the release date? -> October 20",
            "evidence": ["knowledge-gap:gap-1", "executive:knowledge-gap"],
            "confidence": 0.7,
        }
        preview = {
            "gap_id": "gap-1", "project": "alpha", "candidate": candidate,
            "note": "Stages a candidate for review; nothing is promoted.",
        }
        self.assertEqual(result, {"status": "needs_confirmation", "confirm_token": result["confirm_token"], "preview": preview})
        self.assertEqual(self.staged, [])
        done = reg.confirm(result["confirm_token"], pending)
        self.assertEqual(self.staged, [("alpha", "Executive knowledge gap", [candidate])])
        self.assertEqual(done, {"gap_id": "gap-1", "project": "alpha", "staging": {"created": [{"id": "candidate-1"}], "duplicates": []}})
        self.assertEqual(self.store.get("gap-1")["status"], "answered")

    def test_empty_answer_raises_before_preview(self):
        with self.assertRaisesRegex(ValueError, "answer must be non-empty"):
            mod._answer({"context": {"gap_id": "gap-1"}}, {"answer": "  ", "project": "alpha"}, confirm=False)
        self.assertEqual(self.staged, [])

    def test_unknown_project_raises(self):
        with self.assertRaisesRegex(ValueError, "unknown project: missing"):
            mod._answer({"context": {"gap_id": "gap-1"}}, {"answer": "soon", "project": "missing"}, confirm=False)

    def test_missing_project_raises(self):
        self.store.add([{"id": "gap-2", "question": "Which milestone?"}])
        with self.assertRaisesRegex(ValueError, "pass project to stage the answer"):
            mod._answer({"context": {"gap_id": "gap-2"}}, {"answer": "M2"}, confirm=False)


if __name__ == "__main__":
    unittest.main()
