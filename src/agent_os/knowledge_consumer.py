from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .knowledge_context import context as lore_context

DEFAULT_MAPPING_PATH = Path("knowledge/consumers/knowledge-framework-confirmed-mappings.json")


def _key(item_id: str, library_id: str, continuities: list[str]) -> tuple[str, str, tuple[str, ...]]:
    return item_id, library_id, tuple(sorted(continuities))


def load_confirmed_mappings(mapping_path: Path = DEFAULT_MAPPING_PATH) -> list[dict[str, Any]]:
    if not mapping_path.exists():
        return []
    return json.loads(mapping_path.read_text(encoding="utf-8")).get("mappings", [])


def find_confirmed_mapping(item_id: str, library_id: str, continuities: list[str], mapping_path: Path = DEFAULT_MAPPING_PATH) -> dict[str, Any] | None:
    wanted = _key(item_id, library_id, continuities)
    for row in load_confirmed_mappings(mapping_path):
        if _key(row["item_id"], row["library_id"], row["continuities"]) == wanted:
            return row
    return None


def suggest_tags(item_name: str, allowed_tags: list[str], description: str | None = None, library_id: str = "elder-scrolls", continuities: list[str] | None = None, char_budget: int = 2400, path: Path | None = None, item_id: str | None = None, mapping_path: Path = DEFAULT_MAPPING_PATH) -> dict[str, Any]:
    """Reuse confirmed KF mappings first; otherwise build the cheapest bounded tagging packet."""
    if not allowed_tags:
        raise ValueError("allowed_tags must contain the KF-owned taxonomy")
    allowed = list(dict.fromkeys(t.strip() for t in allowed_tags if t.strip()))
    active = continuities or ["tes-base"]

    if item_id:
        cached = find_confirmed_mapping(item_id, library_id, active, mapping_path)
        if cached:
            tags = [tag for tag in cached.get("tags", []) if tag in allowed]
            return {
                "consumer": "knowledge-framework", "item_id": item_id, "item_name": item_name,
                "library_id": library_id, "continuities": active, "allowed_tags": allowed,
                "confirmed_tags": tags, "deterministic_matches": [], "needs_semantic_mapping": False,
                "cache_hit": True, "lore_packet": None,
                "policy": {"taxonomy_authority": "knowledge-framework", "invent_tags": False, "persist_suggestions_as_confirmed": False},
            }

    query = item_name if not description else f"{item_name} {description}"
    lore = lore_context(query, library_id=library_id, continuities=active, char_budget=char_budget, path=path)
    haystack = " ".join(
        [str(x.get("name", "")) + " " + str(x.get("description", "")) for x in lore["entities"]]
        + [str(x.get("text", "")) for x in lore["evidence"]]
        + [str(x.get("predicate", "")) + " " + str(x.get("object", "")) for x in lore["claims"]]
    ).lower()
    deterministic = [tag for tag in allowed if tag.lower() in haystack]
    return {
        "consumer": "knowledge-framework", "item_id": item_id, "item_name": item_name,
        "library_id": library_id, "continuities": lore["continuities"], "allowed_tags": allowed,
        "confirmed_tags": [], "deterministic_matches": deterministic,
        "needs_semantic_mapping": not bool(deterministic), "cache_hit": False, "lore_packet": lore,
        "policy": {"taxonomy_authority": "knowledge-framework", "invent_tags": False, "persist_suggestions_as_confirmed": False},
    }


def semantic_mapping_request(result: dict[str, Any]) -> dict[str, Any] | None:
    """Return the minimal payload for a cheap classifier only when rules/cache were insufficient."""
    if not result.get("needs_semantic_mapping"):
        return None
    lore = result.get("lore_packet") or {}
    return {
        "task": "choose_kf_tags",
        "allowed_tags": result["allowed_tags"],
        "item_name": result["item_name"],
        "continuities": result["continuities"],
        "evidence": lore.get("evidence", []),
        "entities": lore.get("entities", []),
        "instruction": "Choose zero or more allowed_tags supported by the evidence. Never create a tag. Return tags plus short evidence references.",
    }
