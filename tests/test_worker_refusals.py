"""Model refusals are tracked and routed around.

Claude Code reports stop_reason "refusal" and safety_stops in its JSON result;
the adapter used to drop both, so a refusal looked like an ordinary bad answer,
was retried on the same model, and refusals.jsonl stayed empty (only the
one-off ``delegate`` path recorded anything).
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from agent_os.orchestrator import refusal  # noqa: E402
from agent_os.orchestrator.adapters import synthetic  # noqa: E402
from agent_os.orchestrator.adapters.claude_code import ClaudeCodeAdapter, result_signals  # noqa: E402
from test_orchestrator import OrchestratorFixture  # noqa: E402

PROVIDER = {"id": "claude-code", "adapter": "claude_code", "executable": "claude", "options": {}}


def payload(**extra) -> str:
    return json.dumps({"type": "result", "subtype": "success", "is_error": False, "result": "ok", "num_turns": 3,
                       "usage": {"input_tokens": 10, "output_tokens": 5}, **extra})


class ClaudeCodeSignalTests(unittest.TestCase):
    def test_refusal_stop_reason_is_a_refused_failure(self) -> None:
        adapter = ClaudeCodeAdapter(PROVIDER)
        result = adapter.parse_result(None, 0, payload(stop_reason="refusal", result="I can't help with that."), "")
        self.assertEqual((result.outcome, result.failure_kind), ("failed", "refused"))
        self.assertEqual(result.signals["stop_reason"], "refusal")

    def test_safety_stop_is_a_refused_failure(self) -> None:
        result = ClaudeCodeAdapter(PROVIDER).parse_result(None, 0, payload(stop_reason="end_turn", safety_stops=[{"kind": "x"}]), "")
        self.assertEqual(result.failure_kind, "refused")

    def test_completed_result_carries_denial_counts(self) -> None:
        denials = [{"tool_name": "Bash", "tool_input": {"command": "python -m pytest"}}, {"tool_name": "Bash", "tool_input": {}}]
        result = ClaudeCodeAdapter(PROVIDER).parse_result(None, 0, payload(stop_reason="end_turn", permission_denials=denials), "")
        self.assertEqual(result.outcome, "completed")
        self.assertEqual(result.signals["permission_denials"], 2)
        self.assertEqual(result.signals["denied_tools"], {"Bash": 2})
        self.assertEqual(result.signals["denied_commands"], ["python -m pytest"])

    def test_signals_tolerate_missing_fields(self) -> None:
        self.assertEqual(result_signals({}), {"stop_reason": None, "safety_stops": 0, "permission_denials": 0, "denied_tools": {}, "denied_commands": []})


class RefusalRoutingTests(OrchestratorFixture):
    def test_refusal_is_recorded_and_the_node_routes_elsewhere(self) -> None:
        def refuses(request, call):
            if request.role == "reviewer":
                return {"structured": {"status": "done", "verdict": "approved", "findings": []}}
            return {"failure": "refused", "detail": "I can't help with that request."}

        def works(request, call):
            if request.role == "reviewer":
                return {"structured": {"status": "done", "verdict": "approved", "findings": []}}
            return {"edits": {f"{request.node_id}/done.txt": "x\n"}, "structured": {"status": "done"}}

        synthetic.SCRIPTS["alpha"], synthetic.SCRIPTS["beta"] = refuses, works
        run_id = self.create([self.task("a")])
        final = self.engine.run_loop(run_id, max_ticks=60)
        self.assertEqual(final["state"], "COMPLETE", final["state_reason"])
        node = self.node(run_id, "a")
        refused = [item for item in node["failures"] if item["kind"] == "refused"]
        self.assertTrue(refused)
        self.assertIn(refused[0]["capability_class"], node["excluded_classes"].get("alpha", []))
        events = refusal.load(self.engine.store.home)
        self.assertEqual([(event["category"], event["provider"]) for event in events][:1], [("provider_policy", "alpha")])
        self.assertEqual(refusal.summary(self.engine.store.home)["routes"][f"alpha/{events[0]['model']}"]["total"], len(events))

    def test_a_plain_bad_answer_is_not_recorded_as_a_refusal(self) -> None:
        self.engine._record_refusal({"run_id": "r"}, {"id": "n", "role": "implementer", "selection": {}, "attempts": 1}, "worker_failure", "wrong")
        self.assertEqual(refusal.load(self.engine.store.home), [])


if __name__ == "__main__":
    unittest.main()
