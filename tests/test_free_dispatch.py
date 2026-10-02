import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.orchestrator import free_dispatch
from tests import test_orchestrator
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

    def record(self, event):
        self.events = getattr(self, "events", []) + [dict(event)]
        return {**event, "event_id": f"FQE-{len(self.events)}"}


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


class EngineWiringTest(unittest.TestCase):
    def setUp(self):
        import shutil
        import tempfile

        from agent_os.orchestrator.engine import Orchestrator
        from agent_os.orchestrator.store import RunStore

        tmp = Path(tempfile.mkdtemp(prefix="agent-os-free-"))
        self.addCleanup(shutil.rmtree, tmp, True)
        self.recorded = []
        self.engine = Orchestrator(RunStore(tmp / "home"), registry=registry(), free_inputs=inputs(), session_foreman=False)
        self.engine.ledger.emit = lambda run_id, kind, node=None, /, **data: self.recorded.append((kind, data))
        self.engine._availability = {"or-free": True, "local": True, "paid": True}
        self.record = {"run_id": "R1", "policy": {"preference": "balanced", "default_validators": ["x"], "max_escalations": 2,
                                                  "allow_paid_spend": True, "free_routing_enabled": True}, "nodes": {}}

    def kinds(self):
        return [kind for kind, _ in self.recorded]

    def test_default_off_policy_is_false(self):
        from agent_os.orchestrator.model import DEFAULT_POLICY

        self.assertFalse(DEFAULT_POLICY["free_routing_enabled"])

    def test_inputs_are_lazy_and_injectable(self):
        self.assertEqual(self.engine.free_inputs().catalog["snapshot_id"], "FCS-test")

    def test_free_selection_records_paid_route_and_decision(self):
        item = node(requirements=None)
        selection = self.engine._free_hook(self.record, item, {}, None)
        self.assertEqual(selection["model"], "org/a:free")
        state = item["free_route"]
        self.assertEqual(state["free_state"], "free")
        self.assertEqual(state["free_providers"], [])  # recorded only once a launch happens
        self.assertIn(state["paid_route"]["provider"], {"local", "paid"})
        self.assertIn("subscription", state["paid_route"])
        self.assertEqual(self.kinds(), ["free_route_decided"])
        self.assertFalse(hasattr(self.engine.free_inputs().governor, "events"))
        pending = selection["free_attempt"]
        self.assertEqual(pending["paid_route"], state["paid_route"])
        self.engine._free_launched(self.record, item, pending)
        self.assertEqual(state["free_providers"], ["or-free"])
        self.assertEqual(self.engine.free_inputs().governor.events, [pending])
        self.assertEqual(state["event_id"], "FQE-1")

    def test_validator_failure_escalates_free_node_to_router(self):
        item = node(requirements=None, escalations=0, execution_path="model", state="RUNNING")
        self.engine._free_hook(self.record, item, {}, None)
        moved = self.engine._free_after_failure(self.record, item, {"kind": "validator_failed"}, "validator failed")
        self.assertTrue(moved)
        self.assertIn("free_route_escalated", self.kinds())
        self.assertEqual(item["state"], "FAILED_RETRYABLE")
        self.assertEqual(item["escalations"], 1)
        self.assertEqual(item["free_route"]["free_state"], "free")  # a positive-EV alternate remains
        self.assertEqual(item["free_route"]["model"], "org/b:free")

    def test_escalate_decision_skips_free_launch(self):
        self.engine._free_inputs = FreeInputs({"models": []}, [], FakeGovernor(), {})
        item = node(requirements=None)
        self.assertIsNone(self.engine._free_hook(self.record, item, {}, None))
        self.assertEqual(item["free_route"]["free_state"], "escalated")
        self.assertEqual(self.kinds(), ["free_route_decided"])
        self.assertIsNone(self.engine._free_hook(self.record, item, {}, None))  # back on the normal path, no new events
        self.assertEqual(self.kinds(), ["free_route_decided"])


class FlagOnEngineFlowTest(test_orchestrator.OrchestratorFixture):
    providers = ("or-free", "or-free2", "paid")

    def registry(self):
        return ProviderRegistry(providers=[
            test_orchestrator.provider("or-free", models={"fast": "org/a:free"}),
            test_orchestrator.provider("or-free2", models={"reasoning": "org/b:free"}),
            test_orchestrator.provider("paid"),
        ])

    def setUp(self):
        super().setUp()
        self.engine = self.make_engine()
        specs = [dict(spec(slug, low), task_family="implementer") for slug, low in (("org/a:free", 0.8), ("org/b:free", 0.6))]
        self.engine._free_inputs = inputs(specs)
        self.engine._availability = {"or-free": True, "or-free2": True, "paid": True}
        self.fail_command = {"kind": "command", "command": [sys.executable, "-c", "raise SystemExit(1)"]}

    def free_task(self, validator):
        return self.task("a", effort="low", capability_class="fast", validators=[validator])

    def create_free(self, validator, **policy):
        return self.create([self.free_task(validator)], free_routing_enabled=True, **policy)

    def test_launch_routes_free_and_records_attempt_after_launch(self):
        run_id = self.create_free(test_orchestrator.PASS)
        self.engine.start(run_id)
        self.engine.step(run_id)
        item = self.node(run_id, "a")
        self.assertEqual((item["selection"]["provider"], item["selection"]["model"]), ("or-free", "org/a:free"))
        self.assertNotIn("free_attempt", item["selection"])
        state = item["free_route"]
        self.assertEqual(state["route"], "free")
        self.assertEqual(state["free_providers"], ["or-free"])
        self.assertEqual(state["paid_route"], {"model": "paid-fast", "provider": "paid", "subscription": True})
        events = self.engine.free_inputs().governor.events
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["paid_route"], state["paid_route"])

    def test_validator_failure_escalates_to_alternate_then_router_capped_by_max_escalations(self):
        run_id = self.create_free(self.fail_command, max_escalations=2)
        self.engine.run_loop(run_id, max_ticks=40)
        item = self.node(run_id, "a")
        self.assertEqual(item["escalations"], 2)
        state = item["free_route"]
        self.assertEqual(state["free_state"], "escalated")
        self.assertEqual(state["alternates_used"], 1)
        self.assertEqual(item["state"], "FAILED_FINAL")
        self.assertEqual([entry["model"] for entry in self.engine.free_inputs().governor.events][:2], ["org/a:free", "org/b:free"])
        self.assertEqual(self.engine.free_inputs().governor.events[0]["paid_route"], {"model": "paid-fast", "provider": "paid", "subscription": True})

    def test_zero_max_escalations_never_escalates_free_node(self):
        run_id = self.create_free(self.fail_command, max_escalations=0)
        self.engine.run_loop(run_id, max_ticks=40)
        item = self.node(run_id, "a")
        self.assertEqual(item["escalations"], 0)
        self.assertEqual(item["free_route"]["free_state"], "free")


if __name__ == "__main__":
    unittest.main()
