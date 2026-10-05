"""Tests for explicit-scope repository maps."""

from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from test_orchestrator_planner_context import make_repo  # noqa: E402
from agent_os.orchestrator import repomap  # noqa: E402


class ScopeMapTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="agent-os-scope-map-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.repo = make_repo(self.tmp)

    def test_lists_scoped_file_and_named_companion(self) -> None:
        result = repomap.scope_map(self.repo, ["src/billing/invoice.py"])
        self.assertIn("render_invoice, InvoiceError", result["text"])
        self.assertIn("[tests: tests/test_invoice.py]", result["text"])
        self.assertIn("schemas/invoice-v1.schema.json", result["text"])

    def test_marks_new_file(self) -> None:
        result = repomap.scope_map(self.repo, ["src/billing/new_mod.py"])
        self.assertIn("(new file)", result["text"])
        self.assertEqual(result["stats"]["new_files"], 1)

    def test_empty_scope(self) -> None:
        result = repomap.scope_map(self.repo, [])
        self.assertEqual(result["text"], "")
        self.assertEqual(result["stats"], {"scope": 0, "listed": 0, "new_files": 0, "related": 0, "chars": 0})

    def test_truncates_at_line_boundary_within_limit(self) -> None:
        result = repomap.scope_map(self.repo, ["src/billing/invoice.py", "src/billing/tax.py"], max_chars=60)
        self.assertLessEqual(len(result["text"]), 60)


if __name__ == "__main__":
    unittest.main()
