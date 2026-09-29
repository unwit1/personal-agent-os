"""The Orchestrator OS command reference must list every registered
`orchestrate` subcommand, so the doc cannot silently drift (DEC-0027)."""

from __future__ import annotations

import argparse
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from agent_os.orchestrator import cli  # noqa: E402

DOC = ROOT / "docs" / "orchestrator-os" / "COMMANDS.md"


def registered_subcommands() -> set[str]:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command")
    cli.register(sub)
    orchestrate = sub.choices["orchestrate"]._subparsers._group_actions[0]
    return set(orchestrate.choices)


class CommandReferenceTests(unittest.TestCase):
    def test_reference_lists_exactly_the_registered_commands(self) -> None:
        text = DOC.read_text(encoding="utf-8")
        documented = {line.split("`orchestrate ")[1].split("`")[0] for line in text.splitlines() if "`orchestrate " in line}
        registered = registered_subcommands()
        self.assertEqual(registered - documented, set(), "undocumented orchestrate subcommands")
        self.assertEqual(documented - registered, set(), "reference lists commands that no longer exist")

    def test_entrypoint_links_the_reference(self) -> None:
        entry = (ROOT / "docs" / "orchestrator-os" / "ENTRYPOINT.md").read_text(encoding="utf-8")
        self.assertIn("COMMANDS.md", entry)


if __name__ == "__main__":
    unittest.main()
