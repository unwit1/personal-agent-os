"""Orchestrator OS runs without Agent OS: imports, host defaults, a full CLI run,
and the control-plane guard on repositories other than the state root."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from orchestrator_os import control_plane, host  # noqa: E402

PROVIDERS = {"providers": [{
    "id": "synth", "adapter": "synthetic",
    "models": {"fast": "s-fast", "balanced": "s-bal", "reasoning": "s-rea", "frontier": "s-fro"},
    "effort_map": {"none": "n", "low": "l", "medium": "m", "high": "h"}, "max_concurrency": 2,
}]}


def git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-c", "user.name=fixture", "-c", "user.email=f@x", *args], cwd=repo,
                          check=True, capture_output=True, text=True).stdout


def fixture_repo(root: Path) -> Path:
    repo = root / "repo"
    repo.mkdir()
    git(repo, "init", "-q", "-b", "main")
    (repo / "README.md").write_text("fixture\n", encoding="utf-8")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "init")
    return repo


class ImportIsolationTests(unittest.TestCase):
    def test_no_agent_os_module_is_imported(self) -> None:
        code = ("import sys, orchestrator_os.engine, orchestrator_os.service, orchestrator_os.server, "
                "orchestrator_os.cli, orchestrator_os.__main__\n"
                "leaked = sorted(m for m in sys.modules if m == 'agent_os' or m.startswith('agent_os.'))\n"
                "print(leaked); raise SystemExit(1 if leaked else 0)")
        result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True,
                                env={**os.environ, "PYTHONPATH": str(Path(__file__).resolve().parents[1] / "src")})
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


class StandaloneHostTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="orch-host-"))
        self.previous = host.set_host(host.StandaloneHost())
        self.addCleanup(host.set_host, self.previous)
        self.env = os.environ.get(host.PROJECTS_ENV)
        self.addCleanup(lambda: os.environ.pop(host.PROJECTS_ENV, None) if self.env is None else os.environ.__setitem__(host.PROJECTS_ENV, self.env))

    def test_no_registry_means_no_projects_and_a_clear_error(self) -> None:
        os.environ[host.PROJECTS_ENV] = str(self.tmp / "missing.json")
        self.assertEqual(host.projects(), [])
        with self.assertRaises(KeyError):
            host.get_project("anything")
        self.assertIsNone(host.identify_project(self.tmp))
        with self.assertRaises(host.HostCapabilityUnavailable):
            host.claim("p", "t", "a")

    def test_registry_supplies_project_context(self) -> None:
        repo = self.tmp / "web"
        repo.mkdir()
        registry = self.tmp / "projects.json"
        registry.write_text(json.dumps({"projects": [{"id": "web", "path": str(repo), "summary": "a web app",
                                                       "constraints": ["no new deps"], "validation_commands": ["npm test"]}]}), encoding="utf-8")
        os.environ[host.PROJECTS_ENV] = str(registry)
        self.assertEqual(host.get_project("WEB")["id"], "web")
        self.assertEqual(host.identify_project(repo / "src")["id"], "web")
        packet = host.compile_context("web", "fix the login form")
        self.assertEqual(packet["summary"], "a web app")
        self.assertEqual(packet["state"]["validation_commands"], ["npm test"])

    def test_host_can_be_named_by_environment(self) -> None:
        host.set_host(None)
        os.environ[host.HOST_ENV] = "orchestrator_os.host:StandaloneHost"
        self.addCleanup(os.environ.pop, host.HOST_ENV, None)
        self.assertIs(host.get_host(), host.StandaloneHost)


class TargetPolicyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="orch-target-"))

    def test_repository_without_policy_is_not_guarded(self) -> None:
        self.assertFalse(control_plane.applies_to(self.tmp, None))
        self.assertIsNone(control_plane.target_policy(self.tmp)[0])

    def test_repository_policy_is_enforced_with_the_floor(self) -> None:
        (self.tmp / "policy").mkdir()
        (self.tmp / "policy" / "orchestrator-os.policy.json").write_text(json.dumps(
            {"control_plane": {"protected_paths": ["secrets/**"], "records_dir": "evidence/records"}}), encoding="utf-8")
        self.assertTrue(control_plane.applies_to(self.tmp, None))
        policy, records = control_plane.target_policy(self.tmp)
        self.assertEqual(records, "evidence/records/")
        result = control_plane.check(["secrets/key.txt", "policy/orchestrator-os.policy.json", "app.py"], policy=policy)
        self.assertFalse(result["passed"])
        self.assertIn("secrets/key.txt", result["detail"])
        self.assertIn("policy/orchestrator-os.policy.json", result["detail"])
        self.assertNotIn("app.py", result["detail"])

    def test_pre_extraction_layout_keeps_its_records_append_only(self) -> None:
        (self.tmp / "policy").mkdir()
        (self.tmp / "policy" / "orchestrator-os.policy.json").write_text("{}", encoding="utf-8")
        (self.tmp / "projects/personal-agent-os/orchestrator-os/records").mkdir(parents=True)
        self.assertEqual(control_plane.target_policy(self.tmp)[1], "projects/personal-agent-os/orchestrator-os/records/")


class StandaloneRunTests(unittest.TestCase):
    """A planned, implemented, validated, reviewed and integrated run through
    the `orchestrator` command line, on a repository nobody registered."""

    def test_start_recommended_completes_and_integrates(self) -> None:
        tmp = Path(tempfile.mkdtemp(prefix="orch-e2e-"))
        repo = fixture_repo(tmp)
        (tmp / "providers.json").write_text(json.dumps(PROVIDERS), encoding="utf-8")
        env = {**os.environ, "AGENT_OS_PROVIDERS": str(tmp / "providers.json"), "ORCHESTRATOR_STATE_ROOT": str(tmp / "state"),
               "AGENT_OS_ORCHESTRATOR_HOME": str(tmp / "home"), "ORCHESTRATOR_CONFIG_DIR": str(tmp / "config"),
               "PYTHONPATH": str(Path(__file__).resolve().parents[1] / "src")}
        env.pop(host.HOST_ENV, None)
        run = lambda *args: subprocess.run([sys.executable, "-m", "orchestrator_os", *args], cwd=tmp, env=env,  # noqa: E731
                                           capture_output=True, text=True, timeout=300)
        started = run("start-recommended", "--repo", str(repo), "--goal", "add a greeting file", "--validator", "git status", "--max-seconds", "120")
        self.assertEqual(started.returncode, 0, started.stderr[-2000:])
        summary = json.loads(started.stdout)
        self.assertEqual(summary["state"], "COMPLETE")
        log = git(repo, "log", "--all", "--format=%s")  # integration lands on the run branch, not main
        self.assertIn(f"{summary['run_id']}: integrate", log)
        listed = json.loads(run("list").stdout)
        runs = listed["runs"] if isinstance(listed, dict) else listed
        self.assertIn(summary["run_id"], [item["run_id"] for item in runs])
        legacy = run("orchestrate", "status", summary["run_id"])  # old `agent-os orchestrate` spelling still parses
        self.assertEqual(legacy.returncode, 0, legacy.stderr[-1000:])


if __name__ == "__main__":
    unittest.main()
