"""P1.2A multi-agent orchestrator regression suite.

Every test uses synthetic in-process providers, a throwaway Git repository, a
throwaway orchestrator home, telemetry file and claims registry. Nothing here
calls a paid model or touches the machine's real registries.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.orchestrator.adapters import synthetic
from agent_os.orchestrator.adapters.base import AgentLaunchRequest, RunningAgent
from agent_os.orchestrator.adapters.claude_code import ClaudeCodeAdapter
from agent_os.orchestrator.adapters.codex_cli import CodexCliAdapter
from agent_os.orchestrator.adapters.base import ProviderStatus
from agent_os.orchestrator.engine import Orchestrator, OrchestratorError
from agent_os.orchestrator.model import PlanError, PolicyError, merge_policy, scopes_overlap
from agent_os.orchestrator.router import ProviderRegistry, select
from agent_os.orchestrator.store import RunStore, StoreError, redact
from agent_os.orchestrator.worktrees import WorktreeManager, git
from agent_os.paths import ROOT
from agent_os.telemetry import LocalTelemetryStore


PASS = {"kind": "command", "command": [sys.executable, "-c", "print('ok')"]}


def provider(provider_id: str, **extra) -> dict:
    entry = {
        "id": provider_id,
        "adapter": "synthetic",
        "models": {
            "fast": f"{provider_id}-fast",
            "balanced": f"{provider_id}-balanced",
            "reasoning": f"{provider_id}-reasoning",
            "frontier": f"{provider_id}-frontier",
        },
        "effort_map": {"none": "minimal", "low": "lo", "medium": "med", "high": "hi"},
        "max_concurrency": 2,
    }
    entry.update(extra)
    return entry


def edit_script(extra: dict | None = None):
    """Implementers write one file inside their first scope entry; reviewers approve."""

    def script(request: AgentLaunchRequest, call: int) -> dict:
        if request.role == "reviewer":
            return {"structured": {"status": "done", "verdict": "approved", "findings": []}}
        if request.role == "planner":
            return {"structured": {"status": "done", "tasks": [{"id": "impl", "goal": "do it", "scope": ["impl"]}]}}
        base = request.node_id.split(".")[0]
        behaviour = {"edits": {f"{base}/{request.node_id}-{call}.txt": "change\n"}, "structured": {"status": "done", "summary": "edited"}}
        behaviour.update((extra or {}).get(base, {}))
        return behaviour

    return script


class OrchestratorFixture(unittest.TestCase):
    providers = ("alpha", "beta")

    def setUp(self) -> None:
        synthetic.reset()
        self.tmp = Path(tempfile.mkdtemp(prefix="agent-os-orch-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.addCleanup(synthetic.reset)
        self.repo = self.tmp / "repo"
        self.repo.mkdir()
        self.git("init", "-b", "main")
        (self.repo / "README.md").write_text("fixture\n", encoding="utf-8")
        for folder in ("a", "b", "c", "impl"):
            (self.repo / folder).mkdir()
            (self.repo / folder / ".keep").write_text("", encoding="utf-8")
        self.git("add", "-A")
        self.git("commit", "-m", "init")
        self.telemetry_path = self.tmp / "telemetry" / "events.jsonl"
        self.claims = self.tmp / "claims.json"
        self.engine = self.make_engine()
        for name in self.providers:
            synthetic.SCRIPTS[name] = edit_script()

    def git(self, *args: str) -> str:
        return subprocess.run(
            ["git", "-c", "user.name=fixture", "-c", "user.email=f@x", *args],
            cwd=self.repo, check=True, capture_output=True, text=True,
        ).stdout

    def registry(self) -> ProviderRegistry:
        return ProviderRegistry(providers=[provider(name) for name in self.providers])

    def make_engine(self, registry: ProviderRegistry | None = None) -> Orchestrator:
        return Orchestrator(
            RunStore(self.tmp / "home"),
            registry=registry or self.registry(),
            telemetry_store=LocalTelemetryStore(self.telemetry_path),
            claims_path=self.claims,
            sleep=lambda seconds: None,
        )

    def policy(self, **overrides) -> dict:
        base = {"auto_continue": True, "poll_interval_seconds": 0, "announce_claims": False}
        base.update(overrides)
        return base

    def task(self, task_id: str, scope: list[str] | None = None, **extra) -> dict:
        entry = {"id": task_id, "goal": f"work on {task_id}", "scope": scope if scope is not None else [task_id], "validators": [PASS]}
        entry.update(extra)
        return entry

    def create(self, tasks: list[dict], **policy) -> str:
        return self.engine.create_run("fixture goal", repository=self.repo, tasks=tasks, policy=self.policy(**policy))["run_id"]

    def node(self, run_id: str, node_id: str, engine: Orchestrator | None = None) -> dict:
        return (engine or self.engine).load(run_id)["nodes"][node_id]


# ---------------------------------------------------------------------------
# Worktree isolation, concurrency and scope
# ---------------------------------------------------------------------------


class WorktreeIsolationTests(OrchestratorFixture):
    def test_concurrent_editors_get_distinct_worktrees_and_branches(self) -> None:
        synthetic.SCRIPTS["alpha"] = edit_script({"a": {"ticks": 3}, "b": {"ticks": 3}})
        run_id = self.create([self.task("a"), self.task("b")])
        self.engine.start(run_id)
        self.engine.step(run_id)
        a, b = self.node(run_id, "a"), self.node(run_id, "b")
        self.assertEqual(a["state"], "RUNNING")
        self.assertEqual(b["state"], "RUNNING", "independent branches run concurrently")
        self.assertNotEqual(Path(a["worktree"]["path"]).resolve(), Path(b["worktree"]["path"]).resolve())
        self.assertNotEqual(a["worktree"]["branch"], b["worktree"]["branch"])
        for node in (a, b):
            self.assertEqual(node["worktree"]["owned_by"], node["id"])
            self.assertNotEqual(Path(node["worktree"]["path"]).resolve(), self.repo.resolve())
            self.assertIn(node["worktree"]["branch"], self.git("branch", "--list", node["worktree"]["branch"]))

    def test_overlapping_scopes_are_serialized_not_raced(self) -> None:
        synthetic.SCRIPTS["alpha"] = edit_script({"a": {"ticks": 2}, "b": {"edits": {"a/nested/b.txt": "b\n"}}})
        run_id = self.create([self.task("a", ["a"]), self.task("b", ["a/nested"])])
        self.engine.start(run_id)
        self.engine.step(run_id)
        self.assertEqual(self.node(run_id, "a")["state"], "RUNNING")
        b = self.node(run_id, "b")
        self.assertIn(b["state"], {"PENDING", "RUNNABLE"})
        self.assertIsNone(b["worktree"])
        self.assertIn("serialized", b["wait_reason"])
        final = self.engine.run_loop(run_id, max_ticks=60)
        self.assertEqual(final["state"], "COMPLETE", final["state_reason"])
        # b started from the integration head, so it saw a's change.
        a_commit = self.node(run_id, "a")["integration"]["commit"]
        b_base = self.node(run_id, "b")["worktree"]["base_commit"]
        self.assertEqual(b_base, a_commit)

    def test_scope_overlap_rules(self) -> None:
        self.assertTrue(scopes_overlap(["src"], ["src/a.py"]))
        self.assertTrue(scopes_overlap([], ["docs"]))
        self.assertFalse(scopes_overlap(["src/a"], ["src/ab"]))
        self.assertFalse(scopes_overlap(["docs"], ["tests"]))

    def test_edit_outside_scope_fails_validation(self) -> None:
        synthetic.SCRIPTS["alpha"] = edit_script({"a": {"edits": {"README.md": "clobbered\n"}}})
        run_id = self.create([self.task("a")], max_escalations=0, max_stage_retries=0)
        final = self.engine.run_loop(run_id, max_ticks=20)
        a = self.node(run_id, "a")
        self.assertEqual(final["state"], "BLOCKED")
        self.assertFalse(a["integrated"])
        scope = next(item for item in a["validation"]["evidence"] if item["kind"] == "scope")
        self.assertFalse(scope["passed"])
        self.assertEqual((self.repo / "README.md").read_text(encoding="utf-8"), "fixture\n")

    def test_worktree_manager_merge_conflict_is_aborted_cleanly(self) -> None:
        manager = WorktreeManager(self.repo, self.tmp / "wt", "conflict-run")
        base = git(["rev-parse", "HEAD"], self.repo).stdout.strip()
        manager.ensure_integration(base)
        one = manager.create("one", base)
        two = manager.create("two", base)
        for info, text in ((one, "one\n"), (two, "two\n")):
            Path(info["path"], "README.md").write_text(text, encoding="utf-8")
            manager.checkpoint(info["path"], "edit")
        self.assertTrue(manager.merge(one["branch"], "merge one")["merged"])
        outcome = manager.merge(two["branch"], "merge two")
        self.assertFalse(outcome["merged"])
        self.assertEqual(outcome["conflicts"], ["README.md"])
        self.assertEqual(manager.integration_head(), outcome["before"])
        self.assertFalse(git(["status", "--porcelain"], manager.integration_path).stdout.strip())


# ---------------------------------------------------------------------------
# Routing
# ---------------------------------------------------------------------------


class RoutingTests(unittest.TestCase):
    def registry(self, *entries) -> ProviderRegistry:
        return ProviderRegistry(providers=list(entries) or [provider("alpha"), provider("beta")])

    def test_capability_class_resolves_to_provider_model_and_effort(self) -> None:
        choice = select(self.registry(), capability_class="reasoning", effort="high", role="implementer")
        self.assertTrue(choice["resolved"])
        self.assertEqual((choice["provider"], choice["model"], choice["provider_effort"]), ("alpha", "alpha-reasoning", "hi"))

    def test_preference_shifts_class_within_bounds(self) -> None:
        economy = select(self.registry(), capability_class="balanced", effort="low", role="implementer", preference="economy")
        quality = select(self.registry(), capability_class="balanced", effort="low", role="implementer", preference="quality")
        self.assertEqual(economy["model"], "alpha-fast")
        self.assertEqual(quality["model"], "alpha-reasoning")
        floor = select(self.registry(), capability_class="fast", effort="low", role="implementer", preference="economy")
        self.assertEqual(floor["model"], "alpha-fast")

    def test_disabled_or_unavailable_provider_falls_back(self) -> None:
        registry = self.registry(provider("alpha", enabled=False), provider("beta"))
        self.assertEqual(select(registry, capability_class="balanced", effort="low", role="implementer")["provider"], "beta")
        registry = self.registry(provider("alpha"), provider("beta"))
        choice = select(registry, capability_class="balanced", effort="low", role="implementer", availability={"alpha": False})
        self.assertEqual(choice["provider"], "beta")

    def test_missing_class_uses_nearest_stronger_class(self) -> None:
        entry = provider("alpha")
        del entry["models"]["balanced"]
        choice = select(self.registry(entry), capability_class="balanced", effort="low", role="implementer")
        self.assertEqual(choice["model"], "alpha-reasoning")
        self.assertIn("nearest covered class", choice["reason"])

    def test_nothing_configured_is_reported_honestly(self) -> None:
        empty = ProviderRegistry(path=Path(tempfile.gettempdir()) / "does-not-exist-providers.json")
        choice = select(empty, capability_class="balanced", effort="low", role="implementer")
        self.assertFalse(choice["resolved"])
        self.assertIn("no provider registry", choice["reason"])

    def test_user_override_wins(self) -> None:
        choice = select(self.registry(), capability_class="fast", effort="low", role="implementer", override={"provider": "beta", "model": "beta-custom", "effort": "high"})
        self.assertEqual((choice["provider"], choice["model"], choice["effort"]), ("beta", "beta-custom", "high"))
        self.assertTrue(choice["overridden"])

    def test_reviewer_prefers_a_distinct_provider(self) -> None:
        choice = select(self.registry(), capability_class="balanced", effort="medium", role="reviewer", avoid=["alpha"])
        self.assertEqual(choice["provider"], "beta")
        solo = self.registry(provider("alpha"))
        forced = select(solo, capability_class="balanced", effort="medium", role="reviewer", avoid=["alpha"], require_avoid=True)
        self.assertFalse(forced["resolved"])

    def test_placeholder_models_are_not_routable(self) -> None:
        entry = provider("alpha")
        entry["models"] = {"balanced": "<configure-current-balanced-model>"}
        choice = select(self.registry(entry), capability_class="balanced", effort="low", role="implementer")
        self.assertFalse(choice["resolved"])


class OverrideTests(OrchestratorFixture):
    def test_override_applies_without_modifying_manifests_or_tasks(self) -> None:
        manifest_hashes = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in (ROOT / "workflows").glob("*.json")}
        tasks_file = self.tmp / "tasks.json"
        tasks = [self.task("a")]
        tasks_file.write_text(json.dumps(tasks), encoding="utf-8")
        before = tasks_file.read_bytes()
        run_id = self.create(json.loads(tasks_file.read_text(encoding="utf-8")))
        self.engine.set_override(run_id, role="implementer", provider="beta", model="beta-pinned", effort="high")
        self.engine.run_loop(run_id, max_ticks=30)
        selection = self.node(run_id, "a")["selection"]
        self.assertEqual((selection["provider"], selection["model"], selection["effort"]), ("beta", "beta-pinned", "high"))
        self.assertTrue(selection["overridden"])
        self.assertEqual(tasks_file.read_bytes(), before)
        after = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in (ROOT / "workflows").glob("*.json")}
        self.assertEqual(after, manifest_hashes)

    def test_reassign_moves_a_blocked_node_to_another_provider(self) -> None:
        synthetic.SCRIPTS["alpha"] = edit_script({"a": {"failure": "process_error"}})
        run_id = self.create([self.task("a")], max_stage_retries=0, provider_failover=False)
        self.assertEqual(self.engine.run_loop(run_id, max_ticks=10)["state"], "BLOCKED")
        self.engine.reassign(run_id, "a", "beta", effort="low")
        final = self.engine.run_loop(run_id, max_ticks=30)
        self.assertEqual(final["state"], "COMPLETE", final["state_reason"])
        self.assertEqual(self.node(run_id, "a")["selection"]["provider"], "beta")


# ---------------------------------------------------------------------------
# Failure, failover, restart
# ---------------------------------------------------------------------------


class FailoverAndRestartTests(OrchestratorFixture):
    def test_quota_failure_preserves_checkpoint_and_hands_off(self) -> None:
        partial = {"a/partial.txt": "half done\n"}
        synthetic.SCRIPTS["alpha"] = edit_script({"a": {"failure": "quota", "detail": "usage limit reached", "partial_edits": partial}})
        run_id = self.create([self.task("a")])
        final = self.engine.run_loop(run_id, max_ticks=40)
        self.assertEqual(final["state"], "COMPLETE", final["state_reason"])
        a = self.node(run_id, "a")
        self.assertEqual(a["failures"][0]["kind"], "quota")
        self.assertIn("alpha", a["excluded_providers"])
        self.assertEqual(a["selection"]["provider"], "beta")
        # Partial work from the failed provider survived into the integration.
        integration_branch = self.engine.load(run_id)["integration"]["branch"]
        self.assertEqual(self.git("show", f"{integration_branch}:a/partial.txt"), "half done\n")

    def test_every_provider_failing_blocks_instead_of_looping(self) -> None:
        for name in self.providers:
            synthetic.SCRIPTS[name] = edit_script({"a": {"failure": "quota"}})
        run_id = self.create([self.task("a")])
        final = self.engine.run_loop(run_id, max_ticks=40)
        self.assertEqual(final["state"], "BLOCKED")
        self.assertIn("no provider", self.node(run_id, "a")["wait_reason"])

    def test_restart_keeps_passed_work_and_interrupts_running_workers(self) -> None:
        synthetic.SCRIPTS["alpha"] = edit_script({"b": {"ticks": 1000}})
        run_id = self.create([self.task("a"), self.task("b")], require_independent_review_for_model_edits=False)
        self.engine.start(run_id)
        for _ in range(3):
            self.engine.step(run_id)
        a = self.node(run_id, "a")
        self.assertEqual(a["state"], "PASSED")
        self.assertTrue(a["integrated"])
        self.assertEqual(self.node(run_id, "b")["state"], "RUNNING")
        b_worktree = self.node(run_id, "b")["worktree"]["path"]

        # Simulate a crash: a new engine has no live handles for b.
        synthetic._LIVE.clear()
        synthetic.SCRIPTS["alpha"] = edit_script()
        restarted = self.make_engine()
        restarted.step(run_id)
        b = self.node(run_id, "b", restarted)
        self.assertEqual(b["failures"][-1]["kind"], "interrupted")
        final = restarted.run_loop(run_id, max_ticks=40)
        self.assertEqual(final["state"], "COMPLETE", final["state_reason"])
        a_after = self.node(run_id, "a", restarted)
        self.assertEqual(a_after["attempts"], 1, "a passed stage is not rerun after restart")
        self.assertEqual(self.node(run_id, "b", restarted)["worktree"]["path"], b_worktree, "interrupted worker keeps its worktree")

    def test_detached_live_worker_is_not_marked_complete(self) -> None:
        synthetic.SCRIPTS["alpha"] = edit_script({"a": {"ticks": 1000}})
        run_id = self.create([self.task("a")])
        self.engine.start(run_id)
        self.engine.step(run_id)
        record = self.engine.load(run_id)
        record["nodes"]["a"]["process"]["pid"] = os.getpid()  # a live process we did not start here
        self.engine.store.save(record)
        restarted = self.make_engine()
        restarted.step(run_id)
        a = self.node(run_id, "a", restarted)
        self.assertEqual(a["state"], "RUNNING")
        self.assertIn("earlier orchestrator", a["wait_reason"])

    def test_retry_and_escalation_are_bounded(self) -> None:
        failing = {"kind": "command", "command": [sys.executable, "-c", "raise SystemExit(3)"]}
        run_id = self.create([self.task("a", validators=[failing])], max_escalations=2)
        final = self.engine.run_loop(run_id, max_ticks=40)
        a = self.node(run_id, "a")
        self.assertEqual(final["state"], "BLOCKED")
        self.assertEqual(a["state"], "FAILED_FINAL")
        self.assertEqual(a["escalations"], 2)
        self.assertEqual(a["attempts"], 3)
        self.assertEqual(a["capability_class"], "frontier")
        self.assertEqual([item["kind"] for item in a["failures"]], ["validator_failed"] * 3)
        self.assertFalse(a["integrated"])

    def test_process_failures_are_bounded_by_retry_policy(self) -> None:
        for name in self.providers:
            synthetic.SCRIPTS[name] = edit_script({"a": {"failure": "process_error"}})
        run_id = self.create([self.task("a")], max_stage_retries=2)
        final = self.engine.run_loop(run_id, max_ticks=40)
        self.assertEqual(final["state"], "BLOCKED")
        self.assertLessEqual(self.node(run_id, "a")["attempts"], 3)


# ---------------------------------------------------------------------------
# Auto Continue, approval gates, pause/resume
# ---------------------------------------------------------------------------


class AutoContinueTests(OrchestratorFixture):
    def test_auto_continue_drives_a_multi_stage_graph_to_complete(self) -> None:
        tasks = [self.task("a"), self.task("b", depends_on=["a"]), self.task("c", depends_on=["b"])]
        run_id = self.create(tasks)
        final = self.engine.run_loop(run_id)
        self.assertEqual(final["state"], "COMPLETE", final["state_reason"])
        record = self.engine.load(run_id)
        self.assertEqual(record["integration"]["merged"], ["a", "b", "c"])
        for node_id in ("a", "b", "c"):
            reviews = record["nodes"][node_id]["review"]["reviewers"]
            self.assertTrue(reviews and reviews[-1]["independent_provider"])
        self.assertEqual(record["gates"], [])
        self.assertTrue(record["final"]["validation"]["passed"])

    def test_without_auto_continue_the_loop_stops_at_a_stage_boundary(self) -> None:
        run_id = self.create([self.task("a"), self.task("b", depends_on=["a"])], auto_continue=False, require_independent_review_for_model_edits=False)
        first = self.engine.run_loop(run_id, max_ticks=40)
        self.assertNotEqual(first["state"], "COMPLETE")
        self.assertEqual(self.node(run_id, "a")["state"], "PASSED")
        self.assertIn(self.node(run_id, "b")["state"], {"PENDING", "RUNNABLE", "RUNNING"})
        self.engine.set_auto_continue(run_id, True)
        self.assertEqual(self.engine.run_loop(run_id, max_ticks=40)["state"], "COMPLETE")

    def test_auto_continue_stops_exactly_at_an_approval_gate(self) -> None:
        gate = {"kind": "destructive_action", "reason": "deletes generated files"}
        run_id = self.create([self.task("a"), self.task("b", depends_on=["a"], approval_gate=gate)])
        stopped = self.engine.run_loop(run_id, max_ticks=60)
        self.assertEqual(stopped["state"], "APPROVAL_REQUIRED")
        b = self.node(run_id, "b")
        self.assertEqual(b["state"], "APPROVAL_REQUIRED")
        self.assertEqual(b["attempts"], 0, "gated work is not launched before approval")
        gate_id = stopped["gates"][-1]["id"]
        self.engine.decide(run_id, gate_id, approve=True, note="ok")
        final = self.engine.run_loop(run_id, max_ticks=60)
        self.assertEqual(final["state"], "COMPLETE", final["state_reason"])

    def test_rejected_gate_blocks_instead_of_being_skipped(self) -> None:
        gate = {"kind": "consequential_external_write", "reason": "publishes a package"}
        run_id = self.create([self.task("a", approval_gate=gate)])
        stopped = self.engine.run_loop(run_id, max_ticks=10)
        self.engine.decide(run_id, stopped["gates"][0]["id"], approve=False, note="not now")
        final = self.engine.run_loop(run_id, max_ticks=10)
        self.assertEqual(final["state"], "BLOCKED")
        self.assertEqual(self.node(run_id, "a")["state"], "CANCELLED")

    def test_pause_prevents_dispatch_and_resume_continues(self) -> None:
        synthetic.SCRIPTS["alpha"] = edit_script({"a": {"ticks": 2}})
        run_id = self.create([self.task("a"), self.task("b")], max_parallel_editors=1, require_independent_review_for_model_edits=False)
        self.engine.start(run_id)
        self.engine.step(run_id)
        self.assertEqual(self.node(run_id, "a")["state"], "RUNNING")
        self.engine.pause(run_id)
        paused = self.engine.run_loop(run_id, max_ticks=20)
        self.assertEqual(paused["state"], "PAUSED")
        self.assertEqual(self.node(run_id, "a")["state"], "PASSED", "a running worker is still collected while paused")
        self.assertEqual(self.node(run_id, "b")["attempts"], 0, "no new dispatch while paused")
        self.engine.resume(run_id)
        self.assertEqual(self.engine.run_loop(run_id, max_ticks=20)["state"], "COMPLETE")

    def test_stop_cancels_workers_and_resume_continues_from_checkpoint(self) -> None:
        synthetic.SCRIPTS["alpha"] = edit_script({"a": {"ticks": 1000}})
        run_id = self.create([self.task("a")])
        self.engine.start(run_id)
        self.engine.step(run_id)
        stopped = self.engine.stop(run_id)
        a = self.node(run_id, "a")
        self.assertEqual(stopped["state"], "PAUSED")
        self.assertEqual(a["state"], "FAILED_RETRYABLE")
        self.assertEqual(a["retries"], 0, "a user stop does not consume the retry budget")
        synthetic.SCRIPTS["alpha"] = edit_script()
        self.engine.resume(run_id)
        self.assertEqual(self.engine.run_loop(run_id, max_ticks=30)["state"], "COMPLETE")

    def test_budget_gate_stops_runaway_launching(self) -> None:
        run_id = self.create([self.task("a"), self.task("b")], max_launches=1, require_independent_review_for_model_edits=False)
        stopped = self.engine.run_loop(run_id, max_ticks=20)
        self.assertEqual(stopped["state"], "APPROVAL_REQUIRED")
        self.assertEqual(stopped["gates"][-1]["kind"], "budget_exhausted")
        self.engine.decide(run_id, stopped["gates"][-1]["id"], approve=True)
        self.assertEqual(self.engine.run_loop(run_id, max_ticks=20)["state"], "COMPLETE")

    def test_agent_needing_a_decision_opens_a_gate(self) -> None:
        calls = {"n": 0}

        def script(request, call):
            if request.role == "reviewer":
                return {"structured": {"status": "done", "verdict": "approved", "findings": []}}
            calls["n"] += 1
            if calls["n"] == 1:
                return {"structured": {"status": "needs_decision", "question": "keep the v1 API?"}}
            return {"edits": {"a/done.txt": "x\n"}, "structured": {"status": "done"}}

        synthetic.SCRIPTS["alpha"] = script
        synthetic.SCRIPTS["beta"] = script
        run_id = self.create([self.task("a")])
        stopped = self.engine.run_loop(run_id, max_ticks=20)
        self.assertEqual(stopped["state"], "APPROVAL_REQUIRED")
        self.assertEqual(stopped["gates"][0]["kind"], "agent_needs_decision")
        self.engine.decide(run_id, stopped["gates"][0]["id"], approve=True, note="keep v1")
        self.assertEqual(self.engine.run_loop(run_id, max_ticks=30)["state"], "COMPLETE")
        prompt = (self.engine.store.run_dir(run_id) / "workers" / "a-2" / "prompt.md").read_text(encoding="utf-8")
        self.assertIn("keep v1", prompt)

    def test_start_recommended_plans_then_completes(self) -> None:
        run_id = self.engine.create_run("add a feature", repository=self.repo, policy=self.policy(default_validators=[PASS]))["run_id"]
        final = self.engine.run_loop(run_id, max_ticks=60)
        self.assertEqual(final["state"], "COMPLETE", final["state_reason"])
        record = self.engine.load(run_id)
        self.assertEqual(record["nodes"]["plan"]["role"], "planner")
        self.assertIn("impl", record["integration"]["merged"])
        self.assertEqual(record["nodes"]["impl"]["depends_on"], ["plan"])

    def test_model_planner_cannot_inject_shell_commands(self) -> None:
        def script(request, call):
            return {"structured": {"status": "done", "tasks": [{"id": "x", "goal": "g", "execution_path": "deterministic", "command": "rm -rf /"}]}}

        synthetic.SCRIPTS["alpha"] = script
        synthetic.SCRIPTS["beta"] = script
        run_id = self.engine.create_run("goal", repository=self.repo, policy=self.policy(max_stage_retries=0))["run_id"]
        final = self.engine.run_loop(run_id, max_ticks=20)
        self.assertEqual(final["state"], "BLOCKED")
        self.assertNotIn("x", self.engine.load(run_id)["nodes"])

    def test_single_driver_per_run(self) -> None:
        run_id = self.create([self.task("a")])
        self.engine.store.driver_path(run_id).parent.mkdir(parents=True, exist_ok=True)
        # Another live process (our parent) claims to drive this run.
        self.engine.store.driver_path(run_id).write_text(json.dumps({"pid": os.getppid(), "owner": "gui"}), encoding="utf-8")
        with self.assertRaises(OrchestratorError):
            self.engine.run_loop(run_id, max_ticks=1)


# ---------------------------------------------------------------------------
# Review, repair, validation, integration
# ---------------------------------------------------------------------------


class ReviewAndIntegrationTests(OrchestratorFixture):
    def reviewer_script(self, rounds: list[dict]):
        state = {"round": 0}

        def script(request, call):
            if request.role == "reviewer":
                result = rounds[min(state["round"], len(rounds) - 1)]
                state["round"] += 1
                return {"structured": result}
            if request.role == "repairer":
                return {"edits": {"a/fixed.txt": "fixed\n"}, "structured": {"status": "done", "dispositions": [{"id": "R1-1", "disposition": "fixed"}]}}
            return {"edits": {"a/impl.txt": "impl\n"}, "structured": {"status": "done"}}

        return script

    def test_cross_review_is_structured_and_material_findings_route_to_repair(self) -> None:
        finding = {"id": "1", "severity": "high", "path": "a/impl.txt", "summary": "missing null check", "evidence": "line 1", "recommended_action": "add a guard"}
        script = self.reviewer_script([
            {"status": "done", "verdict": "changes_requested", "findings": [finding]},
            {"status": "done", "verdict": "approved", "findings": []},
        ])
        synthetic.SCRIPTS["alpha"] = script
        synthetic.SCRIPTS["beta"] = script
        run_id = self.create([self.task("a")])
        final = self.engine.run_loop(run_id, max_ticks=60)
        self.assertEqual(final["state"], "COMPLETE", final["state_reason"])
        record = self.engine.load(run_id)
        a = record["nodes"]["a"]
        self.assertEqual(a["review"]["rounds"], 2)
        first = a["review"]["findings"][0]
        for key in ("id", "severity", "path", "summary", "evidence", "recommended_action", "disposition", "validator_needed"):
            self.assertIn(key, first)
        self.assertEqual(first["disposition"], "fixed")
        repair = record["nodes"]["a.repair1"]
        self.assertEqual(repair["role"], "repairer")
        self.assertEqual(repair["worktree"]["path"], a["worktree"]["path"], "repair continues in the author's worktree")
        self.assertTrue(repair["validation"]["passed"], "repaired work is revalidated")
        author = a["selection"]["provider"]
        for review in a["review"]["reviewers"]:
            self.assertNotEqual(review["provider"], author)
        self.assertEqual(self.git("show", f"{record['integration']['branch']}:a/fixed.txt"), "fixed\n")

    def test_looks_good_is_not_a_review(self) -> None:
        def script(request, call):
            if request.role == "reviewer":
                return {"structured": None, "summary": "looks good to me"}
            return {"edits": {"a/x.txt": "x\n"}, "structured": {"status": "done"}}

        synthetic.SCRIPTS["alpha"] = script
        synthetic.SCRIPTS["beta"] = script
        run_id = self.create([self.task("a")], max_stage_retries=1)
        final = self.engine.run_loop(run_id, max_ticks=30)
        self.assertEqual(final["state"], "BLOCKED")
        self.assertFalse(self.node(run_id, "a")["integrated"])
        self.assertEqual(self.node(run_id, "a.review1")["failures"][0]["kind"], "malformed")

    def test_unresolved_findings_after_max_rounds_require_approval(self) -> None:
        finding = {"id": "1", "severity": "critical", "summary": "unsafe"}
        script = self.reviewer_script([{"status": "done", "verdict": "changes_requested", "findings": [finding]}])
        synthetic.SCRIPTS["alpha"] = script
        synthetic.SCRIPTS["beta"] = script
        run_id = self.create([self.task("a")], max_review_rounds=1)
        stopped = self.engine.run_loop(run_id, max_ticks=30)
        self.assertEqual(stopped["state"], "APPROVAL_REQUIRED")
        self.assertEqual(stopped["gates"][0]["kind"], "unresolved_review_findings")
        self.assertFalse(self.node(run_id, "a")["integrated"])

    def test_self_reported_success_cannot_bypass_validators(self) -> None:
        failing = {"kind": "command", "command": [sys.executable, "-c", "import pathlib,sys; sys.exit('BUG' in pathlib.Path('a/impl.txt').read_text())"]}

        def script(request, call):
            if request.role == "reviewer":
                return {"structured": {"status": "done", "verdict": "approved", "findings": []}}
            return {"edits": {"a/impl.txt": "BUG\n"}, "structured": {"status": "done", "summary": "all tests pass, definitely done"}}

        synthetic.SCRIPTS["alpha"] = script
        synthetic.SCRIPTS["beta"] = script
        run_id = self.create([self.task("a", validators=[failing])], max_escalations=0)
        final = self.engine.run_loop(run_id, max_ticks=30)
        a = self.node(run_id, "a")
        self.assertEqual(a["result"]["self_reported_status"], "done")
        self.assertFalse(a["validation"]["passed"])
        self.assertNotEqual(a["state"], "PASSED")
        self.assertFalse(a["integrated"])
        self.assertEqual(final["state"], "BLOCKED")
        self.assertEqual(final["integration"]["merged"], [])

    def test_integration_refuses_unvalidated_work(self) -> None:
        run_id = self.create([self.task("a", validators=[])])
        stopped = self.engine.run_loop(run_id, max_ticks=30)
        self.assertEqual(stopped["state"], "APPROVAL_REQUIRED")
        gate = stopped["gates"][-1]
        self.assertEqual(gate["kind"], "policy_restricted_action")
        self.assertFalse(self.node(run_id, "a")["integrated"])
        self.engine.decide(run_id, gate["id"], approve=False)
        self.assertEqual(self.engine.run_loop(run_id, max_ticks=10)["state"], "BLOCKED")
        self.assertFalse(self.node(run_id, "a")["integrated"])

    def test_integration_guard_refuses_a_forged_pass(self) -> None:
        run_id = self.create([self.task("a")], require_independent_review_for_model_edits=False)
        self.engine.start(run_id)
        self.engine.step(run_id)
        record = self.engine.load(run_id)
        record["nodes"]["a"]["state"] = "PASSED"
        record["nodes"]["a"]["validation"] = {"passed": False, "declared_validators": 1, "evidence": []}
        record["nodes"]["a"]["integrated"] = False
        self.engine.store.save(record)
        # a was only launched in the first tick; the forged PASSED record must
        # still be refused at integration.
        self.engine.step(run_id)
        a = self.node(run_id, "a")
        self.assertFalse(a["integrated"])
        self.assertEqual(a["state"], "FAILED_FINAL")
        self.assertIn("integration refused", a["wait_reason"])

    def test_merge_conflict_opens_gate_and_approval_redoes_on_integration_head(self) -> None:
        synthetic.SCRIPTS["beta"] = lambda request, call: {"ticks": 1, "structured": {"status": "done", "verdict": "approved", "findings": []}}
        synthetic.SCRIPTS["alpha"] = lambda request, call: {"edits": {"a/shared.txt": f"from worker {call}\n"}, "structured": {"status": "done"}}
        run_id = self.create([self.task("a")])
        self.engine.start(run_id)
        for _ in range(3):
            self.engine.step(run_id)
            if self.node(run_id, "a")["state"] == "WAITING_FOR_REVIEW":
                break
        record = self.engine.load(run_id)
        integration = Path(record["integration"]["path"])
        (integration / "a").mkdir(exist_ok=True)
        (integration / "a" / "shared.txt").write_text("landed elsewhere\n", encoding="utf-8")
        git(["add", "-A"], integration)
        git(["commit", "-m", "concurrent change"], integration, identity=True)
        stopped = self.engine.run_loop(run_id, max_ticks=20)
        self.assertEqual(stopped["state"], "APPROVAL_REQUIRED")
        gate = stopped["gates"][-1]
        self.assertEqual(gate["kind"], "semantic_merge_conflict")
        self.assertIn("a/shared.txt", gate["reason"])
        old_branch = self.node(run_id, "a")["worktree"]["branch"]
        self.engine.decide(run_id, gate["id"], approve=True)
        final = self.engine.run_loop(run_id, max_ticks=40)
        self.assertEqual(final["state"], "COMPLETE", final["state_reason"])
        a = self.node(run_id, "a")
        self.assertNotEqual(a["worktree"]["branch"], old_branch)
        self.assertIn(old_branch, self.git("branch", "--list", old_branch), "the conflicting branch is kept for inspection")

    def test_failed_completion_validator_schedules_a_bounded_fix(self) -> None:
        completion = {"kind": "outputs_present", "outputs": ["FINAL.md"]}

        def script(request, call):
            if request.role == "reviewer":
                return {"structured": {"status": "done", "verdict": "approved", "findings": []}}
            if request.node_id.startswith("final-fix"):
                return {"edits": {"FINAL.md": "done\n"}, "structured": {"status": "done"}}
            return {"edits": {"a/x.txt": "x\n"}, "structured": {"status": "done"}}

        synthetic.SCRIPTS["alpha"] = script
        synthetic.SCRIPTS["beta"] = script
        run_id = self.create([self.task("a")], completion_validators=[completion])
        final = self.engine.run_loop(run_id, max_ticks=60)
        self.assertEqual(final["state"], "COMPLETE", final["state_reason"])
        self.assertIn("final-fix1", final["integration"]["merged"])

    def test_merge_to_base_requires_approval_then_fast_forwards(self) -> None:
        run_id = self.create([self.task("a")], final_integration="merge_to_base")
        stopped = self.engine.run_loop(run_id, max_ticks=40)
        self.assertEqual(stopped["state"], "APPROVAL_REQUIRED")
        gate = stopped["gates"][-1]
        self.assertEqual(gate["kind"], "consequential_repository_write")
        base_before = self.git("rev-parse", "main").strip()
        self.assertEqual(base_before, stopped["base_commit"], "nothing lands before approval")
        done = self.engine.decide(run_id, gate["id"], approve=True)
        self.assertEqual(done["state"], "COMPLETE")
        self.assertTrue(done["final"]["landed"]["ok"], done["final"]["landed"])
        self.assertEqual(self.git("rev-parse", "main").strip(), done["integration"]["head"])
        self.assertTrue((self.repo / "a").exists())


# ---------------------------------------------------------------------------
# Provider neutrality, privacy, adapters, policy
# ---------------------------------------------------------------------------


class NeutralityAndPrivacyTests(OrchestratorFixture):
    CORE = [
        "__init__.py", "model.py", "store.py", "router.py", "engine.py", "planner.py",
        "prompts.py", "review.py", "validators.py", "worktrees.py", "service.py",
        "adapters/base.py", "adapters/synthetic.py",
    ]
    VENDOR_TERMS = ("claude", "anthropic", "openai", "gpt", "codex", "gemini", "llama", "mistral", "sonnet", "opus", "haiku", "fable")

    def test_core_modules_name_no_provider_model_or_cli_syntax(self) -> None:
        root = ROOT / "src" / "agent_os" / "orchestrator"
        for relative in self.CORE:
            path = root / relative
            if not path.exists():
                continue
            text = path.read_text(encoding="utf-8").casefold()
            for term in self.VENDOR_TERMS:
                self.assertNotIn(term, text, f"{relative} names '{term}'")
            for flag in ("--model", "--effort", "--permission-mode", "model_reasoning_effort", "--sandbox"):
                if relative == "adapters/synthetic.py":
                    continue
                self.assertNotIn(flag, text, f"{relative} contains CLI syntax {flag}")

    def test_run_state_refuses_transcripts_and_redacts_secrets(self) -> None:
        run_id = self.create([self.task("a")])
        record = self.engine.load(run_id)
        record["nodes"]["a"]["transcript"] = ["hello"]
        with self.assertRaises(StoreError):
            self.engine.store.save(record)
        record = self.engine.load(run_id)
        record["goal"] = "use key sk-ant-abcdefghijklmnopqrstuvwxyz0123 and password=hunter2"
        self.engine.store.save(record)
        text = self.engine.store.state_path(run_id).read_text(encoding="utf-8")
        self.assertNotIn("abcdefghijklmnopqrstuvwxyz0123", text)
        self.assertNotIn("hunter2", text)
        self.assertEqual(redact("token ghp_" + "a" * 30), "token [redacted]")

    def test_completed_run_state_holds_no_prompt_text(self) -> None:
        marker = "UNIQUE-PROMPT-MARKER-7731"
        run_id = self.engine.create_run(f"goal {marker}", repository=self.repo, tasks=[self.task("a", goal=f"do {marker}")], policy=self.policy())["run_id"]
        self.engine.run_loop(run_id, max_ticks=30)
        state = self.engine.store.state_path(run_id).read_text(encoding="utf-8")
        self.assertNotIn("Rules:", state)
        self.assertNotIn("agent-os-result", state)
        for key in ("transcript", "messages", "conversation", '"history"'):
            self.assertNotIn(key, state)

    def test_store_rejects_canonical_repository_location(self) -> None:
        with self.assertRaises(StoreError):
            RunStore(ROOT / "projects" / "orchestrator-state")

    def test_telemetry_records_metadata_only(self) -> None:
        run_id = self.create([self.task("a")])
        self.engine.run_loop(run_id, max_ticks=30)
        events = [json.loads(line) for line in self.telemetry_path.read_text(encoding="utf-8").splitlines()]
        self.assertTrue(events)
        allowed = {"schema_version", "event_id", "occurred_at", "project_id", "task_category", "capability_class", "execution_path", "provider", "model", "input_tokens", "cached_tokens", "output_tokens", "duration_ms", "retries", "validator_passed", "escalations", "correction_or_override", "reasoning_tokens", "items_processed"}
        for event in events:
            self.assertLessEqual(set(event), allowed)
        self.assertIn("orchestrator-implementer", {event["task_category"] for event in events})

    def test_policy_rejects_unknown_keys_and_shared_worktrees(self) -> None:
        with self.assertRaises(PolicyError):
            merge_policy({"surprise": True})
        with self.assertRaises(PolicyError):
            merge_policy({"require_isolated_worktrees": False})

    def test_plan_rejects_cycles_and_unknown_dependencies(self) -> None:
        with self.assertRaises(PlanError):
            self.create([self.task("a", depends_on=["b"]), self.task("b", depends_on=["a"])])
        with self.assertRaises(PlanError):
            self.create([self.task("a", depends_on=["missing"])])

    def test_claims_are_announced_and_released_through_coordination(self) -> None:
        with mock.patch("agent_os.registry.identify_project", return_value={"id": "fixture-project"}):
            run_id = self.engine.create_run("goal", repository=self.repo, tasks=[self.task("a")], policy=self.policy(announce_claims=True))["run_id"]
        self.engine.run_loop(run_id, max_ticks=30)
        claims = json.loads(self.claims.read_text(encoding="utf-8"))["claims"]
        self.assertTrue(claims)
        self.assertTrue(all(item["status"] == "released" for item in claims))
        self.assertEqual(claims[0]["scope"], ["a"])


class AdapterTests(unittest.TestCase):
    def request(self, tmp: Path, **extra) -> AgentLaunchRequest:
        prompt = tmp / "prompt.md"
        prompt.write_text("do it", encoding="utf-8")
        values = dict(
            run_id="r", node_id="n", role="implementer", cwd=str(tmp), prompt_path=str(prompt), output_dir=str(tmp / "out"),
            capability_class="reasoning", effort="high", model="model-x", provider_effort="high", read_only=False,
        )
        values.update(extra)
        return AgentLaunchRequest(**values)

    def with_probe(self, adapter, flags):
        adapter._probe = ProviderStatus(adapter.provider["id"], True, executable="/bin/tool", version="1", features={flag: True for flag in flags})
        return adapter

    def test_claude_code_invocation_applies_model_effort_and_permissions(self) -> None:
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp, True)
        from agent_os.orchestrator.adapters.claude_code import OPTIONAL_FLAGS

        adapter = self.with_probe(ClaudeCodeAdapter({"id": "cc", "options": {}, "env_allowlist": []}), OPTIONAL_FLAGS)
        plan = adapter.resolve_invocation(self.request(tmp))
        self.assertEqual(plan.argv[:5], ["-p", "--output-format", "json", "--model", "model-x"])
        self.assertIn("--effort", plan.argv)
        self.assertEqual(plan.argv[plan.argv.index("--effort") + 1], "high")
        self.assertEqual(plan.argv[plan.argv.index("--permission-mode") + 1], "acceptEdits")
        review = adapter.resolve_invocation(self.request(tmp, read_only=True))
        self.assertEqual(review.argv[review.argv.index("--permission-mode") + 1], "plan")
        self.assertEqual(plan.stdin_path, str(tmp / "prompt.md"))

    def test_claude_code_omits_flags_the_installed_cli_does_not_advertise(self) -> None:
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp, True)
        adapter = self.with_probe(ClaudeCodeAdapter({"id": "cc", "options": {}}), [])
        plan = adapter.resolve_invocation(self.request(tmp))
        self.assertNotIn("--effort", plan.argv)

    def test_codex_invocation_applies_model_effort_and_sandbox(self) -> None:
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp, True)
        from agent_os.orchestrator.adapters.codex_cli import OPTIONAL_FLAGS

        adapter = self.with_probe(CodexCliAdapter({"id": "cx", "options": {}}), OPTIONAL_FLAGS)
        plan = adapter.resolve_invocation(self.request(tmp, provider_effort="medium"))
        self.assertEqual(plan.argv[:3], ["exec", "-m", "model-x"])
        self.assertIn('model_reasoning_effort="medium"', plan.argv)
        self.assertEqual(plan.argv[plan.argv.index("-s") + 1], "workspace-write")
        self.assertEqual(plan.argv[-1], "-")
        review = adapter.resolve_invocation(self.request(tmp, read_only=True))
        self.assertEqual(review.argv[review.argv.index("-s") + 1], "read-only")

    def test_result_parsing_classifies_success_quota_and_invalid_model(self) -> None:
        handle = RunningAgent("cc", "n", None, 0.0, "", "", "", None, "")
        adapter = ClaudeCodeAdapter({"id": "cc"})
        ok = adapter.parse_result(handle, 0, json.dumps({"type": "result", "subtype": "success", "is_error": False, "result": "done\n```agent-os-result\n{\"status\": \"done\"}\n```", "usage": {"input_tokens": 5, "output_tokens": 2}}), "")
        self.assertEqual((ok.outcome, ok.structured), ("completed", {"status": "done"}))
        quota = adapter.parse_result(handle, 1, json.dumps({"is_error": True, "subtype": "error", "result": "Claude AI usage limit reached"}), "")
        self.assertEqual(quota.failure_kind, "quota")
        codex = CodexCliAdapter({"id": "cx"})
        bad_model = codex.parse_result(handle, 1, json.dumps({"type": "error", "message": "The model `nope` does not exist"}), "")
        self.assertEqual(bad_model.failure_kind, "invalid_model")
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp, True)
        last = tmp / "last.md"
        last.write_text("ok\n```agent-os-result\n{\"status\": \"done\", \"verdict\": \"approved\", \"findings\": []}\n```", encoding="utf-8")
        handle_with_file = RunningAgent("cx", "n", None, 0.0, "", "", "", str(last), "")
        events = "\n".join(json.dumps(item) for item in ({"type": "turn.completed", "usage": {"input_tokens": 9, "cached_input_tokens": 3, "output_tokens": 4}},))
        done = codex.parse_result(handle_with_file, 0, events, "")
        self.assertEqual(done.structured["verdict"], "approved")
        self.assertEqual(done.usage["cached_tokens"], 3)

    def test_environment_is_allowlisted(self) -> None:
        from agent_os.orchestrator.adapters.base import build_env

        with mock.patch.dict(os.environ, {"UNRELATED_SECRET_TOKEN": "x", "ANTHROPIC_API_KEY": "y", "PATH": os.environ.get("PATH", "")}):
            env = build_env([], [], ("ANTHROPIC_",))
        self.assertNotIn("UNRELATED_SECRET_TOKEN", env)
        self.assertIn("ANTHROPIC_API_KEY", env)


if __name__ == "__main__":
    unittest.main()
