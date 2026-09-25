import importlib.util
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location("dag",ROOT/"compile_build_dag.py")
MOD=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(MOD)

def fixture(layers):
    m={"project_id":"demo","layers":layers,"outputs":[]}
    q={
      "gates":["G00","G01","G23","G25","G27","G29"],
      "adapters":{"preferred":["xedit","mutagen","caprica","pynifly","directxtex"],"supporting":["devbench"]},
      "invalidation_triggers":["source change"],
      "reasons":{"G02":["layer:records"],"G07":["layer:papyrus"],"G12":["layer:mesh"]}
    }
    return m,q

class DagTests(unittest.TestCase):
    def test_independent_layers_generate_from_same_source_lock(self):
        m,q=fixture(["records","papyrus"])
        d=MOD.compile_dag(m,q)
        by={n["id"]:n for n in d["nodes"]}
        self.assertEqual(by["generate.records"]["depends_on"],["source.lock"])
        self.assertEqual(by["generate.papyrus"]["depends_on"],["source.lock"])

    def test_cross_layer_waits_for_all_validators(self):
        m,q=fixture(["records","mesh"])
        d=MOD.compile_dag(m,q)
        by={n["id"]:n for n in d["nodes"]}
        self.assertIn("validate.records",by["integrate.cross-layer"]["depends_on"])
        self.assertIn("validate.mesh",by["integrate.cross-layer"]["depends_on"])

    def test_release_waits_for_runtime_and_package(self):
        m,q=fixture(["records"])
        q["gates"].append("G26")
        d=MOD.compile_dag(m,q)
        by={n["id"]:n for n in d["nodes"]}
        self.assertEqual(by["package.staging"]["depends_on"],["runtime.regression"])
        self.assertEqual(by["release.audit"]["depends_on"],["package.staging"])

    def test_native_configure_precedes_native_build(self):
        m,q=fixture(["native"])
        q["adapters"]["preferred"] += ["commonlib-cmake-configure","commonlib-cmake-build"]
        d=MOD.compile_dag(m,q)
        by={n["id"]:n for n in d["nodes"]}
        self.assertEqual(by["generate.native-configure"]["depends_on"],["source.lock"])
        self.assertEqual(by["generate.native"]["depends_on"],["generate.native-configure"])
        self.assertIn("commonlib-cmake-build",by["generate.native"]["adapters"])

    def test_declared_runtime_adapter_reaches_runtime_nodes(self):
        m,q=fixture(["papyrus"])
        q["gates"].append("G26")
        q["adapters"]["preferred"].append("skytest")
        d=MOD.compile_dag(m,q)
        by={n["id"]:n for n in d["nodes"]}
        self.assertIn("skytest",by["runtime.smoke"]["adapters"])
        self.assertIn("skytest",by["runtime.regression"]["adapters"])

    def test_devbench_runtime_is_wrapped_by_mo2_closed_loop_harness(self):
        m,q=fixture(["records"])
        q["gates"].append("G26")
        d=MOD.compile_dag(m,q)
        by={n["id"]:n for n in d["nodes"]}
        self.assertIn("mo2-devbench-runtime",by["runtime.smoke"]["adapters"])
        self.assertIn("mo2-devbench-runtime",by["runtime.regression"]["adapters"])
        self.assertNotIn("devbench",by["runtime.smoke"]["adapters"])
        self.assertNotIn("devbench",by["runtime.regression"]["adapters"])

    def test_explicit_composite_runtime_adapter_is_not_duplicated(self):
        m,q=fixture(["records"])
        q["gates"].append("G26")
        q["adapters"]["preferred"].append("mo2-devbench-runtime")
        d=MOD.compile_dag(m,q)
        by={n["id"]:n for n in d["nodes"]}
        self.assertEqual(
            by["runtime.smoke"]["adapters"].count("mo2-devbench-runtime"),
            1,
        )


    def test_runtime_gate_assignments_follow_quality_plan(self):
        m,q=fixture(["native"])
        q["gates"] += ["G19","G20","G26"]
        d=MOD.compile_dag(m,q)
        by={n["id"]:n for n in d["nodes"]}
        self.assertEqual(by["runtime.smoke"]["gates"],["G19","G26"])
        self.assertEqual(by["runtime.regression"]["gates"],["G20","G26"])
        self.assertNotIn("G21",by["runtime.regression"]["gates"])
        self.assertNotIn("G27",by["runtime.regression"]["gates"])

    def test_save_migration_gate_only_attaches_when_required(self):
        m,q=fixture(["save-persistence"])
        q["gates"] += ["G21","G26"]
        d=MOD.compile_dag(m,q)
        by={n["id"]:n for n in d["nodes"]}
        self.assertEqual(by["runtime.smoke"]["gates"],["G26"])
        self.assertEqual(by["runtime.regression"]["gates"],["G21","G26"])


    def test_no_runtime_gate_omits_mandatory_runtime_nodes(self):
        m,q=fixture(["records"])
        d=MOD.compile_dag(m,q)
        by={n["id"]:n for n in d["nodes"]}
        self.assertNotIn("runtime.smoke",by)
        self.assertNotIn("runtime.regression",by)
        self.assertEqual(by["package.staging"]["depends_on"],["integrate.gates"])

    def test_smoke_only_runtime_gate_omits_regression_stage(self):
        m,q=fixture(["records"])
        q["gates"].append("G19")
        d=MOD.compile_dag(m,q)
        by={n["id"]:n for n in d["nodes"]}
        self.assertIn("runtime.smoke",by)
        self.assertNotIn("runtime.regression",by)
        self.assertEqual(by["package.staging"]["depends_on"],["runtime.smoke"])


if __name__=="__main__":
    unittest.main()
