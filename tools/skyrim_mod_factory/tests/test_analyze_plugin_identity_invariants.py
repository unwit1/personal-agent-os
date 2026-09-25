import importlib.util
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location(
    "analyze_plugin_identity_invariants",
    ROOT/"analyze_plugin_identity_invariants.py",
)
MOD=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)

def doc(records):
    return {
        "schema_version":"skyrim-semantic-plugin-v1",
        "plugin":{"mod_key":"Fixture.esp","game_release":"skyrim-se-ae"},
        "records":records,
        "provenance":{
            "producer":"fixture",
            "producer_version":"1",
            "form_key_mode":"mutagen-formkey-string",
            "canonical_cross_load_order_form_keys":True,
        },
    }

def rec(form_key,signature="MISC"):
    return {"form_key":form_key,"signature":signature}

class PluginIdentityInvariantTests(unittest.TestCase):
    def analyze(self,records,**kwargs):
        defaults=dict(
            masters=[],
            light_plugin=True,
            header_version=1.71,
            target_runtime="1.6.1170",
            bees_present=False,
        )
        defaults.update(kwargs)
        return MOD.analyze(doc(records),**defaults)

    def test_extended_esl_low_id_passes_on_new_runtime(self):
        report=self.analyze([rec("000001:Fixture.esp")])
        self.assertEqual(report["status"],"pass")

    def test_classic_esl_low_id_fails_on_old_runtime(self):
        report=self.analyze(
            [rec("000001:Fixture.esp")],
            target_runtime="1.5.97",
            header_version=1.70,
        )
        self.assertEqual(report["status"],"fail")
        self.assertEqual(
            report["findings"][0]["rule_id"],
            "SKYRIM-PLUGIN-INVALID-ESL-RANGE",
        )

    def test_bees_allows_extended_range_on_old_runtime(self):
        report=self.analyze(
            [rec("000001:Fixture.esp")],
            target_runtime="1.5.97",
            header_version=1.71,
            bees_present=True,
        )
        self.assertEqual(report["status"],"pass")
        self.assertTrue(report["scope"]["extended_esl_supported"])

    def test_extended_low_id_requires_171_header(self):
        report=self.analyze(
            [rec("000100:Fixture.esp")],
            target_runtime="1.6.1170",
            header_version=1.70,
        )
        self.assertEqual(report["status"],"fail")
        self.assertTrue(any(
            "1.71-compatible" in x["message"] for x in report["findings"]
        ))

    def test_light_id_over_fff_fails(self):
        report=self.analyze([rec("001000:Fixture.esp")])
        self.assertEqual(report["status"],"fail")
        self.assertTrue(any(
            "exceeds 0xFFF" in x["message"] for x in report["findings"]
        ))

    def test_override_origin_must_be_declared_master(self):
        report=self.analyze([rec("012EB7:Skyrim.esm")])
        self.assertEqual(report["status"],"fail")
        self.assertEqual(
            report["findings"][0]["rule_id"],
            "SKYRIM-PLUGIN-MISSING-MASTER",
        )

    def test_declared_master_override_passes(self):
        report=self.analyze(
            [rec("012EB7:Skyrim.esm")],
            masters=["Skyrim.esm"],
        )
        self.assertEqual(report["status"],"pass")

    def test_regular_low_new_id_requires_review(self):
        report=self.analyze(
            [rec("000100:Fixture.esp")],
            light_plugin=False,
            header_version=1.71,
        )
        self.assertEqual(report["status"],"needs-review")
        self.assertEqual(
            report["findings"][0]["rule_id"],
            "SKYRIM-PLUGIN-LOW-REGULAR-FORMID",
        )

if __name__=="__main__":
    unittest.main()
