"""Simple Mode swarm, task progress, updates and chat views (pure functions)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.orchestrator import simple  # noqa: E402


def node(node_id, role, state, **extra):
    return {"id": node_id, "role": role, "state": state, "goal": f"goal of {node_id}", "integrated": False, "attempts": 1, **extra}


RUN = {
    "nodes": [
        node("plan", "planner", "PASSED"),
        node("a", "implementer", "RUNNING", provider="codex", model="gpt-6-luna", provider_effort="low", started_at="2026-09-30T10:00:00+00:00"),
        node("b", "implementer", "VALIDATING", provider="claude-code", model="sonnet", attempts=2),
        node("c", "test_author", "PASSED", integrated=True, model="haiku"),
        node("d", "implementer", "FAILED_FINAL"),
        node("a.review", "reviewer", "RUNNING", provider="codex", model="gpt-6-luna"),
    ],
    "gates": [
        {"id": "G1", "kind": "agent_needs_decision", "node": "d", "reason": "Should the lock be per run or per repository?", "status": "open", "created_at": "2026-09-30T10:05:00+00:00"},
        {"id": "G2", "kind": "agent_needs_decision", "node": "a", "reason": "Keep the old flag?", "status": "approved", "created_at": "2026-09-30T09:00:00+00:00",
         "decided_at": "2026-09-30T09:01:00+00:00", "note": "yes, keep it"},
        {"id": "G3", "kind": "policy_restricted_action", "node": "c", "reason": "no validator", "status": "open", "created_at": "2026-09-30T10:06:00+00:00"},
    ],
    "operator_messages": [{"at": "2026-09-30T09:30:00+00:00", "text": "keep it small"}],
}


class SwarmChatTests(unittest.TestCase):
    def test_swarm_lists_active_agents_and_counts_models(self) -> None:
        swarm = simple.swarm_view(RUN)
        self.assertEqual(swarm["running"], 3)
        self.assertEqual(swarm["by_model"].get("Codex gpt-6-luna"), 2)
        self.assertEqual(sum(swarm["by_model"].values()), 3)
        doing = {agent["task"]: (agent["doing"], agent["phase"]) for agent in swarm["agents"]}
        self.assertEqual(doing["a"], ("writing code", "working"))
        self.assertEqual(doing["b"], ("writing code", "running the tests"))
        self.assertEqual(doing["a.review"], ("reviewing a change", "working"))

    def test_task_progress_reflects_state(self) -> None:
        rows = {row["task"]: row for row in simple.task_list(RUN)}
        self.assertEqual(set(rows), {"a", "b", "c", "d"})  # planner and reviewer are not tasks
        self.assertEqual(rows["c"]["progress"], 100)
        self.assertEqual(rows["c"]["status"], "merged")
        self.assertLess(rows["a"]["progress"], rows["b"]["progress"])
        self.assertTrue(rows["d"]["failed"])

    def test_chat_has_questions_answers_and_messages_in_order(self) -> None:
        chat = simple.chat_view(RUN)
        self.assertEqual([(item["from"], item["text"][:12]) for item in chat],
                         [("agent", "Keep the old"), ("you", "yes, keep it"), ("you", "keep it smal"), ("agent", "Should the l")])
        self.assertTrue(chat[-1]["open"])
        self.assertEqual(chat[-1]["gate_id"], "G1")

    def test_updates_are_milestones_newest_first(self) -> None:
        events = [{"at": "t1", "type": "worker.launched", "node": "a", "detail": "implementer via codex"},
                  {"at": "t2", "type": "worktree.created", "node": "a", "detail": "branch"},
                  {"at": "t3", "type": "gate.opened", "node": "d", "detail": "G1 agent_needs_decision: which lock?"}]
        updates = simple.updates_view(events)
        self.assertEqual([item["type"] for item in updates], ["gate.opened", "worker.launched"])
        self.assertTrue(updates[0]["needs_you"])


if __name__ == "__main__":
    unittest.main()
