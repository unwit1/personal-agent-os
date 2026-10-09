"""Ingester router_command bridge: subscription CLIs only, no live model calls in tests."""
import json
import unittest
from unittest import mock

from agent_os import ingester_router as router

GEN_REQUEST = {
    "output_schema": {"concepts": {"replication.sample": {"type": "object", "required": ["text"],
                                                          "properties": {"text": {"type": "string"}}}}},
    "spans": [{"span_id": "card", "start": 0, "end": 10, "kind": "card", "text": "card text"}],
}


def envelope(model="opus", request=None):
    return {"kind": "ingester.analysis", "contract_version": "1.0", "model": model,
            "request": request or GEN_REQUEST, "prompt": "Write a new passage."}


class RouterTests(unittest.TestCase):
    def fake(self, reply, seen):
        def runner(argv, prompt, env, timeout):
            seen.update(argv=argv, prompt=prompt, env=env)
            return reply
        return runner

    def test_plain_text_reply_fills_the_single_text_concept(self):
        seen = {}
        out = router.handle(envelope(), provider="claude-code", runner=self.fake("The storm broke.", seen))
        self.assertEqual(out["drafts"], [{"concept_id": "replication.sample", "key": "sample",
                                          "value": {"text": "The storm broke."}, "evidence": [{"span_id": "card"}]}])
        self.assertEqual(out["provider"], "agent-os-router/claude-code")
        self.assertEqual(out["usage"]["cost_units"], 0)
        self.assertIn("-p", seen["argv"])
        self.assertEqual(seen["argv"][seen["argv"].index("--model") + 1], "opus")
        self.assertEqual(seen["prompt"], "Write a new passage.")

    def test_json_and_fenced_json_drafts_pass_through(self):
        drafts = [{"concept_id": "x", "key": "k", "value": 1, "evidence": []}]
        for reply in (json.dumps({"drafts": drafts}), "```json\n" + json.dumps({"drafts": drafts}) + "\n```"):
            out = router.handle(envelope(request={"output_schema": {"concepts": {"x": {}, "y": {}}}}),
                                provider="claude-code", runner=self.fake(reply, {}))
            self.assertEqual(out["drafts"], drafts)

    def test_non_json_reply_without_a_text_concept_is_an_error(self):
        with self.assertRaises(router.RouterError):
            router.handle(envelope(request={"output_schema": {"concepts": {"x": {}, "y": {}}}}),
                          provider="claude-code", runner=self.fake("not json", {}))

    def test_paid_api_keys_never_reach_the_cli(self):
        seen = {}
        with mock.patch.dict("os.environ", {"ANTHROPIC_API_KEY": "sk-test", "OPENAI_API_KEY": "sk-test", "KEEP": "1"}):
            router.handle(envelope(), provider="claude-code", runner=self.fake("text", seen))
        self.assertNotIn("ANTHROPIC_API_KEY", seen["env"])
        self.assertNotIn("OPENAI_API_KEY", seen["env"])
        self.assertEqual(seen["env"]["KEEP"], "1")

    def test_model_mapping_per_provider(self):
        self.assertEqual(router._model_for("claude-code", "sonnet"), "sonnet")
        self.assertEqual(router._model_for("claude-code", "mock-model"), "opus")
        self.assertEqual(router._model_for("codex", "opus"), "gpt-6-sol")
        self.assertEqual(router._model_for("codex", "gpt-6-astra"), "gpt-6-astra")

    def test_codex_reads_the_last_message_file(self):
        def runner(argv, prompt, env, timeout):
            out = argv[argv.index("-o") + 1]
            with open(out, "w", encoding="utf-8") as fh:
                fh.write("Codex prose.")
            self.assertIn("read-only", argv)
            return ""
        out = router.handle(envelope(model="gpt-6-sol"), provider="codex", runner=runner)
        self.assertEqual(out["drafts"][0]["value"]["text"], "Codex prose.")

    def test_rejects_unknown_kind_and_provider(self):
        with self.assertRaises(router.RouterError):
            router.handle({"kind": "other"}, provider="claude-code", runner=self.fake("x", {}))
        with self.assertRaises(router.RouterError):
            router.handle(envelope(), provider="paid-api", runner=self.fake("x", {}))

    def test_engine_parses_the_router_output(self):
        try:
            from ingester_engine.analysis_backends import parse_response
        except ImportError:
            self.skipTest("ingester_engine not importable")
        out = router.handle(envelope(), provider="claude-code", runner=self.fake("A passage.", {}))
        parsed = parse_response(out, provider="agent-os-router", model="opus")
        self.assertEqual(parsed.drafts[0]["value"]["text"], "A passage.")


if __name__ == "__main__":
    unittest.main()
