"""Engine wiring of free-first routing (free_routing_enabled, IMP-0015 / ORCH-0038).

In-memory catalog, proven specialization, fake governor, public data policy and a
throwaway orchestrator home: no network and no paid compute.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import json
import unittest
from unittest import mock

from agent_os.orchestrator import free_dispatch, free_quota
from agent_os.orchestrator.engine import Orchestrator
from agent_os.orchestrator.ledger import describe
from agent_os.orchestrator.free_dispatch import FreeInputs
from agent_os.orchestrator.router import ProviderRegistry
from agent_os.orchestrator.store import RunStore
from agent_os.telemetry import LocalTelemetryStore

from tests.test_orchestrator import OrchestratorFixture, provider

TRAINS_FALSE = {"trains_on_prompts": False, "source": "policy:test@v2#data_policies[0]", "verified_at": "2026-10-01T00:00:00Z"}
FREE_A, FREE_B = "org/a:free", "org/b:free"
FAMILY = "implementer"
FREE_PROVIDERS = {"freeone", "freetwo"}


def free_model(slug: str) -> dict:
    return {"slug": slug, "revision": f"{slug}-r1", "context_length": 65536, "supports_tools": True,
            "supports_structured_output": True, "pricing": {"prompt": "0", "completion": "0"},
            "data_policy": dict(TRAINS_FALSE)}


def proven(slug: str, low: float) -> dict:
    return {"task_family": FAMILY, "model": slug, "revision": f"{slug}-r1", "n": 30,
            "wilson95": [low, min(1.0, low + 0.2)], "status": "proven"}


class FakeGovernor:
    """Always has quota; appends to the real ledger file under a temp home."""

    def __init__(self, home: Path) -> None:
        self.home = home

    def can_spend(self, model: str, retry: int = 0):
        return True, "ok"

    def remaining(self):
        return {}

    def record(self, event):
        return free_quota.record(event, self.home)


class FreeRoutingEngineTests(OrchestratorFixture):
    providers = ("alpha", "beta", "freeone", "freetwo")

    def registry(self) -> ProviderRegistry:
        return ProviderRegistry(providers=[
            provider("freeone", models={"fast": FREE_A}, profile={"deployment": "api"}),
            provider("freetwo", models={"fast": FREE_B}, profile={"deployment": "api"}),
            provider("alpha"),
            provider("beta"),
        ])

    def free_home(self) -> Path:
        return self.tmp / "home"

    def ledger_file(self) -> Path:
        return free_quota.ledger_path(self.free_home())

    def free_events(self) -> list[dict]:
        path = self.ledger_file()
        if not path.exists():
            return []
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]

    def free_inputs(self) -> FreeInputs:
        catalog = {"snapshot_id": "FCS-test", "models": [free_model(FREE_A), free_model(FREE_B)]}
        specs = [proven(FREE_A, 0.8), proven(FREE_B, 0.6)]
        return FreeInputs(catalog, specs, FakeGovernor(self.free_home()), {"source": "policy:test@v2", "protected_globs": ["policy/**"]})

    def free_engine(self, tag: str = "") -> Orchestrator:
        return Orchestrator(
            RunStore(self.free_home()), registry=self.registry(),
            telemetry_store=LocalTelemetryStore(self.tmp / f"telemetry{tag}" / "events.jsonl"),
            claims_path=self.tmp / f"claims{tag}.json", sleep=lambda seconds: None, free_inputs=self.free_inputs())

    def start(self, tasks: list[dict], engine: Orchestrator, **policy) -> dict:
        run_id = engine.create_run("fixture goal", repository=self.repo, tasks=tasks, policy=self.policy(**policy))["run_id"]
        engine.run_loop(run_id, max_ticks=60)
        return engine.load(run_id)

    def events_of(self, engine: Orchestrator, run_id: str, kind: str) -> list[dict]:
        events, _ = engine.ledger.read(run_id)
        return [event for event in events if event["type"] == kind]

    def kinds(self, engine: Orchestrator, run_id: str) -> list[str]:
        events, _ = engine.ledger.read(run_id)
        return [event["type"] for event in events]

    def selections(self, record: dict) -> dict:
        return {node_id: (node.get("selection") or {}).get("provider") for node_id, node in record["nodes"].items()}

    # (a) default off ------------------------------------------------------

    def test_default_off_is_unchanged_and_never_consults_free_dispatch(self) -> None:
        results = []
        for label, policy in (("omitted", {}), ("explicit_false", {"free_routing_enabled": False})):
            with self.subTest(label):
                engine = self.free_engine(label)
                with mock.patch.object(free_dispatch, "decide_for_node") as decide:
                    record = self.start([self.task("a", capability_class="fast", effort="low")], engine, **policy)
                    decide.assert_not_called()
                self.assertTrue(all("free_route" not in node for node in record["nodes"].values()))
                self.assertFalse([kind for kind in self.kinds(engine, record["run_id"]) if kind.startswith("free_route")])
                self.assertFalse(self.ledger_file().exists())
                results.append(self.selections(record))
        self.assertEqual(results[0], results[1])
        self.assertFalse(FREE_PROVIDERS & set(results[0].values()))

    # (b) enabled, eligible ------------------------------------------------

    def test_enabled_eligible_task_routes_to_the_free_provider(self) -> None:
        engine = self.free_engine()
        record = self.start([self.task("a", capability_class="fast", effort="low")], engine, free_routing_enabled=True)
        node = record["nodes"]["a"]
        self.assertEqual(node["selection"]["provider"], "freeone")
        self.assertEqual(node["selection"]["model"], FREE_A)
        self.assertEqual(node["free_route"]["route"], "free")
        decided = self.events_of(engine, record["run_id"], "free_route_decided")
        self.assertEqual([event["node"] for event in decided], ["a"])
        self.assertEqual(decided[0]["data"]["route"], "free")
        self.assertEqual(decided[0]["data"]["model"], FREE_A)
        attempts = [event for event in self.free_events() if event.get("type") != "verdict"]
        self.assertTrue(attempts)
        self.assertEqual(attempts[0]["model"], FREE_A)
        self.assertIsInstance(attempts[0]["paid_route"], dict)

    # (c) enabled, validator failure ---------------------------------------

    def test_validator_failure_escalates_off_the_first_free_model(self) -> None:
        # Fails after the first worker call; passes once a later attempt wrote its file.
        gate = {"kind": "command", "command": [sys.executable, "-c", "import glob,sys; sys.exit(0 if glob.glob('a/*-2.txt') else 1)"]}
        engine = self.free_engine()
        record = self.start([self.task("a", capability_class="fast", effort="low", validators=[gate])], engine, free_routing_enabled=True)
        run_id = record["run_id"]
        escalated = self.events_of(engine, run_id, "free_route_escalated")
        self.assertTrue(escalated, self.kinds(engine, run_id))
        self.assertEqual(escalated[0]["data"]["from_model"], FREE_A)
        self.assertEqual(escalated[0]["data"]["failure"], "validator_failed")
        target = escalated[0]["data"]["to"]
        self.assertTrue(target.startswith(("free:", "class:")), target)
        self.assertNotEqual(target, f"free:{FREE_A}")
        self.assertNotEqual(record["nodes"]["a"]["selection"]["model"], FREE_A)
        verdicts = [event for event in self.free_events() if event.get("type") == "verdict"]
        self.assertTrue(verdicts)
        self.assertIs(verdicts[0]["accepted"], False)
        self.assertIs(verdicts[0]["escalated"], True)

    # (d) enabled, ineligible ----------------------------------------------

    def test_ineligible_effort_uses_normal_routing_and_names_the_failed_check(self) -> None:
        engine = self.free_engine()
        record = self.start([self.task("a", capability_class="fast", effort="high")], engine, free_routing_enabled=True)
        self.assertNotIn(record["nodes"]["a"]["selection"]["provider"], FREE_PROVIDERS)
        decided = [event for event in self.events_of(engine, record["run_id"], "free_route_decided") if event["node"] == "a"]
        self.assertEqual(len(decided), 1)
        self.assertEqual(decided[0]["data"]["route"], "escalate")
        self.assertIn("effort high", " ".join(decided[0]["data"]["failed_checks"] or []))
        self.assertFalse([event for event in self.free_events() if event.get("type") != "verdict"])

    def test_reviewer_nodes_are_never_free_routed(self) -> None:
        engine = self.free_engine()
        record = self.start([self.task("a", capability_class="fast", effort="low")], engine, free_routing_enabled=True)
        reviewers = [node for node in record["nodes"].values() if node["role"] == "reviewer" and node.get("selection")]
        self.assertTrue(reviewers)
        for node in reviewers:
            self.assertNotIn(node["selection"]["provider"], FREE_PROVIDERS)
            self.assertNotIn("free_route", node)

    def test_free_route_event_types_are_recorded_and_described(self) -> None:
        engine = self.free_engine()
        run_id = engine.create_run("fixture goal", repository=self.repo, tasks=[self.task("a")], policy=self.policy())["run_id"]
        for kind in ("free_route_decided", "free_route_escalated"):
            record = engine.ledger.emit(run_id, kind, "a", route="free", from_model="m", to="class:fast/low")
            self.assertIsNotNone(record, kind)
            self.assertTrue(describe(record))


if __name__ == "__main__":
    unittest.main()
