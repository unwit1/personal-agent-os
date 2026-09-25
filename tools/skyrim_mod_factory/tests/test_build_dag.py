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
        d=MOD.compile_dag(m,q)
        by={n["id"]:n for n in d["nodes"]}
        self.assertEqual(by["package.staging"]["depends_on"],["runtime.regression"])
        self.assertEqual(by["release.audit"]["depends_on"],["package.staging"])

if __name__=="__main__":
    unittest.main()
