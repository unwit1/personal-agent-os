import importlib.util
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location("render_flm",ROOT/"render_flm.py")
MOD=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)

def intent(entries):
    return {
        "schema_version":"skyrim-runtime-patch-intent-v1",
        "intent_id":"fixture.flm",
        "framework":"flm",
        "framework_version":"1.8.1",
        "grammar_source":{
            "url":"https://github.com/MaskedRPGFan/FormList-Manipulator",
            "snapshot":"82a694e5d33194ae223f23846b1f180ee394cdee",
        },
        "output_file":"Fixture_FLM.ini",
        "entries":entries,
    }

class FLMRendererTests(unittest.TestCase):
    def test_formlist_supports_form_expansion_group_collection_and_named_filter(self):
        row=MOD.render_entry({
            "kind":"FLMFormList",
            "target":{"source":"formlist","form":{"editor_id":"TargetList"}},
            "members":[
                {"source":"form","form":{"editor_id":"DirectForm"}},
                {"source":"formlist_contents","form":{"form_id":"0x8246","plugin":"HearthFires.esm"}},
                {"source":"group","name":"Dolls"},
                {"source":"collection","name":"Irons"},
            ],
            "filter":{"name":"OnlyWhenOptionalModLoads"},
        })
        self.assertEqual(
            row,
            "FormList = TargetList|DirectForm,*0x8246~HearthFires.esm,#Dolls,#Irons|#OnlyWhenOptionalModLoads",
        )

    def test_collection_renders_excluded_keyword_and_inline_filter(self):
        row=MOD.render_entry({
            "kind":"FLMCollection",
            "name":"IronNotWarAxes",
            "form_type":"Weapon",
            "keywords":[
                {"form":{"editor_id":"WeapMaterialIron"}},
                {"form":{"editor_id":"WeapTypeWarAxe"},"exclude":True},
            ],
            "filter":{"conditions":["+Optional.esp","-Conflict.esp&+Required.esp"]},
        })
        self.assertEqual(
            row,
            "Collection = IronNotWarAxes|Weapon|WeapMaterialIron,-WeapTypeWarAxe|+Optional.esp,-Conflict.esp&+Required.esp",
        )

    def test_mod_event_and_simplified_entries_follow_documented_grammar(self):
        self.assertEqual(
            MOD.render_entry({
                "kind":"FLMModEvent",
                "event_name":"TestEvent",
                "target":{"source":"alias","name":"TestAlias"},
                "members":[{"source":"group","name":"Dolls"}],
            }),
            "ModEvent = TestEvent|#TestAlias|#Dolls",
        )
        self.assertEqual(
            MOD.render_entry({
                "kind":"FLMPlant",
                "first":{"editor_id":"ChaurusEggs"},
                "second":{"editor_id":"PlantableAnimalsChaurusNest"},
            }),
            "Plant = ChaurusEggs|PlantableAnimalsChaurusNest",
        )
        self.assertEqual(
            MOD.render_entry({
                "kind":"FLMBToys",
                "members":[{"source":"group","name":"Dolls"}],
                "filter":{"conditions":["+AdditionalHearthfireDolls.esp"]},
            }),
            "BToys = #Dolls|+AdditionalHearthfireDolls.esp",
        )

    def test_definitions_are_emitted_before_operations_without_section_header(self):
        doc=MOD.render_document(intent([
            {
                "kind":"FLMFormList",
                "target":{"source":"alias","name":"TestAlias"},
                "members":[{"source":"group","name":"Dolls"}],
            },
            {
                "kind":"FLMGroup",
                "name":"Dolls",
                "members":[{"source":"form","form":{"editor_id":"BYOHChefDoll"}}],
            },
            {
                "kind":"FLMFilter",
                "name":"Optional",
                "conditions":["+Optional.esp"],
            },
            {
                "kind":"FLMAlias",
                "name":"TestAlias",
                "formlists":[{"form_id":"0x8246","plugin":"HearthFires.esm"}],
            },
        ]))
        self.assertNotIn("[General]",doc)
        self.assertLess(doc.index("Filter ="),doc.index("Alias ="))
        self.assertLess(doc.index("Alias ="),doc.index("Group ="))
        self.assertLess(doc.index("Group ="),doc.index("FormList ="))
        self.assertEqual(MOD.schema_errors(intent([
            {
                "kind":"FLMFormList",
                "target":{"source":"formlist","form":{"editor_id":"TargetList"}},
                "members":[{"source":"form","form":{"editor_id":"DirectForm"}}],
            }
        ])),[])

    def test_dynamic_keyword_is_rejected_by_flm_renderer(self):
        with self.assertRaises(ValueError):
            MOD.form_ref({"dynamic_keyword":"$SomeDynamicKeyword"})

    def test_filter_must_choose_named_or_inline_not_both(self):
        with self.assertRaises(ValueError):
            MOD.filter_ref({"name":"Named","conditions":["+Optional.esp"]})

if __name__=="__main__":
    unittest.main()
