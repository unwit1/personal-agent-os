import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.orchestrator import openrouter_account as acct  # noqa: E402

KEY = "sk-or-FAKEKEY-do-not-leak-123"
POLICY = {"free_rpm": 20, "credit_threshold_usd": 10.0, "stale": False}


class FakeResponse:
    def __init__(self, payload):
        self.body = json.dumps(payload).encode()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def read(self):
        return self.body


class FakeOpener:
    def __init__(self, key, credits):
        self.key, self.credits, self.requests = key, credits, []

    def __call__(self, request, timeout=None):
        self.requests.append((request.get_method(), request.full_url, request.data,
                              request.get_header("Authorization")))
        if request.full_url == acct.OPENROUTER_KEY_URL:
            return FakeResponse({"data": self.key})
        if request.full_url == acct.OPENROUTER_CREDITS_URL:
            return FakeResponse({"data": self.credits})
        raise AssertionError("unexpected url " + request.full_url)


def state_for(total, used, rate=None, free_tier=False):
    key = {"usage": used, "is_free_tier": free_tier, "rate_limit": rate or {"requests": 20, "interval": "1m"}}
    opener = FakeOpener(key, {"total_credits": total, "total_usage": used})
    return acct.account_state(opener=opener, resolve=lambda ref: KEY), opener


class AccountTests(unittest.TestCase):
    def test_unconfigured_makes_no_request(self):
        opener = FakeOpener({}, {})
        state = acct.account_state(opener=opener, resolve=lambda ref: None)
        self.assertEqual(state, {"configured": False})
        self.assertEqual(opener.requests, [])
        self.assertFalse(acct.topup_advice(state, POLICY)["alert"])

    def test_only_get_and_key_never_leaks(self):
        state, opener = state_for(10.0, 9.5)
        self.assertEqual({r[0] for r in opener.requests}, {"GET"})
        self.assertEqual({r[1] for r in opener.requests}, set(acct.ALLOWED_URLS))
        self.assertTrue(all(r[2] is None for r in opener.requests))
        self.assertTrue(all(r[3] == "Bearer " + KEY for r in opener.requests))
        self.assertEqual(state["credits_remaining"], 0.5)
        advice = acct.topup_advice(state, POLICY)
        for blob in (repr(state), json.dumps(state), repr(advice), json.dumps(advice)):
            self.assertNotIn(KEY, blob)

    def test_errors_do_not_leak_key(self):
        def boom(request, timeout=None):
            raise RuntimeError("bad auth " + KEY)
        state = acct.account_state(opener=boom, resolve=lambda ref: KEY)
        self.assertTrue(state["configured"])
        self.assertIn("RuntimeError", state["error"])
        self.assertNotIn(KEY, json.dumps(state))

    def test_paid_up_low_balance_no_alert(self):
        state, _ = state_for(10.0, 9.9)
        advice = acct.topup_advice(state, POLICY)
        self.assertFalse(advice["alert"])
        self.assertEqual(advice["shortfall_usd"], 0.0)

    def test_below_threshold_alerts_with_shortfall(self):
        state, _ = state_for(4.25, 1.0, free_tier=True)
        advice = acct.topup_advice(state, POLICY)
        self.assertTrue(advice["alert"])
        self.assertEqual(advice["shortfall_usd"], 5.75)

    def test_stale_policy_or_unreadable_credits_never_alert(self):
        state, _ = state_for(0.0, 0.0)
        self.assertFalse(acct.topup_advice(state, dict(POLICY, stale=True))["alert"])
        self.assertFalse(acct.topup_advice(dict(state, credits_total=None), POLICY)["alert"])
        self.assertFalse(acct.topup_advice(state, {"free_rpm": 20})["alert"])

    def test_raw_record_staleness_from_verified_at(self):
        from datetime import datetime, timezone
        raw = {"free_rpm": 20, "credit_threshold_usd": 10.0, "max_age_days": 30,
               "verified_at": "2026-10-01T00:00:00Z"}
        state, _ = state_for(0.0, 0.0)
        fresh = datetime(2026, 10, 10, tzinfo=timezone.utc)
        old = datetime(2026, 12, 1, tzinfo=timezone.utc)
        self.assertTrue(acct.topup_advice(state, raw, fresh)["alert"])
        self.assertFalse(acct.topup_advice(state, raw, old)["alert"])
        self.assertFalse(acct.topup_advice(state, dict(raw, verified_at=None), fresh)["alert"])

    def test_rate_limit_discrepancy(self):
        state, _ = state_for(10.0, 0.0, rate={"requests": 100, "interval": "1m"})
        self.assertEqual(len(acct.topup_advice(state, POLICY)["discrepancies"]), 1)
        state, _ = state_for(10.0, 0.0)
        self.assertEqual(acct.topup_advice(state, POLICY)["discrepancies"], [])


if __name__ == "__main__":
    unittest.main()
