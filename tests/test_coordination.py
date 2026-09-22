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

    def test_only_assignee_can_complete_with_validation_evidence(self) -> None:
        created = coordination.delegate("demo", "assigned", "Assigned fixture task", "alpha", assignee="beta", path=self.registry)
        task_id = created["task"]["task_id"]
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
