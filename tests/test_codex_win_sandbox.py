import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from agent_os.orchestrator.adapters.base import AgentLaunchRequest
from agent_os.orchestrator.adapters.codex_cli import WIN_SANDBOX_SHIM, CodexCliAdapter


class CodexWindowsTempdirShimTests(unittest.TestCase):
    def _request(self, tmp: str) -> AgentLaunchRequest:
        return AgentLaunchRequest(run_id="r", node_id="n", role="implementer", cwd=tmp, prompt_path=str(Path(tmp) / "p.md"), output_dir=tmp,
                                  capability_class="fast", effort="low", model="gpt-x", provider_effort=None, read_only=False, timeout_seconds=60)

    def test_worker_env_carries_the_shim_on_windows_only(self) -> None:
        adapter = CodexCliAdapter({"id": "codex", "options": {}})
        with tempfile.TemporaryDirectory() as tmp:
            env = adapter._env(self._request(tmp), {})
            off = adapter._env(self._request(tmp), {"windows_tempdir_shim": False})
        if os.name == "nt":
            self.assertEqual(env["PYTHONPATH"].split(os.pathsep)[0], str(WIN_SANDBOX_SHIM))
        else:
            self.assertNotIn(str(WIN_SANDBOX_SHIM), env.get("PYTHONPATH", ""))
        self.assertNotIn(str(WIN_SANDBOX_SHIM), off.get("PYTHONPATH", ""))
        self.assertTrue((WIN_SANDBOX_SHIM / "sitecustomize.py").is_file())

    def test_shim_changes_only_tempfile_mode_for_workers(self) -> None:
        probe = ("import os, tempfile, sitecustomize; print(sitecustomize.__file__); "
                 "print(tempfile._os.mkdir is os.mkdir)")  # no folder made: a sandboxed run could not remove an owner-only one
        base = {**os.environ, "PYTHONPATH": str(WIN_SANDBOX_SHIM)}
        worker = subprocess.run([sys.executable, "-c", probe], env={**base, "AGENT_OS_ORCHESTRATOR_WORKER": "1"}, capture_output=True, text=True, check=True).stdout.split()
        host = subprocess.run([sys.executable, "-c", probe], env={k: v for k, v in base.items() if k != "AGENT_OS_ORCHESTRATOR_WORKER"}, capture_output=True, text=True, check=True).stdout.split()
        self.assertEqual(Path(worker[0]).parent, WIN_SANDBOX_SHIM)
        self.assertEqual(worker[1], "False" if os.name == "nt" else "True")
        self.assertEqual(host[1], "True")  # outside a worker nothing changes


if __name__ == "__main__":
    unittest.main()
