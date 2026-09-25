import importlib.util
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location("readiness",ROOT/"resolve_implementation_readiness.py")
MOD=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(MOD)


def base(**extra):
    m={
      "schema_version":"skyrim-mod-project-v1",
      "project_id":"demo",
      "name":"Demo",
      "targets":["ae-1.7.x"],
      "layers":["records"],
      "outputs":[{"path":"out/Demo.esp","type":"plugin","generated":True}],
      "validation":{"required_gates":[]},
      "release":{"license":"MIT"}
    }
    m.update(extra)
    return m


class ReadinessTests(unittest.TestCase):
    def test_plugin_kind_is_research_not_user_question(self):
        p=MOD.derive(base())
        item=next(q for q in p["questions"] if q["question_id"]=="architecture.plugin-kind")
        self.assertEqual(item["disposition"],"research-required")
        self.assertNotEqual(item["disposition"],"user-required")

    def test_exact_native_runtime_comes_from_toolchain(self):
        m=base(layers=["native"],outputs=[{"path":"out/Demo.dll","type":"dll","generated":True}])
        p=MOD.derive(m,toolchain={"game":{"runtime":"1.7.104"}})
        item=next(q for q in p["questions"] if q["question_id"]=="runtime.native-exact-runtime")
        self.assertEqual(item["disposition"],"auto-resolved")
        self.assertEqual(item["answer"],"1.7.104")

    def test_missing_license_remains_user_decision(self):
        m=base(release={})
        p=MOD.derive(m)
        item=next(q for q in p["questions"] if q["question_id"]=="licensing.release-license")
        self.assertEqual(item["disposition"],"user-required")
        self.assertTrue(item["blocker"])

    def test_uninstall_defaults_to_not_proven_safe_and_test(self):
        m=base(
          layers=["papyrus","save-persistence"],
          persistence={"uses_save_state":True,"schema_version":1,"supports_upgrade":True}
        )
        p=MOD.derive(m)
        item=next(q for q in p["questions"] if q["question_id"]=="persistence.uninstall-policy")
        self.assertEqual(item["disposition"],"test-required")
        self.assertEqual(item["answer"],"not proven safe")
        self.assertTrue(item["safe_default"])

    def test_framework_version_is_research(self):
        m=base(frameworks=[{"id":"oar","required":True}])
        p=MOD.derive(m)
        item=next(q for q in p["questions"] if q["question_id"]=="framework.version-oar")
        self.assertEqual(item["disposition"],"research-required")

    def test_creative_question_is_user_required(self):
        feature={
          "feature_id":"x",
          "implementation":{"open_architecture_questions":["What visual style should the new effect use?"]},
          "acceptance_criteria":[]
        }
        p=MOD.derive(base(),feature=feature)
        item=next(q for q in p["questions"] if q["question_id"]=="creative-intent.feature-open-0")
        self.assertEqual(item["disposition"],"user-required")


if __name__=="__main__":
    unittest.main()
