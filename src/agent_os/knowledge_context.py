from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .knowledge import search_lore
from .knowledge_continuity import active_continuities, search_evidence_in_continuity, verify_claim_in_continuity

CLAIM_HINTS = re.compile(r"\b(is|was|were|did|does|created|killed|became|caused|means|true|canon|accurate)\b", re.I)
EVIDENCE_HINTS = re.compile(r"\b(source|evidence|quote|text|book|dialogue|according|account|contradict|why|how)\b", re.I)


def plan(query: str) -> dict[str, Any]:
    claim_like = bool(CLAIM_HINTS.search(query))
    evidence_like = bool(EVIDENCE_HINTS.search(query))
    if claim_like and not evidence_like:
        return {"mode": "claim", "calls": ["verify_claim_in_continuity"]}
    if evidence_like:
        return {"mode": "evidence", "calls": ["search_evidence_in_continuity", "search_lore"]}
    return {"mode": "entity", "calls": ["search_lore"]}


def context(query: str, library_id: str = "elder-scrolls", char_budget: int = 5000, path: Path | None = None, continuities: list[str] | None = None) -> dict[str, Any]:
    """Return a compact lore packet scoped to explicitly active continuities."""
    if char_budget < 500:
        raise ValueError("char_budget must be at least 500")
    active = active_continuities(continuities)
    route = plan(query)
    packet: dict[str, Any] = {"library_id": library_id, "query": query, "continuities": active, "route": route, "entities": [], "evidence": [], "claims": []}
    if route["mode"] == "entity":
        packet["entities"] = search_lore(query, library_id, limit=6, char_budget=char_budget, path=path)["results"]
    elif route["mode"] == "claim":
        packet["claims"] = verify_claim_in_continuity(query, library_id, active, limit=6, path=path)["evidence"]
        if not packet["claims"]:
            packet["route"]["fallback"] = "search_evidence_in_continuity"
            packet["evidence"] = search_evidence_in_continuity(query, library_id, active, limit=5, char_budget=char_budget, path=path)["results"]
    else:
        evidence_budget = max(500, int(char_budget * 0.72))
        entity_budget = max(500, char_budget - evidence_budget)
        packet["evidence"] = search_evidence_in_continuity(query, library_id, active, limit=5, char_budget=evidence_budget, path=path)["results"]
        packet["entities"] = search_lore(query, library_id, limit=4, char_budget=entity_budget, path=path)["results"]
    packet["approx_chars"] = len(json.dumps(packet, ensure_ascii=False))
    return packet
