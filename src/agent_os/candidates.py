from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable

from .ingestion import IngestionLedger, stable_stage_id, stable_work_id
from .normalization import normalise_text as _normalise
from .paths import ROOT
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


CANDIDATE_LOCAL_DIR = ROOT / ".agent-local" / "candidates"
CANDIDATE_PROCESSOR_VERSION = "candidate-records@1"


def _fingerprint(project_id: str, kind: str, statement: str) -> str:
    source = f"{project_id}\0{kind}\0{_normalise(statement)}"
    return hashlib.sha256(source.encode("utf-8")).hexdigest()


def load_candidates_incremental(
    project_id: str,
    *,
    source_dir: Path | None = None,
    ledger_path: Path | None = None,
    processor_version: str = CANDIDATE_PROCESSOR_VERSION,
    before_parse: Callable[[Path], None] | None = None,
) -> dict[str, Any]:
    """Read local candidate records through the restart-safe ingestion ledger.

    Candidate JSON remains canonical on disk. The local ledger tracks only
    names, hashes, processing state and checkpoints, so a resumed read never
    changes the review/promotion boundary or copies record content into the
    ledger.
    """
    directory = Path(source_dir) if source_dir is not None else _candidate_dir(project_id)
    target_ledger = Path(ledger_path or (CANDIDATE_LOCAL_DIR / f"{project_id}.json"))
    work_id = stable_work_id("candidate-records", project_id)
    ledger = IngestionLedger(
        target_ledger,
        source="candidate-record",
        work_id=work_id,
        stage_id=stable_stage_id(work_id, "read"),
        processor_version=processor_version,
    )
    records: list[dict[str, Any]] = []
    stats = {
        "checked": 0,
        "queued": 0,
        "reprocessed": 0,
        "resumed": 0,
        "skipped": 0,
        "errors": 0,
    }
    paths = sorted(directory.glob("*.json")) if directory.exists() else []
    for path in paths:
        stats["checked"] += 1
        raw = path.read_bytes()
        source_key = path.name
        queued = ledger.enqueue(source_key, content=raw, processor_version=processor_version)
        if queued["action"] == "queued":
            stats["queued"] += 1
        elif queued["action"] == "requeued":
            stats["reprocessed"] += 1

        item_id = str(queued["item_id"])
        claimed = ledger.claim(1) if queued["status"] != "processed" else []
        if claimed:
            if claimed[0]["item_id"] != item_id:
                raise RuntimeError(f"candidate ledger claimed an unexpected item: {claimed[0]['item_id']}")
            if int(claimed[0].get("attempts", 0)) > 1:
                stats["resumed"] += 1
        elif queued["action"] == "duplicate":
            stats["skipped"] += 1
        else:
            continue

        try:
            if before_parse is not None:
                before_parse(path)
            record = json.loads(raw.decode("utf-8"))
            if not isinstance(record, dict):
                raise ValueError("candidate record must contain a JSON object")
            records.append(record)
            if claimed:
                ledger.complete(item_id, output_refs=(f"candidate-record:{source_key}",))
            ledger.checkpoint(source_key, **stats)
        except (OSError, ValueError, UnicodeError) as exc:
            stats["errors"] += 1
            if claimed:
                ledger.fail(item_id, str(exc), retryable=True)
            ledger.checkpoint(source_key, **stats)
            raise

    stats["records"] = len(records)
    return {"records": records, "stats": stats, "checkpoint": ledger.status()["checkpoint"]}


def _load_candidates(project_id: str) -> list[dict[str, Any]]:
    return list(load_candidates_incremental(project_id)["records"])


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


def stage_candidates(
    project_id: str,
    task_summary: str,
    candidates: Iterable[dict[str, Any]],
    source_agent: str | None = None,
    source_session: str | None = None,
) -> dict[str, Any]:
    """Persist reviewable candidate events; this function never promotes them."""
    project = get_project(project_id)
    existing = {record.get("fingerprint"): record for record in _load_candidates(project["id"])}
    created: list[dict[str, Any]] = []
    duplicates: list[dict[str, Any]] = []
    now = datetime.now(timezone.utc).isoformat()
    for supplied in candidates:
        candidate = dict(supplied)
        _require_candidate(candidate)
        fingerprint = _fingerprint(project["id"], candidate["kind"], candidate["statement"])
        if fingerprint in existing:
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
