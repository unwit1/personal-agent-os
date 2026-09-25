import importlib.util
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location(
    "derive_runtime_smoke",
    ROOT/"derive_runtime_smoke.py",
)
MOD=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)

class DeriveRuntimeSmokeTests(unittest.TestCase):
    def test_derives_schema_valid_nonmutating_health_smoke(self):
        test=MOD.derive({
            "project_id":"fixture",
            "targets":["se-steam","se-steam"],
        })
        self.assertEqual(test["adapter"],"mo2-devbench-runtime")
        self.assertEqual(test["fixture"]["kind"],"custom")
        self.assertFalse(test["safety"]["allow_save_mutation"])
        self.assertFalse(test["safety"]["allow_console_mutation"])
        self.assertEqual(test["targets"],["se-steam"])
        self.assertEqual(
            test["steps"][0]["driver"]["arguments"],
            {"kind":"health"},
        )
        self.assertTrue(all(
            assertion["probe"]["adapter"]=="devbench"
            for assertion in test["assertions"]
        ))
        self.assertEqual(MOD.schema_errors(test),[])

    def test_smoke_only_asserts_harness_health_not_feature_semantics(self):
        test=MOD.derive({"project_id":"fixture","targets":[]})
        ids={x["id"] for x in test["assertions"]}
        self.assertEqual(ids,{"runtime-pid","runtime-executable"})
        self.assertFalse(test["evidence"]["performance"])

if __name__=="__main__":
    unittest.main()
