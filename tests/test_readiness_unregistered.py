"""Readiness checks for repositories that have no Agent OS registration."""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from readiness_fixtures import PASS, ReadinessFixture, provider
from agent_os.orchestrator.adapters import synthetic
from agent_os.orchestrator.engine import Orchestrator, OrchestratorError
from agent_os.orchestrator.router import ProviderRegistry
from agent_os.orchestrator.store import RunStore
from agent_os.paths import ROOT
from agent_os.telemetry import LocalTelemetryStore


class UnregisteredRepositoryTests(ReadinessFixture):
    def setUp(self):
        super().setUp()
        self.engine = Orchestrator(
            RunStore(self.tmp / "home"),
            registry=ProviderRegistry(providers=[provider("alpha"), provider("beta")]),
            telemetry_store=LocalTelemetryStore(self.telemetry_path),
            claims_path=self.claims,
            sleep=lambda _: None,
        )

    def run_summary(self, repo, *, project=None, tasks=None):
        return self.engine.create_run(
            "Check unregistered fixture", repository=repo, project=project,
            tasks=tasks or [{"id": "impl", "goal": "make a small fixture change",
                             "scope": ["impl"], "validators": [PASS]}],
            policy={"auto_continue": True, "poll_interval_seconds": 0,
                    "announce_claims": False,
                    "require_independent_review_for_model_edits": False},
        )

    def test_unregistered_repository_behavior(self):
        before = subprocess.run(["git", "status", "--porcelain", "projects"],
                                cwd=ROOT, capture_output=True, text=True, check=True).stdout
        observed = {}
        for name, fixture in self.fixtures.items():
            with self.subTest(fixture=name):
                summary = self.run_summary(fixture)
                record = self.engine.load(summary["run_id"])
                observed[name] = {"summary": summary, "record": record}
                self.assertIsNone(summary["project"])
                self.assertIsNone(record["project"])
                self.assertEqual(Path(record["repository"]).resolve(), fixture.resolve())

                with self.assertRaises(Exception) as caught:
                    self.run_summary(fixture, project="no-such-project-readiness")
                observed[name]["unknown_project_error"] = (type(caught.exception).__name__, str(caught.exception))

                nested = fixture / ("calc" if name == "python" else "src")
                nested_run = self.run_summary(nested)
                nested_record = self.engine.load(nested_run["run_id"])
                self.assertEqual(Path(nested_record["repository"]).resolve(), fixture.resolve())

                with tempfile.TemporaryDirectory(prefix="not-a-git-repo-") as plain:
                    with self.assertRaises(OrchestratorError) as git_error:
                        self.run_summary(Path(plain))
                self.assertIn("not inside a Git repository", str(git_error.exception))

                self.assertEqual(record["gates"], [])
                # Explicit tasks still run through the normal orchestrator lifecycle.
                self.engine.start(summary["run_id"])
                self.engine.run_loop(summary["run_id"], max_ticks=80)
                final = self.engine.load(summary["run_id"])
                observed[name]["completion"] = final["state"]
                self.assertEqual(final["state"], "COMPLETE")
        after = subprocess.run(["git", "status", "--porcelain", "projects"],
                               cwd=ROOT, capture_output=True, text=True, check=True).stdout
        self.assertEqual(after, before)
