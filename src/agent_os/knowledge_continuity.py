from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .knowledge import connect, search_evidence, verify_claim

DEFAULT_CONTINUITY = "tes-base"


def _continuity(value: dict[str, Any]) -> str:
    return value.get("continuity_id") or value.get("qualifiers", {}).get("continuity_id") or DEFAULT_CONTINUITY


def active_continuities(selected: list[str] | None = None) -> list[str]:
    """Base is always explicit; overlays never activate one another implicitly."""
    values = selected or [DEFAULT_CONTINUITY]
    ordered: list[str] = []
    for value in values:
        if value not in ordered:
            ordered.append(value)
    return ordered


def search_evidence_in_continuity(query: str, library_id: str = "elder-scrolls", continuities: list[str] | None = None, limit: int = 8, char_budget: int = 6000, path: Path | None = None) -> dict[str, Any]:
    active = active_continuities(continuities)
    # Existing evidence can carry continuity in source metadata while the SQLite
    # migration is staged. This keeps old indexes readable.
    broad = search_evidence(query, library_id, limit=max(limit * 4, limit), char_budget=max(char_budget * 3, char_budget), path=path)
    with connect(path) as db:
        source_continuity: dict[str, str] = {}
        for row in db.execute("SELECT id,metadata FROM sources WHERE library_id=?", (library_id,)):
            metadata = json.loads(row["metadata"] or "{}")
            source_continuity[row["id"]] = metadata.get("continuity_id", DEFAULT_CONTINUITY)
    results = []
    used = 0
    for item in broad["results"]:
        continuity_id = source_continuity.get(item["source_id"], DEFAULT_CONTINUITY)
        if continuity_id not in active:
            continue
        tagged = {**item, "continuity_id": continuity_id}
        size = len(json.dumps(tagged, ensure_ascii=False))
        if results and used + size > char_budget:
            break
        results.append(tagged)
        used += size
        if len(results) >= limit:
            break
    return {"library_id": library_id, "query": query, "continuities": active, "results": results, "approx_chars": used}


def verify_claim_in_continuity(claim_text: str, library_id: str = "elder-scrolls", continuities: list[str] | None = None, limit: int = 8, path: Path | None = None) -> dict[str, Any]:
    active = active_continuities(continuities)
    broad = verify_claim(claim_text, library_id, limit=max(limit * 4, limit), path=path)
    evidence = []
    for item in broad["evidence"]:
        # Claim continuity is stored in qualifiers until the DB migration lands.
        with connect(path) as db:
            row = db.execute("SELECT qualifiers FROM claims WHERE id=?", (item["claim_id"],)).fetchone()
        qualifiers = json.loads(row["qualifiers"] or "{}") if row else {}
        continuity_id = qualifiers.get("continuity_id", DEFAULT_CONTINUITY)
        if continuity_id in active:
            evidence.append({**item, "continuity_id": continuity_id})
        if len(evidence) >= limit:
            break
    return {"query": claim_text, "continuities": active, "evidence": evidence, "evidence_found": bool(evidence), "note": "Evidence is filtered to explicitly active continuities; overlays do not activate one another."}
