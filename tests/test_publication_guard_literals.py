import json
import unittest

from agent_os.orchestrator.control_plane import publication_attempts


def _codex(command: str) -> str:
    return json.dumps({"type": "item.completed", "item": {"type": "command_execution", "command": command}})


PS = '"C:\\windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command '


class PublicationGuardLiteralTextTests(unittest.TestCase):
    def test_doc_written_through_a_here_string_is_not_a_push(self) -> None:
        # Seen live: ev-test-suite wrote tests.md, which mentions git push, via @'...'@.
        command = PS + "\"@'\n# Tests\nThe guard blocks git push and gh pr create.\n'@ | Set-Content docs/tests.md\""
        self.assertEqual(publication_attempts([_codex(command)]), [])

    def test_heredoc_body_is_not_a_push(self) -> None:
        command = "bash -lc \"cat > notes.md <<'EOF'\nrun git push later\nEOF\""
        self.assertEqual(publication_attempts([_codex(command)]), [])

    def test_real_pushes_are_still_caught(self) -> None:
        for command in (
            "git push origin main",
            PS + "\"@'\nnotes\n'@ | Set-Content a.md; git push\"",
            PS + "\"@'\ngit push origin main\n'@ | iex\"",
            "bash <<'EOF'\ngit push\nEOF",
            "cat <<'EOF' | sh\ngit push\nEOF",
        ):
            self.assertTrue(publication_attempts([_codex(command)]), command)


if __name__ == "__main__":
    unittest.main()
