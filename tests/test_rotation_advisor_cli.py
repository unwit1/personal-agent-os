import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import contextlib
import io
import json
import tempfile
import unittest

from agent_os.cli import main
from agent_os.orchestrator.ledger import SCHEMA as TELEMETRY_SCHEMA

RUN_ID = "run-20261001T000000Z-aaaaaa"


def usage(input_tokens, output=0, cache_read=0, accuracy="exact", source="claude-code"):
    return {
        "accuracy": accuracy,
        "source": source,
        "input_tokens": input_tokens,
        "uncached_input_tokens": input_tokens - cache_read,
        "cache_read_tokens": cache_read,
        "cache_write_tokens": 0,
        "output_tokens": output,
        "cost_usd": None,
    }


class Run:
    """Writes a synthetic runs/<id>/telemetry.jsonl in the ledger format."""

    def __init__(self, runs_dir: Path, run_id: str):
        self.dir = runs_dir / run_id
        self.dir.mkdir(parents=True)
        self.run_id = run_id
        self.lines: list[str] = []
        self.seq = 0

    def event(self, kind, node=None, seq=None, **data):
        self.seq = seq if seq is not None else self.seq + 1
        self.lines.append(
            json.dumps({
                "schema": TELEMETRY_SCHEMA,
                "at": "2026-10-01T00:00:00+00:00",
                "seq": self.seq,
                "run_id": self.run_id,
                "type": kind,
                "node": node,
                "data": data,
            })
        )
        return self

    def call(self, node, role, input_tokens, prompt, output=0, cache_read=0, attempt=1, cls="standard", kind="model_completed", seq=None, **usage_kwargs):
        return self.event(
            kind,
            node,
            seq=seq,
            role=role,
            capability_class=cls,
            provider="claude-code",
            model="sonnet",
            attempt=attempt,
            prompt_chars=prompt * 4,
            prompt_tokens_estimate=prompt,
            usage=usage(input_tokens, output, cache_read, **usage_kwargs),
        )

    def write(self):
        (self.dir / "telemetry.jsonl").write_text("\n".join(self.lines) + "\n", encoding="utf-8")
        return self.dir


class RotationAdvisorCLITests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.home = Path(self._tmp.name)
        self.runs = self.home / "runs"
        self.runs.mkdir()

    def test_rotation_advisor_cli_with_synthetic_fixture(self):
        """Test rotation-advisor CLI command with a one-run synthetic telemetry fixture."""
        run = Run(self.runs, RUN_ID).event("run_started")
        run.call("a", "implementer", 2000, 1000, output=200, cache_read=500)
        run.call("b", "implementer", 3000, 1000, output=600)
        run.call("c", "reviewer", 900, 300, output=90, cls="fast")
        run.write()

        out_file = self.home / "result.json"

        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            rc = main(["orchestrate", "rotation-advisor", "--home", str(self.home), "--out", str(out_file)])

        self.assertEqual(rc, 0, f"Exit code was {rc}")
        self.assertTrue(out_file.exists(), f"Output file not created at {out_file}")

        output_data = json.loads(out_file.read_text(encoding="utf-8"))

        self.assertIn("schema", output_data)
        self.assertEqual(output_data["schema"], "personal-agent/orchestrator-rotation-advice/v1")

        self.assertIn("mode", output_data)
        self.assertEqual(output_data["mode"], "shadow")

        self.assertIn("coverage", output_data)
        self.assertEqual(output_data["coverage"]["runs"], 1, f"Expected runs == 1, got {output_data['coverage']['runs']}")


if __name__ == "__main__":
    unittest.main()
