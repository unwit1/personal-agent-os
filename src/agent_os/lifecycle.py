"""Privacy-minimal task journals and resumable, idempotent postflight."""
from __future__ import annotations

import hashlib
import json
import re
import uuid
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import candidates, changes, improvements
from .chat import context as chat_context
from .contracts import POSTFLIGHT, REVIEW_RESULT, validate_contract
from .handoffs import create_handoff
from .index import search
from .locking import locked
from .paths import ROOT
from .privacy import privacy_findings, require_private_safe
from .registry import get_project, git_status, load_state
from .review import assess
from .storage import load_json, write_json

MIN_BUDGET = 800


class PreflightError(ValueError):
    def __init__(self, task_id):
        self.task_id = task_id
        super().__init__(f"Task {task_id} could not complete preflight; inspect task-status")


def _now():
    return datetime.now(timezone.utc).isoformat()


def _hash(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def _path(task_id):
    if not isinstance(task_id, str) or not re.fullmatch(r"TASK-[a-f0-9]{32}", task_id):
        raise ValueError("invalid task id")
    return ROOT / ".agent-local" / "tasks" / f"{task_id}.json"


def task_status(task_id: str) -> dict:
    path = _path(task_id)
    if not path.exists():
        raise ValueError("unknown task id")
    return load_json(path)


def _save(record):
    record["updated_at"] = _now()
    write_json(_path(record["task_id"]), record)


def _budget(value):
    if type(value) is not int or not MIN_BUDGET <= value <= 32000:
        raise ValueError("token_budget must be between 800 and 32000 estimated tokens")
    return value


def _query(value):
    if not isinstance(value, str) or not value.strip() or len(value) > 200000:
        raise ValueError("query must be a non-empty string of at most 200000 characters")


def _revision(project_id):
    """Hash metadata freshness, not source content or whole task history."""
    files = [ROOT / "projects/registry.json", ROOT / ".agent-os/index.sqlite", ROOT / "memory/promoted-candidates.json"]
    git = None
    if project_id:
        project = get_project(project_id)
        state = load_state(project)
        files.extend(Path(project["path"]) / item for item in state.get("context_files", []))
        files.extend([ROOT / project["state_file"], ROOT / "projects" / project_id / "handoffs",
                      ROOT / "projects" / project_id / "changes/index.json", ROOT / "projects" / project_id / "improvements/index.json"])
        git = git_status(project)
    stamps = []
    for path in files:
        try:
            stat = path.stat()
            stamps.append((str(path), stat.st_size, stat.st_mtime_ns))
        except OSError:
            stamps.append((str(path), None))
    return _hash({"files": stamps, "git": git})


def _retrieve(query, project_hint, budget):
    result = chat_context(query, project_hint, token_budget=max(250, budget - 650))
    packet = result.get("context") or {}
    packet.pop("task", None)  # The full prompt transits only to the worker.
    context = {"project": packet} if packet else {}
    if result.get("project"):
        project = get_project(result["project"])
        context["privacy_boundary"] = project.get("privacy", "Load development metadata only")
        context["policy"] = {
            "canonical": "policy/CANONICAL_AGENT_POLICY.md",
            "project_root": project["path"],
            "instruction": "Read applicable project-local AGENTS.md/CLAUDE.md before work; project policy is authoritative.",
        }
        # Bounded lexical retrieval, never all promoted memory or raw history.
        context["memory"] = [item for item in search(query, scope="agent-os", limit=4)
                             if "memory" in item.get("path", "").replace("\\", "/").split("/")]
    return result, context


def _envelope(record, context, budget, mode="full"):
    envelope = {
        "schema_version": 1, "task_id": record["task_id"], "source": record["source"],
        "routing": record["routing"], "request": {"prompt_hash": record["prompt_hash"],
        "safe_summary": "Project task" if record["routing"]["project"] else "General task"},
        "privacy": {"prompt_persisted": False, "raw_history_loaded": False,
                    "classification": record["privacy_classification"]},
        "requirements": {"postflight_required": True, "explicit_summary_required": True,
                         "hidden_chain_of_thought": False},
        "preflight_completed": True, "context_mode": mode, "context": deepcopy(context),
        "measurement": {"token_budget": budget, "estimated_tokens": 0, "within_budget": True},
    }
    def size():
        return (len(json.dumps(envelope, ensure_ascii=False)) + 3) // 4
    packet = envelope["context"].get("project", {})
    for key in ("search_matches", "development_context", "matched_skills", "latest_agent_os_handoff", "state", "context_measurement", "context_policy", "summary"):
        if size() > budget:
            packet.pop(key, None)
    for key in ("memory", "project"):
        if size() > budget:
            envelope["context"].pop(key, None)
    # Fixed-point accounting includes the measurement itself.
    for _ in range(3):
        envelope["measurement"]["estimated_tokens"] = size()
    if size() > budget:
        raise ValueError("budget cannot fit mandatory task metadata")
    return envelope


def begin_task(query: str, source_client: str, source_session: str | None = None,
               project_hint: str | None = None, token_budget: int = 2200,
               execution_metadata: dict | None = None) -> dict:
    _query(query)
    _budget(token_budget)
    if not isinstance(source_client, str) or not re.fullmatch(r"[A-Za-z0-9_.-]{1,64}", source_client):
        raise ValueError("source_client must be a short client identifier")
    record = {
        "schema_version": 1, "task_id": "TASK-" + uuid.uuid4().hex,
        "source": {"client": source_client, "session_hash": _hash(source_session) if source_session else None},
        "execution_metadata_hash": _hash(execution_metadata or {}), "prompt_hash": _hash(query),
        "created_at": _now(), "status": "preflight", "preflight_completed": False,
        "routing": {"project": None, "confidence": "none", "ambiguous": False},
        "privacy_classification": "sensitive" if privacy_findings(query) else "unclassified",
        "turn_count": 1, "token_budget": token_budget, "context_hashes": {},
    }
    _save(record)
    try:
        routed, context = _retrieve(query, project_hint, token_budget)
        record["routing"] = {"project": routed.get("project"),
                             "confidence": routed.get("resolution", {}).get("confidence", "none"),
                             "ambiguous": routed.get("resolution", {}).get("ambiguous", False)}
        envelope = _envelope(record, context, token_budget)
        record.update(status="active", preflight_completed=True,
                      context_hashes={key: _hash(value) for key, value in envelope["context"].items()},
                      context_revision=_revision(record["routing"]["project"]))
        _save(record)
        return envelope
    except BaseException:
        abort_task(record["task_id"], stage="preflight", error_class="preflight_failed", partial_changes=False)
        raise PreflightError(record["task_id"]) from None


def continue_task(task_id: str, query: str, token_budget: int | None = None,
                  reset_context: bool = False, resume: bool = False) -> dict:
    _path(task_id)
    _query(query)
    with locked(task_id):
        record = task_status(task_id)
        if record["status"] == "aborted" and resume and record["preflight_completed"]:
            record["status"] = "active"
        if record["status"] != "active":
            raise ValueError("task must be active; use resume for an aborted task or retry pending postflight")
        budget = _budget(token_budget if token_budget is not None else record["token_budget"])
        revision = _revision(record["routing"]["project"])
        if not reset_context and record["prompt_hash"] == _hash(query) and record.get("context_revision") == revision and budget == record["token_budget"]:
            record["turn_count"] += 1
            _save(record)
            return _envelope(record, {}, budget, "delta")
        routed, context = _retrieve(query, record["routing"]["project"], budget)
        if not record["routing"]["project"]:
            record["routing"] = {"project": routed.get("project"),
                                 "confidence": routed.get("resolution", {}).get("confidence", "none"),
                                 "ambiguous": routed.get("resolution", {}).get("ambiguous", False)}
        record["prompt_hash"] = _hash(query)
        if privacy_findings(query):
            record["privacy_classification"] = "sensitive"
        if not reset_context:
            context = {k: v for k, v in context.items() if record["context_hashes"].get(k) != _hash(v)}
        envelope = _envelope(record, context, budget, "full" if reset_context else "delta")
        if reset_context:
            record["context_hashes"] = {}
        record["context_hashes"].update({k: _hash(v) for k, v in envelope["context"].items()})
        record["turn_count"] += 1
        record["token_budget"] = budget
        record["context_revision"] = _revision(record["routing"]["project"])
        _save(record)
        return envelope


def review_requirement(postflight: dict) -> dict:
    risk = assess(postflight["files_changed"], postflight["validation"]["status"] == "failed",
                  postflight.get("architecture_change", False))
    # Sensitive/destructive changes always need independent review, even when small.
    sensitive = any(term in " ".join(postflight["files_changed"]).lower()
                    for term in ("security", "privacy", "schema", "migration", "memory", "policy", "credential"))
    required = risk["review_level"] >= 2 or sensitive or postflight.get("destructive_change", False) or postflight.get("cross_project", False) or len(postflight["files_changed"]) >= 40 or postflight["validation"]["status"] == "failed" or postflight.get("architecture_change", False)
    return {**risk, "required": required, "status": "unavailable" if required else "not_required", "findings": []}


def _capture(record, payload):
    project = record["routing"]["project"]
    task_id = record["task_id"]
    refs = {"changes": [], "improvements": [], "candidates": []}
    proposed_changes = payload.get("proposed_changes", [])
    if payload["files_changed"] and not proposed_changes:
        proposed_changes = [{"title": payload["summary"][:180], "request_summary": payload["summary"],
                             "change_type": "other", "repository_files": payload["files_changed"]}]
    for item in proposed_changes:
        supplied = dict(item)
        diagnosis = supplied.pop("diagnosis_summary", None)
        fix = supplied.pop("fix_summary", None)
        captured = changes.capture_change(project, **supplied, source_kind="agent", task_id=task_id)
        change_id = captured["record"]["change_id"]
        if diagnosis or fix:
            changes.update_change(project, change_id, diagnosis_summary=diagnosis, fix_summary=fix)
        refs["changes"].append(change_id)
    for item in payload.get("proposed_improvements", []):
        if item["evidence"]:
            result = improvements.capture_improvement(project, **item, task_id=task_id)
            refs["improvements"].append(result["record"]["id"])
    proposed = [item for key in ("lessons", "proposed_memories", "proposed_skills")
                for item in payload.get(key, []) if item["evidence"]]
    proposed.extend({"kind": "decision_candidate", "statement": item["decision"],
                     "evidence": item.get("evidence") or payload["evidence"]}
                    for item in payload["decisions"] if item["decision"].strip())
    if proposed:
        result = candidates.stage_candidates(project, payload["summary"], proposed,
                                              source_agent=record["source"]["client"], task_id=task_id)
        refs["candidates"] = [item["id"] for item in result["staged"] + result["duplicates"]]
    return refs


def finish_task(task_id: str, postflight: dict, *, reviewer=None) -> dict:
    """Only a configured callable reviewer can supply a review; clients cannot assert one."""
    _path(task_id)
    validate_contract(postflight, POSTFLIGHT, "postflight")
    if not postflight["summary"].strip():
        raise ValueError("postflight summary must not be blank")
    if postflight["validation"]["status"] == "passed" and not postflight["validation"]["checks"]:
        raise ValueError("passing validation requires check evidence")
    # Validate every proposed write before any canonical side effect or retry journal.
    for item in postflight.get("proposed_changes", []):
        if not item["title"].strip() or not item["request_summary"].strip():
            raise ValueError("change proposal needs a title and summary")
    for item in postflight.get("proposed_improvements", []):
        if not all(item[key].strip() for key in ("title", "observation", "suggested_direction")) or not item["acceptance"] or not all(value.strip() for value in item["acceptance"]):
            raise ValueError("improvement proposal needs direction and acceptance criteria")
    for key in ("lessons", "proposed_memories", "proposed_skills"):
        for item in postflight.get(key, []):
            candidates._require_candidate(item)
    if postflight["sanitized"]:
        require_private_safe(postflight, "postflight")
    payload_hash = _hash(postflight)
    with locked(task_id):
        record = task_status(task_id)
        if record["status"] == "finished":
            if record.get("postflight_hash") != payload_hash:
                raise ValueError("finished task has a different postflight")
            return record["result"]
        if record["status"] not in {"active", "postflight_pending"}:
            raise ValueError("task must complete preflight before postflight")
        if record.get("postflight_hash") and record["postflight_hash"] != payload_hash:
            raise ValueError("retry pending postflight with the original payload")
        record.update(status="postflight_pending", postflight_hash=payload_hash)
        # A safe payload is the recovery journal. Unreviewed/private prose stays transient.
        if postflight["sanitized"]:
            record["pending_postflight"] = postflight
        _save(record)
        review = record.get("review") or review_requirement(postflight)
        if review["required"] and reviewer is not None and "review" not in record:
            try:
                checked = reviewer({"task_id": task_id, "project": record["routing"]["project"],
                                    "postflight": deepcopy(postflight), "risk": deepcopy(review)})
                validate_contract(checked, REVIEW_RESULT, "review")
                require_private_safe(checked, "review")
                review.update(checked)
            except Exception:
                review.update(status="failed", findings=["Independent review did not complete."])
        # Journal review receipt before canonical capture, so a retry never buys another review.
        record["review"] = review
        _save(record)
        validation_failed = postflight["validation"]["status"] == "failed"
        outcome = "validation_failed" if validation_failed else ("review_required" if review["required"] and review["status"] not in {"pass", "pass_with_notes"} else "completed")
        material = bool(postflight["files_changed"] or postflight["decisions"] or any(postflight.get(k) for k in ("lessons", "proposed_memories", "proposed_skills", "proposed_changes", "proposed_improvements")))
        durable = bool(record["routing"]["project"] and material and postflight["sanitized"] and postflight["evidence"])
        refs = {}
        if durable:
            with locked():
                refs = _capture(record, postflight)
                remaining = list(postflight["remaining"])
                if outcome != "completed":
                    remaining.append("Resolve " + outcome.replace("_", " ") + " before treating this work as verified.")
                handoff = create_handoff(record["routing"]["project"], [postflight["summary"]], remaining,
                                         postflight["validation"]["checks"], [item["decision"] for item in postflight["decisions"]], task_id=task_id)
                refs["handoff"] = str(handoff.relative_to(ROOT)).replace("\\", "/")
                trace = {"schema_version": 1, "task_id": task_id, "project": record["routing"]["project"],
                         "prompt_hash": record["prompt_hash"], "source": record["source"],
                         "postflight": postflight, "review": review, "artifacts": refs,
                         "outcome": outcome, "status": "unverified", "created_at": record["created_at"]}
                trace_path = ROOT / "projects" / record["routing"]["project"] / "tasks" / f"{task_id}.json"
                write_json(trace_path, trace)
                refs["trace"] = str(trace_path.relative_to(ROOT)).replace("\\", "/")
        result = {"task_id": task_id, "status": "finished", "outcome": outcome, "review": review,
                  "durable_capture": durable, "artifacts": refs}
        record.update(status="finished", result=result)
        record.pop("pending_postflight", None)
        _save(record)
        return result


def abort_task(task_id: str, stage: str = "execution", error_class: str = "execution_failed",
               partial_changes: bool = True, validation_status: str = "unknown") -> dict:
    _path(task_id)
    if stage not in {"preflight", "execution", "postflight"} or error_class not in {"preflight_failed", "execution_failed", "interrupted", "timeout", "postflight_failed", "invalid_result", "client_unavailable"}:
        raise ValueError("unsupported failure classification")
    if type(partial_changes) is not bool or validation_status not in {"unknown", "passed", "failed", "not_run"}:
        raise ValueError("invalid failure metadata")
    with locked(task_id):
        record = task_status(task_id)
        if record["status"] == "finished":
            raise ValueError("cannot abort a finished task")
        record["failure"] = {"stage": stage, "error_class": error_class,
                             "partial_changes": partial_changes, "validation_status": validation_status,
                             "recovery": "retry finish_task" if record.get("postflight_hash") else "inspect changes then continue_task with resume=true"}
        record["status"] = "postflight_pending" if record.get("postflight_hash") else "aborted"
        _save(record)
        return {"task_id": task_id, "status": record["status"], "failure": record["failure"]}
