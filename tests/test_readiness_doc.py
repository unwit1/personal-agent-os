"""Check that the Stage 2 checkpoint includes all fixture evidence."""

from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "orchestrator-os" / "readiness.md"
EVIDENCE = DOC.parent / "readiness"
AREAS = ("worktree", "privacy", "validators", "unregistered", "cost", "review", "dirty-large")
ITEM = re.compile(r"\b(?:WT|PR|VD|NR|CC|RG|DL)-\d+\b")


class ReadinessDocumentTests(unittest.TestCase):
    def test_checkpoint_links_all_evidence_and_results(self) -> None:
        self.assertTrue(DOC.is_file(), str(DOC))
        text = DOC.read_text(encoding="utf-8")
        self.assertIn("**Stage 3 prompt:**", text)
        checklist = text.split("## Readiness checklist", 1)
        self.assertEqual(len(checklist), 2, "Missing Readiness checklist section")
        checklist_section = checklist[1].split("\n## ", 1)[0]
        checklist_rows = [line for line in checklist_section.splitlines() if line.startswith("|")]
        self.assertTrue(checklist_rows, "Missing Readiness checklist table")
        self.assertEqual(checklist_rows[0].split("|")[1].strip(), "item")
        checklist_items = {
            item
            for line in checklist_rows[2:]
            if (item := line.split("|")[1].strip()) and ITEM.fullmatch(item)
        }
        for area in AREAS:
            with self.subTest(area=area):
                path = EVIDENCE / f"{area}.md"
                self.assertTrue(path.is_file(), str(path))
                self.assertIn(f"(readiness/{area}.md)", text)
                evidence = path.read_text(encoding="utf-8")
                results = evidence.split("## Results", 1)
                self.assertEqual(len(results), 2, f"Missing Results table: {path}")
                section = results[1].split("\n## ", 1)[0]
                rows = [line for line in section.splitlines() if line.startswith("|")]
                for row in rows[2:]:
                    item_cell = row.split("|")[1].strip()
                    match = ITEM.match(item_cell)
                    if match:
                        item = match.group()
                        self.assertIn(item, checklist_items, f"Missing checklist row for {item} from {path}")


if __name__ == "__main__":
    unittest.main()
