"""The efficiency benchmark runs the real orchestration path and never
reports invented token numbers."""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.orchestrator.benchmark import run_benchmark  # noqa: E402


class BenchmarkTests(unittest.TestCase):
    def test_offline_benchmark_is_honest_and_repeatable(self) -> None:
        out = Path(tempfile.mkdtemp(prefix="agent-os-bench-test-"))
        self.addCleanup(shutil.rmtree, out, True)
        report = run_benchmark(["repository_inspection", "test_failure_repair", "roadmap_continuation"], out_dir=out)
        self.assertEqual(report["totals"]["passed"], 3, json.dumps(report["scenarios"], indent=1)[:2000])
        by_name = {item["scenario"]: item for item in report["scenarios"]}
        self.assertEqual(by_name["repository_inspection"]["model_calls"], 0)
        self.assertEqual(by_name["repository_inspection"]["model_calls_avoided"], 1)
        self.assertEqual(by_name["test_failure_repair"]["escalations"], 1)
        roadmap_run = by_name["roadmap_continuation"]
        self.assertEqual(roadmap_run["model_calls_by_role"], {"planner": 1, "implementer": 1, "reviewer": 1})
        for item in report["scenarios"]:
            self.assertEqual(item["tokens"]["accuracy"], "unavailable", "synthetic workers never report tokens")
            self.assertIsNone(item["tokens"]["input"])
            self.assertIn("ESTIMATED", item["baseline_modeled"]["label"])
        self.assertTrue((out / "results.json").exists())
        self.assertIn("Methodology", (out / "report.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
