import json
import tempfile
import unittest
from pathlib import Path

from agent_os.orchestrator.prompts import build
from agent_os.orchestrator.stall import repeated_command


def _codex(command: str) -> str:
    return json.dumps({"type": "item.completed", "item": {"type": "command_execution", "command": command, "exit_code": 0}})


def _claude(command: str) -> str:
    return json.dumps({"type": "assistant", "message": {"content": [{"type": "tool_use", "name": "Bash", "input": {"command": command}}]}})


class WorkerStallTests(unittest.TestCase):
    def _write(self, lines: list[str]) -> str:
        handle = tempfile.NamedTemporaryFile("w", suffix=".log", delete=False, encoding="utf-8")
        handle.write("\n".join(lines) + "\n")
        handle.close()
        self.addCleanup(Path(handle.name).unlink)
        return handle.name

    def test_polling_the_same_process_is_a_loop(self) -> None:
        # The audit-test-failures attempt 3 shape: a poll of one PID, with
        # changing CPU numbers in the output and an occasional sleep between.
        poll = "powershell -Command '$p = Get-Process -Id 202612; if ($p) { 'RUNNING' }'"
        lines = [_codex("python -m unittest discover -s tests")] + [_codex(poll) for _ in range(10)] + [_codex("Start-Sleep -Seconds 30"), _codex(poll)]
        loop = repeated_command(self._write(lines))
        self.assertIsNotNone(loop)
        self.assertGreaterEqual(loop["count"], 9)
        self.assertIn("Get-Process", loop["command"])

    def test_claude_stream_json_is_read_too(self) -> None:
        self.assertIsNotNone(repeated_command(self._write([_claude("sleep 30; tail log") for _ in range(12)])))

    def test_varied_work_is_not_a_loop(self) -> None:
        lines = [_codex(f"rg -n pattern{i % 5} src") for i in range(12)] + ["not json", ""]
        self.assertIsNone(repeated_command(self._write(lines)))
        self.assertIsNone(repeated_command(self._write([_codex("python -m unittest") for _ in range(5)])))  # too few to judge
        self.assertIsNone(repeated_command(None))
        self.assertIsNone(repeated_command(str(Path(tempfile.gettempdir()) / "missing-stall.log")))

    def test_editing_prompt_forbids_polling_foreign_processes(self) -> None:
        run = {"run_id": "r", "goal": "g", "nodes": {}, "policy": {}}
        node = {"id": "n", "role": "implementer", "goal": "do it", "scope": ["a.py"], "validators": []}
        text = build(run, node)
        self.assertIn("Never wait on, poll, or inspect processes you did not start", text)


if __name__ == "__main__":
    unittest.main()
