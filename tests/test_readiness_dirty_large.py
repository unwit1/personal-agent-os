from __future__ import annotations

import os
import platform
import subprocess
import sys
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import readiness_fixtures
from readiness_fixtures import ReadinessFixture
from agent_os.orchestrator.engine import Orchestrator
from agent_os.orchestrator.router import ProviderRegistry
from agent_os.orchestrator.store import RunStore
from agent_os.telemetry import LocalTelemetryStore
from agent_os.orchestrator import repomap


def git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True).stdout


class DirtyLargeReadiness(ReadinessFixture):
    def _engine(self, tag: str) -> Orchestrator:
        return Orchestrator(RunStore(self.tmp / f"home-{tag}"), registry=ProviderRegistry(
            providers=[readiness_fixtures.provider(name) for name in self.providers]),
            telemetry_store=LocalTelemetryStore(self.tmp / f"telemetry-{tag}.jsonl"),
            claims_path=self.tmp / f"claims-{tag}.json", sleep=lambda _: None)

    def _run(self, repo: Path, tag: str, goal: str = "change calc add") -> dict:
        engine = self._engine(tag)
        created = engine.create_run(goal, repository=repo, tasks=[{"id": "impl", "goal": goal,
            "scope": ["impl"], "validators": [readiness_fixtures.PASS]}],
            policy={"auto_continue": True, "poll_interval_seconds": 0, "announce_claims": False})
        engine.start(created["run_id"])
        engine.run_loop(created["run_id"])
        return engine.load(created["run_id"])

    def test_dirty_and_large_repositories(self):
        timings = {}
        for kind, repo in self.fixtures.items():
            with self.subTest(fixture=kind):
                base = (repo / "README.md").read_bytes() + b"dirty change\n"
                (repo / "README.md").write_bytes(base)
                notes = b"untracked preservation\n"
                (repo / "notes.txt").write_bytes(notes)
                engine = self._engine(f"dirty-{kind}")
                created = engine.create_run("dirty fixture change", repository=repo,
                    tasks=[{"id": "impl", "goal": "change fixture", "scope": ["impl"], "validators": [readiness_fixtures.PASS]}],
                    policy={"auto_continue": True, "poll_interval_seconds": 0, "announce_claims": False})
                record = engine.load(created["run_id"])
                self.assertTrue(record["preflight"]["dirty_worktree"])
                self.assertTrue(record["preflight"]["note"])
                engine.start(created["run_id"])
                engine.run_loop(created["run_id"])
                record = engine.load(created["run_id"])
                branch = record["integration"].get("branch")
                files = git(repo, "ls-tree", "-r", "--name-only", branch).splitlines() if branch else []
                self.assertNotIn("notes.txt", files)
                self.assertEqual((repo / "README.md").read_bytes(), base)
                self.assertEqual((repo / "notes.txt").read_bytes(), notes)
                timings[f"{kind}_dirty"] = "completed; original bytes preserved; notes excluded"

                (repo / "README.md").write_text("staged\n", encoding="utf-8")
                git(repo, "add", "README.md")
                try:
                    staged_engine = self._engine(f"staged-{kind}")
                    staged = staged_engine.create_run("staged fixture", repository=repo,
                        tasks=[{"id": "impl", "goal": "change fixture", "scope": ["impl"], "validators": [readiness_fixtures.PASS]}],
                        policy={"auto_continue": True})
                    staged_result = f"proceeded; dirty_worktree={staged_engine.load(staged['run_id'])['preflight']['dirty_worktree']}"
                except Exception as exc:
                    staged_result = f"refused: {type(exc).__name__}: {exc}"
                timings[f"{kind}_staged"] = staged_result
                git(repo, "reset", "--hard", "HEAD")
                (repo / "notes.txt").unlink(missing_ok=True)

        large = self.py_repo
        bulk = large / "bulk"
        bulk.mkdir()
        for index in range(1200):
            (bulk / f"file-{index:04}.txt").write_text("small\n", encoding="utf-8")
        blob = large / "big" / "blob.txt"
        blob.parent.mkdir()
        blob.write_bytes(b"x" * 300_000)
        git(large, "add", "-A")
        git(large, "commit", "-m", "large fixture")
        start = time.perf_counter()
        mapped = repomap.build(large, "change calc add")
        map_seconds = time.perf_counter() - start
        self.assertLessEqual(len(mapped["text"]), 6000 + 200)
        self.assertNotIn("bulk/", mapped["text"])
        self.assertNotIn("blob.txt", mapped["text"])
        self.assertEqual(mapped["stats"]["tracked_files"], 1206)
        run_start = time.perf_counter()
        large_run = self._run(large, "large-python")
        run_seconds = time.perf_counter() - run_start
        self.assertIn(large_run["state"], {"COMPLETE", "COMPLETED"})
        timings["large_map"] = f"{map_seconds:.3f}s; chars={len(mapped['text'])}; stats={mapped['stats']}"
        timings["large_run"] = f"{run_seconds:.3f}s; state={large_run['state']}"
        self.__class__.evidence = timings
        self.__class__.environment = f"{platform.platform()}; Python {platform.python_version()}"
        print(f"READINESS_EVIDENCE {self.__class__.environment} {timings}")


if __name__ == "__main__":
    unittest.main()
