"""Orchestrator OS foundations: control-plane guard, delegate, capability
evidence, continuation checkpoints, and evidence-record validation."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
import unittest.mock
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from agent_os.orchestrator import capability, continuation, control_plane, evidence  # noqa: E402
from agent_os.orchestrator.adapters import synthetic  # noqa: E402
from agent_os.orchestrator.delegate import check_contract, delegate  # noqa: E402
from agent_os.orchestrator.engine import _control_plane  # noqa: E402
from agent_os.orchestrator.model import PolicyError, merge_policy  # noqa: E402
from agent_os.orchestrator.router import ProviderRegistry  # noqa: E402
from agent_os.orchestrator.validators import run_all  # noqa: E402


class ControlPlaneTests(unittest.TestCase):
    def test_protected_paths_are_blocked(self) -> None:
        changed = ["policy/orchestrator-os.policy.json", "projects/personal-agent-os/orchestrator-os/evals/holdout/case.json", "src/agent_os/cli.py"]
        self.assertEqual(control_plane.protected_changes(changed), changed[:2])
        self.assertFalse(control_plane.check(changed)["passed"])

    # Tests below kill mutants that survived the first mutation run (DEC-0012).
    def test_missing_or_corrupt_policy_file_falls_back_to_floor(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "absent.json"
            corrupt = Path(tmp) / "corrupt.json"
            corrupt.write_text("{not json", encoding="utf-8")
            listed = Path(tmp) / "list.json"
            listed.write_text("[1, 2]", encoding="utf-8")
            for path in (missing, corrupt, listed):
                self.assertEqual(control_plane.load_policy(path), {})
            with unittest.mock.patch.object(control_plane, "POLICY_PATH", missing):
                self.assertEqual(set(control_plane.protected_globs()), set(control_plane.FLOOR))
                self.assertFalse(control_plane.check(["policy/anything.json"])["passed"])

    def test_directory_glob_matches_the_directory_itself(self) -> None:
        self.assertTrue(control_plane._match("policy", "policy/**"))
        self.assertFalse(control_plane._match("policyx", "policy/**"))

    def test_unresolvable_repository_fails_closed(self) -> None:
        with unittest.mock.patch.object(control_plane.Path, "resolve", side_effect=OSError("boom")):
            self.assertTrue(control_plane.applies_to("/some/where", None))

    def test_check_detail_names_hits_and_truncates(self) -> None:
        self.assertIsNone(control_plane.check(["src/agent_os/cli.py"])["detail"])
        many = [f"policy/p{index}.json" for index in range(12)]
        detail = control_plane.check(many)["detail"]
        self.assertIn("policy/p0.json", detail)
        self.assertIn("policy/p9.json", detail)
        self.assertNotIn("policy/p10.json", detail)

    def test_path_normalization(self) -> None:
        self.assertEqual(control_plane.protected_changes(["./policy/a.json", "policy\\b.json"]), ["./policy/a.json", "policy\\b.json"])
        self.assertEqual(control_plane.protected_changes([".github/policy/x", "policyx/a"]), [])

    def test_operator_grant_allows_only_the_granted_path(self) -> None:
        changed = ["policy/orchestrator-os.policy.json", "src/agent_os/orchestrator/validators.py"]
        self.assertEqual(control_plane.protected_changes(changed, ["policy/orchestrator-os.policy.json"]), ["src/agent_os/orchestrator/validators.py"])

    def test_floor_survives_a_weakened_or_missing_policy(self) -> None:
        # A candidate that empties protected_paths (or deletes the policy) still
        # cannot touch the floor.
        for policy in ({}, {"control_plane": {"protected_paths": []}}):
            hits = control_plane.protected_changes(["policy/orchestrator-os.policy.json", "src/agent_os/orchestrator/control_plane.py"], policy=policy)
            self.assertEqual(len(hits), 2)

    def test_policy_is_read_from_trusted_checkout_not_worktree(self) -> None:
        self.assertEqual(control_plane.POLICY_PATH, ROOT / "policy" / "orchestrator-os.policy.json")
        with tempfile.TemporaryDirectory() as tmp:
            # A tampered policy inside some worktree has no effect on the check.
            (Path(tmp) / "policy").mkdir()
            (Path(tmp) / "policy" / "orchestrator-os.policy.json").write_text("{}", encoding="utf-8")
            self.assertFalse(control_plane.check(["projects/personal-agent-os/orchestrator-os/evals/suites/EVS-ROUTING.json"])["passed"])

    def test_validator_step_includes_control_plane_only_when_enabled(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            enabled = run_all([], tmp, changed=["policy/x.json"], scope=[], control_plane={"allowed": []})
            self.assertFalse(enabled["passed"])
            self.assertIn("control-plane", [item["name"] for item in enabled["evidence"]])
            self.assertEqual(enabled["declared_validators"], 0)
            disabled = run_all([], tmp, changed=["policy/x.json"], scope=[])
            self.assertNotIn("control-plane", [item["name"] for item in disabled["evidence"]])

    def test_engine_enables_guard_for_this_repository_only(self) -> None:
        policy = merge_policy()
        self.assertIsNotNone(_control_plane({"project": "personal-agent-os", "repository": "/elsewhere", "policy": policy}))
        self.assertIsNotNone(_control_plane({"project": None, "repository": str(ROOT), "policy": policy}))
        self.assertIsNone(_control_plane({"project": "hr-gui", "repository": tempfile.gettempdir(), "policy": policy}))
        granted = merge_policy({"protected_paths_allowed": ["policy/**"]})
        self.assertEqual(_control_plane({"project": "personal-agent-os", "repository": "", "policy": granted})["allowed"], ["policy/**"])

    def test_grant_must_be_a_list_of_strings(self) -> None:
        with self.assertRaises(PolicyError):
            merge_policy({"protected_paths_allowed": "policy/**"})


class DelegateTests(unittest.TestCase):
    CONTRACT = {"required": {"items": "array"}, "items": {"min_items": 2, "expected_ids": ["A", "B"], "required": {"id": "string", "status": "string"}, "enums": {"status": ["yes", "no"]}}}

    def setUp(self) -> None:
        synthetic.reset()
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name)
        self.registry = ProviderRegistry(providers=[
            {"id": "cheap", "adapter": "synthetic", "options": {"script": "delegate-test"}, "models": {"fast": "cheap-fast", "balanced": "cheap-balanced"}, "costs": {"fast": 1, "balanced": 3}},
        ])

    def tearDown(self) -> None:
        synthetic.reset()
        self.tmp.cleanup()

    def test_contract_checks(self) -> None:
        self.assertEqual(check_contract({"items": [{"id": "A", "status": "yes"}, {"id": "B", "status": "no"}]}, self.CONTRACT), [])
        errors = check_contract({"items": [{"id": "A", "status": "maybe"}]}, self.CONTRACT)
        self.assertTrue(any("at least 2" in item for item in errors))
        self.assertTrue(any("not in" in item for item in errors))
        self.assertTrue(any("missing ids: B" in item for item in errors))
        self.assertEqual(check_contract(None, self.CONTRACT), ["no JSON object in output"])

    def test_delegate_routes_read_only_validates_and_records(self) -> None:
        seen = {}

        def script(request, call):
            seen["read_only"] = request.read_only
            return {"structured": {"items": [{"id": "A", "status": "yes"}, {"id": "B", "status": "no"}]}, "usage": {"input_tokens": 50, "output_tokens": 5}}

        synthetic.SCRIPTS["delegate-test"] = script
        outcome = delegate("classify", task_family="unit_classification", contract=self.CONTRACT, registry=self.registry, home=self.home, cwd=self.home)
        self.assertEqual(outcome["status"], "passed", outcome.get("errors"))
        self.assertTrue(seen["read_only"])
        self.assertEqual(outcome["selection"]["model"], "cheap-fast")
        observations = capability.read_observations(self.home)
        self.assertEqual(len(observations), 1)
        self.assertTrue(observations[0]["validator_passed"])
        self.assertNotIn("classify", json.dumps(observations))  # no prompt text in evidence

    def test_contract_failure_is_recorded_not_raised(self) -> None:
        synthetic.SCRIPTS["delegate-test"] = lambda request, call: {"structured": {"items": []}}
        outcome = delegate("classify", task_family="unit_classification", contract=self.CONTRACT, registry=self.registry, home=self.home, cwd=self.home)
        self.assertEqual(outcome["status"], "contract_failed")
        self.assertFalse(capability.read_observations(self.home)[0]["validator_passed"])


class CapabilityTests(unittest.TestCase):
    def test_wilson_and_qualification(self) -> None:
        low, high = capability.wilson(20, 20)
        self.assertGreater(low, 0.8)
        self.assertEqual(high, 1.0)
        self.assertEqual(capability.wilson(0, 0), (None, None))
        base = {"task_family": "f", "role": "analyst", "provider": "p", "model_resolved": "m-1", "effort": "low", "toolset": "read_only"}
        records = capability.summarize([{**base, "status": "passed", "validator_passed": True, "cost_usd": 0.01, "call_id": str(i)} for i in range(40)], floor=0.9)
        self.assertEqual(records[0]["metrics"]["qualified_at_floor"], 0.9)
        tiny = capability.summarize([{**base, "status": "passed", "validator_passed": True}], floor=0.9)
        self.assertIsNone(tiny[0]["metrics"]["qualified_at_floor"])

    def test_availability_failures_do_not_count_against_capability(self) -> None:
        base = {"task_family": "f", "role": "analyst", "provider": "p", "model_resolved": "m-1", "effort": "low", "toolset": "read_only"}
        records = capability.summarize([
            {**base, "status": "failed", "validator_passed": False, "failure_type": "quota: limit"},
            {**base, "status": "passed", "validator_passed": True},
        ])
        self.assertEqual(records[0]["metrics"]["sample_count"], 1)
        self.assertEqual(records[0]["metrics"]["validator_pass_rate"], 1.0)
        self.assertEqual(records[0]["metrics"]["availability_failures"], 1)


class ContinuationTests(unittest.TestCase):
    STATUS = {
        "schema": "personal-agent/orchestrator-os-status/v1", "phase": "test", "active_objective": "Build the eval runner",
        "completed": ["a"], "blockers": [], "recent_decisions": [],
        "next_action": {"summary": "Implement IMP-0003", "worker_class": "balanced", "effort": "medium", "context_refs": ["IMP-0003"], "stop_conditions": ["tests pass"]},
    }

    def test_checkpoints_are_sequential_immutable_and_prompt_is_small(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            directory, prompt = Path(tmp) / "ckpt", Path(tmp) / "next.md"
            first = continuation.build(self.STATUS, directory=directory)
            self.assertEqual(first["id"], "ORCH-0001")
            continuation.write(first, directory, prompt)
            with self.assertRaises(FileExistsError):
                continuation.write(first, directory, prompt)
            second = continuation.build(self.STATUS, directory=directory)
            self.assertEqual((second["id"], second["previous"]), ("ORCH-0002", "ORCH-0001"))
            text = prompt.read_text(encoding="utf-8")
            self.assertIn("docs/orchestrator-os/ENTRYPOINT.md", text)
            self.assertIn("ORCH-0001", text)
            self.assertIn("Implement IMP-0003", text)
            self.assertLess(len(text), 2500)


class EvidenceTests(unittest.TestCase):
    def test_record_validation(self) -> None:
        good = {"schema": "personal-agent/evidence-record/v1", "id": "FND-0099", "type": "FND", "title": "A finding", "status": "accepted", "created_at": "x", "links": [{"rel": "derived_from", "ref": "EVR-0001"}]}
        self.assertEqual(evidence.validate_record(good, "t"), [])
        self.assertTrue(evidence.validate_record({**good, "type": "DEC"}, "t"))
        self.assertTrue(evidence.validate_record({**good, "links": [{"rel": "likes", "ref": "x"}]}, "t"))

    def test_repository_state_is_valid(self) -> None:
        result = evidence.validate_tree()
        self.assertEqual(result["errors"], [])


if __name__ == "__main__":
    unittest.main()
