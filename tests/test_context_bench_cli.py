import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


class ContextBenchCLITests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
