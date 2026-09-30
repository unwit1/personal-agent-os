"""Pre-existing failures of non-test project validators are recognised by their error signature.

Live 2026-09-30: `agent.py validate` failed inside every run worktree with the same
pre-existing error ("job-applicant-dashboard: missing context file ..."). The baseline
excuse only understood failing *test names*, so every task failed validation, retried
and escalated (~5 min per validation) although no task broke anything.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.orchestrator.validators import error_signature  # noqa: E402

VALIDATE_OUTPUT = '{\n "ok": false,\n "errors": [\n  "job-applicant-dashboard: missing context file: docs/AGENT_OS_INTEGRATION.md"\n ],\n "checked": 711\n}'


class ErrorSignatureTests(unittest.TestCase):
    def test_json_errors_list_is_the_signature_and_ignores_counts_and_warnings(self) -> None:
        change = error_signature(VALIDATE_OUTPUT, "C:\\wt\\change\\src\\cli.py:88: SyntaxWarning: bad escape", "C:\\wt\\change")
        base = error_signature(VALIDATE_OUTPUT.replace("711", "723"), "", "C:\\wt\\base")
        self.assertEqual(change, ["error: job-applicant-dashboard: missing context file: docs/AGENT_OS_INTEGRATION.md"])
        self.assertEqual(change, base)

    def test_error_lines_are_normalized_for_worktree_paths_timings_and_addresses(self) -> None:
        change = error_signature("", 'Traceback (most recent call last):\n  File "C:\\wt\\one\\m.py", line 3\nValueError: boom at 0x1a2b after 3.2 s', "C:\\wt\\one")
        base = error_signature("", 'Traceback (most recent call last):\n  File "C:\\wt\\base\\m.py", line 3\nValueError: boom at 0x9f9f after 9.9 s', "C:\\wt\\base")
        self.assertEqual(change, base)
        self.assertTrue(any("ValueError: boom" in line for line in change))

    def test_a_new_error_is_not_hidden(self) -> None:
        base = error_signature(VALIDATE_OUTPUT, "", "C:\\wt\\base")
        change = error_signature(VALIDATE_OUTPUT.replace('"\n ],', '", "schemas/x.json: invalid"\n ],'), "", "C:\\wt\\change")
        self.assertTrue(set(change) - set(base))  # the engine reports it as broken by the change

    def test_nothing_error_like_means_no_signature(self) -> None:
        self.assertEqual(error_signature("all good\n", "", "."), [])


if __name__ == "__main__":
    unittest.main()
