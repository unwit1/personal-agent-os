import importlib.util
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location(
    "validate_semantic_oracle_pair",
    ROOT/"validate_semantic_oracle_pair.py",
)
MOD=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)

def doc(producer,*,editor_id="Same",fields=None,canonical=True,load_hash=None):
    provenance={
        "producer":producer,
        "producer_version":"1",
        "form_key_mode":"mutagen-formkey-string" if canonical else "target-plugin-plus-load-order-formid",
        "canonical_cross_load_order_form_keys":canonical,
        "coverage":{"semantic_fields":fields if fields is not None else ["editor_id"]},
    }
    if load_hash:
        provenance["load_order_sha256"]=load_hash
    return {
        "schema_version":"skyrim-semantic-plugin-v1",
        "plugin":{"mod_key":"Fixture.esp"},
        "records":[{
            "form_key":"000001:Fixture.esp" if canonical else "Fixture.esp|01000001",
            "signature":"MISC",
            "editor_id":editor_id,
        }],
        "provenance":provenance,
    }

class ValidateSemanticOraclePairTests(unittest.TestCase):
    def test_matching_mutagen_and_xdump_pass(self):
        report=MOD.validate_pair(
            doc("mutagen-semantic-export"),
            doc("xedit-xdump-text-normalizer"),
            require_producers={
                "mutagen-semantic-export",
                "xedit-xdump-text-normalizer",
            },
        )
        self.assertEqual(report["status"],"pass")
        self.assertEqual(report["compared_fields"],["editor_id"])

    def test_shared_semantic_disagreement_fails(self):
        report=MOD.validate_pair(
            doc("mutagen-semantic-export",editor_id="A"),
            doc("xedit-xdump-text-normalizer",editor_id="B"),
        )
        self.assertEqual(report["status"],"fail")
        self.assertEqual(report["diff"]["verdict"],"different")

    def test_incompatible_identity_needs_review(self):
        report=MOD.validate_pair(
            doc("mutagen-semantic-export"),
            doc(
                "xedit-xdump-text-normalizer",
                canonical=False,
                load_hash="abc",
            ),
        )
        self.assertEqual(report["status"],"needs-review")
        self.assertFalse(report["diff"]["comparable"])

    def test_no_shared_declared_fields_needs_review(self):
        report=MOD.validate_pair(
            doc("mutagen-semantic-export",fields=["editor_id"]),
            doc("xedit-xdump-text-normalizer",fields=["asset_paths"]),
        )
        self.assertEqual(report["status"],"needs-review")
        self.assertEqual(report["compared_fields"],[])

    def test_missing_required_producer_is_reported(self):
        report=MOD.validate_pair(
            doc("fixture-a"),
            doc("fixture-b"),
            require_producers={
                "mutagen-semantic-export",
                "xedit-xdump-text-normalizer",
            },
        )
        self.assertTrue(
            any("required semantic producers" in x for x in report["issues"])
        )

if __name__=="__main__":
    unittest.main()
