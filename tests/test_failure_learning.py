"""Every model failure is recorded, and unremedied or recurring ones become an
improvement and a fix run (policy failure_learning)."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from agent_os.orchestrator import failure_learning as fl  # noqa: E402
from agent_os.orchestrator.adapters import synthetic  # noqa: E402
from agent_os.orchestrator.model import DEFAULT_POLICY  # noqa: E402
from test_orchestrator import OrchestratorFixture  # noqa: E402


def node(node_id, **extra):
    base = {"id": node_id, "role": "implementer", "failures": [], "selection": {"provider": "claude-code", "model": "sonnet"},
            "result": None, "integration": None, "review": {}, "escalations": 0, "state": "PASSED", "attempts": 1}
    base.update(extra)
    return base


def record(run_id="r1", nodes=(), gates=()):
    return {"run_id": run_id, "nodes": {item["id"]: item for item in nodes}, "gates": list(gates), "policy": dict(DEFAULT_POLICY)}


class SignatureTests(unittest.TestCase):
    def test_failures_are_normalised(self) -> None:
        excerpt = "FAILED tests/t.py::T::test_x\nE   AssertionError: 4 != 5"
        rec = record(nodes=[
            node("a", failures=[{"kind": "validator_failed", "detail": "unit=FAIL", "excerpt": excerpt},
                                {"kind": "validator_failed", "detail": "unit=FAIL", "excerpt": excerpt},
                                {"kind": "quota", "detail": "limit"}]),
            node("b", failures=[{"kind": "validator_failed", "detail": "editable-scope=FAIL (edits outside declared scope: x)"}]),
            node("c", result={"signals": {"denied_commands": ["python -c 'print(1)'", "cd x && ls"]}}),
            node("d", integration={"deferred": True, "reason": "needs a restart"}, review={"oscillation": True}, escalations=1),
            node("e", state="FAILED_FINAL", failures=[{"kind": "stuck", "detail": "looping"}]),
            node("f", state="FAILED_FINAL", wait_reason="no provider: no usable provider covers balanced"),
        ], gates=[{"id": "G1", "kind": "unresolved_review_findings", "node": "d", "reason": "2 findings"}])
        found = sorted(item["signature"] for item in fl.signatures(rec))
        self.assertEqual(found, sorted([
            "validator_failed:AssertionError", "validator_failed:unchanged", "scope_violation",
            "permission_denied:python -c", "permission_denied:cd x",
            "blocked_on_host:deferred", "review_oscillation", "escalated:implementer",
            "stuck", "failed_final:stuck", "unroutable", "review_unresolved",
        ]))

    def test_remedies_match_by_prefix(self) -> None:
        self.assertIn("failure_excerpt", fl.remedy_for("validator_failed:ImportError"))
        self.assertIn("did not change", fl.remedy_for("validator_failed:unchanged"))
        self.assertIsNone(fl.remedy_for("stuck"))
        self.assertIn("changed nothing", fl.remedy_for("blocked_on_host:deferred"))
        self.assertIsNone(fl.remedy_for("refused_twice"))


class LearnTests(unittest.TestCase):
    def setUp(self) -> None:
        self.home = Path(tempfile.mkdtemp())

    def test_learning_is_idempotent_and_unremedied_failures_need_improvement(self) -> None:
        rec = record(nodes=[node("a", failures=[{"kind": "stuck", "detail": "looping on ls"}])])
        first = fl.learn(self.home, rec)
        self.assertEqual(first["recorded"], 1)
        self.assertEqual([item["signature"] for item in first["needs_improvement"]], ["stuck"])
        again = fl.learn(self.home, rec)
        self.assertEqual((again["recorded"], again["needs_improvement"]), (0, []))

    def test_remedied_failures_escalate_only_when_they_recur_across_runs(self) -> None:
        failing = [{"kind": "validator_failed", "detail": "unit=FAIL", "excerpt": "E   ImportError: x"}]
        once = fl.learn(self.home, record("r1", [node("a", failures=failing)]))
        self.assertEqual(once["needs_improvement"], [])
        twice = fl.learn(self.home, record("r2", [node("a", failures=failing)]))
        self.assertEqual([item["signature"] for item in twice["needs_improvement"]], ["validator_failed:ImportError"])
        fields = fl.improvement_fields(twice["needs_improvement"][0])
        self.assertEqual(fields["dedupe_key"], "failure-signature:validator_failed:ImportError")
        self.assertIn("although a remedy exists", fields["observation"])

    def test_evidence_drops_long_identifiers(self) -> None:
        fields = fl.improvement_fields({"signature": "unroutable", "remedy": None, "runs": 1, "occurrences": 1,
                                        "examples": ["r/n (local): worktree /tmp/wt/af03a901deadbeefcafe0123456789ab failed"]})
        self.assertNotIn("af03a901deadbeefcafe0123456789ab", fields["evidence"][0])

    def test_daily_limit_and_active_fix_runs_block_new_fix_runs(self) -> None:
        self.assertIsNone(fl.fix_run_allowed(self.home, "stuck", daily_limit=1, active_runs=[]))
        fl.note_fix_run(self.home, "stuck", "fix-1", "IMP-1")
        self.assertIn("daily limit", fl.fix_run_allowed(self.home, "other", daily_limit=1, active_runs=[]))
        self.assertIn("still active", fl.fix_run_allowed(self.home, "stuck", daily_limit=5, active_runs=["fix-1"]))


class EngineFailureLearningTests(OrchestratorFixture):
    def stuck_run(self, **policy) -> str:
        def script(request, call):
            if request.role == "reviewer":
                return {"structured": {"status": "done", "verdict": "approved", "findings": []}}
            if call == 1:
                return {"failure": "stuck", "detail": "looping on the same ls command"}
            return {"edits": {f"{request.node_id}/done.txt": "x\n"}, "structured": {"status": "done"}}

        synthetic.reset()  # call numbers restart, so each run's first call fails
        for name in self.providers:
            synthetic.SCRIPTS[name] = script
        run_id = self.create([self.task("a")], **policy)
        self.engine.run_loop(run_id, max_ticks=60)
        return run_id

    def test_embedded_engine_records_signatures_without_side_effects(self) -> None:
        self.stuck_run()
        rows = fl._read(fl.ledger_path(self.engine.store.home))
        self.assertIn("stuck", [row["signature"] for row in rows])
        self.assertEqual(self.engine.failure_hooks, {"improve": None, "launch": None})

    def test_unremedied_failure_files_an_improvement_and_starts_one_fix_run(self) -> None:
        improvements, launches = [], []
        self.engine.failure_hooks = {
            "improve": lambda need: improvements.append(need["signature"]) or {"id": f"IMP-{len(improvements)}"},
            "launch": lambda parent, need, imp: launches.append((need["signature"], imp)) or f"fix-{len(launches)}",
        }
        run_id = self.stuck_run()
        self.assertIn("stuck", improvements)
        self.assertIn(("stuck", improvements and f"IMP-{improvements.index('stuck') + 1}"), launches)
        events = (self.engine.store.run_dir(run_id) / "events.jsonl").read_text(encoding="utf-8")
        self.assertIn("failure_learning.fix_run", events)

    def test_record_and_improve_modes_and_fix_runs_never_start_fix_runs(self) -> None:
        launches, improvements = [], []
        self.engine.failure_hooks = {"improve": lambda need: improvements.append(need) or {"id": "IMP-1"},
                                     "launch": lambda *a: launches.append(a) or "fix-x"}
        self.stuck_run(failure_learning="record")
        self.assertEqual((launches, improvements), ([], []))
        self.stuck_run(failure_learning="improve")
        self.assertEqual(launches, [])
        self.assertTrue(improvements)
        # A fix run that fails files its improvement but never starts another fix run.
        self.stuck_run(failure_learning="record")  # re-arms the scripted first-call failure
        synthetic.reset()
        for name in self.providers:
            synthetic.SCRIPTS[name] = lambda request, call: ({"failure": "stuck", "detail": "loop"} if call == 1 else
                                                             {"edits": {f"{request.node_id}/f.txt": "x\n"}, "structured": {"status": "done", "verdict": "approved", "findings": []}})
        before = len(improvements)
        run_id = self.engine.create_run("fix goal", repository=self.repo, tasks=[self.task("a")], policy=self.policy(),
                                        origin={"type": "failure_learning", "signature": "stuck"})["run_id"]
        self.engine.run_loop(run_id, max_ticks=60)
        self.assertGreater(len(improvements), before)  # the fix run's own failure was still filed
        self.assertEqual(launches, [])

    def test_a_rejected_improvement_does_not_stop_the_others(self) -> None:
        filed = []

        def improve(need):
            if need["signature"] == "stuck":
                raise ValueError("improvement rejected by privacy gate: long_identifier")
            filed.append(need["signature"])
            return {"id": "IMP-9"}

        self.engine.failure_hooks = {"improve": improve, "launch": None}
        run_id = self.stuck_run()
        report = self.engine._learn_failures(run_id)  # already learned: nothing new
        self.assertEqual(report["recorded"], 0)
        events = (self.engine.store.run_dir(run_id) / "events.jsonl").read_text(encoding="utf-8")
        self.assertNotIn("failure_learning.error", events)

    def test_policy_defaults(self) -> None:
        self.assertEqual(DEFAULT_POLICY["failure_learning"], "fix")
        self.assertEqual(DEFAULT_POLICY["failure_learning_daily_fix_runs"], 3)
        self.assertEqual(DEFAULT_POLICY["failure_learning_fix_max_usd"], 5.0)


if __name__ == "__main__":
    unittest.main()
