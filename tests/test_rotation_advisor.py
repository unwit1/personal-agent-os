import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import unittest

from agent_os.orchestrator import rotation_advisor as ra


def call(attempt, i, o=0, p=3000, role="implementer"):
    return {"input": i, "output": o, "cache_read": 0, "prompt": p, "attempt": attempt, "role": role}


HEAVY = [call(1, 10000, 4000), call(2, 50000, 1000), call(3, 60000, 1000)]


class RotationAdvisorTests(unittest.TestCase):
    def test_constants(self):
        self.assertEqual(ra.MODE, "shadow")
        self.assertTrue(ra.SCHEMA.startswith("personal-agent/"))

    def test_heavy_series_rotates_with_exact_numbers(self):
        est = ra.estimate_boundary(HEAVY, 1, 10000, 0, 0)
        self.assertEqual(est, {
            "continue_cost": 110000,
            "rotate_cost": 30000,
            "bootstrap_overhead": 20000,
            "handoff_overhead": 4000,
            "retrieval_tokens": 6000,
            "rediscovery_penalty": 0,
            "projected_savings": 80000,
            "recommendation": "rotate",
        })
        late = ra.estimate_boundary(HEAVY, 2, 10000, 0, 0)
        self.assertEqual((late["continue_cost"], late["rotate_cost"]), (60000, 15500))
        advice = ra.advise_worker(HEAVY, 10000, 0, 0)
        self.assertEqual(advice["boundary"], 1)
        self.assertEqual(advice["recommendation"], "rotate")
        self.assertEqual(advice["estimate"], est)

    def test_handoff_cap(self):
        series = [call(1, 10000, 40000), call(2, 50000, 0)]
        est = ra.estimate_boundary(series, 1, 10000, 0, 0)
        self.assertEqual(est["handoff_overhead"], ra.HANDOFF_CAP)

    def test_short_cheap_series_continues(self):
        series = [call(1, 1000, 200, p=500), call(2, 900, 0, p=500)]
        est = ra.estimate_boundary(series, 1, 1000, 0, 0)
        self.assertEqual(est["projected_savings"], 900 - 1600)
        self.assertEqual(est["recommendation"], "continue")
        advice = ra.advise_worker(series, 1000, 0, 0)
        self.assertEqual(advice["recommendation"], "continue")
        self.assertIsNone(advice["boundary"])

    def test_retries_and_reviews_flip_to_continue(self):
        est = ra.estimate_boundary(HEAVY, 1, 10000, 20, 4)
        self.assertEqual(est["rediscovery_penalty"], 60000)
        self.assertEqual(est["projected_savings"], 20000)
        self.assertEqual(est["recommendation"], "continue")
        self.assertEqual(ra.advise_worker(HEAVY, 10000, 20, 4)["recommendation"], "continue")

    def test_single_call_series(self):
        advice = ra.advise_worker([call(1, 5000, 100)], 5000, 0, 0)
        self.assertEqual(advice, {"boundary": None, "estimate": None, "recommendation": "continue"})
        self.assertIsNone(ra.estimate_boundary([call(1, 5000)], 1, 5000, 0, 0))

    def test_same_attempt_boundary_never_rotates(self):
        series = [call(1, 10000, 4000), call(1, 50000, 0)]
        est = ra.estimate_boundary(series, 1, 10000, 0, 0)
        self.assertGreater(est["projected_savings"], 0)
        self.assertEqual(est["recommendation"], "continue")

    def test_unscored_without_bootstrap_or_retrieval(self):
        self.assertIsNone(ra.estimate_boundary(HEAVY, 1, {"reviewer": 1}, 0, 0))
        no_p = [call(1, 10000, 4000, p=None), call(2, 50000, 0, p=None)]
        self.assertIsNone(ra.estimate_boundary(no_p, 1, 10000, 0, 0))
        est = ra.estimate_boundary(no_p, 1, 10000, 0, 0, {"implementer": 2000})
        self.assertEqual(est["retrieval_tokens"], 2000)

    def test_deterministic(self):
        a = ra.advise_worker(HEAVY, 10000, 1, 1)
        b = ra.advise_worker([dict(c) for c in HEAVY], 10000, 1, 1)
        self.assertEqual(a, b)


if __name__ == "__main__":
    unittest.main()
