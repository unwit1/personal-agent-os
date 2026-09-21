from pathlib import Path

from agent_os.knowledge import upsert_entity
from agent_os.knowledge_benchmark import BenchmarkCase, evaluate, gate


def test_benchmark_passes_relevant_budgeted_results(tmp_path: Path):
    db = tmp_path / "knowledge.sqlite"
    upsert_entity({"id":"tes:lorkhan","library_id":"elder-scrolls","name":"Lorkhan","entity_type":"deity","description":"Associated with creation of Mundus."}, db)
    cases = (BenchmarkCase("lorkhan","Lorkhan creation Mundus",("tes:lorkhan",)),)
    report = evaluate(cases, db_path=db, char_budget=500)
    assert report["summary"]["mean_expected_entity_recall"] == 1.0
    assert report["summary"]["budget_pass_rate"] == 1.0
    assert gate(report)["passed"] is True


def test_gate_rejects_missing_retrieval(tmp_path: Path):
    db = tmp_path / "knowledge.sqlite"
    cases = (BenchmarkCase("missing","Numidium",("tes:numidium",)),)
    report = evaluate(cases, db_path=db, char_budget=500)
    decision = gate(report)
    assert decision["passed"] is False
    assert decision["reasons"]
