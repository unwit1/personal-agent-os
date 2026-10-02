import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.orchestrator import free_routing
from agent_os.orchestrator.router import ProviderRegistry

FREE = {"prompt": "0", "completion": "0"}
TRAINS_FALSE = {"trains_on_prompts": False, "source": "policy:test@v2#data_policies[0]", "verified_at": "2026-10-01T00:00:00Z"}


def provider(provider_id: str, **extra) -> dict:
    entry = {
        "id": provider_id,
        "adapter": "synthetic",
        "models": {
            "fast": f"{provider_id}-fast",
            "balanced": f"{provider_id}-balanced",
            "reasoning": f"{provider_id}-reasoning",
            "frontier": f"{provider_id}-frontier",
        },
        "effort_map": {"none": "minimal", "low": "lo", "medium": "med", "high": "hi"},
        "max_concurrency": 2,
    }
    entry.update(extra)
    return entry


def model(slug: str, **extra) -> dict:
    return {"slug": slug, "revision": f"{slug}-r1", "context_length": 65536, "supports_tools": True,
            "supports_structured_output": True, "pricing": dict(FREE), "data_policy": dict(TRAINS_FALSE), **extra}


def record(slug: str, low: float, n: int = 30, status: str = "proven") -> dict:
    return {"task_family": "unit_test_generation", "model": slug, "revision": f"{slug}-r1", "n": n,
            "wilson95": [low, min(1.0, low + 0.2)], "status": status}


class FakeGovernor:
    def __init__(self, blocked: dict | None = None) -> None:
        self.blocked = blocked or {}
        self.asked: list[str] = []

    def can_spend(self, model: str, retry: int = 0):
        self.asked.append(model)
        if model in self.blocked:
            return False, self.blocked[model]
        return True, "ok"

    def remaining(self):
        return {"daily_left": 40, "minute_left": 10, "reset_at": "2026-10-02T00:00:00Z"}


CATALOG = {"snapshot_id": "FCS-test", "models": [model("org/a:free"), model("org/b:free")]}
SPECS = [record("org/a:free", 0.8), record("org/b:free", 0.6)]
POLICY = {"source": "policy:test@v2", "protected_globs": ["policy/**", "src/agent_os/orchestrator/control_plane.py"]}


def task(**extra) -> dict:
    base = {"task_family": "unit_test_generation", "role": "test_author", "effort": "low",
            "validators": ["python -m unittest tests.test_x"], "scope": ["tests/test_x.py"],
            "sensitivity": "internal", "capability_class": "fast", "run_id": "R1", "node_id": "n1"}
    base.update(extra)
    return base


class EligibilityTest(unittest.TestCase):
    def check(self, **extra):
        item = task(**extra)
        return free_routing.eligible(item, sensitivity=item["sensitivity"], protected_globs=POLICY["protected_globs"])

    def test_low_risk_verifiable_task_is_eligible(self):
        self.assertEqual(self.check(), (True, []))

    def test_each_check_fails_alone(self):
        cases = {
            "validators": ({"validators": []}, "no declared validators"),
            "role": ({"role": "planner"}, "role planner"),
            "effort": ({"effort": "high"}, "effort high"),
            "secret": ({"scope": ["config/.env.local"]}, "secret"),
            "protected": ({"scope": ["policy/CANONICAL_AGENT_POLICY.md"]}, "protected paths"),
            "sensitivity": ({"sensitivity": "private"}, "sensitivity private"),
        }
        for name, (extra, needle) in cases.items():
            with self.subTest(name):
                ok, failed = self.check(**extra)
                self.assertFalse(ok)
                self.assertEqual(len(failed), 1, failed)
                self.assertIn(needle, failed[0])

    def test_secret_sensitivity_never_allowed_even_if_policy_lists_it(self):
        ok, failed = free_routing.eligible(task(), sensitivity="secret", protected_globs=[],
                                           allowed_sensitivity=["public", "internal", "secret"])
        self.assertFalse(ok)


class DecideTest(unittest.TestCase):
    def decide(self, item=None, *, catalog=CATALOG, specs=SPECS, governor=None, policy=POLICY):
        return free_routing.decide(item or task(), catalog=catalog, specializations=specs,
                                   governor=governor or FakeGovernor(), project_policy=policy)

    def test_eligible_free_route_chosen(self):
        decision = self.decide()
        self.assertEqual(decision["route"], "free")
        self.assertEqual(decision["model"], "org/a:free")
        self.assertEqual(decision["revision"], "org/a:free-r1")
        self.assertEqual(decision["catalog_snapshot"], "FCS-test")
        self.assertTrue(decision["eligibility"]["low_risk_verifiable"])
        self.assertIn("policy:test@v2", decision["policy_allowed_by"])
        self.assertTrue(any(item.startswith("data_policy:trains_on_prompts=false") for item in decision["policy_allowed_by"]))
        self.assertEqual([rung["rung"] for rung in decision["ladder"]],
                         ["alternate_free", "local_or_already_paid", "cheap_paid", "frontier"])

    def test_missing_validators_escalates(self):
        decision = self.decide(task(validators=[]))
        self.assertEqual(decision["route"], "escalate")
        self.assertIsNone(decision["model"])
        self.assertIn("no declared validators", decision["reason"])
        self.assertNotIn("alternate_free", [rung["rung"] for rung in decision["ladder"]])

    def test_sensitive_data_escalates(self):
        for extra in ({"sensitivity": "secret"}, {"scope": ["secrets/openrouter.json"]}):
            with self.subTest(extra):
                decision = self.decide(task(**extra))
                self.assertEqual(decision["route"], "escalate")
                self.assertFalse(decision["eligibility"]["low_risk_verifiable"])

    def test_incompatible_data_policy_escalates(self):
        unknown = {"models": [model("org/a:free", data_policy={"trains_on_prompts": None, "source": "unknown"})]}
        decision = self.decide(catalog=unknown)
        self.assertEqual((decision["route"], decision["reason"]), ("escalate", "data_policy: unknown"))
        trains = {"models": [model("org/a:free", data_policy={"trains_on_prompts": True, "source": "p@v2"})]}
        self.assertEqual(self.decide(catalog=trains)["route"], "escalate")
        # Public work needs no data-policy entry; the project may also allow training endpoints.
        self.assertEqual(self.decide(task(sensitivity="public"), catalog=unknown, specs=[record("org/a:free", 0.8)])["route"], "free")
        allowing = {**POLICY, "allow_training_endpoints": True}
        self.assertEqual(self.decide(catalog=trains, specs=[record("org/a:free", 0.8)], policy=allowing)["route"], "free")

    def test_project_policy_resolver_beats_snapshot_copy(self):
        policy = {**POLICY, "data_policy_for": lambda slug, revision: {"trains_on_prompts": None}}
        self.assertEqual(self.decide(policy=policy)["reason"], "data_policy: unknown")

    def test_quota_exhausted_escalates(self):
        governor = FakeGovernor({"org/a:free": "daily allowance reached", "org/b:free": "daily allowance reached"})
        decision = self.decide(governor=governor)
        self.assertEqual(decision["route"], "escalate")
        self.assertTrue(decision["reason"].startswith("quota: "))
        self.assertEqual(governor.asked, ["org/a:free", "org/b:free"])

    def test_priority_lane_never_routes_to_canary_models(self):
        canaries = [record("org/a:free", 0.4, n=5, status="canary"), record("org/b:free", 0.3, n=3, status="canary")]
        decision = self.decide(specs=canaries)
        self.assertEqual((decision["route"], decision["model"]), ("escalate", None))
        self.assertIn("priority lane", decision["reason"])
        # A proven model still wins the priority lane; the canary is not an alternate.
        mixed = [record("org/a:free", 0.4, n=5, status="canary"), record("org/b:free", 0.6)]
        decision = self.decide(specs=mixed)
        self.assertEqual((decision["route"], decision["model"]), ("free", "org/b:free"))
        self.assertEqual(decision["alternates"], [])
        # Swarm work may still use canary models.
        self.assertEqual(self.decide(task(lane="swarm", role="inline"), specs=canaries)["route"], "free")

    def test_non_free_or_unfit_models_are_never_named(self):
        catalog = {"models": [model("org/a:free", pricing={"prompt": "0", "completion": "0.000001"}),
                              model("org/b:free", supports_tools=False)]}
        decision = self.decide(task(needs_tools=True), catalog=catalog)
        self.assertEqual(decision["route"], "escalate")
        self.assertIsNone(decision["model"])

    def test_refused_model_ranked_higher_is_never_chosen_or_alternate(self):
        catalog = {"models": [model("org/paid", pricing={"prompt": "0.000001", "completion": "0.000001"}),
                              model("org/trains:free", data_policy={"trains_on_prompts": True, "source": "p@v2"}),
                              model("org/b:free")]}
        specs = [record("org/paid", 0.95), record("org/trains:free", 0.9), record("org/gone:free", 0.85),
                 record("org/b:free", 0.6)]
        decision = self.decide(catalog=catalog, specs=specs)
        self.assertEqual((decision["route"], decision["model"]), ("free", "org/b:free"))
        self.assertEqual(decision["alternates"], [])


class EscalateTest(unittest.TestCase):
    def registry(self):
        return ProviderRegistry(providers=[
            provider("local", models={"fast": "local-fast"}, profile={"deployment": "local"}),
            provider("paid", profile={"deployment": "api"}),
        ])

    def test_ladder_order_on_repeated_failure(self):
        registry = self.registry()
        decision = free_routing.decide(task(verified_outputs=["tests/test_a.py"]), catalog=CATALOG, specializations=SPECS,
                                       governor=FakeGovernor(), project_policy=POLICY)
        self.assertEqual(decision["model"], "org/a:free")
        seen = [(decision["rung"], decision["model"])]
        step = decision
        for index in range(5):
            step = free_routing.escalate(step, {"kind": "validator_failed", "verified_outputs": [f"tests/test_{index}.py"]},
                                         registry=registry, governor=FakeGovernor())
            seen.append((step["rung"], step["model"]))
        self.assertEqual(seen, [
            ("free", "org/a:free"),
            ("alternate_free", "org/b:free"),
            ("local_or_already_paid", "local-fast"),
            ("cheap_paid", "paid-balanced"),
            ("frontier", "paid-frontier"),
            ("exhausted", None),
        ])
        self.assertEqual(step["verified_outputs"], ["tests/test_a.py"] + [f"tests/test_{i}.py" for i in range(5)])
        self.assertEqual(len(step["history"]), 5)

    def test_router_rungs_report_paid_and_never_resolve_without_registry(self):
        decision = free_routing.decide(task(validators=[]), catalog=CATALOG, specializations=SPECS,
                                       governor=FakeGovernor(), project_policy=POLICY)
        step = free_routing.escalate(decision, None, registry=self.registry())
        self.assertEqual((step["rung"], step["provider"], step["paid"]), ("local_or_already_paid", "local", False))
        step = free_routing.escalate(step, "invalid_output", registry=self.registry())
        self.assertEqual((step["rung"], step["paid"]), ("cheap_paid", True))
        empty = free_routing.escalate(decision, None, registry=ProviderRegistry(providers=[]))
        self.assertEqual(empty["route"], "exhausted")

    def test_alternate_skipped_without_positive_expected_value_or_quota(self):
        weak = [record("org/a:free", 0.8), record("org/b:free", 0.05)]
        decision = free_routing.decide(task(), catalog=CATALOG, specializations=weak,
                                       governor=FakeGovernor(), project_policy=POLICY)
        self.assertLessEqual(decision["alternates"][0]["expected_value"], 0)
        step = free_routing.escalate(decision, "validator_failed", registry=self.registry())
        self.assertEqual(step["rung"], "local_or_already_paid")
        decision = free_routing.decide(task(), catalog=CATALOG, specializations=SPECS,
                                       governor=FakeGovernor(), project_policy=POLICY)
        step = free_routing.escalate(decision, "validator_failed", registry=self.registry(),
                                     governor=FakeGovernor({"org/b:free": "per-minute limit reached"}))
        self.assertEqual(step["rung"], "local_or_already_paid")

    def test_sensitive_work_never_resolves_to_api_provider(self):
        for extra in ({"sensitivity": "secret"}, {"scope": ["secrets/openrouter.json"]}, {"sensitivity": "private"}):
            with self.subTest(extra):
                step = free_routing.decide(task(**extra), catalog=CATALOG, specializations=SPECS,
                                           governor=FakeGovernor(), project_policy=POLICY)
                providers = []
                for _ in range(4):
                    step = free_routing.escalate(step, "validator_failed", registry=self.registry())
                    providers.append(step["provider"])
                self.assertEqual(providers, ["local", None, None, None])
                self.assertEqual(step["route"], "exhausted")

    def test_preserves_select_kwargs(self):
        decision = free_routing.decide(task(validators=[]), catalog=CATALOG, specializations=SPECS,
                                       governor=FakeGovernor(), project_policy=POLICY)
        step = free_routing.escalate(decision, None, registry=self.registry(), excluded=["local"])
        self.assertEqual((step["rung"], step["provider"]), ("cheap_paid", "paid"))


if __name__ == "__main__":
    unittest.main()
