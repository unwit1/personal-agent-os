import json
import tempfile
import unittest
from pathlib import Path
import importlib.util

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location("render_spid",ROOT/"render_spid.py")
MOD=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)

class SpidRendererTests(unittest.TestCase):
    def test_editor_id_simple(self):
        e={"kind":"Perk","form":{"editor_id":"MyPerk"}}
        self.assertEqual(MOD.render(e),"Perk = MyPerk")

    def test_positional_filter_preservation(self):
        e={"kind":"Item","form":{"editor_id":"SteelSword"},"form_filters":["BanditFaction"],"count_or_package_index":5}
        self.assertEqual(MOD.render(e),"Item = SteelSword||BanditFaction|||5")

    def test_formid_and_deterministic_chance(self):
        e={"kind":"Spell","form":{"form_id":"0x12345","plugin":"MyMod.esp"},"chance":{"percent":50,"deterministic":True}}
        self.assertEqual(MOD.render(e),"Spell = 0x12345~MyMod.esp||||||50!")

    def test_invalid_kind(self):
        with self.assertRaises(ValueError):
            MOD.render({"kind":"NotAType","form":{"editor_id":"X"}})

if __name__=="__main__":
    unittest.main()
