import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.orchestrator import free_quota
from agent_os.orchestrator.free_quota import Governor

POLICY = {"free_rpm": 3, "daily_free_requests_low": 10, "daily_free_requests_high": 20,
          "failed_requests_count": True, "reset": "00:00Z"}
T0 = datetime(2026, 10, 1, 12, 0, 0, tzinfo=timezone.utc)
M = "x/y:free"


def ev(ts, outcome="success", model=M):
    return {"ts": ts.strftime("%Y-%m-%dT%H:%M:%SZ"), "model": model, "outcome": outcome}


class Clock:
    def __init__(self, t):
        self.t = t

    def __call__(self):
        return self.t


class FreeQuotaTests(unittest.TestCase):
    def gov(self, events=(), clock=None, policy=POLICY, **kw):
        return Governor(policy, now=clock or Clock(T0), events=list(events), **kw)

    def test_daily_cap_with_reserve(self):
        events = [ev(T0 - timedelta(minutes=5 + i)) for i in range(7)]
        g = self.gov(events, reserve=2)
        self.assertEqual(g.remaining()["daily_left"], 1)
        self.assertTrue(g.can_spend(M)[0])
        g = self.gov(events + [ev(T0 - timedelta(hours=1))], reserve=2)
        ok, reason = g.can_spend(M)
        self.assertFalse(ok)
        self.assertIn("daily", reason)
        self.assertEqual(self.gov(high_tier=True).remaining()["daily_left"], 20)

    def test_failed_requests_flag(self):
        events = [ev(T0 - timedelta(hours=1), "rate_limited") for _ in range(4)]
        self.assertEqual(self.gov(events).remaining()["daily_left"], 6)
        policy = dict(POLICY, failed_requests_count=False)
        self.assertEqual(self.gov(events, policy=policy).remaining()["daily_left"], 10)

    def test_rpm_window(self):
        events = [ev(T0 - timedelta(seconds=s)) for s in (5, 20, 59)]
        clock = Clock(T0)
        g = self.gov(events, clock)
        self.assertEqual(g.remaining()["minute_left"], 0)
        self.assertEqual(g.can_spend(M), (False, "per-minute limit reached"))
        clock.t = T0 + timedelta(seconds=10)  # oldest (5s ago) is now 15s... 59s ago is 69s old
        self.assertEqual(g.remaining()["minute_left"], 1)
        self.assertTrue(g.can_spend(M)[0])

    def test_retry_budget(self):
        g = self.gov(retry_budget=1)
        self.assertTrue(g.can_spend(M, retry=1)[0])
        self.assertFalse(g.can_spend(M, retry=2)[0])

    def test_backoff_growth_and_cap(self):
        g = self.gov(backoff_base=10, backoff_cap=50, failure_threshold=2)
        self.assertEqual([g.backoff_seconds(n) for n in range(1, 7)], [0, 10, 20, 40, 50, 50])

    def test_backoff_blocks_then_clears(self):
        fails = [ev(T0 - timedelta(seconds=100 - i), "provider_error") for i in range(3)]
        clock = Clock(T0)
        g = self.gov(fails, clock, backoff_base=60, backoff_cap=600, failure_threshold=2)
        # 3 failures -> 120s after the last (T0-98s) -> blocked until T0+22s
        ok, reason = g.can_spend(M)
        self.assertFalse(ok)
        self.assertIn("backoff", reason)
        self.assertTrue(g.can_spend("other/model:free")[0])
        clock.t = T0 + timedelta(seconds=30)
        self.assertTrue(g.can_spend(M)[0])
        g._events.append(ev(T0, "success"))
        self.assertEqual(g.consecutive_failures(M), 0)

    def test_reset_rollover(self):
        late = datetime(2026, 10, 1, 23, 59, 0, tzinfo=timezone.utc)
        events = [ev(late - timedelta(minutes=10 + i)) for i in range(10)]
        clock = Clock(late)
        g = self.gov(events, clock)
        self.assertEqual(g.remaining()["daily_left"], 0)
        self.assertEqual(g.remaining()["reset_at"], "2026-10-02T00:00:00Z")
        clock.t = datetime(2026, 10, 2, 0, 0, 1, tzinfo=timezone.utc)
        self.assertEqual(g.remaining()["daily_left"], 10)
        self.assertEqual(g.remaining()["reset_at"], "2026-10-03T00:00:00Z")

    def test_policy_reset_time(self):
        g = self.gov(policy=dict(POLICY, reset="06:00Z"))
        self.assertEqual(g.remaining()["reset_at"], "2026-10-02T06:00:00Z")

    def test_expiring_capacity(self):
        events = [ev(T0 - timedelta(minutes=5 + i)) for i in range(4)]
        g = self.gov(events, reserve=2)
        self.assertEqual(g.expiring_capacity(T0), 4)
        self.assertEqual(g.expiring_capacity(T0 + timedelta(days=1)), 8)

    def test_record_appends_without_text(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            entry = free_quota.record({"model": M, "outcome": "success"}, home)
            self.assertTrue(entry["event_id"].startswith("FQE-"))
            with self.assertRaises(ValueError):
                free_quota.record({"model": M, "outcome": "success", "prompt": "hi"}, home)
            g = Governor(POLICY, now=Clock(datetime.now(timezone.utc)), home=home)
            g.record({"model": M, "outcome": "success"})
            self.assertEqual(len(free_quota.read_events(home)), 2)


if __name__ == "__main__":
    unittest.main()
