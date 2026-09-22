"""Efficiency telemetry: usage normalization, the run ledger, aggregation,
avoided work, loop guards, and fail-open behaviour.

Unit tests use no engine; the integration tests drive the real engine with
synthetic workers in a throwaway repository.
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from test_orchestrator import PASS, OrchestratorFixture, edit_script  # noqa: E402

from agent_os.orchestrator import usage  # noqa: E402
from agent_os.orchestrator.adapters import synthetic  # noqa: E402
from agent_os.orchestrator.adapters.claude_code import ClaudeCodeAdapter  # noqa: E402
from agent_os.orchestrator.adapters.codex_cli import CodexCliAdapter  # noqa: E402
from agent_os.orchestrator.ledger import Ledger, describe, read_events, summarize  # noqa: E402
from agent_os.orchestrator.validators import test_counts  # noqa: E402

FAIL = {"kind": "command", "command": [sys.executable, "-c", "import sys; sys.exit(1)"]}

# Shape of a real `claude -p --output-format json` result (numbers from a live run).
CLAUDE_RESULT = {
    "type": "result", "subtype": "success", "is_error": False, "num_turns": 32, "total_cost_usd": 1.1904574,
    "result": "done\n```agent-os-result\n{\"status\": \"done\"}\n```",
    "usage": {"input_tokens": 38, "cache_creation_input_tokens": 110143, "cache_read_input_tokens": 1615447,
              "output_tokens": 42672, "output_tokens_details": {"thinking_tokens": 26560}},
}


class UsageNormalizationTests(unittest.TestCase):
    def test_claude_input_includes_cache_reads_and_writes(self) -> None:
        record = usage.from_claude(CLAUDE_RESULT)
        self.assertEqual(record["accuracy"], "exact")
        self.assertEqual(record["input_tokens"], 38 + 110143 + 1615447)
        self.assertEqual(record["uncached_input_tokens"], 38)
        self.assertEqual(record["cache_read_tokens"], 1615447)
        self.assertEqual(record["cache_write_tokens"], 110143)
        self.assertEqual(record["reasoning_tokens"], 26560)
        self.assertEqual(record["turns"], 32)
        self.assertAlmostEqual(record["cost_usd"], 1.190457, places=5)

    def test_codex_input_already_includes_cached(self) -> None:
        record = usage.from_codex_turns([{"input_tokens": 1000, "cached_input_tokens": 600, "output_tokens": 50}, {"input_tokens": 200, "cached_input_tokens": 0, "output_tokens": 10}], tool_calls=3)
        self.assertEqual(record["input_tokens"], 1200)
        self.assertEqual(record["uncached_input_tokens"], 600)
        self.assertEqual(record["cache_read_tokens"], 600)
        self.assertEqual(record["turns"], 2)
        self.assertEqual(record["tool_calls"], 3)

    def test_missing_usage_is_unavailable_not_zero(self) -> None:
        for record in (usage.from_claude({"result": "x"}), usage.from_codex_turns([]), usage.coerce(None)):
            self.assertEqual(record["accuracy"], "unavailable")
            self.assertIsNone(record["input_tokens"])
            self.assertIsNone(record["output_tokens"])

    def test_totals_only_sum_exact_usage(self) -> None:
        totals = usage.empty_totals()
        usage.add(totals, usage.normalized(total_input=100, output=10, source="t"))
        usage.add(totals, usage.normalized(total_input=999, output=99, source="t", accuracy="estimated"))
        usage.add(totals, usage.unavailable("t"))
        self.assertEqual((totals["input_tokens"], totals["output_tokens"]), (100, 10))
        self.assertEqual((totals["calls_exact"], totals["calls_estimated"], totals["calls_unavailable"]), (1, 1, 1))

    def test_adapters_parse_usage(self) -> None:
        claude = ClaudeCodeAdapter({"id": "claude-code", "executable": "claude"})
        result = claude.parse_result(None, 0, json.dumps(CLAUDE_RESULT), "")
        self.assertEqual(result.usage["input_tokens"], 1725628)
        codex = CodexCliAdapter({"id": "codex", "executable": "codex"})
        stdout = "\n".join(json.dumps(item) for item in (
            {"type": "item.completed", "item": {"type": "command_execution", "command": "ls"}},
            {"type": "item.completed", "item": {"type": "agent_message", "text": "done"}},
            {"type": "turn.completed", "usage": {"input_tokens": 5000, "cached_input_tokens": 4000, "output_tokens": 70}},
        ))

        class Handle:
            result_path = None

        parsed = codex.parse_result(Handle(), 0, stdout, "")
        self.assertEqual(parsed.usage["input_tokens"], 5000)
        self.assertEqual(parsed.usage["tool_calls"], 1)
        silent = codex.parse_result(Handle(), 0, json.dumps({"type": "item.completed", "item": {"type": "agent_message", "text": "ok"}}), "")
        self.assertEqual(silent.usage["accuracy"], "unavailable")

    def test_test_counts_from_unittest_and_pytest(self) -> None:
        self.assertEqual(test_counts("Ran 44 tests in 1s\n\nFAILED (failures=1, errors=1)"), {"tests_run": 44, "tests_failed": 2, "tests_passed": 42})
        self.assertEqual(test_counts("==== 3 passed, 1 failed in 0.2s ===="), {"tests_run": 4, "tests_failed": 1, "tests_passed": 3})
        self.assertEqual(test_counts("no tests here"), {})


class LedgerUnitTests(unittest.TestCase):
    def setUp(self) -> None:
        import tempfile
        import shutil

        self.tmp = Path(tempfile.mkdtemp(prefix="agent-os-ledger-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.ledger = Ledger(lambda run_id: self.tmp / run_id)

    def test_events_keep_run_id_order_and_transcript(self) -> None:
        for kind in ("run_started", "model_started", "model_completed", "run_completed"):
            self.ledger.emit("r1", kind, "n", provider="codex", usage=usage.normalized(total_input=10, output=2, source="codex"))
        events, malformed = self.ledger.read("r1")
        self.assertEqual(malformed, 0)
        self.assertEqual([event["type"] for event in events], ["run_started", "model_started", "model_completed", "run_completed"])
        self.assertEqual({event["run_id"] for event in events}, {"r1"})
        transcript = (self.tmp / "r1" / "transcript.log").read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(transcript), 4)
        self.assertIn("Codex finished", transcript[2])

    def test_aggregation_keeps_accuracy_separate(self) -> None:
        exact = usage.normalized(total_input=1000, cache_read=800, output=100, source="claude-code", cost_usd=0.5)
        estimated = usage.normalized(total_input=50, output=5, source="x", accuracy="estimated")
        self.ledger.emit("r", "model_completed", "a", provider="claude-code", capability_class="reasoning", role="implementer", usage=exact, prompt_tokens_estimate=100)
        self.ledger.emit("r", "model_completed", "b", provider="codex", capability_class="fast", role="implementer", usage=estimated)
        self.ledger.emit("r", "model_failed", "c", provider="codex", capability_class="fast", role="reviewer", usage=usage.unavailable("codex"))
        report = summarize(self.ledger.read("r")[0])
        self.assertEqual(report["model_calls"]["total"], 3)
        self.assertEqual(report["model_calls"]["failed"], 1)
        self.assertEqual(report["model_calls"]["expensive"], 1)
        self.assertEqual(report["tokens"]["exact"]["input"], 1000)
        self.assertEqual(report["tokens"]["exact"]["cache_read"], 800)
        self.assertEqual(report["tokens"]["estimated"]["input"], 50)
        self.assertEqual(report["tokens"]["unavailable_calls"], 1)
        self.assertEqual(report["tokens"]["provider_reported_cost_usd"], 0.5)
        self.assertEqual(report["prompt_vs_actual"]["agent_overhead_tokens_estimate"], 900)

    def test_avoided_tokens_only_counted_with_an_estimate(self) -> None:
        self.ledger.emit("r", "work_avoided", category="cache", model_calls_avoided=1, tokens_avoided_estimate=None)
        self.ledger.emit("r", "work_avoided", category="resume", model_calls_avoided=1, tokens_avoided_estimate=5000)
        report = summarize(self.ledger.read("r")[0])
        self.assertEqual(report["avoided"]["model_calls"], 2)
        self.assertEqual(report["avoided"]["tokens_estimate"], 5000)
        self.assertEqual(report["avoided"]["estimated_events"], 1)

    def test_malformed_lines_are_skipped_and_counted(self) -> None:
        self.ledger.emit("r", "run_started")
        path = self.tmp / "r" / "telemetry.jsonl"
        with path.open("a", encoding="utf-8") as handle:
            handle.write("{not json\n")
            handle.write(json.dumps({"schema": "other", "data": {}}) + "\n")
            handle.write(json.dumps([1, 2]) + "\n")
        self.ledger.emit("r", "run_completed")
        events, malformed = read_events(path)
        self.assertEqual([event["type"] for event in events], ["run_started", "run_completed"])
        self.assertEqual(malformed, 3)
        self.assertEqual(summarize(events, malformed)["malformed_lines"], 3)

    def test_write_failure_fails_open_with_warning(self) -> None:
        self.ledger.fail_writes = True
        self.assertIsNone(self.ledger.emit("r", "run_started"))
        self.assertIsNone(self.ledger.emit("r", "not_a_real_type"))
        self.assertIn("2 telemetry record(s)", self.ledger.warning("r"))

    def test_private_fields_are_dropped(self) -> None:
        record = self.ledger.emit("r", "note", text="api_key=sk-abcdefghijklmnop1234", prompt="secret prompt", transcript="x")
        self.assertNotIn("prompt", record["data"])
        self.assertNotIn("transcript", record["data"])
        self.assertNotIn("sk-abcdefghijklmnop1234", json.dumps(record))

    def test_describe_is_plain_english(self) -> None:
        line = describe({"type": "tests_completed", "node": "impl", "data": {"tests_run": 44, "tests_passed": 42, "passed": False}})
        self.assertEqual(line, "42 of 44 tests passed (impl)")


class EngineTelemetryTests(OrchestratorFixture):
    def events(self, run_id: str) -> list[dict]:
        return self.engine.ledger.read(run_id)[0]

    def types(self, run_id: str) -> list[str]:
        return [event["type"] for event in self.events(run_id)]

    def test_run_records_ordered_events_and_reconciles(self) -> None:
        run_id = self.create([self.task("a")])
        self.engine.start(run_id)
        final = self.engine.run_loop(run_id, max_ticks=40)
        self.assertEqual(final["state"], "COMPLETE")
        types = self.types(run_id)
        order = [types.index(kind) for kind in ("run_started", "routing_decision", "model_started", "model_completed", "checkpoint_created", "tests_started", "tests_completed", "review_started", "review_completed", "commit_created", "run_completed")]
        self.assertEqual(order, sorted(order), types)
        self.assertEqual({event["run_id"] for event in self.events(run_id)}, {run_id})
        report = self.engine.efficiency(run_id)
        self.assertTrue(report["reconciliation"]["consistent"], report["reconciliation"])
        self.assertEqual(report["model_calls"]["total"], 2)
        self.assertEqual(report["model_calls"]["roles"], {"implementer": 1, "reviewer": 1})
        self.assertEqual(report["tokens"]["synthetic"]["calls"], 2)
        self.assertEqual(report["tokens"]["exact"]["calls"], 0, "synthetic usage is never counted as provider-measured")
        self.assertTrue(Path(report["files"]["transcript"]).exists())

    def test_model_calls_are_attributed_to_provider_and_role(self) -> None:
        run_id = self.create([self.task("a")])
        self.engine.start(run_id)
        self.engine.run_loop(run_id, max_ticks=40)
        completed = [event for event in self.events(run_id) if event["type"] == "model_completed"]
        by_role = {event["data"]["role"]: event["data"]["provider"] for event in completed}
        self.assertNotEqual(by_role["implementer"], by_role["reviewer"], "cross-review uses the other provider")
        decision = next(event for event in self.events(run_id) if event["type"] == "routing_decision")
        self.assertIn("planned as", decision["data"]["reason"])
        self.assertEqual(decision["data"]["tier"], "stronger model")

    def test_missing_provider_usage_does_not_crash(self) -> None:
        synthetic.SCRIPTS["alpha"] = edit_script({"a": {"usage": None}})
        run_id = self.create([self.task("a")])
        self.engine.start(run_id)
        self.assertEqual(self.engine.run_loop(run_id, max_ticks=40)["state"], "COMPLETE")
        node = self.node(run_id, "a")
        self.assertEqual(node["result"]["usage"]["accuracy"], "unavailable")
        self.assertEqual(self.engine.efficiency(run_id)["tokens"]["unavailable_calls"], 1)

    def test_escalation_and_retries_are_recorded(self) -> None:
        attempts = {"n": 0}

        def flaky(request, call):
            if request.role == "reviewer":
                return {"structured": {"status": "done", "verdict": "approved", "findings": []}}
            attempts["n"] += 1
            if attempts["n"] == 1:
                return {"failure": "process_error"}
            content = "bad\n" if attempts["n"] == 2 else "good\n"
            return {"edits": {"a/out.txt": content}, "structured": {"status": "done"}}

        synthetic.SCRIPTS["alpha"] = synthetic.SCRIPTS["beta"] = flaky
        check = {"kind": "command", "command": [sys.executable, "-c", "import sys; sys.exit(0 if open('a/out.txt').read()=='good\\n' else 1)"]}
        run_id = self.create([self.task("a", validators=[check])])
        self.engine.start(run_id)
        self.assertEqual(self.engine.run_loop(run_id, max_ticks=60)["state"], "COMPLETE")
        report = self.engine.efficiency(run_id)
        self.assertEqual(report["counts"]["retries"], 1)
        self.assertEqual(report["counts"]["escalations"], 1)
        escalation = next(event for event in self.events(run_id) if event["type"] == "model_escalated")
        self.assertEqual(escalation["data"]["reason"], "its tests failed")
        self.assertEqual(report["tests"]["failed_runs"], 1)

    def test_identical_code_reuses_test_results(self) -> None:
        run_id = self.create([self.task("a")], completion_validators=[PASS])
        self.engine.start(run_id)
        self.engine.run_loop(run_id, max_ticks=40)
        report = self.engine.efficiency(run_id)
        # The integration branch has the node's exact tree, so the completion
        # check reuses the node's result instead of running tests again.
        self.assertEqual(report["counts"]["cache_hits"], 1)
        self.assertEqual(report["tests"]["reused"], 1)
        self.assertIn("validation_cache", report["avoided"]["reasons"])

    def test_reuse_can_be_disabled(self) -> None:
        run_id = self.create([self.task("a")], completion_validators=[PASS], reuse_validation=False)
        self.engine.start(run_id)
        self.engine.run_loop(run_id, max_ticks=40)
        self.assertEqual(self.engine.efficiency(run_id)["counts"]["cache_hits"], 0)

    def test_unchanged_code_after_failure_trips_loop_guard(self) -> None:
        synthetic.SCRIPTS["alpha"] = synthetic.SCRIPTS["beta"] = edit_script({"a": {"edits": {"a/same.txt": "same\n"}}})
        run_id = self.create([self.task("a", validators=[FAIL])], max_escalations=1)
        self.engine.start(run_id)
        self.assertEqual(self.engine.run_loop(run_id, max_ticks=40)["state"], "BLOCKED")
        guards = [event["data"]["guard"] for event in self.events(run_id) if event["type"] == "loop_guard"]
        self.assertIn("unchanged_code_retest", guards)
        self.assertIn("escalation_limit", guards)
        report = self.engine.efficiency(run_id)
        self.assertEqual(report["tests"]["runs"], 1, "identical failing code is tested once")

    def test_no_change_worker_skips_review(self) -> None:
        synthetic.SCRIPTS["alpha"] = synthetic.SCRIPTS["beta"] = edit_script({"a": {"edits": {}}})
        run_id = self.create([self.task("a")])
        self.engine.start(run_id)
        self.assertEqual(self.engine.run_loop(run_id, max_ticks=40)["state"], "COMPLETE")
        self.assertNotIn("review_started", self.types(run_id))
        report = self.engine.efficiency(run_id)
        self.assertEqual(report["avoided"]["model_calls"], 1)
        self.assertEqual(report["avoided"]["tokens_estimate"], 0, "no measured review cost: no token claim")

    def test_deterministic_step_records_local_execution(self) -> None:
        task = {"id": "det", "goal": "run a command", "scope": ["a"], "execution_path": "deterministic", "command": [sys.executable, "-c", "open('a/x.txt','w').write('x')"], "validators": [PASS]}
        run_id = self.create([task])
        self.engine.start(run_id)
        self.assertEqual(self.engine.run_loop(run_id, max_ticks=40)["state"], "COMPLETE")
        report = self.engine.efficiency(run_id)
        self.assertEqual(report["model_calls"]["total"], 0)
        self.assertGreaterEqual(report["counts"]["local_operations"], 1)
        self.assertEqual(report["avoided"]["reasons"].get("deterministic"), 1)

    def test_telemetry_failure_never_breaks_the_run(self) -> None:
        self.engine.ledger.fail_writes = True
        run_id = self.create([self.task("a")])
        self.engine.start(run_id)
        final = self.engine.run_loop(run_id, max_ticks=40)
        self.assertEqual(final["state"], "COMPLETE")
        self.assertIn("could not be written", final["telemetry_warning"])

    def test_nested_repository_is_not_its_parent_project(self) -> None:
        from agent_os.paths import ROOT

        nested = ROOT / ".agent-local" / "tmp-nested-repo-test"
        self.addCleanup(__import__("shutil").rmtree, nested, True)
        nested.mkdir(parents=True, exist_ok=True)
        __import__("subprocess").run(["git", "init", "-q"], cwd=nested, check=True)
        self.assertIsNone(self.engine._resolve_target(nested, None)[0])
        self.assertEqual(self.engine._resolve_target(ROOT / "src", None)[0], "personal-agent-os")

    def test_context_selection_is_recorded_for_registered_projects(self) -> None:
        run_id = self.engine.create_run("goal", repository=self.repo, project="personal-agent-os", tasks=[self.task("a")], policy=self.policy(default_validators=[PASS]))["run_id"]
        self.engine.start(run_id)
        self.engine.run_loop(run_id, max_ticks=40)
        selected = [event for event in self.events(run_id) if event["type"] == "context_selected"]
        self.assertTrue(selected)
        data = selected[0]["data"]
        self.assertGreater(data["candidate_tokens_estimate"], data["selected_tokens_estimate"])
        self.assertGreater(data["candidate_items"], data["selected_items"])
        self.assertIsNotNone(self.engine.efficiency(run_id)["context"]["reduction_pct"])


if __name__ == "__main__":
    unittest.main()
