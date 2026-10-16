"""A timed-out validator must never take down the process that started it."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.orchestrator.adapters.base import kill_tree
from agent_os.orchestrator.validators import run_validator

SLEEP = [sys.executable, "-c", "import time; time.sleep(60)"]


class KillTreeSafetyTests(unittest.TestCase):
    def test_a_child_in_our_own_process_group_is_killed_without_killing_us(self) -> None:
        child = subprocess.Popen(SLEEP)  # same process group as this test
        self.addCleanup(child.kill)
        kill_tree(child.pid)
        child.wait(timeout=10)
        self.assertIsNotNone(child.returncode)  # and we are still here to assert it

    @unittest.skipIf(os.name == "nt", "process groups are POSIX")
    def test_validator_commands_run_in_their_own_process_group(self) -> None:
        code = "import os; print(os.getpgid(0))"
        with tempfile.TemporaryDirectory() as tmp:
            result = run_validator({"kind": "command", "name": "group", "command": [sys.executable, "-c", code]}, tmp)
        self.assertTrue(result["passed"])
        self.assertNotIn(str(os.getpgrp()), result["detail"] or "")


if __name__ == "__main__":
    unittest.main()
