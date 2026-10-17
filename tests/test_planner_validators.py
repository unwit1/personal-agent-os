"""Planned validators that would collect the whole test suite are dropped.

A planner validator running ``pytest tests`` collected every test module, so one
unrelated import error aborted the validator on every escalation. Whole-suite
commands are dropped with a note unless they are canonical project commands."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.orchestrator.planner import _collects_whole_suite, _planned_validators  # noqa: E402

PATTERNS = [r"python -m pytest .*", r"python -m unittest .*"]


class PlannedValidatorWholeSuiteTests(unittest.TestCase):
    def plan(self, commands, project_commands=(), patterns=PATTERNS):
        notes: list[str] = []
        task = {"id": "t1", "validators": list(commands)}
        validators = _planned_validators(task, list(patterns), list(project_commands), notes)
        return validators, notes

    def test_whole_suite_commands_are_dropped_with_note(self):
        for command in ("python -m pytest tests -k resolver", "python -m unittest discover"):
            with self.subTest(command=command):
                validators, notes = self.plan([command])
                self.assertEqual(validators, [])
                self.assertEqual(
                    notes,
                    [f"t1: dropped validator {command} that collects the whole test suite; name test modules"],
                )

    def test_named_modules_are_kept(self):
        for command in ("python -m pytest tests/test_source_resolvers.py", "python -m unittest tests.test_x"):
            with self.subTest(command=command):
                validators, notes = self.plan([command])
                self.assertEqual(notes, [])
                self.assertEqual(len(validators), 1)
                self.assertEqual(validators[0]["command"], command.split())

    def test_whole_suite_project_command_is_kept(self):
        command = "python -m pytest tests -k resolver"
        validators, notes = self.plan([command], project_commands=[command], patterns=[])
        self.assertEqual(notes, [])
        self.assertEqual(validators[0]["command"], command.split())

    def test_help_and_version_flags_are_kept(self):
        for command in ("python -m unittest -h", "python -m pytest --help"):
            with self.subTest(command=command):
                validators, notes = self.plan([command])
                self.assertEqual(notes, [])
                self.assertEqual(validators[0]["command"], command.split())

    def test_collects_whole_suite_classification(self):
        self.assertFalse(_collects_whole_suite(["python", "-m", "unittest", "-h"]))
        self.assertTrue(_collects_whole_suite(["pytest"]))
        self.assertTrue(_collects_whole_suite(["python", "-m", "pytest", "tests/"]))
        self.assertTrue(_collects_whole_suite(["python", "-m", "pytest", "-k", "tests/test_x.py", "."]))
        self.assertFalse(_collects_whole_suite(["python", "-m", "pytest", "tests/test_x.py::T"]))
        self.assertFalse(_collects_whole_suite(["python", "-m", "unittest", "tests.test_x.T.test_y"]))
        self.assertFalse(_collects_whole_suite(["python", "agent.py", "validate"]))


if __name__ == "__main__":
    unittest.main()
