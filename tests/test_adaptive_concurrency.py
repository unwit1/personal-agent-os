import random
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

from agent_os.orchestrator.adaptive_concurrency import ConcurrencyPolicy, next_limit  # noqa: E402

POLICY = ConcurrencyPolicy()


def spare(limit):
    return {"running": limit, "waiting": 0, "kv_usage": 0.3}


class AdaptiveConcurrencyTests(unittest.TestCase):
    def test_raise_only_after_consecutive_spare_samples(self):
        limit, mem, d = next_limit(4, spare(4), {}, POLICY)
        self.assertEqual((limit, d["reason"]), (4, "hold"))
        limit, mem, d = next_limit(limit, spare(limit), mem, POLICY)
        self.assertEqual((limit, d["reason"], d["from"], d["to"]), (6, "raise", 4, 6))
        self.assertEqual(mem, {"up": 0, "down": 0})

    def test_unused_limit_does_not_raise(self):
        mem = {}
        for _ in range(5):
            limit, mem, d = next_limit(8, {"running": 2, "waiting": 0, "kv_usage": 0.2}, mem, POLICY)
            self.assertEqual(limit, 8)

    def test_immediate_backoff_on_queueing(self):
        limit, _, d = next_limit(8, {"running": 8, "waiting": 3, "kv_usage": 0.5}, {}, POLICY)
        self.assertEqual((limit, d["reason"]), (6, "backoff_queue"))

    def test_halves_on_kv_saturation(self):
        limit, _, d = next_limit(16, {"running": 16, "waiting": 0, "kv_usage": 0.95}, {}, POLICY)
        self.assertEqual((limit, d["reason"]), (8, "backoff_kv"))
        limit, _, _ = next_limit(3, {"running": 3, "waiting": 0, "kv_usage": 0.99}, {}, POLICY)
        self.assertEqual(limit, POLICY.minimum)

    def test_no_change_in_band(self):
        mem = {"up": 1, "down": 0}
        for kv in (0.70, 0.80, 0.89):
            limit, mem, d = next_limit(8, {"running": 8, "waiting": 0, "kv_usage": kv}, mem, POLICY)
            self.assertEqual((limit, d["reason"]), (8, "hold"))
            self.assertEqual(mem, {"up": 0, "down": 0})

    def test_missing_metrics_hold(self):
        for m in (None, {}, {"running": 1, "waiting": 0}):
            limit, mem, d = next_limit(6, m, {"up": 1, "down": 0}, POLICY)
            self.assertEqual((limit, d["reason"]), (6, "no_metrics"))
            self.assertEqual(mem, {"up": 1, "down": 0})

    def test_bounds_over_random_samples(self):
        rng = random.Random(1234)
        limit, mem = POLICY.start, {}
        for _ in range(100):
            m = {
                "running": rng.randint(0, 40),
                "waiting": rng.choice([0, 0, 1, 5]),
                "kv_usage": rng.random(),
            }
            limit, mem, _ = next_limit(limit, m, mem, POLICY)
            self.assertGreaterEqual(limit, POLICY.minimum)
            self.assertLessEqual(limit, POLICY.maximum)
        limit = POLICY.maximum
        for _ in range(10):
            limit, mem, _ = next_limit(limit, spare(limit), mem, POLICY)
        self.assertEqual(limit, POLICY.maximum)

    def test_out_of_range_current_is_clamped(self):
        self.assertEqual(next_limit(100, None, {}, POLICY)[0], POLICY.maximum)
        self.assertEqual(next_limit(0, None, {}, POLICY)[0], POLICY.minimum)

    def test_no_oscillation_when_alternating_across_threshold(self):
        limit, mem = 8, {}
        seen = []
        for i in range(20):
            m = spare(limit) if i % 2 == 0 else {"running": limit, "waiting": 1, "kv_usage": 0.3}
            limit, mem, _ = next_limit(limit, m, mem, POLICY)
            seen.append(limit)
        self.assertTrue(all(b <= a for a, b in zip(seen, seen[1:])))
        self.assertEqual(seen[-1], POLICY.minimum)


if __name__ == '__main__':
    unittest.main()
