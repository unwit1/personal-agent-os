import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

import json
import os
import tempfile
import unittest
from types import SimpleNamespace

from agent_os.executive.window import model_bridge as mb


class FakeRunner:
    def __init__(self, *outputs):
        self.outputs = list(outputs)
        self.calls = []

    def __call__(self, argv, **kwargs):
        self.calls.append((argv, kwargs))
        return self.outputs.pop(0)


def ok(sid, result="hi"):
    return SimpleNamespace(returncode=0, stderr="", stdout=json.dumps(
        {"result": result, "session_id": sid, "is_error": False}))


class BridgeTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.home = Path(self._tmp.name)

    def test_mcp_config_names_one_server(self):
        path = mb.mcp_config(self.home / "c.json")
        cfg = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(list(cfg["mcpServers"]), ["agent-os"])
        server = cfg["mcpServers"]["agent-os"]
        self.assertEqual(server["command"], sys.executable)
        self.assertTrue(server["args"][0].endswith("agent.py"))
        self.assertEqual(server["args"][1], "mcp")

    def test_first_and_second_call_argv(self):
        runner = FakeRunner(ok("sid-1"), ok("sid-1"))
        bridge = mb.ChatBridge(self.home, runner=runner)
        first = bridge.send("c1", "hello")
        self.assertEqual(first, {"reply": "hi", "session_id": "sid-1", "error": None})
        cfg = str(self.home / "mcp-config.json")
        expected = ["claude", "-p", "hello", "--output-format", "json",
                    "--mcp-config", cfg, "--strict-mcp-config",
                    "--allowedTools", "mcp__agent-os__*",
                    "--disallowedTools", ",".join(mb.BUILTIN_TOOLS)]
        self.assertEqual(runner.calls[0][0], expected)
        bridge.send("c1", "again")
        argv = runner.calls[1][0]
        self.assertEqual(argv[-2:], ["--resume", "sid-1"])
        self.assertEqual(json.loads((self.home / "sessions.json").read_text())["c1"], "sid-1")
        # new bridge instance reloads sessions; other conversation has none
        runner2 = FakeRunner(ok("sid-2"))
        mb.ChatBridge(self.home, runner=runner2).send("c2", "x")
        self.assertNotIn("--resume", runner2.calls[0][0])

    def test_allowlist_only_agent_os(self):
        argv = mb.build_invocation("p", None, "cfg.json")
        allowed = argv[argv.index("--allowedTools") + 1:argv.index("--allowedTools") + 2]
        self.assertTrue(all(a.startswith("mcp__agent-os__") for a in allowed))
        for tool in ("Bash", "Edit", "Write", "WebFetch"):
            self.assertIn(tool, argv[argv.index("--disallowedTools") + 1].split(","))

    def test_no_api_key_set(self):
        before = os.environ.get("ANTHROPIC_API_KEY")
        runner = FakeRunner(ok("s"))
        mb.ChatBridge(self.home, runner=runner).send("c", "t")
        self.assertEqual(os.environ.get("ANTHROPIC_API_KEY"), before)
        argv, kwargs = runner.calls[0]
        self.assertNotIn("env", kwargs)
        self.assertFalse(any("ANTHROPIC_API_KEY" in a for a in argv))

    def test_errors_surfaced(self):
        err = SimpleNamespace(returncode=1, stderr="", stdout=json.dumps(
            {"result": "boom", "session_id": "s", "is_error": True}))
        crash = SimpleNamespace(returncode=2, stderr="not logged in", stdout="")
        bridge = mb.ChatBridge(self.home, runner=FakeRunner(err, crash))
        self.assertEqual(bridge.send("c", "t")["error"], "boom")
        self.assertEqual(bridge.send("c", "t")["error"], "not logged in")

        def missing(argv, **kw):
            raise FileNotFoundError("claude")
        out = mb.ChatBridge(self.home, runner=missing).send("c", "t")
        self.assertIn("FileNotFoundError", out["error"])

    def test_option_prompt(self):
        item = {"id": "i-1", "title": "Reply to Bob", "why": "unanswered", "context": {"thread": "t9"}}
        action = {"action_id": "mail.reply", "label": "Respond", "consequential": True}
        text = mb.option_prompt(item, action)
        for part in ("i-1", "Reply to Bob", "unanswered", "t9", "mail.reply", "executive_window.run", "preview", "confirm"):
            self.assertIn(part, text)


if __name__ == "__main__":
    unittest.main()
