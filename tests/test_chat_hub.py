from __future__ import annotations

import io
import json
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.executive import chat_hub as hub
from agent_os.orchestrator.router import ProviderRegistry


class Response(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


class ChatHubTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name)
        for target, value in [("secret_refs.status", {"configured": False}), ("usage_hub._home", self.home),
                              ("usage_hub.plans", []), ("model_profile.sensitive_repos", {"hr gui"})]:
            mock = patch.object(hub.secret_refs if target.startswith("secret_refs") else
                                hub.usage_hub if target.startswith("usage_hub") else hub.model_profile,
                                target.split(".")[1], return_value=value)
            mock.start()
            self.addCleanup(mock.stop)
        self.addCleanup(patch.stopall)
        self.registry = ProviderRegistry(providers=[
            {"id": "claude", "adapter": "claude_code", "models": {"balanced": "sonnet", "fast": "sonnet"}},
            {"id": "codex", "adapter": "codex_cli", "models": {"balanced": "gpt"}},
            {"id": "api", "adapter": "openai_api", "models": {"balanced": "api-model"},
             "options": {"base_url": "https://example.test/api/v1", "secret_ref": "secrets://test/default"}},
            {"id": "local", "adapter": "openai_api", "models": {"balanced": "local-model"},
             "options": {"base_url": "http://127.0.0.1:8080"}},
            {"id": "disabled", "adapter": "claude_code", "enabled": False, "models": {"balanced": "no"}},
            {"id": "other", "adapter": "anthropic_api", "models": {"balanced": "no"}},
        ])
        self.requests = []

    def opener(self, request, **kwargs):
        self.requests.append(request)
        return Response(json.dumps({"choices": [{"message": {"content": "API answer"}}],
                                    "usage": {"prompt_tokens": 12, "completion_tokens": 3}}).encode())

    def send(self, provider="api", model="api-model", text="hello", **kwargs):
        with patch("agent_os.orchestrator.secret_refs.resolve", return_value="test-secret"), \
             patch("agent_os.orchestrator.adapters.http_api._price_cost", return_value=None):
            return hub.send("c1", provider, model, text, home=self.home, registry=self.registry,
                            opener=kwargs.pop("opener", self.opener), context_builder=kwargs.pop("context_builder", lambda *args: ""), **kwargs)

    def test_provider_metadata_is_unique_private_and_has_headroom(self):
        with patch.object(hub.usage_hub, "plans", return_value=[{"providers": ["claude"], "state": "tight"}]):
            rows = {p["id"]: p for p in hub.providers(self.registry)}
        self.assertEqual(set(rows), {"claude", "codex", "api", "local"})
        self.assertEqual(rows["claude"]["models"], ["sonnet"])
        self.assertEqual(rows["claude"]["headroom"], "tight")
        self.assertTrue(rows["local"]["sensitive_ok"])
        self.assertFalse(rows["api"]["sensitive_ok"])
        self.assertNotIn("options", rows["api"])

    def test_free_provider_only_when_configured_and_uses_catalog(self):
        inputs = SimpleNamespace(catalog={"models": [{"slug": "one:free"}, {"slug": "one:free"}, {"slug": "two:free"}]})
        with patch.object(hub.secret_refs, "status", return_value={"configured": True}), \
             patch("agent_os.orchestrator.free_dispatch.FreeInputs.load_default", return_value=inputs):
            free = next(p for p in hub.providers(self.registry) if p["id"] == "openrouter-free")
        self.assertEqual(free["models"], ["one:free", "two:free"])
        self.assertFalse(free["sensitive_ok"])

    def test_sensitive_rejected_before_context_or_dispatch(self):
        context = Mock(side_effect=AssertionError("context must not load"))
        out = self.send(project="work", project_resolver=lambda _: {"path": str(self.home / "HR GUI")}, context_builder=context)
        self.assertIn("Sensitive", out["error"])
        context.assert_not_called()
        self.assertEqual(self.requests, [])
        self.assertFalse((self.home / "chats").exists())

    def test_sensitive_local_provider_cannot_override_chat_to_a_remote_host(self):
        local = self.registry.get("local")
        local["options"]["paths"] = {"chat": "https://example.test/chat/completions"}
        context = Mock()
        out = self.send("local", "local-model", project="work", context_builder=context,
                        project_resolver=lambda _: {"path": str(self.home / "HR GUI")})
        self.assertIn("Sensitive", out["error"])
        self.assertFalse(self.requests)
        context.assert_not_called()

    def test_redirects_are_refused_without_following_them(self):
        self.assertIsNone(hub._NoRedirect().redirect_request(None, None, 302, "redirect", {}, "https://other.test"))

    def test_unknown_project_and_provider_model_fail_without_call(self):
        resolver = Mock(side_effect=KeyError("missing"))
        self.assertEqual(self.send(project="missing", project_resolver=resolver)["error"], "Unknown project")
        self.assertTrue(self.send(model="arbitrary")["error"])
        self.assertTrue(self.send(provider="disabled", model="no")["error"])
        self.assertEqual(self.requests, [])

    def test_api_request_context_history_persistence_and_usage(self):
        out = self.send(project="p", project_resolver=lambda _: {"path": str(self.home)}, context_builder=lambda *_: "project context")
        self.assertIsNone(out["error"])
        self.assertEqual(out["usage"]["input_tokens"], 12)
        self.send(text="again", project="p", project_resolver=lambda _: {"path": str(self.home)})
        request = self.requests[0]
        self.assertEqual(request.full_url, "https://example.test/api/v1/chat/completions")
        self.assertEqual(request.get_header("Authorization"), "Bearer test-secret")
        body = json.loads(request.data)
        self.assertEqual(body["messages"][0], {"role": "system", "content": "project context"})
        self.assertEqual(set(body), {"model", "messages"})
        self.assertEqual(len(json.loads(self.requests[1].data)["messages"]), 3)
        record = hub.conversation(self.home, "c1")
        self.assertEqual(len(record["turns"]), 4)
        self.assertTrue(record["turns"][0]["at"])
        self.assertNotIn("test-secret", json.dumps(record))
        self.assertNotIn("turns", hub.conversations(self.home)[0])

    def test_default_context_uses_budget(self):
        with patch("agent_os.chat.context", return_value={"context": "compact"}) as context:
            self.assertIn("compact", hub._context("query", "project"))
        context.assert_called_once_with(query="query", project_hint="project", token_budget=1500)
        self.assertEqual(hub._context("query", None), "")

    def test_history_is_bounded_and_routing_cannot_change(self):
        self.send()
        record = hub.conversation(self.home, "c1")
        record["turns"] = [{"role": "user", "text": str(i), "at": "now"} for i in range(30)]
        hub._write_json(self.home / "chats" / "c1.json", record)
        self.send(text="next")
        messages = json.loads(self.requests[-1].data)["messages"]
        self.assertEqual(len(messages), 21)
        self.assertEqual(messages[0]["content"], "10")
        before = len(self.requests)
        self.assertTrue(self.send(project="new")["error"])
        self.assertTrue(self.send(provider="local", model="local-model")["error"])
        self.assertEqual(len(self.requests), before)

    def test_claude_model_mcp_resume_and_sensitive_allowed(self):
        calls = []
        def runner(argv, **kwargs):
            calls.append(argv)
            return SimpleNamespace(returncode=0, stdout=json.dumps({"result": "Claude answer", "session_id": "session-1"}), stderr="")
        for text in ("first", "second"):
            out = self.send("claude", "sonnet", text, runner=runner, project="sensitive",
                            project_resolver=lambda _: {"path": str(self.home / "HR GUI")})
            self.assertIsNone(out["error"])
        self.assertEqual(calls[0][calls[0].index("--model") + 1], "sonnet")
        self.assertIn("--strict-mcp-config", calls[0])
        self.assertEqual(calls[0][calls[0].index("--tools") + 1], "")
        self.assertEqual(calls[1][calls[1].index("--resume") + 1], "session-1")
        config = json.loads((self.home / "chats" / "c1" / "mcp-config.json").read_text())
        self.assertEqual(config["mcpServers"]["agent-os"]["args"][-1], "mcp")

    def test_claude_pending_previews_use_the_window_home(self):
        runner = Mock(return_value=SimpleNamespace(returncode=0, stdout=json.dumps({"result": "hi", "session_id": "s"}), stderr=""))
        self.send("claude", "sonnet", runner=runner)
        self.assertEqual(runner.call_args.kwargs["env"]["AGENT_OS_EXECUTIVE_WINDOW_HOME"], str(self.home))

    def test_codex_jsonl_final_message_usage_and_mcp_flags(self):
        events = [{"type": "item.completed", "item": {"type": "agent_message", "text": "draft"}},
                  {"type": "item.completed", "item": {"type": "agent_message", "text": "final"}},
                  {"type": "turn.completed", "usage": {"input_tokens": 10}}]
        runner = Mock(return_value=SimpleNamespace(returncode=0, stdout="garbage\n" + "\n".join(map(json.dumps, events))))
        out = self.send("codex", "gpt", runner=runner)
        self.assertEqual(out["reply"], "final")
        self.assertEqual(out["usage"], {"input_tokens": 10})
        argv = runner.call_args.args[0]
        for flag in ("--json", "--skip-git-repo-check", "read-only", "-m"):
            self.assertIn(flag, argv)
        self.assertTrue(any("mcp_servers.agent-os.command=" in arg for arg in argv))
        self.assertTrue(any('"mcp"' in arg for arg in argv))
        self.assertEqual(runner.call_args.kwargs["env"]["AGENT_OS_EXECUTIVE_WINDOW_HOME"], str(self.home))

    def test_codex_history_is_last_ten_turns_and_failures_stay_private(self):
        events = json.dumps({"type": "item.completed", "item": {"type": "agent_message", "text": "reply"}})
        runner = Mock(return_value=SimpleNamespace(returncode=0, stdout=events))
        self.send("codex", "gpt", runner=runner)
        record = hub.conversation(self.home, "c1")
        record["turns"] = [{"role": "user", "text": "TURN-" + str(i), "at": "now"} for i in range(30)]
        hub._write_json(self.home / "chats" / "c1.json", record)
        self.send("codex", "gpt", runner=runner)
        prompt = runner.call_args.args[0][-1]
        self.assertIn("TURN-20", prompt)
        self.assertNotIn("TURN-19", prompt)
        runner.return_value = SimpleNamespace(returncode=0, stdout=json.dumps({"type": "turn.failed", "error": "secret"}))
        self.assertEqual(self.send("codex", "gpt", runner=runner)["error"], "Codex request failed")
        self.assertEqual(len(hub.conversation(self.home, "c1")["turns"]), 32)

    def test_failures_do_not_return_secrets_or_write_failed_turn(self):
        def failed(request, **kwargs):
            raise RuntimeError("test-secret private prompt")
        out = self.send(opener=failed)
        self.assertEqual(out["error"], "Provider request failed")
        self.assertNotIn("test-secret", json.dumps(out))
        self.assertEqual(hub.conversations(self.home), [])

    def test_missing_secret_ref_never_falls_back_to_another_key(self):
        with patch("agent_os.orchestrator.adapters.http_api.OpenAiCompatibleAdapter.key", return_value=None):
            out = self.send()
        self.assertIn("secret", out["error"])
        self.assertFalse(self.requests)

    def test_response_secret_is_redacted_before_persisting(self):
        def echo(request, **kwargs):
            return Response(json.dumps({"choices": [{"message": {"content": "test-secret"}}]}).encode())
        out = self.send(opener=echo)
        self.assertEqual(out["reply"], "[redacted]")
        self.assertNotIn("test-secret", json.dumps(hub.conversation(self.home, "c1")))

    def test_pasted_provider_key_is_not_stored_in_title_or_turns(self):
        self.send(text="test-secret")
        self.assertNotIn("test-secret", json.dumps(hub.conversation(self.home, "c1")))
        self.assertEqual(hub._redact({'reply': 'key"with-quotes'}, 'key"with-quotes'), {"reply": "[redacted]"})

    def test_free_quota_guard_and_reservation(self):
        governor = Mock()
        governor.can_spend.return_value = (False, "blocked")
        inputs = SimpleNamespace(catalog={"models": [{"slug": "one:free"}]}, governor=governor)
        with patch.object(hub.secret_refs, "status", return_value={"configured": True}), \
             patch("agent_os.orchestrator.free_dispatch.FreeInputs.load_default", return_value=inputs):
            self.assertEqual(self.send("openrouter-free", "one:free")["error"], "Free quota unavailable")
            self.assertEqual(self.requests, [])
            governor.record.assert_not_called()
            governor.can_spend.return_value = (True, "ok")
            self.assertIsNone(self.send("openrouter-free", "one:free")["error"])
            governor.record.assert_called_once()
            self.assertEqual(self.requests[0].full_url, "https://openrouter.ai/api/v1/chat/completions")

    def test_delete_tombstones_and_bad_ids_cannot_traverse(self):
        self.send()
        hub.delete(self.home, "c1")
        self.assertEqual(hub.conversations(self.home), [])
        with self.assertRaises(KeyError):
            hub.conversation(self.home, "c1")
        self.assertTrue(self.send()["error"])
        for id in ("../outside", "x/y", "", "-" * 101):
            with self.subTest(id=id), self.assertRaises(ValueError):
                hub.send(id, "claude", "sonnet", "hello", home=self.home, registry=self.registry)

    def test_separate_conversations_do_not_block_each_other(self):
        entered = threading.Event()
        release = threading.Event()
        def slow(request, **kwargs):
            entered.set()
            self.assertTrue(release.wait(3))
            return self.opener(request, **kwargs)
        with patch("agent_os.orchestrator.secret_refs.resolve", return_value="test-secret"), \
             patch("agent_os.orchestrator.adapters.http_api._price_cost", return_value=None):
            first = threading.Thread(target=lambda: hub.send("first", "api", "api-model", "hello", home=self.home,
                                     registry=self.registry, opener=slow, context_builder=lambda *_: ""))
            first.start()
            try:
                self.assertTrue(entered.wait(2))
                self.assertIsNone(self.send()["error"])
            finally:
                release.set()
                first.join(3)
            self.assertFalse(first.is_alive())


if __name__ == "__main__":
    unittest.main()
