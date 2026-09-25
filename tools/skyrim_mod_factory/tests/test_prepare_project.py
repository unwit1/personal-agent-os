import importlib.util
import json, tempfile, unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location("prep",ROOT/"prepare_project.py")
MOD=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(MOD)

class PrepTests(unittest.TestCase):
    def test_pattern_enriches_quality(self):
        m={"features":[{"feature_id":"a","pattern_id":"p"}]}
        q={"gates":["G00"],"runtime_scenarios":[],"mutation_tests":[],"human_checks":[],
           "adapters":{"preferred":[],"supporting":[]},"reasons":{}}
        patterns={"p":{"pattern_id":"p","selection":{"preferred":["xedit"]},
          "validation":{"gates":["G24"],"runtime_tests":["smoke"],"negative_tests":["bad"],"human_checks":[]}}}
        out=MOD.enrich_quality(m,q,patterns)
        self.assertIn("G24",out["gates"])
        self.assertIn("xedit",out["adapters"]["preferred"])
        self.assertIn("smoke",out["runtime_scenarios"])

    def test_unknown_pattern_is_issue(self):
        q={"gates":["G00"],"runtime_scenarios":[],"mutation_tests":[],"human_checks":[],
           "adapters":{"preferred":[],"supporting":[]},"reasons":{}}
        out=MOD.enrich_quality({"features":[{"feature_id":"x","pattern_id":"nope"}]},q,{})
        self.assertTrue(out["pattern_issues"])

if __name__=="__main__":
    unittest.main()
