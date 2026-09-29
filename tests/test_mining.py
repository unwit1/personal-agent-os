"""MIE-0004: failure/success signature clustering and coverage gaps."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from agent_os.orchestrator import mining  # noqa: E402


def fail(id, signature, status, recurrence, links=(), **extra):
    return {"id": id, "type": "FAIL", "signature": signature, "status": status, "recurrence": recurrence,
            "links": [{"rel": r, "ref": f} for r, f in links], **extra}


class MiningTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.records = Path(self.tmp.name)
        (self.records / "failures").mkdir()
        (self.records / "successes").mkdir()

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def write(self, kind, record):
        (self.records / kind / f"{record['id']}.json").write_text(json.dumps(record), encoding="utf-8")

    def test_clusters_by_signature_and_sums_recurrence(self) -> None:
        self.write("failures", fail("FAIL-1", "quota", "resolved", 3))
        self.write("failures", fail("FAIL-2", "quota", "open", 2))
        clusters = mining.cluster_failures([json.loads((self.records / "failures" / p.name).read_text()) for p in (self.records / "failures").glob("*.json")])
        quota = next(c for c in clusters if c["signature"] == "quota")
        self.assertEqual((quota["occurrences"], quota["distinct_records"], quota["open"]), (5, 2, 1))

    def test_open_recurring_uncovered_needs_coverage(self) -> None:
        self.write("failures", fail("FAIL-1", "bug_a", "open", 3))  # no test/exp link
        self.write("failures", fail("FAIL-2", "bug_b", "open", 3, links=[("tests", "tests/test_x.py")]))  # covered
        self.write("failures", fail("FAIL-3", "bug_c", "open", 1))  # not recurring
        self.write("failures", fail("FAIL-4", "bug_d", "resolved", 5))  # resolved
        report = mining.build(self.records)
        needing = {c["signature"] for c in report["needs_coverage"]}
        self.assertEqual(needing, {"bug_a"})
        self.assertEqual(report["totals"]["open_failures"], 3)

    def test_coverage_recognizes_experiment_and_regression_links(self) -> None:
        self.write("failures", fail("FAIL-1", "s", "open", 4, links=[("evidence_for", "EXP-0009")]))
        self.assertEqual(mining.build(self.records)["needs_coverage"], [])
        self.write("failures", fail("FAIL-2", "t", "open", 4, regression_case="tests/test_t.py"))
        self.assertNotIn("t", {c["signature"] for c in mining.build(self.records)["needs_coverage"]})

    def test_success_patterns_and_reuse_hint(self) -> None:
        self.write("successes", {"id": "SUC-1", "type": "SUC", "signature": "cheap_route", "recurrence": 2, "summary": "a reusable workflow"})
        report = mining.build(self.records)
        self.assertEqual(report["success_patterns"][0]["signature"], "cheap_route")
        self.assertTrue(report["success_patterns"][0]["reusable_hint"])

    def test_repository_records_have_no_open_coverage_gap(self) -> None:
        """Dogfood: real FAIL records are all resolved, so nothing is flagged."""
        report = mining.build()
        self.assertEqual(report["needs_coverage"], [], report["needs_coverage"])
        self.assertGreaterEqual(report["totals"]["failure_records"], 4)


if __name__ == "__main__":
    unittest.main()
