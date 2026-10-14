"""Any eligible registered provider as the session foreman: eligibility,
``use("registered")`` without re-registering, never treated as a rented pod,
and the engine's paid gate following model_profile.is_paid. No network."""

from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.orchestrator import foreman_deploy as fd  # noqa: E402
from agent_os.orchestrator.engine import Orchestrator  # noqa: E402
from agent_os.orchestrator.model_profile import is_paid  # noqa: E402
from agent_os.orchestrator.router import ProviderRegistry  # noqa: E402

ALLOWANCE_BLOCKED = {"deployment": "api", "billing": {"mode": "allowance", "overage": "blocked",
                                                      "allowance": {"unit": "requests", "amount": 500, "reset_window": "daily"}}}
ALLOWANCE_UNKNOWN = {"deployment": "api", "billing": {"mode": "allowance"}}

PROVIDERS = [
    {"id": "claude-code", "adapter": "claude_code", "models": {"fast": "haiku", "balanced": "sonnet", "reasoning": "opus"}},
    {"id": "plan-api", "adapter": "openai_api", "models": {"balanced": "m-small", "reasoning": "m-large"}, "profile": ALLOWANCE_BLOCKED},
    {"id": "metered-api", "adapter": "anthropic_api", "models": {"reasoning": "a-large"}, "profile": ALLOWANCE_UNKNOWN},
    {"id": "workers-only", "adapter": "openai_api", "models": {"fast": "w"}, "roles": ["implementer"]},
    {"id": "off", "adapter": "codex_cli", "enabled": False, "models": {"fast": "x"}},
    {"id": "synthetic", "adapter": "synthetic", "models": {"fast": "s"}},
    {"id": "down-api", "adapter": "openai_api", "models": {"fast": "d"}},
]
UP = lambda entry: entry["id"] != "down-api"  # noqa: E731


def registry() -> ProviderRegistry:
    return ProviderRegistry(providers=[json.loads(json.dumps(item)) for item in PROVIDERS], discover=False)


class Base(unittest.TestCase):
    def setUp(self) -> None:
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.registered: list[str] = []
        self.unregistered: list[str] = []

    def manager(self, reg=None) -> fd.ForemanManager:
        return fd.ForemanManager(base=self.root / "foreman", budget_home=self.root / "budget", registry=reg or registry(), probe=UP,
                                 resolve=lambda ref: None, register=lambda state: self.registered.append(state["provider_id"]),
                                 unregister=lambda state: self.unregistered.append(state["provider_id"]), inventory=lambda: [])


class EligibilityTests(Base):
    def test_only_enabled_planner_capable_available_api_or_cli_providers(self) -> None:
        eligible = {item["provider"]: item for item in fd.eligible_foremen(registry(), probe=UP)}
        self.assertEqual(set(eligible), {"claude-code", "plan-api", "metered-api"})
        self.assertEqual(eligible["plan-api"]["models"], {"balanced": "m-small", "reasoning": "m-large"})
        self.assertEqual((eligible["plan-api"]["adapter"], eligible["plan-api"]["deployment"]), ("openai_api", "api"))
        self.assertIn("allowance 500 requests", eligible["plan-api"]["billing"])
        self.assertIn("overage blocked", eligible["plan-api"]["billing"])
        self.assertEqual(eligible["claude-code"]["deployment"], "subscription")
        self.assertIn("refusal_profile", eligible["claude-code"])

    def test_paid_follows_model_profile_is_paid(self) -> None:
        eligible = {item["provider"]: item for item in fd.eligible_foremen(registry(), probe=UP)}
        self.assertFalse(eligible["plan-api"]["paid"])  # allowance with blocked overage: no usage spend
        self.assertTrue(eligible["metered-api"]["paid"])  # allowance, overage unknown: may spend
        self.assertFalse(eligible["claude-code"]["paid"])

    def test_probe_failure_excludes_and_explains(self) -> None:
        self.assertEqual(fd.eligible_foremen(registry(), probe=lambda entry: False), [])
        broken = mock.Mock(side_effect=RuntimeError("boom"))
        with mock.patch("agent_os.orchestrator.adapters.get_adapter", broken):
            self.assertEqual(fd.eligible_foremen(registry()), [])  # a crashing probe is "not available", not an error

    def test_session_foreman_entries_are_excluded(self) -> None:
        path = self.root / "providers.json"
        raw = [*PROVIDERS[:2], {"id": "foreman-qwen", "adapter": "openai_api", "models": {"reasoning": "q"}, "roles": ["planner", "inline"],
                                "options": {"base_url": "http://127.0.0.1:9"}, "session_foreman": "FMN-1"}]
        path.write_text(json.dumps({"schema_version": 1, "providers": raw}), encoding="utf-8")
        reg = ProviderRegistry(path, discover=False)
        self.assertEqual({item["provider"] for item in fd.eligible_foremen(reg, probe=UP)}, {"claude-code", "plan-api"})
        with self.assertRaisesRegex(ValueError, "session-foreman entry"):
            self.manager(reg).use("registered", provider="foreman-qwen")


class UseRegisteredTests(Base):
    def test_use_registered_sets_provider_and_model_without_registering(self) -> None:
        status = self.manager().use("registered", provider="plan-api", model="m-small", backups=[])
        self.assertEqual((status["kind"], status["status"], status["provider_id"], status["override_model"]), ("registered", "ready", "plan-api", "m-small"))
        state = fd.load_state(self.root / "foreman")
        self.assertFalse(state["registered"])
        self.assertEqual(self.registered, [])
        hold = fd.planner_hold({"foreman": {"deployment_id": state["id"]}}, self.root / "foreman")
        self.assertEqual((hold["provider"], hold["override_model"]), ("plan-api", "m-small"))
        self.manager().stop()
        self.assertEqual(self.unregistered, [])  # never removes your provider

    def test_default_model_is_the_reasoning_tier(self) -> None:
        status = self.manager().use("registered", provider="plan-api", backups=[])
        self.assertEqual((status["override_model"], status["model"]["repo"]), (None, "m-large"))

    def test_ineligible_or_unknown_provider_is_refused_with_the_reason(self) -> None:
        cases = {"workers-only": "planner role", "off": "disabled", "synthetic": "adapter", "down-api": "not available", "nope": "not registered"}
        for provider, reason in cases.items():
            with self.assertRaisesRegex(ValueError, reason, msg=provider):
                self.manager().use("registered", provider=provider)
        with self.assertRaisesRegex(ValueError, "registered provider id"):
            self.manager().use("registered")
        with self.assertRaisesRegex(ValueError, "offers"):
            self.manager().use("registered", provider="plan-api", model="opus")
        self.assertEqual(fd.load_state(self.root / "foreman"), {})

    def test_existing_callers_still_work(self) -> None:
        status = self.manager().use("claude", model="sonnet", backups=[])
        self.assertEqual((status["kind"], status["provider_id"]), ("claude", "claude-code"))
        with self.assertRaisesRegex(ValueError, "registered"):
            self.manager().use("huggingface")

    def test_reap_and_resume_never_treat_it_as_a_rented_pod(self) -> None:
        self.assertIn("registered", fd.SOURCES)
        self.assertIn("registered", fd.NOT_RENTED)
        manager = self.manager()
        manager.use("registered", provider="plan-api", backups=[])
        state = fd.load_state(self.root / "foreman")
        fd._save_state({**state, "pod_id": "stray", "watchdog_epoch": 0}, self.root / "foreman")
        self.assertFalse(manager.reap()["reaped"])
        self.assertEqual(manager.resume()["status"], "ready")
        self.assertEqual(fd.load_state(self.root / "foreman")["status"], "ready")
        self.assertEqual(self.unregistered, [])

    def test_cli_passes_the_provider_through(self) -> None:
        from agent_os.cli import main

        fake = mock.Mock()
        fake.use.return_value = {"kind": "registered"}
        with mock.patch.object(fd, "manager", return_value=fake), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main(["orchestrate", "foreman", "use", "registered", "--provider", "plan-api", "--model", "m-large"]), 0)
        self.assertEqual(fake.use.call_args.args, ("registered",))
        self.assertEqual((fake.use.call_args.kwargs["provider"], fake.use.call_args.kwargs["model"]), ("plan-api", "m-large"))


class PaidGateTests(unittest.TestCase):
    """engine._foreman_gate blocks paid foremen via _paid_blocked, which is is_paid."""

    def test_allowance_blocked_is_not_paid_blocked_but_allowance_unknown_is(self) -> None:
        reg = registry()
        fake = SimpleNamespace(registry=lambda: reg)
        blocked = set(Orchestrator._paid_blocked(fake, {"policy": {}}))
        self.assertNotIn("plan-api", blocked)
        self.assertIn("metered-api", blocked)
        self.assertEqual(blocked, {item["id"] for item in reg.providers if is_paid(item)})
        self.assertEqual(Orchestrator._paid_blocked(fake, {"policy": {"allow_paid_spend": True}}), [])

    def test_paid_registered_foreman_waits_when_paid_spend_is_off(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            manager = fd.ForemanManager(base=home, budget_home=home / "budget", registry=registry(), probe=UP, resolve=lambda ref: None,
                                        register=lambda state: None, unregister=lambda state: None, inventory=lambda: [])
            manager.use("registered", provider="metered-api", backups=[])
            record = {"foreman": {"deployment_id": fd.load_state(home)["id"]}}
            paid = set(Orchestrator._paid_blocked(SimpleNamespace(registry=registry), {"policy": {}}))
            self.assertIn("wait", fd.planner_hold(record, home, paid))  # the gate then holds or falls back to the normal planner
            self.assertEqual(fd.planner_hold(record, home, set())["provider"], "metered-api")


if __name__ == "__main__":
    unittest.main()
