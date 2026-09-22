from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any, Callable, Iterable

from .candidates import stage_candidates
from .ingestion import IngestionLedger, stable_stage_id, stable_work_id
from .normalization import normalise_text as _normalise
from .paths import ROOT
from .privacy import privacy_findings, require_private_safe
from .registry import get_project
from .storage import load_json, write_json
from .timestamps import utc_now_iso as _now


CHANGE_TYPES = {"bug", "feature", "refactor", "workflow", "performance", "security", "test", "documentation", "architecture", "other"}
STATUSES = {"OPEN", "ANALYZED", "PROPOSED", "IMPLEMENTED", "VERIFIED", "REJECTED", "DUPLICATE", "SUPERSEDED", "BLOCKED"}
ACTIVE_STATUSES = {"OPEN", "ANALYZED", "PROPOSED", "IMPLEMENTED", "BLOCKED"}
CHANGE_PROCESSOR_VERSION = "change-records@1"
TRANSITIONS = {
    "OPEN": {"ANALYZED", "REJECTED", "DUPLICATE", "BLOCKED"},
    "ANALYZED": {"PROPOSED", "REJECTED", "DUPLICATE", "BLOCKED"},
    "PROPOSED": {"IMPLEMENTED", "REJECTED", "SUPERSEDED", "BLOCKED"},
    "IMPLEMENTED": {"VERIFIED", "PROPOSED", "BLOCKED"},
    "VERIFIED": {"SUPERSEDED"},
    "BLOCKED": {"OPEN", "ANALYZED", "PROPOSED"},
    "DUPLICATE": set(),
    "REJECTED": set(),
    "SUPERSEDED": set(),
}


def _directory(project_id: str) -> Path:
    return ROOT / "projects" / project_id / "changes"


def _records(project_id: str) -> list[dict[str, Any]]:
    return list(load_changes_incremental(project_id)["records"])


def load_changes_incremental(
    project_id: str,
    *,
    source_dir: Path | None = None,
    ledger_path: Path | None = None,
    processor_version: str = CHANGE_PROCESSOR_VERSION,
    before_parse: Callable[[Path], None] | None = None,
) -> dict[str, Any]:
    """Read local change records through a restart-safe ingestion ledger.

    Canonical change JSON remains on disk. The ledger stores only source names,
    fingerprints, processing state, output references, and checkpoints.
    """
    directory = Path(source_dir) if source_dir is not None else _directory(project_id)
    target_ledger = Path(ledger_path or (ROOT / ".agent-local" / "changes" / f"{project_id}.json"))
    work_id = stable_work_id("change-records", project_id)
    ledger = IngestionLedger(
        target_ledger,
        source="change-record",
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
    paths = sorted(directory.glob("CR-*.json")) if directory.exists() else []
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
                raise RuntimeError(f"change ledger claimed an unexpected item: {claimed[0]['item_id']}")
            if int(claimed[0].get("attempts", 0)) > 1:
                stats["resumed"] += 1
        elif queued["action"] == "duplicate":
            stats["skipped"] += 1
        else:
            continue

        try:
            if before_parse is not None:
                before_parse(path)
            record = load_json(path)
            if not isinstance(record, dict):
                raise ValueError("change record must contain a JSON object")
            records.append(record)
            if claimed:
                ledger.complete(item_id, output_refs=(f"change-record:{source_key}",))
            ledger.checkpoint(source_key, **stats)
        except (OSError, ValueError, UnicodeError) as exc:
            stats["errors"] += 1
            if claimed:
                ledger.fail(item_id, str(exc), retryable=True)
            ledger.checkpoint(source_key, **stats)
            raise

    stats["records"] = len(records)
    return {"records": records, "stats": stats, "checkpoint": ledger.status()["checkpoint"]}


def _fingerprint(project_id: str, change_type: str, title: str, request_summary: str, components: Iterable[str], files: Iterable[str]) -> str:
    parts = [project_id, change_type, _normalise(title), _normalise(request_summary), *sorted(_normalise(item) for item in components), *sorted(_normalise(item) for item in files)]
    return hashlib.sha256("\0".join(parts).encode("utf-8")).hexdigest()


def _index(project_id: str) -> list[dict[str, Any]]:
    return [
        {
            "change_id": record["change_id"],
            "title": record["title"],
            "change_type": record["change_type"],
            "status": record["status"],
            "components": record.get("components", []),
            "updated_at": record["updated_at"],
            "fingerprint": record["fingerprint"],
        }
        for record in sorted(_records(project_id), key=lambda item: item["change_id"])
    ]


def _write(record: dict[str, Any]) -> None:
    directory = _directory(record["routing"]["project_id"])
    write_json(directory / f"{record['change_id']}.json", record)
    write_json(directory / "index.json", {"schema_version": 1, "project": record["routing"]["project_id"], "changes": _index(record["routing"]["project_id"])})


def capture_change(
    project: str,
    title: str,
    request_summary: str,
    change_type: str = "other",
    components: Iterable[str] = (),
    repository_files: Iterable[str] = (),
    routing_confidence: float = 1.0,
    source_kind: str = "manual",
    external_key: str | None = None,
    google_eligible: bool = False,
    reusable_candidate: bool = False,
) -> dict[str, Any]:
    canonical = get_project(project)["id"]
    if change_type not in CHANGE_TYPES:
        raise ValueError(f"unsupported change type: {change_type}")
    if source_kind not in {"chat", "agent", "issue", "manual", "import"}:
        raise ValueError(f"unsupported source kind: {source_kind}")
    if not 0 <= routing_confidence <= 1:
        raise ValueError("routing confidence must be between 0 and 1")
    component_items = list(dict.fromkeys(str(item).strip() for item in components if str(item).strip()))
    file_items = list(dict.fromkeys(str(item).strip() for item in repository_files if str(item).strip()))
    safe_input = {"title": title, "request_summary": request_summary, "components": component_items, "repository_files": file_items, "external_key": external_key}
    require_private_safe(safe_input, "change")
    if not title.strip() or not request_summary.strip():
        raise ValueError("change title and request summary are required")
    fingerprint = _fingerprint(canonical, change_type, title, request_summary, component_items, file_items)
    records = _records(canonical)
    for existing in records:
        same_external = external_key and any(ref.get("external_key") == external_key for ref in existing.get("source_refs", []))
        if same_external or (existing.get("fingerprint") == fingerprint and existing.get("status") not in {"REJECTED", "SUPERSEDED"}):
            if external_key and not same_external:
                existing.setdefault("source_refs", []).append({"kind": source_kind, "external_key": external_key})
                existing["updated_at"] = _now()
                _write(existing)
            return {"project": canonical, "created": False, "duplicate_of": existing["change_id"], "record": existing}
    now = _now()
    record = {
        "schema_version": 1,
        "change_id": f"CR-{fingerprint[:16]}",
        "created_at": now,
        "updated_at": now,
        "change_type": change_type,
        "status": "OPEN",
        "title": title.strip()[:180],
        "request_summary": request_summary.strip()[:3000],
        "diagnosis_summary": None,
        "fix_summary": None,
        "validation_summary": None,
        "components": component_items,
        "repository_files": file_items,
        "routing": {"project_id": canonical, "confidence": routing_confidence, "evidence": [{"kind": "explicit_project", "value": canonical}]},
        "relations": {"duplicate_of": None, "supersedes": [], "related_to": [], "merged_from": []},
        "implementation": {"commit": None, "pull_request": None, "files_changed": [], "tests": []},
        "reusable": {"candidate": bool(reusable_candidate), "lesson": None, "pattern_ids": []},
        "privacy": {"contains_raw_private_source": False, "google_eligible": bool(google_eligible), "google_block_reasons": [], "policy_version": "1"},
        "source_refs": [{"kind": source_kind, "external_key": external_key}] if external_key else [{"kind": source_kind}],
        "fingerprint": fingerprint,
    }
    _write(record)
    return {"project": canonical, "created": True, "record": record}


def get_change(project: str, change_id: str) -> dict[str, Any]:
    canonical = get_project(project)["id"]
    if not re.fullmatch(r"CR-[A-Za-z0-9._-]+", change_id):
        raise ValueError("invalid change id")
    path = _directory(canonical) / f"{change_id}.json"
    if not path.exists():
        raise KeyError(f"unknown change: {change_id}")
    return load_json(path)


def list_changes(project: str, status: str | None = None) -> list[dict[str, Any]]:
    canonical = get_project(project)["id"]
    return [record for record in _records(canonical) if status is None or record.get("status") == status]


def update_change(
    project: str,
    change_id: str,
    status: str | None = None,
    diagnosis_summary: str | None = None,
    fix_summary: str | None = None,
    validation_summary: str | None = None,
    implementation: dict[str, Any] | None = None,
    reusable_lesson: str | None = None,
) -> dict[str, Any]:
    record = get_change(project, change_id)
    updates = {"diagnosis_summary": diagnosis_summary, "fix_summary": fix_summary, "validation_summary": validation_summary, "implementation": implementation, "reusable_lesson": reusable_lesson}
    require_private_safe(updates, "change update")
    if status:
        if status not in STATUSES:
            raise ValueError(f"unsupported change status: {status}")
        if status != record["status"] and status not in TRANSITIONS[record["status"]]:
            raise ValueError(f"invalid change transition: {record['status']} -> {status}")
        if status == "VERIFIED":
            validation = validation_summary or record.get("validation_summary")
            tests = (implementation or record.get("implementation") or {}).get("tests", [])
            if not validation or not tests:
                raise ValueError("VERIFIED requires a validation summary and passing test evidence")
        record["status"] = status
    for key, value in (("diagnosis_summary", diagnosis_summary), ("fix_summary", fix_summary), ("validation_summary", validation_summary)):
        if value is not None:
            record[key] = value.strip()
    if implementation is not None:
        allowed = {"commit", "pull_request", "files_changed", "tests"}
        if set(implementation) - allowed:
            raise ValueError("unexpected implementation fields")
        record["implementation"] = {**record.get("implementation", {}), **implementation}
    if reusable_lesson is not None:
        record.setdefault("reusable", {})["candidate"] = True
        record["reusable"]["lesson"] = reusable_lesson.strip()
    record["updated_at"] = _now()
    _write(record)
    return record


def search_changes(project: str, query: str, limit: int = 8, include_terminal: bool = False) -> list[dict[str, Any]]:
    canonical = get_project(project)["id"]
    terms = set(re.findall(r"[a-z0-9]+", query.casefold()))
    scored: list[tuple[int, dict[str, Any]]] = []
    for record in _records(canonical):
        if not include_terminal and record.get("status") not in ACTIVE_STATUSES | {"VERIFIED"}:
            continue
        haystack = " ".join([record.get("title", ""), record.get("request_summary", ""), record.get("diagnosis_summary") or "", record.get("fix_summary") or "", *record.get("components", []), *record.get("repository_files", [])]).casefold()
        score = sum(3 if term in record.get("title", "").casefold() else 1 for term in terms if term in haystack)
        if score and record.get("status") in ACTIVE_STATUSES:
            score += 1
        if score or not terms:
            scored.append((score, record))
    return [record for _, record in sorted(scored, key=lambda item: (-item[0], item[1]["change_id"]))[: max(0, limit)]]


def compact_changes(project: str, task: str, limit: int = 3) -> list[dict[str, Any]]:
    return [
        {"id": record["change_id"], "title": record["title"], "status": record["status"], "type": record["change_type"], "summary": (record.get("fix_summary") or record.get("request_summary") or "")[:240]}
        for record in search_changes(project, task, limit=limit)
    ]


def google_safe_projection(project: str, change_id: str) -> dict[str, Any]:
    record = get_change(project, change_id)
    source = {
        "title": record["title"],
        "request_summary": record["request_summary"],
        "diagnosis_summary": record.get("diagnosis_summary"),
        "fix_summary": record.get("fix_summary"),
        "validation_summary": record.get("validation_summary"),
    }
    findings = privacy_findings(source)
    if not record.get("privacy", {}).get("google_eligible") or findings:
        reasons = findings or ["not_explicitly_eligible"]
        return {"allowed": False, "change_id": change_id, "block_reasons": reasons}
    source_kind = record.get("source_refs", [{}])[0].get("kind", "manual")
    projection = {
        "projection_version": 1,
        "external_key": hashlib.sha256(f"google\0{change_id}".encode("utf-8")).hexdigest()[:24],
        "change_id": change_id,
        "captured_at": record["created_at"],
        "updated_at": record["updated_at"],
        "change_type": record["change_type"],
        "status": record["status"],
        "project_id": record["routing"]["project_id"],
        "project_confidence": record["routing"]["confidence"],
        "safe_title": record["title"][:180],
        "safe_request_summary": record["request_summary"][:1200],
        "safe_diagnosis_summary": (record.get("diagnosis_summary") or "")[:1200] or None,
        "safe_fix_summary": (record.get("fix_summary") or "")[:1200] or None,
        "safe_validation_summary": (record.get("validation_summary") or "")[:800] or None,
        "reusable_candidate": bool(record.get("reusable", {}).get("candidate")),
        "source_kind": source_kind,
        "agent_os_ingested": True,
        "canonical_ref": f"projects/{record['routing']['project_id']}/changes/{change_id}.json",
        "export_policy_version": "1",
    }
    require_private_safe(projection, "safe projection")
    return {"allowed": True, "projection": projection}


def promote_change(project: str, change_id: str) -> dict[str, Any]:
    record = get_change(project, change_id)
    reusable = record.get("reusable", {})
    if record.get("status") != "VERIFIED" or not reusable.get("candidate") or not reusable.get("lesson"):
        raise ValueError("promotion requires VERIFIED status and an explicit reusable lesson")
    evidence = [record.get("validation_summary", ""), *record.get("implementation", {}).get("tests", [])]
    return stage_candidates(
        record["routing"]["project_id"],
        f"Promote reusable lesson from {change_id}",
        [{"kind": "skill_candidate", "statement": reusable["lesson"], "evidence": [item for item in evidence if item], "confidence": 0.9}],
        source_agent="change-capture",
        source_session=change_id,
    )
