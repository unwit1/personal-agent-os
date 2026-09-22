from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any, Callable, Iterable

from .ingestion import IngestionLedger, stable_stage_id, stable_work_id
from .normalization import normalise_text as _normalise
from .paths import ROOT, project_collection_dir
from .privacy import require_private_safe
from .registry import get_project
from .storage import load_json, write_json
from .timestamps import utc_now_iso as _now


CATEGORIES = {"bug", "performance", "architecture", "missing_test", "documentation", "skill_candidate", "workflow", "security", "privacy", "other"}
STATUSES = {"candidate", "ready", "in_progress", "implemented", "verified", "rejected", "superseded", "duplicate"}
PRIORITIES = {"critical", "high", "medium", "low"}
ACTIVE_STATUSES = {"candidate", "ready", "in_progress", "implemented"}
IMPROVEMENT_PROCESSOR_VERSION = "improvement-records@1"
TRANSITIONS = {
    "candidate": {"ready", "rejected", "superseded", "duplicate"},
    "ready": {"in_progress", "rejected", "superseded", "duplicate"},
    "in_progress": {"implemented", "ready", "rejected", "superseded"},
    "implemented": {"verified", "in_progress", "rejected", "superseded"},
    "verified": {"superseded"},
    "rejected": set(),
    "superseded": set(),
    "duplicate": set(),
}


def _directory(project_id: str) -> Path:
    return project_collection_dir(project_id, "improvements", root=ROOT)


def _records(project_id: str) -> list[dict[str, Any]]:
    return list(load_improvements_incremental(project_id)["records"])


def load_improvements_incremental(
    project_id: str,
    *,
    source_dir: Path | None = None,
    ledger_path: Path | None = None,
    processor_version: str = IMPROVEMENT_PROCESSOR_VERSION,
    before_parse: Callable[[Path], None] | None = None,
) -> dict[str, Any]:
    """Read local improvement records through a restart-safe ingestion ledger.

    Improvement JSON remains canonical on disk. The local ledger stores only
    source names, fingerprints, processing state, and checkpoints; it never
    copies record content into the resumability metadata.
    """
    directory = Path(source_dir) if source_dir is not None else _directory(project_id)
    target_ledger = Path(
        ledger_path or (ROOT / ".agent-local" / "improvements" / f"{project_id}.json")
    )
    work_id = stable_work_id("improvement-records", project_id)
    ledger = IngestionLedger(
        target_ledger,
        source="improvement-record",
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
    paths = sorted(directory.glob("IMP-*.json")) if directory.exists() else []
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
                raise RuntimeError(f"improvement ledger claimed an unexpected item: {claimed[0]['item_id']}")
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
                raise ValueError("improvement record must contain a JSON object")
            records.append(record)
            if claimed:
                ledger.complete(item_id, output_refs=(f"improvement-record:{source_key}",))
            ledger.checkpoint(source_key, **stats)
        except (OSError, ValueError, UnicodeError) as exc:
            stats["errors"] += 1
            if claimed:
                ledger.fail(item_id, str(exc), retryable=True)
            ledger.checkpoint(source_key, **stats)
            raise

    stats["records"] = len(records)
    return {"records": records, "stats": stats, "checkpoint": ledger.status()["checkpoint"]}


def _dedupe_key(project_id: str, category: str, subsystem: str | None, title: str, observation: str, supplied: str | None) -> str:
    if supplied:
        source = f"{project_id}\0{_normalise(supplied)}"
    else:
        source = f"{project_id}\0{category}\0{_normalise(subsystem or '')}\0{_normalise(title)}\0{_normalise(observation)}"
    return hashlib.sha256(source.encode("utf-8")).hexdigest()


def _allocate_id() -> str:
    largest = 0
    for path in (ROOT / "projects").glob("*/improvements/IMP-*.json"):
        match = re.fullmatch(r"IMP-(\d+)", path.stem)
        if match:
            largest = max(largest, int(match.group(1)))
    return f"IMP-{largest + 1:04d}"


def _index(project_id: str) -> list[dict[str, Any]]:
    return [
        {
            "id": record["id"],
            "title": record["title"],
            "category": record["category"],
            "subsystem": record.get("subsystem"),
            "status": record["status"],
            "priority": record["priority"],
            "dedupe_key": record["dedupe_key"],
            "updated_at": record["updated_at"],
            "github_issue_number": (record.get("github") or {}).get("issue_number"),
        }
        for record in sorted(_records(project_id), key=lambda item: item["id"])
    ]


def _write(record: dict[str, Any]) -> None:
    directory = _directory(record["project"])
    write_json(directory / f"{record['id']}.json", record)
    write_json(directory / "index.json", {"schema_version": 1, "project": record["project"], "improvements": _index(record["project"])})


def capture_improvement(
    project: str,
    title: str,
    category: str,
    observation: str,
    suggested_direction: str,
    acceptance: Iterable[str],
    subsystem: str | None = None,
    priority: str = "medium",
    evidence: Iterable[str] = (),
    risks: Iterable[str] = (),
    source: dict[str, Any] | None = None,
    dedupe_key: str | None = None,
) -> dict[str, Any]:
    canonical = get_project(project)["id"]
    acceptance_items = [str(item).strip() for item in acceptance if str(item).strip()]
    evidence_items = [str(item).strip() for item in evidence if str(item).strip()]
    risk_items = [str(item).strip() for item in risks if str(item).strip()]
    if category not in CATEGORIES:
        raise ValueError(f"unsupported improvement category: {category}")
    if priority not in PRIORITIES:
        raise ValueError(f"unsupported improvement priority: {priority}")
    if not title.strip() or not observation.strip() or not suggested_direction.strip() or not acceptance_items:
        raise ValueError("title, observation, suggested direction, and acceptance are required")
    if source is not None:
        if set(source) - {"type", "reference"} or source.get("type") not in {"chat", "work", "codex", "claude", "manual", "regression", "review", "other"}:
            raise ValueError("invalid improvement source")
    safe_input = {"title": title, "observation": observation, "direction": suggested_direction, "acceptance": acceptance_items, "evidence": evidence_items, "risks": risk_items, "source": source or {}}
    require_private_safe(safe_input, "improvement")
    fingerprint = _dedupe_key(canonical, category, subsystem, title, observation, dedupe_key)
    for existing in _records(canonical):
        if existing.get("dedupe_key") == fingerprint and existing.get("status") in ACTIVE_STATUSES:
            merged = list(dict.fromkeys([*existing.get("evidence", []), *evidence_items]))
            if merged != existing.get("evidence", []):
                existing["evidence"] = merged
                existing["updated_at"] = _now()
                _write(existing)
            return {"project": canonical, "created": False, "duplicate_of": existing["id"], "record": existing}
    now = _now()
    record = {
        "schema_version": 1,
        "id": _allocate_id(),
        "project": canonical,
        "title": title.strip()[:160],
        "category": category,
        "subsystem": subsystem.strip() if subsystem else None,
        "status": "candidate",
        "priority": priority,
        "observation": observation.strip(),
        "evidence": evidence_items,
        "suspected_root_cause": None,
        "suggested_direction": suggested_direction.strip(),
        "acceptance": acceptance_items,
        "risks": risk_items,
        "dedupe_key": fingerprint,
        "source": source or {"type": "manual", "reference": None},
        "github": None,
        "created_at": now,
        "updated_at": now,
        "notes": None,
    }
    _write(record)
    return {"project": canonical, "created": True, "record": record}


def get_improvement(project: str, improvement_id: str) -> dict[str, Any]:
    canonical = get_project(project)["id"]
    if not re.fullmatch(r"IMP-[0-9]{4,}", improvement_id):
        raise ValueError("invalid improvement id")
    path = _directory(canonical) / f"{improvement_id}.json"
    if not path.exists():
        raise KeyError(f"unknown improvement: {improvement_id}")
    return load_json(path)


def list_improvements(project: str, status: str | None = None) -> list[dict[str, Any]]:
    canonical = get_project(project)["id"]
    return [record for record in _records(canonical) if status is None or record.get("status") == status]


def update_improvement(project: str, improvement_id: str, status: str | None = None, evidence: Iterable[str] = (), github: dict[str, Any] | None = None) -> dict[str, Any]:
    record = get_improvement(project, improvement_id)
    evidence_items = [str(item).strip() for item in evidence if str(item).strip()]
    if status:
        if status not in STATUSES:
            raise ValueError(f"unsupported improvement status: {status}")
        if status != record["status"] and status not in TRANSITIONS[record["status"]]:
            raise ValueError(f"invalid improvement transition: {record['status']} -> {status}")
        if status == "verified" and not evidence_items and not record.get("evidence"):
            raise ValueError("verified improvements require evidence")
        record["status"] = status
    record["evidence"] = list(dict.fromkeys([*record.get("evidence", []), *evidence_items]))
    if github is not None:
        require_private_safe(github, "GitHub linkage")
        record["github"] = github
    record["updated_at"] = _now()
    _write(record)
    return record


def search_improvements(project: str, query: str, limit: int = 8, include_terminal: bool = False) -> list[dict[str, Any]]:
    canonical = get_project(project)["id"]
    terms = set(re.findall(r"[a-z0-9]+", query.casefold()))
    scored: list[tuple[int, dict[str, Any]]] = []
    for record in _records(canonical):
        if not include_terminal and record.get("status") not in ACTIVE_STATUSES:
            continue
        haystack = " ".join([record.get("title", ""), record.get("category", ""), record.get("subsystem") or "", record.get("observation", ""), " ".join(record.get("acceptance", []))]).casefold()
        score = sum(3 if term in record.get("title", "").casefold() else 1 for term in terms if term in haystack)
        if score or not terms:
            scored.append((score, record))
    return [record for _, record in sorted(scored, key=lambda item: (-item[0], item[1]["id"]))[: max(0, limit)]]


def compact_improvements(project: str, task: str, limit: int = 3) -> list[dict[str, Any]]:
    return [
        {
            "id": record["id"],
            "title": record["title"],
            "status": record["status"],
            "priority": record["priority"],
            "acceptance": record.get("acceptance", [""])[0] if record.get("acceptance") else "",
            "issue": (record.get("github") or {}).get("issue_url"),
        }
        for record in search_improvements(project, task, limit=limit)
    ]


def issue_payload(project: str, improvement_id: str) -> dict[str, str]:
    record = get_improvement(project, improvement_id)
    if record["status"] not in {"ready", "in_progress", "implemented"}:
        raise ValueError("only ready or active improvements can be prepared for a project issue")
    marker = f"<!-- agent-os:{record['id']} -->"
    body = "\n".join([
        marker,
        record["observation"],
        "",
        f"Suggested direction: {record['suggested_direction']}",
        "",
        "Acceptance:",
        *(f"- {item}" for item in record["acceptance"]),
    ])
    return {"title": f"[{record['id']}] {record['title']}", "body": body, "marker": marker}
