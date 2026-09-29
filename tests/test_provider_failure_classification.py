"""Worker failure classification (IMP-0016).

A transient provider failure (529 overloaded, 5xx, dropped connection) used to
be classified as ``quota`` -- a one-hour machine-wide cooldown -- or as
``process_error``, which the provider breaker never sees. The labeled corpus in
tests/fixtures/provider-failure-corpus.json pins the expected kind per message.
"""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.orchestrator import provider_health  # noqa: E402
from agent_os.orchestrator.adapters.base import RunningAgent, classify_failure  # noqa: E402
from agent_os.orchestrator.adapters.claude_code import ClaudeCodeAdapter  # noqa: E402
from agent_os.orchestrator.adapters.codex_cli import CodexCliAdapter  # noqa: E402

CORPUS = Path(__file__).resolve().parent / "fixtures" / "provider-failure-corpus.json"
OVERLOADED = 'API Error: 529 {"type":"error","error":{"type":"overloaded_error","message":"Overloaded"}}'


class ClassifyFailureCorpusTests(unittest.TestCase):
    def test_every_corpus_case_gets_its_label(self) -> None:
        cases = json.loads(CORPUS.read_text(encoding="utf-8"))["cases"]
        self.assertGreaterEqual(len(cases), 20)
        for case in cases:
            with self.subTest(case=case["id"]):
                self.assertEqual(classify_failure(case["text"], 1), case["label"])

    def test_quota_wins_when_a_message_names_both(self) -> None:
        self.assertEqual(classify_failure("exceeded retry limit, last status: 429 Too Many Requests; 503 earlier", 1), "quota")

    def test_invalid_model_wins_over_transient(self) -> None:
        self.assertEqual(classify_failure("HTTP 500 while loading: model gpt-x not found", 1), "invalid_model")

    def test_bare_status_numbers_in_prose_are_not_transient(self) -> None:
        for text in ("Refactored the handler that returns 503 to callers", "listening on port 5029", "processed 500 rows"):
            with self.subTest(text=text):
                self.assertEqual(classify_failure(text, 1), "process_error")

    def test_empty_text_is_a_process_error(self) -> None:
        self.assertEqual(classify_failure("", 1), "process_error")
        self.assertEqual(classify_failure(None, None), "process_error")  # type: ignore[arg-type]


class AdapterClassificationTests(unittest.TestCase):
    handle = RunningAgent("p", "n", None, 0.0, "", "", "", None, "")

    def test_claude_overloaded_json_result_is_unavailable(self) -> None:
        stdout = json.dumps({"type": "result", "subtype": "success", "is_error": True, "result": OVERLOADED})
        result = ClaudeCodeAdapter({"id": "cc"}).parse_result(self.handle, 1, stdout, "")
        self.assertEqual((result.outcome, result.failure_kind), ("failed", "unavailable"))

    def test_claude_overloaded_on_stderr_without_json_is_unavailable(self) -> None:
        result = ClaudeCodeAdapter({"id": "cc"}).parse_result(self.handle, 1, "", OVERLOADED)
        self.assertEqual(result.failure_kind, "unavailable")

    def test_codex_stream_retry_exhaustion_is_unavailable(self) -> None:
        events = json.dumps({"type": "turn.failed", "error": {"message": "stream error: exceeded retry limit, last status: 503 Service Unavailable"}})
        result = CodexCliAdapter({"id": "cx"}).parse_result(self.handle, 1, events, "")
        self.assertEqual(result.failure_kind, "unavailable")


class HealthConsequenceTests(unittest.TestCase):
    """The point of the reclassification: one transient failure must not cool
    the provider machine-wide; the breaker opens only on repetition."""

    def setUp(self) -> None:
        self.home = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.home, True)
        self.now = datetime(2026, 9, 29, 12, 0, tzinfo=timezone.utc)

    def test_single_overload_leaves_provider_usable(self) -> None:
        self.assertEqual(classify_failure(OVERLOADED, 1), "unavailable")
        self.assertIsNone(provider_health.record_unavailable(self.home, "claude-code", OVERLOADED, self.now))
        self.assertEqual(provider_health.cooling(self.home, self.now), set())

    def test_repeated_overloads_open_the_breaker(self) -> None:
        opened = None
        for _ in range(provider_health.BREAKER_FAILURES):
            opened = provider_health.record_unavailable(self.home, "claude-code", OVERLOADED, self.now)
        self.assertIsNotNone(opened)
        self.assertEqual(provider_health.cooling(self.home, self.now), {"claude-code"})


if __name__ == "__main__":
    unittest.main()
