import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.local_paths import is_gitignored_local_path  # noqa: E402
from agent_os.paths import ROOT  # noqa: E402


class LocalPathPrivacyTests(unittest.TestCase):
    def test_outside_repository_is_safe(self) -> None:
        self.assertTrue(is_gitignored_local_path(Path.home() / ".agent-os" / "synthetic"))

    def test_default_boundary_allows_only_agent_local(self) -> None:
        self.assertTrue(is_gitignored_local_path(ROOT / ".agent-local" / "synthetic.jsonl"))
        self.assertFalse(is_gitignored_local_path(ROOT / ".tmp" / "synthetic.json"))
        self.assertFalse(is_gitignored_local_path(ROOT / "projects" / "synthetic.json"))

    def test_callers_can_preserve_an_explicit_ignored_root_policy(self) -> None:
        self.assertTrue(
            is_gitignored_local_path(
                ROOT / ".tmp" / "synthetic.json",
                allowed_roots=(".agent-local", ".tmp"),
            )
        )
        self.assertFalse(
            is_gitignored_local_path(
                ROOT / ".agent-os" / "synthetic.json",
                allowed_roots=(".agent-local", ".tmp"),
            )
        )


if __name__ == "__main__":
    unittest.main()
