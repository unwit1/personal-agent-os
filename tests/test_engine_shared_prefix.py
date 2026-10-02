import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

import tempfile
import unittest
from unittest import mock

from agent_os.orchestrator import engine as engine_mod
from agent_os.orchestrator.engine import Orchestrator
from agent_os.orchestrator.store import RunStore


class SharedPrefixCacheTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.orch = Orchestrator(RunStore(Path(tmp.name)), session_foreman=False)
        self.orch.ledger = mock.Mock()

    def record(self, on=True, run_id="run-1"):
        return {"run_id": run_id, "goal": "g", "policy": {"shared_prefix": on}}

    def test_compiled_once_per_run_and_family(self):
        rec = self.record()
        with mock.patch.object(engine_mod.prompts, "shared_prefix", return_value="PFX\n") as sp:
            a = self.orch._run_prefix(rec, {"id": "n1", "role": "implementer"})
            b = self.orch._run_prefix(rec, {"id": "n2", "role": "repairer"})
        self.assertEqual(sp.call_count, 1)
        self.assertEqual(a.encode(), b.encode())
        self.assertEqual(self.orch.ledger.emit.call_count, 1)
        kwargs = self.orch.ledger.emit.call_args.kwargs
        self.assertEqual(kwargs["family"], "worker")
        self.assertEqual(len(kwargs["prefix_sha256"]), 64)

    def test_families_and_runs_compile_separately(self):
        def node(role):
            return {"id": role, "role": role}

        with mock.patch.object(engine_mod.prompts, "shared_prefix", side_effect=lambda r, f: f + "\n") as sp:
            self.orch._run_prefix(self.record(), node("implementer"))
            self.orch._run_prefix(self.record(), node("reviewer"))
            self.orch._run_prefix(self.record(), node("planner"))
            self.orch._run_prefix(self.record(run_id="run-2"), node("implementer"))
        self.assertEqual(sp.call_count, 4)

    def test_flag_off_compiles_nothing(self):
        with mock.patch.object(engine_mod.prompts, "shared_prefix") as sp:
            self.assertIsNone(self.orch._run_prefix(self.record(on=False), {"id": "n", "role": "implementer"}))
        sp.assert_not_called()
        self.orch.ledger.emit.assert_not_called()


if __name__ == "__main__":
    unittest.main()
