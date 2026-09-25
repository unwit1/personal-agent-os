import importlib.util
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location("cmp",ROOT/"compare_semantic_plugins.py")
MOD=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(MOD)

class SemanticDiffTests(unittest.TestCase):
    def test_scalar(self):
        out=[]
        MOD.diff_values({"x":1},{"x":2},"",out)
        self.assertEqual(out[0]["path"],"x")
        self.assertEqual(out[0]["kind"],"changed")

    def test_array_order_is_significant(self):
        out=[]
        MOD.diff_values([1,2],[2,1],"items",out)
        self.assertEqual(out[0]["kind"],"list-changed")

    def test_record_key(self):
        self.assertEqual(MOD.record_key({"signature":"NPC_","form_key":"A.esp|000123"}),"NPC_:A.esp|000123")

if __name__=="__main__":
    unittest.main()
