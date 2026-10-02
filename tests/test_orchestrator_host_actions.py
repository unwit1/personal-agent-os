"""Host-level prerequisites never stall a run on a person.

A sandboxed worker cannot restart the MCP server or drive a nested run. Asking
through an approval gate only relaunched the same worker, which asked again, so
the orchestrator now defers such steps and the MCP server reloads edited code.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from agent_os.orchestrator.adapters import synthetic
from agent_os.orchestrator.engine import _host_action
from agent_os.orchestrator.roadmap import relevant_items
from test_orchestrator import OrchestratorFixture


def host_blocked_script(status: str, question: str):
    def script(request, call):
        if request.role == "reviewer":
            return {"structured": {"status": "done", "verdict": "approved", "findings": []}}
        if request.node_id == "verify":
            return {"structured": {"status": status, "summary": question, "question": question}}
        return {"edits": {f"{request.node_id}/done.txt": "x\n"}, "structured": {"status": "done"}}

    return script


class HostActionTests(OrchestratorFixture):
    def run_blocked(self, status: str, question: str) -> dict:
        for name in self.providers:
            synthetic.SCRIPTS[name] = host_blocked_script(status, question)
        run_id = self.create([self.task("verify", scope=["a"]), self.task("impl", depends_on=["verify"])])
        final = self.engine.run_loop(run_id, max_ticks=40)
        self.assertEqual(final["state"], "COMPLETE", final["state_reason"])
        self.assertEqual(final["gates"], [])
        record = self.engine.load(run_id)
        self.assertTrue(record["nodes"]["verify"]["integration"]["deferred"])
        self.assertIn("impl", record["integration"]["merged"])
        return record

    def test_blocked_on_host_is_deferred_without_a_gate(self) -> None:
        record = self.run_blocked("blocked_on_host", "needs a client restart")
        self.assertEqual(record["deferred_host_actions"][0]["node"], "verify")
        # Once the host is fixed, the deferred step can run again (nothing was merged).
        retried = self.engine.retry(record["run_id"], "verify")
        node = next(item for item in retried["nodes"] if item["id"] == "verify")
        self.assertEqual(node["state"], "FAILED_RETRYABLE")
        self.assertFalse(self.engine.load(record["run_id"]).get("deferred_host_actions"))

    def test_host_level_needs_decision_is_deferred_without_a_gate(self) -> None:
        self.run_blocked("needs_decision", "Can the Agent OS MCP server be restarted from its owning host?")

    def test_deferred_step_with_unmerged_work_holds_its_dependents(self) -> None:
        question = "needs a client restart"

        def script(request, call):
            if request.role == "reviewer":
                return {"structured": {"status": "done", "verdict": "approved", "findings": []}}
            if request.node_id == "verify":
                return {"edits": {"a/api.py": "def api():\n    return 1\n"},
                        "structured": {"status": "blocked_on_host", "summary": question, "question": question}}
            return {"edits": {f"{request.node_id}/done.txt": "x\n"}, "structured": {"status": "done"}}

        for name in self.providers:
            synthetic.SCRIPTS[name] = script
        run_id = self.create([self.task("verify", scope=["a"]), self.task("impl", depends_on=["verify"])])
        self.engine.run_loop(run_id, max_ticks=40)
        record = self.engine.load(run_id)
        verify = record["nodes"]["verify"]
        self.assertTrue(verify["integration"]["deferred"])
        self.assertIn("a/api.py", verify["integration"]["unmerged_files"])
        self.assertNotIn("impl", record["integration"]["merged"])
        self.assertIn("deferred host action on verify", record["nodes"]["impl"]["wait_reason"])

    def test_design_questions_still_open_a_gate(self) -> None:
        self.assertFalse(_host_action("keep the v1 API?"))
        self.assertTrue(_host_action("Restart the Agent OS MCP server before expecting clients to use the fix"))


class BaselineValidationTests(OrchestratorFixture):
    """A project suite that already fails on main must not fail every worker."""

    def suite(self, extra_failure: bool) -> dict:
        # Fails "t.flaky" everywhere; also fails "t.broken" once a worker adds a file beside a/.keep.
        code = (
            "import os,sys;"
            "print('FAIL: test_flaky (t.flaky)');"
            + ("print('FAIL: test_broken (t.broken)') if len(os.listdir('a')) > 1 else None;" if extra_failure else "")
            + "sys.exit(1)"
        )
        return {"kind": "command", "command": [sys.executable, "-c", code], "name": "project-validation-1"}

    def test_pre_existing_failures_are_excused(self) -> None:
        run_id = self.create([self.task("a", validators=[self.suite(False)])], require_independent_review_for_model_edits=False)
        final = self.engine.run_loop(run_id, max_ticks=40)
        self.assertEqual(final["state"], "COMPLETE", final["state_reason"])
        record = self.engine.load(run_id)
        self.assertEqual(list(record["validation_baseline"].values()), [["t.flaky"]])

    def test_planned_copy_of_the_project_suite_uses_the_same_baseline(self) -> None:
        planned = dict(self.suite(False), name="planned-1")
        project_command = " ".join(planned["command"]) + " -v"
        with mock.patch("agent_os.orchestrator.engine._project_commands", return_value=[project_command]):
            run_id = self.create([self.task("a", validators=[planned])], require_independent_review_for_model_edits=False)
            final = self.engine.run_loop(run_id, max_ticks=40)
        self.assertEqual(final["state"], "COMPLETE", final["state_reason"])

    def test_task_specific_validator_must_still_pass_outright(self) -> None:
        planned = dict(self.suite(False), name="planned-1")
        with mock.patch("agent_os.orchestrator.engine._project_commands", return_value=["python -m unittest discover -s tests"]):
            run_id = self.create([self.task("a", validators=[planned])], require_independent_review_for_model_edits=False)
            final = self.engine.run_loop(run_id, max_ticks=40)
        self.assertNotEqual(final["state"], "COMPLETE")

    def test_cached_failure_from_before_itemizing_is_rerun(self) -> None:
        run_id = self.create([self.task("a", validators=[self.suite(False)])], require_independent_review_for_model_edits=False)
        record = self.engine.load(run_id)
        node = record["nodes"]["a"]
        legacy = {"name": "project-validation-1", "kind": "command", "passed": False, "returncode": 1}
        with mock.patch("agent_os.orchestrator.engine._tree_hash", return_value="t" * 40):
            from agent_os.orchestrator.engine import _validation_key

            record["validation_cache"] = {_validation_key("t" * 40, [self.suite(False)]): {"evidence": [legacy], "declared_validators": 1, "passed": False, "at": "then"}}
            validation = self.engine._validate(record, node, [self.suite(False)], self.repo)
        self.assertTrue(validation["passed"], validation)
        self.assertNotIn("reused", validation)

    def test_new_failures_still_fail(self) -> None:
        run_id = self.create([self.task("a", validators=[self.suite(True)])], require_independent_review_for_model_edits=False)
        self.engine.run_loop(run_id, max_ticks=40)
        node = self.engine.load(run_id)["nodes"]["a"]
        self.assertNotEqual(node["state"], "PASSED")


class ReviewEscalationTests(OrchestratorFixture):
    def test_stronger_reviewer_settles_before_a_person_is_asked(self) -> None:
        def script(request, call):
            if request.role == "reviewer":
                if request.capability_class == "reasoning":
                    return {"structured": {"status": "done", "verdict": "approved", "findings": []}}
                finding = {"id": "F1", "severity": "medium", "summary": "looks out of scope", "path": "a"}
                return {"structured": {"status": "done", "verdict": "changes_requested", "findings": [finding]}}
            return {"edits": {f"a/{request.node_id}-{call}.txt": "x\n"}, "structured": {"status": "done"}}

        for name in self.providers:
            synthetic.SCRIPTS[name] = script
        run_id = self.create([self.task("a")])
        final = self.engine.run_loop(run_id, max_ticks=80)
        self.assertEqual(final["state"], "COMPLETE", final["state_reason"])
        self.assertEqual(final["gates"], [])
        node = self.engine.load(run_id)["nodes"]["a"]
        self.assertTrue(node["review"]["escalated"])

    def test_confirmed_findings_get_one_last_repair_before_a_person(self) -> None:
        # Seen live: the stronger reviewer confirmed a concrete doc error and
        # the run asked a person although nobody had been asked to fix it.
        state = {"fixed": False, "repairs": 0}

        def script(request, call):
            if request.role == "repairer":
                state["repairs"] += 1
                if state["repairs"] >= 2:  # ordinary repairs fail; only the final one succeeds
                    state["fixed"] = True
                return {"edits": {f"a/fix-{call}.txt": "x\n"}, "structured": {"status": "done", "dispositions": [{"id": "F1", "disposition": "fixed"}]}}
            if request.role == "reviewer":
                if state["fixed"]:
                    return {"structured": {"status": "done", "verdict": "approved", "findings": []}}
                finding = {"id": "F1", "severity": "medium", "summary": "wrong field in the table", "path": "a", "recommended_action": "use the source field"}
                return {"structured": {"status": "done", "verdict": "changes_requested", "findings": [finding]}}
            return {"edits": {f"a/{request.node_id}-{call}.txt": "x\n"}, "structured": {"status": "done"}}

        for name in self.providers:
            synthetic.SCRIPTS[name] = script
        run_id = self.create([self.task("a")])
        final = self.engine.run_loop(run_id, max_ticks=120)
        node = self.engine.load(run_id)["nodes"]["a"]
        self.assertTrue(node["review"]["escalated"])
        self.assertTrue(node["review"].get("final_repair"))
        self.assertEqual(final["gates"], [], "the last repair settled it without a person")
        self.assertEqual(final["state"], "COMPLETE", final["state_reason"])


class QuotaCooldownTests(unittest.TestCase):
    def test_reset_time_is_read_from_the_quota_message(self) -> None:
        from datetime import datetime, timedelta, timezone

        from agent_os.orchestrator.engine import _quota_reset

        now = datetime.now(timezone.utc).astimezone().replace(hour=12, minute=0, second=0, microsecond=0)
        reset = datetime.fromisoformat(_quota_reset("You've hit your usage limit ... try again at 1:50 PM.", now))
        self.assertEqual(reset - now, timedelta(hours=1, minutes=50))
        later = datetime.fromisoformat(_quota_reset("try again at 11:00 AM", now))
        self.assertEqual(later - now, timedelta(hours=23))
        # Seen live: at 18:50:24 Codex still said "try again at 6:50 PM"; that
        # is the window flipping over, not a reset 24 hours away.
        flipping = now.replace(hour=18, minute=50, second=24)
        soon = datetime.fromisoformat(_quota_reset("try again at 6:50 PM.", flipping))
        self.assertEqual(soon - flipping, timedelta(minutes=5))
        self.assertEqual(datetime.fromisoformat(_quota_reset("limit reached", now)) - now, timedelta(hours=1))

    def test_cooling_provider_is_unavailable_until_reset(self) -> None:
        import tempfile
        from datetime import datetime, timedelta, timezone

        from agent_os.orchestrator import engine

        home = Path(tempfile.mkdtemp())
        until = (datetime.now(timezone.utc) + timedelta(minutes=30)).isoformat()
        engine._write_cooldown(home, "codex", until, "quota")
        self.assertEqual(engine._cooling_providers(home), {"codex"})
        self.assertEqual(engine._cooling_providers(home, datetime.now(timezone.utc) + timedelta(hours=1)), set())


class UnavailableModelTests(unittest.TestCase):
    def test_unavailable_model_drops_the_tier(self) -> None:
        from agent_os.orchestrator.router import normalize_provider

        raw = {"id": "claude-code", "discover": True, "models": {"frontier": "fable", "reasoning": "opus"}, "unavailable_models": ["fable"]}
        provider = normalize_provider(raw, 0, discovered={"frontier": "fable", "reasoning": "opus"})
        self.assertEqual(provider["models"], {"reasoning": "opus"})


class RetryPromptTests(unittest.TestCase):
    def test_failed_validation_forbids_already_done(self) -> None:
        from agent_os.orchestrator.engine import _prior_attempts

        node = {"failures": [{"kind": "validator_failed", "detail": "broken by this change: t.x"}]}
        self.assertIn("Do not report already_done", _prior_attempts(node))
        node = {"failures": [{"kind": "timeout", "detail": "slow"}]}
        self.assertNotIn("already_done", _prior_attempts(node))


class PlannerScopeTests(unittest.TestCase):
    def test_validator_test_file_joins_the_scope(self) -> None:
        from agent_os.orchestrator.planner import _scope_validator_tests

        cases = {
            "tests.test_connector_registry": "tests/test_connector_registry.py",
            "tests.test_orchestrator.RoutingTests.test_x": "tests/test_orchestrator.py",
            "tests/test_mail.py::Cls::test_y": "tests/test_mail.py",
        }
        for token, path in cases.items():
            task = {"id": "t", "scope": ["src/agent_os"], "validators": [{"command": ["python", "-m", "unittest", token]}]}
            _scope_validator_tests(task)
            self.assertEqual(task["scope"], ["src/agent_os", path], token)
        task = {"id": "t", "scope": ["src"], "validators": [{"command": ["python", "-m", "unittest", "discover", "-s", "tests"]}]}
        _scope_validator_tests(task)
        self.assertEqual(task["scope"], ["src"])


class RoadmapHandoffTests(unittest.TestCase):
    def test_host_chores_are_not_planned(self) -> None:
        stage = {"id": "P0.3", "title": "Document cache", "excerpt": "cache"}
        items = ["Run P0.3 cache regressions. P0.0A G1 still needs the owning MCP host restart and exact-model smoke."]
        self.assertEqual(relevant_items(stage, items), ["Run P0.3 cache regressions."])
        self.assertEqual(relevant_items(stage, ["P0.3: restart the MCP server."]), [])


class McpReloadTests(unittest.TestCase):
    def test_reload_serves_fresh_code(self) -> None:
        from agent_os import mcp_server

        saved = dict(sys.modules)
        self.addCleanup(lambda: (sys.modules.clear(), sys.modules.update(saved)))
        handle, available = mcp_server._reload()
        self.assertIsNot(handle, mcp_server._handle_mcp)
        self.assertIn("orchestrate.status", available)



class NewFindingsAfterFinalRepairTests(OrchestratorFixture):
    def test_findings_new_after_the_final_repair_get_one_more_repair(self) -> None:
        # Seen live: round 4 raised real bugs no worker had been asked to fix,
        # and the run sat on a gate for two hours.
        state = {"repairs": 0}

        def script(request, call):
            if request.role == "repairer":
                state["repairs"] += 1
                return {"edits": {f"a/fix-{state['repairs']}.txt": "x"}, "structured": {"status": "done"}}
            if request.role == "reviewer":
                if state["repairs"] >= 3:  # the extra repair fixed it
                    return {"structured": {"status": "done", "verdict": "approved", "findings": []}}
                finding = {"id": f"bug{state['repairs']}", "severity": "high", "summary": f"new bug {state['repairs']}", "path": "a"}
                return {"structured": {"status": "done", "verdict": "changes_requested", "findings": [finding]}}
            return {"edits": {f"a/{request.node_id}-{call}.txt": "x"}, "structured": {"status": "done"}}

        for name in self.providers:
            synthetic.SCRIPTS[name] = script
        run_id = self.create([self.task("a")])
        final = self.engine.run_loop(run_id, max_ticks=160)
        node = self.engine.load(run_id)["nodes"]["a"]
        self.assertTrue(node["review"].get("final_repair"))
        self.assertTrue(node["review"].get("extra_repair"))
        self.assertEqual(final["gates"], [])
        self.assertEqual(final["state"], "COMPLETE", final["state_reason"])

    def test_the_extra_repair_happens_once(self) -> None:
        def script(request, call):
            if request.role == "reviewer":
                finding = {"id": f"bug{call}", "severity": "high", "summary": f"bug {call}", "path": "a"}
                return {"structured": {"status": "done", "verdict": "changes_requested", "findings": [finding]}}
            return {"edits": {f"a/{request.node_id}-{call}.txt": "x"}, "structured": {"status": "done"}}

        for name in self.providers:
            synthetic.SCRIPTS[name] = script
        run_id = self.create([self.task("a")])
        final = self.engine.run_loop(run_id, max_ticks=160)
        self.assertEqual(final["state"], "APPROVAL_REQUIRED")
        self.assertEqual(len([g for g in final["gates"] if g["status"] == "open"]), 1)


class WaitForCheaperResetTests(OrchestratorFixture):
    """H6 (Hermes min_switch_reset_seconds): a cheap provider that resets soon
    is waited for instead of failing over to a costlier one."""

    def registry(self):
        from agent_os.orchestrator.router import ProviderRegistry
        from test_orchestrator import provider

        cheap = {"fast": 0.03, "balanced": 0.03, "reasoning": 0.03, "frontier": 0.03}
        dear = {"fast": 1.0, "balanced": 1.0, "reasoning": 1.0, "frontier": 1.0}
        return ProviderRegistry(providers=[provider("alpha", costs=cheap), provider("beta", costs=dear)])

    def cool_alpha(self, minutes: float) -> None:
        from datetime import datetime, timedelta, timezone

        from agent_os.orchestrator import engine as engine_mod

        until = (datetime.now(timezone.utc) + timedelta(minutes=minutes)).isoformat(timespec="seconds")
        engine_mod._write_cooldown(self.engine.store.home, "alpha", until, "quota: test")

    def first_launch(self, run_id: str) -> dict:
        self.engine.start(run_id)
        for _ in range(3):
            self.engine.step(run_id)
        return self.engine.load(run_id)["nodes"]["a"]

    def test_waits_when_the_cheaper_provider_resets_soon(self) -> None:
        self.cool_alpha(2)
        node = self.first_launch(self.create([self.task("a")]))
        self.assertEqual(node["state"], "RUNNABLE")
        self.assertIn("waiting for usage reset: alpha", node["wait_reason"])

    def test_fails_over_when_the_reset_is_far(self) -> None:
        self.cool_alpha(120)
        node = self.first_launch(self.create([self.task("a")]))
        self.assertEqual((node.get("selection") or {}).get("provider"), "beta")

    def test_zero_turns_waiting_off(self) -> None:
        self.cool_alpha(2)
        node = self.first_launch(self.create([self.task("a")], wait_for_reset_seconds=0))
        self.assertEqual((node.get("selection") or {}).get("provider"), "beta")


if __name__ == "__main__":
    unittest.main()
