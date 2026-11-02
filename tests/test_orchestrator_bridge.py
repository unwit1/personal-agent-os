"""Contract: Agent OS drives the standalone orchestrator-os package through
agent_os.orchestrator_bridge (AGENT_OS_ORCHESTRATOR_BACKEND=external).

Each check runs in a fresh interpreter because the backend is chosen when the
CLI and MCP modules are imported. Providers are synthetic only: an explicit
registry file plus an injected engine, so no installed coding CLI can be
reached, and failure learning is off so no fix run can start.
"""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HAVE_EXTERNAL = importlib.util.find_spec("orchestrator_os") is not None

SCRIPT = textwrap.dedent(r'''
    import contextlib, io, json, os, subprocess, sys
    from pathlib import Path
    tmp = Path(sys.argv[1])
    from orchestrator_os import service
    from orchestrator_os.engine import Orchestrator
    from orchestrator_os.router import ProviderRegistry
    from orchestrator_os.store import RunStore
    from orchestrator_os.adapters import synthetic
    providers = json.loads((tmp / "providers.json").read_text())["providers"]
    engine = Orchestrator(RunStore(tmp / "home"), registry=ProviderRegistry(providers=providers), sleep=lambda s: None)
    service.set_engine(engine)
    from agent_os import orchestrator_bridge
    from agent_os.cli import main
    from agent_os.mcp_server import _handle_mcp, methods
    from orchestrator_os import host
    out = {"backend": orchestrator_bridge.backend(), "host": type(host.get_host()).__name__,
           "cli_module": orchestrator_bridge.module("cli").__name__}
    def cli(*argv):
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            code = main(list(argv))
        return code, json.loads(buffer.getvalue())
    policy = ["--set", "poll_interval_seconds=0", "--set", "announce_claims=false", "--set", "failure_learning=off"]
    tasks = tmp / "tasks.json"
    tasks.write_text(json.dumps([{"id": "a", "goal": "work on a", "scope": ["synthetic"],
                                  "validators": [{"kind": "command", "command": [sys.executable, "-c", "print('ok')"]}]}]))
    code, created = cli("orchestrate", "create", "--goal", "bridge goal", "--repo", str(tmp / "repo"), "--tasks", str(tasks), *policy, "--start", "--auto-continue")
    code, final = cli("orchestrate", "run", created["run_id"])
    out["cli"] = {"code": code, "state": final["state"], "merged": final["integration"]["merged"]}
    out["cli_reason"] = final.get("state_reason")
    available = methods()
    def call(name, arguments):
        response = _handle_mcp({"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": name, "arguments": arguments}}, available)
        assert not response["result"]["isError"], response
        return json.loads(response["result"]["content"][0]["text"])
    made = call("orchestrate.create", {"goal": "mcp goal", "repository": str(tmp / "repo"),
        "tasks": [{"id": "b", "goal": "work on b", "scope": ["synthetic"], "validators": [{"kind": "command", "command": [sys.executable, "-c", "print('ok')"]}]}],
        "policy": {"poll_interval_seconds": 0, "announce_claims": False, "failure_learning": "off"}, "start": True, "auto_continue": True})
    advanced = call("orchestrate.advance", {"run_id": made["run_id"], "max_seconds": 60})
    out["mcp"] = {"state": advanced["state"]}
    from agent_os.executive.window.providers_orchestrator import orchestrator_items
    out["executive_items"] = len(orchestrator_items())
    out["paid"] = [n.get("provider") for r in service.list_runs() for n in service.status(r["run_id"])["nodes"] if n.get("provider") not in (None, "synth")]
    print("RESULT " + json.dumps(out))
''')


@unittest.skipUnless(HAVE_EXTERNAL, "orchestrator-os package not installed")
class ExternalBackendTests(unittest.TestCase):
    def test_cli_mcp_and_executive_window_drive_the_external_engine(self) -> None:
        tmp = Path(tempfile.mkdtemp(prefix="agent-os-bridge-"))
        repo = tmp / "repo"
        repo.mkdir()
        for folder in ("a", "b"):
            (repo / folder).mkdir()
            (repo / folder / ".keep").write_text("", encoding="utf-8")
        git = ["git", "-c", "user.name=fixture", "-c", "user.email=f@x"]
        subprocess.run([*git, "init", "-q", "-b", "main"], cwd=repo, check=True)
        subprocess.run([*git, "add", "-A"], cwd=repo, check=True)
        subprocess.run([*git, "commit", "-qm", "init"], cwd=repo, check=True)
        provider = {"id": "synth", "adapter": "synthetic",
                    "models": {"fast": "s", "balanced": "s", "reasoning": "s", "frontier": "s"},
                    "effort_map": {"none": "n", "low": "l", "medium": "m", "high": "h"}, "max_concurrency": 2}
        (tmp / "providers.json").write_text(json.dumps({"providers": [provider]}), encoding="utf-8")
        env = {**os.environ, "AGENT_OS_ORCHESTRATOR_BACKEND": "external", "AGENT_OS_PROVIDERS": str(tmp / "providers.json"),
               "AGENT_OS_ORCHESTRATOR_HOME": str(tmp / "home"), "PYTHONPATH": str(ROOT / "src")}
        env.pop("ORCHESTRATOR_HOST", None)
        # Belt and braces: no installed coding-agent CLI is reachable from the child.
        agent_clis = ("claude", "codex", "opencode", "gemini", "aider")
        env["PATH"] = os.pathsep.join(entry for entry in env.get("PATH", "").split(os.pathsep)
                                      if entry and not any((Path(entry) / name).exists() for name in agent_clis))
        result = subprocess.run([sys.executable, "-c", SCRIPT, str(tmp)], cwd=ROOT, env=env, capture_output=True, text=True, timeout=600)
        lines = [line for line in result.stdout.splitlines() if line.startswith("RESULT ")]
        self.assertTrue(lines, result.stdout[-2000:] + result.stderr[-3000:])
        out = json.loads(lines[-1][len("RESULT "):])
        self.assertEqual(out["backend"], "external")
        self.assertEqual(out["host"], "AgentOSHost")
        self.assertEqual(out["cli_module"], "orchestrator_os.cli")
        self.assertEqual(out["cli"], {"code": 0, "state": "COMPLETE", "merged": ["a"]}, out.get("cli_reason"))
        self.assertEqual(out["mcp"], {"state": "COMPLETE"})
        self.assertEqual(out["executive_items"], 0)
        self.assertEqual(out["paid"], [])


class InternalDefaultTests(unittest.TestCase):
    def test_default_backend_is_the_in_tree_engine(self) -> None:
        from agent_os import orchestrator_bridge

        previous = os.environ.pop(orchestrator_bridge.BACKEND_ENV, None)
        try:
            self.assertEqual(orchestrator_bridge.backend(), "internal")
            self.assertEqual(orchestrator_bridge.module("service").__name__, "agent_os.orchestrator.service")
        finally:
            if previous is not None:
                os.environ[orchestrator_bridge.BACKEND_ENV] = previous

    def test_unknown_backend_is_rejected(self) -> None:
        from agent_os import orchestrator_bridge

        os.environ[orchestrator_bridge.BACKEND_ENV] = "both"
        try:
            with self.assertRaises(ValueError):
                orchestrator_bridge.backend()
        finally:
            os.environ.pop(orchestrator_bridge.BACKEND_ENV, None)


if __name__ == "__main__":
    unittest.main()
