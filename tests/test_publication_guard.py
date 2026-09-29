"""IMP-0014: external publication requires operator approval."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from agent_os.orchestrator import control_plane  # noqa: E402
from agent_os.orchestrator.adapters import synthetic  # noqa: E402
from agent_os.orchestrator.adapters.base import AgentLaunchRequest, ProviderStatus  # noqa: E402
from agent_os.orchestrator.adapters.claude_code import lean_flags  # noqa: E402
from agent_os.orchestrator.adapters.codex_cli import CodexCliAdapter  # noqa: E402

from test_orchestrator import OrchestratorFixture  # noqa: E402


def command_event(command: str) -> str:
    return json.dumps({"type": "item.completed", "item": {"type": "command_execution", "command": command}})


class PatternTests(unittest.TestCase):
    def test_publishing_commands_are_detected(self) -> None:
        for command in ("git push origin main", "npm publish", "twine upload dist/*", "gh release create v1", "curl -X POST https://example.com/api", "docker push img"):
            with self.subTest(command):
                self.assertEqual(control_plane.publication_attempts([command_event(command)]), [command])
        self.assertEqual(control_plane.publication_attempts(["$ git push --force"]), ["git push --force"])

    def test_ordinary_commands_and_prose_are_not(self) -> None:
        texts = [command_event("git status"), command_event("python -m unittest"), command_event("curl https://example.com"),
                 json.dumps({"type": "item.completed", "item": {"type": "agent_message", "text": "I did not git push"}}), "I did not run git push."]
        self.assertEqual(control_plane.publication_attempts(texts), [])

    def test_only_command_execution_items_count(self) -> None:
        # A non-command event that happens to carry a "command" field and
        # mention command_execution must not count as an executed command.
        other = json.dumps({"type": "item.completed", "item": {"type": "file_change", "command": "git push", "note": "no command_execution here"}})
        self.assertEqual(control_plane.publication_attempts([other]), [])

    def test_check_detail(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            clean = Path(tmp) / "clean.log"
            clean.write_text(command_event("git status") + "
", encoding="utf-8")
            self.assertIsNone(control_plane.publication_check([clean])["detail"])
            bad = Path(tmp) / "bad.log"
            bad.write_text(command_event("git push origin main") + "
", encoding="utf-8")
            detail = control_plane.publication_check([bad])["detail"]
            self.assertIn("operator approval", detail)
            self.assertIn("git push origin main", detail)

    def test_check_reads_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "stdout.log"
            log.write_text(command_event("git push") + "\n", encoding="utf-8")
            self.assertFalse(control_plane.publication_check([log, Path(tmp) / "missing.log"])["passed"])


class AdapterDefaultTests(unittest.TestCase):
    def test_claude_denies_publishing_tools_for_editing_workers(self) -> None:
        editing = lean_flags({}, {"--tools": True, "--disallowedTools": True}, read_only=False)
        self.assertIn("--disallowedTools", editing)
        self.assertIn("Bash(git push:*)", editing[editing.index("--disallowedTools") + 1])
        self.assertNotIn("--disallowedTools", lean_flags({"allow_publishing": True}, {"--disallowedTools": True}, read_only=False))
        self.assertNotIn("--disallowedTools", lean_flags({}, {"--disallowedTools": True}, read_only=True))

    def test_codex_editing_workers_have_no_network(self) -> None:
        adapter = CodexCliAdapter({"id": "codex", "options": {}})
        status = ProviderStatus("codex", True, executable="codex", features={"--sandbox": True})
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(CodexCliAdapter, "probe", return_value=status):
            request = AgentLaunchRequest(run_id="r", node_id="n", role="implementer", cwd=tmp, prompt_path=str(Path(tmp) / "p.md"), output_dir=tmp,
                                         capability_class="fast", effort="low", model="m", provider_effort="low", read_only=False)
            argv = adapter.resolve_invocation(request).argv
        self.assertIn("sandbox_workspace_write.network_access=false", argv)


class EngineGuardTests(OrchestratorFixture):
    def run_with_push(self, **policy) -> dict:
        def script(request, call):
            if request.role == "reviewer":
                return {"structured": {"status": "done", "verdict": "approved", "findings": []}}
            out = Path(request.output_dir)
            out.mkdir(parents=True, exist_ok=True)
            (out / "stdout.log").write_text(command_event("git push origin HEAD") + "\n", encoding="utf-8")
            return {"edits": {"a/x.txt": "x\n"}, "structured": {"status": "done", "summary": "pushed"}}

        for name in self.providers:
            synthetic.SCRIPTS[name] = script
        run_id = self.create([self.task("a")], max_stage_retries=0, max_escalations=0, provider_failover=False, **policy)
        self.engine.run_loop(run_id, max_ticks=40)
        return self.node(run_id, "a")

    def test_attempted_push_fails_validation(self) -> None:
        node = self.run_with_push()
        guard = [item for item in node["validation"]["evidence"] if item.get("name") == "publication-guard"]
        self.assertTrue(guard and not guard[0]["passed"])
        self.assertFalse(node["integrated"])

    def test_operator_can_allow_publication(self) -> None:
        node = self.run_with_push(allow_worker_publication=True)
        self.assertNotIn("publication-guard", [item.get("name") for item in node["validation"]["evidence"]])
        self.assertTrue(node["integrated"])


if __name__ == "__main__":
    unittest.main()
