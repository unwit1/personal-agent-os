from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.executive.window import providers_candidates as mod


class CandidateProviderTests(unittest.TestCase):
    def setUp(self):
        self.projects = ["zeta", "alpha"]
        self.records = {
            "alpha": [
                {"id": "candidate-2", "status": "candidate", "statement": "Second", "kind": "lesson_candidate", "task_summary": "Task", "evidence": ["e2"], "confidence": 0.8},
                {"id": "candidate-1", "status": "candidate", "statement": "First", "kind": "decision_candidate", "task_summary": None, "evidence": None, "confidence": None},
                {"id": "candidate-0", "status": "rejected", "statement": "Rejected", "kind": "lesson_candidate"},
                {"id": "candidate-3", "status": "promoted", "statement": "Promoted", "kind": "lesson_candidate"},
                {"id": "candidate-4", "status": "merged", "statement": "Merged", "kind": "lesson_candidate"},
            ],
            "zeta": [
                {"id": "candidate-5", "status": "candidate", "statement": "Zeta", "kind": "preference_candidate", "evidence": [], "confidence": 0.5},
            ],
        }
        mod.PROJECTS = lambda: self.projects
        mod.STATUS = lambda pid: {"candidates": self.records[pid]}
        self.addCleanup(setattr, mod, "PROJECTS", None)
        self.addCleanup(setattr, mod, "STATUS", None)

    def test_emits_only_candidates_with_exact_item_shape_and_sorted_order(self):
        self.assertEqual(mod.candidate_items(), [
            {
                "id": "candidate:alpha:candidate-1",
                "kind": "memory_candidate",
                "title": "First",
                "tab": "work",
                "source": "Candidate memory",
                "sensitivity": "personal",
                "why": "decision_candidate staged from: unknown",
                "context": {"project": "alpha", "candidate_id": "candidate-1", "kind": "decision_candidate", "evidence": [], "confidence": None},
            },
            {
                "id": "candidate:alpha:candidate-2",
                "kind": "memory_candidate",
                "title": "Second",
                "tab": "work",
                "source": "Candidate memory",
                "sensitivity": "personal",
                "why": "lesson_candidate staged from: Task",
                "context": {"project": "alpha", "candidate_id": "candidate-2", "kind": "lesson_candidate", "evidence": ["e2"], "confidence": 0.8},
            },
            {
                "id": "candidate:zeta:candidate-5",
                "kind": "memory_candidate",
                "title": "Zeta",
                "tab": "work",
                "source": "Candidate memory",
                "sensitivity": "personal",
                "why": "preference_candidate staged from: unknown",
                "context": {"project": "zeta", "candidate_id": "candidate-5", "kind": "preference_candidate", "evidence": [], "confidence": 0.5},
            },
        ])

    def test_skips_project_when_status_raises_key_error(self):
        mod.PROJECTS = lambda: ["alpha", "missing", "zeta"]

        def status(pid):
            if pid == "missing":
                raise KeyError(pid)
            return {"candidates": self.records[pid]}

        mod.STATUS = status
        items = mod.candidate_items()
        self.assertEqual([item["context"]["project"] for item in items], ["alpha", "alpha", "zeta"])


if __name__ == "__main__":
    unittest.main()
