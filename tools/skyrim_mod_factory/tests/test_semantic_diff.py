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

    def semantic_doc(self,value=1,*,mode="canonical-formkey",canonical=True,load_hash=None):
        provenance={
            "producer":"fixture",
            "producer_version":"1",
            "form_key_mode":mode,
            "canonical_cross_load_order_form_keys":canonical,
        }
        if load_hash:
            provenance["load_order_sha256"]=load_hash
        return {
            "schema_version":"skyrim-semantic-plugin-v1",
            "plugin":{"mod_key":"Fixture.esp"},
            "records":[{
                "form_key":"Fixture.esp|000001",
                "signature":"MISC",
                "fields":{"value":value},
            }],
            "provenance":provenance,
        }

    def test_canonical_identity_documents_are_comparable(self):
        result=MOD.compare(self.semantic_doc(1),self.semantic_doc(2))
        self.assertTrue(result["comparable"])
        self.assertEqual(result["verdict"],"different")
        self.assertEqual(result["summary"]["changed"],1)

    def test_noncanonical_identity_without_load_hash_is_not_comparable(self):
        before=self.semantic_doc(
            mode="target-plugin-plus-load-order-formid",
            canonical=False,
        )
        after=self.semantic_doc(
            mode="target-plugin-plus-load-order-formid",
            canonical=False,
        )
        result=MOD.compare(before,after)
        self.assertFalse(result["comparable"])
        self.assertEqual(result["verdict"],"not-comparable")
        self.assertEqual(result["records_added"],[])
        self.assertEqual(result["records_removed"],[])

    def test_noncanonical_identity_with_matching_load_hash_is_comparable(self):
        before=self.semantic_doc(
            1,
            mode="target-plugin-plus-load-order-formid",
            canonical=False,
            load_hash="abc",
        )
        after=self.semantic_doc(
            2,
            mode="target-plugin-plus-load-order-formid",
            canonical=False,
            load_hash="abc",
        )
        result=MOD.compare(before,after)
        self.assertTrue(result["comparable"])
        self.assertEqual(result["verdict"],"different")

    def test_noncanonical_identity_with_different_load_hash_is_not_comparable(self):
        before=self.semantic_doc(
            mode="target-plugin-plus-load-order-formid",
            canonical=False,
            load_hash="abc",
        )
        after=self.semantic_doc(
            mode="target-plugin-plus-load-order-formid",
            canonical=False,
            load_hash="def",
        )
        result=MOD.compare(before,after)
        self.assertFalse(result["comparable"])
        self.assertEqual(result["verdict"],"not-comparable")
        self.assertTrue(result["comparability_reasons"])


    def test_declared_coverage_ignores_producer_private_evidence(self):
        before=self.semantic_doc()
        after=self.semantic_doc()
        before["provenance"]["coverage"]={"semantic_fields":["editor_id"]}
        after["provenance"]["coverage"]={"semantic_fields":["editor_id"]}
        before["records"][0]["editor_id"]="SameEDID"
        after["records"][0]["editor_id"]="SameEDID"
        before["records"][0]["fields"]={"_xdump":{"raw":"different-a"}}
        after["records"][0]["fields"]={"_mutagen":{"raw":"different-b"}}
        result=MOD.compare(before,after)
        self.assertEqual(result["verdict"],"equivalent")
        self.assertEqual(
            result["coverage"]["compared_fields"],
            ["editor_id"],
        )

    def test_declared_coverage_detects_shared_semantic_field_change(self):
        before=self.semantic_doc()
        after=self.semantic_doc()
        before["provenance"]["coverage"]={"semantic_fields":["editor_id"]}
        after["provenance"]["coverage"]={"semantic_fields":["editor_id"]}
        before["records"][0]["editor_id"]="BeforeEDID"
        after["records"][0]["editor_id"]="AfterEDID"
        result=MOD.compare(before,after)
        self.assertEqual(result["verdict"],"different")
        self.assertEqual(result["summary"]["changed"],1)

    def test_declared_coverage_does_not_compare_one_sided_field(self):
        before=self.semantic_doc()
        after=self.semantic_doc()
        before["provenance"]["coverage"]={
            "semantic_fields":["editor_id","asset_paths"]
        }
        after["provenance"]["coverage"]={"semantic_fields":["editor_id"]}
        before["records"][0]["editor_id"]="SameEDID"
        after["records"][0]["editor_id"]="SameEDID"
        before["records"][0]["asset_paths"]=["a.nif"]
        after["records"][0]["asset_paths"]=["b.nif"]
        result=MOD.compare(before,after)
        self.assertEqual(result["verdict"],"equivalent")
        self.assertEqual(
            result["coverage"]["before_only_fields"],
            ["asset_paths"],
        )


if __name__=="__main__":
    unittest.main()
