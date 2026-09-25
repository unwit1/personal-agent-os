import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location("run_adapter",ROOT/"run_adapter.py")
MOD=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)

class AdapterRunnerTests(unittest.TestCase):
    def test_substitution(self):
        self.assertEqual(MOD.subst("{root}/Tool.exe",{"root":"C:/X"}),"C:/X/Tool.exe")

    def test_missing_substitution(self):
        with self.assertRaises(ValueError):
            MOD.subst("{root}/{missing}",{"root":"X"})

    def test_file_fact_missing(self):
        fact=MOD.file_fact("__definitely_missing_skyrim_factory_test__")
        self.assertFalse(fact["exists"])

if __name__=="__main__":
    unittest.main()
