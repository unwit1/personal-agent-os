import importlib.util
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location("quality",ROOT/"derive_quality_plan.py")
MOD=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(MOD)

def base(layers, outputs, **extra):
    m={
      "schema_version":"skyrim-mod-project-v1",
      "project_id":"demo",
      "name":"Demo",
      "targets":["ae-1.7.x"],
      "layers":layers,
      "outputs":[{"path":f"out/{i}.{t}","type":t} for i,t in enumerate(outputs)],
      "validation":{"required_gates":[]}
    }
    m.update(extra)
    return m

class QualityPlanTests(unittest.TestCase):
    def test_records_get_schema_and_independent_validation(self):
        p=MOD.derive(base(["records"],["plugin"]))
        self.assertIn("G02",p["gates"])
        self.assertIn("G24",p["gates"])
        self.assertIn("xedit",p["adapters"]["preferred"])

    def test_esl_gets_light_gate(self):
        p=MOD.derive(base(["records"],["plugin"],plugin_policy={"kind":"esp-fe"}))
        self.assertIn("G04",p["gates"])

    def test_native_persistent_is_critical(self):
        p=MOD.derive(base(["native","save-persistence"],["dll"],persistence={"uses_skse_cosave":True}))
        self.assertEqual(p["risk_tier"],"critical")
        self.assertIn("G21",p["gates"])
        self.assertTrue(any("schema version" in q for q in p["blocking_questions"]))

    def test_mesh_texture_requests_independent_assets(self):
        p=MOD.derive(base(["mesh","texture"],["nif","dds"]))
        self.assertIn("G12",p["gates"])
        self.assertIn("G13",p["gates"])
        self.assertIn("G28",p["gates"])
        self.assertIn("pynifly",p["adapters"]["preferred"])
        self.assertIn("directxtex",p["adapters"]["preferred"])

    def test_navmesh_requires_runtime_and_human_pathing(self):
        p=MOD.derive(base(["world","navmesh"],["plugin"]))
        self.assertIn("G15",p["gates"])
        self.assertIn("G26",p["gates"])
        self.assertTrue(any("path traversal" in x for x in p["runtime_scenarios"]))

    def test_papyrus_prefers_pyro_build(self):
        p=MOD.derive(base(["papyrus"],["pex"]))
        self.assertIn("pyro",p["adapters"]["preferred"])
        self.assertIn("official-papyruscompiler",p["adapters"]["preferred"])

    def test_papyrus_extender_framework_adds_provider_checks(self):
        p=MOD.derive(base(
            ["papyrus"],["pex"],
            frameworks=[{"id":"papyrus-extender","required":True}]
        ))
        self.assertIn("papyrus-extender",p["adapters"]["supporting"])
        self.assertTrue(any("provider" in x.lower() for x in p["static_checks"]))
        self.assertTrue(any("Papyrus Extender" in x for x in p["runtime_scenarios"]))

    def test_native_prefers_commonlib_build_pipeline(self):
        p=MOD.derive(base(["native"],["dll"]))
        self.assertIn("commonlib-cmake-configure",p["adapters"]["preferred"])
        self.assertIn("commonlib-cmake-build",p["adapters"]["preferred"])

if __name__=="__main__":
    unittest.main()
