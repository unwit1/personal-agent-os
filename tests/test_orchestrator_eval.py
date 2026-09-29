"""`agent-os orchestrate eval` (IMP-0003): trusted suites, separate dimensions,
noninferiority verdicts, holdout refusal, append-only EVR records."""

from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from agent_os.orchestrator import capability  # noqa: E402
from agent_os.orchestrator import eval as evaluation  # noqa: E402
from agent_os.orchestrator.adapters import synthetic  # noqa: E402
from agent_os.orchestrator.router import ProviderRegistry  # noqa: E402
from agent_os.orchestrator.store import HOME_ENV  # noqa: E402


class ParseAndCompareTests(unittest.TestCase):
    def test_parse_unittest(self) -> None:
        out = "FAIL: test_a (tests.x.T.test_a)\nERROR: test_b (tests.x.T.test_b)\n----\nRan 10 tests in 1.5s\n\nFAILED (failures=1, errors=1, skipped=2)\n"
        parsed = evaluation.parse_unittest(out, 1)
        self.assertEqual((parsed["tests_run"], parsed["passed"], parsed["failures"], parsed["errors"], parsed["skipped"]), (10, 6, 1, 1, 2))
        self.assertEqual(len(parsed["failing"]), 2)
        crashed = evaluation.parse_unittest("ImportError: nope", 1)
        self.assertEqual((crashed["tests_run"], crashed["errors"], crashed["pass_rate"]), (0, 1, 0.0))

    def test_dimensions_stay_separate_and_verdicts(self) -> None:
        incumbent = {"ref": "a", "accuracy": 0.75, "contract_pass": True, "cost_usd": 0.20, "seconds": 100, "input_tokens": 400000}
        cheaper_same = {"ref": "b", "accuracy": 0.76, "contract_pass": True, "cost_usd": 0.05, "seconds": 20, "input_tokens": 30000}
        dims = evaluation.compare("cases", incumbent, cheaper_same, 0.02)
        self.assertEqual(dims["accuracy"]["verdict"], "noninferior")
        self.assertEqual(dims["cost_usd"]["verdict"], "improved")
        self.assertEqual(evaluation.primary_verdict("cases", dims), "noninferior")
        worse = evaluation.compare("cases", incumbent, {**cheaper_same, "accuracy": 0.6}, 0.02)
        # Cheaper does not rescue a quality regression: no blended score.
        self.assertEqual(evaluation.primary_verdict("cases", worse), "regressed")

    def test_new_failing_test_is_a_regression_even_at_equal_pass_rate(self) -> None:
        a = {"ref": "a", "pass_rate": 0.9, "failures": 1, "errors": 0, "tests_run": 10, "seconds": 1, "failing": ["x"]}
        b = {"ref": "b", "pass_rate": 0.9, "failures": 1, "errors": 0, "tests_run": 10, "seconds": 1, "failing": ["y"]}
        dims = evaluation.compare("tests", a, b, 0.02)
        self.assertEqual(evaluation.primary_verdict("tests", dims), "regressed")

    def test_score_cases(self) -> None:
        cases = [{"input_ref": "A", "expected_status": "partial"}, {"input_ref": "B", "expected_status": "missing"}]
        score = evaluation.score_cases({"items": [{"id": "A", "status": "partial"}, {"id": "B", "status": "partial"}]}, cases)
        self.assertEqual((score["correct"], score["accuracy"]), (1, 0.5))
        self.assertEqual(score["wrong"], [{"id": "B", "expected": "missing", "got": "partial"}])

    def test_route_parsing(self) -> None:
        self.assertEqual(evaluation.parse_route("codex:gpt-6-luna@fast"), {"spec": "codex:gpt-6-luna@fast", "provider": "codex", "model": "gpt-6-luna", "capability_class": "fast"})
        self.assertEqual(evaluation.parse_route("claude-code")["model"], None)


class GovernanceTests(unittest.TestCase):
    def test_holdout_requires_operator_flag(self) -> None:
        suite = {"id": "EVS-X", "type": "EVS", "metrics": {"splits": ["protected_holdout"], "runners": []}}
        with self.assertRaises(evaluation.EvalError):
            evaluation.check_holdout(suite, [], operator_holdout=False)
        evaluation.check_holdout(suite, [], operator_holdout=True)
        by_path = {"id": "EVS-Y", "type": "EVS", "metrics": {"splits": ["development"], "runners": ["projects/personal-agent-os/orchestrator-os/evals/holdout/cases.json"]}}
        with self.assertRaises(evaluation.EvalError):
            evaluation.check_holdout(by_path, [], operator_holdout=False)
        with self.assertRaises(evaluation.EvalError):
            evaluation.check_holdout({"metrics": {}}, [{"split": "rolling_private"}], operator_holdout=False)

    def test_suites_come_from_the_trusted_checkout(self) -> None:
        self.assertEqual(evaluation.SUITES, ROOT / "projects" / "personal-agent-os" / "orchestrator-os" / "evals" / "suites")
        self.assertEqual(evaluation.load_suite("EVS-CONTROL-PLANE")["id"], "EVS-CONTROL-PLANE")
        with self.assertRaises(evaluation.EvalError):
            evaluation.load_suite("EVS-DOES-NOT-EXIST")

    def test_evr_records_are_append_only_and_numbered(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            self.assertEqual(evaluation.next_evr_id(directory), "EVR-0001")
            (directory / "EVR-0007.json").write_text("{}", encoding="utf-8")
            self.assertEqual(evaluation.next_evr_id(directory), "EVR-0008")
            with self.assertRaises(evaluation.EvalError):
                evaluation.write_evr({"id": "EVR-0007"}, directory)

    def test_evr_shape(self) -> None:
        suite = {"id": "EVS-CAPABILITY-CLASSIFICATION", "type": "EVS", "metrics": {"task_families": ["f"]}}
        results = [{"ref": "a", "accuracy": 0.7, "contract_pass": True, "cost_usd": 0.1, "seconds": 10, "input_tokens": 1}, {"ref": "b", "accuracy": 0.8, "contract_pass": True, "cost_usd": 0.1, "seconds": 10, "input_tokens": 1}]
        record = evaluation.build_evr(suite, "cases", results, "a", 0.02, "EVR-0100", [])
        self.assertEqual(record["outcome"], "improved")
        self.assertEqual(record["metrics"]["comparisons"]["b"]["verdict"], "improved")
        from agent_os.orchestrator.evidence import validate_record
        self.assertEqual(validate_record(record, "evr"), [])


class RunnerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.previous = os.environ.get(HOME_ENV)
        os.environ[HOME_ENV] = self.tmp.name
        synthetic.reset()

    def tearDown(self) -> None:
        synthetic.reset()
        if self.previous is None:
            os.environ.pop(HOME_ENV, None)
        else:
            os.environ[HOME_ENV] = self.previous
        self.tmp.cleanup()

    def test_test_runner_uses_trusted_copy_in_a_detached_worktree(self) -> None:
        result = evaluation.run_tests_for_ref("HEAD", ["tests/test_timestamps.py"])
        self.assertGreater(result["tests_run"], 0)
        self.assertEqual(result["failures"] + result["errors"], 0, result["failing"])
        self.assertEqual(list((Path(self.tmp.name) / "eval-worktrees").glob("*")), [])  # cleaned up

    def test_case_route_scores_accuracy_and_records_it(self) -> None:
        case_file = json.loads((ROOT / "projects/personal-agent-os/orchestrator-os/evals/cases/development/research-implementation-classification.json").read_text(encoding="utf-8"))
        labels = {case["input_ref"]: case["expected_status"] for case in case_file["cases"]}
        answers = dict(labels)
        answers["MIE-0001"] = "missing" if labels["MIE-0001"] != "missing" else "partial"
        synthetic.SCRIPTS["eval-test"] = lambda request, call: {"structured": {"items": [{"id": key, "status": value, "evidence": []} for key, value in answers.items()]}}
        registry = ProviderRegistry(providers=[{"id": "syn", "adapter": "synthetic", "options": {"script": "eval-test"}, "models": {"fast": "syn-fast"}}])
        result = evaluation.run_cases_for_route(evaluation.parse_route("syn"), case_file, Path(self.tmp.name), floor=0.9, registry=registry)
        self.assertEqual((result["correct"], result["accuracy"]), (19, 0.95))
        observation = capability.read_observations()[-1]
        self.assertEqual(observation["accuracy"], 0.95)
        self.assertTrue(observation["validator_passed"])
        self.assertEqual(capability.summarize([observation])[0]["metrics"]["mean_accuracy"], 0.95)


if __name__ == "__main__":
    unittest.main()
