import importlib.util
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location(
    "normalize_xdump_semantic",
    ROOT/"normalize_xdump_semantic.py",
)
MOD=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)

class NormalizeXDumpSemanticTests(unittest.TestCase):
    def test_normalizes_record_identity_fields_vmad_and_assets(self):
        doc=MOD.parse_xdump(
            """Iron Armor [ARMO:01001234]
  EDID - Editor ID: ArmorIron
  Model
    MODL - Model Filename: Armor\\Iron\\IronArmor.nif
  VMAD - Virtual Machine Adapter
    Script
      scriptName: ExampleScript
Second Record [MISC:01005678]
  EDID - Editor ID: ExampleMisc
  DATA - Data
    Value: 25
""",
            plugin="Fixture.esp",
            created_at="2026-09-24T00:00:00+00:00",
        )
        self.assertEqual(doc["schema_version"],"skyrim-semantic-plugin-v1")
        self.assertEqual(doc["plugin"]["mod_key"],"Fixture.esp")
        self.assertEqual(len(doc["records"]),2)

        armo=doc["records"][0]
        self.assertEqual(armo["signature"],"ARMO")
        self.assertEqual(armo["form_key"],"Fixture.esp|01001234")
        self.assertEqual(armo["editor_id"],"ArmorIron")
        self.assertIn("Armor\\Iron\\IronArmor.nif",armo["asset_paths"])
        self.assertIn("vmad",armo)
        self.assertTrue(armo["vmad"]["xdump_lines"])
        self.assertEqual(MOD.schema_errors(doc),[])

    def test_preserves_ordered_field_evidence(self):
        doc=MOD.parse_xdump(
            """Quest [QUST:01000001]
  EDID - Editor ID: QuestFixture
  Conditions
    CTDA - Condition: first
    CTDA - Condition: second
""",
            plugin="Fixture.esp",
            created_at="2026-09-24T00:00:00+00:00",
        )
        rows=doc["records"][0]["fields"]["_xdump"]["ordered_fields"]
        self.assertEqual(
            [r["value"] for r in rows if r["name"].startswith("CTDA")],
            ["first","second"],
        )

    def test_provenance_declares_noncanonical_formkey_scope(self):
        doc=MOD.parse_xdump(
            "Record [STAT:FE001234]\n  EDID - Editor ID: Fixture",
            plugin="Fixture.esp",
            created_at="2026-09-24T00:00:00+00:00",
        )
        prov=doc["provenance"]
        self.assertFalse(prov["canonical_cross_load_order_form_keys"])
        self.assertEqual(
            prov["form_key_mode"],
            "target-plugin-plus-load-order-formid",
        )
        self.assertTrue(prov["coverage"]["omissions"])

    def test_rejects_text_without_record_headers(self):
        with self.assertRaises(ValueError):
            MOD.parse_xdump(
                "not an xDump record tree",
                plugin="Fixture.esp",
            )

if __name__=="__main__":
    unittest.main()
