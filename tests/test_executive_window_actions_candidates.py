from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.executive.window import actions_candidates as mod
from agent_os.executive.window.confirm import PendingStore
from agent_os.executive.window.registry import Registry


class CandidateActionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.records = [{
            "id": "candidate-1", "status": "candidate", "kind": "fact_candidate",
            "statement": "The release is October 20", "evidence": ["note-1"],
            "confidence": 0.8, "task_summary": "Release planning",
        }]
        self.curated = []
        self.curation = {"promoted": ["candidate-1"]}
        mod.STATUS = lambda project: {"project": project, "candidates": self.records}
        mod.CURATE = lambda project, ids, action: self.curated.append((project, ids, action)) or self.curation
        self.addCleanup(setattr, mod, "STATUS", None)
        self.addCleanup(setattr, mod, "CURATE", None)

    def _invoke_and_confirm(self, action_id, action, note):
        reg = Registry()
        mod.register(reg)
        item = {"id": "memory-candidate:candidate-1", "kind": "memory_candidate",
                "context": {"project": "alpha", "candidate_id": "candidate-1"}}
        preview = {
            "project": "alpha", "candidate_id": "candidate-1", "action": action,
            "candidate": {key: self.records[0].get(key) for key in
                          ("kind", "statement", "evidence", "confidence", "task_summary")},
            "note": note,
        }
        pending = PendingStore(self.tmp.name)
        result = reg.invoke(action_id, item, {}, pending)
        self.assertEqual(result["status"], "needs_confirmation")
        self.assertEqual(result["preview"], preview)
        self.assertEqual(self.curated, [])
        done = reg.confirm(result["confirm_token"], pending)
        self.assertEqual(self.curated, [("alpha", ["candidate-1"], action)])
        self.assertEqual(done, {"project": "alpha", "candidate_id": "candidate-1",
                                "action": action, "curation": self.curation})

    def test_accept_preview_then_confirm(self):
        self._invoke_and_confirm(
            "candidate.accept", "promote",
            "Promotes this candidate if it passes the curator checks (evidence, confidence >= 0.7, non-material kind).",
        )

    def test_reject_preview_then_confirm(self):
        self._invoke_and_confirm(
            "candidate.reject", "reject", "Marks this candidate rejected; nothing is promoted."
        )

    def test_already_rejected_candidate_raises(self):
        self.records[0]["status"] = "rejected"
        with self.assertRaisesRegex(ValueError, "^candidate already rejected$"):
            mod._accept({"context": {"project": "alpha", "candidate_id": "candidate-1"}}, {}, confirm=False)

    def test_unknown_candidate_raises(self):
        with self.assertRaisesRegex(ValueError, "^unknown candidate: missing$"):
            mod._accept({"context": {"project": "alpha", "candidate_id": "missing"}}, {}, confirm=False)


if __name__ == "__main__":
    unittest.main()
