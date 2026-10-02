import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import json
import tempfile
import unittest

from agent_os.orchestrator import rotation_advisor
from agent_os.orchestrator.ledger import SCHEMA as TELEMETRY_SCHEMA

RUN = "run-20260101T000000Z-abcdef"
NODES = ("n-alpha", "n-beta", "n-gamma", "n-plan", "n-rev")


def usage(input_tokens, output=0):
    return {"accuracy": "exact", "source": "claude-code", "input_tokens": input_tokens, "uncached_input_tokens": input_tokens,
            "cache_read_tokens": 0, "cache_write_tokens": 0, "output_tokens": output, "cost_usd": None}


class Run:
    def __init__(self, runs_dir: Path, run_id: str):
        self.dir = runs_dir / run_id
        self.dir.mkdir(parents=True)
        self.run_id = run_id
        self.lines: list[str] = []
        self.seq = 0

    def event(self, kind, node=None, **data):
        self.seq += 1
        self.lines.append(json.dumps({"schema": TELEMETRY_SCHEMA, "at": "2026-01-01T00:00:00+00:00", "seq": self.seq,
                                      "run_id": self.run_id, "type": kind, "node": node, "data": data}))
        return self

    def call(self, node, role, input_tokens, prompt, output=0, attempt=1):
        return self.event("model_completed", node, role=role, capability_class="standard", provider="claude-code", model="sonnet",
                          attempt=attempt, prompt_chars=prompt * 4, prompt_tokens_estimate=prompt, usage=usage(input_tokens, output))

    def write(self, extra=""):
        (self.dir / "telemetry.jsonl").write_text("\n".join(self.lines) + "\n" + extra, encoding="utf-8")
        return self.dir


class RotationAdvisorReportTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.home = Path(self._tmp.name)
        self.runs = self.home / "runs"
        self.runs.mkdir()

    def make_run(self, extra=""):
        run = Run(self.runs, RUN).event("run_started")
        for attempt in (1, 2, 3):
            run.call("n-alpha", "implementer", 10000, 100, output=200, attempt=attempt)
        run.call("n-beta", "implementer", 1000, 100)
        run.call("n-gamma", "implementer", 1000, 100)
        run.call("n-plan", "planner", 800, 100)
        # rework events after every call, so they are counted but cannot change a score
        run.event("retry", "n-alpha").event("model_escalated", "n-alpha").event("fallback", "n-alpha")
        run.event("review_started", "n-rev", subject="n-alpha")
        run.event("review_completed", "n-rev", subject="n-alpha", material_findings=1)
        return run.write(extra)

    def test_exact_aggregates(self):
        self.make_run()
        result = rotation_advisor.report(self.home)
        self.assertEqual((result["schema"], result["mode"], result["dispatch_changed"]),
                         ("personal-agent/orchestrator-rotation-advice/v1", "shadow", False))
        self.assertEqual(result["runs"], [RUN])
        cov = result["coverage"]
        self.assertEqual((cov["runs"], cov["workers"], cov["calls"], cov["eligible_calls"], cov["malformed_lines"]), (1, 4, 6, 6, 0))
        self.assertEqual(cov["event_counts"], {"retry": 1, "model_escalated": 1, "fallback": 1, "review_started": 1,
                                               "review_completed": 1, "review_required": 1})
        rec = result["recommendations"]
        self.assertEqual(rec["by_role"], {"implementer": {"continue": 2, "rotate": 1}, "planner": {"continue": 1, "rotate": 0}})
        self.assertEqual(rec["by_node_call_bucket"], {"1": {"continue": 3, "rotate": 0}, "2-3": {"continue": 0, "rotate": 1},
                                                      "4+": {"continue": 0, "rotate": 0}})
        self.assertEqual(rec["by_role_and_bucket"]["implementer"]["2-3"], {"continue": 0, "rotate": 1})
        self.assertEqual(result["would_rotate_share"], 0.25)
        # bootstrap(implementer) = median(10000, 1000, 1000) = 1000; boundary 1: rest 20000 vs 2000 + 200 + 200
        self.assertEqual(result["predicted_savings"], {"count": 1, "median": 17600, "p90": 17600, "min": 17600, "max": 17600})
        self.assertEqual(result["break_even_boundary"], {"implementer": {"count": 1, "median": 1, "p90": 1, "min": 1, "max": 1}})
        self.assertEqual(result["sum_continue_cost"], 32800)
        self.assertEqual(result["sum_rotate_cost_if_advised"], 15200)

    def test_node_ids_never_appear(self):
        self.make_run()
        text = json.dumps(rotation_advisor.report(self.home))
        for node in NODES:
            self.assertNotIn(node, text)

    def test_malformed_lines_and_foreign_dirs_are_counted(self):
        self.make_run(extra="not json\n{\"schema\": \"other\"}\n")
        (self.runs / "not-a-run").mkdir()
        result = rotation_advisor.report(self.home)
        self.assertEqual(result["coverage"]["malformed_lines"], 2)
        self.assertEqual(result["coverage"]["malformed_runs"], 1)
        self.assertEqual(result["coverage"]["runs"], 1)
        self.assertEqual(result["recommendations"]["by_role"]["implementer"], {"continue": 2, "rotate": 1})

    def test_empty_home_has_zero_coverage(self):
        empty = self.home / "empty"
        empty.mkdir()
        result = rotation_advisor.report(empty)
        self.assertEqual((result["coverage"]["runs"], result["coverage"]["workers"], result["coverage"]["eligible_calls"]), (0, 0, 0))
        self.assertIsNone(result["would_rotate_share"])
        self.assertEqual(result["predicted_savings"]["count"], 0)
        self.assertEqual((result["sum_continue_cost"], result["sum_rotate_cost_if_advised"]), (0, 0))
        self.assertEqual(result["recommendations"]["by_role"], {})

    def test_out_file_written_only_when_given(self):
        self.make_run()
        rotation_advisor.report(self.home)
        self.assertFalse((self.home / "out").exists())
        target = self.home / "out" / "advice.json"
        result = rotation_advisor.report(self.home, target)
        self.assertEqual(json.loads(target.read_text(encoding="utf-8")), result)

    def test_deterministic_apart_from_generated_at(self):
        self.make_run()
        first, second = rotation_advisor.report(self.home), rotation_advisor.report(self.home)
        first.pop("generated_at"), second.pop("generated_at")
        self.assertEqual(json.dumps(first, sort_keys=True), json.dumps(second, sort_keys=True))


if __name__ == "__main__":
    unittest.main()
