import importlib.util
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def load(name):
    spec=importlib.util.spec_from_file_location(name,ROOT/f"{name}.py")
    m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

KID=load("render_kid"); BOS=load("render_bos")

class RuntimeRendererTests(unittest.TestCase):
    def test_kid(self):
        e={"kind":"KIDKeyword","keyword":{"editor_id":"MyKeyword"},"target_type":"Armor","filters":["ArmorHeavy","-ArmorShield"],"chance":75}
        self.assertEqual(KID.render(e),"Keyword = MyKeyword|Armor|ArmorHeavy,-ArmorShield||75")
    def test_bos_simple(self):
        e={"kind":"BOSFormSwap","base":[{"editor_id":"TreePine01"}],"swap":[{"form_id":"0x123","plugin":"Trees.esp"}]}
        self.assertEqual(BOS.section(e),"Forms")
        self.assertEqual(BOS.render_line(e),"TreePine01|0x123~Trees.esp")
    def test_bos_conditional(self):
        e={"kind":"BOSFormSwap","base":[{"editor_id":"A"}],"swap":[{"editor_id":"B"}],"conditions":["LocTypeCity","-Snow"]}
        self.assertEqual(BOS.section(e),"Forms|LocTypeCity,-Snow")

if __name__=="__main__": unittest.main()
