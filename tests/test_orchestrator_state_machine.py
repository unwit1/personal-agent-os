"""IMP-0007: the orchestrator as a state machine.

Random operation sequences (worker outcomes, ticks, pause/resume/stop, gate
decisions, retries, crash-restarts) drive a real engine with synthetic
workers, and the constitution section 10 invariants are checked after every
operation. Two drivers share one harness:

* a subsumed seeded random-sequence runner with delta-debugging shrinking
  (always runs; no dependency);
* Hypothesis ``RuleBasedStateMachine`` (runs only where the dev-only
  ``hypothesis`` package is installed; prior art PA-hypothesis).

``AGENT_OS_SM_SEEDS`` / ``AGENT_OS_SM_OPS`` scale the random runner.
"""

from __future__ import annotations

import os
import random
import shutil
import subprocess
import sys
import tempfile
import unittest
from collections import deque
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from agent_os.orchestrator.adapters import synthetic  # noqa: E402
from agent_os.orchestrator.engine import Orchestrator, OrchestratorError  # noqa: E402
from agent_os.orchestrator.router import ProviderRegistry  # noqa: E402
from agent_os.orchestrator.store import RunStore  # noqa: E402
from agent_os.telemetry import LocalTelemetryStore  # noqa: E402

from test_orchestrator import PASS, provider  # noqa: E402

WORKER_OUTCOMES = ("ok", "ok", "ok", "out_of_scope", "crash", "quota", "no_change")
REVIEW_OUTCOMES = ("approve", "approve", "reject")
TERMINAL = {"COMPLETE", "FAILED"}


class _ProcessDeath(BaseException):
    """Simulated crash; BaseException so engine error handling cannot absorb it."""


class Harness:
    """One throwaway repository + engine; operations and invariants."""

    def __init__(self) -> None:
        synthetic.reset()
        self.tmp = Path(tempfile.mkdtemp(prefix="agent-os-sm-"))
        self.repo = self.tmp / "repo"
        self.repo.mkdir()
        self._git("init", "-b", "main")
        for folder in ("a", "b"):
            (self.repo / folder).mkdir()
            (self.repo / folder / ".keep").write_text("", encoding="utf-8")
        self._git("add", "-A")
        self._git("commit", "-m", "init")
        self.main_head = self._git("rev-parse", "main").strip()
        self.queue: deque[str] = deque()
        self.reviews: deque[str] = deque()
        for name in ("alpha", "beta"):
            synthetic.SCRIPTS[name] = self._script
        self.engine = self._engine()
        tasks = [{"id": "a", "goal": "work on a", "scope": ["a"], "validators": [PASS]},
                 {"id": "b", "goal": "work on b", "scope": ["b"], "validators": [PASS], "depends_on": ["a"]}]
        self.run_id = self.engine.create_run("state machine", repository=self.repo, tasks=tasks,
                                             policy={"poll_interval_seconds": 0, "announce_claims": False, "max_launches": 30})["run_id"]
        self.initial_policy = dict(self.engine.load(self.run_id)["policy"])
        self.trace: list[str] = []
        self.crashes = 0

    def _arm_merge_crash(self) -> None:
        from agent_os.orchestrator import worktrees

        original = worktrees.WorktreeManager.merge
        harness = self

        def merge_then_die(manager, branch, message):
            outcome = original(manager, branch, message)
            worktrees.WorktreeManager.merge = original  # one crash only
            if outcome.get("merged"):
                harness.crashes += 1
                raise _ProcessDeath("killed after merge, before persist")
            return outcome

        worktrees.WorktreeManager.merge = merge_then_die
        self._restore_merge = original

    def close(self) -> None:
        if getattr(self, "_restore_merge", None) is not None:
            from agent_os.orchestrator import worktrees

            worktrees.WorktreeManager.merge = self._restore_merge
        synthetic.reset()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _git(self, *args: str) -> str:
        return subprocess.run(["git", "-c", "user.name=f", "-c", "user.email=f@x", *args], cwd=self.repo, check=True, capture_output=True, text=True).stdout

    def _engine(self) -> Orchestrator:
        registry = ProviderRegistry(providers=[provider("alpha"), provider("beta")])
        return Orchestrator(RunStore(self.tmp / "home"), registry=registry, telemetry_store=LocalTelemetryStore(self.tmp / "t.jsonl"),
                            claims_path=self.tmp / "claims.json", sleep=lambda seconds: None)

    def _script(self, request, call):
        if request.role == "reviewer":
            outcome = self.reviews.popleft() if self.reviews else "approve"
            if outcome == "reject":
                return {"structured": {"status": "done", "verdict": "changes_requested", "findings": [{"id": "F1", "severity": "high", "summary": "wrong", "path": "x"}]}}
            return {"structured": {"status": "done", "verdict": "approved", "findings": []}}
        base = request.node_id.split(".")[0]
        outcome = self.queue.popleft() if self.queue else "ok"
        if outcome == "crash":
            return {"failure": "failed", "detail": "worker crashed"}
        if outcome == "quota":
            return {"failure": "quota", "detail": "usage limit"}
        if outcome == "unavailable":
            return {"failure": "unavailable", "detail": "provider unreachable"}
        if outcome == "no_change":
            return {"structured": {"status": "done", "summary": "nothing"}}
        target = f"{base}/{request.node_id}-{call}.txt" if outcome == "ok" else f"outside-{call}.txt"
        return {"edits": {target: "change\n"}, "structured": {"status": "done", "summary": "edited"}}

    # ---- operations ---------------------------------------------------
    def apply(self, op: str) -> None:
        self.trace.append(op)
        kind, _, arg = op.partition(":")
        run = self.run_id
        try:
            if kind == "worker":
                self.queue.append(arg)
            elif kind == "review":
                self.reviews.append(arg)
            elif kind == "start":
                self.engine.start(run)
            elif kind == "step":
                self.engine.step(run)
            elif kind == "pause":
                self.engine.pause(run)
            elif kind == "resume":
                self.engine.resume(run)
            elif kind == "stop":
                self.engine.stop(run)
            elif kind in {"approve", "reject"}:
                gates = [gate for gate in self.engine.load(run)["gates"] if gate["status"] == "open"]
                if gates:
                    self.engine.decide(run, gates[0]["id"], approve=kind == "approve")
            elif kind == "retry":
                record = self.engine.load(run)
                failed = [node_id for node_id, node in record["nodes"].items() if node["state"] in {"FAILED_FINAL", "FAILED_RETRYABLE"}]
                if failed:
                    self.engine.retry(run, failed[0])
            elif kind == "restart":
                # Crash kill-point: in-flight workers die with the process.
                synthetic._LIVE.clear()
                self.engine = self._engine()
            elif kind == "crash_after_merge":
                # Kill-point between a consequential effect (integration merge
                # commit) and persisting the run record: the next merge lands,
                # then the "process" dies before the engine saves, and a fresh
                # engine resumes from the stale record.
                self._arm_merge_crash()
        except OrchestratorError:
            pass  # an operation refused in this state is legal; invariants still apply
        except _ProcessDeath:
            synthetic._LIVE.clear()
            self.engine = self._engine()

    # ---- invariants (constitution section 10) --------------------------
    def check(self) -> list[str]:
        record = self.engine.load(self.run_id)
        policy_now = record["policy"]
        problems = []
        for node_id, node in record["nodes"].items():
            if node["integrated"]:
                if node["role"] not in {"implementer", "test_author"}:
                    problems.append(f"{node_id}: role {node['role']} was integrated (read-only roles must never write)")
                if not (node.get("validation") or {}).get("passed"):
                    problems.append(f"{node_id}: integrated without passing validation")
                if node["state"] in {"FAILED_FINAL", "CANCELLED", "FAILED_RETRYABLE"}:
                    problems.append(f"{node_id}: integrated while {node['state']}")
                review = node.get("review") or {}
                reviewers = review.get("reviewers") or []
                # review_required None means "policy default" (model edits
                # need independent review); resolving it matters: a check on
                # the raw field was vacuous and missed a planted bug (EXP-0003).
                required = node.get("review_required")
                if required is None:
                    required = bool(policy_now.get("require_independent_review_for_model_edits")) and node.get("execution_path") != "deterministic"
                if (required or reviewers) and not review.get("accepted_by_user") and (not reviewers or reviewers[-1].get("verdict") != "approved"):
                    problems.append(f"{node_id}: integrated without an approving review")
        branch = (record.get("integration") or {}).get("branch")
        if branch:
            subjects = self._git("log", branch, "--format=%s").splitlines()
            for node_id in record["nodes"]:
                count = sum(1 for line in subjects if line == f"agent-os {self.run_id}: integrate {node_id}")
                if count > 1:
                    problems.append(f"{node_id}: merged {count} times into the integration branch (duplicated consequential effect)")
        merged = list((record.get("integration") or {}).get("merged") or [])
        if len(merged) != len(set(merged)):
            problems.append(f"integration.merged has duplicates: {merged}")
        for node_id, node in record["nodes"].items():
            if node["integrated"] and node_id not in merged:
                problems.append(f"{node_id}: integrated but missing from integration.merged")
        if record["state"] == "COMPLETE" and not ((record.get("final") or {}).get("validation") or {}).get("passed"):
            problems.append("run COMPLETE without passing completion validation")
        if self._git("rev-parse", "main").strip() != self.main_head:
            problems.append("base branch main changed (final_integration=branch must never touch it)")
        policy = record["policy"]
        for key in ("validation_required_before_integration", "require_independent_review_for_model_edits", "protected_paths_allowed", "final_integration"):
            if policy.get(key) != self.initial_policy.get(key):
                problems.append(f"policy {key} changed from {self.initial_policy.get(key)!r} to {policy.get(key)!r}")
        if not set(self.initial_policy["approval_gates"]) <= set(policy["approval_gates"]):
            problems.append("approval gates were removed")
        return problems


def random_ops(rng: random.Random, count: int) -> list[str]:
    """Half the sequences are 'hostile' (frequent review rejections and worker
    failures) so review-exhaustion gates, failure states and gate decisions
    are reached, not just the happy path."""
    hostile = rng.random() < 0.5
    workers = ("ok", "out_of_scope", "crash", "quota", "unavailable", "no_change") if hostile else WORKER_OUTCOMES
    reviews = ("approve", "reject", "reject") if hostile else REVIEW_OUTCOMES
    ops = ["start"]
    menu = ["step"] * 10 + ["worker"] * 3 + ["review"] * (5 if hostile else 2) + ["pause", "resume", "resume", "approve", "approve", "reject", "retry", "restart", "crash_after_merge"]
    if rng.random() < 0.3:
        menu.append("stop")
    for _ in range(count):
        kind = rng.choice(menu)
        if kind == "worker":
            ops.append(f"worker:{rng.choice(workers)}")
        elif kind == "review":
            ops.append(f"review:{rng.choice(reviews)}")
        else:
            ops.append(kind)
    return ops


def violations(ops: list[str]) -> list[str]:
    harness = Harness()
    try:
        for op in ops:
            harness.apply(op)
            problems = harness.check()
            if problems:
                return problems
        return []
    finally:
        harness.close()


def shrink(ops: list[str]) -> list[str]:
    """Delta-debugging lite: drop chunks, then single ops, while it still fails."""
    current = list(ops)
    chunk = max(1, len(current) // 2)
    while chunk >= 1:
        index, changed = 0, False
        while index < len(current):
            candidate = current[:index] + current[index + chunk:]
            if candidate and violations(candidate):
                current, changed = candidate, True
            else:
                index += chunk
        if not changed:
            chunk //= 2
    return current


class RandomSequenceInvariantTests(unittest.TestCase):
    def test_invariants_hold_over_random_operation_sequences(self) -> None:
        seeds = int(os.environ.get("AGENT_OS_SM_SEEDS", "6"))
        count = int(os.environ.get("AGENT_OS_SM_OPS", "30"))
        for seed in range(seeds):
            ops = random_ops(random.Random(seed), count)
            problems = violations(ops)
            if problems:
                minimal = shrink(ops)
                self.fail(f"seed {seed}: {problems[0]}\nminimal sequence ({len(minimal)} ops): {minimal}")

    def test_harness_detects_a_planted_violation(self) -> None:
        # The invariant checker must be able to fail: plant an integrated
        # reviewer node and expect a report.
        harness = Harness()
        try:
            record = harness.engine.load(harness.run_id)
            node = next(iter(record["nodes"].values()))
            node.update(role="reviewer", integrated=True)
            harness.engine.store.save(record)
            self.assertTrue(any("read-only" in item for item in harness.check()))
        finally:
            harness.close()

    def test_harness_detects_a_planted_duplicate_merge(self) -> None:
        harness = Harness()
        try:
            for op in ["start"] + ["step"] * 12:
                harness.apply(op)
            record = harness.engine.load(harness.run_id)
            branch = record["integration"]["branch"]
            integrated = [node_id for node_id, node in record["nodes"].items() if node["integrated"]]
            self.assertTrue(branch and integrated, "setup did not integrate anything")
            # Plant with plumbing: the integration worktree may already be
            # cleaned up, but the branch remains.
            tree = harness._git("rev-parse", f"{branch}^{{tree}}").strip()
            head = harness._git("rev-parse", branch).strip()
            duplicate = harness._git("commit-tree", tree, "-p", head, "-m", f"agent-os {harness.run_id}: integrate {integrated[0]}").strip()
            harness._git("update-ref", f"refs/heads/{branch}", duplicate)
            self.assertTrue(any("merged 2 times" in item for item in harness.check()))
        finally:
            harness.close()

    def test_crash_after_merge_is_adopted_not_repeated(self) -> None:
        """Regression (IMP-0012): a merge that landed before the process died is
        adopted on resume through its idempotency key, never merged again."""
        harness = Harness()
        try:
            harness.apply("start")
            harness.apply("crash_after_merge")
            for _ in range(40):
                harness.apply("step")
                self.assertEqual(harness.check(), [])
            self.assertEqual(harness.crashes, 1, "the kill-point did not fire")
            events = [event.get("type") or event.get("kind") for event in harness.engine.events(harness.run_id, limit=1000)]
            self.assertIn("integration.recovered", events)
            record = harness.engine.load(harness.run_id)
            subjects = harness._git("log", record["integration"]["branch"], "--format=%s").splitlines()
            for node_id, node in record["nodes"].items():
                if node["integrated"]:
                    self.assertEqual(subjects.count(f"agent-os {harness.run_id}: integrate {node_id}"), 1)
        finally:
            harness.close()

    def test_shrinker_minimizes(self) -> None:
        import unittest.mock as mock

        def fake(ops):
            return ["bad"] if "restart" in ops and "stop" in ops else []

        with mock.patch(f"{__name__}.violations", side_effect=fake):
            self.assertEqual(sorted(shrink(["start", "step", "restart", "step", "stop", "step"])), ["restart", "stop"])


try:
    from hypothesis import HealthCheck, settings
    from hypothesis import strategies as st
    from hypothesis.stateful import RuleBasedStateMachine, invariant, rule

    class OrchestratorMachine(RuleBasedStateMachine):
        def __init__(self) -> None:
            super().__init__()
            self.h = Harness()
            self.h.apply("start")

        def teardown(self) -> None:
            self.h.close()

        @rule(outcome=st.sampled_from(WORKER_OUTCOMES))
        def worker(self, outcome):
            self.h.apply(f"worker:{outcome}")

        @rule(outcome=st.sampled_from(REVIEW_OUTCOMES))
        def review(self, outcome):
            self.h.apply(f"review:{outcome}")

        @rule(op=st.sampled_from(["step", "step", "step", "pause", "resume", "stop", "approve", "reject", "retry", "restart"]))
        def control(self, op):
            self.h.apply(op)

        @invariant()
        def constitution_invariants(self):
            problems = self.h.check()
            assert not problems, problems

    OrchestratorMachine.TestCase.settings = settings(max_examples=int(os.environ.get("AGENT_OS_SM_EXAMPLES", "15")), stateful_step_count=25, deadline=None,
                                                     suppress_health_check=[HealthCheck.too_slow])
    HypothesisStateMachineTests = OrchestratorMachine.TestCase
except ImportError:  # dev-only dependency absent: the subsumed runner still covers the invariants
    class HypothesisStateMachineTests(unittest.TestCase):
        def test_hypothesis_not_installed(self) -> None:
            self.skipTest("hypothesis not installed (dev-only extra)")


if __name__ == "__main__":
    unittest.main()
