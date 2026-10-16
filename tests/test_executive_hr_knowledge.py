from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os import mcp_server
from agent_os.executive import hr_knowledge

MARKER = "SECRET-MARKER-XYZZY"
PAY = "knowledge/libraries/hours-pay-benefits/pay.json"


def build(root: Path) -> None:
    lib = root / "knowledge" / "libraries" / "hours-pay-benefits"
    lib.mkdir(parents=True)
    (lib / "pay.json").write_text(json.dumps({"claims": [
        {"text": "Transit drivers earn overtime at 1.5x after 40 hours.", "source": "Handbook", "page": 12, "effective": "2025-01-01"},
        {"claim": "Overtime for drivers at 1.25x.", "citation": "Handbook p.9", "superseded_by": "pay.json#1"},
        {"statement": "Paid time off accrues monthly.", "citation": "Handbook p.20"},
    ]}))
    (lib / "omitted.json").write_text(json.dumps([{"text": f"overtime omitted {MARKER}", "omitted": True}]))
    (lib / "guide.md").write_text("# Holidays\nOffice closed on holidays.\n")
    (lib / "restricted-notes.md").write_text(f"# overtime\ndriver {MARKER}\n")
    for name in ("restricted-evidence", "private", "restricted"):
        directory = root / "knowledge" / name
        directory.mkdir(parents=True)
        (directory / "x.json").write_text(json.dumps([{"text": f"overtime driver {MARKER}", "source": "s"}]))
        (directory / "x.md").write_text(f"# overtime\ndriver {MARKER}\n")


class HrKnowledgeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        build(self.root)
        patcher = patch.dict(os.environ, {hr_knowledge.ENV_ROOT: str(self.root)})
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_overtime_for_drivers_with_citation_and_synonyms(self):
        for query in ("What's our policy on overtime for drivers?", "OT for driver"):
            results = hr_knowledge.search_claims(query)
            self.assertEqual(results[0]["source_path"], PAY)
            self.assertIn("1.5x", results[0]["text"])
            self.assertEqual(results[0]["citation"], "Handbook, page 12")
            self.assertEqual(results[0]["effective_date"], "2025-01-01")
        superseded = [r for r in results if r["superseded_by"]]
        self.assertEqual(superseded[0]["superseded_by"], "pay.json#1")

    def test_pto_synonym_and_markdown(self):
        self.assertIn("accrues", hr_knowledge.search_claims("PTO")[0]["text"])
        self.assertIn("holidays", hr_knowledge.search_claims("holidays")[0]["text"].casefold())

    def test_restricted_never_read(self):
        blob = json.dumps(hr_knowledge.search_claims("overtime driver", limit=50))
        self.assertNotIn(MARKER, blob)
        self.assertNotIn(MARKER, json.dumps(hr_knowledge.policy_lookup("overtime", 50)))

    def test_nothing_relevant_and_cache(self):
        self.assertEqual(hr_knowledge.search_claims("zebra"), [])
        first = hr_knowledge.load_index(self.root)
        self.assertIs(first, hr_knowledge.load_index(self.root))
        path = self.root / "knowledge/libraries/hours-pay-benefits/guide.md"
        path.write_text("# Zebra\nZebra rules.\n")
        os.utime(path, ns=(1, 1))
        self.assertTrue(hr_knowledge.search_claims("zebra"))

    def test_mcp_tool(self):
        self.assertIn("hr.policy_lookup", mcp_server.TOOL_SCHEMAS)
        result = mcp_server.methods()["hr.policy_lookup"](query="overtime drivers", limit=1)
        self.assertEqual(len(result["results"]), 1)
        self.assertTrue(result["answer_guidance"].startswith("Quote the claim"))


if __name__ == "__main__":
    unittest.main()
