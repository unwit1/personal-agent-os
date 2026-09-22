from __future__ import annotations

import copy
import json
import shutil
import sys
import unittest
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os import capabilities, workflows
from agent_os.compiler import compile_context
from agent_os.paths import ROOT


MANIFEST = {
    "schema": "personal-agent/workflow-manifest/v1",
    "version": 1,
    "workflow_id": "fixture-sweep",
    "project": "personal-agent-os",
    "goal": "Exercise the staged orchestrator deterministically.",
    "max_escalations": 1,
    "stages": [
        {
            "stage_id": "cheap-check",
            "goal": "A deterministic stage that passes.",
            "required_context": {"task": "routing and validation", "token_budget": 600, "include_handoff": False},
            "preferred_execution_path": "deterministic",
            "capability_class": "deterministic",
            "effort": "none",
            "validator": {"kind": "command", "command": [sys.executable, "-c", "raise SystemExit(0)"]},
            "stop_condition": "the check has run",
            "expected_outputs": ["check result"],
            "checkpoint": "projects/personal-agent-os/workflows",
            "next_stage": "think",
        },
        {
            "stage_id": "think",
            "goal": "A model stage that must be handed to an agent.",
            "required_context": {"task": "token budget pruning", "token_budget": 900},
            "preferred_execution_path": "model",
            "capability_class": "fast",
            "effort": "low",
            "allowed_tools": ["read"],
            "validator": {"kind": "outputs_present"},
            "stop_condition": "a recommendation exists",
            "expected_outputs": ["recommendation"],
            "next_stage": None,
        },
    ],
}

FAILING_COMMAND = [sys.executable, "-c", "raise SystemExit(1)"]


class WorkflowFixture(unittest.TestCase):
    """Each test gets its own manifest directory and run store."""

    def setUp(self) -> None:
        scratch = ROOT / ".tmp"
        scratch.mkdir(exist_ok=True)
        self.temporary = scratch / f"workflow-{uuid.uuid4()}"
        (self.temporary / "workflows").mkdir(parents=True)
        (self.temporary / "projects" / "personal-agent-os" / "workflows").mkdir(parents=True)
        self._workflow_dir = workflows.WORKFLOW_DIR
        self._root = workflows.ROOT
        workflows.WORKFLOW_DIR = self.temporary / "workflows"
        workflows.ROOT = self.temporary
        self.addCleanup(self._restore)
        self.write_manifest(MANIFEST)

    def _restore(self) -> None:
        workflows.WORKFLOW_DIR = self._workflow_dir
        workflows.ROOT = self._root
        shutil.rmtree(self.temporary, ignore_errors=True)

    def write_manifest(self, manifest: dict) -> dict:
        path = workflows.WORKFLOW_DIR / f"{manifest['workflow_id']}.json"
        path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        return manifest


class ManifestValidationTests(WorkflowFixture):
    def test_the_reference_manifest_is_valid(self) -> None:
        self.assertEqual(workflows.manifest_problems(MANIFEST), [])

    def test_shipped_manifests_are_valid(self) -> None:
        """The manifests actually committed to the repository must load."""
        shipped = sorted(self._workflow_dir.glob("*.json"))
        self.assertTrue(shipped, "no workflow manifest is shipped")
        for path in shipped:
            with self.subTest(manifest=path.name):
                manifest = json.loads(path.read_text(encoding="utf-8"))
                self.assertEqual(workflows.manifest_problems(manifest), [])
                self.assertEqual(path.stem, manifest["workflow_id"])

    def _broken(self, mutate) -> list[str]:
        manifest = copy.deepcopy(MANIFEST)
        mutate(manifest)
        return workflows.manifest_problems(manifest)

    def test_unsupported_schema_is_rejected(self) -> None:
        problems = self._broken(lambda m: m.__setitem__("schema", "something/else"))
        self.assertIn("unsupported manifest schema", problems)

    def test_unknown_capability_class_is_rejected(self) -> None:
        problems = self._broken(lambda m: m["stages"][1].__setitem__("capability_class", "genius"))
        self.assertTrue(any("unsupported capability_class" in item for item in problems))

    def test_duplicate_stage_ids_are_rejected(self) -> None:
        problems = self._broken(lambda m: m["stages"][1].__setitem__("stage_id", "cheap-check"))
        self.assertTrue(any("duplicate stage_id" in item for item in problems))

    def test_dangling_next_stage_is_rejected(self) -> None:
        problems = self._broken(lambda m: m["stages"][0].__setitem__("next_stage", "nowhere"))
        self.assertTrue(any("unknown stage nowhere" in item for item in problems))

    def test_token_budget_below_the_floor_is_rejected(self) -> None:
        problems = self._broken(lambda m: m["stages"][1]["required_context"].__setitem__("token_budget", 10))
        self.assertTrue(any("token_budget" in item for item in problems))

    def test_deterministic_stage_without_a_validator_is_rejected(self) -> None:
        """A deterministic stage nobody can check is just an unverified stage."""
        problems = self._broken(lambda m: m["stages"][0].__setitem__("validator", {"kind": "none"}))
        self.assertTrue(any("needs a validator" in item for item in problems))

    def test_invalid_execution_path_candidates_are_rejected(self) -> None:
        problems = self._broken(lambda m: m["stages"][1].__setitem__("available_execution_paths", ["model", "model"]))
        self.assertTrue(any("available_execution_paths must be unique" in item for item in problems))

    def test_command_validator_without_a_command_is_rejected(self) -> None:
        problems = self._broken(lambda m: m["stages"][0].__setitem__("validator", {"kind": "command"}))
        self.assertTrue(any("declares no command" in item for item in problems))

    def test_loading_an_invalid_manifest_raises(self) -> None:
        broken = copy.deepcopy(MANIFEST)
        broken["workflow_id"] = "broken-sweep"
        broken["stages"][0]["capability_class"] = "genius"
        self.write_manifest(broken)
        with self.assertRaises(ValueError):
            workflows.load_manifest("broken-sweep")


class StageOrderingTests(WorkflowFixture):
    def test_explicit_links_determine_order(self) -> None:
        self.assertEqual(workflows.ordered_stage_ids(MANIFEST), ["cheap-check", "think"])

    def test_declaration_order_covers_unlinked_stages(self) -> None:
        manifest = copy.deepcopy(MANIFEST)
        manifest["stages"][0]["next_stage"] = None
        self.assertEqual(workflows.ordered_stage_ids(manifest), ["cheap-check", "think"])

    def test_next_stage_skips_completed_work(self) -> None:
        record = workflows.start("fixture-sweep", run_id="r1")
        self.assertEqual(workflows.next_stage_id(MANIFEST, record), "cheap-check")
        record["stages"]["cheap-check"]["status"] = "complete"
        self.assertEqual(workflows.next_stage_id(MANIFEST, record), "think")

    def test_a_blocked_stage_stops_the_run(self) -> None:
        """Blocked work must not be silently stepped over."""
        record = workflows.start("fixture-sweep", run_id="r2")
        record["stages"]["cheap-check"]["status"] = "blocked"
        self.assertIsNone(workflows.next_stage_id(MANIFEST, record))


class RestartAndIdempotencyTests(WorkflowFixture):
    def test_starting_an_existing_run_resumes_it(self) -> None:
        first = workflows.start("fixture-sweep", run_id="resume-me")
        workflows.run_stage("fixture-sweep", "resume-me")
        second = workflows.start("fixture-sweep", run_id="resume-me")
        self.assertEqual(first["created_at"], second["created_at"], "resuming created a new run")
        self.assertEqual(second["stages"]["cheap-check"]["status"], "complete")

    def test_start_can_refuse_to_clobber_an_existing_run(self) -> None:
        workflows.start("fixture-sweep", run_id="no-clobber")
        with self.assertRaises(ValueError):
            workflows.start("fixture-sweep", run_id="no-clobber", resume=False)

    def test_rerunning_a_completed_stage_is_a_no_op(self) -> None:
        """A successful cheap stage is never redone without a recorded reason."""
        workflows.start("fixture-sweep", run_id="idem")
        first = workflows.run_stage("fixture-sweep", "idem", "cheap-check")
        self.assertTrue(first["completed_stage"]["validation"]["passed"])
        attempts = workflows.load_run("personal-agent-os", "idem")["stages"]["cheap-check"]["attempts"]
        again = workflows.run_stage("fixture-sweep", "idem", "cheap-check")
        self.assertTrue(again["skipped"])
        after = workflows.load_run("personal-agent-os", "idem")["stages"]["cheap-check"]
        self.assertEqual(after["attempts"], attempts, "a completed stage was re-executed")
        self.assertEqual(after["capability_class"], "deterministic", "a passing stage was escalated")

    def test_completing_a_finished_stage_twice_is_idempotent(self) -> None:
        workflows.start("fixture-sweep", run_id="idem2")
        workflows.run_stage("fixture-sweep", "idem2", "cheap-check")
        workflows.complete_stage("fixture-sweep", "idem2", "think", outputs=["recommendation"])
        repeat = workflows.complete_stage("fixture-sweep", "idem2", "think", outputs=["recommendation"])
        self.assertTrue(repeat["skipped"])

    def test_a_run_interrupted_mid_workflow_resumes_from_persisted_state(self) -> None:
        workflows.start("fixture-sweep", run_id="interrupted")
        workflows.run_stage("fixture-sweep", "interrupted")
        # Simulate a new session: nothing in memory, only what is on disk.
        resumed = workflows.status("fixture-sweep", "interrupted")
        self.assertEqual(resumed["next_stage"]["stage_id"], "think")
        self.assertEqual(resumed["stages"][0]["status"], "complete")


class CheckpointTests(WorkflowFixture):
    def test_checkpoint_round_trips_through_disk(self) -> None:
        workflows.start("fixture-sweep", run_id="ckpt")
        workflows.run_stage("fixture-sweep", "ckpt", "cheap-check")
        reloaded = workflows.load_run("personal-agent-os", "ckpt")
        self.assertEqual(
            reloaded["stages"]["cheap-check"]["checkpoint"],
            MANIFEST["stages"][0]["checkpoint"],
        )

    def test_agent_reported_checkpoint_is_persisted(self) -> None:
        workflows.start("fixture-sweep", run_id="ckpt2")
        workflows.run_stage("fixture-sweep", "ckpt2", "cheap-check")
        workflows.complete_stage(
            "fixture-sweep", "ckpt2", "think", outputs=["recommendation"], checkpoint="artifacts/think.json"
        )
        reloaded = workflows.load_run("personal-agent-os", "ckpt2")
        self.assertEqual(reloaded["stages"]["think"]["checkpoint"], "artifacts/think.json")
        self.assertEqual(reloaded["status"], "complete")

    def test_run_state_never_carries_a_transcript(self) -> None:
        workflows.start("fixture-sweep", run_id="no-transcript")
        workflows.run_stage("fixture-sweep", "no-transcript", "cheap-check")
        record = workflows.load_run("personal-agent-os", "no-transcript")
        self.assertFalse(workflows.FORBIDDEN_RUN_KEYS.intersection(record))
        serialized = json.dumps(record)
        self.assertLess(len(serialized), 4000, "run state is growing like a transcript")

    def test_saving_conversation_context_is_refused(self) -> None:
        record = workflows.start("fixture-sweep", run_id="guard")
        record["transcript"] = ["a long chat"]
        with self.assertRaises(ValueError):
            workflows._save(record)


class EscalationTests(WorkflowFixture):
    def _failing_manifest(self, max_escalations: int = 1) -> dict:
        manifest = copy.deepcopy(MANIFEST)
        manifest["workflow_id"] = "failing-sweep"
        manifest["max_escalations"] = max_escalations
        manifest["stages"][0]["validator"] = {"kind": "command", "command": FAILING_COMMAND}
        return self.write_manifest(manifest)

    def test_a_failed_validator_escalates_one_rung(self) -> None:
        self._failing_manifest()
        workflows.start("failing-sweep", run_id="esc")
        workflows.run_stage("failing-sweep", "esc", "cheap-check")
        state = workflows.load_run("personal-agent-os", "esc")["stages"]["cheap-check"]
        self.assertEqual(state["capability_class"], "fast", "escalation skipped a rung or did not happen")
        self.assertEqual(state["escalations"], 1)
        self.assertIn("validator failed", state["escalation_reason"])

    def test_escalation_stops_at_the_configured_budget(self) -> None:
        self._failing_manifest(max_escalations=1)
        workflows.start("failing-sweep", run_id="esc2")
        workflows.run_stage("failing-sweep", "esc2", "cheap-check")
        workflows.run_stage("failing-sweep", "esc2", "cheap-check")
        state = workflows.load_run("personal-agent-os", "esc2")["stages"]["cheap-check"]
        self.assertEqual(state["status"], "blocked")
        self.assertIn("escalation budget exhausted", state["escalation_reason"])
        self.assertEqual(workflows.load_run("personal-agent-os", "esc2")["status"], "blocked")

    def test_no_escalation_without_evidence(self) -> None:
        """A passing stage must never be promoted to a stronger class."""
        workflows.start("fixture-sweep", run_id="no-esc")
        workflows.run_stage("fixture-sweep", "no-esc", "cheap-check")
        state = workflows.load_run("personal-agent-os", "no-esc")["stages"]["cheap-check"]
        self.assertEqual(state["escalations"], 0)
        self.assertIsNone(state["escalation_reason"])
        self.assertEqual(state["capability_class"], "deterministic")

    def test_partial_work_survives_a_failed_stage(self) -> None:
        workflows.start("fixture-sweep", run_id="partial")
        workflows.run_stage("fixture-sweep", "partial", "cheap-check")
        workflows.complete_stage(
            "fixture-sweep", "partial", "think", outputs=["half a recommendation"], passed=False, detail="ran out of time"
        )
        state = workflows.load_run("personal-agent-os", "partial")["stages"]["think"]
        self.assertFalse(state["validation"]["passed"])
        self.assertIn("half a recommendation", state["outputs"], "partial work was discarded")
        self.assertEqual(state["capability_class"], "balanced", "the unresolved stage did not escalate")
        # Escalation leaves the stage retryable at the higher class rather than
        # dead, so only the unresolved portion is redone.
        self.assertEqual(state["status"], "pending")
        self.assertIn("validator failed", state["escalation_reason"])

    def test_a_caller_cannot_declare_success_the_validator_denies(self) -> None:
        """`passed` is not a way to bypass the declared validator."""
        workflows.start("fixture-sweep", run_id="honest")
        workflows.run_stage("fixture-sweep", "honest", "cheap-check")
        result = workflows.complete_stage("fixture-sweep", "honest", "think", outputs=[])
        self.assertFalse(result["completed_stage"]["validation"]["passed"])
        self.assertIn("missing outputs", result["completed_stage"]["validation"]["detail"])


class StageContextTests(WorkflowFixture):
    def test_each_stage_compiles_its_own_budgeted_context(self) -> None:
        workflows.start("fixture-sweep", run_id="ctx")
        workflows.run_stage("fixture-sweep", "ctx", "cheap-check")
        packet = workflows.prepare_stage("fixture-sweep", "ctx", "think")
        budget = MANIFEST["stages"][1]["required_context"]["token_budget"]
        self.assertLessEqual(packet["context_tokens"], budget)
        self.assertTrue(packet["context"]["context_measurement"]["within_budget"])
        self.assertEqual(packet["context"]["task"], "token budget pruning")

    def test_a_stage_packet_carries_no_earlier_stage_output(self) -> None:
        workflows.start("fixture-sweep", run_id="ctx2")
        workflows.run_stage("fixture-sweep", "ctx2", "cheap-check")
        packet = workflows.prepare_stage("fixture-sweep", "ctx2", "think")
        blob = json.dumps(packet["context"])
        self.assertNotIn("check result", blob, "a previous stage's output leaked into stage context")

    def test_staging_does_not_inflate_total_context(self) -> None:
        """Staging must cost less context than one packet carrying everything.

        The comparison is against a single-pass packet sized to cover the whole
        workflow, which is what a non-staged session would have to load.
        """
        workflows.start("fixture-sweep", run_id="ctx3")
        staged_total = 0
        for stage in MANIFEST["stages"]:
            packet = workflows.prepare_stage("fixture-sweep", "ctx3", stage["stage_id"])
            staged_total += packet["context_tokens"]
        single = compile_context(
            "personal-agent-os",
            MANIFEST["goal"],
            token_budget=sum(s["required_context"]["token_budget"] for s in MANIFEST["stages"]),
        )
        unstaged = single["context_measurement"]["estimated_packet_tokens"]
        naive = single["context_measurement"]["naive_all_registered_context_tokens"]
        self.assertLess(staged_total, naive, "staging cost more than loading everything")
        self.assertLessEqual(
            staged_total,
            unstaged * 2,
            f"staged context ({staged_total}) ballooned against a single pass ({unstaged})",
        )


class NextPromptTests(WorkflowFixture):
    def test_the_next_prompt_is_generated_from_persisted_state(self) -> None:
        workflows.start("fixture-sweep", run_id="prompt")
        workflows.run_stage("fixture-sweep", "prompt", "cheap-check")
        summary = workflows.status("fixture-sweep", "prompt")
        prompt = summary["next_prompt"]
        self.assertIn("fixture-sweep", prompt)
        self.assertIn("prompt", prompt)
        self.assertIn("think", prompt)
        self.assertIn("a recommendation exists", prompt, "the stop condition is missing from the prompt")
        self.assertIn("recommendation", prompt)

    def test_an_explicit_template_is_used_and_substituted(self) -> None:
        manifest = copy.deepcopy(MANIFEST)
        manifest["workflow_id"] = "templated"
        manifest["stages"][1]["next_prompt"] = "Run {stage_id} of {workflow_id} for {project} as {run_id}."
        self.write_manifest(manifest)
        workflows.start("templated", run_id="tmpl")
        workflows.run_stage("templated", "tmpl", "cheap-check")
        prompt = workflows.status("templated", "tmpl")["next_prompt"]
        self.assertEqual(prompt, "Run think of templated for personal-agent-os as tmpl.")

    def test_a_finished_run_recommends_nothing_further(self) -> None:
        workflows.start("fixture-sweep", run_id="done")
        workflows.run_stage("fixture-sweep", "done", "cheap-check")
        workflows.complete_stage("fixture-sweep", "done", "think", outputs=["recommendation"])
        summary = workflows.status("fixture-sweep", "done")
        self.assertEqual(summary["run_status"], "complete")
        self.assertIsNone(summary["next_stage"])
        self.assertIsNone(summary["next_prompt"])

    def test_completion_packet_names_the_next_stage_and_capability(self) -> None:
        workflows.start("fixture-sweep", run_id="packet")
        result = workflows.run_stage("fixture-sweep", "packet", "cheap-check")
        self.assertEqual(result["next_stage"]["stage_id"], "think")
        self.assertEqual(result["next_stage"]["capability_class"], "fast")
        self.assertIsNotNone(result["next_prompt"])
        self.assertLess(len(json.dumps(result)), 8000, "the completion packet is not compact")


class CapabilityTests(unittest.TestCase):
    def test_classes_are_ordered_cheapest_first(self) -> None:
        self.assertEqual(
            capabilities.CAPABILITY_CLASSES,
            ("deterministic", "fast", "balanced", "reasoning", "frontier"),
        )
        self.assertTrue(capabilities.is_at_least("reasoning", "fast"))
        self.assertFalse(capabilities.is_at_least("fast", "reasoning"))

    def test_escalation_walks_one_rung_and_stops_at_the_top(self) -> None:
        self.assertEqual(capabilities.next_class("deterministic"), "fast")
        self.assertIsNone(capabilities.next_class("frontier"))

    def test_execution_policy_selects_the_cheapest_declared_path(self) -> None:
        self.assertEqual(
            capabilities.select_execution_path("model", ["model", "skill", "cache"]),
            "cache",
        )
        self.assertEqual(capabilities.select_execution_path("model"), "model")

    def test_execution_policy_rejects_unknown_or_empty_candidates(self) -> None:
        with self.assertRaises(ValueError):
            capabilities.select_execution_path("model", [])
        with self.assertRaises(ValueError):
            capabilities.select_execution_path("model", ["model", "unknown"])


    def test_an_unknown_class_is_rejected(self) -> None:
        with self.assertRaises(capabilities.UnknownCapabilityClass):
            capabilities.rank("genius")

    def test_resolution_is_honest_when_no_provider_is_configured(self) -> None:
        missing = Path(ROOT / ".tmp" / f"absent-{uuid.uuid4()}.json")
        resolved = capabilities.resolve("balanced", missing)
        self.assertFalse(resolved["resolved"])
        self.assertIsNone(resolved["model"])
        self.assertIn("no provider", resolved["reason"])

    def test_a_configured_provider_resolves_a_model_at_run_time(self) -> None:
        scratch = ROOT / ".tmp"
        scratch.mkdir(exist_ok=True)
        path = scratch / f"providers-{uuid.uuid4()}.json"
        path.write_text(
            json.dumps(
                {
                    "providers": [
                        {"id": "local-runner", "enabled": True, "models": {"fast": "small-1", "balanced": "medium-1"}}
                    ]
                }
            ),
            encoding="utf-8",
        )
        self.addCleanup(path.unlink)
        self.assertEqual(capabilities.resolve("fast", path)["model"], "small-1")
        self.assertFalse(capabilities.resolve("frontier", path)["resolved"])

    def test_a_disabled_provider_is_skipped(self) -> None:
        scratch = ROOT / ".tmp"
        scratch.mkdir(exist_ok=True)
        path = scratch / f"providers-{uuid.uuid4()}.json"
        path.write_text(
            json.dumps({"providers": [{"id": "off", "enabled": False, "models": {"fast": "unused"}}]}),
            encoding="utf-8",
        )
        self.addCleanup(path.unlink)
        self.assertFalse(capabilities.resolve("fast", path)["resolved"])


class ExecutionPolicyTests(WorkflowFixture):
    def test_prepared_stage_persists_the_cheapest_declared_path(self) -> None:
        manifest = copy.deepcopy(MANIFEST)
        manifest["stages"][1]["available_execution_paths"] = ["model", "skill", "cache"]
        self.write_manifest(manifest)
        workflows.start("fixture-sweep", run_id="policy")

        packet = workflows.prepare_stage("fixture-sweep", "policy", "think")
        state = workflows.load_run("personal-agent-os", "policy")["stages"]["think"]
        self.assertEqual(packet["stage"]["execution_path"], "cache")
        self.assertEqual(state["execution_path"], "cache")

    def test_run_stage_uses_selected_non_deterministic_path(self) -> None:
        manifest = copy.deepcopy(MANIFEST)
        manifest["stages"][1]["available_execution_paths"] = ["model", "skill"]
        self.write_manifest(manifest)
        workflows.start("fixture-sweep", run_id="skill-route")

        packet = workflows.run_stage("fixture-sweep", "skill-route", "think")
        state = workflows.load_run("personal-agent-os", "skill-route")["stages"]["think"]
        self.assertEqual(packet["stage"]["execution_path"], "skill")
        self.assertEqual(state["execution_path"], "skill")
        self.assertEqual(state["status"], "awaiting_agent")


class ProviderNeutralityTests(unittest.TestCase):
    """The orchestrator core must not know any vendor's name.

    Scope note: this covers the orchestrator modules and the manifest schema
    only. The client-surface registry added in P0.0 names vendors on purpose --
    it exists to describe real clients -- so the whole repository is not a
    meaningful target for this check.
    """

    CORE = (
        Path("src") / "agent_os" / "workflows.py",
        Path("src") / "agent_os" / "capabilities.py",
        Path("schemas") / "workflow-manifest-v1.schema.json",
    )
    VENDOR_TERMS = (
        "claude", "anthropic", "openai", "gpt", "codex", "gemini", "llama",
        "mistral", "cohere", "ollama", "sonnet", "opus", "haiku",
    )

    def test_core_modules_name_no_provider_or_model(self) -> None:
        for relative in self.CORE:
            with self.subTest(module=str(relative)):
                text = (ROOT / relative).read_text(encoding="utf-8").casefold()
                for term in self.VENDOR_TERMS:
                    self.assertNotIn(term, text, f"{relative} names the vendor '{term}'")

    def test_shipped_manifests_name_no_provider_or_model(self) -> None:
        for path in sorted((ROOT / "workflows").glob("*.json")):
            with self.subTest(manifest=path.name):
                text = path.read_text(encoding="utf-8").casefold()
                for term in self.VENDOR_TERMS:
                    self.assertNotIn(term, text, f"{path.name} names the vendor '{term}'")

    def test_stages_declare_capability_classes_not_models(self) -> None:
        for path in sorted((ROOT / "workflows").glob("*.json")):
            manifest = json.loads(path.read_text(encoding="utf-8"))
            for stage in manifest["stages"]:
                with self.subTest(manifest=path.name, stage=stage["stage_id"]):
                    self.assertIn(stage["capability_class"], capabilities.CAPABILITY_CLASSES)
                    self.assertNotIn("model_name", stage)
                    self.assertNotIn("provider", stage)


class WritebackSafetyTests(WorkflowFixture):
    def test_a_run_never_writes_canonical_memory(self) -> None:
        """Stage completion touches run state only, never promoted memory."""
        memory = ROOT / "memory" / "promoted-candidates.json"
        before = memory.read_bytes() if memory.exists() else None
        workflows.start("fixture-sweep", run_id="safe")
        workflows.run_stage("fixture-sweep", "safe", "cheap-check")
        workflows.complete_stage("fixture-sweep", "safe", "think", outputs=["recommendation"])
        after = memory.read_bytes() if memory.exists() else None
        self.assertEqual(before, after, "a workflow run altered canonical memory")

    def test_runs_are_written_only_under_the_project_run_store(self) -> None:
        workflows.start("fixture-sweep", run_id="scoped")
        workflows.run_stage("fixture-sweep", "scoped", "cheap-check")
        written = sorted(p.relative_to(self.temporary).as_posix() for p in self.temporary.rglob("*.json"))
        self.assertEqual(
            written,
            ["projects/personal-agent-os/workflows/scoped.json", "workflows/fixture-sweep.json"],
        )


if __name__ == "__main__":
    unittest.main()
