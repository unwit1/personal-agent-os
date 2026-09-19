from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .knowledge import search_evidence, search_lore, verify_claim

CLAIM_HINTS = re.compile(r"\b(is|was|were|did|does|created|killed|became|caused|means|true|canon|accurate)\b", re.I)
EVIDENCE_HINTS = re.compile(r"\b(source|evidence|quote|text|book|dialogue|according|account|contradict|why|how)\b", re.I)


def plan(query: str) -> dict[str, Any]:
    """Choose the smallest retrieval path likely to answer the question."""
    claim_like = bool(CLAIM_HINTS.search(query))
    evidence_like = bool(EVIDENCE_HINTS.search(query))
    if claim_like and not evidence_like:
        mode = "claim"
        calls = ["verify_claim"]
    elif evidence_like:
        mode = "evidence"
        calls = ["search_evidence", "search_lore"]
    else:
        mode = "entity"
        calls = ["search_lore"]
    return {"mode": mode, "calls": calls}


def context(query: str, library_id: str = "elder-scrolls", char_budget: int = 5000, path: Path | None = None) -> dict[str, Any]:
    """Return one compact lore packet without blindly invoking every retrieval surface."""
    if char_budget < 500:
        raise ValueError("char_budget must be at least 500")
    route = plan(query)
    packet: dict[str, Any] = {"library_id": library_id, "query": query, "route": route, "entities": [], "evidence": [], "claims": []}
    # Reserve budget by route. JSON overhead is intentionally kept outside the
    # retrieval budget and measured in the returned packet.
    if route["mode"] == "entity":
        packet["entities"] = search_lore(query, library_id, limit=6, char_budget=char_budget, path=path)["results"]
    elif route["mode"] == "claim":
        packet["claims"] = verify_claim(query, library_id, limit=6, path=path)["evidence"]
        # Claims may not yet have been extracted. Fall back to exact source evidence
        # rather than escalating to a model or returning an unsupported conclusion.
        if not packet["claims"]:
            packet["route"]["fallback"] = "search_evidence"
            packet["evidence"] = search_evidence(query, library_id, limit=5, char_budget=char_budget, path=path)["results"]
    else:
        evidence_budget = max(500, int(char_budget * 0.72))
        entity_budget = max(500, char_budget - evidence_budget)
        packet["evidence"] = search_evidence(query, library_id, limit=5, char_budget=evidence_budget, path=path)["results"]
        packet["entities"] = search_lore(query, library_id, limit=4, char_budget=entity_budget, path=path)["results"]
    packet["approx_chars"] = len(json.dumps(packet, ensure_ascii=False))
    return packet
