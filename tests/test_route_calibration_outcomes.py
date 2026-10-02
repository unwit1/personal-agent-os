import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

from agent_os.orchestrator.route_calibration import MODE, SCHEMA, node_outcomes  # noqa: E402


def ev(type_, node, seq, **data):
    return {"type": type_, "node": node, "seq": seq, "data": data}


class NodeOutcomesTest(unittest.TestCase):
    def test_constants(self):
        self.assertEqual(MODE, "shadow")
        self.assertTrue(SCHEMA.endswith("route-calibration/v1"))

    def test_clean_pass(self):
        out = node_outcomes([
            ev("model_completed", "a", 1, role="implementer", capability_class="cheap",
               effort="low", provider="p"),
            ev("tests_completed", "a", 2, passed=False),
            ev("tests_completed", "a", 3, passed=True),
            ev("review_completed", "r", 4, subject="a.repair1", material_findings=0,
               verdict="approved"),
        ])
        self.assertEqual(len(out), 1)
        o = out[0]
        self.assertEqual(o["family"], "orchestrator-implementer")
        self.assertEqual(o["initial_class"], "cheap")
        self.assertEqual(o["final_class"], "cheap")
        self.assertTrue(o["validation_passed"])
        self.assertTrue(o["reviewed"])
        self.assertIs(o["review_clean"], True)
        self.assertIs(o["cheap_route_passed"], True)

    def test_escalation_and_fail(self):
        out = node_outcomes([
            "junk", {"type": "retry", "node": "b", "data": 1},
            ev("model_failed", "b", 2, role="implementer", capability_class="cheap"),
            ev("model_escalated", "b", 3, to="strong/high"),
            ev("retry", "b", 4),
            ev("fallback", "b", 5),
        ])
        o = out[0]
        self.assertEqual((o["escalations"], o["final_class"]), (1, "strong"))
        self.assertEqual((o["retries"], o["fallbacks"]), (1, 1))
        self.assertIs(o["cheap_route_passed"], False)
        self.assertIsNone(o["provider"])

    def test_blocked_review_unlabeled_and_reviewer_excluded(self):
        out = node_outcomes([
            ev("model_completed", "z", 1, role="reviewer"),
            ev("retry", "orphan", 1),
            ev("model_completed", "c", 1, role="implementer"),
            ev("model_completed", "d", 1, role="implementer"),
            ev("review_completed", "r", 2, subject="d", material_findings=1, verdict="x"),
        ])
        self.assertEqual([o["node"] for o in out], ["c", "d"])
        self.assertIsNone(out[0]["cheap_route_passed"])
        self.assertIs(out[1]["review_clean"], False)
        self.assertIs(out[1]["cheap_route_passed"], False)


if __name__ == "__main__":
    unittest.main()
