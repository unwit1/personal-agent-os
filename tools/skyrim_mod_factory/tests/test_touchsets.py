import importlib.util
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location("touch",ROOT/"compare_touchsets.py")
MOD=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(MOD)

class TouchTests(unittest.TestCase):
    def test_exact(self):
        self.assertEqual(MOD.fields_overlap(["ACBS.Flags"],["ACBS.Flags"]),["ACBS.Flags"])
    def test_prefix(self):
        x=MOD.fields_overlap(["ACBS"],["ACBS.Flags"])
        self.assertTrue(x)
    def test_unspecified_is_whole_record(self):
        self.assertEqual(MOD.fields_overlap([],["FULL"]),["<whole-or-unspecified-record>"])

if __name__=="__main__":
    unittest.main()
