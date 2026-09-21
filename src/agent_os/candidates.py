from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from .paths import ROOT
from .locking import canonical_write
from .privacy import require_private_safe
from .registry import get_project
from .storage import load_json, write_json


KINDS = {
    "decision_candidate",
    "lesson_candidate",
    "skill_candidate",
    "skill_patch_candidate",
    "preference_candidate",
    "project_state_candidate",
    "prompt_optimization_candidate",
    "test_candidate",
    "deterministic_rule_candidate",
    "documentation_candidate",
}
STATUSES = {"candidate", "rejected", "merged", "promoted", "superseded"}


def _candidate_dir(project_id: str) -> Path:
    return ROOT / "projects" / project_id / "candidates"


def _normalise(value: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", value.casefold()))


def _fingerprint(project_id: str, kind: str, statement: str) -> str:
    source = f"{project_id}\0{kind}\0{_normalise(statement)}"
    return hashlib.sha256(source.encode("utf-8")).hexdigest()


def _load_candidates(project_id: str) -> list[dict[str, Any]]:
    directory = _candidate_dir(project_id)
    records: list[dict[str, Any]] = []
    for path in sorted(directory.glob("*.json")) if directory.exists() else []:
        records.append(load_json(path))
    return records


def _require_candidate(candidate: dict[str, Any]) -> None:
    kind = candidate.get("kind")
    statement = candidate.get("statement")
    if kind not in KINDS:
        raise ValueError(f"unsupported candidate kind: {kind}")
    if not isinstance(statement, str) or not statement.strip():
        raise ValueError("candidate statement is required")
    evidence = candidate.get("evidence", [])
    if not isinstance(evidence, list) or not all(isinstance(item, str) and item.strip() for item in evidence):
        raise ValueError("candidate evidence must be a list of non-empty strings")
    confidence = candidate.get("confidence")
    if confidence is not None and (not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1):
        raise ValueError("candidate confidence must be between 0 and 1")


@canonical_write
def stage_candidates(
    project_id: str,
    task_summary: str,
    candidates: Iterable[dict[str, Any]],
    source_agent: str | None = None,
    source_session: str | None = None,
    task_id: str | None = None,
) -> dict[str, Any]:
    """Persist reviewable candidate events; this function never promotes them."""
    project = get_project(project_id)
    candidates = list(candidates)
    require_private_safe({"summary": task_summary, "candidates": candidates, "agent": source_agent, "session": source_session, "task_id": task_id}, "candidates")
    for item in candidates:
        _require_candidate(item)
    existing = {record.get("fingerprint"): record for record in _load_candidates(project["id"])}
    created: list[dict[str, Any]] = []
    duplicates: list[dict[str, Any]] = []
    now = datetime.now(timezone.utc).isoformat()
    for supplied in candidates:
        candidate = dict(supplied)
        _require_candidate(candidate)
        fingerprint = _fingerprint(project["id"], candidate["kind"], candidate["statement"])
        if fingerprint in existing:
            if task_id and task_id not in existing[fingerprint].get("task_ids", []):
                existing[fingerprint].setdefault("task_ids", []).append(task_id)
                write_json(_candidate_dir(project["id"]) / f"{existing[fingerprint]['id']}.json", existing[fingerprint])
            duplicates.append({"id": existing[fingerprint]["id"], "fingerprint": fingerprint})
            continue
        record = {
            "id": f"candidate-{fingerprint[:16]}",
            "kind": candidate["kind"],
            "project": project["id"],
            "statement": candidate["statement"].strip(),
            "evidence": list(candidate.get("evidence", [])),
            "confidence": candidate.get("confidence"),
            "source_agent": source_agent,
            "source_session": source_session,
            "task_summary": task_summary.strip(),
            "status": "candidate",
            "created_at": now,
            "resolved_at": None,
            "fingerprint": fingerprint,
            "task_ids": [task_id] if task_id else [],
        }
        write_json(_candidate_dir(project["id"]) / f"{record['id']}.json", record)
        existing[fingerprint] = record
        created.append(record)
    return {"project": project["id"], "staged": created, "duplicates": duplicates, "promotion": "requires curator action"}


def candidate_status(project_id: str) -> dict[str, Any]:
    project = get_project(project_id)
    records = _load_candidates(project["id"])
    counts = {status: sum(record.get("status") == status for record in records) for status in sorted(STATUSES)}
    return {"project": project["id"], "counts": counts, "candidates": records}


def _promoted_path() -> Path:
    return ROOT / "memory" / "promoted-candidates.json"


@canonical_write
def curate_candidates(project_id: str, candidate_ids: Iterable[str] | None = None, action: str = "review") -> dict[str, Any]:
    """Review staged candidates. Promotion is explicit and produces canonical Git-tracked data."""
    project = get_project(project_id)
    selected = set(candidate_ids or [])
    records = [record for record in _load_candidates(project["id"]) if not selected or record["id"] in selected]
    if selected and len(records) != len(selected):
        found = {record["id"] for record in records}
        raise KeyError(f"unknown candidate ids: {', '.join(sorted(selected - found))}")
    if action not in {"review", "reject", "promote"}:
        raise ValueError("action must be review, reject, or promote")
    results: list[dict[str, Any]] = []
    promoted: list[dict[str, Any]] = []
    existing_memory = load_json(_promoted_path()) if _promoted_path().exists() else {"schema_version": 1, "entries": []}
    known = {entry.get("fingerprint") for entry in existing_memory.get("entries", [])}
    for record in records:
        path = _candidate_dir(project["id"]) / f"{record['id']}.json"
        if record.get("status") != "candidate":
            results.append({"id": record["id"], "outcome": "skipped", "reason": f"already {record.get('status')}"})
            continue
        has_evidence = bool(record.get("evidence"))
        confidence = record.get("confidence")
        material = record["kind"] in {"decision_candidate", "skill_candidate", "skill_patch_candidate", "project_state_candidate", "deterministic_rule_candidate"}
        review = {
            "deterministic_checks": {"valid_kind": record.get("kind") in KINDS, "has_evidence": has_evidence},
            "peer_review_required": material,
            "reason": "material candidate requires independent evidence review" if material else "routine candidate; deterministic checks first",
        }
        if action == "review":
            results.append({"id": record["id"], "outcome": "review_required", "review": review})
            continue
        if action == "reject":
            record["status"] = "rejected"
            record["resolved_at"] = datetime.now(timezone.utc).isoformat()
            write_json(path, record)
            results.append({"id": record["id"], "outcome": "rejected"})
            continue
        if not has_evidence or (confidence is not None and confidence < 0.7):
            results.append({"id": record["id"], "outcome": "not_promoted", "reason": "evidence and confidence threshold not met", "review": review})
            continue
        if material:
            results.append({"id": record["id"], "outcome": "review_required", "review": review})
            continue
        require_private_safe(record, "candidate promotion")
        if record.get("fingerprint") in known:
            record["status"] = "merged"
            record["resolved_at"] = datetime.now(timezone.utc).isoformat()
            write_json(path, record)
            results.append({"id": record["id"], "outcome": "merged"})
            continue
        record["status"] = "promoted"
        record["resolved_at"] = datetime.now(timezone.utc).isoformat()
        write_json(path, record)
        promoted.append(record)
        known.add(record.get("fingerprint"))
        results.append({"id": record["id"], "outcome": "promoted", "canonical_path": str(_promoted_path())})
    if promoted:
        existing_memory.setdefault("entries", []).extend(promoted)
        write_json(_promoted_path(), existing_memory)
    return {"project": project["id"], "action": action, "results": results, "canonical_data_is_git_versioned": bool(promoted)}
