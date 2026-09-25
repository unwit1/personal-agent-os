import importlib.util
import tempfile
import unittest
from pathlib import Path

TOOLS=Path(__file__).resolve().parents[2]
SPEC=importlib.util.spec_from_file_location(
    "extract_papyrus_api",
    TOOLS/"knowledge"/"extract_papyrus_api.py",
)
MOD=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)

class ExtractPapyrusPropertiesTests(unittest.TestCase):
    def test_scan_file_extracts_script_parent_and_properties(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            psc=root/"ChildScript.psc"
            psc.write_text(
                """Scriptname ChildScript extends ParentScript
ObjectReference Property TargetRef Auto
Int Property Count = 3 AutoReadOnly
String Property Label
Event OnInit()
EndEvent
""",
                encoding="utf-8",
            )
            data=MOD.scan_file(psc,root)
            self.assertEqual(data["script"],"ChildScript")
            self.assertEqual(data["extends"],"ParentScript")
            props={x["name"]:x for x in data["properties"]}
            self.assertEqual(props["TargetRef"]["type"],"ObjectReference")
            self.assertTrue(props["TargetRef"]["auto"])
            self.assertEqual(props["Count"]["default"],"3")
            self.assertTrue(props["Count"]["auto"])
            self.assertFalse(props["Label"]["auto"])
            self.assertEqual(data["declarations"][0]["name"],"OnInit")

    def test_symbol_inventory_defaults_required_false(self):
        data=[{
            "script":"Example",
            "extends":None,
            "source":"Example.psc",
            "declarations":[],
            "properties":[{
                "name":"Target",
                "type":"ObjectReference",
                "default":None,
                "modifiers":"Auto",
                "auto":True,
                "conditional":False,
                "hidden":False,
                "line":2,
            }],
        }]
        inv=MOD.symbol_inventory(data,"fixture")
        self.assertEqual(
            inv["schema_version"],
            "skyrim-papyrus-symbol-inventory-v1",
        )
        prop=inv["scripts"][0]["properties"][0]
        self.assertFalse(prop["required"])
        self.assertTrue(prop["auto"])

if __name__=="__main__":
    unittest.main()
