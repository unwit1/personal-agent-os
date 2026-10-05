import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


class ContextBenchCLITests(unittest.TestCase):
    def _run(self, *args):
        env = os.environ.copy()
        env["PYTHONPATH"] = "src"
        return subprocess.run(
            ["python", "-m", "agent_os", "orchestrate", "context-bench", *map(str, args)],
            env=env,
            capture_output=True,
            text=True,
        )

    def test_context_bench_cli_writes_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            out_file = Path(tmp) / "r.json"
            env = os.environ.copy()
            env["PYTHONPATH"] = "src"

            result = subprocess.run(
                ["python", "-m", "agent_os", "orchestrate", "context-bench", "--out", str(out_file)],
                env=env,
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 0, f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}")
            output_data = json.loads(out_file.read_text(encoding="utf-8"))
            self.assertEqual(output_data["schema"], "personal-agent/orchestrator-context-bench/v1")
            self.assertEqual(output_data["model_calls"], 0)

    def test_baseline_comparison_passes_without_regression(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / "base.json"
            cur = Path(tmp) / "cur.json"
            first = self._run("--out", base)
            self.assertEqual(first.returncode, 0, f"stdout:\n{first.stdout}\nstderr:\n{first.stderr}")

            result = self._run("--baseline", base, "--fail-on-regression", "--out", cur)
            self.assertEqual(result.returncode, 0, f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}")
            comparison = json.loads(cur.read_text(encoding="utf-8"))["comparison"]
            self.assertFalse(comparison["regressed"])
            self.assertEqual(comparison["schema"], "personal-agent/orchestrator-context-bench-compare/v1")

    def test_baseline_regression_can_fail_command(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / "base.json"
            cur = Path(tmp) / "cur.json"
            first = self._run("--out", base)
            self.assertEqual(first.returncode, 0, f"stdout:\n{first.stdout}\nstderr:\n{first.stderr}")
            baseline = json.loads(base.read_text(encoding="utf-8"))
            baseline["prompts"]["totals"]["total_tokens"] -= 100
            base.write_text(json.dumps(baseline), encoding="utf-8")

            result = self._run("--baseline", base, "--fail-on-regression", "--out", cur)
            self.assertEqual(result.returncode, 1, f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}")
            comparison = json.loads(cur.read_text(encoding="utf-8"))["comparison"]
            self.assertIn("prompts.totals.total_tokens", comparison["regressions"])

    def test_baseline_regression_without_flag_returns_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / "base.json"
            cur = Path(tmp) / "cur.json"
            first = self._run("--out", base)
            self.assertEqual(first.returncode, 0, f"stdout:\n{first.stdout}\nstderr:\n{first.stderr}")
            baseline = json.loads(base.read_text(encoding="utf-8"))
            baseline["prompts"]["totals"]["total_tokens"] -= 100
            base.write_text(json.dumps(baseline), encoding="utf-8")

            result = self._run("--baseline", base, "--out", cur)
            self.assertEqual(result.returncode, 0, f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}")
            comparison = json.loads(cur.read_text(encoding="utf-8"))["comparison"]
            self.assertTrue(comparison["regressed"])

    def test_scope_repo_flag_builds_scope_maps(self):
        with tempfile.TemporaryDirectory() as tmp:
            out_file = Path(tmp) / "r.json"
            scope_repo = Path(__file__).resolve().parents[1]

            result = self._run("--scope-repo", str(scope_repo), "--out", str(out_file))
            self.assertEqual(result.returncode, 0, f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}")

            output_data = json.loads(out_file.read_text(encoding="utf-8"))
            self.assertIsNotNone(output_data.get("scope_maps"))
            self.assertGreaterEqual(output_data["scope_maps"]["cases"], 1)

    def test_without_scope_repo_flag_scope_maps_null(self):
        with tempfile.TemporaryDirectory() as tmp:
            out_file = Path(tmp) / "r.json"

            result = self._run("--out", str(out_file))
            self.assertEqual(result.returncode, 0, f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}")

            output_data = json.loads(out_file.read_text(encoding="utf-8"))
            self.assertIsNone(output_data.get("scope_maps"))


if __name__ == "__main__":
    unittest.main()
