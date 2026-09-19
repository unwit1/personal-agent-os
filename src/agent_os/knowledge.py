from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path
from typing import Any

from .paths import INDEX_DIR

DB_PATH = INDEX_DIR / "knowledge.sqlite"


def connect(path: Path | None = None) -> sqlite3.Connection:
    target = path or DB_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(target)
    db.row_factory = sqlite3.Row
    db.executescript("""
    CREATE TABLE IF NOT EXISTS sources (
      id TEXT PRIMARY KEY, library_id TEXT NOT NULL, title TEXT NOT NULL,
      source_class TEXT NOT NULL, uri TEXT, metadata TEXT NOT NULL DEFAULT '{}'
    );
    CREATE TABLE IF NOT EXISTS entities (
      id TEXT PRIMARY KEY, library_id TEXT NOT NULL, name TEXT NOT NULL,
      entity_type TEXT NOT NULL, aliases TEXT NOT NULL DEFAULT '[]',
      description TEXT, metadata TEXT NOT NULL DEFAULT '{}'
    );
    CREATE TABLE IF NOT EXISTS claims (
      id TEXT PRIMARY KEY, library_id TEXT NOT NULL, subject_id TEXT NOT NULL,
      predicate TEXT NOT NULL, object_json TEXT NOT NULL, qualifiers TEXT NOT NULL DEFAULT '{}',
      citations TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'asserted'
    );
    CREATE TABLE IF NOT EXISTS contradictions (
      id TEXT PRIMARY KEY, library_id TEXT NOT NULL, claim_ids TEXT NOT NULL,
      kind TEXT NOT NULL, notes TEXT, resolution TEXT
    );
    CREATE INDEX IF NOT EXISTS idx_entities_library_name ON entities(library_id, name);
    CREATE INDEX IF NOT EXISTS idx_claims_library_subject ON claims(library_id, subject_id);
    """)
    return db


def upsert_source(source: dict[str, Any], path: Path | None = None) -> None:
    with connect(path) as db:
        db.execute("INSERT OR REPLACE INTO sources VALUES (?,?,?,?,?,?)", (
            source["id"], source["library_id"], source["title"], source["source_class"],
            source.get("uri"), json.dumps(source.get("metadata", {}), ensure_ascii=False)))


def upsert_entity(entity: dict[str, Any], path: Path | None = None) -> None:
    with connect(path) as db:
        db.execute("INSERT OR REPLACE INTO entities VALUES (?,?,?,?,?,?,?)", (
            entity["id"], entity["library_id"], entity["name"], entity["entity_type"],
            json.dumps(entity.get("aliases", []), ensure_ascii=False), entity.get("description"),
            json.dumps(entity.get("metadata", {}), ensure_ascii=False)))


def upsert_claim(claim: dict[str, Any], path: Path | None = None) -> None:
    if not claim.get("citations"):
        raise ValueError("claims require at least one citation")
    with connect(path) as db:
        db.execute("INSERT OR REPLACE INTO claims VALUES (?,?,?,?,?,?,?,?)", (
            claim["id"], claim["library_id"], claim["subject_id"], claim["predicate"],
            json.dumps(claim.get("object"), ensure_ascii=False), json.dumps(claim.get("qualifiers", {}), ensure_ascii=False),
            json.dumps(claim["citations"], ensure_ascii=False), claim.get("status", "asserted")))


def _terms(query: str) -> list[str]:
    return [t.lower() for t in re.findall(r"[\w'-]+", query) if len(t) > 1]


def _clip(value: str | None, limit: int) -> str | None:
    if value is None or len(value) <= limit:
        return value
    return value[: max(0, limit - 1)].rstrip() + "…"


def search_lore(query: str, library_id: str = "elder-scrolls", limit: int = 8, char_budget: int = 6000, path: Path | None = None) -> dict[str, Any]:
    terms = _terms(query)
    with connect(path) as db:
        rows = db.execute("SELECT * FROM entities WHERE library_id=?", (library_id,)).fetchall()
        scored = []
        for row in rows:
            hay = " ".join([row["name"], row["description"] or "", row["aliases"]]).lower()
            score = sum(3 if term in row["name"].lower() else 1 for term in terms if term in hay)
            if score:
                scored.append((score, row))
        scored.sort(key=lambda item: (-item[0], item[1]["name"].lower()))
        results, used = [], 0
        for score, row in scored[:limit]:
            item = {"id": row["id"], "name": row["name"], "entity_type": row["entity_type"], "score": score, "description": _clip(row["description"], 600)}
            size = len(json.dumps(item, ensure_ascii=False))
            if results and used + size > char_budget:
                break
            results.append(item); used += size
    return {"library_id": library_id, "query": query, "results": results, "approx_chars": used}


def get_entity(entity_id: str, library_id: str = "elder-scrolls", char_budget: int = 8000, path: Path | None = None) -> dict[str, Any]:
    with connect(path) as db:
        entity = db.execute("SELECT * FROM entities WHERE id=? AND library_id=?", (entity_id, library_id)).fetchone()
        if not entity:
            raise KeyError(f"Unknown entity: {entity_id}")
        claims = db.execute("SELECT * FROM claims WHERE subject_id=? AND library_id=? ORDER BY id", (entity_id, library_id)).fetchall()
        result = {"id": entity["id"], "name": entity["name"], "entity_type": entity["entity_type"], "description": entity["description"], "claims": []}
        used = len(json.dumps(result, ensure_ascii=False))
        for claim in claims:
            item = {"id": claim["id"], "predicate": claim["predicate"], "object": json.loads(claim["object_json"]), "status": claim["status"], "citations": json.loads(claim["citations"])}
            size = len(json.dumps(item, ensure_ascii=False))
            if result["claims"] and used + size > char_budget:
                break
            result["claims"].append(item); used += size
        result["approx_chars"] = used
        return result


def verify_claim(claim_text: str, library_id: str = "elder-scrolls", limit: int = 8, path: Path | None = None) -> dict[str, Any]:
    terms = set(_terms(claim_text))
    with connect(path) as db:
        rows = db.execute("SELECT c.*, e.name FROM claims c JOIN entities e ON e.id=c.subject_id WHERE c.library_id=?", (library_id,)).fetchall()
        matches = []
        for row in rows:
            rendered = f"{row['name']} {row['predicate']} {row['object_json']}".lower()
            overlap = len([term for term in terms if term in rendered])
            if overlap:
                matches.append((overlap, row))
        matches.sort(key=lambda item: -item[0])
        evidence = [{"claim_id": r["id"], "subject": r["name"], "predicate": r["predicate"], "object": json.loads(r["object_json"]), "citations": json.loads(r["citations"]), "overlap": score} for score, r in matches[:limit]]
    return {"query": claim_text, "evidence": evidence, "verified": bool(evidence), "note": "verified means matching stored evidence exists; it is not an independent truth judgment"}


def find_contradictions(entity_or_claim: str, library_id: str = "elder-scrolls", path: Path | None = None) -> dict[str, Any]:
    with connect(path) as db:
        rows = db.execute("SELECT * FROM contradictions WHERE library_id=?", (library_id,)).fetchall()
        matches = []
        for row in rows:
            ids = json.loads(row["claim_ids"])
            if entity_or_claim == row["id"] or entity_or_claim in ids:
                matches.append({"id": row["id"], "claim_ids": ids, "kind": row["kind"], "notes": row["notes"], "resolution": row["resolution"]})
            else:
                placeholders = ",".join("?" for _ in ids)
                if ids and db.execute(f"SELECT 1 FROM claims WHERE id IN ({placeholders}) AND subject_id=? LIMIT 1", (*ids, entity_or_claim)).fetchone():
                    matches.append({"id": row["id"], "claim_ids": ids, "kind": row["kind"], "notes": row["notes"], "resolution": row["resolution"]})
    return {"query": entity_or_claim, "contradictions": matches}
