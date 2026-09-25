import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location("render_oar",ROOT/"render_oar.py")
MOD=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)

def intent(entries):
    return {
        "schema_version":"skyrim-runtime-patch-intent-v1",
        "intent_id":"fixture.oar",
        "framework":"oar",
        "framework_version":"current-source-snapshot",
        "grammar_source":{
            "url":"https://github.com/ersh1/OpenAnimationReplacer",
            "snapshot":"f4e7688b065175aff70aa523073857911e15aca3",
        },
        "oar":{
            "name":"Fixture OAR Pack",
            "author":"Agent OS",
            "description":"Fixture",
        },
        "entries":entries,
    }

class OARRendererTests(unittest.TestCase):
    def test_root_and_submod_use_upstream_parser_field_names(self):
        doc=intent([{
            "kind":"OARSubmod",
            "directory":"Combat/Swords",
            "name":"Sword combat",
            "description":"Fixture submod",
            "priority":500,
            "disabled":False,
            "override_animations_folder":"SharedSwordAnimations",
            "required_behavior_project_name":"DefaultMale",
            "interruptible":True,
            "replace_on_loop":False,
            "replace_on_echo":True,
            "conditions":[{"condition":"IsActorBase","Form":"Skyrim.esm|0x7"}],
            "paired_conditions":[{"condition":"IsFemale","negated":True}],
        }])
        files=MOD.render_files(doc)
        self.assertEqual(
            files["config.json"],
            {"name":"Fixture OAR Pack","author":"Agent OS","description":"Fixture"},
        )
        sub=files["Combat/Swords/config.json"]
        self.assertEqual(sub["priority"],500)
        self.assertEqual(sub["overrideAnimationsFolder"],"SharedSwordAnimations")
        self.assertEqual(sub["requiredBehaviorProjectName"],"DefaultMale")
        self.assertTrue(sub["interruptible"])
        self.assertFalse(sub["replaceOnLoop"])
        self.assertTrue(sub["replaceOnEcho"])
        self.assertEqual(sub["conditions"][0]["condition"],"IsActorBase")
        self.assertEqual(sub["pairedConditions"][0]["condition"],"IsFemale")

    def test_empty_conditions_are_preserved_for_always_on_submod(self):
        files=MOD.render_files(intent([{
            "kind":"OARSubmod",
            "directory":"Always",
            "name":"Always",
            "priority":10,
            "conditions":[],
        }]))
        self.assertEqual(files["Always/config.json"]["conditions"],[])

    def test_duplicate_casefolded_submod_paths_fail_closed(self):
        with self.assertRaisesRegex(ValueError,"duplicate OAR"):
            MOD.render_files(intent([
                {"kind":"OARSubmod","directory":"Combat/Swords","name":"A","priority":1,"conditions":[]},
                {"kind":"OARSubmod","directory":"combat/swords","name":"B","priority":2,"conditions":[]},
            ]))

    def test_parent_traversal_and_absolute_paths_are_rejected(self):
        for value in ("../escape","Combat/../../escape","/absolute","C:/absolute"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    MOD.safe_relative_directory(value)

    def test_schema_rejects_condition_without_discriminator(self):
        errors=MOD.schema_errors(intent([{
            "kind":"OARSubmod",
            "directory":"Broken",
            "name":"Broken",
            "priority":1,
            "conditions":[{"negated":True}],
        }]))
        self.assertTrue(errors)

    def test_writer_creates_only_declared_config_tree(self):
        files=MOD.render_files(intent([{
            "kind":"OARSubmod",
            "directory":"Combat/Swords",
            "name":"Sword combat",
            "priority":500,
            "conditions":[],
        }]))
        with tempfile.TemporaryDirectory() as td:
            written=MOD.write_files(files,Path(td))
            rel=sorted(str(x.relative_to(td)).replace("\\","/") for x in written)
            self.assertEqual(rel,["Combat/Swords/config.json","config.json"])

if __name__=="__main__":
    unittest.main()
