"""DEC-0009: subsumed retry/backoff/circuit breaker and key-optional direct API
workers. No real network calls: HTTP is faked."""

from __future__ import annotations

import io
import json
import sys
import tempfile
import unittest
import urllib.error
from email.message import Message
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.orchestrator import retry  # noqa: E402
from agent_os.orchestrator.adapters import http_api  # noqa: E402
from agent_os.orchestrator.adapters.base import AgentLaunchRequest  # noqa: E402
from agent_os.orchestrator.router import ProviderRegistry, select  # noqa: E402


class Response(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def http_error(code: int, retry_after: str | None = None) -> urllib.error.HTTPError:
    headers = Message()
    if retry_after is not None:
        headers["retry-after"] = retry_after
    return urllib.error.HTTPError("https://x", code, "err", headers, io.BytesIO(b'{"error":"x"}'))


class RetryTests(unittest.TestCase):
    def test_full_jitter_is_bounded(self) -> None:
        self.assertEqual(retry.full_jitter(10, base=1, cap=30, rng=lambda: 1.0), 30)
        self.assertEqual(retry.full_jitter(2, base=1, cap=30, rng=lambda: 0.5), 2.0)

    def test_retry_after_parsing(self) -> None:
        self.assertEqual(retry.parse_retry_after("7"), 7.0)
        self.assertAlmostEqual(retry.parse_retry_after("Thu, 01 Jan 2026 00:00:10 GMT", now=1767225600.0), 10.0, places=0)
        self.assertIsNone(retry.parse_retry_after("soon"))

    def test_policy_honours_retry_after_and_limits(self) -> None:
        calls, sleeps = [], []

        def flaky():
            calls.append(1)
            if len(calls) < 3:
                raise retry.RetryableError("429", status=429, retry_after=2.0)
            return "ok"

        self.assertEqual(retry.RetryPolicy(max_attempts=4, deadline=None).call(flaky, sleep=sleeps.append), "ok")
        self.assertEqual(sleeps, [2.0, 2.0])
        with self.assertRaises(retry.RetryableError):
            retry.RetryPolicy(max_attempts=2, deadline=None).call(lambda: (_ for _ in ()).throw(retry.RetryableError("x")), sleep=lambda s: None)
        # Deadline stops a retry whose wait would exceed it.
        with self.assertRaises(retry.RetryableError):
            retry.RetryPolicy(max_attempts=5, deadline=1.0).call(lambda: (_ for _ in ()).throw(retry.RetryableError("x", retry_after=5)), sleep=lambda s: None)

    def test_non_retryable_errors_are_not_retried(self) -> None:
        calls = []

        def bad():
            calls.append(1)
            raise ValueError("validation")

        with self.assertRaises(ValueError):
            retry.RetryPolicy().call(bad, sleep=lambda s: None)
        self.assertEqual(len(calls), 1)

    def test_circuit_breaker_states(self) -> None:
        now = [0.0]
        breaker = retry.CircuitBreaker(fail_max=2, reset_timeout=10, clock=lambda: now[0])
        for _ in range(2):
            with self.assertRaises(RuntimeError):
                breaker.call(lambda: (_ for _ in ()).throw(RuntimeError("down")))
        self.assertEqual(breaker.state, "open")
        with self.assertRaises(retry.CircuitOpenError):
            breaker.call(lambda: "x")
        now[0] = 11
        self.assertEqual(breaker.call(lambda: "up"), "up")  # half-open probe succeeds
        self.assertEqual(breaker.state, "closed")


def request(tmp: Path, model: str = "m") -> AgentLaunchRequest:
    prompt = tmp / "prompt.md"
    prompt.write_text("classify this", encoding="utf-8")
    return AgentLaunchRequest(run_id="r", node_id="n", role="planner", cwd=str(tmp), prompt_path=str(prompt), output_dir=str(tmp / "out"),
                              capability_class="fast", effort="low", model=model, provider_effort="low", read_only=True, timeout_seconds=60)


def run(adapter, req):
    handle = adapter.start(req)
    for _ in range(500):
        if not adapter.poll(handle).running:
            break
        import time

        time.sleep(0.01)
    return adapter.collect(handle)


class ApiAdapterTests(unittest.TestCase):
    def test_anthropic_success_maps_usage_and_structured_output(self) -> None:
        seen = {}

        def opener(req, timeout=0):
            seen["url"], seen["headers"], seen["body"] = req.full_url, dict(req.header_items()), json.loads(req.data)
            return Response(json.dumps({"model": "claude-haiku-4-5-20251001", "content": [{"type": "text", "text": "ok\n```json\n{\"a\": 1}\n```"}],
                                        "usage": {"input_tokens": 100, "cache_read_input_tokens": 20, "cache_creation_input_tokens": 0, "output_tokens": 7}}).encode())

        with tempfile.TemporaryDirectory() as tmp, mock.patch.dict("os.environ", {"ANTHROPIC_API_KEY": "sk-test"}):
            adapter = http_api.AnthropicApiAdapter({"id": "anthropic-api", "options": {}}, opener=opener)
            self.assertTrue(adapter.probe().available)
            result = run(adapter, request(Path(tmp), "claude-haiku-4-5-20251001"))
        self.assertEqual(result.outcome, "completed")
        self.assertEqual(result.structured, {"a": 1})
        self.assertEqual((result.usage["input_tokens"], result.usage["output_tokens"], result.usage["model_resolved"]), (120, 7, "claude-haiku-4-5-20251001"))
        self.assertTrue(seen["url"].endswith("/v1/messages"))
        self.assertEqual(seen["headers"].get("X-api-key"), "sk-test")

    def test_rate_limit_retries_with_retry_after_then_succeeds(self) -> None:
        attempts = []

        def opener(req, timeout=0):
            attempts.append(1)
            if len(attempts) == 1:
                raise http_error(429, retry_after="0")
            return Response(json.dumps({"choices": [{"message": {"content": "fine"}}], "usage": {"prompt_tokens": 10, "completion_tokens": 2}, "model": "local"}).encode())

        with tempfile.TemporaryDirectory() as tmp:
            adapter = http_api.OpenAiCompatibleAdapter({"id": "local", "options": {"base_url": "http://127.0.0.1:1/x"}}, opener=opener)
            self.assertTrue(adapter.probe().available)  # local base_url needs no key
            result = run(adapter, request(Path(tmp)))
        self.assertEqual((result.outcome, len(attempts), result.usage["input_tokens"]), ("completed", 2, 10))

    def test_auth_failure_is_not_retried(self) -> None:
        attempts = []

        def opener(req, timeout=0):
            attempts.append(1)
            raise http_error(401)

        with tempfile.TemporaryDirectory() as tmp, mock.patch.dict("os.environ", {"OPENAI_API_KEY": "bad"}):
            result = run(http_api.OpenAiCompatibleAdapter({"id": "openai-api", "options": {}}, opener=opener), request(Path(tmp)))
        self.assertEqual((result.outcome, result.failure_kind, len(attempts)), ("failed", "auth", 1))

    def test_missing_key_disables_provider(self) -> None:
        with mock.patch.dict("os.environ", {}, clear=True), mock.patch.object(http_api, "read_key", return_value=None):
            self.assertFalse(http_api.AnthropicApiAdapter({"id": "anthropic-api", "options": {}}).probe().available)
            self.assertFalse(http_api.suggested_anthropic()["enabled"])

    def test_inline_role_gating(self) -> None:
        registry = ProviderRegistry(providers=[{"id": "api", "adapter": "anthropic_api", "models": {"fast": "claude-haiku-4-5-20251001"}, "roles": ["inline"], "costs": {"fast": 0.1}}])
        self.assertFalse(select(registry, capability_class="fast", effort="low", role="implementer", availability={"api": True})["resolved"])
        self.assertTrue(select(registry, capability_class="fast", effort="low", role="inline", availability={"api": True})["resolved"])


if __name__ == "__main__":
    unittest.main()
