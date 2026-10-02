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

RUN_A = "run-20261001T000000Z-aaaaaa"
RUN_B = "run-20261001T000001Z-bbbbbb"


def usage(input_tokens, output=0, cache_read=0, accuracy="exact", source="claude-code"):
    return {"accuracy": accuracy, "source": source, "input_tokens": input_tokens, "uncached_input_tokens": input_tokens - cache_read,
            "cache_read_tokens": cache_read, "cache_write_tokens": 0, "output_tokens": output, "cost_usd": None}


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
        self.lines.append(json.dumps({"schema": TELEMETRY_SCHEMA, "at": "2026-10-01T00:00:00+00:00", "seq": self.seq,
                                      "run_id": self.run_id, "type": kind, "node": node, "data": data}))
        return self

    def call(self, node, role, input_tokens, prompt, output=0, cache_read=0, attempt=1, cls="standard", kind="model_completed",
             seq=None, **usage_kwargs):
        return self.event(kind, node, seq=seq, role=role, capability_class=cls, provider="claude-code", model="sonnet", attempt=attempt,
                          prompt_chars=prompt * 4, prompt_tokens_estimate=prompt,
                          usage=usage(input_tokens, output, cache_read, **usage_kwargs))

    def write(self):
        (self.dir / "telemetry.jsonl").write_text("\n".join(self.lines) + "\n", encoding="utf-8")
        return self.dir


class ContextEconomyTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.home = Path(self._tmp.name)
        self.runs = self.home / "runs"
        self.runs.mkdir()

    def test_amplification_exact_values_and_exclusions(self):
        run = Run(self.runs, RUN_A).event("run_started")
        run.call("a", "implementer", 2000, 1000, output=200, cache_read=500)
        run.call("b", "implementer", 3000, 1000, output=600)
        run.call("c", "reviewer", 900, 300, output=90, cls="fast")
        run.call("d", "implementer", 99999, 1, source="synthetic")
        run.call("e", "implementer", 5000, 1000, accuracy="estimated")
        run.call("f", "implementer", 0, 1000, accuracy="unavailable")
        run.call("g", "implementer", 100, 100, cache_read=200)  # cache exceeds input: inconsistent
        run.write()
        result = context_economy.build([run.dir])
        cov = result["coverage"]
        self.assertEqual((cov["calls"], cov["exact_calls"], cov["unreported_calls"], cov["synthetic_calls_excluded"], cov["eligible_calls"]), (7, 4, 2, 1, 3))
        self.assertEqual(cov["excluded"], {"estimated": 1, "unavailable": 1, "synthetic": 1, "inconsistent": 1})
        everything = result["amplification"]["all"]
        # input_tokens is provider input already; cache fields are not added again
        self.assertEqual((everything["count"], everything["sum_input"], everything["sum_prompt_estimate"], everything["sum_output"]), (3, 5900, 2300, 890))
        self.assertEqual((everything["pooled_amplification"], everything["pooled_output_ratio"]), (2.5652, 0.1508))
        impl = result["amplification"]["by_role"]["implementer"]
        self.assertEqual((impl["count"], impl["sum_input"], impl["pooled_amplification"]), (2, 5000, 2.5))
        self.assertEqual(impl["amplification"], {"count": 2, "median": 2.5, "p90": 3.0, "min": 2.0, "max": 3.0})
        self.assertEqual(impl["output_ratio"], {"count": 2, "median": 0.15, "p90": 0.2, "min": 0.1, "max": 0.2})
        self.assertEqual(impl["cache_read_share"], {"count": 2, "median": 0.125, "p90": 0.25, "min": 0.0, "max": 0.25})
        self.assertEqual(result["amplification"]["by_capability_class"]["fast"]["sum_input"], 900)
        self.assertEqual(set(result["amplification"]["by_capability_class"]), {"fast", "standard"})

    def test_growth_buckets_ordinals_and_exponent(self):
        run = Run(self.runs, RUN_A).event("run_started")
        run.call("one", "implementer", 50, 10)
        for attempt, tokens in ((2, 100), (5, 200), (7, 400)):  # raw attempt numbers are not ordinals
            run.call("three", "implementer", tokens, 10, attempt=attempt)
        for attempt, tokens in enumerate((100, 150, 200, 250, 300), 1):
            run.call("five", "implementer", tokens, 10, attempt=attempt)
        run.write()
        result = context_economy.build([run.dir])
        buckets = result["session_growth"]["by_node_bucket"]
        self.assertEqual(list(buckets), ["1", "2-3", "4+"])
        self.assertEqual((buckets["1"]["nodes"], buckets["1"]["calls"], buckets["1"]["sum_input"]), (1, 1, 50))
        self.assertEqual(buckets["1"]["growth_ratio"]["count"], 0)
        self.assertIsNone(buckets["1"]["growth_ratio"]["median"])
        self.assertEqual((buckets["2-3"]["nodes"], buckets["2-3"]["calls"], buckets["2-3"]["sum_input"]), (1, 3, 700))
        self.assertEqual(buckets["2-3"]["growth_ratio"]["median"], 4.0)
        self.assertEqual((buckets["2-3"]["first_input"]["median"], buckets["2-3"]["last_input"]["median"]), (100, 400))
        self.assertEqual((buckets["4+"]["nodes"], buckets["4+"]["calls"], buckets["4+"]["sum_input"]), (1, 5, 1000))
        self.assertEqual(buckets["4+"]["growth_ratio"]["median"], 3.0)
        by_run = result["session_growth"]["by_run"][RUN_A]
        self.assertEqual(by_run["calls"], 9)
        self.assertEqual(by_run["input_by_node_bucket"], {"1": 50, "2-3": 700, "4+": 1000, "none": 0})
        self.assertEqual(by_run["cumulative_input"][-1], 1750)

    def test_growth_exponent_constant_vs_rising(self):
        flat = Run(self.runs, RUN_A)
        rising = Run(self.runs, RUN_B)
        for index in range(5):
            flat.call("n", "implementer", 100, 10, attempt=index + 1)
            rising.call("n", "implementer", 100 * (index + 1), 10, attempt=index + 1)
        result = context_economy.build([flat.write(), rising.write()])
        by_run = result["session_growth"]["by_run"]
        self.assertEqual(by_run[RUN_A]["growth_exponent"], 1.0)
        self.assertEqual(by_run[RUN_A]["cumulative_input"], [100, 200, 300, 400, 500])
        self.assertEqual(by_run[RUN_B]["cumulative_input"], [100, 300, 600, 1000, 1500])
        self.assertGreater(by_run[RUN_B]["growth_exponent"], 1.5)

    def test_growth_exponent_needs_three_points(self):
        run = Run(self.runs, RUN_A).call("n", "implementer", 100, 10).call("n", "implementer", 100, 10, attempt=2)
        result = context_economy.build([run.write()])
        self.assertIsNone(result["session_growth"]["by_run"][RUN_A]["growth_exponent"])

    def test_fanout(self):
        run = Run(self.runs, RUN_A).event("run_started")
        run.call("plan", "planner", 1000, 400, cls="strong")
        run.call("i1", "implementer", 2000, 1500)  # +500
        run.call("i2", "implementer", 1000, 1200)  # -200
        run.call("r1", "reviewer", 3000, 1000)  # +2000
        run.call("r1", "reviewer", 500, 600, attempt=2)  # -100
        run.call("x1", "implementer", 7777, 100, accuracy="estimated")  # a node, but not measured
        run.event("retry", "r1").event("model_escalated", "r1").write()
        fan = context_economy.build([run.dir])["fanout"]["by_run"][RUN_A]
        self.assertEqual(fan["worker_nodes"], {"implementer": 3, "reviewer": 1})
        self.assertEqual(fan["worker_nodes_total"], 4)
        self.assertEqual((fan["planner_input"], fan["worker_input"], fan["fanout_input_ratio"]), (1000, 6500, 6.5))
        self.assertEqual((fan["duplicated_fixed_overhead"], fan["overhead_share"], fan["negative_overhead_calls"]), (2200, 0.3385, 2))
        self.assertEqual(fan["overhead_per_worker_call"], {"count": 4, "median": 200.0, "p90": 2000, "min": -200, "max": 2000})
        self.assertEqual((fan["repeat_attempt_input"], fan["retries"], fan["escalations"], fan["fallbacks"]), (500, 1, 1, 0))

    def test_fanout_totals_recompute_ratios_from_sums(self):
        first = Run(self.runs, RUN_A).call("p", "planner", 100, 50, cls="strong").call("w", "implementer", 300, 100)
        second = Run(self.runs, RUN_B).call("p", "planner", 900, 50, cls="strong").call("w", "implementer", 1000, 100)
        fan = context_economy.build([first.write(), second.write()])["fanout"]
        self.assertEqual(fan["by_run"][RUN_A]["fanout_input_ratio"], 3.0)
        self.assertEqual(fan["totals"]["planner_input"], 1000)
        self.assertEqual(fan["totals"]["worker_input"], 1300)
        self.assertEqual(fan["totals"]["fanout_input_ratio"], 1.3)  # not the mean of 3.0 and 1.1111
        self.assertEqual(fan["totals"]["worker_nodes"], {"implementer": 2})

    def test_resume_overhead(self):
        run = Run(self.runs, RUN_A).event("run_started")
        run.call("warm_called", "implementer", 100, 10, seq=10)
        run.event("checkpoint_created", "warm_ck", seq=11)
        run.call("other", "implementer", 50, 10, seq=12)
        run.event("run_resumed", seq=20)
        run.call("warm_called", "implementer", 200, 10, seq=21)
        run.call("warm_called", "implementer", 300, 10, seq=22)
        run.call("warm_ck", "implementer", 400, 10, seq=23)
        run.call("cold_new", "implementer", 500, 10, seq=24)
        run.call("retry_node", "implementer", 600, 10, attempt=2, seq=25)
        run.event("run_paused", seq=30).event("run_resumed", seq=40)
        run.call("cold_new", "implementer", 700, 10, seq=41)
        run.call("fresh", "implementer", 800, 10, seq=42)
        plain = Run(self.runs, RUN_B).call("n", "implementer", 10, 10)
        result = context_economy.build([run.write(), plain.write()])
        self.assertEqual(list(result["resume"]["by_run"]), [RUN_A])
        got = result["resume"]["by_run"][RUN_A]
        self.assertEqual(got, {
            "resumes": 2, "pauses": 1, "checkpoints": 1, "warm_nodes": 4, "run_input": 3650,
            "resume_overhead_input": 2200, "resume_first_input": 1900, "cold_resume_input": 1300,
            "resume_share": 0.6027, "resume_first_share": 0.5205,
        })
        self.assertEqual(result["resume"]["totals"], got)

    def test_sizes_only_never_opens_worker_files(self):
        sentinel = "SENTINEL-PHRASE secret words go here!!"
        run = Run(self.runs, RUN_A).event("run_started", mode="fix the secret goal")
        run.call("node-secret-id", "implementer", 800, 10)
        run.write()
        worker = run.dir / "workers" / "node-secret-id-1"
        worker.mkdir(parents=True)
        (worker / "prompt.md").write_bytes(sentinel.encode().ljust(40, b"."))
        (worker / "stdout.log").write_bytes(b"1234567")
        (worker / "notes.txt").write_bytes(b"123")
        (run.dir / "workers" / "oddname").mkdir()
        real_open, real_read_text = builtins.open, Path.read_text

        def guard(real):
            def wrapper(target, *args, **kwargs):
                if "workers" in str(target):
                    raise AssertionError("worker file was opened")
                return real(target, *args, **kwargs)
            return wrapper

        with mock.patch("builtins.open", guard(real_open)), mock.patch.object(Path, "read_text", lambda self, *a, **k: guard(real_read_text)(self, *a, **k)):
            result = context_economy.build([run.dir])
        text = json.dumps(result)
        self.assertNotIn("SENTINEL", text)
        self.assertNotIn("secret", text)
        files = result["worker_files"]["by_role"]["implementer"]
        self.assertEqual(files["prompt"]["sum_bytes"], 40)
        self.assertEqual(files["stdout"]["sum_bytes"], 7)
        self.assertEqual(files["other"]["sum_bytes"], 3)
        self.assertEqual(result["worker_files"]["prompt_bytes_per_estimated_token"]["median"], 4.0)
        self.assertEqual(result["coverage"]["unparsed_worker_dirs"], 1)

    def test_privacy_sanitizes_labels_and_rejects_leaks(self):
        run = Run(self.runs, RUN_A).event("run_started", mode="a goal sentence with spaces")
        run.event("model_completed", "planted-node-id", role="x" * 81, capability_class="two words", provider="claude-code", model="sonnet",
                  attempt=1, prompt_tokens_estimate=10, usage=usage(100))
        run.write()
        result = context_economy.build([run.dir])
        self.assertEqual(result["coverage"]["sanitized_labels"], 2)
        self.assertEqual(list(result["amplification"]["by_role"]), ["other"])
        text = json.dumps(result)
        self.assertNotIn("planted-node-id", text)
        self.assertNotIn("goal sentence", text)
        self.assertTrue(result["privacy"]["passed"])
        context_economy.assert_aggregate_only(result)

        with self.assertRaises(ValueError) as caught:
            context_economy.assert_aggregate_only({**result, "note": "a goal sentence"})
        self.assertNotIn("goal sentence", str(caught.exception))
        self.assertIn("$.note", str(caught.exception))
        with self.assertRaises(ValueError):
            context_economy.assert_aggregate_only({"note": "x" * 81})
        leaked = {"runs": ["planted-node-id"]}
        context_economy.assert_aggregate_only(leaked)
        with self.assertRaises(ValueError):
            context_economy.assert_aggregate_only(leaked, forbidden={"planted-node-id"})

    def test_malformed_input_is_counted(self):
        run = Run(self.runs, RUN_A).call("n", "implementer", 100, 10)
        run.write()
        with open(run.dir / "telemetry.jsonl", "a", encoding="utf-8") as handle:
            handle.write("not json\n{broken\n")
        (self.runs / "not-a-run").mkdir()
        result = context_economy.build([run.dir, self.runs / "not-a-run"])
        self.assertEqual((result["coverage"]["malformed_lines"], result["coverage"]["malformed_runs"], result["coverage"]["runs"]), (2, 1, 1))
        self.assertEqual(result["runs"], [RUN_A])
        self.assertEqual(result["coverage"]["runs_without_run_started"], 1)

    def test_deterministic_and_report_writes_json(self):
        run = Run(self.runs, RUN_A).event("run_started").call("p", "planner", 100, 50).call("w", "implementer", 300, 100)
        run.write()
        Run(self.runs, RUN_B).call("w", "implementer", 10, 5).write()
        first = context_economy.build([run.dir])
        second = context_economy.build([run.dir])
        first.pop("generated_at"), second.pop("generated_at")
        self.assertEqual(json.dumps(first), json.dumps(second))
        out = self.home / "reports" / "ce.json"
        result = context_economy.report(self.home, out)
        self.assertEqual(result["runs"], [RUN_A, RUN_B])
        written = json.loads(out.read_text(encoding="utf-8"))
        self.assertEqual(written["schema"], context_economy.SCHEMA)
        self.assertEqual(written["coverage"]["eligible_calls"], 3)

    def test_empty_home(self):
        result = context_economy.report(self.home / "missing")
        self.assertEqual(result["runs"], [])
        self.assertIsNone(result["amplification"]["all"]["pooled_amplification"])


if __name__ == "__main__":
    unittest.main()
