from __future__ import annotations

from pathlib import Path
from typing import Any

from .knowledge_context import context as lore_context


def suggest_tags(item_name: str, allowed_tags: list[str], description: str | None = None, library_id: str = "elder-scrolls", continuities: list[str] | None = None, char_budget: int = 2400, path: Path | None = None) -> dict[str, Any]:
    """Prepare a cheap, bounded KF tagging packet. Never invents taxonomy values."""
    if not allowed_tags:
        raise ValueError("allowed_tags must contain the KF-owned taxonomy")
    allowed = list(dict.fromkeys(t.strip() for t in allowed_tags if t.strip()))
    query = item_name if not description else f"{item_name} {description}"
    lore = lore_context(query, library_id=library_id, continuities=continuities, char_budget=char_budget, path=path)

    haystack = " ".join(
        [str(x.get("name", "")) + " " + str(x.get("description", "")) for x in lore["entities"]]
        + [str(x.get("text", "")) for x in lore["evidence"]]
        + [str(x.get("predicate", "")) + " " + str(x.get("object", "")) for x in lore["claims"]]
    ).lower()

    deterministic = [tag for tag in allowed if tag.lower() in haystack]
    return {
        "consumer": "knowledge-framework",
        "item_name": item_name,
        "library_id": library_id,
        "continuities": lore["continuities"],
        "allowed_tags": allowed,
        "deterministic_matches": deterministic,
        "needs_semantic_mapping": not bool(deterministic),
        "lore_packet": lore,
        "policy": {
            "taxonomy_authority": "knowledge-framework",
            "invent_tags": False,
            "persist_suggestions_as_confirmed": False,
        },
    }
