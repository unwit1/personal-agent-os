import sys
import json
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

from agent_os.orchestrator.route_calibration import build, report  # noqa: E402


class BuildTest(unittest.TestCase):
    def test_empty_run_dirs(self):
        result = build([])
        self.assertEqual(result["schema"], "personal-agent/orchestrator-route-calibration/v1")
        self.assertEqual(result["mode"], "shadow")
        self.assertIsNotNone(result["generated_at"])
        self.assertEqual(result["routing_changed"], False)
        self.assertEqual(result["runs"], [])
        self.assertEqual(result["coverage"]["runs"], 0)
        self.assertEqual(result["coverage"]["malformed_runs"], 0)
        self.assertEqual(result["coverage"]["malformed_lines"], 0)
        self.assertEqual(result["coverage"]["nodes"], 0)
        self.assertEqual(result["coverage"]["labeled"], 0)
        self.assertEqual(result["coverage"]["unlabeled"], 0)
        self.assertEqual(result["coverage"]["reviewer_nodes_excluded"], 0)

    def test_malformed_run_dir_name(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            malformed_dir = tmpdir_path / "bad-name-123"
            malformed_dir.mkdir()
            telemetry = malformed_dir / "telemetry.jsonl"
            telemetry.write_text("")

            result = build([malformed_dir])
            self.assertEqual(result["coverage"]["malformed_runs"], 1)
            self.assertEqual(result["runs"], [])

    def test_valid_run_structure(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            run_dir = tmpdir_path / "run-20260101T000000Z-abc123"
            run_dir.mkdir()

            telemetry = run_dir / "telemetry.jsonl"
            telemetry.write_text(
                json.dumps({"type": "model_completed", "node": "test-node", "seq": 1,
                           "data": {"role": "worker", "capability_class": "cheap",
                                   "effort": "low", "provider": "p1"}}) + "\n" +
                json.dumps({"type": "tests_completed", "node": "test-node", "seq": 2,
                           "data": {"passed": True}}) + "\n"
            )

            result = build([run_dir])
            self.assertEqual(result["coverage"]["runs"], 1)
            self.assertEqual(result["coverage"]["malformed_runs"], 0)
            self.assertEqual(len(result["runs"]), 1)
            self.assertEqual(result["runs"][0], "run-20260101T000000Z-abc123")

    def test_multiple_run_dirs(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            run1 = tmpdir_path / "run-20260101T000000Z-abc123"
            run2 = tmpdir_path / "run-20260102T000000Z-def456"
            run1.mkdir()
            run2.mkdir()

            for run_dir in [run1, run2]:
                telemetry = run_dir / "telemetry.jsonl"
                telemetry.write_text(
                    json.dumps({"type": "model_completed", "node": "node-1", "seq": 1,
                               "data": {"role": "worker", "capability_class": "cheap",
                                       "effort": "low", "provider": "p1"}}) + "\n"
                )

            result = build([run1, run2])
            self.assertEqual(result["coverage"]["runs"], 2)
            self.assertEqual(len(result["runs"]), 2)

    def test_coverage_tracking(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            run_dir = tmpdir_path / "run-20260101T000000Z-abc123"
            run_dir.mkdir()

            telemetry = run_dir / "telemetry.jsonl"
            telemetry.write_text(
                json.dumps({"type": "model_completed", "node": "test-node", "seq": 1,
                           "data": {"role": "worker", "capability_class": "cheap",
                                   "effort": "low", "provider": "p1"}}) + "\n" +
                json.dumps({"type": "tests_completed", "node": "test-node", "seq": 2,
                           "data": {"passed": True}}) + "\n"
            )

            result = build([run_dir])
            cov = result["coverage"]
            self.assertIn("runs", cov)
            self.assertIn("malformed_runs", cov)
            self.assertIn("malformed_lines", cov)
            self.assertIn("nodes", cov)
            self.assertIn("labeled", cov)
            self.assertIn("unlabeled", cov)
            self.assertIn("sanitized_labels", cov)

    def test_cells_structure(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            run_dir = tmpdir_path / "run-20260101T000000Z-abc123"
            run_dir.mkdir()

            outcomes = []
            for i in range(10):
                outcomes.append(
                    json.dumps({"type": "model_completed", "node": f"node-{i}", "seq": 1,
                               "data": {"role": "worker", "capability_class": "cheap",
                                       "effort": "low", "provider": "p1"}}) + "\n" +
                    json.dumps({"type": "tests_completed", "node": f"node-{i}", "seq": 2,
                               "data": {"passed": True}}) + "\n"
                )

            telemetry = run_dir / "telemetry.jsonl"
            telemetry.write_text("".join(outcomes))

            result = build([run_dir], min_samples=5)
            self.assertIn("cells", result)
            self.assertIsInstance(result["cells"], dict)

    def test_calibration_structure(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            run_dir = tmpdir_path / "run-20260101T000000Z-abc123"
            run_dir.mkdir()

            outcomes = []
            for i in range(10):
                outcomes.append(
                    json.dumps({"type": "model_completed", "node": f"node-{i}", "seq": 1,
                               "data": {"role": "worker", "capability_class": "cheap",
                                       "effort": "low", "provider": "p1"}}) + "\n" +
                    json.dumps({"type": "tests_completed", "node": f"node-{i}", "seq": 2,
                               "data": {"passed": True}}) + "\n"
                )

            telemetry = run_dir / "telemetry.jsonl"
            telemetry.write_text("".join(outcomes))

            result = build([run_dir], min_samples=5, target=0.9)
            self.assertIn("calibration", result)
            self.assertIn("curve", result["calibration"])
            self.assertIn("target", result["calibration"])
            self.assertIn("recommended_threshold", result["calibration"])
            self.assertEqual(result["calibration"]["target"], 0.9)

    def test_advice_structure(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            run_dir = tmpdir_path / "run-20260101T000000Z-abc123"
            run_dir.mkdir()

            outcomes = []
            for i in range(10):
                outcomes.append(
                    json.dumps({"type": "model_completed", "node": f"node-{i}", "seq": 1,
                               "data": {"role": "worker", "capability_class": "cheap",
                                       "effort": "low", "provider": "p1"}}) + "\n" +
                    json.dumps({"type": "tests_completed", "node": f"node-{i}", "seq": 2,
                               "data": {"passed": True}}) + "\n"
                )

            telemetry = run_dir / "telemetry.jsonl"
            telemetry.write_text("".join(outcomes))

            result = build([run_dir], min_samples=5)
            self.assertIn("advice", result)
            self.assertIsInstance(result["advice"], dict)

    def test_method_metadata(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            run_dir = tmpdir_path / "run-20260101T000000Z-abc123"
            run_dir.mkdir()
            telemetry = run_dir / "telemetry.jsonl"
            telemetry.write_text("")

            result = build([run_dir])
            self.assertIn("method", result)
            self.assertEqual(result["method"]["estimator"], "beta_binomial_laplace")
            self.assertEqual(result["method"]["bound"], "wilson_95")
            self.assertEqual(result["method"]["prior_art"], "PA-routellm")
            self.assertEqual(result["method"]["decision"], "BORROW")

    def test_routing_changed_always_false(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            run_dir = tmpdir_path / "run-20260101T000000Z-abc123"
            run_dir.mkdir()
            telemetry = run_dir / "telemetry.jsonl"
            telemetry.write_text("")

            result = build([run_dir])
            self.assertEqual(result["routing_changed"], False)

    def test_synthetic_home_with_coverage_and_cells(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            schema = "personal-agent/orchestrator-telemetry/v1"

            run1 = tmpdir_path / "run-20260101T000000Z-abc123"
            run1.mkdir()
            telemetry1 = run1 / "telemetry.jsonl"
            telemetry1.write_text(
                json.dumps({"schema": schema, "type": "model_completed", "node": "node-1", "seq": 1,
                           "data": {"role": "worker", "capability_class": "cheap",
                                   "effort": "low", "provider": "p1"}}) + "\n" +
                json.dumps({"schema": schema, "type": "tests_completed", "node": "node-1", "seq": 2,
                           "data": {"passed": True}}) + "\n" +
                json.dumps({"schema": schema, "type": "model_completed", "node": "node-2", "seq": 1,
                           "data": {"role": "worker", "capability_class": "cheap",
                                   "effort": "low", "provider": "p1"}}) + "\n" +
                json.dumps({"schema": schema, "type": "model_escalated", "node": "node-2", "seq": 2,
                           "data": {"to": "expensive/default"}}) + "\n"
            )

            run2 = tmpdir_path / "run-20260102T000000Z-def456"
            run2.mkdir()
            telemetry2 = run2 / "telemetry.jsonl"
            telemetry2.write_text(
                json.dumps({"schema": schema, "type": "model_completed", "node": "node-3", "seq": 1,
                           "data": {"role": "worker", "capability_class": "cheap",
                                   "effort": "low", "provider": "p1"}}) + "\n" +
                json.dumps({"schema": schema, "type": "tests_completed", "node": "node-3", "seq": 2,
                           "data": {"passed": False}}) + "\n" +
                json.dumps({"schema": schema, "type": "model_completed", "node": "node-4", "seq": 1,
                           "data": {"role": "reviewer", "capability_class": "standard",
                                   "effort": "medium", "provider": "p2"}}) + "\n" +
                json.dumps({"schema": schema, "type": "model_completed", "node": "node-5", "seq": 1,
                           "data": {"role": "worker", "capability_class": "expensive",
                                   "effort": "high", "provider": "p3"}}) + "\n" +
                json.dumps({"schema": schema, "type": "tests_completed", "node": "node-5", "seq": 2,
                           "data": {"passed": True}}) + "\n"
            )

            malformed_run = tmpdir_path / "bad-run-dir"
            malformed_run.mkdir()
            malformed_telemetry = malformed_run / "telemetry.jsonl"
            malformed_telemetry.write_text("")

            run3 = tmpdir_path / "run-20260103T000000Z-aabbcc"
            run3.mkdir()
            telemetry3 = run3 / "telemetry.jsonl"
            telemetry3.write_text(
                json.dumps({"schema": schema, "type": "model_completed", "node": "node-6", "seq": 1,
                           "data": {"role": "worker", "capability_class": "cheap",
                                   "effort": "low", "provider": "p1"}}) + "\n" +
                "not valid json\n" +
                json.dumps({"schema": schema, "type": "tests_completed", "node": "node-6", "seq": 2,
                           "data": {"passed": True}}) + "\n"
            )

            result = build([run1, run2, malformed_run, run3])

            self.assertEqual(result["coverage"]["runs"], 3)
            self.assertEqual(result["coverage"]["malformed_runs"], 1)
            self.assertEqual(result["coverage"]["malformed_lines"], 1)
            self.assertEqual(result["coverage"]["nodes"], 5)
            self.assertEqual(result["coverage"]["reviewer_nodes_excluded"], 1)
            self.assertEqual(result["coverage"]["labeled"], 5)
            self.assertEqual(result["coverage"]["unlabeled"], 0)

            self.assertEqual(len(result["runs"]), 3)
            self.assertIn("run-20260101T000000Z-abc123", result["runs"])
            self.assertIn("run-20260102T000000Z-def456", result["runs"])
            self.assertIn("run-20260103T000000Z-aabbcc", result["runs"])

            cells = result["cells"]
            self.assertIn("orchestrator-worker", cells)
            self.assertIn("cheap", cells["orchestrator-worker"])

            cheap_cell = cells["orchestrator-worker"]["cheap"]
            self.assertEqual(cheap_cell["n"], 4)
            self.assertEqual(cheap_cell["passes"], 2)
            self.assertEqual(cheap_cell["unlabeled"], 0)
            self.assertEqual(cheap_cell["escalated"], 1)

            self.assertIn("expensive", cells["orchestrator-worker"])
            expensive_cell = cells["orchestrator-worker"]["expensive"]
            self.assertEqual(expensive_cell["n"], 1)
            self.assertEqual(expensive_cell["passes"], 1)

    def test_malformed_json_line(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            run_dir = tmpdir_path / "run-20260101T000000Z-abc123"
            run_dir.mkdir()

            telemetry = run_dir / "telemetry.jsonl"
            telemetry.write_text(
                json.dumps({"type": "model_completed", "node": "node-1", "seq": 1,
                           "data": {"role": "worker", "capability_class": "cheap",
                                   "effort": "low", "provider": "p1"}}) + "\n" +
                "not valid json\n"
            )

            result = build([run_dir])
            self.assertGreater(result["coverage"]["malformed_lines"], 0)

    def test_min_samples_parameter(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            run_dir = tmpdir_path / "run-20260101T000000Z-abc123"
            run_dir.mkdir()

            outcomes = []
            for i in range(3):
                outcomes.append(
                    json.dumps({"type": "model_completed", "node": f"node-{i}", "seq": 1,
                               "data": {"role": "worker", "capability_class": "cheap",
                                       "effort": "low", "provider": "p1"}}) + "\n" +
                    json.dumps({"type": "tests_completed", "node": f"node-{i}", "seq": 2,
                               "data": {"passed": True}}) + "\n"
                )

            telemetry = run_dir / "telemetry.jsonl"
            telemetry.write_text("".join(outcomes))

            result = build([run_dir], min_samples=5)
            if "orchestrator-worker" in result["cells"]:
                cell = result["cells"]["orchestrator-worker"].get("cheap", {})
                self.assertFalse(cell.get("sufficient", False))

    def test_target_parameter(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            run_dir = tmpdir_path / "run-20260101T000000Z-abc123"
            run_dir.mkdir()

            outcomes = []
            for i in range(10):
                outcomes.append(
                    json.dumps({"type": "model_completed", "node": f"node-{i}", "seq": 1,
                               "data": {"role": "worker", "capability_class": "cheap",
                                       "effort": "low", "provider": "p1"}}) + "\n" +
                    json.dumps({"type": "tests_completed", "node": f"node-{i}", "seq": 2,
                               "data": {"passed": True}}) + "\n"
                )

            telemetry = run_dir / "telemetry.jsonl"
            telemetry.write_text("".join(outcomes))

            result1 = build([run_dir], min_samples=5, target=0.9)
            result2 = build([run_dir], min_samples=5, target=0.85)
            self.assertEqual(result1["calibration"]["target"], 0.9)
            self.assertEqual(result2["calibration"]["target"], 0.85)


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
