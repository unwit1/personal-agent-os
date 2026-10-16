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

    def test_json_with_another_concept_id_still_fills_the_sample(self):
        # The engine prompt asks for JSON drafts; models sometimes pick their own concept id or shape.
        for reply in (json.dumps({"drafts": [{"concept_id": "replication.generate", "value": {"text": "Rain fell."}}]}),
                      json.dumps({"drafts": [{"concept_id": "sample", "value": "Rain fell."}]}),
                      json.dumps({"text": "Rain fell."})):
            out = router.handle(envelope(), provider="claude-code", runner=self.fake(reply, {}))
            self.assertEqual(out["drafts"][0]["concept_id"], "replication.sample")
            self.assertEqual(out["drafts"][0]["value"]["text"], "Rain fell.")

    def test_empty_sample_is_an_error_not_an_empty_generation(self):
        for reply in ("", json.dumps({"drafts": []}), json.dumps({"drafts": [{"concept_id": "x", "value": {}}]})):
            with self.assertRaises(router.RouterError):
                router.handle(envelope(), provider="claude-code", runner=self.fake(reply, {}))

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


class RouterPolicyTests(unittest.TestCase):
    """AB-5 optional envelope fields: provider_policy and allowance."""

    def run_with(self, extra, provider="claude-code"):
        seen = {}

        def runner(argv, prompt, env, timeout):
            seen["argv"] = argv
            return "Text."
        out = router.handle({**envelope(), **extra}, provider=provider, runner=runner)
        return out, seen

    def test_allowed_provider_is_kept(self):
        out, _ = self.run_with({"provider_policy": {"allowed_providers": ["claude-code", "codex"]}})
        self.assertEqual(out["provider"], "agent-os-router/claude-code")

    def test_disallowed_provider_switches_to_first_allowed(self):
        with mock.patch.object(router, "call_cli", return_value="Text.") as call:
            out = router.handle({**envelope(), "provider_policy": {"allowed_providers": ["agent-os-router/codex"]}},
                                provider="claude-code")
        self.assertEqual(out["provider"], "agent-os-router/codex")
        self.assertEqual(call.call_args.args[0], "codex")

    def test_no_allowed_provider_is_an_error(self):
        with self.assertRaises(router.RouterError):
            self.run_with({"provider_policy": {"allowed_providers": ["paid-api"]}})

    def test_allowance_reports_zero_cost_and_rejects_bad_values(self):
        out, _ = self.run_with({"allowance": {"max_cost_units": 0}})
        self.assertEqual(out["usage"]["cost_units"], 0)
        for bad in (-1, "lots"):
            with self.assertRaises(router.RouterError):
                self.run_with({"allowance": {"max_cost_units": bad}})

    def test_envelope_without_optional_fields_is_unchanged(self):
        out, _ = self.run_with({})
        self.assertEqual(out["provider"], "agent-os-router/claude-code")


if __name__ == "__main__":
    unittest.main()


class RouterStdioTests(unittest.TestCase):
    def test_main_reads_and_writes_utf8_even_when_the_pipes_default_to_cp1252(self):
        import io
        import sys

        prompt = {"model": "opus", "request": {"brief": "“Kaladin’s storm”"}}
        stdin = io.TextIOWrapper(io.BytesIO(json.dumps(prompt, ensure_ascii=False).encode("utf-8")), encoding="cp1252")
        out_bytes = io.BytesIO()
        stdout = io.TextIOWrapper(out_bytes, encoding="cp1252")
        seen = {}

        def fake_handle(envelope, timeout, **_):
            seen["brief"] = envelope["request"]["brief"]
            return {"drafts": ["He said “no” — then left."]}

        with mock.patch.object(router, "handle", fake_handle), \
                mock.patch.object(sys, "stdin", stdin), mock.patch.object(sys, "stdout", stdout):
            self.assertEqual(router.main([]), 0)
            sys.stdout.flush()
        self.assertEqual(seen["brief"], "“Kaladin’s storm”")
        self.assertEqual(json.loads(out_bytes.getvalue().decode("utf-8"))["drafts"][0], "He said “no” — then left.")


class RouterOutputLimitTests(unittest.TestCase):
    def run_with(self, provider, **kw):
        seen = {}

        def runner(argv, prompt, env, timeout):
            seen["env"] = env
            return "Some prose."
        router.handle(envelope(), provider=provider, runner=runner, **kw)
        return seen.get("env", {})

    def test_claude_gets_the_enforced_cap(self):
        env = self.run_with("claude-code", max_output_tokens=3000)
        self.assertEqual(env["CLAUDE_CODE_MAX_OUTPUT_TOKENS"], "3000")

    def test_envelope_allowance_and_flag_take_the_smaller(self):
        payload = envelope()
        payload["allowance"] = {"max_output_tokens": 1200}
        seen = {}
        router.handle(payload, provider="claude-code", max_output_tokens=3000,
                      runner=lambda a, p, env, t: seen.setdefault("env", env) and "x")
        self.assertEqual(seen["env"]["CLAUDE_CODE_MAX_OUTPUT_TOKENS"], "1200")

    def test_codex_fails_closed_when_a_cap_is_requested(self):
        with self.assertRaises(router.RouterError):
            self.run_with("codex", max_output_tokens=3000)

    def test_no_cap_leaves_the_environment_alone(self):
        self.assertNotIn("CLAUDE_CODE_MAX_OUTPUT_TOKENS", self.run_with("claude-code"))
