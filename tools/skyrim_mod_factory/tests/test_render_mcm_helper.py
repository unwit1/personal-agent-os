import importlib.util
import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location(
    "render_mcm_helper",
    ROOT/"render_mcm_helper.py",
)
MOD=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)

def intent():
    return {
        "schema_version":"skyrim-mcm-helper-intent-v1",
        "config":{
            "modName":"Fixture",
            "displayName":"Fixture MCM",
            "minMcmVersion":13,
            "pages":[{
                "pageDisplayName":"$General",
                "cursorFillMode":"topToBottom",
                "content":[
                    {
                        "type":"hiddenToggle",
                        "groupControl":1,
                        "valueOptions":{
                            "sourceType":"PropertyValueBool",
                            "propertyName":"AdvancedEnabled",
                        },
                    },
                    {
                        "id":"bEnabled:General",
                        "text":"$Enabled",
                        "type":"toggle",
                        "groupCondition":1,
                        "valueOptions":{"sourceType":"ModSettingBool"},
                    },
                    {
                        "id":"fScale:General",
                        "text":"$Scale",
                        "type":"slider",
                        "valueOptions":{
                            "min":0.5,"max":2.0,"step":0.1,
                            "sourceType":"ModSettingFloat",
                        },
                    },
                    {
                        "id":"iMode:General",
                        "text":"$Mode",
                        "type":"enum",
                        "valueOptions":{
                            "options":["$A","$B"],
                            "shortNames":["A","B"],
                            "sourceType":"ModSettingInt",
                        },
                    },
                ],
            }],
        },
        "settings":[{
            "name":"General",
            "values":[
                {"name":"bEnabled","value":True},
                {"name":"fScale","value":1.25},
                {"name":"iMode","value":0},
            ],
        }],
    }

class RenderMCMHelperTests(unittest.TestCase):
    def test_valid_config_and_settings_pass(self):
        report=MOD.validate_semantics(intent())
        self.assertEqual(report["status"],"pass")
        self.assertEqual(report["coverage"]["mod_setting_controls"],3)
        self.assertEqual(report["coverage"]["settings_defaults"],3)

    def test_render_is_deterministic_and_uses_key_section_ids(self):
        config_bytes,settings_bytes,report=MOD.render(intent())
        config=json.loads(config_bytes)
        self.assertEqual(config["modName"],"Fixture")
        self.assertIn("$schema",config)
        self.assertEqual(
            settings_bytes.decode("utf-8"),
            "[General]\nbEnabled=1\nfScale=1.25\niMode=0\n",
        )
        self.assertEqual(
            {x["id"] for x in report["controls"]},
            {"bEnabled:General","fScale:General","iMode:General"},
        )

    def test_missing_modsetting_default_fails(self):
        value=intent()
        value["settings"][0]["values"].pop()
        report=MOD.validate_semantics(value)
        self.assertEqual(report["status"],"fail")
        self.assertTrue(any(
            x["code"]=="MCM-MODSETTING-DEFAULT-MISSING"
            for x in report["issues"]
        ))

    def test_modsetting_source_must_match_setting_prefix(self):
        value=intent()
        control=value["config"]["pages"][0]["content"][1]
        control["valueOptions"]["sourceType"]="ModSettingFloat"
        report=MOD.validate_semantics(value)
        self.assertEqual(report["status"],"fail")
        self.assertTrue(any(
            x["code"]=="MCM-MODSETTING-SOURCE-TYPE"
            for x in report["issues"]
        ))

    def test_ini_default_must_match_prefix_type(self):
        value=intent()
        value["settings"][0]["values"][1]["value"]="not-a-float"
        report=MOD.validate_semantics(value)
        self.assertEqual(report["status"],"fail")
        self.assertTrue(any(
            x["code"]=="MCM-SETTING-TYPE-MISMATCH"
            for x in report["issues"]
        ))

    def test_unresolved_group_condition_fails(self):
        value=intent()
        value["config"]["pages"][0]["content"][1]["groupCondition"]=99
        report=MOD.validate_semantics(value)
        self.assertEqual(report["status"],"fail")
        self.assertTrue(any(
            x["code"]=="MCM-GROUPCONDITION-UNRESOLVED"
            for x in report["issues"]
        ))

    def test_duplicate_group_control_fails(self):
        value=intent()
        value["config"]["pages"][0]["content"].insert(1,{
            "type":"toggle",
            "groupControl":1,
            "valueOptions":{
                "sourceType":"PropertyValueBool",
                "propertyName":"Other",
            },
        })
        report=MOD.validate_semantics(value)
        self.assertEqual(report["status"],"fail")
        self.assertTrue(any(
            x["code"]=="MCM-DUPLICATE-GROUPCONTROL"
            for x in report["issues"]
        ))

    def test_slider_range_and_step_are_checked(self):
        value=intent()
        slider=value["config"]["pages"][0]["content"][2]["valueOptions"]
        slider["min"]=5
        slider["max"]=1
        slider["step"]=0
        report=MOD.validate_semantics(value)
        codes={x["code"] for x in report["issues"]}
        self.assertIn("MCM-SLIDER-RANGE",codes)
        self.assertIn("MCM-SLIDER-STEP",codes)

    def test_short_names_must_match_options_length(self):
        value=intent()
        value["config"]["pages"][0]["content"][3]["valueOptions"]["shortNames"]=["A"]
        report=MOD.validate_semantics(value)
        self.assertEqual(report["status"],"fail")
        self.assertTrue(any(
            x["code"]=="MCM-SHORTNAMES-LENGTH"
            for x in report["issues"]
        ))

    def test_page_cursor_fill_mode_is_accepted_by_compat_schema(self):
        value=intent()
        config=value["config"]
        config["$schema"]=MOD.UPSTREAM_SCHEMA_URL
        errors=MOD.validate_json(config,MOD.MCM_SCHEMA)
        self.assertEqual(errors,[])

if __name__=="__main__":
    unittest.main()
