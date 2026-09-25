import importlib.util
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location("quorum",ROOT/"evaluate_validation_quorum.py")
MOD=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(MOD)


def check(name,family,fp="same",status="pass",discovered=10,processed=10,skipped=0,unclassified=0):
    return {
      "validator":name,
      "implementation_family":family,
      "status":status,
      "independent":True,
      "semantic_fingerprint":fp,
      "evidence":[],
      "coverage":{
        "discovered":discovered,
        "processed":processed,
        "skipped":skipped,
        "unclassified":unclassified,
        "skip_reasons":["known unsupported"] if skipped else []
      }
    }


def doc(checks, required="A", roundtrip=None, intent=None, runtime=None):
    return {
      "schema_version":"skyrim-validation-quorum-v1",
      "artifact":"Demo.esp",
      "artifact_type":"plugin",
      "required_level":required,
      "checks":checks,
      "round_trip":roundtrip or {"status":"not-run"},
      "intent_diff":intent or {"status":"not-run"},
      "runtime_assertion":runtime or {"status":"not-run"}
    }


class QuorumTests(unittest.TestCase):
    def test_one_parser_is_level_a(self):
        r=MOD.evaluate(doc([check("mutagen","mutagen")]))
        self.assertEqual(r["achieved_level"],"A")
        self.assertEqual(r["status"],"pass")

    def test_two_independent_families_are_level_b(self):
        r=MOD.evaluate(doc([check("mutagen","mutagen"),check("xdump","xedit")],required="B"))
        self.assertEqual(r["achieved_level"],"B")
        self.assertTrue(r["meets_required_level"])

    def test_two_wrappers_same_family_do_not_make_b(self):
        r=MOD.evaluate(doc([check("xedit-gui","xedit"),check("xdump","xedit")],required="B"))
        self.assertEqual(r["achieved_level"],"A")
        self.assertEqual(r["status"],"insufficient-evidence")

    def test_roundtrip_and_intent_raise_to_c(self):
        r=MOD.evaluate(doc(
          [check("mutagen","mutagen"),check("xdump","xedit")],
          required="C",
          roundtrip={"status":"pass","semantic_equivalence":True},
          intent={"status":"pass","unexplained_changes":[]}
        ))
        self.assertEqual(r["achieved_level"],"C")
        self.assertEqual(r["status"],"pass")

    def test_runtime_assertion_raises_to_d(self):
        r=MOD.evaluate(doc(
          [check("mutagen","mutagen"),check("xdump","xedit")],
          required="D",
          roundtrip={"status":"pass","semantic_equivalence":True},
          intent={"status":"pass","unexplained_changes":[]},
          runtime={"status":"pass","assertions_total":3,"assertions_passed":3}
        ))
        self.assertEqual(r["achieved_level"],"D")
        self.assertEqual(r["status"],"pass")

    def test_fingerprint_disagreement_blocks(self):
        r=MOD.evaluate(doc([check("mutagen","mutagen","a"),check("xdump","xedit","b")]))
        self.assertEqual(r["status"],"blocked")
        self.assertTrue(any("disagree" in x for x in r["blockers"]))

    def test_unclassified_coverage_blocks(self):
        r=MOD.evaluate(doc([check("mutagen","mutagen",discovered=10,processed=9,unclassified=1)]))
        self.assertEqual(r["status"],"blocked")
        self.assertTrue(any("unclassified" in x for x in r["blockers"]))

    def test_skipped_without_reason_blocks(self):
        c=check("mutagen","mutagen",discovered=10,processed=9,skipped=1)
        c["coverage"]["skip_reasons"]=[]
        r=MOD.evaluate(doc([c]))
        self.assertEqual(r["status"],"blocked")


if __name__=="__main__":
    unittest.main()
