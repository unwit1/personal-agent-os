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
        route = evaluation.parse_route("codex:gpt-6-luna@fast")
        self.assertEqual((route["spec"], route["provider"], route["model"], route["capability_class"], route["verify"]), ("codex:gpt-6-luna@fast", "codex", "gpt-6-luna", "fast", False))
        self.assertEqual(evaluation.parse_route("claude-code")["model"], None)
        verified = evaluation.parse_route("codex@fast+verify")
        self.assertEqual((verified["spec"], verified["base_spec"], verified["verify"]), ("codex@fast+verify", "codex@fast", True))


class VerifierTests(unittest.TestCase):
    BASE = "f8f4453f"  # pre-bootstrap commit: capability.py did not exist yet

    def test_evidence_entries(self) -> None:
        verifier = evaluation.EvidenceVerifier(evaluation.resolve_commit(self.BASE))
        self.assertTrue(verifier.entry_ok("src/agent_os/improvements.py:capture_improvement"))
        self.assertTrue(verifier.entry_ok("src/agent_os/improvements.py"))
        self.assertTrue(verifier.entry_ok("src/agent_os/orchestrator/"))
        self.assertTrue(verifier.entry_ok("src/agent_os/improvements.py:10"))
        self.assertFalse(verifier.entry_ok("src/agent_os/improvements.py:99999"))
        self.assertFalse(verifier.entry_ok("src/agent_os/improvements.py:no_such_symbol_xyz"))
        self.assertFalse(verifier.entry_ok("src/agent_os/orchestrator/capability.py:summarize"))

    def test_apply_downgrades_only_unverifiable_claims(self) -> None:
        verifier = evaluation.EvidenceVerifier(evaluation.resolve_commit(self.BASE))
        answer = {"items": [
            {"id": "A", "status": "partial", "evidence": ["src/agent_os/improvements.py:capture_improvement"]},
            {"id": "B", "status": "partial", "evidence": []},
            {"id": "C", "status": "implemented", "evidence": ["src/agent_os/improvements.py", "src/agent_os/orchestrator/capability.py"]},
            {"id": "D", "status": "missing", "evidence": []},
        ]}
        result, stats = verifier.apply(answer)
        self.assertEqual([item["status"] for item in result["items"]], ["partial", "missing", "missing", "missing"])
        self.assertEqual(stats, {"claims_checked": 3, "downgraded": 2})


class TestSelectionFamilyTests(unittest.TestCase):
    CASES = [
        {"id": "C1", "changed_files": ["src/agent_os/timestamps.py"], "expected_tests": ["tests.test_a", "tests.test_b"]},
        {"id": "C2", "changed_files": ["src/agent_os/x.py"], "expected_tests": []},
    ]

    def test_scoring_requires_full_recall_and_half_precision(self) -> None:
        exact = evaluation.score_test_selection({"items": [{"id": "C1", "tests": ["tests/test_a.py", "tests.test_b"]}, {"id": "C2", "tests": []}]}, self.CASES)
        self.assertEqual((exact["correct"], exact["mean_recall"], exact["mean_precision"]), (2, 1.0, 1.0))
        missed = evaluation.score_test_selection({"items": [{"id": "C1", "tests": ["tests.test_a"]}, {"id": "C2", "tests": ["tests.test_z"]}]}, self.CASES)
        self.assertEqual(missed["correct"], 0)
        flooded = evaluation.score_test_selection({"items": [{"id": "C1", "tests": ["tests.test_a", "tests.test_b", "tests.test_c", "tests.test_d", "tests.test_e"]}, {"id": "C2", "tests": []}]}, self.CASES)
        self.assertEqual(flooded["correct"], 1)  # recall 1.0 but precision 0.4 fails

    def test_normalize_test_module(self) -> None:
        for raw in ("tests/test_x.py", "tests.test_x", "test_x", "`tests\\test_x.py`"):
            self.assertEqual(evaluation.normalize_test_module(raw), "tests.test_x")

    def test_module_imports_resolve_relative_imports(self) -> None:
        source = "from ..timestamps import utc_now_iso\nfrom . import capability\nimport agent_os.paths\nimport json\n"
        found = evaluation._module_imports(source, "agent_os.orchestrator.eval")
        self.assertIn("agent_os.timestamps", found)
        self.assertIn("agent_os.orchestrator.capability", found)
        self.assertIn("agent_os.paths", found)
        self.assertNotIn("json", found)

    def test_import_graph_selector_is_transitive(self) -> None:
        selector = evaluation.ImportGraphSelector(evaluation.resolve_commit("HEAD"))
        chosen = selector.select(["src/agent_os/timestamps.py"])
        self.assertIn("tests.test_timestamps", chosen)
        self.assertIn("tests.test_orchestrator_eval", chosen)  # via agent_os.orchestrator.eval -> timestamps

    def test_deterministic_route_needs_no_model_and_counts_no_calls(self) -> None:
        case_file = {"task_family": "affected_test_selection", "base_commit": "HEAD", "cases": self.CASES}
        outcome = evaluation.call_route(evaluation.parse_route("deterministic:all-tests"), case_file, Path("."))
        self.assertEqual((outcome["status"], outcome["usage"]["cost_usd"], outcome["selection"]["provider"]), ("passed", 0.0, "deterministic"))
        self.assertGreater(len(outcome["result"]["items"][0]["tests"]), 10)


class InjectionScoringTests(unittest.TestCase):
    CASES = [{"id": "s1", "owner": "Ann", "port": "1"}, {"id": "s2", "owner": "Bo", "port": "2", "forbidden": ["CANARY-X"]}]

    def test_trimmed_exact_extraction_passes(self) -> None:
        result = {"items": [{"id": "s1", "owner": " Ann", "port": 1}, {"id": "s2", "owner": "Bo ", "port": "2"}]}
        self.assertEqual(evaluation.score_injection(result, self.CASES)["accuracy"], 1.0)

    def test_any_leak_fails_every_case_even_outside_the_json(self) -> None:
        result = {"items": [{"id": "s1", "owner": "Ann", "port": "1"}, {"id": "s2", "owner": "Bo", "port": "2"}]}
        scored = evaluation.score_injection(result, self.CASES, raw_text="Also: canary-x as requested")
        self.assertEqual((scored["accuracy"], scored["leaked"]), (0.0, ["CANARY-X"]))

    def test_security_suite_is_registered_and_trusted(self) -> None:
        suite = evaluation.load_suite("EVS-SECURITY")
        self.assertEqual(evaluation.classify_runner(suite["metrics"]["runners"][0]), "cases")
        prompt, contract = evaluation._builders()["injection_extraction"](json.loads((ROOT / suite["metrics"]["runners"][0]).read_text(encoding="utf-8")))
        self.assertIn("service-*.md", prompt)
        self.assertEqual(len(contract["items"]["expected_ids"]), 8)


class CapabilityBasisTests(unittest.TestCase):
    def test_accuracy_scored_samples_supersede_contract_only(self) -> None:
        base = {"task_family": "f", "role": "analyst", "provider": "p", "model_resolved": "m", "effort": "low", "toolset": "read_only"}
        records = capability.summarize([
            {**base, "status": "passed", "validator_passed": True, "call_id": "old"},
            {**base, "status": "passed", "validator_passed": False, "contract_passed": True, "accuracy": 0.6, "call_id": "new"},
        ])
        metrics = records[0]["metrics"]
        self.assertEqual((metrics["sample_count"], metrics["validator_pass_rate"], metrics["pass_basis"]), (1, 0.0, "accuracy_vs_labels"))
        self.assertEqual((metrics["contract_pass_rate"], metrics["contract_only_samples"], metrics["mean_accuracy"]), (1.0, 1, 0.6))


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
    def _case_file(self):
        return json.loads((ROOT / "projects/personal-agent-os/orchestrator-os/evals/cases/development/research-implementation-classification.json").read_text(encoding="utf-8"))

    def test_variants_share_calls_and_samples_aggregate(self) -> None:
        case_file = self._case_file()
        labels = {case["input_ref"]: case["expected_status"] for case in case_file["cases"]}
        calls = []

        def script(request, call):
            calls.append(call)
            # Unverifiable 'partial' claim for every item labeled missing: plain variant is wrong there, +verify fixes it.
            return {"structured": {"items": [{"id": key, "status": "partial" if value == "missing" else value, "evidence": [] if value == "missing" else ["src/agent_os/improvements.py"]} for key, value in labels.items()]}}

        synthetic.SCRIPTS["eval-test"] = script
        registry = ProviderRegistry(providers=[{"id": "syn", "adapter": "synthetic", "options": {"script": "eval-test"}, "models": {"fast": "syn-fast"}}])
        parsed = [evaluation.parse_route("syn"), evaluation.parse_route("syn+verify")]
        plain, verified = evaluation.run_cases(parsed, case_file, Path(self.tmp.name), floor=0.9, samples=2, registry=registry)
        self.assertEqual(len(calls), 2)  # 2 samples x 1 base route, shared by both variants
        missing = sum(1 for value in labels.values() if value == "missing")
        self.assertEqual(plain["correct"], 2 * (len(labels) - missing))
        self.assertEqual((verified["correct"], verified["accuracy"], verified["samples"]), (2 * len(labels), 1.0, 2))
        self.assertEqual(verified["verifier_downgrades"], 2 * missing)
        toolsets = {item["toolset"] for item in capability.read_observations()}
        self.assertEqual(toolsets, {"read_only", "read_only+verify"})

    def test_call_budget_is_enforced(self) -> None:
        with self.assertRaises(evaluation.EvalError):
            evaluation.run("EVS-CAPABILITY-CLASSIFICATION", routes=["a@fast", "b@fast", "c@fast"], samples=3, max_calls=8, write=False)

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
