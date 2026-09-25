import importlib.util
import copy
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location(
    "analyze_ctda_invariants",
    ROOT/"analyze_ctda_invariants.py",
)
MOD=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)

def predicate(**changes):
    value={
        "type_byte":0x00,
        "comparison":{"kind":"literal","value":1.0},
        "function":1,
        "parameter_1":None,
        "parameter_2":None,
        "run_on":0,
        "reference":None,
        "parameter_3":None,
    }
    value.update(changes)
    return value

def packet(predicates,intentional=False):
    return {
        "schema_version":"skyrim-ctda-predicate-set-v1",
        "record":"QUST:000001:Fixture.esp",
        "predicates":predicates,
        "intentional_rewrite":intentional,
    }

class CTDAInvariantTests(unittest.TestCase):
    def test_identical_full_predicate_sequence_passes(self):
        source=packet([predicate(),predicate(type_byte=0x21,function=14)])
        output=copy.deepcopy(source)
        report=MOD.analyze(source,output)
        self.assertEqual(report["status"],"pass")

    def test_lost_or_flag_fails(self):
        source=packet([predicate(type_byte=0x01)])
        output=packet([predicate(type_byte=0x00)])
        report=MOD.analyze(source,output)
        self.assertEqual(report["status"],"fail")
        self.assertTrue(any(
            "does not exactly preserve" in x["message"]
            for x in report["findings"]
        ))

    def test_changed_run_on_fails(self):
        source=packet([predicate(run_on=0)])
        output=packet([predicate(run_on=1)])
        self.assertEqual(MOD.analyze(source,output)["status"],"fail")

    def test_reordered_predicates_fail(self):
        a=predicate(function=1)
        b=predicate(function=14)
        source=packet([a,b])
        output=packet([b,a])
        report=MOD.analyze(source,output)
        self.assertEqual(report["status"],"fail")
        self.assertEqual(
            report["findings"][-1]["evidence"]["first_mismatch_index"],
            0,
        )

    def test_alias_and_packdata_flags_are_mutually_exclusive(self):
        bad=predicate(type_byte=0x0A)
        report=MOD.analyze(packet([bad]),packet([bad]))
        self.assertEqual(report["status"],"fail")
        self.assertTrue(any(
            "Use aliases and Use packdata" in x["message"]
            for x in report["findings"]
        ))

    def test_global_flag_must_match_comparison_kind(self):
        bad=predicate(
            type_byte=0x04,
            comparison={"kind":"literal","value":1.0},
        )
        report=MOD.analyze(packet([bad]),packet([bad]))
        self.assertEqual(report["status"],"fail")
        self.assertTrue(any(
            "Use global flag" in x["message"]
            for x in report["findings"]
        ))

    def test_run_on_reference_requires_reference(self):
        bad=predicate(run_on=2,reference=None)
        report=MOD.analyze(packet([bad]),packet([bad]))
        self.assertEqual(report["status"],"fail")
        self.assertTrue(any(
            "requires an explicit CTDA reference" in x["message"]
            for x in report["findings"]
        ))

    def test_intentional_rewrite_requires_review_not_false_pass(self):
        source=packet([predicate(function=1)])
        output=packet([predicate(function=14)],intentional=True)
        report=MOD.analyze(source,output)
        self.assertEqual(report["status"],"needs-review")
        self.assertTrue(report["issues"])

if __name__=="__main__":
    unittest.main()
