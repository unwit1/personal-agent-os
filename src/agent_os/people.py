"""Local-first person and relationship graph.

The database intentionally lives under .agent-local. Git may contain schemas,
code and sanitized relationship summaries, but raw identifiers and private
third-party evidence belong here.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Any

from .paths import ROOT
from .source_attribution import validate_source_actor
from .timestamps import utc_now_iso

DEFAULT_DB = ROOT / ".agent-local" / "people" / "people.sqlite3"
SANITIZED_CONTEXT = ROOT / "profile" / "relationship-context.json"
PRIVACY_CLASSES = {"personal_summary", "restricted_detail", "work_context", "public_creator"}
STATUSES = {"candidate", "active", "historical", "archived", "rejected"}


def _id(prefix: str, *parts: Any) -> str:
    body = "\x1f".join("" if part is None else str(part) for part in parts)
    return f"{prefix}:{hashlib.sha256(body.encode('utf-8')).hexdigest()[:20]}"


class PeopleStore:
    def __init__(self, path: Path | None = None) -> None:
        self.path = Path(path or DEFAULT_DB)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.path)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS people (
              person_id TEXT PRIMARY KEY, display_name TEXT NOT NULL, domain TEXT NOT NULL,
              status TEXT NOT NULL, privacy_class TEXT NOT NULL,
              identity_confidence REAL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS aliases (
              alias_id TEXT PRIMARY KEY, person_id TEXT NOT NULL, alias TEXT NOT NULL,
              source_ref TEXT, identity_confidence REAL, created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_alias_text ON aliases(alias);
            CREATE TABLE IF NOT EXISTS relationships (
              edge_id TEXT PRIMARY KEY, subject_id TEXT NOT NULL, predicate TEXT NOT NULL,
              object_id TEXT, object_label TEXT, domain TEXT NOT NULL, status TEXT NOT NULL,
              identity_confidence REAL, relationship_confidence REAL,
              valid_from TEXT, valid_to TEXT, privacy_class TEXT NOT NULL,
              created_at TEXT NOT NULL, updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS evidence (
              evidence_id TEXT PRIMARY KEY, target_type TEXT NOT NULL, target_id TEXT NOT NULL,
              source_type TEXT NOT NULL, source_ref TEXT NOT NULL, source_actor TEXT NOT NULL,
              observed_at TEXT, confidence REAL, note TEXT, created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS identity_candidates (
              candidate_id TEXT PRIMARY KEY, label TEXT NOT NULL, domain TEXT NOT NULL,
              status TEXT NOT NULL, rationale TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL
            );
            """
        )
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()

    def __enter__(self) -> "PeopleStore":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    def upsert_person(
        self, display_name: str, *, person_id: str | None = None, domain: str = "personal",
        status: str = "active", privacy_class: str = "personal_summary",
        identity_confidence: float | None = None,
    ) -> str:
        if status not in STATUSES:
            raise ValueError(f"unsupported person status: {status}")
        if privacy_class not in PRIVACY_CLASSES:
            raise ValueError(f"unsupported privacy class: {privacy_class}")
        pid = person_id or _id("person", domain, display_name.casefold())
        stamp = utc_now_iso()
        self.conn.execute(
            "INSERT INTO people VALUES (?,?,?,?,?,?,?,?) "
            "ON CONFLICT(person_id) DO UPDATE SET display_name=excluded.display_name,domain=excluded.domain,"
            "status=excluded.status,privacy_class=excluded.privacy_class,"
            "identity_confidence=excluded.identity_confidence,updated_at=excluded.updated_at",
            (pid, display_name, domain, status, privacy_class, identity_confidence, stamp, stamp),
        )
        self.conn.commit()
        return pid

    def add_alias(self, person_id: str, alias: str, *, source_ref: str | None = None, identity_confidence: float | None = None) -> str:
        aid = _id("alias", person_id, alias.casefold(), source_ref or "")
        self.conn.execute(
            "INSERT OR REPLACE INTO aliases VALUES (?,?,?,?,?,?)",
            (aid, person_id, alias, source_ref, identity_confidence, utc_now_iso()),
        )
        self.conn.commit()
        return aid

    def alias_candidates(self, alias: str) -> list[dict[str, Any]]:
        """Return every exact alias candidate. Never silently merge same-name people."""
        rows = self.conn.execute(
            "SELECT p.*,a.alias,a.identity_confidence AS alias_confidence,a.source_ref "
            "FROM aliases a JOIN people p ON p.person_id=a.person_id WHERE lower(a.alias)=lower(?) "
            "ORDER BY COALESCE(a.identity_confidence,0) DESC,p.person_id",
            (alias,),
        ).fetchall()
        return [dict(row) for row in rows]

    def add_relationship(
        self, subject_id: str, predicate: str, *, object_id: str | None = None,
        object_label: str | None = None, domain: str = "personal", status: str = "active",
        identity_confidence: float | None = None, relationship_confidence: float | None = None,
        valid_from: str | None = None, valid_to: str | None = None,
        privacy_class: str = "personal_summary",
    ) -> str:
        if not object_id and not object_label:
            raise ValueError("relationship requires object_id or object_label")
        if status not in STATUSES:
            raise ValueError(f"unsupported relationship status: {status}")
        if privacy_class not in PRIVACY_CLASSES:
            raise ValueError(f"unsupported privacy class: {privacy_class}")
        edge = _id("rel", subject_id, predicate, object_id or object_label, valid_from or "", valid_to or "")
        stamp = utc_now_iso()
        self.conn.execute(
            "INSERT OR REPLACE INTO relationships VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (edge, subject_id, predicate, object_id, object_label, domain, status,
             identity_confidence, relationship_confidence, valid_from, valid_to,
             privacy_class, stamp, stamp),
        )
        self.conn.commit()
        return edge

    def add_evidence(
        self, target_type: str, target_id: str, *, source_type: str, source_ref: str,
        source_actor: str, observed_at: str | None = None, confidence: float | None = None,
        note: str | None = None,
    ) -> str:
        actor = validate_source_actor(source_actor)
        assert actor is not None
        eid = _id("evidence", target_type, target_id, source_type, source_ref, observed_at or "")
        self.conn.execute(
            "INSERT OR REPLACE INTO evidence VALUES (?,?,?,?,?,?,?,?,?,?)",
            (eid, target_type, target_id, source_type, source_ref, actor, observed_at, confidence, note, utc_now_iso()),
        )
        self.conn.commit()
        return eid

    def relationships_for(self, person_id: str) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            "SELECT * FROM relationships WHERE subject_id=? OR object_id=? "
            "ORDER BY COALESCE(valid_from,''),edge_id",
            (person_id, person_id),
        ).fetchall()
        return [dict(row) for row in rows]

    def stats(self) -> dict[str, Any]:
        return {
            "path": str(self.path),
            "people": self.conn.execute("SELECT COUNT(*) FROM people").fetchone()[0],
            "aliases": self.conn.execute("SELECT COUNT(*) FROM aliases").fetchone()[0],
            "relationships": self.conn.execute("SELECT COUNT(*) FROM relationships").fetchone()[0],
            "evidence": self.conn.execute("SELECT COUNT(*) FROM evidence").fetchone()[0],
            "identity_candidates": self.conn.execute("SELECT COUNT(*) FROM identity_candidates WHERE status='candidate'").fetchone()[0],
            "local_private": True,
        }

    def stage_identity_candidate(self, label: str, *, domain: str, rationale: str) -> str:
        cid = _id("candidate", domain, label.casefold(), rationale)
        stamp = utc_now_iso()
        self.conn.execute(
            "INSERT OR IGNORE INTO identity_candidates VALUES (?,?,?,?,?,?,?)",
            (cid, label, domain, "candidate", rationale, stamp, stamp),
        )
        self.conn.commit()
        return cid



def bootstrap_from_sanitized_context(
    context_path: Path | None = None,
    *,
    db_path: Path | None = None,
) -> dict[str, Any]:
    """Seed the local graph from Git-safe relationship context.

    This is idempotent. It copies only the already-sanitized relationship
    projection; it does not import raw mail, contact identifiers, or private
    third-party details.
    """
    path = Path(context_path or SANITIZED_CONTEXT)
    data = json.loads(path.read_text(encoding="utf-8"))
    durable = data.get("durable_relationship_context") or {}
    unresolved = data.get("unresolved_identity_candidates") or []
    created: dict[str, Any] = {"people": [], "relationships": [], "candidates": []}

    with PeopleStore(db_path) as store:
        user_id = store.upsert_person(
            "User",
            person_id="person:user",
            domain="personal",
            status="active",
            privacy_class="personal_summary",
            identity_confidence=1.0,
        )
        created["people"].append(user_id)

        partner = durable.get("partner")
        if isinstance(partner, dict) and partner.get("display_name"):
            partner_id = store.upsert_person(
                str(partner["display_name"]),
                person_id=str(partner.get("person_id") or _id("person", "personal", str(partner["display_name"]).casefold())),
                domain="personal",
                status="active",
                privacy_class="personal_summary",
                identity_confidence=1.0 if partner.get("identity_confidence") == "stated" else None,
            )
            store.add_alias(
                partner_id,
                str(partner["display_name"]),
                source_ref=f"{path.name}#durable_relationship_context.partner",
                identity_confidence=1.0 if partner.get("identity_confidence") == "stated" else None,
            )
            edge = store.add_relationship(
                user_id,
                str(partner.get("relationship_type") or "romantic_partner"),
                object_id=partner_id,
                domain="personal",
                status="active",
                identity_confidence=1.0,
                relationship_confidence=1.0 if partner.get("relationship_confidence") == "stated" else None,
                privacy_class="personal_summary",
            )
            store.add_evidence(
                "relationship",
                edge,
                source_type="sanitized_profile",
                source_ref=f"{path.name}#durable_relationship_context.partner",
                source_actor="user_confirmed",
                observed_at=str(data.get("updated_at") or ""),
                confidence=1.0,
                note="Sanitized projection only; raw relationship evidence remains outside Git.",
            )
            created["people"].append(partner_id)
            created["relationships"].append(edge)

        family = durable.get("family")
        if isinstance(family, dict) and family.get("sibling_structure"):
            edge = store.add_relationship(
                user_id,
                "family_structure",
                object_label=str(family["sibling_structure"]),
                domain="personal",
                status="active",
                identity_confidence=1.0,
                relationship_confidence=1.0,
                privacy_class="restricted_detail",
            )
            store.add_evidence(
                "relationship",
                edge,
                source_type="sanitized_profile",
                source_ref=f"{path.name}#durable_relationship_context.family",
                source_actor="user_confirmed",
                observed_at=str(data.get("updated_at") or ""),
                confidence=1.0,
                note="Sanitized family-structure statement; no sibling identities imported.",
            )
            created["relationships"].append(edge)

        for candidate in unresolved:
            if not isinstance(candidate, dict) or not candidate.get("label"):
                continue
            cid = store.stage_identity_candidate(
                str(candidate["label"]),
                domain=str(candidate.get("domain") or "personal"),
                rationale=str(candidate.get("reason") or "unresolved identity candidate from sanitized context"),
            )
            created["candidates"].append(cid)

        created["stats"] = store.stats()
    return created


def people_status(db_path: Path | None = None) -> dict[str, Any]:
    with PeopleStore(db_path) as store:
        return store.stats()


def alias_lookup(alias: str, db_path: Path | None = None) -> dict[str, Any]:
    with PeopleStore(db_path) as store:
        return {"query": alias, "matches": store.alias_candidates(alias), "local_private": True}


def relationship_lookup(person_id: str, db_path: Path | None = None) -> dict[str, Any]:
    with PeopleStore(db_path) as store:
        return {"person_id": person_id, "relationships": store.relationships_for(person_id), "local_private": True}
