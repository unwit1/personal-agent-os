import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import unittest
from unittest import mock

from agent_os.orchestrator import prompts


def _run(flag):
    return {
        "run_id": "run-20260101T000000Z-000009",
        "goal": "ship the shared prefix",
        "project": "fixture",
        "policy": {"shared_prefix": flag},
        "operator_messages": [{"text": "prefer small diffs"}],
        "nodes": {},
    }


def _node(name, scope, command):
    return {
        "id": name,
        "role": "implementer",
        "goal": f"do the {name} work",
        "scope": scope,
        "validators": [{"kind": "command", "command": command}],
    }


NODES = [
    _node("alpha-node", ["src/alpha.py"], "python -m unittest tests.test_alpha"),
    _node("beta-node", ["src/beta.py", "tests/test_beta.py"], "python -m unittest tests.test_beta"),
]
CWDS = ["/fixture/wt/alpha-cwd", "/fixture/wt/beta-cwd"]


class SharedPrefixTests(unittest.TestCase):
    def setUp(self):
        prompts._shared_packet.cache_clear()
        packet = ("Project summary: fixture", {"selected_items": 1})
        patches = [
            mock.patch.object(prompts, "_context_packet", return_value=packet),
            mock.patch.object(prompts, "_shared_packet", return_value=packet),
        ]
        for patch in patches:
            patch.start()
            self.addCleanup(patch.stop)

    def test_prefix_is_identical_and_node_text_follows_it(self):
        run = _run(True)
        prefix = prompts.shared_prefix(run, "worker")
        for node, cwd in zip(NODES, CWDS):
            text, _ = prompts.build_measured(run, node, cwd=cwd)
            self.assertEqual(text[: len(prefix)], prefix)
            self.assertTrue(text.startswith(prefix))
            suffix = text[len(prefix):]
            for value in (node["id"], node["scope"][0], cwd):
                self.assertIn(value, suffix)
                self.assertNotIn(value, prefix)
        explicit, _ = prompts.build_measured(run, NODES[0], cwd=CWDS[0], prefix=prefix)
        self.assertEqual(explicit, prompts.build_measured(run, NODES[0], cwd=CWDS[0])[0])

    def test_prefix_ignores_nodes(self):
        run = _run(True)
        before = prompts.shared_prefix(run, "worker")
        run["nodes"] = {node["id"]: node for node in NODES}
        self.assertEqual(prompts.shared_prefix(run, "worker"), before)
        self.assertIn("prefer small diffs", before)
        self.assertIn("Do not commit, push", before)

    def test_flag_off_keeps_current_layout(self):
        for flag in (False, None):
            run = _run(flag)
            text, _ = prompts.build_measured(run, NODES[0], cwd=CWDS[0])
            self.assertTrue(text.startswith("You are the implementer for Agent OS orchestrated run"))
        run = _run(False)
        del run["policy"]
        self.assertTrue(prompts.build_measured(run, NODES[0])[0].startswith("You are the implementer"))

    def test_flag_on_keeps_every_worker_rule(self):
        off, _ = prompts.build_measured(_run(False), NODES[1], cwd=CWDS[1])
        on, _ = prompts.build_measured(_run(True), NODES[1], cwd=CWDS[1])
        on_lines = on.splitlines()
        for line in off.splitlines():
            if line.strip():
                self.assertIn(line, on_lines)


if __name__ == "__main__":
    unittest.main()
