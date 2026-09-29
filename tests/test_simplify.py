"""MIE-0011 simplification engine: candidates on a fixture repository."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.orchestrator import simplify  # noqa: E402

LOADER = '''def load_{name}(path):
    """Load records."""
    rows = []
    for line in open(path):
        if line.strip():
            rows.append(line.strip())
    rows.sort()
    total = len(rows)
    return rows[:total]
'''


class SimplifyTests(unittest.TestCase):
    def test_candidates_on_fixture(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pkg = root / "src" / "agent_os"
            pkg.mkdir(parents=True)
            (root / "tests").mkdir()
            (pkg / "__init__.py").write_text("", encoding="utf-8")
            (pkg / "cli.py").write_text("from . import used\n\n\ndef main():\n    return used.helper()\n", encoding="utf-8")
            (pkg / "used.py").write_text("def helper():\n    return 1\n\n\ndef forgotten_public():\n    return 2\n", encoding="utf-8")
            (pkg / "orphan.py").write_text("X = 1\n", encoding="utf-8")
            (pkg / "a.py").write_text(LOADER.format(name="alpha"), encoding="utf-8")
            (pkg / "b.py").write_text(LOADER.format(name="beta"), encoding="utf-8")
            (root / "tests" / "test_used.py").write_text("from agent_os import a, b, used\n", encoding="utf-8")
            (root / "pyproject.toml").write_text('[project]\nname = "x"\ndependencies = ["keyring>=25", "requests>=2"]\n', encoding="utf-8")
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            report = simplify.build(root)
        dead = {item["module"] for item in report["dead_module_candidates"]}
        self.assertEqual(dead, {"agent_os.orphan"})
        unused = {(item["module"], item["name"]) for item in report["unused_public_functions"]}
        self.assertIn(("agent_os.used", "forgotten_public"), unused)
        self.assertNotIn(("agent_os.used", "helper"), unused)
        self.assertEqual([sorted(group["functions"]) for group in report["duplicates"]], [["agent_os.a:load_alpha", "agent_os.b:load_beta"]])
        self.assertEqual({dep["requirement"]: dep["candidate"] for dep in report["dependencies"]}, {"keyring>=25": "remove", "requests>=2": "remove"})

    def test_fingerprint_ignores_names_and_docstrings_but_not_structure(self) -> None:
        import ast

        first = ast.parse(LOADER.format(name="x")).body[0]
        second = ast.parse(LOADER.format(name="y").replace('"""Load records."""', '"""Other doc."""')).body[0]
        changed = ast.parse(LOADER.format(name="z").replace("rows.sort()", "rows.reverse()")).body[0]
        self.assertEqual(simplify.body_fingerprint(first), simplify.body_fingerprint(second))
        self.assertNotEqual(simplify.body_fingerprint(first), simplify.body_fingerprint(changed))


if __name__ == "__main__":
    unittest.main()
