import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import hashlib
import json
import os
import re
import tempfile
import unittest

from agent_os.orchestrator import route_calibration


class RouteCalibrationShadowTests(unittest.TestCase):
    """Tests proving route_calibration is advice-only and never affects dispatch."""

    def test_no_source_file_imports_route_calibration(self):
        """Scan every .py file under src/agent_os/orchestrator except route_calibration.py and cli.py.
        Assert that none contains the text 'route_calibration'."""
        src_dir = Path(__file__).resolve().parents[1] / "src" / "agent_os" / "orchestrator"

        python_files = []
        for root, dirs, files in os.walk(src_dir):
            for file in files:
                if file.endswith(".py"):
                    filepath = Path(root) / file
                    # Skip route_calibration.py and cli.py
                    if filepath.name not in ("route_calibration.py", "cli.py"):
                        python_files.append(filepath)

        self.assertGreater(len(python_files), 10, "Should find many Python files to scan")

        # Check that none of these files contain 'route_calibration'
        for filepath in python_files:
            content = filepath.read_text(encoding="utf-8")
            if "route_calibration" in content:
                self.fail(f"{filepath.relative_to(src_dir)} contains 'route_calibration'")

    def test_route_calibration_no_subprocess_or_network_imports(self):
        """Assert route_calibration.py contains no subprocess, socket, urllib, http, or requests imports."""
        calibration_path = Path(__file__).resolve().parents[1] / "src" / "agent_os" / "orchestrator" / "route_calibration.py"
        content = calibration_path.read_text(encoding="utf-8")

        forbidden_modules = ["subprocess", "socket", "urllib", "http", "requests"]

        for module in forbidden_modules:
            # Look for direct imports or from imports
            if re.search(rf'import\s+{module}|from\s+{module}|import\s+.*\b{module}\b', content):
                self.fail(f"route_calibration imports forbidden module: {module}")

    def test_report_snapshot_unchanged_without_out_param(self):
        """Build a synthetic temp home with rich fixture, snapshot file hashes, call route_calibration.report(home)
        without out parameter, and assert snapshot is unchanged. Also verify at least one run was processed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            self._create_rich_fixture_home(home)

            # Snapshot the home directory before calling report
            initial_snapshot = self._snapshot_directory_hashes(home)

            # Call route_calibration.report(home) without out parameter
            result = route_calibration.report(home)

            # Verify result is a dict
            self.assertIsInstance(result, dict)

            # Verify that at least one run was processed
            self.assertEqual(result['coverage']['runs'], 1, "Should have processed 1 run")

            # Snapshot after and verify it's unchanged
            final_snapshot = self._snapshot_directory_hashes(home)

            self.assertEqual(initial_snapshot, final_snapshot,
                           "File hashes should be unchanged after report(home) without out parameter")

    def test_build_deterministic_except_generated_at(self):
        """Two build() calls on the same fixture give identical results once 'generated_at' is removed.
        Uses a rich fixture with enough nodes per capability class to produce non-empty calibrated cells and advice."""
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            self._create_rich_fixture_home(home)

            # Extract run directory for build() call
            runs_dir = home / "runs"
            run_dirs = [p for p in sorted(runs_dir.glob("*")) if p.is_dir()]

            # Call build() twice
            result1 = route_calibration.build(run_dirs)
            result2 = route_calibration.build(run_dirs)

            # Verify cells and advice are non-empty (rich fixture has enough samples)
            self.assertGreater(len(result1.get('cells', {})), 0, "Should have calibrated cells")
            self.assertGreater(len(result1.get('advice', {})), 0, "Should have routing advice")

            # Remove generated_at from both results for comparison
            result1_normalized = self._normalize_for_comparison(result1)
            result2_normalized = self._normalize_for_comparison(result2)

            # Verify they are identical except for generated_at
            self.assertEqual(result1_normalized, result2_normalized,
                           "Two build() calls should produce identical results (except generated_at)")

    def test_report_mode_is_shadow(self):
        """Assert that report()['mode'] == 'shadow'."""
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            runs_dir = home / "runs"
            runs_dir.mkdir(parents=True)

            # Create a synthetic run
            run_dir = runs_dir / "run-20261001T000000Z-aaaaaa"
            run_dir.mkdir(parents=True)

            # Create minimal telemetry.jsonl
            telemetry_file = run_dir / "telemetry.jsonl"
            telemetry_file.write_text(
                '{"schema": "personal-agent/orchestrator-run-telemetry/v1", "at": "2026-10-01T00:00:00+00:00", '
                '"seq": 1, "run_id": "run-20261001T000000Z-aaaaaa", "type": "run_started", "data": {}}\n',
                encoding="utf-8"
            )

            result = route_calibration.report(home)

            self.assertIn("mode", result)
            self.assertEqual(result["mode"], "shadow")

    def test_report_routing_changed_is_false(self):
        """Assert that report()['routing_changed'] is False."""
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            runs_dir = home / "runs"
            runs_dir.mkdir(parents=True)

            # Create a synthetic run
            run_dir = runs_dir / "run-20261001T000000Z-aaaaaa"
            run_dir.mkdir(parents=True)

            # Create minimal telemetry.jsonl
            telemetry_file = run_dir / "telemetry.jsonl"
            telemetry_file.write_text(
                '{"schema": "personal-agent/orchestrator-run-telemetry/v1", "at": "2026-10-01T00:00:00+00:00", '
                '"seq": 1, "run_id": "run-20261001T000000Z-aaaaaa", "type": "run_started", "data": {}}\n',
                encoding="utf-8"
            )

            result = route_calibration.report(home)

            self.assertIn("routing_changed", result)
            self.assertIs(result["routing_changed"], False)

    @staticmethod
    def _create_rich_fixture_home(home: Path) -> None:
        """Create a synthetic home directory with a run containing multiple nodes per capability class.

        Generates at least 6 nodes per capability class (to meet min_samples=5) with a mix of:
        - Passed tests (cheap_route_passed=True)
        - Escalations (cheap_route_passed=False)
        - Reviews with findings
        This ensures cells and advice are non-empty.
        """
        runs_dir = home / "runs"
        runs_dir.mkdir(parents=True)

        schema = "personal-agent/orchestrator-telemetry/v1"
        run_dir = runs_dir / "run-20261001T000000Z-abc123"
        run_dir.mkdir(parents=True)

        telemetry_file = run_dir / "telemetry.jsonl"
        events = []

        # Add run_started event
        events.append(json.dumps({
            "schema": schema,
            "type": "run_started",
            "seq": 0,
            "at": "2026-10-01T00:00:00+00:00",
            "run_id": "run-20261001T000000Z-abc123",
            "data": {}
        }) + "\n")

        seq = 1
        # Create 8 nodes in orchestrator-implementer/cheap family with mixed outcomes
        for i in range(1, 9):
            node_id = f"cheap-node-{i}"

            # Model completed event
            events.append(json.dumps({
                "schema": schema,
                "type": "model_completed",
                "node": node_id,
                "seq": seq,
                "at": f"2026-10-01T00:00:{seq:02d}+00:00",
                "data": {
                    "role": "implementer",
                    "capability_class": "cheap",
                    "effort": "low",
                    "provider": "claude"
                }
            }) + "\n")
            seq += 1

            # Nodes 1-5: passing tests; nodes 6-7: escalated; node 8: failed tests
            if i <= 5:
                events.append(json.dumps({
                    "schema": schema,
                    "type": "tests_completed",
                    "node": node_id,
                    "seq": seq,
                    "at": f"2026-10-01T00:00:{seq:02d}+00:00",
                    "data": {"passed": True}
                }) + "\n")
                seq += 1
            elif i <= 7:
                # Escalated
                events.append(json.dumps({
                    "schema": schema,
                    "type": "model_escalated",
                    "node": node_id,
                    "seq": seq,
                    "at": f"2026-10-01T00:00:{seq:02d}+00:00",
                    "data": {"to": "standard/default"}
                }) + "\n")
                seq += 1
            else:
                # Failed tests
                events.append(json.dumps({
                    "schema": schema,
                    "type": "tests_completed",
                    "node": node_id,
                    "seq": seq,
                    "at": f"2026-10-01T00:00:{seq:02d}+00:00",
                    "data": {"passed": False}
                }) + "\n")
                seq += 1

        # Create 8 nodes in orchestrator-implementer/standard family
        for i in range(1, 9):
            node_id = f"standard-node-{i}"

            events.append(json.dumps({
                "schema": schema,
                "type": "model_completed",
                "node": node_id,
                "seq": seq,
                "at": f"2026-10-01T00:00:{seq:02d}+00:00",
                "data": {
                    "role": "implementer",
                    "capability_class": "standard",
                    "effort": "medium",
                    "provider": "claude"
                }
            }) + "\n")
            seq += 1

            # Nodes 1-5: passing tests; nodes 6-7: failed tests; node 8: escalated
            if i <= 5:
                events.append(json.dumps({
                    "schema": schema,
                    "type": "tests_completed",
                    "node": node_id,
                    "seq": seq,
                    "at": f"2026-10-01T00:00:{seq:02d}+00:00",
                    "data": {"passed": True}
                }) + "\n")
                seq += 1
            elif i <= 7:
                # Failed tests
                events.append(json.dumps({
                    "schema": schema,
                    "type": "tests_completed",
                    "node": node_id,
                    "seq": seq,
                    "at": f"2026-10-01T00:00:{seq:02d}+00:00",
                    "data": {"passed": False}
                }) + "\n")
                seq += 1

                # Add review with findings for failed tests
                events.append(json.dumps({
                    "schema": schema,
                    "type": "review_completed",
                    "node": "reviewer-std",
                    "seq": seq,
                    "at": f"2026-10-01T00:00:{seq:02d}+00:00",
                    "data": {
                        "subject": f"{node_id}.repair1",
                        "material_findings": 1,
                        "verdict": "changes_requested"
                    }
                }) + "\n")
                seq += 1
            else:
                # Escalated
                events.append(json.dumps({
                    "schema": schema,
                    "type": "model_escalated",
                    "node": node_id,
                    "seq": seq,
                    "at": f"2026-10-01T00:00:{seq:02d}+00:00",
                    "data": {"to": "frontier/default"}
                }) + "\n")
                seq += 1

        telemetry_file.write_text("".join(events), encoding="utf-8")

    @staticmethod
    def _snapshot_directory_hashes(path: Path) -> dict:
        """Create a snapshot of all files under a directory: compute SHA256 hash of each file."""
        snapshot = {}
        for root, dirs, files in os.walk(path):
            for file in files:
                filepath = Path(root) / file
                relative = filepath.relative_to(path)
                file_hash = hashlib.sha256(filepath.read_bytes()).hexdigest()
                snapshot[str(relative)] = file_hash
        return snapshot

    @staticmethod
    def _normalize_for_comparison(result: dict) -> dict:
        """Remove generated_at from a result dict for deterministic comparison."""
        normalized = dict(result)
        if "generated_at" in normalized:
            del normalized["generated_at"]
        return normalized


if __name__ == "__main__":
    unittest.main()
