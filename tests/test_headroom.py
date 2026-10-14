"""Plan headroom (headroom.py), its routing effect and sensitive-run
exclusion. No real usage sources: readers and clocks are faked."""

from __future__ import annotations

import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.orchestrator import headroom  # noqa: E402
from agent_os.orchestrator.model import PolicyError, merge_policy  # noqa: E402
from agent_os.orchestrator.model_profile import is_sensitive, sensitive_problem  # noqa: E402
from agent_os.orchestrator.router import ProviderRegistry, select  # noqa: E402

NOW = 1_800_000_000.0
HOUR = 3600.0


def plan(used: float, resets_in_hours: float, minutes: int = 300, observed: float = NOW) -> dict:
    return {"windows": [headroom.window("5h" if minutes == 300 else "weekly", used, NOW + resets_in_hours * HOUR, minutes)],
            "observed_at": headroom._iso(observed), "overage": "blocked"}


class ParserTests(unittest.TestCase):
    def test_codex_rate_limits(self) -> None:
        parsed = headroom.parse_codex({"primary": {"used_percent": 84.0, "window_minutes": 300, "resets_at": NOW + HOUR},
                                       "secondary": {"used_percent": 50.0, "window_minutes": 10080, "resets_at": NOW + 48 * HOUR},
                                       "credits": {"has_credits": False, "unlimited": False}, "plan_type": "plus"}, NOW)
        self.assertEqual([(item["name"], item["used"]) for item in parsed["windows"]], [("5h", 0.84), ("weekly", 0.5)])
        self.assertEqual((parsed["overage"], parsed["plan"]), ("blocked", "plus"))

    def test_claude_rate_limit_event(self) -> None:
        parsed = headroom.parse_claude({"type": "rate_limit_event", "rate_limit_info": {
            "overageStatus": "rejected", "isUsingOverage": False,
            "unifiedWindows": {"five_hour": {"utilization": 0.59, "resetsAt": NOW + HOUR}, "seven_day": {"utilization": 0.72, "resetsAt": NOW + 72 * HOUR}}}}, NOW)
        self.assertEqual([(item["name"], item["used"], item["minutes"]) for item in parsed["windows"]], [("5h", 0.59, 300), ("weekly", 0.72, 10080)])
        self.assertEqual(parsed["overage"], "blocked")

    def test_nanogpt_uses_used_over_limit_not_percent(self) -> None:
        parsed = headroom.parse_nanogpt({"active": True, "limits": {"weeklyInputTokens": 60_000_000, "dailyInputTokens": None},
                                         "allowOverage": False, "dailyInputTokens": None,
                                         "weeklyInputTokens": {"used": 30_000_000, "remaining": 30_000_000, "percentUsed": 50, "resetAt": (NOW + HOUR) * 1000},
                                         "routing": {"paidOverageEnabled": False}}, NOW)
        self.assertEqual(len(parsed["windows"]), 1)
        self.assertEqual((parsed["windows"][0]["used"], parsed["windows"][0]["minutes"], parsed["overage"]), (0.5, 10080, "blocked"))
        self.assertEqual(parsed["windows"][0]["resets_at"], headroom._iso(NOW + HOUR))

    def test_codex_reader_finds_last_rate_limits(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            day = Path(tmp) / "2026" / "10" / "14"
            day.mkdir(parents=True)
            lines = [json.dumps({"timestamp": "2026-10-14T10:00:00Z", "payload": {"type": "token_count", "rate_limits": {"primary": {"used_percent": 10, "window_minutes": 300, "resets_at": NOW}}}}),
                     json.dumps({"timestamp": "2026-10-14T11:00:00Z", "payload": {"type": "token_count", "rate_limits": {"primary": {"used_percent": 40, "window_minutes": 300, "resets_at": NOW}}}}),
                     json.dumps({"timestamp": "2026-10-14T12:00:00Z", "payload": {"type": "token_count", "rate_limits": {"primary": None, "secondary": None}}}),
                     "not json"]
            (day / "rollout.jsonl").write_text("\n".join(lines), encoding="utf-8")
            self.assertEqual(headroom.read_codex(Path(tmp))["windows"][0]["used"], 0.4)
            self.assertIsNone(headroom.read_codex(Path(tmp) / "missing"))


class AssessTests(unittest.TestCase):
    def test_states(self) -> None:
        self.assertEqual(headroom.assess(plan(0.99, 2), NOW)["state"], "exhausted")
        self.assertEqual(headroom.assess(plan(0.99, 2), NOW)["until"], headroom._iso(NOW + 2 * HOUR))
        self.assertEqual(headroom.assess(plan(0.90, 2), NOW)["state"], "tight")  # under 15% left
        self.assertEqual(headroom.assess(plan(0.60, 4), NOW)["state"], "tight")  # 60% used, 20% elapsed
        self.assertEqual(headroom.assess(plan(0.40, 4), NOW)["state"], "ok")  # ahead of pace, but over half left
        self.assertEqual(headroom.assess(plan(0.30, 2), NOW)["state"], "ok")
        expiring = headroom.assess(plan(0.20, 10, minutes=10080), NOW)  # weekly, 10 h left, 80% unused
        self.assertEqual((expiring["state"], expiring["multiplier"]), ("expiring", 0.6))

    def test_reset_window_counts_as_empty_and_stale_is_unknown(self) -> None:
        self.assertEqual(headroom.assess(plan(0.99, -1), NOW)["state"], "ok")
        self.assertEqual(headroom.assess(plan(0.99, 2, observed=NOW - 7 * HOUR), NOW)["state"], "unknown")
        self.assertEqual(headroom.assess(None, NOW), {"state": "unknown", "multiplier": 1.0, "detail": "no usage data"})

    def test_tight_outranks_expiring(self) -> None:
        snapshot = {"windows": [headroom.window("5h", 0.9, NOW + HOUR, 300), headroom.window("weekly", 0.2, NOW + 10 * HOUR, 10080)],
                    "observed_at": headroom._iso(NOW)}
        self.assertEqual(headroom.assess(snapshot, NOW)["state"], "tight")


class SourceAndRefreshTests(unittest.TestCase):
    def test_source_keys(self) -> None:
        self.assertEqual(headroom.source_key({"adapter": "codex_cli"}), "codex")
        self.assertEqual(headroom.source_key({"adapter": "claude_code"}), "claude")
        self.assertIsNone(headroom.source_key({"adapter": "claude_code", "options": {"env": {"ANTHROPIC_BASE_URL": "https://bridge"}}}))
        nano = {"adapter": "openai_api", "options": {"base_url": "https://n/sub/v1", "secret_ref": "secrets://nanogpt/subscription",
                                                     "catalog": {"service": "nanogpt", "endpoint": "subscription"}}}
        self.assertEqual(headroom.source_key(nano), "nanogpt|https://n/sub/v1|secrets://nanogpt/subscription")
        self.assertIsNone(headroom.source_key({"adapter": "openai_api", "options": {"base_url": "https://x"}}))

    def test_shared_nanogpt_allowance_is_read_once_and_cached(self) -> None:
        options = {"base_url": "https://n/sub/v1", "secret_ref": "secrets://nanogpt/subscription", "catalog": {"service": "nanogpt", "endpoint": "subscription"}}
        providers = [{"id": "nano-a", "adapter": "openai_api", "options": options}, {"id": "nano-b", "adapter": "openai_api", "options": options},
                     {"id": "codex", "adapter": "codex_cli"}, {"id": "nano-off", "adapter": "openai_api", "options": options, "enabled": False}]
        calls = []

        def nano(base_url, secret_ref):
            calls.append(("nano", base_url, secret_ref))
            return plan(0.99, 5, minutes=10080)

        def codex():
            calls.append(("codex",))
            return plan(0.2, 4)

        with tempfile.TemporaryDirectory() as tmp:
            first = headroom.for_providers(providers, Path(tmp), now=NOW, readers={"nanogpt": nano, "codex": codex})
            again = headroom.for_providers(providers, Path(tmp), now=NOW + 10, readers={"nanogpt": nano, "codex": codex})
        self.assertEqual(calls, [("codex",), ("nano", "https://n/sub/v1", "secrets://nanogpt/subscription")])
        self.assertEqual((first["nano-a"]["state"], first["nano-b"]["state"], first["codex"]["state"]), ("exhausted", "exhausted", "ok"))
        self.assertNotIn("nano-off", first)  # disabled entries do not route, so they are not listed
        self.assertEqual(again, first)

    def test_failed_read_keeps_last_snapshot(self) -> None:
        providers = [{"id": "codex", "adapter": "codex_cli"}]
        with tempfile.TemporaryDirectory() as tmp:
            headroom.for_providers(providers, Path(tmp), now=NOW, readers={"codex": lambda: plan(0.5, 4)})
            later = headroom.for_providers(providers, Path(tmp), now=NOW + 120, readers={"codex": lambda: None})
        self.assertEqual(later["codex"]["windows"][0]["used"], 0.5)


def registry() -> ProviderRegistry:
    return ProviderRegistry(providers=[
        {"id": "cheap", "adapter": "codex_cli", "models": {"balanced": "c"}, "costs": {"balanced": 1.0}},
        {"id": "dear", "adapter": "claude_code", "models": {"balanced": "d"}, "costs": {"balanced": 2.0}},
    ])


class RouterTests(unittest.TestCase):
    def test_no_headroom_keeps_cheapest(self) -> None:
        self.assertEqual(select(registry(), capability_class="balanced", effort="low", role="implementer")["provider"], "cheap")

    def test_tight_plan_yields_to_provider_with_room(self) -> None:
        choice = select(registry(), capability_class="balanced", effort="low", role="implementer",
                        headroom={"cheap": {"state": "tight", "multiplier": 3.0, "detail": "5h 90% used"}})
        self.assertEqual(choice["provider"], "dear")

    def test_expiring_plan_is_preferred(self) -> None:
        choice = select(registry(), capability_class="balanced", effort="low", role="implementer",
                        headroom={"dear": {"state": "expiring", "multiplier": 0.4, "detail": "weekly 10% used"}})
        self.assertEqual(choice["provider"], "dear")
        self.assertTrue(any("cost x0.4" in note for note in choice["notes"]))

    def test_exhausted_plan_is_skipped_even_when_overridden(self) -> None:
        plans = {"cheap": {"state": "exhausted", "multiplier": 1.0, "until": "2026-10-19T00:00:00+00:00"}}
        self.assertEqual(select(registry(), capability_class="balanced", effort="low", role="implementer", headroom=plans)["provider"], "dear")
        overridden = select(registry(), capability_class="balanced", effort="low", role="implementer", headroom=plans, override={"provider": "cheap"})
        self.assertEqual(overridden["provider"], "dear")
        self.assertTrue(any("exhausted until 2026-10-19" in note for note in overridden["notes"]))


class SensitiveTests(unittest.TestCase):
    def test_policy_values(self) -> None:
        self.assertEqual(merge_policy()["sensitive_data"], "auto")
        self.assertTrue(merge_policy({"sensitive_data": True})["sensitive_data"])
        with self.assertRaises(PolicyError):
            merge_policy({"sensitive_data": "maybe"})

    def test_auto_follows_repository_list(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.assertTrue(is_sensitive({"sensitive_data": "auto"}, r"C:\Users\x\GitHub\HR GUI", Path(tmp)))
            self.assertFalse(is_sensitive({"sensitive_data": "auto"}, r"C:\Users\x\GitHub\brickmen", Path(tmp)))
            self.assertFalse(is_sensitive({"sensitive_data": False}, r"C:\Users\x\GitHub\HR GUI", Path(tmp)))
            self.assertTrue(is_sensitive({"sensitive_data": True}, None, Path(tmp)))
            (Path(tmp) / "sensitive-repos.json").write_text(json.dumps(["Brickmen"]), encoding="utf-8")
            self.assertTrue(is_sensitive({}, r"C:\Users\x\GitHub\brickmen", Path(tmp)))
            self.assertFalse(is_sensitive({}, r"C:\Users\x\GitHub\HR GUI", Path(tmp)))

    def test_only_own_subscriptions_and_local_models_see_sensitive_data(self) -> None:
        self.assertIsNone(sensitive_problem({"adapter": "claude_code"}))
        self.assertIsNone(sensitive_problem({"adapter": "codex_cli"}))
        self.assertIsNone(sensitive_problem({"adapter": "openai_api", "options": {"base_url": "http://127.0.0.1:11434/v1"}}))
        nano = {"adapter": "openai_api", "options": {"base_url": "https://nano-gpt.com/api/subscription/v1"},
                "profile": {"deployment": "api", "billing": {"mode": "allowance", "overage": "blocked"}, "privacy": {"weights_location": "third_party"}}}
        self.assertEqual(sensitive_problem(nano), "third-party host")
        self.assertEqual(sensitive_problem({"adapter": "openai_api", "options": {"base_url": "https://openrouter.ai/api/v1"}}), "api deployment")


if __name__ == "__main__":
    unittest.main()
