"""Claude Code coding-plan endpoint configuration and credential isolation."""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.orchestrator.adapters.base import AgentLaunchRequest, ProviderStatus  # noqa: E402
from agent_os.orchestrator.adapters.claude_code import ClaudeCodeAdapter  # noqa: E402


REFERENCE = "secrets://zai-coding/default"
PLACEHOLDER_SECRET = "fake-launch-value"


class ClaudeCodeEndpointTests(unittest.TestCase):
    def setUp(self) -> None:
        root = Path.cwd()
        prompt = root / "prompt.md"
        self.request = AgentLaunchRequest(
            run_id="r", node_id="n", role="implementer", cwd=str(root),
            prompt_path=str(prompt), output_dir=str(root / "unused-test-output"),
            capability_class="reasoning", effort="high", model="glm-5.1",
            provider_effort=None, read_only=False,
        )

    def adapter(self, options: dict) -> ClaudeCodeAdapter:
        adapter = ClaudeCodeAdapter({"id": "zai-coding", "options": options})
        adapter._probe = ProviderStatus("zai-coding", True, executable="claude", version="1")
        return adapter

    def test_endpoint_and_secret_are_launch_env_only(self) -> None:
        adapter = self.adapter({
            "env": {
                "ANTHROPIC_BASE_URL": "https://api.z.ai/api/anthropic",
                "ANTHROPIC_DEFAULT_SONNET_MODEL": "glm-5.1",
                "API_TIMEOUT_MS": "60000",
            },
            "secret_env": {"ANTHROPIC_AUTH_TOKEN": REFERENCE},
        })
        inherited = {
            "ANTHROPIC_API_KEY": "operator-api-key-placeholder",
            "ANTHROPIC_AUTH_TOKEN": "operator-auth-token-placeholder",
            "ANTHROPIC_BASE_URL": "https://operator.example",
        }
        with mock.patch.dict(os.environ, inherited), mock.patch(
            "agent_os.orchestrator.secret_refs.resolve", return_value=PLACEHOLDER_SECRET
        ), mock.patch("agent_os.orchestrator.adapters.base.subprocess.Popen") as popen, \
                mock.patch("pathlib.Path.mkdir"), mock.patch("pathlib.Path.write_text") as write_text, \
                mock.patch("builtins.open", mock.mock_open(read_data=b"test prompt")):
            popen.return_value.pid = 123
            plan = adapter.resolve_invocation(self.request)
            adapter.start(self.request)

        self.assertNotIn("ANTHROPIC_API_KEY", plan.env)
        self.assertEqual(plan.env["ANTHROPIC_AUTH_TOKEN"], PLACEHOLDER_SECRET)
        self.assertEqual(plan.env["ANTHROPIC_BASE_URL"], "https://api.z.ai/api/anthropic")
        self.assertEqual(plan.env["ANTHROPIC_DEFAULT_SONNET_MODEL"], "glm-5.1")
        self.assertEqual(plan.env["API_TIMEOUT_MS"], "60000")
        self.assertEqual(popen.call_args.kwargs["env"]["ANTHROPIC_AUTH_TOKEN"], PLACEHOLDER_SECRET)
        persisted = write_text.call_args.args[0]
        for text in (plan.display, " ".join(plan.argv), persisted):
            self.assertNotIn(PLACEHOLDER_SECRET, text)
            self.assertNotIn(inherited["ANTHROPIC_API_KEY"], text)
        self.assertNotIn('"env"', persisted)

    def test_each_option_alone_scrubs_operator_connection(self) -> None:
        inherited = {
            "ANTHROPIC_API_KEY": "operator-api-key-placeholder",
            "ANTHROPIC_AUTH_TOKEN": "operator-auth-token-placeholder",
            "ANTHROPIC_BASE_URL": "https://operator.example",
        }
        for options in ({"env": {"ANTHROPIC_DEFAULT_SONNET_MODEL": "glm-5.1"}},
                        {"secret_env": {"ANTHROPIC_AUTH_TOKEN": REFERENCE}}):
            with self.subTest(options=options), mock.patch.dict(os.environ, inherited), mock.patch(
                "agent_os.orchestrator.secret_refs.resolve", return_value=PLACEHOLDER_SECRET
            ):
                env = self.adapter(options).resolve_invocation(self.request).env
                self.assertNotIn("ANTHROPIC_API_KEY", env)
                self.assertNotIn("ANTHROPIC_BASE_URL", env)
                self.assertNotEqual(env.get("ANTHROPIC_AUTH_TOKEN"), inherited["ANTHROPIC_AUTH_TOKEN"])

    def test_plain_env_rejects_disallowed_and_secret_names(self) -> None:
        for name in ("OPENAI_BASE_URL", "ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN",
                     "CLAUDE_CLIENT_SECRET", "CLAUDE_api_key"):
            with self.subTest(name=name), self.assertRaisesRegex(RuntimeError, "disallowed name"):
                self.adapter({"env": {name: "invalid"}}).resolve_invocation(self.request)

    def test_probe_reports_unconfigured_secret_reference(self) -> None:
        adapter = self.adapter({"secret_env": {"ANTHROPIC_AUTH_TOKEN": REFERENCE}})
        with mock.patch("agent_os.orchestrator.secret_refs.resolve", return_value=None):
            status = adapter.probe()
            self.assertFalse(status.available)
            self.assertIn(REFERENCE, status.reason)
            with self.assertRaisesRegex(RuntimeError, REFERENCE):
                adapter.resolve_invocation(self.request)

    def test_probe_tolerates_missing_or_invalid_secret_env(self) -> None:
        self.assertTrue(self.adapter({"secret_env": None}).probe().available)
        status = self.adapter({"secret_env": ["not", "a", "dict"]}).probe()
        self.assertFalse(status.available)
        self.assertIn("secret_env", status.reason)


if __name__ == "__main__":
    unittest.main()
