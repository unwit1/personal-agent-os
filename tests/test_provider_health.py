"""IMP-0005: shared provider health (quota cooldowns + unavailable breaker),
used by engine runs and by orchestrate delegate."""

from __future__ import annotations

import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.orchestrator import provider_health as health  # noqa: E402
from agent_os.orchestrator.adapters import synthetic  # noqa: E402
from agent_os.orchestrator.delegate import delegate  # noqa: E402
from agent_os.orchestrator.router import ProviderRegistry  # noqa: E402

# Evening local time, so "resets 7:10pm"-style times fall later today or tomorrow.
NOW = datetime(2026, 9, 28, 18, 0, tzinfo=timezone.utc).astimezone().replace(hour=18, minute=0)


def local(iso: str) -> datetime:
    return datetime.fromisoformat(iso).astimezone()


class ResetParsingTests(unittest.TestCase):
    """Messages actually seen during the 2026-09-28 bootstrap (FAIL-0001)."""

    def test_codex_try_again_at(self) -> None:
        reset = local(health.quota_reset("You've hit your usage limit. Upgrade to Pro ... or try again at 9:12 PM.", NOW))
        self.assertEqual((reset.hour, reset.minute, reset.date()), (21, 12, NOW.date()))

    def test_claude_session_resets_time(self) -> None:
        reset = local(health.quota_reset("You've hit your session limit · resets 7:10pm (America/New_York)", NOW))
        self.assertEqual((reset.hour, reset.minute), (19, 10))

    def test_claude_weekly_resets_date(self) -> None:
        reset = local(health.quota_reset("You've hit your weekly limit · resets Oct 3, 6pm (America/New_York)", NOW))
        self.assertEqual((reset.month, reset.day, reset.hour), (10, 3, 18))

    def test_relative_and_retry_after(self) -> None:
        self.assertEqual(local(health.quota_reset("rate limited, retry after 30 seconds", NOW)) - NOW, timedelta(seconds=30))
        self.assertEqual(local(health.quota_reset("try again in 2 hours", NOW)) - NOW, timedelta(hours=2))
        self.assertEqual(local(health.quota_reset("429", NOW, retry_after=12)) - NOW, timedelta(seconds=12))
        self.assertEqual(local(health.quota_reset("limit reached", NOW)) - NOW, timedelta(hours=1))

    def test_past_time_rolls_to_tomorrow(self) -> None:
        reset = local(health.quota_reset("try again at 9:00 AM", NOW))
        self.assertEqual(reset.date(), NOW.date() + timedelta(days=1))


class BreakerTests(unittest.TestCase):
    def test_three_unavailable_in_window_open_then_expire(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            t0 = datetime(2026, 9, 29, 12, 0, tzinfo=timezone.utc)
            self.assertIsNone(health.record_unavailable(home, "codex", "down", t0))
            self.assertIsNone(health.record_unavailable(home, "codex", "down", t0 + timedelta(minutes=1)))
            self.assertEqual(health.cooling(home, t0 + timedelta(minutes=1)), set())
            opened = health.record_unavailable(home, "codex", "down", t0 + timedelta(minutes=2))
            self.assertIsNotNone(opened)
            self.assertEqual(health.cooling(home, t0 + timedelta(minutes=3)), {"codex"})
            # Half-open by expiry: after the cooldown the provider is probed again.
            self.assertEqual(health.cooling(home, t0 + timedelta(minutes=18)), set())

    def test_old_failures_fall_out_of_the_window(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            t0 = datetime(2026, 9, 29, 12, 0, tzinfo=timezone.utc)
            health.record_unavailable(home, "codex", "down", t0)
            health.record_unavailable(home, "codex", "down", t0 + timedelta(minutes=1))
            self.assertIsNone(health.record_unavailable(home, "codex", "down", t0 + timedelta(minutes=30)))


class DelegateDeferralTests(unittest.TestCase):
    def setUp(self) -> None:
        synthetic.reset()
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name)

    def tearDown(self) -> None:
        synthetic.reset()
        self.tmp.cleanup()

    def registry(self, *ids: str) -> ProviderRegistry:
        return ProviderRegistry(providers=[{"id": pid, "adapter": "synthetic", "options": {"script": pid}, "models": {"fast": f"{pid}-fast"}, "costs": {"fast": index + 1}} for index, pid in enumerate(ids)])

    def test_quota_failure_cools_provider_and_next_call_routes_elsewhere(self) -> None:
        synthetic.SCRIPTS["cheap"] = lambda request, call: {"failure": "quota", "detail": "usage limit, try again at 11:59 PM"}
        synthetic.SCRIPTS["other"] = lambda request, call: {"structured": {"ok": True}}
        registry = self.registry("cheap", "other")
        first = delegate("x", task_family="t", registry=registry, home=self.home, cwd=self.home, record=False)
        self.assertEqual(first["status"], "failed")
        self.assertIn("cooldown_until", first)
        second = delegate("x", task_family="t", registry=registry, home=self.home, cwd=self.home, record=False)
        self.assertEqual((second["status"], second["selection"]["provider"]), ("passed", "other"))

    def test_all_providers_cooling_is_reported_as_deferred(self) -> None:
        synthetic.SCRIPTS["cheap"] = lambda request, call: {"failure": "quota", "detail": "usage limit"}
        registry = self.registry("cheap")
        delegate("x", task_family="t", registry=registry, home=self.home, cwd=self.home, record=False)
        again = delegate("x", task_family="t", registry=registry, home=self.home, cwd=self.home, record=False)
        self.assertEqual(again["status"], "unroutable")
        self.assertIn("cheap", again["deferred_until"])


if __name__ == "__main__":
    unittest.main()
