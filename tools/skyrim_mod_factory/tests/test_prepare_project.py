import importlib.util
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location("prep",ROOT/"prepare_project.py")
MOD=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(MOD)

def qbase():
    return {"gates":["G00"],"runtime_scenarios":[],"mutation_tests":[],"human_checks":[],
            "adapters":{"preferred":[],"supporting":[]},"reasons":{}}

class PrepTests(unittest.TestCase):
    def test_pattern_adapter_enriches_quality(self):
        m={"features":[{"feature_id":"a","pattern_id":"p"}]}
        patterns={"p":{"pattern_id":"p","selection":{"preferred":["xedit"]},
          "validation":{"gates":["G24"],"runtime_tests":["smoke"],"negative_tests":["bad"],"human_checks":[]}}}
        out=MOD.enrich_quality(m,qbase(),patterns,{},{"xedit"})
        self.assertIn("G24",out["gates"])
        self.assertIn("xedit",out["adapters"]["preferred"])
        self.assertIn("smoke",out["runtime_scenarios"])
        self.assertFalse(out["provider_issues"])

    def test_framework_does_not_become_fake_adapter(self):
        patterns={"p":{"pattern_id":"p","selection":{"preferred":["oar"]},
          "validation":{"gates":[]}}}
        providers={"oar":{"provider_id":"oar","kind":"framework","validation_adapters":["devbench"]}}
        out=MOD.enrich_quality({"features":[{"feature_id":"x","pattern_id":"p"}]},qbase(),patterns,providers,{"devbench"})
        self.assertIn("oar",out["framework_dependencies"])
        self.assertNotIn("oar",out["adapters"]["preferred"])
        self.assertIn("devbench",out["adapters"]["supporting"])

    def test_alias_resolves_to_adapter(self):
        patterns={"p":{"pattern_id":"p","selection":{"preferred":["xedit-inspection"]},"validation":{"gates":[]}}}
        providers={"xedit-inspection":{"provider_id":"xedit-inspection","kind":"alias","adapter_id":"xedit","validation_adapters":[]}}
        out=MOD.enrich_quality({"features":[{"feature_id":"x","pattern_id":"p"}]},qbase(),patterns,providers,{"xedit"})
        self.assertIn("xedit",out["adapters"]["preferred"])
        self.assertFalse(out["unadapted_providers"])

    def test_unadapted_preferred_is_explicit(self):
        patterns={"p":{"pattern_id":"p","selection":{"preferred":["kreate"]},"validation":{"gates":[]}}}
        providers={"kreate":{"provider_id":"kreate","kind":"unadapted-tool","validation_adapters":["xedit"]}}
        out=MOD.enrich_quality({"features":[{"feature_id":"x","pattern_id":"p"}]},qbase(),patterns,providers,{"xedit"})
        self.assertIn("kreate",out["unadapted_providers"])

    def test_unknown_pattern_is_issue(self):
        out=MOD.enrich_quality({"features":[{"feature_id":"x","pattern_id":"nope"}]},qbase(),{}, {}, {"xedit"})
        self.assertTrue(out["pattern_issues"])

    def test_effective_manifest_adds_selected_pattern_without_mutating_source(self):
        source={
          "project_id":"demo",
          "layers":["records"],
          "features":[{"feature_id":"f","intent":"Do a thing"}]
        }
        original_layers=list(source["layers"])
        feature={"feature_id":"f","summary":"Conditional animation","implementation":{"selected_layers":["animation"]}}
        selection={"status":"selected","selected_pattern":"conditional-animation-replacement"}
        patterns={"conditional-animation-replacement":{
          "preferred_layers":["animation"],"pattern_id":"conditional-animation-replacement"
        }}
        effective,deductions=MOD.make_effective_manifest(source,feature,selection,patterns)
        self.assertEqual(source["layers"],original_layers)
        self.assertNotIn("animation",source["layers"])
        self.assertIn("animation",effective["layers"])
        self.assertEqual(effective["features"][0]["pattern_id"],"conditional-animation-replacement")
        self.assertTrue(deductions)

    def test_unresolved_pattern_does_not_invent_pattern_id(self):
        source={"project_id":"demo","layers":["records"],"features":[{"feature_id":"f","intent":"Unknown"}]}
        feature={"feature_id":"f","summary":"Unknown","implementation":{}}
        selection={"status":"research-required","selected_pattern":None}
        effective,_=MOD.make_effective_manifest(source,feature,selection,{})
        self.assertNotIn("pattern_id",effective["features"][0])

if __name__=="__main__":
    unittest.main()
