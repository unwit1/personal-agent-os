"""A failed validation hands the retried worker the error lines, not just test names.

Measured 2026-10-16 (run hr-cc-run4): $6.58 of $15.15 went to frontier retries
after validator failures whose prompt carried only failing test names. The
validator kept the last five output lines, which for unittest is only the
summary ("Ran 15 tests", "FAILED (failures=2)").
"""

from __future__ import annotations

import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.orchestrator.engine import _prior_attempts  # noqa: E402
from agent_os.orchestrator.validators import EXCERPT_LIMIT, failure_excerpt, run_validator  # noqa: E402

PYTEST_OUTPUT = """\
============================= test session starts ==============================
collected 15 items

tests/test_orchestrator_api_retry.py ..F............                     [100%]

=================================== FAILURES ===================================
____________________ RetryHelperTests.test_full_jitter_is_bounded ____________________

self = <tests.test_orchestrator_api_retry.RetryHelperTests testMethod=test_full_jitter_is_bounded>

    def test_full_jitter_is_bounded(self) -> None:
        self.assertEqual(retry.full_jitter(10, base=1, cap=30, rng=lambda: 1.0), 30)
>       self.assertEqual(retry.full_jitter(2, base=1, cap=30, rng=lambda: 0.5), 2.0)
E       AssertionError: 4.5 != 2.0

tests/test_orchestrator_api_retry.py:42: AssertionError
=========================== short test summary info ============================
FAILED tests/test_orchestrator_api_retry.py::RetryHelperTests::test_full_jitter_is_bounded - AssertionError: 4.5 != 2.0
========================= 1 failed, 14 passed in 0.41s =========================
"""

UNITTEST_OUTPUT = """\
..F...E
======================================================================
ERROR: test_parse (tests.test_retry.RetryTests.test_parse)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/wt/src/retry.py", line 12, in parse
    return float(value) / 0
           ~~~~~~~~~~~~~^~~
ZeroDivisionError: float division by zero

======================================================================
FAIL: test_jitter (tests.test_retry.RetryTests.test_jitter)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/wt/tests/test_retry.py", line 9, in test_jitter
    self.assertEqual(jitter(2), 2.0)
AssertionError: 4.5 != 2.0

----------------------------------------------------------------------
Ran 7 tests in 0.004s

FAILED (failures=1, errors=1)
"""

COLLECTION_ERROR = """\
==================================== ERRORS ====================================
____________ ERROR collecting tests/test_orchestrator_api_retry.py _____________
E     File "/wt/src/agent_os/orchestrator/retry.py", line 63
E       def full_jitter((attempt: int) -> float:
E                       ^
E   SyntaxError: invalid syntax
=========================== short test summary info ============================
ERROR tests/test_orchestrator_api_retry.py
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
"""


class FailureExcerptTests(unittest.TestCase):
    def test_pytest_assertion_keeps_the_assertion_and_test_id(self) -> None:
        excerpt = failure_excerpt(PYTEST_OUTPUT)
        self.assertIn("E       AssertionError: 4.5 != 2.0", excerpt)
        self.assertIn("FAILED tests/test_orchestrator_api_retry.py::RetryHelperTests::test_full_jitter_is_bounded", excerpt)
        self.assertNotIn("collected 15 items", excerpt)
        self.assertLess(len(excerpt), len(PYTEST_OUTPUT) / 2)

    def test_unittest_keeps_both_exception_lines_which_the_tail_lost(self) -> None:
        excerpt = failure_excerpt(UNITTEST_OUTPUT)
        self.assertIn("ZeroDivisionError: float division by zero", excerpt)
        self.assertIn("AssertionError: 4.5 != 2.0", excerpt)
        self.assertIn("FAIL: test_jitter (tests.test_retry.RetryTests.test_jitter)", excerpt)
        tail = " | ".join(UNITTEST_OUTPUT.strip().splitlines()[-3:])
        self.assertNotIn("Error", tail)  # what the worker saw before this change

    def test_collection_error_keeps_the_syntax_error(self) -> None:
        self.assertIn("SyntaxError: invalid syntax", failure_excerpt(COLLECTION_ERROR))

    def test_excerpt_is_capped_on_whole_lines_and_deduplicated(self) -> None:
        many = "\n".join(f"FAILED tests/test_x.py::T::test_{index} - AssertionError: boom" for index in range(200))
        excerpt = failure_excerpt(many + "\n" + many)
        self.assertLessEqual(len(excerpt), EXCERPT_LIMIT)
        self.assertTrue(excerpt.endswith("boom"))
        self.assertEqual(len(excerpt.splitlines()), len(set(excerpt.splitlines())))

    def test_passing_or_unparseable_output_gives_nothing(self) -> None:
        self.assertEqual(failure_excerpt("Ran 3 tests in 0.1s\n\nOK\n"), "")
        self.assertEqual(failure_excerpt("make: *** [all] Stopped"), "")


class RunValidatorExcerptTests(unittest.TestCase):
    def test_a_failing_unittest_validator_records_the_excerpt(self) -> None:
        with tempfile.TemporaryDirectory() as root:
            tests = Path(root) / "tests"
            tests.mkdir()
            (tests / "__init__.py").write_text("", encoding="utf-8")
            (tests / "test_sample.py").write_text(textwrap.dedent("""\
                import unittest

                class SampleTests(unittest.TestCase):
                    def test_math(self):
                        self.assertEqual(2 + 2, 5)
                """), encoding="utf-8")
            result = run_validator({"kind": "command", "name": "unit", "command": [sys.executable, "-m", "unittest", "discover", "-s", "tests"]}, root, 120)
        self.assertFalse(result["passed"])
        self.assertIn("AssertionError: 4 != 5", result["excerpt"])
        self.assertNotIn("AssertionError", result["detail"] or "")

    def test_a_passing_validator_records_no_excerpt(self) -> None:
        with tempfile.TemporaryDirectory() as root:
            result = run_validator({"kind": "command", "name": "ok", "command": [sys.executable, "-c", "print('fine')"]}, root, 60)
        self.assertTrue(result["passed"])
        self.assertNotIn("excerpt", result)


class RetryPromptExcerptTests(unittest.TestCase):
    def node(self, *excerpts: str | None) -> dict:
        failures = []
        for excerpt in excerpts:
            failure = {"kind": "validator_failed", "detail": "unit=FAIL (FAILED (failures=1))"}
            if excerpt is not None:
                failure["excerpt"] = excerpt
            failures.append(failure)
        return {"role": "implementer", "failures": failures, "decisions": [], "review": {"findings": []}}

    def test_retry_prompt_quotes_the_failing_output(self) -> None:
        text = _prior_attempts(self.node("FAIL: test_jitter (t.T.test_jitter)\nAssertionError: 4.5 != 2.0"))
        self.assertIn("failing validator output:", text)
        self.assertIn("    AssertionError: 4.5 != 2.0", text)
        self.assertIn("fix the failure shown above", text)
        self.assertNotIn("run that test to see why", text)
        self.assertNotIn("same failing output", text)

    def test_an_unchanged_failure_is_called_out(self) -> None:
        text = _prior_attempts(self.node("AssertionError: 4.5 != 2.0", "AssertionError: 4.5 != 2.0"))
        self.assertIn("same failing output as the previous attempt", text)
        self.assertNotIn("same failing output", _prior_attempts(self.node("AssertionError: 9 != 2.0", "AssertionError: 4.5 != 2.0")))

    def test_without_an_excerpt_the_old_instruction_stays(self) -> None:
        text = _prior_attempts(self.node(None))
        self.assertIn("run that test to see why", text)
        self.assertIn("Do not report already_done", text)


if __name__ == "__main__":
    unittest.main()
