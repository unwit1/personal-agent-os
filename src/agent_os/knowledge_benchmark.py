from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

from .knowledge import search_lore


@dataclass(frozen=True)
class BenchmarkCase:
    id: str
    query: str
    expected_entity_ids: tuple[str, ...]


DEFAULT_CASES = (
    BenchmarkCase("creation-lorkhan", "Lorkhan creation Mundus", ("tes:lorkhan",)),
    BenchmarkCase("vivec", "Vivec Tribunal", ("tes:vivec", "tes:tribunal")),
    BenchmarkCase("dwemer", "Dwemer disappearance Red Mountain", ("tes:dwemer", "tes:red-mountain")),
    BenchmarkCase("numidium", "Numidium", ("tes:numidium",)),
    BenchmarkCase("red-mountain-battle", "Battle of Red Mountain", ("tes:battle-of-red-mountain", "tes:red-mountain")),
    BenchmarkCase("lessons", "36 Lessons of Vivec", ("tes:36-lessons", "tes:vivec")),
)


def evaluate(cases: Iterable[BenchmarkCase] = DEFAULT_CASES, *, db_path: Path | None = None, char_budget: int = 2400, limit: int = 6) -> dict:
    rows = []
    for case in cases:
        result = search_lore(case.query, limit=limit, char_budget=char_budget, path=db_path)
        returned = [item["id"] for item in result["results"]]
        expected = set(case.expected_entity_ids)
        hits = expected.intersection(returned)
        rows.append({
            "id": case.id, "query": case.query, "expected": list(case.expected_entity_ids),
            "returned": returned, "hits": sorted(hits), "recall": len(hits) / len(expected),
            "approx_chars": result["approx_chars"], "within_budget": result["approx_chars"] <= char_budget,
        })
    count = len(rows)
    mean_recall = sum(row["recall"] for row in rows) / count if count else 0.0
    budget_pass_rate = sum(1 for row in rows if row["within_budget"]) / count if count else 0.0
    return {
        "cases": rows,
        "summary": {
            "cases": count,
            "mean_expected_entity_recall": round(mean_recall, 4),
            "budget_pass_rate": round(budget_pass_rate, 4),
            "max_chars": max((row["approx_chars"] for row in rows), default=0),
            "char_budget": char_budget,
        },
    }


def gate(report: dict, *, min_recall: float = 0.80, required_budget_pass_rate: float = 1.0) -> dict:
    summary = report["summary"]
    reasons = []
    if summary["mean_expected_entity_recall"] < min_recall:
        reasons.append(f"recall {summary['mean_expected_entity_recall']:.2f} < {min_recall:.2f}")
    if summary["budget_pass_rate"] < required_budget_pass_rate:
        reasons.append(f"budget pass rate {summary['budget_pass_rate']:.2f} < {required_budget_pass_rate:.2f}")
    return {"passed": not reasons, "reasons": reasons, "thresholds": {"min_recall": min_recall, "required_budget_pass_rate": required_budget_pass_rate}}


def save_report(report: dict, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
