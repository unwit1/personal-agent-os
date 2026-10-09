import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from agent_os.orchestrator.adapters.base import AgentLaunchRequest
from agent_os.orchestrator.adapters.codex_cli import PYTEST_TMP_PLUGIN, WIN_SANDBOX_SHIM, CodexCliAdapter


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


    def test_worker_env_loads_the_pytest_tmp_plugin_on_windows_only(self) -> None:
        adapter = CodexCliAdapter({"id": "codex", "options": {}})
        with tempfile.TemporaryDirectory() as tmp:
            env = adapter._env(self._request(tmp), {})
            off = adapter._env(self._request(tmp), {"windows_tempdir_shim": False})
        if os.name == "nt":
            self.assertIn(PYTEST_TMP_PLUGIN, env["PYTEST_PLUGINS"].split(","))
        else:
            self.assertNotIn(PYTEST_TMP_PLUGIN, env.get("PYTEST_PLUGINS", ""))
        self.assertNotIn(PYTEST_TMP_PLUGIN, off.get("PYTEST_PLUGINS", ""))
        self.assertTrue((WIN_SANDBOX_SHIM / f"{PYTEST_TMP_PLUGIN}.py").is_file())

    def test_pytest_plugin_relaxes_only_tmp_path_folder_mode_for_workers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "test_probe.py").write_text(
                "import pathlib\n"
                "from _pytest.tmpdir import TempPathFactory\n"
                "def test_probe(tmp_path):\n"
                "    (tmp_path / 'f.txt').write_text('ok')\n"
                "    print('WRAPPED', getattr(TempPathFactory.mktemp, 'agent_os_inherited_acl', False))\n"
                "    print('PATH_MKDIR_RESTORED', pathlib.Path.mkdir.__qualname__ == 'Path.mkdir')\n",
                encoding="utf-8")
            base = {**os.environ, "PYTHONPATH": str(WIN_SANDBOX_SHIM), "PYTEST_PLUGINS": PYTEST_TMP_PLUGIN}
            argv = [sys.executable, "-m", "pytest", "-q", "-s", "-p", "no:cacheprovider", "--basetemp", str(Path(tmp, "bt")), "test_probe.py"]
            worker = subprocess.run(argv, cwd=tmp, env={**base, "AGENT_OS_ORCHESTRATOR_WORKER": "1"}, capture_output=True, text=True)
            host = subprocess.run(argv, cwd=tmp, env={k: v for k, v in base.items() if k != "AGENT_OS_ORCHESTRATOR_WORKER"}, capture_output=True, text=True)
        self.assertEqual(worker.returncode, 0, worker.stdout + worker.stderr)
        self.assertIn(f"WRAPPED {os.name == 'nt'}", worker.stdout)
        self.assertIn("PATH_MKDIR_RESTORED True", worker.stdout)  # patched only during folder creation
        self.assertEqual(host.returncode, 0, host.stdout + host.stderr)
        self.assertIn("WRAPPED False", host.stdout)  # outside a worker nothing changes


if __name__ == "__main__":
    unittest.main()
