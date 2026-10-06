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


class KnowledgeGapEnqueueActionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.store = GapStore(self.tmp.name)
        mod.STORE_FACTORY = lambda: self.store
        self.addCleanup(setattr, mod, "STORE_FACTORY", None)
        self.reg = Registry()
        mod.register(self.reg)
        self.pending = PendingStore(self.tmp.name)
        self.item = {"id": "knowledge-gap-enqueue", "kind": "knowledge_gap_enqueue"}
        self.gaps = [{"id": "g1", "question": "Q1?", "topic": "t", "utility": 1, "urgency": 1}]

    def test_preview_does_not_write_and_confirm_enqueues(self):
        result = self.reg.invoke("knowledge_gap.enqueue", self.item, {"gaps": self.gaps}, self.pending)

        self.assertEqual(result["status"], "needs_confirmation")
        self.assertEqual(self.store.gaps(), [])
        done = self.reg.confirm(result["confirm_token"], self.pending)

        self.assertEqual(done["enqueued"], ["g1"])
        self.assertEqual([gap["id"] for gap in self.store.gaps()], ["g1"])

    def test_empty_or_non_list_gaps_raise(self):
        for gaps in ([], None, "not a list", {"id": "g1"}):
            with self.subTest(gaps=gaps):
                with self.assertRaisesRegex(ValueError, "gaps must be a non-empty JSON list of objects"):
                    mod._enqueue(self.item, {"gaps": gaps}, confirm=False)


if __name__ == "__main__":
    unittest.main()
