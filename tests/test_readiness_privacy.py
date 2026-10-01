from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import readiness_fixtures
from agent_os.orchestrator.engine import Orchestrator
from agent_os.orchestrator.repomap import build
from agent_os.orchestrator.router import ProviderRegistry
from agent_os.orchestrator.store import RunStore, StoreError, redact
from agent_os.telemetry import LocalTelemetryStore


class ReadinessPrivacyTests(readiness_fixtures.ReadinessFixture):
    def _git(self, repo: Path, *args: str) -> str:
        return subprocess.run(
            ["git", "-c", "user.name=fixture", "-c", "user.email=f@x", *args],
            cwd=repo, check=True, capture_output=True, text=True,
        ).stdout

    def _engine(self, repo: Path) -> Orchestrator:
        return Orchestrator(
            RunStore(self.tmp / "home"),
            registry=ProviderRegistry(providers=[readiness_fixtures.provider(name) for name in self.providers]),
            telemetry_store=LocalTelemetryStore(self.telemetry_path),
            claims_path=self.claims,
            sleep=lambda seconds: None,
        )

    def _policy(self, **overrides) -> dict:
        policy = {"auto_continue": True, "poll_interval_seconds": 0, "announce_claims": False}
        policy.update(overrides)
        return policy

    def _task(self) -> dict:
        return {"id": "impl", "goal": "small fixture change", "scope": ["src"],
                "validators": [readiness_fixtures.PASS]}

    def test_pr1_run_state_refuses_transcripts_and_redacts_secrets(self):
        for name, repo in self.fixtures.items():
            with self.subTest(fixture=name):
                engine = Orchestrator(
                    RunStore(self.tmp / f"home-{name}"),
                    registry=ProviderRegistry(providers=[readiness_fixtures.provider(p) for p in self.providers]),
                    telemetry_store=LocalTelemetryStore(self.tmp / f"telemetry-{name}.jsonl"),
                    claims_path=self.tmp / f"claims-{name}.json", sleep=lambda seconds: None,
                )
                run_id = engine.create_run("goal", repository=repo, tasks=[self._task()],
                                            policy=self._policy())["run_id"]
                record = engine.load(run_id)
                with self.assertRaises(StoreError):
                    record["nodes"]["impl"]["transcript"] = ["hello"]
                    engine.store.save(record)
                record = engine.load(run_id)
                record["goal"] = "use key sk-ant-abcdefghijklmnopqrstuvwxyz0123 and password=hunter2"
                engine.store.save(record)
                stored = engine.store.state_path(run_id).read_text(encoding="utf-8")
                self.assertNotIn("abcdefghijklmnopqrstuvwxyz0123", stored)
                self.assertNotIn("hunter2", stored)
                self.assertEqual(redact("token ghp_" + "a" * 30), "token [redacted]")
                cleaned = redact("sk-ant-abcdefghijklmnopqrstuvwxyz0123 password=hunter2")
                self.assertNotIn("abcdefghijklmnopqrstuvwxyz0123", cleaned)
                self.assertNotIn("hunter2", cleaned)

    def test_gap_redact_misses_generic_sk_token(self):
        token = "sk-test-123456"
        observed = redact(token)
        for name, _repo in self.fixtures.items():
            with self.subTest(fixture=name):
                self.assertEqual(observed, token, "current generic sk-token behavior changed")

    def test_pr2_state_and_telemetry_hold_no_prompt_text(self):
        marker = "UNIQUE-PRIVACY-PROMPT-MARKER"
        for name, repo in self.fixtures.items():
            with self.subTest(fixture=name):
                engine = self._engine(repo)
                run_id = engine.create_run(f"goal {marker}", repository=repo, tasks=[self._task()],
                                           policy=self._policy())["run_id"]
                engine.run_loop(run_id, max_ticks=30)
                state = engine.store.state_path(run_id).read_text(encoding="utf-8")
                telemetry = self.telemetry_path.read_text(encoding="utf-8")
                self.assertNotIn("Rules:", state)
                self.assertNotIn("agent-os-result", state)
                for key in ('"transcript"', '"messages"', '"conversation"', '"history"'):
                    self.assertNotIn(key, state)
                self.assertNotIn(marker, telemetry)
                allowed = {"schema_version", "event_id", "occurred_at", "project_id", "task_category", "capability_class", "execution_path", "provider", "model", "input_tokens", "cached_tokens", "output_tokens", "duration_ms", "retries", "validator_passed", "escalations", "correction_or_override", "reasoning_tokens", "items_processed"}
                events = [json.loads(line) for line in telemetry.splitlines()]
                self.assertTrue(events)
                for event in events:
                    self.assertLessEqual(set(event), allowed)

    def test_pr3_repo_map_secret_file_visibility(self):
        observations = {}
        for name, repo in self.fixtures.items():
            with self.subTest(fixture=name):
                (repo / ".env").write_text("API_KEY=sk-test-123456\n", encoding="utf-8")
                (repo / "config").mkdir()
                (repo / "config" / "secrets.json").write_text('{"api_key":"sk-test-123456"}\n', encoding="utf-8")
                self._git(repo, "add", ".env", "config/secrets.json")
                self._git(repo, "commit", "-m", "fixture secret files")
                result = build(repo, "add a feature using the api key config")
                observations[name] = {"secret_value": "sk-test-123456" in result["text"],
                                      "env_path": ".env" in result["text"]}
                self.assertFalse(observations[name]["secret_value"], observations[name])
                self.assertFalse(observations[name]["env_path"], observations[name])
        self.assertTrue(all(not seen["secret_value"] for seen in observations.values()))

    def test_pr4_repo_map_excludes_bulk_data_directory_contents(self):
        for name, repo in self.fixtures.items():
            with self.subTest(fixture=name):
                rows = repo / "data" / "rows"
                rows.mkdir(parents=True)
                for index in range(70):
                    (rows / f"row{index:02d}.csv").write_text("id,value\n1,x\n", encoding="utf-8")
                self._git(repo, "add", "data")
                self._git(repo, "commit", "-m", "fixture data rows")
                result = build(repo, "add a feature")
                self.assertTrue(any(value in ("data", "data/rows") for value in result["stats"]["data_dirs"]))
                self.assertNotRegex(result["text"], r"row\d+\.csv")

    def test_gap_pr5_agent_local_leaks_into_status_or_integration_branch(self):
        for name, repo in self.fixtures.items():
            with self.subTest(fixture=name):
                engine = self._engine(repo)
                task = self._task()
                task["scope"] = ["impl", ".agent-local"]
                run_id = engine.create_run("privacy history check", repository=repo, tasks=[task],
                                           policy=self._policy(share_run_history=True))["run_id"]
                engine.run_loop(run_id, max_ticks=30)
                record = engine.load(run_id)
                self.assertEqual(record["nodes"]["impl"]["state"], "PASSED", record["nodes"]["impl"])
                events = engine.store.events_path(run_id).read_text(encoding="utf-8")
                self.assertNotIn("run history snapshot failed", events)
                prompts = list(engine.store.run_dir(run_id).glob("workers/impl-*/prompt.md"))
                self.assertTrue(prompts, "worker prompt was not recorded")
                self.assertTrue(any("Run history of this machine" in path.read_text(encoding="utf-8") for path in prompts))
                status = self._git(repo, "status", "--porcelain", "--untracked-files=all")
                branch = record.get("integration", {}).get("branch")
                self.assertTrue(branch, record.get("integration"))
                tree = self._git(repo, "ls-tree", "-r", "--name-only", branch)
                leaked = [line for line in (status + "\n" + tree).splitlines() if ".agent-local" in line]
                self.assertTrue(leaked, "expected to observe .agent-local leakage without a fixture .gitignore")

    def test_pr6_store_rejects_canonical_repository_location(self):
        root = Path(__file__).resolve().parents[1]
        with self.assertRaises(StoreError):
            RunStore(root / "projects" / "orchestrator-state")


if __name__ == "__main__":
    unittest.main()
