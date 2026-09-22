from __future__ import annotations

import json
import shutil
import sys
import unittest
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os import coordination
from agent_os.paths import ROOT


class ClaimFixture(unittest.TestCase):
    """Each test gets its own registry; none touches the machine's real one."""

    def setUp(self) -> None:
        scratch = ROOT / ".tmp"
        scratch.mkdir(exist_ok=True)
        self.directory = scratch / f"claims-{uuid.uuid4()}"
        self.directory.mkdir()
        self.registry = self.directory / "work-claims.json"
        self.addCleanup(shutil.rmtree, self.directory, True)

    def claim(self, agent: str, scope, task: str = "work", project: str = "demo", **kw):
        return coordination.claim(project, task, agent, scope, path=self.registry, **kw)


class OverlapTests(ClaimFixture):
    def test_a_first_claim_finds_clear_ground(self) -> None:
        result = self.claim("alpha", ["src/one.py"])
        self.assertEqual(result["conflicts"], [])
        self.assertIn("No one else", result["advice"])

    def test_two_agents_on_the_same_file_see_each_other(self) -> None:
        self.claim("alpha", ["src/one.py"], task="measuring a corpus")
        second = self.claim("beta", ["src/one.py"], task="refactoring")
        self.assertEqual(len(second["conflicts"]), 1)
        self.assertEqual(second["conflicts"][0]["agent"], "alpha")
        self.assertEqual(second["conflicts"][0]["task"], "measuring a corpus")

    def test_a_directory_claim_covers_files_beneath_it(self) -> None:
        """The real incident: one agent held a file, another took the tree."""
        self.claim("alpha", ["src/agent_os/cli.py"])
        second = self.claim("beta", ["src/agent_os"])
        self.assertEqual(len(second["conflicts"]), 1)

    def test_a_glob_and_a_path_recognise_each_other(self) -> None:
        self.claim("alpha", ["src/**/*.py"])
        second = self.claim("beta", ["src/agent_os/chat.py"])
        self.assertEqual(len(second["conflicts"]), 1)

    def test_unrelated_scopes_do_not_conflict(self) -> None:
        self.claim("alpha", ["docs/readme.md"])
        second = self.claim("beta", ["src/one.py"])
        self.assertEqual(second["conflicts"], [])

    def test_an_unscoped_claim_overlaps_everything(self) -> None:
        """Claiming nothing in particular means claiming the lot."""
        self.claim("alpha", None)
        second = self.claim("beta", ["src/deep/nested/file.py"])
        self.assertEqual(len(second["conflicts"]), 1)

    def test_different_projects_never_conflict(self) -> None:
        self.claim("alpha", ["src/one.py"], project="demo")
        second = coordination.claim("other", "work", "beta", ["src/one.py"], path=self.registry)
        self.assertEqual(second["conflicts"], [])

    def test_an_agent_does_not_conflict_with_itself(self) -> None:
        self.claim("alpha", ["src/one.py"])
        second = self.claim("alpha", ["src/one.py"])
        self.assertEqual(second["conflicts"], [])


class CheckTests(ClaimFixture):
    def test_check_reports_without_announcing(self) -> None:
        """Looking must not leave a footprint."""
        self.claim("alpha", ["src/one.py"])
        before = len(coordination.active_claims("demo", self.registry))
        result = coordination.check("demo", ["src/one.py"], path=self.registry)
        after = len(coordination.active_claims("demo", self.registry))
        self.assertFalse(result["clear"])
        self.assertEqual(before, after, "check() recorded a claim")

    def test_clear_ground_is_reported_as_clear(self) -> None:
        self.claim("alpha", ["src/one.py"])
        result = coordination.check("demo", ["docs/other.md"], path=self.registry)
        self.assertTrue(result["clear"])


class LeaseTests(ClaimFixture):
    def test_a_dead_agent_stops_blocking_the_repository(self) -> None:
        """A crashed session must not hold ground for ever."""
        self.claim("alpha", ["src/one.py"], lease_minutes=1)
        data = json.loads(self.registry.read_text(encoding="utf-8"))
        data["claims"][0]["heartbeat_epoch"] -= 3600  # an hour with no heartbeat
        self.registry.write_text(json.dumps(data), encoding="utf-8")

        second = self.claim("beta", ["src/one.py"])
        self.assertEqual(second["conflicts"], [], "an expired claim still blocked")
        remaining = {c["agent"] for c in coordination.active_claims("demo", self.registry)}
        self.assertNotIn("alpha", remaining)

    def test_a_heartbeat_keeps_a_claim_alive(self) -> None:
        first = self.claim("alpha", ["src/one.py"], lease_minutes=1)
        data = json.loads(self.registry.read_text(encoding="utf-8"))
        data["claims"][0]["heartbeat_epoch"] -= 30
        self.registry.write_text(json.dumps(data), encoding="utf-8")
        coordination.heartbeat(first["claim"]["claim_id"], path=self.registry)
        second = self.claim("beta", ["src/one.py"])
        self.assertEqual(len(second["conflicts"]), 1)

    def test_releasing_frees_the_ground(self) -> None:
        first = self.claim("alpha", ["src/one.py"])
        coordination.release(first["claim"]["claim_id"], "finished", path=self.registry)
        second = self.claim("beta", ["src/one.py"])
        self.assertEqual(second["conflicts"], [])


class MessageTests(ClaimFixture):
    def test_a_message_reaches_the_claim_holder_on_heartbeat(self) -> None:
        first = self.claim("alpha", ["src/one.py"])
        claim_id = first["claim"]["claim_id"]
        coordination.message(claim_id, "I need cli.py too - can we split it?",
                             sender="beta", path=self.registry)
        beat = coordination.heartbeat(claim_id, path=self.registry)
        self.assertEqual(len(beat["new_messages"]), 1)
        self.assertEqual(beat["new_messages"][0]["from"], "beta")

    def test_a_message_is_delivered_only_once(self) -> None:
        first = self.claim("alpha", ["src/one.py"])
        claim_id = first["claim"]["claim_id"]
        coordination.message(claim_id, "hello", sender="beta", path=self.registry)
        coordination.heartbeat(claim_id, path=self.registry)
        again = coordination.heartbeat(claim_id, path=self.registry)
        self.assertEqual(again["new_messages"], [])

    def test_messaging_an_unknown_claim_is_an_error(self) -> None:
        with self.assertRaises(KeyError):
            coordination.message("WC-nope", "hi", sender="beta", path=self.registry)


class DelegatedTaskTests(ClaimFixture):
    def test_delegation_is_stable_and_idempotent(self) -> None:
        first = coordination.delegate(
            "demo", "fixture-review", "Review synthetic fixture", "alpha",
            assignee="beta", scope=["src/agent_os"], path=self.registry,
        )
        second = coordination.delegate(
            "demo", "fixture-review", "A different duplicate title", "other",
            assignee="other", path=self.registry,
        )
        self.assertTrue(first["created"])
        self.assertFalse(second["created"])
        self.assertTrue(second["idempotent"])
        self.assertEqual(first["task"]["task_id"], second["task"]["task_id"])
        self.assertEqual(len(coordination.list_tasks("demo", path=self.registry)), 1)

    def test_review_gate_is_immutable_across_delegation_retries(self) -> None:
        normal = coordination.delegate("demo", "gate-normal", "Normal fixture", "alpha", path=self.registry)
        with self.assertRaisesRegex(ValueError, "review_required cannot change"):
            coordination.delegate(
                "demo", "gate-normal", "Normal fixture", "alpha", review_required=True, path=self.registry,
            )
        self.assertFalse(normal["task"]["review_required"])

        gated = coordination.delegate(
            "demo", "gate-enabled", "Gated fixture", "alpha", review_required=True, path=self.registry,
        )
        with self.assertRaisesRegex(ValueError, "review_required cannot change"):
            coordination.delegate(
                "demo", "gate-enabled", "Gated fixture", "alpha", review_required=False, path=self.registry,
            )
        self.assertTrue(gated["task"]["review_required"])

    def test_dependencies_block_claim_until_completed(self) -> None:
        prerequisite = coordination.delegate("demo", "prepare", "Prepare fixture", "alpha", path=self.registry)
        dependent = coordination.delegate(
            "demo", "review", "Review fixture", "alpha",
            depends_on=[prerequisite["task"]["task_id"]], path=self.registry,
        )
        blocked = coordination.claim_task(dependent["task"]["task_id"], "beta", path=self.registry)
        self.assertFalse(blocked["claimed"])
        self.assertEqual(blocked["blocked_by"], [prerequisite["task"]["task_id"]])

        coordination.claim_task(prerequisite["task"]["task_id"], "alpha", path=self.registry)
        coordination.complete_task(
            prerequisite["task"]["task_id"], "alpha", "synthetic validator passed", "fixture ready", path=self.registry
        )
        claimed = coordination.claim_task(dependent["task"]["task_id"], "beta", path=self.registry)
        self.assertTrue(claimed["claimed"])
        self.assertEqual(claimed["task"]["status"], "in_progress")

    def test_dependency_cycles_are_rejected_but_unknown_dependencies_can_wait(self) -> None:
        first_id = coordination._task_id("demo", "cycle-first")
        second_id = coordination._task_id("demo", "cycle-second")
        first = coordination.delegate(
            "demo", "cycle-first", "Cycle fixture", "alpha", depends_on=[second_id], path=self.registry,
        )
        self.assertEqual(first["task"]["depends_on"], [second_id])
        with self.assertRaisesRegex(ValueError, "must be acyclic"):
            coordination.delegate(
                "demo", "cycle-second", "Cycle fixture", "alpha", depends_on=[first_id], path=self.registry,
            )
        self.assertEqual(len(coordination.list_tasks("demo", path=self.registry)), 1)
        with self.assertRaisesRegex(ValueError, "must be acyclic"):
            coordination.delegate(
                "demo", "self-cycle", "Self cycle fixture", "alpha",
                depends_on=[coordination._task_id("demo", "self-cycle")], path=self.registry,
            )

    def test_normal_task_completes_without_review_gate(self) -> None:
        created = coordination.delegate("demo", "assigned", "Assigned fixture task", "alpha", assignee="beta", path=self.registry)
        task_id = created["task"]["task_id"]
        self.assertFalse(created["task"]["review_required"])
        with self.assertRaises(ValueError):
            coordination.claim_task(task_id, "alpha", path=self.registry)
        coordination.claim_task(task_id, "beta", path=self.registry)
        with self.assertRaises(ValueError):
            coordination.complete_task(task_id, "alpha", "synthetic pass", path=self.registry)
        with self.assertRaises(ValueError):
            coordination.complete_task(task_id, "beta", "", path=self.registry)
        completed = coordination.complete_task(task_id, "beta", "synthetic pass", "done", path=self.registry)
        self.assertTrue(completed["completed"])
        self.assertEqual(coordination.list_tasks("demo", "completed", self.registry)[0]["task_id"], task_id)
        retried = coordination.complete_task(task_id, "beta", "synthetic pass", "different retry result", path=self.registry)
        self.assertTrue(retried["completed"])
        self.assertTrue(retried["idempotent"])
        self.assertEqual(retried["task"]["result"], "done")
        with self.assertRaisesRegex(ValueError, "only the assigned agent"):
            coordination.complete_task(task_id, "alpha", "synthetic pass", path=self.registry)

    def test_same_agent_claim_retry_is_idempotent(self) -> None:
        created = coordination.delegate(
            "demo", "claim-retry", "Claim retry fixture", "alpha", assignee="beta", path=self.registry,
        )
        task_id = created["task"]["task_id"]
        first = coordination.claim_task(task_id, "beta", path=self.registry)
        before = json.dumps(first["task"], sort_keys=True)
        retry = coordination.claim_task(task_id, "beta", path=self.registry)
        self.assertTrue(first["claimed"])
        self.assertFalse(retry["claimed"])
        self.assertTrue(retry["idempotent"])
        self.assertEqual(json.dumps(retry["task"], sort_keys=True), before)
        with self.assertRaisesRegex(ValueError, "assigned to another agent"):
            coordination.claim_task(task_id, "gamma", path=self.registry)

    def test_review_required_task_needs_approved_peer_review(self) -> None:
        created = coordination.delegate(
            "demo", "gated", "Review-gated fixture task", "alpha", assignee="beta",
            review_required=True, path=self.registry,
        )
        task_id = created["task"]["task_id"]
        coordination.claim_task(task_id, "beta", path=self.registry)
        with self.assertRaisesRegex(ValueError, "approved independent peer review"):
            coordination.complete_task(task_id, "beta", "synthetic pass", path=self.registry)

        requested = coordination.request_review(
            "demo", "gated-review", "alpha", task_id=task_id, reviewer="gamma", path=self.registry,
        )
        coordination.submit_review(
            requested["review"]["review_id"], "gamma", "approved", "synthetic peer validation passed",
            path=self.registry,
        )
        completed = coordination.complete_task(task_id, "beta", "synthetic pass", path=self.registry)
        self.assertTrue(completed["completed"])

    def test_requeue_recovers_interrupted_work_and_preserves_reviews(self) -> None:
        created = coordination.delegate(
            "demo", "recoverable", "Recoverable fixture task", "alpha", assignee="beta", path=self.registry,
        )
        task_id = created["task"]["task_id"]
        requested = coordination.request_review(
            "demo", "recoverable-review", "alpha", task_id=task_id, reviewer="delta", path=self.registry,
        )
        coordination.claim_task(task_id, "beta", path=self.registry)
        with self.assertRaisesRegex(ValueError, "requester or assigned agent"):
            coordination.requeue_task(task_id, "gamma", "synthetic interruption", path=self.registry)

        recovered = coordination.requeue_task(task_id, "alpha", "assigned agent stopped", path=self.registry)
        self.assertTrue(recovered["requeued"])
        self.assertFalse(recovered["idempotent"])
        self.assertEqual(recovered["task"]["status"], "queued")
        self.assertIsNone(recovered["task"]["assignee"])
        self.assertEqual(recovered["task"]["last_assignee"], "beta")
        self.assertEqual(recovered["task"]["requeue_count"], 1)
        self.assertEqual(coordination.list_reviews("demo", path=self.registry)[0]["review_id"], requested["review"]["review_id"])

        with self.assertRaisesRegex(ValueError, "last requeue agent"):
            coordination.requeue_task(task_id, "gamma", "unauthorized repeat", path=self.registry)
        repeated = coordination.requeue_task(task_id, "alpha", "same interruption", path=self.registry)
        self.assertFalse(repeated["requeued"])
        self.assertTrue(repeated["idempotent"])
        claimed = coordination.claim_task(task_id, "gamma", path=self.registry)
        self.assertTrue(claimed["claimed"])

    def test_requeue_recovers_assigned_task_before_first_claim(self) -> None:
        created = coordination.delegate(
            "demo", "assigned-recovery", "Assigned fixture task", "alpha", assignee="beta", path=self.registry,
        )
        task_id = created["task"]["task_id"]
        recovered = coordination.requeue_task(task_id, "alpha", "assigned agent stopped before starting", path=self.registry)
        self.assertTrue(recovered["requeued"])
        self.assertEqual(recovered["task"]["requeued_from_status"], "assigned")
        self.assertEqual(recovered["task"]["status"], "queued")
        self.assertIsNone(recovered["task"]["assignee"])
        claimed = coordination.claim_task(task_id, "gamma", path=self.registry)
        self.assertTrue(claimed["claimed"])

    def test_requeue_requires_fresh_approval_for_gated_completion(self) -> None:
        created = coordination.delegate(
            "demo", "recoverable-gated", "Recoverable gated task", "alpha", assignee="beta",
            review_required=True, path=self.registry,
        )
        task_id = created["task"]["task_id"]
        coordination.claim_task(task_id, "beta", path=self.registry)
        prior = coordination.request_review(
            "demo", "prior-review", "alpha", task_id=task_id, reviewer="gamma", path=self.registry,
        )
        coordination.submit_review(
            prior["review"]["review_id"], "gamma", "approved", "synthetic pre-requeue approval",
            path=self.registry,
        )
        coordination.requeue_task(task_id, "alpha", "synthetic interruption after review", path=self.registry)
        coordination.claim_task(task_id, "delta", path=self.registry)
        with self.assertRaisesRegex(ValueError, "approved independent peer review"):
            coordination.complete_task(task_id, "delta", "synthetic pass", path=self.registry)

        fresh = coordination.request_review(
            "demo", "fresh-review", "alpha", task_id=task_id, reviewer="epsilon", path=self.registry,
        )
        coordination.submit_review(
            fresh["review"]["review_id"], "epsilon", "approved", "synthetic post-requeue approval",
            path=self.registry,
        )
        completed = coordination.complete_task(task_id, "delta", "synthetic pass", path=self.registry)
        self.assertTrue(completed["completed"])
        self.assertEqual(len(coordination.list_reviews("demo", path=self.registry)), 2)

    def test_changes_requested_review_blocks_gated_completion(self) -> None:
        created = coordination.delegate(
            "demo", "gated-changes", "Review-gated fixture task", "alpha", assignee="beta",
            review_required=True, path=self.registry,
        )
        task_id = created["task"]["task_id"]
        coordination.claim_task(task_id, "beta", path=self.registry)
        requested = coordination.request_review(
            "demo", "gated-changes-review", "alpha", task_id=task_id, reviewer="gamma", path=self.registry,
        )
        coordination.submit_review(
            requested["review"]["review_id"], "gamma", "changes_requested", "synthetic reviewer found an issue",
            findings=["fixture assertion needs correction"], path=self.registry,
        )
        with self.assertRaisesRegex(ValueError, "approved independent peer review"):
            coordination.complete_task(task_id, "beta", "synthetic pass", path=self.registry)
        self.assertEqual(coordination.list_tasks("demo", "in_progress", self.registry)[0]["task_id"], task_id)

    def test_gated_completion_rejects_non_independent_approved_reviews(self) -> None:
        created = coordination.delegate(
            "demo", "gated-identity", "Review-gated fixture task", "alpha", assignee="beta",
            review_required=True, path=self.registry,
        )
        task_id = created["task"]["task_id"]
        coordination.claim_task(task_id, "beta", path=self.registry)

        assigned_worker_review = coordination.request_review(
            "demo", "assigned-worker-review", "alpha", task_id=task_id, reviewer="beta", path=self.registry,
        )
        coordination.submit_review(
            assigned_worker_review["review"]["review_id"], "beta", "approved", "synthetic approval by worker",
            path=self.registry,
        )
        with self.assertRaisesRegex(ValueError, "approved independent peer review"):
            coordination.complete_task(task_id, "beta", "synthetic pass", path=self.registry)

        unrelated_requester_review = coordination.request_review(
            "demo", "unrelated-requester-review", "delta", task_id=task_id, reviewer="gamma", path=self.registry,
        )
        coordination.submit_review(
            unrelated_requester_review["review"]["review_id"], "gamma", "approved", "synthetic approval by unrelated requester",
            path=self.registry,
        )
        with self.assertRaisesRegex(ValueError, "approved independent peer review"):
            coordination.complete_task(task_id, "beta", "synthetic pass", path=self.registry)


class PeerReviewTests(ClaimFixture):
    def test_review_request_is_idempotent_and_requires_one_link(self) -> None:
        task = coordination.delegate("demo", "fixture", "Run fixture", "alpha", path=self.registry)
        first = coordination.request_review(
            "demo", "fixture-review", "alpha", task_id=task["task"]["task_id"],
            reviewer="beta", changed_files=["src/fixture.py"], path=self.registry,
        )
        second = coordination.request_review(
            "demo", "fixture-review", "other", task_id=task["task"]["task_id"],
            reviewer="gamma", path=self.registry,
        )
        self.assertTrue(first["created"])
        self.assertFalse(second["created"])
        self.assertTrue(second["idempotent"])
        self.assertEqual(first["review"]["review_id"], second["review"]["review_id"])
        with self.assertRaisesRegex(ValueError, "linked task project"):
            coordination.request_review(
                "other", "cross-project", "alpha", task_id=task["task"]["task_id"], path=self.registry,
            )
        with self.assertRaises(ValueError):
            coordination.request_review(
                "demo", "bad", "alpha", task_id=task["task"]["task_id"],
                commit_fingerprint="abc1234", path=self.registry,
            )
        with self.assertRaises(ValueError):
            coordination.request_review(
                "demo", "self-review", "alpha", commit_fingerprint="abc1234",
                reviewer="alpha", path=self.registry,
            )

    def test_task_and_review_listing_respects_case_insensitive_project_identity(self) -> None:
        task = coordination.delegate("Demo", "case-list", "Case fixture", "alpha", path=self.registry)
        requested = coordination.request_review(
            "dEmO", "case-list-review", "alpha", task_id=task["task"]["task_id"],
            reviewer="beta", path=self.registry,
        )
        self.assertEqual(
            coordination.list_tasks("demo", path=self.registry)[0]["task_id"], task["task"]["task_id"],
        )
        self.assertEqual(
            coordination.list_reviews("DEMO", path=self.registry)[0]["review_id"], requested["review"]["review_id"],
        )

    def test_reviewer_separation_findings_and_validation_are_enforced(self) -> None:
        requested = coordination.request_review(
            "demo", "commit-review", "alpha", commit_fingerprint="abc1234",
            reviewer="beta", changed_files=["src/fixture.py"], path=self.registry,
        )
        review_id = requested["review"]["review_id"]
        with self.assertRaises(ValueError):
            coordination.submit_review(review_id, "alpha", "approved", "synthetic pass", path=self.registry)
        with self.assertRaises(ValueError):
            coordination.submit_review(review_id, "gamma", "approved", "synthetic pass", path=self.registry)
        with self.assertRaises(ValueError):
            coordination.submit_review(review_id, "beta", "approved", "", path=self.registry)
        with self.assertRaises(ValueError):
            coordination.submit_review(
                review_id, "beta", "changes_requested", "synthetic fail",
                findings=["one", "two", "three", "four", "five", "six"], path=self.registry,
            )
        result = coordination.submit_review(
            review_id, "beta", "changes_requested", "synthetic validator failed",
            findings=["fixture assertion needs correction"], path=self.registry,
        )
        self.assertEqual(result["review"]["status"], "changes_requested")
        self.assertEqual(coordination.list_reviews("demo", "changes_requested", self.registry)[0]["review_id"], review_id)

    def test_commit_fingerprint_review_can_be_completed_once(self) -> None:
        requested = coordination.request_review(
            "demo", "commit-review", "alpha", commit_fingerprint="def5678", path=self.registry,
        )
        review_id = requested["review"]["review_id"]
        result = coordination.submit_review(review_id, "beta", "approved", "synthetic tests passed", path=self.registry)
        self.assertTrue(result["submitted"])
        with self.assertRaises(ValueError):
            coordination.submit_review(review_id, "gamma", "approved", "another pass", path=self.registry)

    def test_peer_review_verdict_retry_is_idempotent_and_immutable(self) -> None:
        requested = coordination.request_review(
            "demo", "retry-review", "alpha", commit_fingerprint="retry123", reviewer="beta", path=self.registry,
        )
        review_id = requested["review"]["review_id"]
        first = coordination.submit_review(
            review_id, "beta", "approved", "synthetic tests passed", findings=["no issues"], path=self.registry,
        )
        retry = coordination.submit_review(
            review_id, "beta", "approved", "synthetic tests passed", findings=["no issues"], path=self.registry,
        )
        self.assertTrue(first["submitted"])
        self.assertFalse(retry["submitted"])
        self.assertTrue(retry["idempotent"])
        self.assertEqual(retry["review"]["reviewed_at"], first["review"]["reviewed_at"])
        with self.assertRaisesRegex(ValueError, "final verdict"):
            coordination.submit_review(
                review_id, "beta", "changes_requested", "synthetic changed verdict", path=self.registry,
            )
        self.assertEqual(coordination.list_reviews("demo", path=self.registry)[0]["status"], "approved")


class HonestyTests(ClaimFixture):
    def test_the_registry_says_it_is_not_a_lock(self) -> None:
        """An agent that thinks it holds a lock is worse than one that knows."""
        result = coordination.status("demo", path=self.registry)
        self.assertIn("not a lock", result["covers"])

    def test_a_conflict_never_prevents_the_claim(self) -> None:
        """Overlap is a conversation, not an arbitration."""
        self.claim("alpha", ["src/one.py"])
        second = self.claim("beta", ["src/one.py"])
        self.assertTrue(second["conflicts"])
        self.assertEqual(second["claim"]["status"], "active")
        agents = {c["agent"] for c in coordination.active_claims("demo", self.registry)}
        self.assertEqual(agents, {"alpha", "beta"})

    def test_a_corrupt_registry_degrades_to_empty(self) -> None:
        self.registry.write_text("{ not json", encoding="utf-8")
        self.assertEqual(coordination.active_claims("demo", self.registry), [])
        result = self.claim("alpha", ["src/one.py"])
        self.assertEqual(result["conflicts"], [])


class PreflightTests(ClaimFixture):
    def test_the_preflight_surfaces_active_work_unasked(self) -> None:
        """The failure this exists to prevent: not knowing anyone was there."""
        import os

        from agent_os.chat import context

        os.environ[coordination.CLAIMS_ENV] = str(self.registry)
        self.addCleanup(os.environ.pop, coordination.CLAIMS_ENV, None)
        coordination.claim("personal-agent-os", "refactoring the router", "codex",
                           ["src/agent_os"], path=self.registry)

        result = context("improve the mcp routing layer and skill discovery in agent os")
        if result.get("project") != "personal-agent-os":
            self.skipTest("router did not resolve this project on this machine")
        self.assertIn("active_work", result)
        self.assertEqual(result["active_work"]["claims"][0]["agent"], "codex")


if __name__ == "__main__":
    unittest.main()
