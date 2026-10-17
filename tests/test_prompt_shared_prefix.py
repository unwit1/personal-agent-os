import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import unittest
from collections import Counter
from unittest import mock

from agent_os.orchestrator import prompts


def _run(flag):
    run = {
        "run_id": "run-20260101T000000Z-000009",
        "goal": "ship the shared prefix",
        "project": "fixture",
        "operator_messages": [{"text": "prefer small diffs"}],
        "nodes": {},
    }
    if flag is not None:
        run["policy"] = {"shared_prefix": flag}
    return run


def _impl(name, scope, command):
    return {
        "id": name,
        "role": "implementer",
        "goal": f"do the {name} work",
        "scope": scope,
        "validators": [{"kind": "command", "command": command}],
    }


WORKERS = [
    (_impl("alpha-node", ["src/alpha.py"], "python -m unittest tests.test_alpha"), "/fixture/wt/alpha-cwd"),
    (_impl("beta-node", ["src/beta.py", "tests/test_beta.py"], "python -m unittest tests.test_beta"), "/fixture/wt/beta-cwd"),
]
REPAIRER = ({"id": "gamma-node.repair1", "role": "repairer", "goal": "fix gamma", "scope": ["src/gamma.py"]}, "/fixture/wt/gamma-cwd")
REVIEWERS = [
    ({"id": "alpha-node.review", "role": "reviewer", "goal": "review alpha", "subject": "alpha-node"}, "/fixture/wt/alpha-review"),
    ({"id": "beta-node.review", "role": "reviewer", "goal": "review beta", "subject": "beta-node"}, "/fixture/wt/beta-review"),
]
PLANNERS = [
    ({"id": "plan-a", "role": "planner", "goal": "plan a"}, "/fixture/wt/plan-a"),
    ({"id": "plan-b", "role": "planner", "goal": "plan b"}, "/fixture/wt/plan-b"),
]
FINDINGS = [{"id": "R1-1", "severity": "high", "path": "src/gamma.py", "summary": "wrong", "recommended_action": "fix it"}]
PACKET = ("Project summary: fixture", {"selected_items": 1})


def _lines(text):
    return Counter(line for line in text.splitlines() if line.strip())


class SharedPrefixTests(unittest.TestCase):
    def setUp(self):
        patch = mock.patch.object(prompts, "_context_packet", return_value=PACKET)
        patch.start()
        self.addCleanup(patch.stop)

    def test_reviewer_is_told_which_findings_are_already_decided(self):
        open_one = {"id": "R2-1", "severity": "high", "path": "src/a.py", "summary": "still open", "disposition": "open"}
        settled = [
            {"id": "R1-4", "severity": "low", "path": "tests/t.py", "summary": "shim hides items", "disposition": "follow_up", "disposition_reason": None},
            {"id": "R1-5", "severity": "medium", "path": "src/a.py", "summary": "path regex", "disposition": "rejected", "disposition_reason": "paths are quoted upstream"},
        ]
        with mock.patch.object(prompts, "_sibling_lines", return_value=[]):
            text = prompts.build(_run(None), REVIEWERS[0][0], diff="+x", findings=[open_one, *settled])
        unresolved, decided = text.split("Already decided", 1)
        self.assertIn("[R2-1]", unresolved)
        self.assertNotIn("[R1-4]", unresolved)
        self.assertIn("[R1-4] follow_up", decided)
        self.assertIn("paths are quoted upstream", decided)
        with mock.patch.object(prompts, "_sibling_lines", return_value=[]):
            plain = prompts.build(_run(None), REVIEWERS[0][0], diff="+x", findings=[open_one])
        self.assertNotIn("Already decided", plain)

    def test_worker_prefix_is_identical_and_node_text_follows_it(self):
        run = _run(True)
        prefix = prompts.shared_prefix(run, "worker")
        for node, cwd in WORKERS:
            text, _ = prompts.build_measured(run, node, cwd=cwd)
            self.assertEqual(text[: len(prefix)], prefix)
            suffix = text[len(prefix):]
            for value in (node["id"], node["scope"][0], node["validators"][0]["command"], cwd):
                self.assertIn(value, suffix)
                self.assertNotIn(value, prefix)
            explicit, _ = prompts.build_measured(run, node, cwd=cwd, prefix=prefix)
            self.assertEqual(explicit, text)
        self.assertIn("prefer small diffs", prefix)
        self.assertIn("Do not commit, push", prefix)

    def test_prefix_is_identical_across_nodes_in_every_family(self):
        run = _run(True)
        groups = {"worker": [*WORKERS, (REPAIRER[0], REPAIRER[1])], "reviewer": REVIEWERS, "planner": PLANNERS}
        for family, nodes in groups.items():
            prefix = prompts.shared_prefix(run, family)
            self.assertTrue(prefix.endswith("\n\n"))
            for node, cwd in nodes:
                text, _ = prompts.build_measured(run, node, cwd=cwd, findings=FINDINGS if node["role"] == "repairer" else None)
                self.assertTrue(text.startswith(prefix), node["id"])
                self.assertNotIn(node["id"], prefix)
                self.assertNotIn(cwd, prefix)

    def test_prefix_ignores_nodes_and_cwd(self):
        run = _run(True)
        before = {family: prompts.shared_prefix(run, family) for family in ("worker", "reviewer", "planner")}
        run["nodes"] = {node["id"]: node for node, _ in [*WORKERS, *REVIEWERS]}
        for family, expected in before.items():
            self.assertEqual(prompts.shared_prefix(run, family), expected)

    def test_flag_on_changes_only_the_order_of_lines(self):
        cases = [(*item, None) for item in WORKERS] + [(*REPAIRER, FINDINGS), (*REVIEWERS[0], FINDINGS), (*PLANNERS[0], None)]
        for messages in ([{"text": "prefer small diffs"}], []):
            off_run, on_run = _run(False), _run(True)
            off_run["operator_messages"] = on_run["operator_messages"] = messages
            on_run["nodes"] = off_run["nodes"] = {node["id"]: node for node, _ in WORKERS}
            for node, cwd, findings in cases:
                kwargs = {"cwd": cwd, "findings": findings, "diff": "+x", "repo_map": "map"}
                off, off_measure = prompts.build_measured(off_run, node, **kwargs)
                on, on_measure = prompts.build_measured(on_run, node, **kwargs)
                self.assertEqual(_lines(on), _lines(off), node["id"])
                self.assertEqual(on_measure, off_measure)
                self.assertTrue(on.endswith(prompts._contract(node["role"])))

    def test_flag_on_keeps_per_node_project_context(self):
        seen = []

        def packet(project, task, budget):
            seen.append((project, task, budget))
            return PACKET

        with mock.patch.object(prompts, "_context_packet", side_effect=packet):
            for node, cwd in [*WORKERS, *REVIEWERS]:
                text, measurement = prompts.build_measured(_run(True), node, cwd=cwd)
                self.assertIn("Project context:\nProject summary: fixture", text)
                self.assertEqual(measurement, PACKET[1])
                self.assertEqual(seen[-1], ("fixture", node["goal"], 1200))

    def test_flag_off_keeps_current_layout(self):
        for flag in (False, None):
            for node, cwd in [*WORKERS, REPAIRER, *REVIEWERS, *PLANNERS]:
                text, _ = prompts.build_measured(_run(flag), node, cwd=cwd)
                self.assertTrue(text.startswith(f"You are the {node['role'].replace('_', ' ')} for Agent OS orchestrated run"))
        run = _run(False)
        del run["policy"]
        text = prompts.build_measured(run, WORKERS[0][0], cwd=WORKERS[0][1])[0]
        self.assertTrue(text.startswith("You are the implementer for Agent OS orchestrated run"))
        self.assertLess(text.index("Overall goal:"), text.index("Your assignment"))

    def test_prefix_argument_is_ignored_when_flag_is_off(self):
        node, cwd = WORKERS[0]
        self.assertEqual(
            prompts.build_measured(_run(False), node, cwd=cwd, prefix="IGNORED\n"),
            prompts.build_measured(_run(False), node, cwd=cwd),
        )


if __name__ == "__main__":
    unittest.main()
