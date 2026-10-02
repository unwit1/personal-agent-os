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
        """Build a synthetic temp home, snapshot file hashes, call route_calibration.report(home)
        without out parameter, and assert snapshot is unchanged."""
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            runs_dir = home / "runs"
            runs_dir.mkdir(parents=True)

            # Create a synthetic run with minimal structure
            run_dir = runs_dir / "run-20261001T000000Z-aaaaaa"
            run_dir.mkdir(parents=True)

            # Create a minimal telemetry.jsonl
            telemetry_file = run_dir / "telemetry.jsonl"
            telemetry_file.write_text(
                '{"schema": "personal-agent/orchestrator-run-telemetry/v1", "at": "2026-10-01T00:00:00+00:00", '
                '"seq": 1, "run_id": "run-20261001T000000Z-aaaaaa", "type": "run_started", "data": {}}\n',
                encoding="utf-8"
            )

            # Snapshot the home directory before calling report
            initial_snapshot = self._snapshot_directory_hashes(home)

            # Call route_calibration.report(home) without out parameter
            result = route_calibration.report(home)

            # Verify result is a dict
            self.assertIsInstance(result, dict)

            # Snapshot after and verify it's unchanged
            final_snapshot = self._snapshot_directory_hashes(home)

            self.assertEqual(initial_snapshot, final_snapshot,
                           "File hashes should be unchanged after report(home) without out parameter")

    def test_build_deterministic_except_generated_at(self):
        """Two build() calls on the same fixture give identical results once 'generated_at' is removed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            runs_dir = home / "runs"
            runs_dir.mkdir(parents=True)

            # Create a synthetic run with some events
            run_dir = runs_dir / "run-20261001T000000Z-testrun"
            run_dir.mkdir(parents=True)

            # Create telemetry.jsonl with some model events
            telemetry_file = run_dir / "telemetry.jsonl"
            telemetry_file.write_text(
                '{"schema": "personal-agent/orchestrator-run-telemetry/v1", "at": "2026-10-01T00:00:00+00:00", '
                '"seq": 1, "run_id": "run-20261001T000000Z-testrun", "type": "run_started", "data": {}}\n'
                '{"schema": "personal-agent/orchestrator-run-telemetry/v1", "at": "2026-10-01T00:00:01+00:00", '
                '"seq": 2, "run_id": "run-20261001T000000Z-testrun", "type": "model_completed", "node": "worker-1", '
                '"data": {"role": "implementer", "capability_class": "standard", "provider": "claude", "model": "sonnet", '
                '"attempt": 1, "prompt_tokens_estimate": 100, "usage": {"input_tokens": 200, "uncached_input_tokens": 200, '
                '"cache_read_tokens": 0, "cache_write_tokens": 0, "output_tokens": 50, "cost_usd": null, "accuracy": "exact", '
                '"source": "claude-code"}}}\n'
                '{"schema": "personal-agent/orchestrator-run-telemetry/v1", "at": "2026-10-01T00:00:02+00:00", '
                '"seq": 3, "run_id": "run-20261001T000000Z-testrun", "type": "tests_completed", "node": "worker-1", '
                '"data": {"passed": true}}\n',
                encoding="utf-8"
            )

            # Call build() twice
            run_dirs = [run_dir]
            result1 = route_calibration.build(run_dirs)
            result2 = route_calibration.build(run_dirs)

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
