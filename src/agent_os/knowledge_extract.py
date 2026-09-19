from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .knowledge import evidence_chunk, upsert_claim

ALLOWED_STATUSES = {"asserted", "disputed", "superseded", "overlay"}


def claim_candidate(subject_id: str, predicate: str, object_value: Any, evidence_chunk_id: str, *, library_id: str = "elder-scrolls", status: str = "asserted", qualifiers: dict | None = None, path: Path | None = None) -> dict:
    """Build a deterministic claim candidate anchored to an existing evidence chunk.

    This function deliberately does not call a model. A model or deterministic extractor
    may propose fields, but this boundary validates and binds them to stored evidence.
    """
    chunk = evidence_chunk(evidence_chunk_id, path)
    if chunk["library_id"] != library_id:
        raise ValueError("evidence chunk belongs to a different knowledge library")
    if status not in ALLOWED_STATUSES:
        raise ValueError(f"unsupported claim status: {status}")
    predicate = predicate.strip()
    if not subject_id.strip() or not predicate:
        raise ValueError("subject_id and predicate are required")
    fingerprint = json.dumps([library_id, subject_id, predicate, object_value, evidence_chunk_id], sort_keys=True, ensure_ascii=False)
    claim_id = "claim:" + hashlib.sha256(fingerprint.encode("utf-8")).hexdigest()[:20]
    return {
        "id": claim_id, "library_id": library_id, "subject_id": subject_id,
        "predicate": predicate, "object": object_value, "qualifiers": qualifiers or {},
        "citations": [{"source_id": chunk["source_id"], "locator": chunk["locator"], "evidence_chunk_id": evidence_chunk_id, "evidence_hash": chunk["text_hash"]}],
        "status": status,
    }


def accept_claim(candidate: dict, path: Path | None = None) -> dict:
    upsert_claim(candidate, path)
    return candidate
