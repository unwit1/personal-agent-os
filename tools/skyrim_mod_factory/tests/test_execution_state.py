import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location("execute_build_dag",ROOT/"execute_build_dag.py")
MOD=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)

class ExecutionStateTests(unittest.TestCase):
    def test_file_fingerprint_is_stable_and_content_sensitive(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/"file.txt"
            path.write_text("one",encoding="utf-8")
            first=MOD.path_fingerprint(str(path))
            second=MOD.path_fingerprint(str(path))
            self.assertEqual(first,second)
            path.write_text("two",encoding="utf-8")
            third=MOD.path_fingerprint(str(path))
            self.assertNotEqual(first["sha256"],third["sha256"])

    def test_directory_fingerprint_changes_when_child_changes(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)/"tree"
            root.mkdir()
            (root/"a.txt").write_text("a",encoding="utf-8")
            first=MOD.path_fingerprint(str(root))
            (root/"a.txt").write_text("b",encoding="utf-8")
            second=MOD.path_fingerprint(str(root))
            self.assertEqual(first["kind"],"directory")
            self.assertEqual(first["file_count"],1)
            self.assertNotEqual(first["sha256"],second["sha256"])

    def test_missing_path_has_explicit_missing_fingerprint(self):
        with tempfile.TemporaryDirectory() as td:
            missing=Path(td)/"missing"
            fp=MOD.path_fingerprint(str(missing))
            self.assertFalse(fp["exists"])
            self.assertEqual(fp["kind"],"missing")
            self.assertNotIn("sha256",fp)

    def test_execution_state_atomic_round_trip(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/"state.json"
            state=MOD.new_execution_state("fixture","build-1")
            state["nodes"]["preflight.manifest"]={
                "fingerprint":"a"*64,
                "status":"passed",
                "updated_at":"2026-09-24T00:00:00+00:00",
                "step_record":{"id":"preflight.manifest","status":"passed"},
                "output_fingerprints":[],
            }
            MOD.save_execution_state(path,state)
            loaded=MOD.load_execution_state(path,"fixture")
            self.assertEqual(loaded["build_id"],"build-1")
            self.assertEqual(
                loaded["nodes"]["preflight.manifest"]["fingerprint"],
                "a"*64,
            )
            self.assertFalse(any(p.name.endswith(".tmp") for p in path.parent.iterdir()))

    def test_execution_state_rejects_wrong_project(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/"state.json"
            MOD.save_execution_state(
                path,
                MOD.new_execution_state("project-a","build-1"),
            )
            with self.assertRaises(ValueError):
                MOD.load_execution_state(path,"project-b")

    def test_node_fingerprint_changes_with_declared_input(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            inp=root/"input.txt"
            inp.write_text("one",encoding="utf-8")
            node={
                "id":"generate.fixture",
                "depends_on":[],
                "adapters":[],
                "gates":[],
                "outputs":[],
            }
            context={"nodes":{"generate.fixture":{"inputs":[str(inp)]}}}
            kwargs=dict(
                manifest={"project_id":"fixture"},
                quality={},
                lock={},
                context=context,
                capability_map={},
                adapter_dir=root/"adapters",
                gate_registry={},
                dependency_fingerprints={},
            )
            first=MOD.compute_node_fingerprint(node,**kwargs)
            inp.write_text("two",encoding="utf-8")
            second=MOD.compute_node_fingerprint(node,**kwargs)
            self.assertNotEqual(first,second)

    def test_dependency_fingerprint_invalidates_downstream(self):
        node={
            "id":"validate.fixture",
            "depends_on":["generate.fixture"],
            "adapters":[],
            "gates":[],
            "outputs":[],
        }
        common=dict(
            manifest={"project_id":"fixture"},
            quality={},
            lock={},
            context={},
            capability_map={},
            adapter_dir=Path("."),
            gate_registry={},
        )
        first=MOD.compute_node_fingerprint(
            node,dependency_fingerprints={"generate.fixture":"a"*64},**common
        )
        second=MOD.compute_node_fingerprint(
            node,dependency_fingerprints={"generate.fixture":"b"*64},**common
        )
        self.assertNotEqual(first,second)

    def test_reuse_requires_matching_output_content(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            out=root/"output.txt"
            out.write_text("good",encoding="utf-8")
            node={
                "id":"generate.fixture",
                "depends_on":[],
                "adapters":[],
                "gates":[],
                "outputs":[str(out)],
            }
            context={}
            state=MOD.new_execution_state("fixture","build-1")
            step={"id":"generate.fixture","status":"passed","issues":[]}
            MOD.checkpoint_node(
                state,
                node=node,
                fingerprint="c"*64,
                step=step,
                context=context,
            )
            reused=MOD.reusable_prior_step(node,"c"*64,state)
            self.assertIsNotNone(reused)
            self.assertTrue(reused["evidence"]["resumed_from_state"])

            out.write_text("changed",encoding="utf-8")
            self.assertIsNone(MOD.reusable_prior_step(node,"c"*64,state))

    def test_failed_or_review_checkpoint_is_never_reused(self):
        node={"id":"fixture","depends_on":[],"adapters":[],"gates":[],"outputs":[]}
        for status in ("failed","needs-review","skipped"):
            state=MOD.new_execution_state("fixture","build-1")
            state["nodes"]["fixture"]={
                "fingerprint":"d"*64,
                "status":status,
                "updated_at":"2026-09-24T00:00:00+00:00",
                "step_record":{"id":"fixture","status":status},
                "output_fingerprints":[],
            }
            self.assertIsNone(MOD.reusable_prior_step(node,"d"*64,state))

if __name__=="__main__":
    unittest.main()
