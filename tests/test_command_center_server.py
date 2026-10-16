from __future__ import annotations

import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from agent_os.executive.keep_awake import KeepAwake
from agent_os.executive.window import server
from agent_os.executive.window.registry import Registry


class RequestSocket:
    """Exercise the real HTTP handler entirely in memory, without sockets."""
    def __init__(self, request):
        self.input = io.BytesIO(request)
        self.output = bytearray()

    def makefile(self, *args):
        return self.input

    def sendall(self, data):
        self.output.extend(data)


def request(api, method, path, body=None, *, host="localhost:1234", token="session"):
    data = json.dumps(body or {}).encode()
    headers = f"{method} {path} HTTP/1.0\r\nHost: {host}\r\nContent-Length: {len(data)}\r\n"
    if token is not None:
        headers += f"X-Agent-OS-Token: {token}\r\n"
    socket = RequestSocket(headers.encode() + b"\r\n" + data)
    server.make_handler(api, "session", {"localhost:1234", "pc.tailnet.ts.net"})(socket, ("127.0.0.1", 1), SimpleNamespace())
    header, payload = bytes(socket.output).split(b"\r\n\r\n", 1)
    return int(header.split()[1]), json.loads(payload)


class CommandCenterServerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name)
        self.repo = self.home / "project"
        self.repo.mkdir()
        self.registry = Registry()
        self.api = server.Api(self.registry, Mock(), self.home, transport=Mock(), gateway_factory=Mock(),
                              usage_home=self.home, wake=KeepAwake(platform="linux"),
                              orchestrator_url="http://127.0.0.1:9876/", remote_hosts=("pc.tailnet.ts.net",))

    def test_get_usage_uses_shared_summary(self):
        with patch.object(server.usage_hub, "summary", return_value={"plans": []}) as summary:
            self.assertEqual(self.api.get("/api/usage", {}), {"plans": []})
        summary.assert_called_once_with(home=self.home)

    def test_extras_updates_only_local_status(self):
        out = self.api.post("/api/extras", {"id": "claude-cloud-credit", "status": "used"})
        self.assertEqual(out["status"], "used")
        self.assertTrue((self.home / "plan-extras.json").exists())
        with self.assertRaises(ValueError):
            self.api.post("/api/extras", {"id": "unknown", "status": "used"})

    def test_url_allowlist_rejects_credentials_subdomains_and_schemes(self):
        with patch.object(server.webbrowser, "open", return_value=True) as opener:
            for host in ("claude.ai", "chatgpt.com", "nano-gpt.com", "openrouter.ai", "github.com"):
                self.assertTrue(self.api.post("/api/open-url", {"url": f"https://{host}/settings"})["opened"])
            self.assertEqual(opener.call_count, 5)
            for url in ("http://claude.ai/", "https://claude.ai.evil.test/", "https://evil.test/claude.ai", "file:///anything",
                        "https://user@claude.ai/", "https://claude.ai:444/", "https://claude.ai\\evil.test/", "https://claude.ai/\n"):
                with self.subTest(url=url), self.assertRaises(ValueError):
                    self.api.post("/api/open-url", {"url": url})
            self.assertEqual(opener.call_count, 5)

    def test_chat_read_routes_and_send_delete(self):
        with patch.object(server.chat_hub, "providers", return_value=[{"id": "fake"}]) as providers, \
             patch.object(server.chat_hub, "conversations", return_value=[{"id": "c"}]) as conversations, \
             patch.object(server.chat_hub, "conversation", return_value={"turns": []}) as conversation, \
             patch.object(server.chat_hub, "send", return_value={"reply": "hi", "error": None}) as send, \
             patch.object(server.chat_hub, "delete", return_value={"deleted": "c"}) as delete:
            self.assertEqual(self.api.get("/api/chat/providers", {}), [{"id": "fake"}])
            self.assertEqual(self.api.get("/api/chat/conversations", {}), [{"id": "c"}])
            self.assertEqual(self.api.get("/api/chat/conversation", {"id": ["c"]}), {"turns": []})
            out = self.api.post("/api/chat/send", {"conversation_id": "c", "provider": "fake", "model": "m", "text": "hello", "project": "p"})
            self.assertEqual(out["reply"], "hi")
            send.assert_called_once_with("c", "fake", "m", "hello", project="p", home=self.home)
            conversation.assert_called_once_with(self.home, "c")
            conversations.assert_called_once_with(self.home)
            providers.assert_called_once_with()
            self.assertEqual(self.api.post("/api/chat/delete", {"id": "c"}), {"deleted": "c"})
            delete.assert_called_once_with(self.home, "c")

    def test_chat_request_counts_busy_and_releases_on_failure(self):
        def failed(*args, **kwargs):
            self.assertEqual(self.api.wake._requests, 1)
            raise ValueError("failed")
        with patch.object(server.chat_hub, "send", side_effect=failed), self.assertRaises(ValueError):
            self.api.post("/api/chat/send", {"text": "hello"})
        self.assertEqual(self.api.wake._requests, 0)

    def test_projects_list_and_resume_association(self):
        rows = [{"id": "p", "claude_sessions": [{"id": "s"}], "codex_sessions": [], "cloud_sessions": []}]
        with patch.object(server.projects_view, "projects", return_value=rows) as projects, \
             patch.object(server.projects_view, "project_path", return_value=self.repo), \
             patch.object(server.projects_view, "resume_command", return_value={"opened": True}) as resume:
            self.assertEqual(self.api.get("/api/projects", {}), rows)
            self.assertTrue(self.api.post("/api/projects/resume", {"kind": "claude", "session_id": "s", "project": "p"})["opened"])
            resume.assert_called_once_with("claude", "s", self.repo)
            for kind, id in [("codex", "s"), ("claude", "foreign"), ("other", "s")]:
                with self.assertRaises(ValueError):
                    self.api.post("/api/projects/resume", {"kind": kind, "session_id": id, "project": "p"})
            self.assertEqual(resume.call_count, 1)
        self.assertEqual(projects.call_args.kwargs, {"state_home": self.home})

    def cloud_patches(self, **kwargs):
        return patch.multiple(server.cloud_lane, preflight=Mock(return_value={"branch": "main", "repo": str(self.repo)}),
                              submit=Mock(**kwargs))

    def test_cloud_preview_cannot_submit_and_confirm_is_once(self):
        with patch.object(server.projects_view, "project_path", return_value=self.repo), \
             self.cloud_patches(return_value={"session_id": "session_cloud"}) as _:
            preview = self.api.post("/api/cloud/preview", {"project": "p", "task": "do work"})
            self.assertEqual(preview["preview"]["task"], "do work")
            server.cloud_lane.submit.assert_not_called()
            out = self.api.post("/api/confirm", {"confirm_token": preview["confirm_token"]})
            self.assertEqual(out["result"]["session_id"], "session_cloud")
            server.cloud_lane.submit.assert_called_once_with(self.repo, "do work", home=self.home)
            with self.assertRaises(KeyError):
                self.api.post("/api/confirm", {"confirm_token": preview["confirm_token"]})
            self.assertEqual(server.cloud_lane.submit.call_count, 1)
        audit = (self.home / "audit.jsonl").read_text(encoding="utf-8")
        self.assertNotIn("do work", audit)

    def test_cloud_sensitive_and_failed_preflight_create_no_token(self):
        with patch.object(server.projects_view, "project_path", return_value=self.home / "HR GUI"), self.cloud_patches():
            with self.assertRaises(ValueError):
                self.api.post("/api/cloud/preview", {"project": "p", "task": "secret"})
            server.cloud_lane.preflight.assert_not_called()
            server.cloud_lane.submit.assert_not_called()
        with patch.object(server.projects_view, "project_path", return_value=self.repo), \
             patch.object(server.cloud_lane, "preflight", side_effect=ValueError("dirty")):
            with self.assertRaises(ValueError):
                self.api.post("/api/cloud/preview", {"project": "p", "task": "task"})
        self.assertEqual(self.api.pending.list(), [])

    def test_confirm_rechecks_branch_path_and_sensitive_policy(self):
        for change in ("branch", "path", "sensitive", "dirty"):
            with self.subTest(change=change), patch.object(server.projects_view, "project_path", return_value=self.repo) as path, \
                 self.cloud_patches():
                preview = self.api.post("/api/cloud/preview", {"project": "p", "task": "task"})
                if change == "path":
                    path.return_value = self.home
                elif change == "branch":
                    server.cloud_lane.preflight.return_value = {"branch": "other"}
                elif change == "dirty":
                    server.cloud_lane.preflight.side_effect = ValueError("dirty")
                else:
                    (self.home / "sensitive-repos.json").write_text(json.dumps([self.repo.name]), encoding="utf-8")
                with self.assertRaises(ValueError):
                    self.api.post("/api/confirm", {"confirm_token": preview["confirm_token"]})
                server.cloud_lane.submit.assert_not_called()
                self.assertEqual(self.api.pending.list(), [])
                if change == "sensitive":
                    (self.home / "sensitive-repos.json").write_text("[]", encoding="utf-8")

    def test_dismiss_cloud_preview_never_submits(self):
        with patch.object(server.projects_view, "project_path", return_value=self.repo), self.cloud_patches():
            preview = self.api.post("/api/cloud/preview", {"project": "p", "task": "task"})
            self.api.post("/api/dismiss", {"confirm_token": preview["confirm_token"]})
            self.assertEqual(self.api.pending.list(), [])
            server.cloud_lane.submit.assert_not_called()

    def test_expired_cloud_preview_cannot_submit(self):
        with patch.object(server.projects_view, "project_path", return_value=self.repo), self.cloud_patches():
            preview = self.api.post("/api/cloud/preview", {"project": "p", "task": "task"})
            self.api.pending.ttl_seconds = -1
            with self.assertRaises(KeyError):
                self.api.post("/api/confirm", {"confirm_token": preview["confirm_token"]})
            server.cloud_lane.submit.assert_not_called()

    def test_cloud_errors_are_not_logged_or_returned_and_request_is_released(self):
        with patch.object(server.projects_view, "project_path", return_value=self.repo), self.cloud_patches(side_effect=RuntimeError("secret-value")):
            preview = self.api.post("/api/cloud/preview", {"project": "p", "task": "task"})
            with self.assertRaisesRegex(ValueError, "^cloud submission failed$"):
                self.api.post("/api/confirm", {"confirm_token": preview["confirm_token"]})
        self.assertEqual(self.api.wake._requests, 0)
        self.assertNotIn("secret-value", (self.home / "audit.jsonl").read_text())

    def test_config_round_trip_and_validation(self):
        config = self.api.get("/api/config", {})
        self.assertEqual(config["orchestrator_url"], "http://127.0.0.1:9876/")
        self.assertEqual(config["remote_hosts"], ["pc.tailnet.ts.net"])
        self.api.post("/api/config", {"keep_awake": False})
        self.assertFalse(self.api.get("/api/config", {})["keep_awake"])
        other = server.Api(self.registry, Mock(), self.home, transport=Mock(), gateway_factory=Mock(), usage_home=self.home)
        self.assertFalse(other.wake.enabled)
        for value in ("false", 1, None):
            with self.assertRaises(ValueError):
                self.api.post("/api/config", {"keep_awake": value})

    def test_every_new_post_requires_token_and_checked_host(self):
        spy = SimpleNamespace(post=Mock(return_value={"ok": True}), get=Mock(return_value={"ok": True}))
        for path in ("/api/extras", "/api/open-url", "/api/chat/send", "/api/chat/delete", "/api/projects/resume",
                     "/api/cloud/preview", "/api/config", "/api/confirm"):
            with self.subTest(path=path):
                self.assertEqual(request(spy, "POST", path, token=None)[0], 403)
                self.assertEqual(request(spy, "POST", path, token="wrong")[0], 403)
                self.assertEqual(request(spy, "POST", path + "?token=session", token=None)[0], 403)
                self.assertEqual(request(spy, "POST", path, host="evil.test")[0], 403)
                self.assertEqual(request(spy, "POST", path, host="pc.tailnet.ts.net")[0], 200)
        self.assertEqual(spy.post.call_count, 8)

    def test_get_routes_are_host_checked_and_parse_query(self):
        spy = SimpleNamespace(get=Mock(return_value={"ok": True}))
        for path in ("/api/usage", "/api/chat/providers", "/api/chat/conversations", "/api/chat/conversation?id=c", "/api/projects", "/api/config"):
            self.assertEqual(request(spy, "GET", path, host="evil.test")[0], 403)
            self.assertEqual(request(spy, "GET", path)[0], 200)
        self.assertEqual(spy.get.call_count, 6)
        self.assertIn(unittest.mock.call("/api/chat/conversation", {"id": ["c"]}), spy.get.call_args_list)

    def test_build_server_remote_hosts_do_not_change_binding(self):
        fake = SimpleNamespace(server_address=("127.0.0.1", 1234))
        with patch.object(server, "_bind_exclusive", return_value=fake) as bind:
            built, token = server.build_server(registry=self.registry, bridge=Mock(), home=self.home, transport=Mock(),
                           gateway_factory=Mock(), usage_home=self.home, wake=self.api.wake, remote_hosts=("PC.TAILNET.TS.NET",))
        self.assertEqual(bind.call_args.args[:2], ("127.0.0.1", 0))
        self.assertEqual(built.api.remote_hosts, ["pc.tailnet.ts.net"])
        with self.assertRaises(ValueError):
            server.build_server(host="0.0.0.0")
        for host in ("https://pc.test", "*.test", "user@pc.test", "pc.test/path", "pc.test:99999", "pc.test\n"):
            with self.assertRaises(ValueError):
                server._remote_host(host)


if __name__ == "__main__":
    unittest.main()
