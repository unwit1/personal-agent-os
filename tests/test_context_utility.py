"""MIE-0009: context-utility telemetry for delegate attachments."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from agent_os.orchestrator import context_utility as cu  # noqa: E402


class UtilityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.d = Path(self.tmp.name)
        (self.d / "alpha.md").write_text("The alpha module relies on quantumflux calibration daily.", encoding="utf-8")
        (self.d / "beta.md").write_text("The beta module uses ordinary common shared widgets.", encoding="utf-8")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_distinctive_token_reference(self) -> None:
        result = cu.attachment_utility("I applied quantumflux from the note.", ["alpha.md", "beta.md"], self.d)
        self.assertEqual((result["referenced"], result["unreferenced"]), (1, ["beta.md"]))

    def test_stem_reference_at_word_boundary(self) -> None:
        result = cu.attachment_utility("See file beta.md for details.", ["alpha.md", "beta.md"], self.d)
        self.assertNotIn("beta.md", result["unreferenced"])

    def test_shared_common_words_do_not_credit(self) -> None:
        result = cu.attachment_utility("Something about a module that uses things.", ["alpha.md", "beta.md"], self.d)
        self.assertEqual((result["referenced"], result["utilization"]), (0, 0.0))

    def test_missing_files_and_token_estimate(self) -> None:
        empty = cu.attachment_utility("x", ["nope.md"], self.d)
        self.assertEqual((empty["attachments"], empty["utilization"]), (0, None))
        full = cu.attachment_utility("quantumflux", ["alpha.md", "beta.md"], self.d)
        self.assertGreater(full["attached_tokens_est"], 0)

    def test_report_aggregates_and_flags_always_unreferenced(self) -> None:
        home = self.d / "home"
        for i in range(2):
            call = home / "delegations" / f"DLG-{i}"
            call.mkdir(parents=True)
            (call / "outcome.json").write_text(json.dumps({
                "attachments": ["alpha.md", "beta.md"],
                "context_utility": {"attachments": 2, "referenced": 1, "utilization": 0.5, "attached_tokens_est": 20, "unreferenced": ["beta.md"]},
            }), encoding="utf-8")
        report = cu.report(home)
        self.assertEqual((report["delegations_with_attachments"], report["mean_utilization"]), (2, 0.5))
        self.assertEqual([t["attachment"] for t in report["always_unreferenced"]], ["beta.md"])


if __name__ == "__main__":
    unittest.main()
