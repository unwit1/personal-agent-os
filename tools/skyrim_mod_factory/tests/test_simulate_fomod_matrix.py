import importlib.util
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location(
    "simulate_fomod_matrix",
    ROOT/"simulate_fomod_matrix.py",
)
MOD=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)

def intent():
    return {
        "schema_version":"skyrim-fomod-intent-v1",
        "metadata":{
            "name":"Fixture","author":"Tester","version":"1.0",
            "description":"Fixture",
        },
        "module":{
            "name":"Fixture Installer",
            "dependencies":{
                "kind":"file","file":"Skyrim.esm","state":"Active",
            },
            "required_files":[{
                "kind":"file","source":"core.txt","destination":"core.txt",
            }],
            "steps":[{
                "name":"Variant",
                "groups":[{
                    "name":"Choose",
                    "type":"SelectExactlyOne",
                    "options":[
                        {
                            "name":"A","description":"A","type":"Recommended",
                            "files":[{
                                "kind":"folder","source":"a","destination":"",
                            }],
                            "flags":[{"name":"variant","value":"a"}],
                        },
                        {
                            "name":"B","description":"B","type":"Optional",
                            "files":[{
                                "kind":"folder","source":"b","destination":"",
                            }],
                            "flags":[{"name":"variant","value":"b"}],
                        },
                    ],
                }],
            }],
            "conditional_installs":[{
                "dependencies":{
                    "kind":"flag","flag":"variant","value":"b",
                },
                "files":[{
                    "kind":"file","source":"b.ini",
                    "destination":"SKSE/Plugins/b.ini",
                }],
            }],
        },
    }

ENV={"files":{"Skyrim.esm":"Active"},"game_version":"1.6.1170"}

class SimulateFomodMatrixTests(unittest.TestCase):
    def test_exactly_one_group_enumerates_two_cases(self):
        report=MOD.simulate(intent(),environment=ENV)
        self.assertEqual(report["status"],"pass")
        self.assertEqual(report["total_cases"],2)
        selections={
            case["selections"][0]["options"][0]
            for case in report["cases"]
        }
        self.assertEqual(selections,{"A","B"})

    def test_conditional_install_fires_only_for_matching_flag(self):
        report=MOD.simulate(intent(),environment=ENV)
        by_choice={
            case["selections"][0]["options"][0]:case
            for case in report["cases"]
        }
        self.assertFalse(any(
            x["source"]=="b.ini" for x in by_choice["A"]["installed_items"]
        ))
        self.assertTrue(any(
            x["source"]=="b.ini" for x in by_choice["B"]["installed_items"]
        ))

    def test_module_dependency_false_yields_no_cases_without_invalidating_installer(self):
        report=MOD.simulate(
            intent(),
            environment={"files":{"Skyrim.esm":"Missing"}},
        )
        self.assertEqual(report["status"],"pass")
        self.assertFalse(report["module_dependencies_met"])
        self.assertEqual(report["total_cases"],0)

    def test_later_step_visibility_uses_prior_flags(self):
        value=intent()
        value["module"]["steps"].append({
            "name":"Only For B",
            "visible":{"kind":"flag","flag":"variant","value":"b"},
            "groups":[{
                "name":"Extra",
                "type":"SelectExactlyOne",
                "options":[{
                    "name":"Extra On","description":"extra","type":"Recommended",
                    "flags":[{"name":"extra","value":"yes"}],
                }],
            }],
        })
        report=MOD.simulate(value,environment=ENV)
        by_choice={
            case["selections"][0]["options"][0]:case
            for case in report["cases"]
        }
        self.assertEqual(by_choice["A"]["visible_steps"],["Variant"])
        self.assertEqual(by_choice["B"]["visible_steps"],["Variant","Only For B"])
        self.assertEqual(by_choice["B"]["flags"]["extra"],"yes")

    def test_multiple_required_in_exactly_one_is_unsatisfiable(self):
        value=intent()
        for option in value["module"]["steps"][0]["groups"][0]["options"]:
            option["type"]="Required"
        report=MOD.simulate(value,environment=ENV)
        self.assertEqual(report["status"],"fail")
        self.assertTrue(any(
            "unsatisfiable group" in issue
            for case in report["cases"]
            for issue in case["issues"]
        ))

    def test_conflicting_flags_fail_case(self):
        value=intent()
        group=value["module"]["steps"][0]["groups"][0]
        group["type"]="SelectAll"
        for option in group["options"]:
            option["type"]="Required"
        group["options"][1]["flags"][0]["value"]="different"
        report=MOD.simulate(value,environment=ENV)
        self.assertEqual(report["status"],"fail")
        self.assertTrue(any(
            "condition flag conflict" in issue
            for issue in report["cases"][0]["issues"]
        ))

    def test_ambiguous_equal_priority_destination_collision_fails(self):
        value=intent()
        group=value["module"]["steps"][0]["groups"][0]
        group["type"]="SelectAll"
        for option in group["options"]:
            option["type"]="Required"
            option["flags"]=[]
        group["options"][0]["files"]=[{
            "kind":"file","source":"a.txt","destination":"same.txt","priority":0,
        }]
        group["options"][1]["files"]=[{
            "kind":"file","source":"b.txt","destination":"same.txt","priority":0,
        }]
        report=MOD.simulate(value,environment=ENV)
        self.assertEqual(report["status"],"fail")
        self.assertTrue(any(
            "ambiguous install collision" in issue
            for issue in report["cases"][0]["issues"]
        ))

    def test_higher_priority_resolves_destination_winner(self):
        value=intent()
        group=value["module"]["steps"][0]["groups"][0]
        group["type"]="SelectAll"
        for option in group["options"]:
            option["type"]="Required"
            option["flags"]=[]
        group["options"][0]["files"]=[{
            "kind":"file","source":"a.txt","destination":"same.txt","priority":0,
        }]
        group["options"][1]["files"]=[{
            "kind":"file","source":"b.txt","destination":"same.txt","priority":1,
        }]
        report=MOD.simulate(value,environment=ENV)
        self.assertEqual(report["status"],"pass")

    def test_max_case_guard_prevents_exponential_blowup(self):
        value=intent()
        group=value["module"]["steps"][0]["groups"][0]
        group["type"]="SelectAny"
        with self.assertRaisesRegex(ValueError,"max_cases"):
            MOD.simulate(value,environment=ENV,max_cases=3)

if __name__=="__main__":
    unittest.main()
