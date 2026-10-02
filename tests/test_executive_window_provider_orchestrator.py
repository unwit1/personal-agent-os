import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

import unittest

from agent_os.executive.window.providers_orchestrator import orchestrator_items


class OrchestratorProviderTests(unittest.TestCase):
    def test_gates_become_items(self):
        """Open approval gates produce orchestrator_gate items."""
        runs = [{"run_id": "run1", "state": "APPROVAL_REQUIRED"}]
        statuses = {
            "run1": {
                "gates": [
                    {
                        "id": "G1",
                        "kind": "consequential_repository_write",
                        "status": "open",
                        "reason": "test reason",
                        "node": None,
                        "created_at": "2026-10-02T12:00:00Z",
                    }
                ],
                "nodes": [],
            }
        }
        items = orchestrator_items(
            lambda: runs,
            lambda run_id: statuses.get(run_id, {"gates": [], "nodes": []}),
        )
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["kind"], "orchestrator_gate")
        self.assertEqual(items[0]["id"], "gate:run1:G1")
        self.assertEqual(items[0]["tab"], "work")
        self.assertIn("run1", items[0]["context"]["run_id"])
        self.assertIn("G1", items[0]["context"]["gate_id"])

    def test_parked_nodes_become_items(self):
        """Blocked/failed nodes produce orchestrator_parked items."""
        runs = [{"run_id": "run2", "state": "BLOCKED"}]
        statuses = {
            "run2": {
                "gates": [],
                "nodes": [
                    {
                        "id": "node1",
                        "state": "FAILED_FINAL",
                        "goal": "test goal",
                        "provider": "claude",
                        "failures": [{"kind": "timeout"}],
                    }
                ],
            }
        }
        items = orchestrator_items(
            lambda: runs,
            lambda run_id: statuses.get(run_id, {"gates": [], "nodes": []}),
        )
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["kind"], "orchestrator_parked")
        self.assertEqual(items[0]["id"], "parked:run2:node1")
        self.assertEqual(items[0]["tab"], "work")
        self.assertIn("run2", items[0]["context"]["run_id"])
        self.assertIn("node1", items[0]["context"]["node_id"])

    def test_closed_gates_ignored(self):
        """Closed approval gates are not included; only open gates become items."""
        runs = [{"run_id": "run3", "state": "APPROVAL_REQUIRED"}]
        statuses = {
            "run3": {
                "gates": [
                    {
                        "id": "G1",
                        "kind": "consequential_repository_write",
                        "status": "open",
                        "reason": "test",
                        "node": None,
                    },
                    {
                        "id": "G2",
                        "kind": "consequential_repository_write",
                        "status": "approved",
                        "reason": "test",
                        "node": None,
                    }
                ],
                "nodes": [],
            }
        }
        items = orchestrator_items(
            lambda: runs,
            lambda run_id: statuses.get(run_id, {"gates": [], "nodes": []}),
        )
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["id"], "gate:run3:G1")

    def test_completed_runs_ignored(self):
        """Runs in COMPLETE state produce no items."""
        runs = [{"run_id": "run4", "state": "COMPLETE"}]
        statuses = {
            "run4": {
                "gates": [
                    {
                        "id": "G1",
                        "kind": "consequential_repository_write",
                        "status": "open",
                        "reason": "test",
                        "node": None,
                    }
                ],
                "nodes": [],
            }
        }
        items = orchestrator_items(
            lambda: runs,
            lambda run_id: statuses.get(run_id, {"gates": [], "nodes": []}),
        )
        self.assertEqual(len(items), 0)

    def test_passed_nodes_ignored(self):
        """Nodes in PASSED state are not parked items."""
        runs = [{"run_id": "run5", "state": "RUNNING"}]
        statuses = {
            "run5": {
                "gates": [],
                "nodes": [
                    {
                        "id": "node1",
                        "state": "PASSED",
                        "goal": "test goal",
                        "provider": "claude",
                    }
                ],
            }
        }
        items = orchestrator_items(
            lambda: runs,
            lambda run_id: statuses.get(run_id, {"gates": [], "nodes": []}),
        )
        self.assertEqual(len(items), 0)

    def test_multiple_gates_and_nodes(self):
        """Multiple gates and nodes in one run produce multiple items."""
        runs = [{"run_id": "run6", "state": "RUNNING"}]
        statuses = {
            "run6": {
                "gates": [
                    {
                        "id": "G1",
                        "kind": "consequential_repository_write",
                        "status": "open",
                        "reason": "test gate 1",
                        "node": None,
                    },
                    {
                        "id": "G2",
                        "kind": "agent_needs_decision",
                        "status": "open",
                        "reason": "test gate 2",
                        "node": "node1",
                    },
                ],
                "nodes": [
                    {
                        "id": "node1",
                        "state": "FAILED_FINAL",
                        "goal": "test goal",
                        "provider": "claude",
                        "failures": [{"kind": "timeout"}],
                    },
                    {
                        "id": "node2",
                        "state": "FAILED_FINAL",
                        "goal": "test goal 2",
                        "provider": "codex",
                        "failures": [{"kind": "process_error"}],
                    },
                ],
            }
        }
        items = orchestrator_items(
            lambda: runs,
            lambda run_id: statuses.get(run_id, {"gates": [], "nodes": []}),
        )
        self.assertEqual(len(items), 4)
        kinds = [item["kind"] for item in items]
        self.assertEqual(kinds.count("orchestrator_gate"), 2)
        self.assertEqual(kinds.count("orchestrator_parked"), 2)

    def test_item_has_required_fields(self):
        """Each item has id, kind, tab, title, why, source, context."""
        runs = [{"run_id": "run7", "state": "APPROVAL_REQUIRED"}]
        statuses = {
            "run7": {
                "gates": [
                    {
                        "id": "G1",
                        "kind": "consequential_repository_write",
                        "status": "open",
                        "reason": "ready to save",
                        "node": None,
                    }
                ],
                "nodes": [],
            }
        }
        items = orchestrator_items(
            lambda: runs,
            lambda run_id: statuses.get(run_id, {"gates": [], "nodes": []}),
        )
        self.assertEqual(len(items), 1)
        item = items[0]
        self.assertIn("id", item)
        self.assertIn("kind", item)
        self.assertIn("tab", item)
        self.assertIn("title", item)
        self.assertIn("why", item)
        self.assertIn("source", item)
        self.assertIn("context", item)
        self.assertEqual(item["tab"], "work")

    def test_empty_runs(self):
        """No runs produce no items."""
        items = orchestrator_items(lambda: [], lambda run_id: {"gates": [], "nodes": []})
        self.assertEqual(len(items), 0)

    def test_run_with_no_gates_or_nodes(self):
        """A running run with no gates or failed nodes produces no items."""
        runs = [{"run_id": "run8", "state": "RUNNING"}]
        statuses = {
            "run8": {
                "gates": [],
                "nodes": [
                    {"id": "node1", "state": "RUNNING", "goal": "test", "provider": "claude"}
                ],
            }
        }
        items = orchestrator_items(
            lambda: runs,
            lambda run_id: statuses.get(run_id, {"gates": [], "nodes": []}),
        )
        self.assertEqual(len(items), 0)

    def test_corrupt_run_status_skipped(self):
        """If a run's status raises (corrupt/missing), skip it and continue."""
        runs = [
            {"run_id": "run_bad", "state": "RUNNING"},
            {"run_id": "run_good", "state": "APPROVAL_REQUIRED"}
        ]
        statuses = {
            "run_good": {
                "gates": [
                    {
                        "id": "G1",
                        "kind": "consequential_repository_write",
                        "status": "open",
                        "reason": "test",
                        "node": None,
                    }
                ],
                "nodes": [],
            }
        }
        def failing_status(run_id):
            if run_id == "run_bad":
                raise ValueError("Corrupt run state")
            return statuses.get(run_id, {"gates": [], "nodes": []})

        items = orchestrator_items(
            lambda: runs,
            failing_status,
        )
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["id"], "gate:run_good:G1")

    def test_run_without_state_field(self):
        """A run missing the 'state' field is skipped using get()."""
        runs = [
            {"run_id": "run_no_state"},
            {"run_id": "run_with_state", "state": "APPROVAL_REQUIRED"}
        ]
        statuses = {
            "run_with_state": {
                "gates": [
                    {
                        "id": "G1",
                        "kind": "consequential_repository_write",
                        "status": "open",
                        "reason": "test",
                        "node": None,
                    }
                ],
                "nodes": [],
            }
        }
        items = orchestrator_items(
            lambda: runs,
            lambda run_id: statuses.get(run_id, {"gates": [], "nodes": []}),
        )
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["id"], "gate:run_with_state:G1")

    def test_cancelled_rejected_by_user_node_ignored(self):
        """A CANCELLED node with wait_reason ending in 'rejected by user' produces no item."""
        runs = [{"run_id": "run9", "state": "RUNNING"}]
        statuses = {
            "run9": {
                "gates": [
                    {
                        "id": "G1",
                        "kind": "consequential_repository_write",
                        "status": "open",
                        "reason": "test",
                        "node": None,
                    }
                ],
                "nodes": [
                    {
                        "id": "node_rejected",
                        "state": "CANCELLED",
                        "goal": "test goal",
                        "provider": "claude",
                        "wait_reason": "Dependent node cancelled due to gate rejected by user",
                    }
                ],
            }
        }
        items = orchestrator_items(
            lambda: runs,
            lambda run_id: statuses.get(run_id, {"gates": [], "nodes": []}),
        )
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["kind"], "orchestrator_gate")

    def test_cancelled_other_reason_node_included(self):
        """A CANCELLED node without 'rejected by user' in wait_reason produces an item."""
        runs = [{"run_id": "run10", "state": "RUNNING"}]
        statuses = {
            "run10": {
                "gates": [],
                "nodes": [
                    {
                        "id": "node_cancelled",
                        "state": "CANCELLED",
                        "goal": "test goal",
                        "provider": "claude",
                        "wait_reason": "Resource exhausted",
                    }
                ],
            }
        }
        items = orchestrator_items(
            lambda: runs,
            lambda run_id: statuses.get(run_id, {"gates": [], "nodes": []}),
        )
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["kind"], "orchestrator_parked")
        self.assertEqual(items[0]["id"], "parked:run10:node_cancelled")

    def test_failed_final_rejected_by_user_node_ignored(self):
        """A FAILED_FINAL node with 'rejected by user' wait_reason produces no item."""
        runs = [{"run_id": "run11", "state": "RUNNING"}]
        statuses = {
            "run11": {
                "gates": [],
                "nodes": [
                    {
                        "id": "node_failed_rejected",
                        "state": "FAILED_FINAL",
                        "goal": "test goal",
                        "provider": "claude",
                        "wait_reason": "Gate rejected by user",
                    }
                ],
            }
        }
        items = orchestrator_items(
            lambda: runs,
            lambda run_id: statuses.get(run_id, {"gates": [], "nodes": []}),
        )
        self.assertEqual(len(items), 0)

    def test_rejected_by_user_with_note_ignored(self):
        """A node with 'rejected by user: note' wait_reason is correctly filtered."""
        runs = [{"run_id": "run12", "state": "RUNNING"}]
        statuses = {
            "run12": {
                "gates": [],
                "nodes": [
                    {
                        "id": "node_rejected_with_note",
                        "state": "CANCELLED",
                        "goal": "test goal",
                        "provider": "claude",
                        "wait_reason": "rejected by user: user pressed decline",
                    }
                ],
            }
        }
        items = orchestrator_items(
            lambda: runs,
            lambda run_id: statuses.get(run_id, {"gates": [], "nodes": []}),
        )
        self.assertEqual(len(items), 0)


if __name__ == "__main__":
    unittest.main()
