import importlib.util
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location(
    "parse_xedit_check_errors",
    ROOT/"parse_xedit_check_errors.py",
)
MOD=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)

class ParseXEditCheckErrorsTests(unittest.TestCase):
    def test_clean_complete_session_passes(self):
        report=MOD.parse_text("""[00:00] Start: Checking for Errors
[00:00] Checking for Errors in [04] CleanPatch.esp
[00:00] Done: Checking for Errors, Processed Records: 3259, Errors found: 0, Elapsed Time: 00:00
""")
        self.assertEqual(report["status"],"pass")
        self.assertTrue(report["completion_detected"])
        self.assertEqual(report["processed_records"],3259)
        self.assertEqual(report["declared_errors"],0)
        self.assertEqual(report["target"],"CleanPatch.esp")
        self.assertEqual(report["findings"],[])

    def test_unresolved_reference_is_structured_failure(self):
        report=MOD.parse_text("""[00:00] Start: Checking for Errors
[00:00] Checking for Errors in [01] Broken.esp
[00:01] Example Record [ARMO:01121DD4]
[00:01] ARMO \\ Male world model \\ MOD2 -> [01100D6B] < Error: Could not be resolved >
[00:02] Done: Checking for Errors, Processed Records: 42, Errors found: 1, Elapsed Time: 00:02
""")
        self.assertEqual(report["status"],"fail")
        self.assertEqual(len(report["findings"]),1)
        finding=report["findings"][0]
        self.assertEqual(finding["category"],"unresolved-reference")
        self.assertEqual(finding["form_id"],"01121DD4")
        self.assertEqual(finding["signature"],"ARMO")
        self.assertEqual(finding["plugin"],"Broken.esp")

    def test_invalid_light_objectid_is_classified(self):
        report=MOD.parse_text("""[00:00] Start: Checking for Errors
[00:00] Checking for Errors in [FE 000] LightPatch.esp
[00:00] RedRoseWreathTexture [TXST:FE0002C9]
[00:00] TXST -> ObjectID 0012C9 is invalid for a light module.
[00:00] Done: Checking for Errors, Processed Records: 4, Errors found: 1, Elapsed Time: 00:00
""")
        self.assertEqual(report["status"],"fail")
        self.assertEqual(
            report["findings"][0]["category"],
            "invalid-light-objectid",
        )

    def test_incomplete_zero_error_session_never_passes(self):
        report=MOD.parse_text("""[00:00] Start: Checking for Errors
[00:00] Checking for Errors in [04] Interrupted.esp
""")
        self.assertEqual(report["status"],"needs-review")
        self.assertFalse(report["completion_detected"])
        self.assertTrue(any("completion summary" in x for x in report["issues"]))

    def test_declared_error_count_mismatch_is_preserved(self):
        report=MOD.parse_text("""[00:00] Start: Checking for Errors
[00:00] Checking for Errors in [04] Broken.esp
[00:00] Example [PACK:04000001]
[00:00] PACK \\ Data -> Target is not persistent
[00:01] Done: Checking for Errors, Processed Records: 10, Errors found: 2, Elapsed Time: 00:01
""")
        self.assertEqual(report["status"],"fail")
        self.assertTrue(any("declared 2 errors" in x for x in report["issues"]))

    def test_warning_with_zero_declared_errors_requires_review(self):
        report=MOD.parse_text("""[00:00] Start: Checking for Errors
[00:00] Checking for Errors in [04] WarningOnly.esp
[00:00] Example [QUST:04000001]
[00:00] QUST \\ Conditions -> <Warning: Quest Stage not found>
[00:01] Done: Checking for Errors, Processed Records: 10, Errors found: 0, Elapsed Time: 00:01
""")
        self.assertEqual(report["status"],"needs-review")
        self.assertEqual(report["findings"][0]["severity"],"warning")

    def test_most_recent_session_is_selected(self):
        report=MOD.parse_text("""[00:00] Start: Checking for Errors
[00:00] Checking for Errors in [01] OldBroken.esp
[00:00] Old [ARMO:01000001]
[00:00] ARMO -> < Error: Could not be resolved >
[00:01] Done: Checking for Errors, Processed Records: 5, Errors found: 1, Elapsed Time: 00:01
[00:02] Start: Checking for Errors
[00:02] Checking for Errors in [02] CurrentClean.esp
[00:03] Done: Checking for Errors, Processed Records: 6, Errors found: 0, Elapsed Time: 00:01
""")
        self.assertEqual(report["status"],"pass")
        self.assertEqual(report["target"],"CurrentClean.esp")
        self.assertEqual(report["declared_errors"],0)
        self.assertEqual(report["findings"],[])

if __name__=="__main__":
    unittest.main()
