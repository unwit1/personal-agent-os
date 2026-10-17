"""Editing workers may run their own validators and read-only commands.

Measured 2026-10-17 over 48 real worker calls: 36 hit permission denials (107
in all; 26 were the task's own test run, 7 the scratch-directory mkdir the
worker rules ask for), and 13 ended blocked_on_host only because the worker
could not run its validator.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.orchestrator.engine import _worker_allowed_tools  # noqa: E402
from agent_os.orchestrator.model import DEFAULT_POLICY  # noqa: E402
from agent_os.orchestrator.prompts import _WORKER_RULES_TAIL  # noqa: E402

PROVIDER = {"options": {"allowed_tools": ["WebSearch"]}}


def record(**policy) -> dict:
    return {"policy": {**DEFAULT_POLICY, **policy}}


def node(role="implementer", validators=None) -> dict:
    return {"role": role, "validators": validators or []}


class WorkerAllowedToolsTests(unittest.TestCase):
    def test_test_runner_validator_is_allowed_by_prefix(self) -> None:
        validators = [{"kind": "command", "command": ["python", "-m", "pytest", "-q", "-p", "no:cacheprovider", "tests/test_a.py"]}]
        tools = _worker_allowed_tools(record(), node(validators=validators), PROVIDER)
        self.assertIn("Bash(python -m pytest:*)", tools)
        self.assertIn("Bash(git diff:*)", tools)
        self.assertIn("Bash(mkdir -p .agent-os-scratch:*)", tools)
        self.assertEqual(tools[0], "WebSearch")

    def test_other_validator_commands_are_allowed_exactly(self) -> None:
        tools = _worker_allowed_tools(record(), node(validators=[{"kind": "command", "command": "python agent.py validate"}]), PROVIDER)
        self.assertIn("Bash(python agent.py validate)", tools)
        self.assertNotIn("Bash(python agent.py validate:*)", tools)

    def test_default_validators_apply_when_the_node_has_none(self) -> None:
        tools = _worker_allowed_tools(record(default_validators=[{"kind": "command", "command": "python -m unittest tests.test_a"}]), node(), {})
        self.assertIn("Bash(python -m unittest:*)", tools)

    def test_reviewers_and_planners_keep_provider_permissions_only(self) -> None:
        for role in ("reviewer", "planner"):
            self.assertEqual(_worker_allowed_tools(record(), node(role=role), PROVIDER), ["WebSearch"])

    def test_policy_switch_restores_provider_permissions(self) -> None:
        self.assertEqual(_worker_allowed_tools(record(worker_self_check=False), node(), PROVIDER), ["WebSearch"])
        self.assertTrue(DEFAULT_POLICY["worker_self_check"])

    def test_nothing_that_mutates_or_runs_arbitrary_code_is_preapproved(self) -> None:
        tools = _worker_allowed_tools(record(), node(), {})
        for risky in ("Bash(rm", "Bash(git push", "Bash(git commit", "Bash(python -c", "Bash(find", "Bash(sed"):
            self.assertFalse(any(tool.startswith(risky) for tool in tools), risky)

    def test_worker_rules_say_a_denied_command_is_not_a_host_action(self) -> None:
        text = " ".join(_WORKER_RULES_TAIL)
        self.assertIn("If a command is denied, do not retry", text)
        self.assertIn("not a host action", text)


if __name__ == "__main__":
    unittest.main()
