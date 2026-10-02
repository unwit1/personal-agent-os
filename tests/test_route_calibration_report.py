import sys
import json
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

from agent_os.orchestrator.route_calibration import build, report  # noqa: E402


class BuildTest(unittest.TestCase):
    def test_synthetic_home_with_coverage_and_cells(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            schema = "personal-agent/orchestrator-telemetry/v1"

            run1 = tmpdir_path / "run-20260101T000000Z-abc123"
            run1.mkdir()
            telemetry1 = run1 / "telemetry.jsonl"
            events1 = []
            # Add 5 passing cheap nodes and 1 escalated cheap node (6 total for min_samples=5)
            for i in range(1, 6):
                events1.append(json.dumps({"schema": schema, "type": "model_completed", "node": f"node-{i}", "seq": 1,
                           "data": {"role": "worker", "capability_class": "cheap",
                                   "effort": "low", "provider": "p1"}}) + "\n")
                events1.append(json.dumps({"schema": schema, "type": "tests_completed", "node": f"node-{i}", "seq": 2,
                           "data": {"passed": True}}) + "\n")
            # One escalated (counts as failed)
            events1.append(json.dumps({"schema": schema, "type": "model_completed", "node": "node-6", "seq": 1,
                           "data": {"role": "worker", "capability_class": "cheap",
                                   "effort": "low", "provider": "provider with spaces"}}) + "\n")
            events1.append(json.dumps({"schema": schema, "type": "model_escalated", "node": "node-6", "seq": 2,
                           "data": {"to": "expensive/default"}}) + "\n")
            telemetry1.write_text("".join(events1))

            run2 = tmpdir_path / "run-20260102T000000Z-def456"
            run2.mkdir()
            telemetry2 = run2 / "telemetry.jsonl"
            telemetry2.write_text(
                json.dumps({"schema": schema, "type": "model_completed", "node": "node-7", "seq": 1,
                           "data": {"role": "worker", "capability_class": "cheap",
                                   "effort": "low", "provider": "p1"}}) + "\n" +
                json.dumps({"schema": schema, "type": "tests_completed", "node": "node-7", "seq": 2,
                           "data": {"passed": True}}) + "\n" +
                json.dumps({"schema": schema, "type": "model_completed", "node": "node-8", "seq": 1,
                           "data": {"role": "reviewer", "capability_class": "standard",
                                   "effort": "medium", "provider": "p2"}}) + "\n"
            )

            malformed_run = tmpdir_path / "bad-run-dir"
            malformed_run.mkdir()
            malformed_telemetry = malformed_run / "telemetry.jsonl"
            malformed_telemetry.write_text("")

            run3 = tmpdir_path / "run-20260103T000000Z-aabbcc"
            run3.mkdir()
            telemetry3 = run3 / "telemetry.jsonl"
            telemetry3.write_text(
                json.dumps({"schema": schema, "type": "model_completed", "node": "node-9", "seq": 1,
                           "data": {"role": "worker", "capability_class": "cheap",
                                   "effort": "low", "provider": "p1"}}) + "\n" +
                "not valid json\n" +
                json.dumps({"schema": schema, "type": "tests_completed", "node": "node-9", "seq": 2,
                           "data": {"passed": True}}) + "\n"
            )

            result = build([run1, run2, malformed_run, run3], min_samples=5, target=0.9)

            # Check coverage counts
            self.assertEqual(result["coverage"]["runs"], 3)
            self.assertEqual(result["coverage"]["malformed_runs"], 1)
            self.assertEqual(result["coverage"]["malformed_lines"], 1)
            self.assertEqual(result["coverage"]["nodes"], 8)
            self.assertEqual(result["coverage"]["reviewer_nodes_excluded"], 1)
            self.assertEqual(result["coverage"]["labeled"], 8)
            self.assertEqual(result["coverage"]["unlabeled"], 0)
            self.assertEqual(result["coverage"]["sanitized_labels"], 1)

            # Check run IDs
            self.assertEqual(len(result["runs"]), 3)
            self.assertIn("run-20260101T000000Z-abc123", result["runs"])
            self.assertIn("run-20260102T000000Z-def456", result["runs"])
            self.assertIn("run-20260103T000000Z-aabbcc", result["runs"])

            # Check cells structure and values
            cells = result["cells"]
            self.assertIn("orchestrator-worker", cells)
            self.assertIn("cheap", cells["orchestrator-worker"])

            cheap_cell = cells["orchestrator-worker"]["cheap"]
            self.assertEqual(cheap_cell["n"], 8)
            self.assertEqual(cheap_cell["passes"], 7)
            self.assertEqual(cheap_cell["unlabeled"], 0)
            self.assertEqual(cheap_cell["escalated"], 1)
            self.assertTrue(cheap_cell["sufficient"])
            self.assertIn("other", cheap_cell["by_provider"])

            # Check that no node id appears in any label
            for family in cells:
                for class_name in cells[family]:
                    cell = cells[family][class_name]
                    for effort in cell.get("by_effort", {}).keys():
                        self.assertNotIn("node", effort.lower())
                    for provider in cell.get("by_provider", {}).keys():
                        self.assertNotIn("node", provider.lower())

            # Check calibration and advice
            calibration = result["calibration"]
            self.assertEqual(calibration["target"], 0.9)
            self.assertEqual(calibration["reason"], "no_threshold_meets_target")
            self.assertIsNone(calibration["recommended_threshold"])

            # Check advice
            advice = result["advice"]
            self.assertIn("orchestrator-worker", advice)
            self.assertIn("cheap", advice["orchestrator-worker"])
            self.assertEqual(advice["orchestrator-worker"]["cheap"], "escalate_earlier")

            # Verify routing_changed is False
            self.assertEqual(result["routing_changed"], False)


class ReportTest(unittest.TestCase):
    def test_empty_home(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            result = report(home=tmpdir_path)
            self.assertEqual(result["runs"], [])
            self.assertEqual(result["coverage"]["runs"], 0)

    def test_report_with_runs(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            runs_dir = tmpdir_path / "runs"
            runs_dir.mkdir()

            run_dir = runs_dir / "run-20260101T000000Z-abc123"
            run_dir.mkdir()
            telemetry = run_dir / "telemetry.jsonl"
            telemetry.write_text(
                json.dumps({"type": "model_completed", "node": "node-1", "seq": 1,
                           "data": {"role": "worker", "capability_class": "cheap",
                                   "effort": "low", "provider": "p1"}}) + "\n"
            )

            result = report(home=tmpdir_path)
            self.assertEqual(len(result["runs"]), 1)
            self.assertEqual(result["runs"][0], "run-20260101T000000Z-abc123")

    def test_report_with_output_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            runs_dir = tmpdir_path / "runs"
            runs_dir.mkdir()

            run_dir = runs_dir / "run-20260101T000000Z-abc123"
            run_dir.mkdir()
            telemetry = run_dir / "telemetry.jsonl"
            telemetry.write_text(
                json.dumps({"type": "model_completed", "node": "node-1", "seq": 1,
                           "data": {"role": "worker", "capability_class": "cheap",
                                   "effort": "low", "provider": "p1"}}) + "\n"
            )

            out_path = tmpdir_path / "output" / "report.json"
            result = report(home=tmpdir_path, out=out_path)

            self.assertTrue(out_path.exists())
            with open(out_path) as f:
                loaded = json.load(f)
            self.assertEqual(loaded["schema"], result["schema"])
            self.assertEqual(loaded["mode"], result["mode"])

    def test_report_output_parents_created(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            runs_dir = tmpdir_path / "runs"
            runs_dir.mkdir()

            run_dir = runs_dir / "run-20260101T000000Z-abc123"
            run_dir.mkdir()
            telemetry = run_dir / "telemetry.jsonl"
            telemetry.write_text("")

            out_path = tmpdir_path / "deep" / "nested" / "path" / "report.json"
            result = report(home=tmpdir_path, out=out_path)

            self.assertTrue(out_path.exists())
            self.assertTrue(out_path.parent.exists())

    def test_report_multiple_runs_sorted(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            runs_dir = tmpdir_path / "runs"
            runs_dir.mkdir()

            for name in ["run-20260103T000000Z-abcdef", "run-20260101T000000Z-abc123",
                        "run-20260102T000000Z-def456"]:
                run_dir = runs_dir / name
                run_dir.mkdir()
                telemetry = run_dir / "telemetry.jsonl"
                telemetry.write_text("")

            result = report(home=tmpdir_path)
            self.assertEqual(len(result["runs"]), 3)
            self.assertEqual(result["runs"],
                           ["run-20260101T000000Z-abc123", "run-20260102T000000Z-def456",
                            "run-20260103T000000Z-abcdef"])

    def test_report_non_matching_dirs_ignored(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            runs_dir = tmpdir_path / "runs"
            runs_dir.mkdir()

            valid_run = runs_dir / "run-20260101T000000Z-abc123"
            valid_run.mkdir()
            telemetry = valid_run / "telemetry.jsonl"
            telemetry.write_text("")

            invalid_dir = runs_dir / "not-a-run"
            invalid_dir.mkdir()

            result = report(home=tmpdir_path)
            self.assertEqual(len(result["runs"]), 1)
            self.assertEqual(result["coverage"]["malformed_runs"], 1)

    def test_report_json_formatting(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            runs_dir = tmpdir_path / "runs"
            runs_dir.mkdir()

            run_dir = runs_dir / "run-20260101T000000Z-abc123"
            run_dir.mkdir()
            telemetry = run_dir / "telemetry.jsonl"
            telemetry.write_text("")

            out_path = tmpdir_path / "report.json"
            result = report(home=tmpdir_path, out=out_path)

            with open(out_path) as f:
                content = f.read()
            loaded = json.loads(content)

            self.assertEqual(loaded["schema"], result["schema"])
            keys = list(loaded.keys())
            self.assertEqual(keys, sorted(keys))


if __name__ == "__main__":
    unittest.main()
