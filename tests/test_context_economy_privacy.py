import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import builtins
import io
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

    def test_sentinel_in_all_event_fields_and_worker_files_not_leaked(self):
        """Plant sentinel in all four event fields plus worker files, verify complete privacy."""
        node_id_with_sentinel = f"worker-{SENTINEL}"

        run = Run(self.runs, RUN_ID)
        # Plant sentinel in summary
        run.event("run_started", summary=f"Summary with {SENTINEL}")
        # Plant sentinel in goal
        run.event("run_info", goal=f"Goal with {SENTINEL}")
        # Plant sentinel in failure text
        run.event("model_failed", node_id_with_sentinel, failure_text=f"Failure: {SENTINEL}")
        # Add a regular call with sentinel in node id
        run.call(node_id_with_sentinel, "implementer", 1000, 500)
        run.write()

        # Create worker files with sentinel in all relevant files
        worker_dir = run.dir / "workers" / f"{node_id_with_sentinel}-1"
        worker_dir.mkdir(parents=True)
        (worker_dir / "prompt.md").write_text(f"Prompt: {SENTINEL}")
        (worker_dir / "stdout.log").write_text(f"Stdout: {SENTINEL}")
        (worker_dir / "last-message.md").write_text(f"Message: {SENTINEL}")

        # Write to output file
        out_file = self.home / "comprehensive.json"
        result = context_economy.report(home=self.home, out=out_file)

        # Verify sentinel not in result
        result_text = json.dumps(result)
        self.assertNotIn(SENTINEL, result_text, "Sentinel found in result dict")

        # Verify node id not in result
        self.assertNotIn(node_id_with_sentinel, result_text, "Node ID with sentinel found in result")
        self.assertNotIn("worker-", result_text, "Node ID pattern found in result")

        # Verify sentinel not in written file
        self.assertTrue(out_file.exists(), "Output file was not created")
        written_text = out_file.read_text(encoding="utf-8")
        self.assertNotIn(SENTINEL, written_text, "Sentinel found in written file")
        self.assertNotIn(node_id_with_sentinel, written_text, "Node ID with sentinel found in written file")
        self.assertNotIn("worker-", written_text, "Node ID pattern found in written file")

        # Verify the file is valid JSON and has proper schema
        written_data = json.loads(written_text)
        self.assertEqual(written_data["schema"], context_economy.SCHEMA, "Output file has incorrect schema")
        self.assertTrue(written_data["privacy"]["passed"], "Privacy check failed in written file")

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

        workers_prefix = str((run.dir / "workers").resolve())

        real_open = builtins.open
        real_read_text = Path.read_text
        real_path_open = Path.open
        real_read_bytes = Path.read_bytes
        real_io_open = io.open

        def check_workers_access(target_str):
            """Check if target is under workers prefix; raise if so."""
            if target_str.startswith(workers_prefix):
                raise AssertionError(f"worker file access attempted: {target_str}")

        def guard_open(target, *args, **kwargs):
            try:
                target_str = str(Path(target).resolve())
                check_workers_access(target_str)
            except (TypeError, ValueError):
                pass
            return real_open(target, *args, **kwargs)

        def guard_read_text(self, *args, **kwargs):
            check_workers_access(str(self.resolve()))
            return real_read_text(self, *args, **kwargs)

        def guard_path_open(self, *args, **kwargs):
            check_workers_access(str(self.resolve()))
            return real_path_open(self, *args, **kwargs)

        def guard_read_bytes(self, *args, **kwargs):
            check_workers_access(str(self.resolve()))
            return real_read_bytes(self, *args, **kwargs)

        def guard_io_open(target, *args, **kwargs):
            try:
                target_str = str(Path(target).resolve())
                check_workers_access(target_str)
            except (TypeError, ValueError):
                pass
            return real_io_open(target, *args, **kwargs)

        with mock.patch("builtins.open", guard_open), \
             mock.patch.object(Path, "read_text", guard_read_text), \
             mock.patch.object(Path, "open", guard_path_open), \
             mock.patch.object(Path, "read_bytes", guard_read_bytes), \
             mock.patch("io.open", guard_io_open):
            result = context_economy.report(home=self.home)

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


if __name__ == "__main__":
    unittest.main()
