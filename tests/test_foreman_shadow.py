"""IMP-0015: shadow foreman proposal, storage, comparison and report."""

from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.orchestrator import context_contract, foreman  # noqa: E402
from agent_os.orchestrator.adapters import synthetic  # noqa: E402
from agent_os.orchestrator.model import new_node  # noqa: E402
from agent_os.orchestrator.router import ProviderRegistry  # noqa: E402


def run_record() -> dict:
    a = new_node("a", "Add the parser", "implementer", capability_class="balanced")
    b = new_node("b", "Add tests", "test_author", depends_on=["a"], capability_class="balanced")
    c = new_node("c", "Refactor the scheduler", "implementer", depends_on=["a"], capability_class="balanced")
    d = new_node("d", "Write docs", "implementer", capability_class="fast")
    review = new_node("a.review1", "review", "reviewer", subject="a", origin="review")
    for node, extra in ((a, {"attempts": 1}), (b, {"attempts": 1}), (c, {"attempts": 3, "retries": 2}), (d, {"attempts": 1})):
        node.update(state="PASSED", selection={"provider": "cloud", "capability_class": node["capability_class"]}, **extra)
    nodes = {n["id"]: n for n in (a, b, c, d, review)}
    return {"run_id": "run-1", "goal": "Parser feature", "order": list(nodes), "nodes": nodes}


PROPOSAL = {"id": "FSH-1", "status": "passed", "selection": {"provider": "local-abl", "model": "m"}, "refusal": None, "proposal": {"tasks": [
    {"id": "a", "capability_class": "balanced", "depends_on": []},
    {"id": "b", "capability_class": "fast", "depends_on": []},
    {"id": "c", "capability_class": "fast", "depends_on": ["a"]},
    {"id": "d", "capability_class": "reasoning", "depends_on": ["b"]},
    {"id": "zz", "capability_class": "fast"},
]}}


class CompareTests(unittest.TestCase):
    def test_verdicts_dag_and_coverage(self) -> None:
        result = foreman.compare(run_record(), PROPOSAL)
        verdicts = {row["id"]: row["verdict"] for row in result["rows"]}
        self.assertEqual(verdicts, {"a": "agree", "b": "cheaper_likely_ok", "c": "cheaper_risky", "d": "stronger"})
        self.assertEqual((result["tasks"], result["scored"], result["class_agreement"]), (4, 4, 0.25))
        self.assertEqual(result["dag"], {"edges_missing": ["a->b"], "edges_extra": ["b->d"]})
        self.assertEqual(result["extra_tasks"], ["zz"])

    def test_missing_or_invalid_tasks_are_unscored(self) -> None:
        result = foreman.compare(run_record(), {"proposal": {"tasks": [{"id": "a", "capability_class": "huge"}]}})
        self.assertEqual((result["scored"], result["counts"]["unscored"], result["class_agreement"]), (0, 4, None))
        refused = foreman.compare(run_record(), {"status": "contract_failed", "refusal": {"category": "provider_policy"}, "proposal": None})
        self.assertEqual(refused["foreman_refusal"], {"category": "provider_policy"})

    def test_contract_is_neutral_and_keeps_the_shadow_fact(self) -> None:
        registry = ProviderRegistry(providers=[{"id": "local-abl", "adapter": "synthetic", "models": {"fast": "m"}, "profile": {"deployment": "local", "refusal_profile": "abliterated"}}])
        contract = foreman.build_contract(run_record(), registry.providers)
        self.assertTrue(any(fact["safety_relevant"] and "shadow evaluation" in fact["text"] for fact in contract["facts"]))
        text = context_contract.render(contract)
        self.assertIn('"id": "d"', text)
        self.assertNotIn("a.review1", text)
        self.assertIn('"refusal_profile": "abliterated"', text)


class ProposeTests(unittest.TestCase):
    def test_propose_routes_by_preference_and_stores_then_reports(self) -> None:
        home = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, home, True)
        synthetic.reset()
        self.addCleanup(synthetic.reset)
        synthetic.SCRIPTS["abl"] = lambda request, call: {"structured": PROPOSAL["proposal"]}
        synthetic.SCRIPTS["std"] = lambda request, call: {"structured": {"tasks": []}}
        registry = ProviderRegistry(providers=[
            {"id": "std", "adapter": "synthetic", "roles": ["inline"], "models": {"balanced": "s"}, "costs": {"balanced": 1}, "options": {"script": "std"}},
            {"id": "abl", "adapter": "synthetic", "roles": ["inline"], "models": {"balanced": "m"}, "costs": {"balanced": 3}, "options": {"script": "abl"},
             "profile": {"deployment": "local", "refusal_profile": "abliterated"}},
        ])
        record = run_record()
        stored = foreman.propose("run-1", requirements={"prefer_refusal_profile": ["abliterated"]}, home=home, record_evidence=False,
                                 registry=registry, loader=lambda run_id: record)
        self.assertEqual((stored["status"], stored["selection"]["provider"]), ("passed", "abl"))
        self.assertEqual(len(foreman.load_proposals("run-1", home)), 1)
        summary = foreman.report(home, loader=lambda run_id: record)
        bucket = summary["foremen"]["abl/m"]
        self.assertEqual((bucket["proposals"], bucket["agree"], bucket["cheaper_likely_ok"], bucket["cheaper_risky"], bucket["stronger"]), (1, 1, 1, 1, 1))

    def test_report_is_empty_without_proposals(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(foreman.report(Path(tmp), loader=mock.Mock())["foremen"], {})


if __name__ == "__main__":
    unittest.main()
