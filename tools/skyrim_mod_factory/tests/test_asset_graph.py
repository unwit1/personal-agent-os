import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location("assets",ROOT/"validate_asset_graph.py")
MOD=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(MOD)

class AssetTests(unittest.TestCase):
    def test_norm(self):
        self.assertEqual(MOD.norm(r"\\Meshes\\Actors\\X.NIF"),"meshes/actors/x.nif")
    def test_inventory_case(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); p=root/"Meshes"/"X.nif"; p.parent.mkdir(); p.write_text("x")
            exact,folded=MOD.inventory([root])
            self.assertIn("Meshes/X.nif",exact)
            self.assertIn("meshes/x.nif",folded)

if __name__=="__main__":
    unittest.main()
