"""Selected knowledge-gap questions as items in the Executive window."""

from __future__ import annotations

from .. import knowledge_gaps
from .gap_store import GapStore


BUDGET = 3


def knowledge_gap_items(store=None) -> list[dict]:
    """Return selected, unanswered knowledge gaps in window item format."""
    if store is None:
        store = GapStore()

    open_gaps = store.gaps()
    by_id = {gap["id"]: gap for gap in open_gaps}
    selected = knowledge_gaps.select_questions(
        open_gaps,
        budget=BUDGET,
        asked_ids=store.answered_ids(),
    )

    return [
        {
            "id": f"knowledge-gap:{entry['id']}",
            "kind": "knowledge_gap_question",
            "title": entry["question"],
            "tab": by_id[entry["id"]]["tab"],
            "score": entry["score"],
            "source": "Knowledge gap",
            "sensitivity": "personal",
            "why": entry["why"],
            "context": {
                "gap_id": entry["id"],
                "topic": entry.get("topic"),
                "project": by_id[entry["id"]].get("project"),
            },
        }
        for entry in selected["ask"]
    ]
