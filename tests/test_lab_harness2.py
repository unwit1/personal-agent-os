"""The Harness2 lab runs Propose-Probe-Compose through our adapter with no model.

Skips unless harness2 (Python 3.12+) is importable; it is an optional extra.
"""

from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from orchestrator_os import lab_harness2  # noqa: E402


class ScorerTests(unittest.TestCase):
    def test_recall_and_tokens(self) -> None:
        result = lab_harness2.score_packet("- a\n- b\n", ["a", "c"])
        self.assertEqual((result["recall"], result["missing"]), (0.5, ["c"]))
        self.assertGreater(result["tokens"], 0)

    def test_variants_are_valid_python(self) -> None:
        for name, script in lab_harness2._variants().items():
            compile(script, name, "exec")


@unittest.skipUnless(importlib.util.find_spec("harness2") is not None, "optional extra: pip install orchestrator-os[harness2] (Python 3.12+)")
class LabRunTests(unittest.TestCase):
    def test_pipeline_completes_without_model_calls(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = lab_harness2.run(Path(tmp) / "lab", k=1)
        self.assertEqual(report["model_calls"], 0)
        self.assertEqual(report["harness2"]["failed"], 0)
        self.assertGreater(report["harness2"]["executions"], 0)
        composed = report["summary"]["harness2_composed"]["holdout"]
        existing = report["summary"]["existing"]["holdout"]
        self.assertGreaterEqual(composed["recall"], existing["recall"])


if __name__ == "__main__":
    unittest.main()
