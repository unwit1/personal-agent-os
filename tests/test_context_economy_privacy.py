import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import builtins
import json
import tempfile
import unittest
from unittest import mock

from agent_os.orchestrator import context_economy
from agent_os.orchestrator.ledger import SCHEMA as TELEMETRY_SCHEMA

SENTINEL = "SECRET-SENTINEL-12345"
RUN_ID = "run-20261001T000000Z-aaaaaa"


def usage(input_tokens, output=0, cache_read=0, accuracy="exact", source="claude-code"):
    return {
        "accuracy": accuracy,
        "source": source,
        "input_tokens": input_tokens,
        "uncached_input_tokens": input_tokens - cache_read,
        "cache_read_tokens": cache_read,
        "cache_write_tokens": 0,
        "output_tokens": output,
        "cost_usd": None,
    }


class Run:
    """Writes a synthetic runs/<id>/telemetry.jsonl in the ledger format."""

    def __init__(self, runs_dir: Path, run_id: str):
        self.dir = runs_dir / run_id
        self.dir.mkdir(parents=True)
        self.run_id = run_id
        self.lines: list[str] = []
        self.seq = 0

    def event(self, kind, node=None, seq=None, **data):
        self.seq = seq if seq is not None else self.seq + 1
        self.lines.append(
            json.dumps(
                {
                    "schema": TELEMETRY_SCHEMA,
                    "at": "2026-10-01T00:00:00+00:00",
                    "seq": self.seq,
                    "run_id": self.run_id,
                    "type": kind,
                    "node": node,
                    "data": data,
                }
            )
        )
        return self

    def call(
        self,
        node,
        role,
        input_tokens,
        prompt,
        output=0,
        cache_read=0,
        attempt=1,
        cls="standard",
        kind="model_completed",
        seq=None,
        **usage_kwargs
    ):
        return self.event(
            kind,
            node,
            seq=seq,
            role=role,
            capability_class=cls,
            provider="claude-code",
            model="sonnet",
            attempt=attempt,
            prompt_chars=prompt * 4,
            prompt_tokens_estimate=prompt,
            usage=usage(input_tokens, output, cache_read, **usage_kwargs),
        )

    def write(self):
        (self.dir / "telemetry.jsonl").write_text("\n".join(self.lines) + "\n", encoding="utf-8")
        return self.dir


class ContextEconomyPrivacyTests(unittest.TestCase):
    """Test that context_economy maintains privacy and never leaks sentinel data."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.home = Path(self._tmp.name)
        self.runs = self.home / "runs"
        self.runs.mkdir()

    def test_sentinel_in_event_fields_not_leaked(self):
        """Plant sentinel in various event data fields and verify it's not in output."""
        node_id_with_sentinel = f"node-{SENTINEL}"
        run = Run(self.runs, RUN_ID)
        run.event("run_started", summary=f"Goal with {SENTINEL} embedded")
        run.call(node_id_with_sentinel, "implementer", 1000, 500)
        run.event("model_failed", SENTINEL, goal=f"Failure because {SENTINEL} occurred")
        run.write()

        result = context_economy.report(home=self.home)

        # Verify report succeeded
        self.assertTrue(result["privacy"]["passed"])
        self.assertIn(RUN_ID, result["runs"])

        # Verify sentinel not in result
        result_text = json.dumps(result)
        self.assertNotIn(SENTINEL, result_text)

        # Verify node id with sentinel not in result
        self.assertNotIn(node_id_with_sentinel, result_text)

        # Verify no node ID appears in the output
        self.assertNotIn("node-", result_text)

    def test_sentinel_in_worker_files_not_leaked(self):
        """Plant sentinel in worker directory files and verify it's not opened."""
        node_id = f"worker-{SENTINEL}"
        run = Run(self.runs, RUN_ID).event("run_started")
        run.call(node_id, "implementer", 2000, 800)
        run.write()

        # Create worker directory with sentinel in files
        worker_dir = run.dir / "workers" / f"{node_id}-1"
        worker_dir.mkdir(parents=True)
        (worker_dir / "prompt.md").write_text(f"Prompt contains {SENTINEL}")
        (worker_dir / "stdout.log").write_text(f"Stdout contains {SENTINEL}")
        (worker_dir / "stderr.log").write_text(f"Stderr contains {SENTINEL}")
        (worker_dir / "last-message.md").write_text(f"Last message contains {SENTINEL}")

        result = context_economy.report(home=self.home)

        # Verify sentinel not in result
        result_text = json.dumps(result)
        self.assertNotIn(SENTINEL, result_text)

        # Worker file sizes were recorded
        self.assertIn("worker_files", result)
        self.assertEqual(result["coverage"]["eligible_calls"], 1)

    def test_report_does_not_open_worker_files(self):
        """Verify that worker files are never opened, only stat'd for size."""
        node_id = "test-node"
        run = Run(self.runs, RUN_ID).event("run_started")
        run.call(node_id, "implementer", 1500, 600)
        run.write()

        worker_dir = run.dir / "workers" / f"{node_id}-1"
        worker_dir.mkdir(parents=True)
        (worker_dir / "prompt.md").write_text(f"This contains {SENTINEL}")
        (worker_dir / "stdout.log").write_bytes(b"output data")

        real_open = builtins.open
        real_read_text = Path.read_text

        def guard_open(target, *args, **kwargs):
            if "workers" in str(target):
                raise AssertionError(f"worker file was opened: {target}")
            return real_open(target, *args, **kwargs)

        def guard_read_text(self, *args, **kwargs):
            if "workers" in str(self):
                raise AssertionError(f"worker file read_text was called: {self}")
            return real_read_text(self, *args, **kwargs)

        with mock.patch("builtins.open", guard_open), mock.patch.object(Path, "read_text", guard_read_text):
            result = context_economy.build([run.dir])

        # Verify files were stat'd (size recorded) but not opened
        self.assertIn("worker_files", result)
        self.assertEqual(result["worker_files"]["by_role"]["implementer"]["prompt"]["sum_bytes"], len(f"This contains {SENTINEL}"))

    def test_assert_aggregate_only_raises_for_long_prose(self):
        """Verify assert_aggregate_only rejects reports with long prose strings."""
        # Build a valid report
        run = Run(self.runs, RUN_ID).event("run_started")
        run.call("node", "implementer", 500, 100)
        run.write()

        valid_result = context_economy.report(home=self.home)

        # Valid report passes
        try:
            context_economy.assert_aggregate_only(valid_result)
        except ValueError:
            self.fail("assert_aggregate_only raised on valid report")

        # Hand-built report with long prose fails
        bad_report = {**valid_result, "note": "x" * 81}
        with self.assertRaises(ValueError) as caught:
            context_economy.assert_aggregate_only(bad_report)
        self.assertIn("privacy rule violated", str(caught.exception))

        # Whitespace in string also fails
        bad_report_whitespace = {**valid_result, "note": "hello world"}
        with self.assertRaises(ValueError):
            context_economy.assert_aggregate_only(bad_report_whitespace)

    def test_sentinel_strings_with_spaces_sanitized(self):
        """Verify that node ids and labels with spaces are sanitized."""
        run = Run(self.runs, RUN_ID).event("run_started")
        run.call("node with spaces", "implementer", 1000, 500)
        run.write()

        result = context_economy.build([run.dir])

        # Space-containing node id should be sanitized (treated as "other")
        result_text = json.dumps(result)
        self.assertNotIn("node with spaces", result_text)

        # Verify privacy check passes
        self.assertTrue(result["privacy"]["passed"])

    def test_output_file_contains_no_sentinel(self):
        """Verify that written output file contains no sentinel strings."""
        node_id = f"secure-{SENTINEL}"
        run = Run(self.runs, RUN_ID).event("run_started", goal=f"Mission: {SENTINEL}")
        run.call(node_id, "implementer", 1200, 600)
        run.write()

        worker_dir = run.dir / "workers" / f"{node_id}-1"
        worker_dir.mkdir(parents=True)
        (worker_dir / "prompt.md").write_text(f"Prompt: {SENTINEL}")

        out_file = self.home / "output.json"
        result = context_economy.report(home=self.home, out=out_file)

        # File was written
        self.assertTrue(out_file.exists())

        # Written file contains no sentinel
        written_text = out_file.read_text(encoding="utf-8")
        self.assertNotIn(SENTINEL, written_text)

        # And no node ids
        self.assertNotIn(node_id, written_text)
        self.assertNotIn("secure-", written_text)

        # But file is valid JSON with proper schema
        written_data = json.loads(written_text)
        self.assertEqual(written_data["schema"], context_economy.SCHEMA)

    def test_multiple_nodes_with_sentinel_all_cleaned(self):
        """Verify that all occurrences of sentinel across multiple nodes are removed."""
        run = Run(self.runs, RUN_ID).event("run_started")

        # Multiple nodes with sentinel in names
        for i in range(3):
            node_id = f"node{i}-{SENTINEL}"
            run.call(node_id, "implementer", 500 * (i + 1), 200)

        run.write()

        # Create worker dirs with sentinel
        for i in range(3):
            node_id = f"node{i}-{SENTINEL}"
            worker_dir = run.dir / "workers" / f"{node_id}-1"
            worker_dir.mkdir(parents=True)
            (worker_dir / "prompt.md").write_text(f"Content {SENTINEL}")

        result = context_economy.report(home=self.home)

        # Verify no sentinel anywhere
        result_text = json.dumps(result)
        self.assertNotIn(SENTINEL, result_text)

        # But we have 3 eligible calls recorded
        self.assertEqual(result["coverage"]["eligible_calls"], 3)

    def test_assert_aggregate_only_forbids_specific_strings(self):
        """Verify that forbidden set of strings (like run ids) is properly rejected."""
        # Create a hand-built report with a specific string in it
        result = {
            "schema": "test",
            "runs": [RUN_ID],
            "data": {"value": "test-value"},
        }

        # Report passes without forbidden set
        try:
            context_economy.assert_aggregate_only(result)
        except ValueError:
            self.fail("assert_aggregate_only raised unexpectedly")

        # Report fails if one of its values is in forbidden set
        with self.assertRaises(ValueError) as caught:
            context_economy.assert_aggregate_only(result, forbidden={RUN_ID})
        self.assertIn("privacy rule violated", str(caught.exception))

    def test_privacy_marker_in_result(self):
        """Verify that result includes privacy marker indicating success."""
        run = Run(self.runs, RUN_ID).event("run_started")
        run.call("node", "implementer", 1000, 500)
        run.write()

        result = context_economy.report(home=self.home)

        self.assertIn("privacy", result)
        self.assertEqual(result["privacy"]["rule"], context_economy.PRIVACY_RULE)
        self.assertTrue(result["privacy"]["passed"])
        self.assertGreater(result["privacy"]["strings_checked"], 0)


if __name__ == "__main__":
    unittest.main()
