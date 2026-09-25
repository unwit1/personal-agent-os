import importlib.util
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location(
    "analyze_vmad_bindings",
    ROOT/"analyze_vmad_bindings.py",
)
MOD=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)

def inventory():
    return {
        "schema_version":"skyrim-papyrus-symbol-inventory-v1",
        "scripts":[
            {
                "name":"BaseScript",
                "parent":None,
                "properties":[
                    {"name":"RequiredRef","type":"ObjectReference","required":True},
                    {"name":"OptionalCount","type":"Int","required":False},
                ],
            },
            {
                "name":"ChildScript",
                "parent":"BaseScript",
                "properties":[
                    {"name":"Label","type":"String","required":False},
                ],
            },
        ],
    }

def bindings(properties,script="ChildScript"):
    return {
        "schema_version":"skyrim-vmad-binding-set-v1",
        "record":"REFR:000001:Fixture.esp",
        "scripts":[{"name":script,"properties":properties}],
    }

class VMADBindingTests(unittest.TestCase):
    def test_inherited_required_property_resolves(self):
        report=MOD.analyze(
            inventory(),
            bindings([
                {"name":"RequiredRef","type":"ObjectReference","value":"000123:Skyrim.esm"},
                {"name":"Label","type":"String","value":"Hello"},
            ]),
        )
        self.assertEqual(report["status"],"pass")

    def test_optional_none_property_is_valid(self):
        report=MOD.analyze(
            inventory(),
            bindings([
                {"name":"RequiredRef","type":"ObjectReference","value":"000123:Skyrim.esm"},
                {"name":"OptionalCount","type":"Int","value":None},
            ]),
        )
        self.assertEqual(report["status"],"pass")

    def test_missing_required_property_fails(self):
        report=MOD.analyze(
            inventory(),
            bindings([{"name":"Label","type":"String","value":"Hello"}]),
        )
        self.assertEqual(report["status"],"fail")
        self.assertTrue(any(
            "required Papyrus property is not bound" in x["message"]
            for x in report["findings"]
        ))

    def test_required_none_property_fails(self):
        report=MOD.analyze(
            inventory(),
            bindings([
                {"name":"RequiredRef","type":"ObjectReference","value":None},
            ]),
        )
        self.assertEqual(report["status"],"fail")
        self.assertTrue(any(
            "bound to None" in x["message"]
            for x in report["findings"]
        ))

    def test_property_type_mismatch_fails(self):
        report=MOD.analyze(
            inventory(),
            bindings([
                {"name":"RequiredRef","type":"Int","value":1},
            ]),
        )
        self.assertEqual(report["status"],"fail")
        self.assertTrue(any(
            "type mismatch" in x["message"] for x in report["findings"]
        ))

    def test_stale_unknown_property_fails(self):
        report=MOD.analyze(
            inventory(),
            bindings([
                {"name":"RequiredRef","type":"ObjectReference","value":"000123:Skyrim.esm"},
                {"name":"OldProperty","type":"Int","value":1},
            ]),
        )
        self.assertEqual(report["status"],"fail")
        self.assertTrue(any(
            "is not declared" in x["message"] for x in report["findings"]
        ))

    def test_missing_script_fails(self):
        report=MOD.analyze(inventory(),bindings([],script="RemovedScript"))
        self.assertEqual(report["status"],"fail")
        self.assertTrue(any(
            "absent from the pinned Papyrus inventory" in x["message"]
            for x in report["findings"]
        ))

    def test_parent_cycle_requires_review(self):
        inv=inventory()
        inv["scripts"][0]["parent"]="ChildScript"
        report=MOD.analyze(
            inv,
            bindings([{"name":"RequiredRef","type":"ObjectReference","value":"x"}]),
        )
        self.assertEqual(report["status"],"needs-review")
        self.assertTrue(any("inheritance cycle" in x for x in report["issues"]))

if __name__=="__main__":
    unittest.main()
