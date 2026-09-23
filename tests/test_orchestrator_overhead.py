"""Per-call overhead options (adapter flags) and the cross-run usage report.

No real model calls: adapters are given a probed feature set, and the report
reads telemetry files written by the ledger.
"""

from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.orchestrator import usage  # noqa: E402
from agent_os.orchestrator.adapters.base import AgentLaunchRequest, ProviderStatus  # noqa: E402
from agent_os.orchestrator.adapters import claude_code, codex_cli  # noqa: E402
from agent_os.orchestrator.ledger import Ledger  # noqa: E402
from agent_os.orchestrator.usage_report import build  # noqa: E402


def request(read_only: bool = False) -> AgentLaunchRequest:
    return AgentLaunchRequest("r", "n", "implementer", ".", "prompt.md", ".", "fast", "low", "m", "low", read_only)


def adapter(cls, flags: tuple[str, ...], **options):
    instance = cls({"id": "p", "executable": "x", "options": options})
    status = ProviderStatus("p", True, executable="x", version="1", features={flag: True for flag in flags})
    instance.probe = lambda: status  # type: ignore[method-assign]
    return instance


class ClaudeLeanFlagTests(unittest.TestCase):
    def test_all_lean_options(self) -> None:
        plan = adapter(claude_code.ClaudeCodeAdapter, claude_code.OPTIONAL_FLAGS, lean_tools=True, disable_skills=True, shared_prompt_cache=True, setting_sources="project,local").resolve_invocation(request())
        argv = plan.argv
        self.assertEqual(argv[argv.index("--tools") + 1], "Bash,Read,Edit,Write,Glob,Grep")
        for flag in ("--disable-slash-commands", "--exclude-dynamic-system-prompt-sections"):
            self.assertIn(flag, argv)
        self.assertEqual(argv[argv.index("--setting-sources") + 1], "project,local")
        self.assertNotIn("--bare", argv, "--bare would ignore OAuth logins")

    def test_read_only_workers_get_no_edit_tools(self) -> None:
        argv = adapter(claude_code.ClaudeCodeAdapter, claude_code.OPTIONAL_FLAGS, lean_tools=True).resolve_invocation(request(read_only=True)).argv
        self.assertEqual(argv[argv.index("--tools") + 1], "Bash,Read,Glob,Grep")

    def test_options_off_and_unadvertised_flags_are_not_passed(self) -> None:
        argv = adapter(claude_code.ClaudeCodeAdapter, claude_code.OPTIONAL_FLAGS, lean_tools=False, disable_skills=False, shared_prompt_cache=False).resolve_invocation(request()).argv
        for flag in ("--tools", "--disable-slash-commands", "--exclude-dynamic-system-prompt-sections", "--setting-sources"):
            self.assertNotIn(flag, argv)
        old_cli = adapter(claude_code.ClaudeCodeAdapter, ("--effort",), lean_tools=True, disable_skills=True, shared_prompt_cache=True).resolve_invocation(request()).argv
        self.assertNotIn("--tools", old_cli)
        self.assertNotIn("--disable-slash-commands", old_cli)

    def test_explicit_tool_list(self) -> None:
        argv = adapter(claude_code.ClaudeCodeAdapter, claude_code.OPTIONAL_FLAGS, lean_tools=["Read"]).resolve_invocation(request()).argv
        self.assertEqual(argv[argv.index("--tools") + 1], "Read")


class CodexLeanFlagTests(unittest.TestCase):
    def test_ignore_user_config_replaces_mcp_disabling(self) -> None:
        with mock.patch.object(codex_cli, "configured_mcp_servers", return_value=["mail"]):
            lean = adapter(codex_cli.CodexCliAdapter, codex_cli.OPTIONAL_FLAGS, use_user_config=False).resolve_invocation(request()).argv
            full = adapter(codex_cli.CodexCliAdapter, codex_cli.OPTIONAL_FLAGS, use_user_config=True).resolve_invocation(request()).argv
        self.assertIn("--ignore-user-config", lean)
        self.assertNotIn("mcp_servers.mail.enabled=false", lean)
        self.assertNotIn("--ignore-user-config", full)
        self.assertIn("mcp_servers.mail.enabled=false", full)
        self.assertIn('model_reasoning_effort="low"', lean, "effort is still passed explicitly")

    def test_ignored_config_still_carries_the_windows_sandbox_mode(self) -> None:
        config = Path(tempfile.mkdtemp(prefix="agent-os-codex-")) / "config.toml"
        self.addCleanup(shutil.rmtree, config.parent, True)
        config.write_text('service_tier = "priority"\n[windows]\nsandbox = "unelevated"\n[plugins."x"]\nenabled = true\n', encoding="utf-8")
        self.assertEqual(codex_cli.carried_config(["windows.sandbox", "missing.key", "plugins"], config), [("windows.sandbox", "unelevated")])
        with mock.patch.object(codex_cli, "_user_config", side_effect=lambda path=None: codex_cli.tomllib.loads(config.read_text(encoding="utf-8"))):
            argv = adapter(codex_cli.CodexCliAdapter, codex_cli.OPTIONAL_FLAGS, use_user_config=False).resolve_invocation(request()).argv
        self.assertIn('windows.sandbox="unelevated"', argv)
        self.assertNotIn("priority", " ".join(argv))

    def test_disable_features(self) -> None:
        argv = adapter(codex_cli.CodexCliAdapter, codex_cli.OPTIONAL_FLAGS, disable_features=["image_generation"]).resolve_invocation(request()).argv
        self.assertEqual(argv[argv.index("--disable") + 1], "image_generation")


class UsageReportTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="agent-os-usage-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.ledger = Ledger(lambda run_id: self.tmp / "runs" / run_id)

    def call(self, run: str, role: str, tier: str, provider: str, record: dict, prompt_chars: int = 400) -> None:
        self.ledger.emit(run, "model_completed", "n", role=role, capability_class=tier, provider=provider, model="m", usage=record, prompt_chars=prompt_chars)

    def test_report_aggregates_exact_and_separates_missing_and_synthetic(self) -> None:
        self.ledger.emit("r1", "task_selected", stage_id="P0.1")
        self.call("r1", "implementer", "fast", "codex", usage.normalized(total_input=10_000, cache_read=8_000, output=100, source="codex"))
        self.call("r1", "reviewer", "reasoning", "claude-code", usage.normalized(uncached_input=10, cache_read=5_000, cache_write=1_000, output=50, cost_usd=0.02, source="claude-code"))
        self.call("r2", "implementer", "fast", "codex", usage.unavailable("codex"))
        synthetic = usage.normalized(total_input=999, output=9, source="synthetic")
        self.call("r2", "reviewer", "balanced", "sim", synthetic)
        self.ledger.emit("r2", "retry", "n", reason="quota")
        self.ledger.emit("r2", "loop_guard", "n", guard="retry_limit", reason="x")
        self.ledger.emit("r2", "work_avoided", category="resume", model_calls_avoided=1)
        (self.tmp / "runs" / "r2" / "telemetry.jsonl").open("a").write("not json\n")
        report = build(sorted(self.tmp.glob("runs/*/telemetry.jsonl")))
        self.assertEqual(report["runs_counted"], 2)
        self.assertEqual(report["totals"]["input"], 10_000 + 6_010)
        self.assertEqual(report["totals"]["unreported_calls"], 1)
        self.assertEqual(report["coverage"]["synthetic_calls_excluded"], 1)
        self.assertEqual(report["by_role"]["implementer"]["calls"], 2)
        self.assertEqual(report["expensive_tier_calls_by_role"], {"reviewer": 1})
        self.assertEqual(report["by_origin"]["roadmap"]["exact_calls"], 2)
        self.assertEqual(report["friction"]["retry"], {"quota": 1})
        self.assertEqual(report["friction"]["loop_guard"], {"retry_limit": 1})
        self.assertEqual(report["model_calls_avoided_by_category"], {"resume": 1})
        self.assertEqual(report["malformed_lines"], 1)
        self.assertEqual(report["prompt_vs_provider_input"]["prompt_tokens_estimate"], 200)
        self.assertEqual(report["top_runs_by_input"][0]["run_id"], "r1")

    def test_since_filter(self) -> None:
        self.call("r1", "implementer", "fast", "codex", usage.normalized(total_input=5, output=1, source="codex"))
        self.assertEqual(build(sorted(self.tmp.glob("runs/*/telemetry.jsonl")), since="2999-01-01")["runs_counted"], 0)


if __name__ == "__main__":
    unittest.main()
