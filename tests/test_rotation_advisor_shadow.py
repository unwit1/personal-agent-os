import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import builtins
import json
import os
import re
import tempfile
import unittest
from unittest import mock

from agent_os.orchestrator import rotation_advisor


class RotationAdvisorShadowTests(unittest.TestCase):
    """Tests proving rotation_advisor is advice-only and never affects dispatch."""

    def test_no_source_file_imports_rotation_advisor(self):
        """Scan every .py file under src/agent_os except rotation_advisor.py and cli.py.
        Assert that none imports rotation_advisor."""
        src_dir = Path(__file__).resolve().parents[1] / "src" / "agent_os"

        # Find all Python files except rotation_advisor.py and cli.py
        python_files = []
        for root, dirs, files in os.walk(src_dir):
            for file in files:
                if file.endswith(".py"):
                    filepath = Path(root) / file
                    # Skip rotation_advisor.py and cli.py
                    if filepath.name not in ("rotation_advisor.py", "cli.py"):
                        python_files.append(filepath)

        self.assertGreater(len(python_files), 10, "Should find many Python files to scan")

        # Check that none of these files import rotation_advisor
        for filepath in python_files:
            content = filepath.read_text(encoding="utf-8")
            # Look for imports of rotation_advisor
            # Match patterns like: from ... import rotation_advisor, import rotation_advisor, etc.
            if re.search(r'from\s+.*rotation_advisor|import\s+.*rotation_advisor', content):
                self.fail(f"{filepath.relative_to(src_dir)} imports rotation_advisor")

    def test_rotation_advisor_imports_no_engine_dispatch_provider(self):
        """Assert rotation_advisor.py doesn't import engine, dispatch or provider modules."""
        advisor_path = Path(__file__).resolve().parents[1] / "src" / "agent_os" / "orchestrator" / "rotation_advisor.py"
        content = advisor_path.read_text(encoding="utf-8")

        # Check for forbidden module imports
        forbidden_patterns = [
            r'from\s+.*\bengine\b',
            r'import\s+.*\bengine\b',
            r'from\s+.*\bdispatch\b',
            r'import\s+.*\bdispatch\b',
            r'from\s+.*\bprovider',
            r'import\s+.*\bprovider',
        ]

        for pattern in forbidden_patterns:
            if re.search(pattern, content):
                self.fail(f"rotation_advisor imports forbidden module matching: {pattern}")

    def test_rotation_advisor_no_subprocess_or_network_imports(self):
        """Assert rotation_advisor contains no subprocess, socket, urllib, or http imports."""
        advisor_path = Path(__file__).resolve().parents[1] / "src" / "agent_os" / "orchestrator" / "rotation_advisor.py"
        content = advisor_path.read_text(encoding="utf-8")

        forbidden_modules = ["subprocess", "socket", "urllib", "http"]

        for module in forbidden_modules:
            # Look for direct imports or from imports
            if re.search(rf'import\s+{module}|from\s+{module}|import\s+.*\b{module}\b', content):
                self.fail(f"rotation_advisor imports forbidden module: {module}")

    def test_report_snapshot_unchanged_without_out_param(self):
        """Build a synthetic temp home, snapshot names/sizes/mtimes, call rotation_advisor.report(home)
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
            initial_snapshot = self._snapshot_directory(home)

            # Call rotation_advisor.report(home) without out parameter
            result = rotation_advisor.report(home)

            # Verify result is a dict
            self.assertIsInstance(result, dict)

            # Snapshot after and verify it's unchanged
            final_snapshot = self._snapshot_directory(home)

            self.assertEqual(initial_snapshot, final_snapshot,
                           "File snapshot should be unchanged after report(home) without out parameter")

    def test_report_never_opens_worker_files(self):
        """Patch builtins.open to assert that no file under workers/ is opened."""
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            runs_dir = home / "runs"
            runs_dir.mkdir(parents=True)

            # Create a synthetic run with worker files
            run_dir = runs_dir / "run-20261001T000000Z-aaaaaa"
            run_dir.mkdir(parents=True)

            # Create telemetry with a model_completed event
            telemetry_file = run_dir / "telemetry.jsonl"
            telemetry_file.write_text(
                '{"schema": "personal-agent/orchestrator-run-telemetry/v1", "at": "2026-10-01T00:00:00+00:00", '
                '"seq": 1, "run_id": "run-20261001T000000Z-aaaaaa", "type": "run_started", "data": {}}\n'
                '{"schema": "personal-agent/orchestrator-run-telemetry/v1", "at": "2026-10-01T00:00:00+00:00", '
                '"seq": 2, "run_id": "run-20261001T000000Z-aaaaaa", "type": "model_completed", "node": "worker-1", '
                '"data": {"role": "implementer", "capability_class": "standard", "provider": "claude-code", "model": "sonnet", '
                '"attempt": 1, "prompt_tokens_estimate": 100, "usage": {"input_tokens": 200, "uncached_input_tokens": 200, '
                '"cache_read_tokens": 0, "cache_write_tokens": 0, "output_tokens": 50, "cost_usd": null, "accuracy": "exact", '
                '"source": "claude-code"}}}\n',
                encoding="utf-8"
            )

            # Create worker files with sentinel content
            worker_dir = run_dir / "workers" / "worker-1-1"
            worker_dir.mkdir(parents=True)
            (worker_dir / "prompt.md").write_bytes(b"SENTINEL-PHRASE secret words!!")
            (worker_dir / "stdout.log").write_bytes(b"1234567")

            real_open = builtins.open
            real_read_text = Path.read_text

            def guard(real):
                def wrapper(target, *args, **kwargs):
                    target_str = str(target)
                    if "workers" in target_str:
                        raise AssertionError(f"worker file was opened: {target_str}")
                    return real(target, *args, **kwargs)
                return wrapper

            with mock.patch("builtins.open", guard(real_open)), \
                 mock.patch.object(Path, "read_text", lambda self, *a, **k: guard(real_read_text)(self, *a, **k)):
                result = rotation_advisor.report(home)

            # Verify that sentinel was not leaked
            result_text = json.dumps(result)
            self.assertNotIn("SENTINEL", result_text)

    def test_report_dispatch_changed_is_false(self):
        """Assert that report['dispatch_changed'] is False."""
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

            result = rotation_advisor.report(home)

            self.assertIn("dispatch_changed", result)
            self.assertIs(result["dispatch_changed"], False)

    def test_report_mode_is_shadow(self):
        """Assert that report['mode'] == 'shadow'."""
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

            result = rotation_advisor.report(home)

            self.assertIn("mode", result)
            self.assertEqual(result["mode"], "shadow")

    @staticmethod
    def _snapshot_directory(path: Path) -> dict:
        """Create a snapshot of all files under a directory: name, size, mtime."""
        snapshot = {}
        for root, dirs, files in os.walk(path):
            for file in files:
                filepath = Path(root) / file
                relative = filepath.relative_to(path)
                stat = filepath.stat()
                snapshot[str(relative)] = {
                    "size": stat.st_size,
                    "mtime": stat.st_mtime,
                }
        return snapshot


if __name__ == "__main__":
    unittest.main()
