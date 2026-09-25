import importlib.util
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location("matrix",ROOT/"derive_test_matrix.py")
MOD=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(MOD)


def base(layers, **extra):
    m={
      "schema_version":"skyrim-mod-project-v1",
      "project_id":"demo",
      "name":"Demo",
      "targets":["ae-1.7.x"],
      "layers":layers,
      "outputs":[{"path":"out/Demo.esp","type":"plugin","generated":True}],
      "validation":{"required_gates":[]},
      "release":{"license":"MIT"}
    }
    m.update(extra)
    return m


class TestMatrixTests(unittest.TestCase):
    def test_every_project_gets_smoke(self):
        p=MOD.derive(base(["records"]))
        ids={x["test_id"] for x in p["cases"]}
        self.assertIn("demo.launch-smoke",ids)

    def test_runtime_patching_gets_positive_and_idempotency(self):
        p=MOD.derive(base(["runtime-patching"]))
        cats={x["category"] for x in p["cases"]}
        self.assertIn("positive",cats)
        self.assertIn("idempotency",cats)

    def test_upgrade_claim_creates_migration_fixture(self):
        p=MOD.derive(base(
          ["papyrus","save-persistence"],
          persistence={"uses_save_state":True,"schema_version":2,"supports_upgrade":True}
        ))
        ids={x["test_id"] for x in p["cases"]}
        self.assertIn("demo.upgrade-prior-release",ids)

    def test_uninstall_claim_creates_destructive_copy_recovery_test(self):
        p=MOD.derive(base(
          ["save-persistence"],
          persistence={"uses_save_state":True,"schema_version":1,"supports_upgrade":False,"supports_uninstall":True}
        ))
        case=next(x for x in p["cases"] if x["test_id"]=="demo.uninstall-claim")
        self.assertEqual(case["category"],"recovery")
        self.assertTrue(case["fixture"]["fresh_copy"])

    def test_required_framework_creates_dependency_diagnostic_test(self):
        p=MOD.derive(base(["animation"],frameworks=[{"id":"oar","required":True}]))
        ids={x["test_id"] for x in p["cases"]}
        self.assertIn("demo.required-dependency-diagnostics",ids)

    def test_acceptance_criterion_maps_and_preserves_hint_as_notes(self):
        feature={
          "feature_id":"f",
          "acceptance_criteria":[{
            "id":"vis",
            "kind":"visual",
            "statement":"The new effect matches the intended appearance.",
            "automatable":False,
            "fixture_hint":"Whiterun exterior at noon"
          }]
        }
        p=MOD.derive(base(["texture"]),feature)
        case=next(x for x in p["cases"] if x["test_id"]=="demo.acceptance.vis")
        self.assertEqual(case["fixture"]["kind"],"custom")
        self.assertEqual(case["fixture"]["notes"],"Whiterun exterior at noon")
        self.assertEqual(case["automation"],"automated-with-supervised-evidence")
        self.assertEqual(p["coverage"]["acceptance_criteria_mapped"],1)

    def test_behavior_requires_pandora_runtime_path(self):
        p=MOD.derive(base(["behavior"]))
        case=next(x for x in p["cases"] if x["test_id"]=="demo.behavior-transition")
        self.assertIn("pandora",case["adapters"])
        self.assertIn("devbench",case["adapters"])


if __name__=="__main__":
    unittest.main()
