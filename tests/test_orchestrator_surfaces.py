"""Headless and GUI surfaces drive the same engine: CLI, MCP, local HTTP API."""

from __future__ import annotations

import contextlib
import http.client
import io
import json
import sys
import threading
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from test_orchestrator import PASS, OrchestratorFixture  # noqa: E402

from agent_os.cli import main  # noqa: E402
from agent_os.mcp_server import TOOL_SCHEMAS, _handle_mcp, methods  # noqa: E402
from agent_os.orchestrator import service  # noqa: E402
from agent_os.orchestrator.server import build_server  # noqa: E402


class SurfaceFixture(OrchestratorFixture):
    def setUp(self) -> None:
        super().setUp()
        service.set_engine(self.engine)
        self.addCleanup(service.set_engine, None)


class CliTests(SurfaceFixture):
    def cli(self, *argv: str) -> tuple[int, object]:
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            code = main(list(argv))
        return code, json.loads(buffer.getvalue())

    def test_headless_create_run_and_result(self) -> None:
        tasks = self.tmp / "tasks.json"
        tasks.write_text(json.dumps([self.task("a"), self.task("b", depends_on=["a"])]), encoding="utf-8")
        code, created = self.cli(
            "orchestrate", "create", "--goal", "cli goal", "--repo", str(self.repo), "--tasks", str(tasks),
            "--set", "poll_interval_seconds=0", "--set", "announce_claims=false", "--start", "--auto-continue",
        )
        self.assertEqual(code, 0)
        run_id = created["run_id"]
        code, final = self.cli("orchestrate", "run", run_id)
        self.assertEqual(code, 0, final)
        self.assertEqual(final["state"], "COMPLETE")
        code, result = self.cli("orchestrate", "result", run_id)
        self.assertEqual(result["integration"]["merged"], ["a", "b"])
        code, listed = self.cli("orchestrate", "list")
        self.assertIn(run_id, [item["run_id"] for item in listed])

    def test_headless_gate_approval_and_exit_codes(self) -> None:
        tasks = self.tmp / "tasks.json"
        tasks.write_text(json.dumps([self.task("a", approval_gate={"kind": "destructive_action", "reason": "drop table"})]), encoding="utf-8")
        _, created = self.cli("orchestrate", "create", "--goal", "g", "--repo", str(self.repo), "--tasks", str(tasks), "--set", "poll_interval_seconds=0", "--set", "announce_claims=false", "--start", "--auto-continue")
        code, stopped = self.cli("orchestrate", "run", created["run_id"])
        self.assertEqual(code, 4)
        self.assertEqual(stopped["state"], "APPROVAL_REQUIRED")
        self.cli("orchestrate", "approve", created["run_id"], stopped["gates"][0]["id"], "--note", "fine")
        code, final = self.cli("orchestrate", "run", created["run_id"])
        self.assertEqual((code, final["state"]), (0, "COMPLETE"))

    def test_start_recommended_with_validator_flag(self) -> None:
        code, final = self.cli(
            "orchestrate", "start-recommended", "--goal", "plan and build", "--repo", str(self.repo),
            "--validator", f'"{sys.executable}" -c "print(1)"', "--set", "poll_interval_seconds=0", "--set", "announce_claims=false",
        )
        self.assertEqual(code, 0, final)
        self.assertEqual(final["state"], "COMPLETE")
        self.assertTrue(final["auto_continue"])

    def test_invalid_policy_is_a_clean_error(self) -> None:
        code, output = self.cli("orchestrate", "create", "--goal", "g", "--repo", str(self.repo), "--set", "nonsense=1")
        self.assertEqual(code, 2)
        self.assertIn("unknown run policy key", output["error"])


class McpTests(SurfaceFixture):
    NAMES = (
        "orchestrate.providers", "orchestrate.create", "orchestrate.status", "orchestrate.list", "orchestrate.advance",
        "orchestrate.control", "orchestrate.decide", "orchestrate.retry", "orchestrate.reassign",
        "orchestrate.review_again", "orchestrate.override", "orchestrate.result",
    )

    def call(self, name: str, arguments: dict) -> dict:
        response = _handle_mcp({"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": name, "arguments": arguments}}, methods())
        payload = json.loads(response["result"]["content"][0]["text"])
        self.assertFalse(response["result"]["isError"], payload)
        return payload

    def test_tools_are_advertised_and_dispatchable(self) -> None:
        available = methods()
        listed = {tool["name"] for tool in _handle_mcp({"jsonrpc": "2.0", "id": 1, "method": "tools/list"}, available)["result"]["tools"]}
        for name in self.NAMES:
            self.assertIn(name, TOOL_SCHEMAS)
            self.assertIn(name, listed)
            self.assertIn(name, available)

    def test_mcp_drives_a_run_to_completion(self) -> None:
        created = self.call("orchestrate.create", {
            "goal": "mcp goal", "repository": str(self.repo), "tasks": [self.task("a")],
            "policy": {"poll_interval_seconds": 0, "announce_claims": False}, "start": True, "auto_continue": True,
        })
        advanced = self.call("orchestrate.advance", {"run_id": created["run_id"], "max_seconds": 30})
        self.assertEqual(advanced["state"], "COMPLETE")
        self.assertIn("driver_note", advanced)
        result = self.call("orchestrate.result", {"run_id": created["run_id"]})
        self.assertEqual(result["integration"]["merged"], ["a"])
        paused = self.call("orchestrate.control", {"run_id": created["run_id"], "action": "pause"})
        self.assertIn(paused["state"], {"COMPLETE", "PAUSED"})


class HttpApiTests(SurfaceFixture):
    def setUp(self) -> None:
        super().setUp()
        self.server, self.token = build_server("127.0.0.1", 0)
        self.port = self.server.server_address[1]
        thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)

    def request(self, method: str, path: str, body: dict | None = None, token: str | None = "default", host: str | None = None):
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=30)
        headers = {"Host": host or f"127.0.0.1:{self.port}"}
        if token is not None:
            headers["X-Agent-OS-Token"] = self.token if token == "default" else token
        payload = None
        if body is not None:
            payload = json.dumps(body)
            headers["Content-Type"] = "application/json"
        connection.request(method, path, body=payload, headers=headers)
        response = connection.getresponse()
        data = response.read()
        connection.close()
        return response.status, data

    def test_api_requires_token_and_loopback_host(self) -> None:
        self.assertEqual(self.request("GET", "/api/runs", token=None)[0], 401)
        self.assertEqual(self.request("GET", "/api/runs", token="wrong")[0], 401)
        self.assertEqual(self.request("POST", "/api/runs", {"goal": "x"}, token=None)[0], 401)
        self.assertEqual(self.request("GET", "/api/runs", host="evil.example:80")[0], 403)
        status, page = self.request("GET", "/", token=None)
        self.assertEqual(status, 200)
        self.assertIn(self.token.encode(), page)
        self.assertNotIn(b"__AGENT_OS_TOKEN__", page)
        self.assertEqual(self.request("GET", "/../src/agent_os/cli.py", token=None)[0], 404)

    def test_gui_api_start_recommended_drives_real_engine_to_complete(self) -> None:
        status, created = self.request("POST", "/api/runs", {
            "goal": "gui goal", "repository": str(self.repo), "validators": f'"{sys.executable}" -c "print(1)"',
            "start_recommended": True, "auto_continue": True, "policy": {"poll_interval_seconds": 0, "announce_claims": False},
        })
        self.assertEqual(status, 200, created)
        run = json.loads(created)
        self.assertTrue(run["auto_continue"])
        deadline = time.time() + 60
        state = run["state"]
        while time.time() < deadline and state != "COMPLETE":
            time.sleep(0.2)
            state = json.loads(self.request("GET", f"/api/runs/{run['run_id']}")[1])["state"]
        self.assertEqual(state, "COMPLETE")
        _, result = self.request("GET", f"/api/runs/{run['run_id']}/result")
        self.assertIn("impl", json.loads(result)["integration"]["merged"])
        _, events = self.request("GET", f"/api/runs/{run['run_id']}/events")
        self.assertIn("run.complete", {item["type"] for item in json.loads(events)})

    def test_gui_controls_pause_and_gate_decision(self) -> None:
        gate = {"kind": "destructive_action", "reason": "rewrites history"}
        status, created = self.request("POST", "/api/runs", {
            "goal": "gated", "repository": str(self.repo), "tasks": [self.task("a", approval_gate=gate)],
            "policy": {"poll_interval_seconds": 0, "announce_claims": False}, "start_recommended": True,
        })
        run_id = json.loads(created)["run_id"]
        deadline = time.time() + 30
        run = {}
        while time.time() < deadline:
            run = json.loads(self.request("GET", f"/api/runs/{run_id}")[1])
            if run["state"] == "APPROVAL_REQUIRED":
                break
            time.sleep(0.1)
        self.assertEqual(run["state"], "APPROVAL_REQUIRED")
        _, decided = self.request("POST", f"/api/runs/{run_id}/decide", {"gate_id": run["gates"][0]["id"], "approve": True})
        while time.time() < deadline:
            run = json.loads(self.request("GET", f"/api/runs/{run_id}")[1])
            if run["state"] == "COMPLETE":
                break
            time.sleep(0.1)
        self.assertEqual(run["state"], "COMPLETE")
        status, paused = self.request("POST", f"/api/runs/{run_id}/pause", {})
        self.assertEqual(status, 200)

    def test_event_stream_emits_status(self) -> None:
        run_id = self.engine.create_run("s", repository=self.repo, tasks=[self.task("a")], policy=self.policy())["run_id"]
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=10)
        connection.request("GET", f"/api/runs/{run_id}/stream?token={self.token}", headers={"Host": f"127.0.0.1:{self.port}"})
        response = connection.getresponse()
        self.assertEqual(response.getheader("Content-Type"), "text/event-stream")
        chunk = b""
        while b"event: status" not in chunk and len(chunk) < 200_000:
            chunk += response.read1(65536) if hasattr(response, "read1") else response.read(1024)
        self.assertIn(b"event: status", chunk)
        connection.close()


if __name__ == "__main__":
    unittest.main()
