"""Claude cloud lane, one-time plan extras, OpenRouter account state, the
usage hub, and sensitive-data guards for delegation. No network, no real
Claude CLI: processes and HTTP are faked."""

from __future__ import annotations

import io
import json
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.orchestrator import cloud_lane, openrouter_account, plan_extras, usage_hub  # noqa: E402
from agent_os.orchestrator.model_profile import is_sensitive, sensitive_paths  # noqa: E402

NOW = datetime(2026, 10, 14, 18, 0, tzinfo=timezone.utc)


def git_repo(root: Path, name: str = "proj") -> Path:
    repo = root / name
    repo.mkdir()
    (repo / "README.md").write_text("hello\n", encoding="utf-8")
    for cmd in (["git", "init", "-q"], ["git", "add", "README.md"],
                ["git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "-m", "init"]):
        subprocess.run(cmd, cwd=repo, check=True, capture_output=True)
    return repo


class FakePty:
    def __init__(self, output: str, alive_for: int = 0) -> None:
        self.output, self.reads, self.alive_for, self.terminated = output, 0, alive_for, False

    def read(self, size: int) -> str:
        self.reads += 1
        if self.reads == 1:
            return self.output
        raise EOFError

    def isalive(self) -> bool:
        self.alive_for -= 1
        return self.alive_for > 0 and not self.terminated

    def terminate(self, force: bool = False) -> None:
        self.terminated = True


class CloudLaneTests(unittest.TestCase):
    def test_preflight_guards(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = git_repo(Path(tmp))
            self.assertEqual(cloud_lane.preflight(repo)["dirty"], [])
            (repo / "README.md").write_text("changed\n", encoding="utf-8")
            with self.assertRaisesRegex(cloud_lane.CloudLaneError, "uncommitted"):
                cloud_lane.preflight(repo)
            self.assertEqual(len(cloud_lane.preflight(repo, allow_dirty=True)["dirty"]), 1)
            with self.assertRaisesRegex(cloud_lane.CloudLaneError, "sensitive"):
                cloud_lane.preflight(repo, allow_dirty=True, sensitive=True)
            with self.assertRaisesRegex(cloud_lane.CloudLaneError, "not the root"):
                cloud_lane.preflight(Path(tmp))
            hr = git_repo(Path(tmp), "HR GUI")
            with self.assertRaisesRegex(cloud_lane.CloudLaneError, "sensitive"):
                cloud_lane.preflight(hr)

    def test_submit_records_session(self) -> None:
        printed = "\x1b[2mCreated cloud session: x\x1b[0m\r\nView: https://claude.ai/code/session_01ABCdef?from=cli&m=0\r\n"
        with tempfile.TemporaryDirectory() as tmp:
            repo = git_repo(Path(tmp))
            fake = FakePty(printed, alive_for=50)
            entry = cloud_lane.submit(repo, "do it", home=Path(tmp), spawn=lambda argv, cwd, env: fake, executable="claude")
            self.assertEqual(entry["session_id"], "session_01ABCdef")
            self.assertEqual(entry["teleport"], "claude --teleport session_01ABCdef")
            self.assertTrue(fake.terminated)
            self.assertEqual([item["session_id"] for item in cloud_lane.sessions(Path(tmp))], ["session_01ABCdef"])

    def test_trust_prompt_is_never_answered(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = git_repo(Path(tmp))
            fake = FakePty("Quick safety check: Yes, I trust this folder", alive_for=50)
            with self.assertRaisesRegex(cloud_lane.CloudLaneError, "not trusted"):
                cloud_lane.submit(repo, "do it", home=Path(tmp), spawn=lambda argv, cwd, env: fake, executable="claude")
            self.assertEqual(cloud_lane.sessions(Path(tmp)), [])

    def test_exit_without_link_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = git_repo(Path(tmp))
            fake = FakePty("Error: not signed in", alive_for=0)
            with self.assertRaisesRegex(cloud_lane.CloudLaneError, "without creating"):
                cloud_lane.submit(repo, "do it", home=Path(tmp), spawn=lambda argv, cwd, env: fake, executable="claude")

    def test_send_followup(self) -> None:
        calls = []

        def run(argv, **kwargs):
            calls.append(argv)
            return subprocess.CompletedProcess(argv, 0, stdout=json.dumps({"ok": True, "session_id": "session_1", "url": "u"}), stderr="")

        def fail(argv, **kwargs):
            return subprocess.CompletedProcess(argv, 0, stdout=json.dumps({"ok": False, "error": "archived"}), stderr="")

        with tempfile.TemporaryDirectory() as tmp:
            self.assertTrue(cloud_lane.send("session_1", "next", home=Path(tmp), run=run, executable="claude")["ok"])
            self.assertEqual(calls[0], ["claude", "-p", "next", "--cloud", "session_1", "--output-format", "json"])
            with self.assertRaisesRegex(cloud_lane.CloudLaneError, "archived"):
                cloud_lane.send("session_1", "next", home=Path(tmp), run=fail, executable="claude")
            self.assertEqual([item["ok"] for item in cloud_lane.sessions(Path(tmp))[0]["followups"]], [True, False])


def plan(source: str, state: str, used: float, hours: float) -> dict:
    return {"source": source, "state": state, "windows": [{"name": "5h", "used": used, "resets_at": (NOW + timedelta(hours=hours)).isoformat()}]}


class ExtrasTests(unittest.TestCase):
    def test_load_merges_and_expires(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            extras = plan_extras.load(Path(tmp), now=NOW)
            self.assertEqual(extras["claude-saved-reset"]["status"], "unknown")
            later = plan_extras.load(Path(tmp), now=datetime(2026, 10, 23, tzinfo=timezone.utc))
            self.assertEqual(later["claude-saved-reset"]["status"], "expired")
            plan_extras.set_status(Path(tmp), "claude-saved-reset", "used", "redeemed 10-14")
            self.assertEqual(plan_extras.load(Path(tmp), now=datetime(2026, 10, 23, tzinfo=timezone.utc))["claude-saved-reset"]["status"], "used")
            with self.assertRaises(ValueError):
                plan_extras.set_status(Path(tmp), "nope", "used")
            with self.assertRaises(ValueError):
                plan_extras.set_status(Path(tmp), "claude-saved-reset", "maybe")

    def test_reset_advice_only_when_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            extras = plan_extras.load(Path(tmp), now=NOW)
        kinds = lambda plans: [(item["kind"], item.get("plan")) for item in plan_extras.advice(extras, plans, now=NOW)]
        self.assertIn(("redeem_reset", "claude"), kinds({"c": plan("claude", "exhausted", 0.99, 3)}))
        self.assertNotIn(("redeem_reset", "claude"), kinds({"c": plan("claude", "exhausted", 0.99, 1)}))  # resets soon anyway
        self.assertNotIn(("redeem_reset", "codex"), kinds({"x": plan("codex", "tight", 0.53, 100)}))  # tight, not nearly full
        self.assertIn(("redeem_reset", "codex"), kinds({"x": plan("codex", "tight", 0.93, 100)}))
        self.assertIn(("use_cloud_credit", "claude"), kinds({}))
        self.assertNotIn(("use_cloud_credit", "claude"), [(item["kind"], item.get("plan")) for item in
                         plan_extras.advice(extras, {}, now=datetime(2026, 11, 5, tzinfo=timezone.utc))])

    def test_used_reset_gives_no_advice(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            for key in ("claude-saved-reset", "claude-limit-reset"):
                plan_extras.set_status(Path(tmp), key, "used")
            extras = plan_extras.load(Path(tmp), now=NOW)
        self.assertEqual([item for item in plan_extras.advice(extras, {"c": plan("claude", "exhausted", 0.99, 3)}, now=NOW)
                          if item["kind"] == "redeem_reset"], [])


class Response(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class OpenRouterAccountTests(unittest.TestCase):
    def test_reads_allowlist_and_derives_tier(self) -> None:
        seen = []

        def opener(request, timeout=0):
            seen.append((request.get_method(), request.full_url))
            body = {"data": {"total_credits": 10, "total_usage": 0.2}} if request.full_url.endswith("/credits") else {"data": {"is_free_tier": False, "limit_remaining": 99}}
            return Response(json.dumps(body).encode())

        with tempfile.TemporaryDirectory() as tmp:
            state = openrouter_account.refresh(Path(tmp), opener=opener, resolve=lambda ref: "sk-test")
            stored = json.loads((Path(tmp) / "free-compute" / "account.json").read_text(encoding="utf-8"))
        self.assertTrue(state["high_allowance"])
        self.assertEqual(stored["high_allowance"], True)
        self.assertNotIn("sk-test", json.dumps(stored))
        self.assertEqual(sorted(seen), [("GET", "https://openrouter.ai/api/v1/credits"), ("GET", "https://openrouter.ai/api/v1/key")])

    def test_unreadable_credits_leave_tier_unknown(self) -> None:
        def opener(request, timeout=0):
            raise OSError("boom sk-test")

        with tempfile.TemporaryDirectory() as tmp:
            state = openrouter_account.refresh(Path(tmp), opener=opener, resolve=lambda ref: "sk-test")
            stored = (Path(tmp) / "free-compute" / "account.json").read_text(encoding="utf-8")
        self.assertIsNone(state["high_allowance"])
        self.assertNotIn("sk-test", stored)


class UsageHubTests(unittest.TestCase):
    def test_one_row_per_plan(self) -> None:
        assessments = {"nano-a": {"source": "nanogpt", "state": "ok", "windows": []}, "nano-b": {"source": "nanogpt", "state": "ok", "windows": []},
                       "codex": {"source": "codex", "state": "tight", "windows": []}}
        with tempfile.TemporaryDirectory() as tmp, mock.patch("agent_os.orchestrator.headroom.for_providers", return_value=assessments):
            rows = usage_hub.plans([], Path(tmp))
        self.assertEqual([(row["plan"], row["providers"]) for row in rows], [("codex", ["codex"]), ("nanogpt", ["nano-a", "nano-b"])])


class SensitivePathTests(unittest.TestCase):
    def test_subfolders_of_sensitive_repos(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.assertTrue(is_sensitive({}, r"C:\Users\x\GitHub\HR GUI\src\app", Path(tmp)))
            self.assertFalse(is_sensitive({}, r"C:\Users\x\GitHub\brickmen\src", Path(tmp)))
            with mock.patch("agent_os.orchestrator.model_profile.sensitive_repos", return_value={"hr gui"}):
                self.assertTrue(sensitive_paths([r"C:\Users\x\GitHub\brickmen", r"C:\Users\x\GitHub\HR GUI\data\a.txt"]))
                self.assertFalse(sensitive_paths([r"C:\Users\x\GitHub\brickmen"]))

    def test_delegate_excludes_third_party_hosts_for_sensitive_work(self) -> None:
        from agent_os.orchestrator import delegate as delegate_module
        from agent_os.orchestrator.router import ProviderRegistry

        registry = ProviderRegistry(providers=[
            {"id": "free-api", "adapter": "openai_api", "models": {"fast": "m"}, "costs": {"fast": 0.01}, "roles": ["inline"],
             "options": {"base_url": "https://openrouter.ai/api/v1"}},
            {"id": "sub", "adapter": "claude_code", "models": {"fast": "haiku"}, "costs": {"fast": 1.0}},
        ])
        seen = {}

        def fake_select(reg, **kwargs):
            seen.update(kwargs)
            return {"resolved": False, "reason": "stop here"}

        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(delegate_module, "select", side_effect=fake_select), \
             mock.patch.object(delegate_module, "_availability", return_value={}):
            delegate_module.delegate("x", task_family="t", registry=registry, home=Path(tmp), role="inline", record=False, sensitive=True)
            self.assertEqual(seen["excluded"], ["free-api"])
            delegate_module.delegate("x", task_family="t", registry=registry, home=Path(tmp), role="inline", record=False, sensitive=False)
            self.assertEqual(seen["excluded"], [])


if __name__ == "__main__":
    unittest.main()
