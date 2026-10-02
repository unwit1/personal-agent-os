import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.orchestrator import free_dispatch
from agent_os.orchestrator.free_dispatch import FreeInputs
from agent_os.orchestrator.router import ProviderRegistry

TRAINS_FALSE = {"trains_on_prompts": False, "source": "policy:test@v2#data_policies[0]", "verified_at": "2026-10-01T00:00:00Z"}


def model(slug: str) -> dict:
    return {"slug": slug, "revision": f"{slug}-r1", "context_length": 65536, "supports_tools": True,
            "supports_structured_output": True, "pricing": {"prompt": "0", "completion": "0"},
            "data_policy": dict(TRAINS_FALSE)}


def spec(slug: str, low: float) -> dict:
    return {"task_family": "test_author", "model": slug, "revision": f"{slug}-r1", "n": 30,
            "wilson95": [low, min(1.0, low + 0.2)], "status": "proven"}


class FakeGovernor:
    def can_spend(self, model: str, retry: int = 0):
        return True, "ok"

    def remaining(self):
        return {}


def provider(provider_id: str, models: dict, deployment: str) -> dict:
    return {"id": provider_id, "adapter": "synthetic", "models": models,
            "effort_map": {"none": "minimal", "low": "lo", "medium": "med", "high": "hi"},
            "max_concurrency": 2, "profile": {"deployment": deployment}}


def registry() -> ProviderRegistry:
    return ProviderRegistry(providers=[
        provider("or-free", {"fast": "org/a:free"}, "api"),
        provider("local", {"fast": "local-fast"}, "local"),
        provider("paid", {"fast": "paid-fast", "balanced": "paid-balanced", "frontier": "paid-frontier"}, "api"),
    ])


def inputs(specs=None) -> FreeInputs:
    catalog = {"snapshot_id": "FCS-test", "models": [model("org/a:free"), model("org/b:free")]}
    specs = [spec("org/a:free", 0.8), spec("org/b:free", 0.6)] if specs is None else specs
    return FreeInputs(catalog, specs, FakeGovernor(), {"source": "policy:test@v2", "protected_globs": ["policy/**"]})


RECORD = {"id": "R1", "policy": {"default_validators": ["python -m unittest tests.test_x"]}}


def node(**extra) -> dict:
    base = {"id": "n1", "role": "test_author", "effort": "low", "capability_class": "fast",
            "scope": ["tests/test_x.py"], "excluded_providers": []}
    base.update(extra)
    return base


class TaskViewTest(unittest.TestCase):
    def test_maps_node_fields_and_falls_back_to_default_validators(self):
        view = free_dispatch.task_view(RECORD, node())
        self.assertEqual(view["validators"], ["python -m unittest tests.test_x"])
        self.assertEqual((view["task_family"], view["sensitivity"], view["lane"]), ("test_author", "internal", "priority"))
        self.assertEqual((view["run_id"], view["node_id"], view["scope"]), ("R1", "n1", ["tests/test_x.py"]))
        own = free_dispatch.task_view(RECORD, node(validators=["x"], task_family="fam"))
        self.assertEqual((own["validators"], own["task_family"]), (["x"], "fam"))

    def test_sensitivity_and_deployment(self):
        self.assertEqual(free_dispatch.task_view(RECORD, node(requirements={"sensitivity": "secret"}))["sensitivity"], "secret")
        self.assertEqual(free_dispatch.task_view(RECORD, node(requirements={"sensitivity": "bogus"}))["sensitivity"], "internal")
        self.assertEqual(free_dispatch.task_view(RECORD, node(requirements={"deployment": ["local"]}))["sensitivity"], "private")


class DecideAndSelectTest(unittest.TestCase):
    def test_eligible_low_risk_task_routes_free_and_selects_serving_provider(self):
        decision = free_dispatch.decide_for_node(RECORD, node(), inputs())
        self.assertEqual((decision["route"], decision["model"]), ("free", "org/a:free"))
        selection, reason = free_dispatch.selection_for(decision, registry(), role="test_author")
        self.assertIsNone(reason)
        self.assertEqual((selection["provider"], selection["model"]), ("or-free", "org/a:free"))
        self.assertTrue(selection["free_route"])
        self.assertFalse(selection["overridden"])
        self.assertTrue(selection["reason"].startswith("free route: "))

    def test_escalations_name_failed_checks(self):
        cases = {
            "effort": (node(effort="high"), "effort high"),
            "planner": (node(role="planner"), "role planner"),
            "secret": (node(requirements={"sensitivity": "secret"}), "sensitivity secret"),
        }
        for name, (item, needle) in cases.items():
            with self.subTest(name):
                decision = free_dispatch.decide_for_node(RECORD, item, inputs())
                self.assertEqual(decision["route"], "escalate")
                self.assertIn(needle, decision["reason"])
                self.assertIn(needle, " ".join(decision["eligibility"]["failed_checks"]))
                self.assertEqual(free_dispatch.selection_for(decision, registry(), role="test_author"),
                                 (None, "not a free route"))

    def test_missing_registry_provider_returns_none(self):
        decision = free_dispatch.decide_for_node(RECORD, node(), inputs())
        empty = ProviderRegistry(providers=[provider("local", {"fast": "local-fast"}, "local")])
        self.assertEqual(free_dispatch.selection_for(decision, empty, role="test_author"),
                         (None, "no registry provider serves org/a:free"))

    def test_excluded_provider_is_named_in_reason(self):
        decision = free_dispatch.decide_for_node(RECORD, node(), inputs())
        selection, reason = free_dispatch.selection_for(decision, registry(), role="test_author", excluded=["or-free"])
        self.assertIsNone(selection)
        self.assertEqual(reason, "free provider or-free: excluded after a provider failure on this node")

    def test_decide_never_raises(self):
        decision = free_dispatch.decide_for_node(RECORD, node(), FreeInputs({"models": []}, [], object(), {}))
        self.assertEqual(decision["route"], "escalate")


class AfterFailureTest(unittest.TestCase):
    def stored(self, **extra):
        decision = free_dispatch.decide_for_node(RECORD, node(), inputs())
        decision.update({"free_state": "free", "free_providers": ["or-free"], **extra})
        return node(free_route=decision)

    def test_free_moves_to_alternate_free_when_positive_ev(self):
        item = self.stored()
        result = free_dispatch.after_failure(
            item, {"kind": "validator_failed", "verified_outputs": ["tests/test_x.py"]}, registry(), FakeGovernor())
        self.assertEqual(result["action"], "free")
        self.assertEqual(result["decision"]["model"], "org/b:free")
        self.assertEqual(result["decision"]["verified_outputs"], ["tests/test_x.py"])
        self.assertEqual(item["free_route"]["model"], "org/a:free")  # stored decision untouched

    def test_free_moves_to_router_class_without_positive_alternate(self):
        decision = free_dispatch.decide_for_node(RECORD, node(), inputs([spec("org/a:free", 0.8), spec("org/b:free", 0.05)]))
        item = node(free_route={**decision, "free_state": "free"})
        result = free_dispatch.after_failure(
            item, {"kind": "validator_failed", "verified_outputs": ["tests/test_x.py"]}, registry(), FakeGovernor())
        self.assertEqual(result["action"], "router")
        self.assertEqual(result["decision"]["rung"], "local_or_already_paid")
        self.assertEqual((result["capability_class"], result["effort"]), ("fast", "low"))
        self.assertEqual(result["decision"]["verified_outputs"], ["tests/test_x.py"])

    def test_provider_failure_skips_alternate_free(self):
        result = free_dispatch.after_failure(self.stored(), {"kind": "quota"}, registry(), FakeGovernor())
        self.assertEqual(result["action"], "router")

    def test_exhausted_when_nothing_left(self):
        item = self.stored(alternates_used=1)
        result = free_dispatch.after_failure(item, {"kind": "validator_failed"}, ProviderRegistry(providers=[]), FakeGovernor())
        self.assertEqual(result["action"], "exhausted")


class ExclusionsTest(unittest.TestCase):
    def test_only_launched_providers_and_tried_models(self):
        item = node(free_route={"tried": ["org/a:free", "paid:paid-fast"], "free_providers": ["or-free", "gone"]})
        self.assertEqual(free_dispatch.free_exclusions(item, registry()), {"or-free": ["fast"]})
        self.assertEqual(free_dispatch.free_exclusions(node(free_route={"tried": ["org/a:free"]}), registry()), {})


class LoadDefaultTest(unittest.TestCase):
    def test_never_raises_and_escalates_on_empty_home(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            loaded = FreeInputs.load_default(Path(tmp))
        decision = free_dispatch.decide_for_node(RECORD, node(), loaded)
        self.assertEqual(decision["route"], "escalate")


if __name__ == "__main__":
    unittest.main()
