"""Readiness evidence for worktree isolation and rollback."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import readiness_fixtures
from agent_os.orchestrator.adapters import synthetic
from agent_os.orchestrator.engine import Orchestrator
from agent_os.orchestrator.router import ProviderRegistry
from agent_os.orchestrator.store import RunStore
from agent_os.orchestrator.worktrees import WorktreeManager, git
from agent_os.telemetry import LocalTelemetryStore


PASS = {"kind": "command", "command": [sys.executable, "-c", "print('ok')"]}


class ReadinessWorktreeTests(readiness_fixtures.ReadinessFixture):
    def setUp(self):
        super().setUp()
        self.providers = ("alpha", "beta")
        self.engines = {}
        for name, repo in self.fixtures.items():
            registry = ProviderRegistry(providers=[readiness_fixtures.provider(p) for p in self.providers])
            self.engines[name] = Orchestrator(
                RunStore(self.tmp / ("home-" + name)), registry=registry,
                telemetry_store=LocalTelemetryStore(self.tmp / ("telemetry-" + name) / "events.jsonl"),
                claims_path=self.tmp / ("claims-" + name + ".json"), sleep=lambda seconds: None,
            )
            synthetic.SCRIPTS["alpha"] = readiness_fixtures.edit_script()
            synthetic.SCRIPTS["beta"] = readiness_fixtures.edit_script()

    def git(self, repo, *args):
        return subprocess.run(["git", "-c", "user.name=fixture", "-c", "user.email=f@x", *args], cwd=repo,
                              check=True, capture_output=True, text=True).stdout.strip()

    def task(self, task_id, scope=None, **extra):
        item = {"id": task_id, "goal": "work on " + task_id, "scope": scope or [task_id], "validators": [PASS]}
        item.update(extra)
        return item

    def create(self, name, tasks, **policy):
        config = {"auto_continue": True, "poll_interval_seconds": 0, "announce_claims": False}
        config.update(policy)
        return self.engines[name].create_run("readiness fixture", repository=self.fixtures[name], tasks=tasks, policy=config)["run_id"]

    def node(self, name, run_id, node_id):
        return self.engines[name].load(run_id)["nodes"][node_id]

    def test_wt_1_concurrent_tasks_have_distinct_external_worktrees(self):
        for name, repo in self.fixtures.items():
            with self.subTest(fixture=name):
                synthetic.SCRIPTS["alpha"] = readiness_fixtures.edit_script({"a": {"ticks": 3}, "b": {"ticks": 3}})
                engine = self.engines[name]
                run_id = self.create(name, [self.task("a"), self.task("b")])
                engine.start(run_id); engine.step(run_id)
                nodes = [self.node(name, run_id, key) for key in ("a", "b")]
                self.assertTrue(all(n["state"] == "RUNNING" for n in nodes))
                paths = [Path(n["worktree"]["path"]).resolve() for n in nodes]
                self.assertNotEqual(paths[0], paths[1])
                self.assertNotEqual(nodes[0]["worktree"]["branch"], nodes[1]["worktree"]["branch"])
                for path in paths:
                    self.assertNotEqual(path, repo.resolve())
                    self.assertFalse(path.is_relative_to(repo.resolve()))

    def test_wt_2_edit_outside_scope_fails_validation(self):
        for name, repo in self.fixtures.items():
            with self.subTest(fixture=name):
                synthetic.SCRIPTS["alpha"] = readiness_fixtures.edit_script({"a": {"edits": {"README.md": "clobbered\n"}}})
                run_id = self.create(name, [self.task("a")], max_escalations=0, max_stage_retries=0)
                final = self.engines[name].run_loop(run_id, max_ticks=20)
                node = self.node(name, run_id, "a")
                self.assertEqual(final["state"], "BLOCKED")
                self.assertFalse(node["integrated"])
                scope = next(e for e in node["validation"]["evidence"] if e["kind"] == "scope")
                self.assertFalse(scope["passed"])
                self.assertIn("fixture", (repo / "README.md").read_text(encoding="utf-8"))

    def test_wt_3_failed_validation_rolls_back_base_cleanly(self):
        for name, repo in self.fixtures.items():
            with self.subTest(fixture=name):
                base = self.git(repo, "rev-parse", "HEAD")
                validator = {"kind": "command", "command": [sys.executable, "-c", "import sys; sys.exit(1)"]}
                run_id = self.create(name, [self.task("a", validators=[validator])], max_escalations=0, max_stage_retries=0)
                result = self.engines[name].run_loop(run_id, max_ticks=20)
                record = self.engines[name].load(run_id)
                self.assertEqual(result["state"], "BLOCKED")
                self.assertEqual(self.git(repo, "rev-parse", "HEAD"), record["base_commit"])
                self.assertEqual(record["base_commit"], base)
                self.assertEqual(self.git(repo, "status", "--porcelain"), "")

    def test_wt_4_branch_integration_keeps_base_head_unchanged(self):
        for name, repo in self.fixtures.items():
            with self.subTest(fixture=name):
                base = self.git(repo, "rev-parse", "HEAD")
                run_id = self.create(name, [self.task("a")], final_integration="branch")
                result = self.engines[name].run_loop(run_id, max_ticks=30)
                record = self.engines[name].load(run_id)
                self.assertEqual(result["state"], "COMPLETE", result["state_reason"])
                self.assertEqual(self.git(repo, "rev-parse", "HEAD"), base)
                branch = record["integration"]["branch"]
                self.assertNotEqual(self.git(repo, "rev-parse", branch), base)
                self.assertIn("a/", self.git(repo, "ls-tree", "-r", "--name-only", branch))

    def test_wt_5_merge_conflict_is_aborted_cleanly(self):
        for name, repo in self.fixtures.items():
            with self.subTest(fixture=name):
                manager = WorktreeManager(repo, self.tmp / ("wt-" + name), "conflict-run")
                base = git(["rev-parse", "HEAD"], repo).stdout.strip()
                manager.ensure_integration(base)
                one = manager.create("one", base); two = manager.create("two", base)
                for info, value in ((one, "one\n"), (two, "two\n")):
                    Path(info["path"], "README.md").write_text(value, encoding="utf-8")
                    manager.checkpoint(info["path"], "edit")
                self.assertTrue(manager.merge(one["branch"], "merge one")["merged"])
                outcome = manager.merge(two["branch"], "merge two")
                self.assertFalse(outcome["merged"])
                self.assertEqual(outcome["conflicts"], ["README.md"])
                self.assertEqual(manager.integration_head(), outcome["before"])
                self.assertEqual(git(["status", "--porcelain"], manager.integration_path).stdout.strip(), "")


if __name__ == "__main__":
    import unittest
    unittest.main()
