"""Work claims, so several agents on one repository do not collide.

This exists because of a real incident on 2026-09-22. Two agents worked the
same scanner repository within the same hour. One measured a corpus, changed
the classifier, and re-measured; the other landed eight commits in between,
including a change that held a whole packet for review whenever any single page
lacked a confident form type. The first agent's before/after comparison
collapsed from 64 documents to 1, and it very nearly attributed that regression
to its own change. Both agents were doing careful work. Neither could see the
other.

The fix is not locking. Nothing here can stop a write, and pretending otherwise
would be worse than useless -- an agent that believes it holds an exclusive
lock is more dangerous than one that knows it does not. What this provides is
*visibility*: an agent announces what it is about to touch, sees who else is
already there, and can leave a message for them.

Claims live in the machine-local Agent OS directory rather than in Git. Two
agents pushing claim files would collide on exactly the thing the claims exist
to prevent, and a claim is worthless a day later anyway.

Three properties matter:

**A claim expires.** An agent that crashes must not block the repository
forever. Claims carry a lease and go stale without a heartbeat.

**Overlap is reported, never resolved.** Two agents wanting the same file is a
conversation, not a race to be arbitrated by a tool. The overlap is surfaced
with enough detail -- who, what, since when -- for a person or an agent to
decide.

**Reads are honest about their own limits.** The registry only covers agents on
this machine that chose to announce themselves. It is a courtesy protocol.
"""

from __future__ import annotations

import fnmatch
import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any

from .machine import CONFIG_DIR
from .timestamps import utc_now_iso

CLAIMS_PATH = CONFIG_DIR / "work-claims.json"
CLAIMS_ENV = "AGENT_OS_CLAIMS"
SCHEMA_VERSION = 1

# How long a claim stands without a heartbeat. Long enough that a slow OCR pass
# does not lose its claim mid-run; short enough that yesterday's dead session
# does not look like today's colleague.
DEFAULT_LEASE_MINUTES = 90

STATUSES = ("active", "released", "expired")
TASK_STATUSES = ("queued", "assigned", "in_progress", "completed", "cancelled")
TASK_KEY_LIMIT = 160
TASK_TITLE_LIMIT = 320
TASK_RESULT_LIMIT = 2000
TASK_VALIDATION_LIMIT = 1000


def claims_path(override: Path | None = None) -> Path:
    if override is not None:
        return Path(override)
    configured = os.environ.get(CLAIMS_ENV)
    return Path(configured).expanduser() if configured else CLAIMS_PATH


def _now_seconds() -> float:
    import time

    return time.time()


def _load(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return {"schema_version": SCHEMA_VERSION, "claims": []}
    if not isinstance(data, dict) or not isinstance(data.get("claims"), list):
        return {"schema_version": SCHEMA_VERSION, "claims": []}
    return data


def _save(path: Path, data: dict[str, Any]) -> None:
    """Write atomically. Two agents writing at once must not shred the file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent, text=True)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(payload)
        os.replace(temporary, path)
    except Exception:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def _normalize_scope(scope) -> list[str]:
    """Scope entries are repository-relative paths or globs."""
    items = []
    for entry in scope or []:
        text = str(entry).strip().replace("\\", "/").lstrip("./")
        if text:
            items.append(text)
    return sorted(dict.fromkeys(items)) or ["**"]


def scopes_overlap(left: list[str], right: list[str]) -> list[tuple[str, str]]:
    """Every pair of scope entries that could touch the same files.

    A bare directory covers everything beneath it, and a glob is matched both
    ways so "src/**" and "src/agent_os/cli.py" recognise each other.
    """
    hits = []
    for a in left:
        for b in right:
            if a == b or a == "**" or b == "**":
                hits.append((a, b))
                continue
            a_dir, b_dir = a.rstrip("/") + "/", b.rstrip("/") + "/"
            if b.startswith(a_dir) or a.startswith(b_dir):
                hits.append((a, b))
                continue
            if fnmatch.fnmatch(b, a) or fnmatch.fnmatch(a, b):
                hits.append((a, b))
    return hits


def _expire(data: dict[str, Any], now: float) -> bool:
    """Mark claims whose lease ran out. Returns whether anything changed."""
    changed = False
    for claim in data["claims"]:
        if claim.get("status") != "active":
            continue
        lease = float(claim.get("lease_seconds") or DEFAULT_LEASE_MINUTES * 60)
        last = float(claim.get("heartbeat_epoch") or claim.get("created_epoch") or 0)
        if now - last > lease:
            claim["status"] = "expired"
            claim["expired_at"] = utc_now_iso()
            changed = True
    return changed


def active_claims(project: str | None = None, path: Path | None = None) -> list[dict[str, Any]]:
    location = claims_path(path)
    data = _load(location)
    if _expire(data, _now_seconds()):
        try:
            _save(location, data)
        except OSError:
            pass
    return [
        claim for claim in data["claims"]
        if claim.get("status") == "active"
        and (project is None or claim.get("project") == project)
    ]


def _claim_id(agent: str, project: str, created: str) -> str:
    return "WC-" + hashlib.sha256(f"{agent}\0{project}\0{created}".encode("utf-8")).hexdigest()[:10]


def claim(
    project: str,
    task: str,
    agent: str,
    scope: list[str] | None = None,
    lease_minutes: int = DEFAULT_LEASE_MINUTES,
    path: Path | None = None,
) -> dict[str, Any]:
    """Announce work, and report anyone already working the same ground.

    The claim is always recorded. An overlap does not block it: the point is
    that both agents can see each other, not that one wins.
    """
    location = claims_path(path)
    data = _load(location)
    now = _now_seconds()
    _expire(data, now)

    wanted = _normalize_scope(scope)
    conflicts = []
    for existing in data["claims"]:
        if existing.get("status") != "active" or existing.get("project") != project:
            continue
        if existing.get("agent") == agent:
            continue
        overlap = scopes_overlap(wanted, existing.get("scope") or ["**"])
        if overlap:
            conflicts.append({
                "claim_id": existing["claim_id"],
                "agent": existing["agent"],
                "task": existing["task"],
                "since": existing["created_at"],
                "overlapping_scope": [f"{a} <-> {b}" for a, b in overlap[:6]],
            })

    created = utc_now_iso()
    record = {
        "claim_id": _claim_id(agent, project, created),
        "project": project,
        "agent": agent,
        "task": task,
        "scope": wanted,
        "status": "active",
        "created_at": created,
        "created_epoch": now,
        "heartbeat_epoch": now,
        "lease_seconds": max(60, int(lease_minutes) * 60),
        "messages": [],
    }
    data["claims"].append(record)
    _save(location, data)

    return {
        "claim": record,
        "conflicts": conflicts,
        "advice": (
            "No one else has announced this ground."
            if not conflicts else
            "Another agent is already working here. Talk to it before editing: "
            "`agent-os work-message <claim_id> \"...\"`, or narrow your scope."
        ),
        "registry_covers": "agents on this machine that announced themselves",
    }


def heartbeat(claim_id: str, path: Path | None = None) -> dict[str, Any]:
    """Keep a claim alive during long work, and collect any replies."""
    location = claims_path(path)
    data = _load(location)
    for record in data["claims"]:
        if record.get("claim_id") == claim_id:
            if record.get("status") != "active":
                return {"claim_id": claim_id, "status": record.get("status"),
                        "reason": "this claim is no longer active; make a new one"}
            record["heartbeat_epoch"] = _now_seconds()
            record["heartbeat_at"] = utc_now_iso()
            _save(location, data)
            unread = [m for m in record.get("messages", []) if not m.get("read")]
            for message in unread:
                message["read"] = True
            if unread:
                _save(location, data)
            return {"claim_id": claim_id, "status": "active", "new_messages": unread}
    raise KeyError(f"unknown claim: {claim_id}")


def release(claim_id: str, note: str | None = None, path: Path | None = None) -> dict[str, Any]:
    location = claims_path(path)
    data = _load(location)
    for record in data["claims"]:
        if record.get("claim_id") == claim_id:
            record["status"] = "released"
            record["released_at"] = utc_now_iso()
            if note:
                record["release_note"] = note
            _save(location, data)
            return {"claim_id": claim_id, "status": "released"}
    raise KeyError(f"unknown claim: {claim_id}")


def message(claim_id: str, text: str, sender: str, path: Path | None = None) -> dict[str, Any]:
    """Leave a note for whoever holds a claim."""
    location = claims_path(path)
    data = _load(location)
    for record in data["claims"]:
        if record.get("claim_id") == claim_id:
            entry = {"from": sender, "text": str(text)[:2000], "at": utc_now_iso(), "read": False}
            record.setdefault("messages", []).append(entry)
            _save(location, data)
            return {"claim_id": claim_id, "delivered_to": record.get("agent"), "message": entry}
    raise KeyError(f"unknown claim: {claim_id}")


def note(project: str, text: str, sender: str, about: str | None = None,
         path: Path | None = None) -> dict[str, Any]:
    """Leave a note for whoever works this project next.

    Messages attach to a claim, which is no help when the agent you need to
    reach never announced itself -- the common case while a protocol is still
    being adopted. A note attaches to the *project*, so it waits in the inbox
    until somebody picks the work up, and it survives the sender's session
    ending.
    """
    location = claims_path(path)
    data = _load(location)
    entry = {
        "note_id": "WN-" + hashlib.sha256(
            f"{project}\0{sender}\0{utc_now_iso()}".encode("utf-8")).hexdigest()[:10],
        "project": project,
        "from": sender,
        "about": about,
        "text": str(text)[:4000],
        "at": utc_now_iso(),
        "acknowledged_by": [],
    }
    data.setdefault("notes", []).append(entry)
    _save(location, data)
    return {"note": entry, "delivered_to": f"the {project} inbox"}


def inbox(project: str | None = None, include_acknowledged: bool = False,
          path: Path | None = None) -> dict[str, Any]:
    """Notes waiting for whoever works this project."""
    data = _load(claims_path(path))
    notes = [
        n for n in data.get("notes", [])
        if (project is None or n.get("project") == project)
        and (include_acknowledged or not n.get("acknowledged_by"))
    ]
    return {"project": project, "waiting": len(notes), "notes": notes}


def acknowledge(note_id: str, agent: str, reply: str | None = None,
                path: Path | None = None) -> dict[str, Any]:
    """Mark a note read, optionally answering it, so it stops being repeated."""
    location = claims_path(path)
    data = _load(location)
    for entry in data.get("notes", []):
        if entry.get("note_id") == note_id:
            entry.setdefault("acknowledged_by", []).append(
                {"agent": agent, "at": utc_now_iso(), "reply": reply})
            _save(location, data)
            return {"note_id": note_id, "acknowledged_by": agent, "reply": reply}
    raise KeyError(f"unknown note: {note_id}")


def _task_id(project: str, task_key: str) -> str:
    return "WT-" + hashlib.sha256(
        f"{project.strip().casefold()}\0{task_key.strip().casefold()}".encode("utf-8")
    ).hexdigest()[:12]


def _task_text(value: str, label: str, limit: int) -> str:
    text = str(value).strip()
    if not text:
        raise ValueError(f"{label} must not be empty")
    return text[:limit]


def _task_dependencies(values: list[str] | None) -> list[str]:
    return sorted({str(value).strip() for value in (values or []) if str(value).strip()})


def _find_task(data: dict[str, Any], task_id: str) -> dict[str, Any]:
    for task in data.get("tasks", []):
        if task.get("task_id") == task_id:
            return task
    raise KeyError(f"unknown delegated task: {task_id}")


def _blocked_by(data: dict[str, Any], task: dict[str, Any]) -> list[str]:
    by_id = {item.get("task_id"): item for item in data.get("tasks", [])}
    return [
        dependency
        for dependency in task.get("depends_on", [])
        if by_id.get(dependency, {}).get("status") != "completed"
    ]


def delegate(
    project: str,
    task_key: str,
    title: str,
    requester: str,
    assignee: str | None = None,
    scope: list[str] | None = None,
    depends_on: list[str] | None = None,
    path: Path | None = None,
) -> dict[str, Any]:
    """Create an idempotent, machine-local task for another agent."""
    project_name = _task_text(project, "project", TASK_KEY_LIMIT)
    key = _task_text(task_key, "task_key", TASK_KEY_LIMIT)
    requester_name = _task_text(requester, "requester", TASK_KEY_LIMIT)
    task_id = _task_id(project_name, key)
    location = claims_path(path)
    data = _load(location)
    data.setdefault("tasks", [])
    existing = next((item for item in data["tasks"] if item.get("task_id") == task_id), None)
    if existing is not None:
        return {"created": False, "idempotent": True, "task": existing}
    assigned = _task_text(assignee, "assignee", TASK_KEY_LIMIT) if assignee else None
    now = utc_now_iso()
    task = {
        "task_id": task_id,
        "project": project_name,
        "task_key": key,
        "title": _task_text(title, "title", TASK_TITLE_LIMIT),
        "requester": requester_name,
        "assignee": assigned,
        "scope": _normalize_scope(scope),
        "depends_on": _task_dependencies(depends_on),
        "status": "assigned" if assigned else "queued",
        "created_at": now,
        "updated_at": now,
    }
    data["tasks"].append(task)
    _save(location, data)
    return {"created": True, "idempotent": False, "task": task}


def list_tasks(
    project: str | None = None,
    status: str | None = None,
    path: Path | None = None,
) -> list[dict[str, Any]]:
    """List delegated tasks without loading prompts, documents, or transcripts."""
    if status is not None and status not in TASK_STATUSES:
        raise ValueError(f"unknown delegated task status: {status}")
    tasks = _load(claims_path(path)).get("tasks", [])
    return sorted(
        [
            task for task in tasks
            if (project is None or task.get("project") == project)
            and (status is None or task.get("status") == status)
        ],
        key=lambda item: (item.get("created_at", ""), item.get("task_id", "")),
    )


def claim_task(task_id: str, agent: str, path: Path | None = None) -> dict[str, Any]:
    """Claim a delegated task once its dependencies are complete."""
    location = claims_path(path)
    data = _load(location)
    task = _find_task(data, task_id)
    agent_name = _task_text(agent, "agent", TASK_KEY_LIMIT)
    if task.get("status") in {"completed", "cancelled"}:
        raise ValueError(f"delegated task is already {task['status']}")
    if task.get("assignee") and task["assignee"] != agent_name:
        raise ValueError("delegated task is assigned to another agent")
    blockers = _blocked_by(data, task)
    if blockers:
        return {"claimed": False, "blocked": True, "blocked_by": blockers, "task": task}
    task["assignee"] = agent_name
    task["status"] = "in_progress"
    task["updated_at"] = utc_now_iso()
    _save(location, data)
    return {"claimed": True, "blocked": False, "task": task}


def complete_task(
    task_id: str,
    agent: str,
    validation: str,
    result: str | None = None,
    path: Path | None = None,
) -> dict[str, Any]:
    """Complete a delegated task only by its assigned agent with evidence."""
    location = claims_path(path)
    data = _load(location)
    task = _find_task(data, task_id)
    agent_name = _task_text(agent, "agent", TASK_KEY_LIMIT)
    evidence = _task_text(validation, "validation", TASK_VALIDATION_LIMIT)
    if task.get("status") != "in_progress":
        raise ValueError("delegated task must be in_progress before completion")
    if task.get("assignee") != agent_name:
        raise ValueError("only the assigned agent can complete a delegated task")
    task["status"] = "completed"
    task["validation"] = evidence
    if result:
        task["result"] = str(result).strip()[:TASK_RESULT_LIMIT]
    task["completed_at"] = utc_now_iso()
    task["updated_at"] = task["completed_at"]
    _save(location, data)
    return {"completed": True, "task": task}


def status(project: str | None = None, path: Path | None = None) -> dict[str, Any]:
    """What is being worked on right now, and by whom."""
    claims = active_claims(project, path)
    waiting = inbox(project, path=path)
    return {
        "registry": str(claims_path(path)),
        "covers": "agents on this machine that announced themselves; not a lock",
        "unread_notes": waiting["waiting"],
        "notes": waiting["notes"],
        "active": [
            {
                "claim_id": c["claim_id"],
                "project": c["project"],
                "agent": c["agent"],
                "task": c["task"],
                "scope": c["scope"],
                "since": c["created_at"],
                "unread_messages": sum(1 for m in c.get("messages", []) if not m.get("read")),
            }
            for c in claims
        ],
    }


def check(project: str, scope: list[str] | None = None, path: Path | None = None) -> dict[str, Any]:
    """Look before you leap: who is already on this ground?

    Announces nothing. Use this when you only want to know, and `claim` when
    you are about to start.
    """
    wanted = _normalize_scope(scope)
    overlapping = []
    for existing in active_claims(project, path):
        hits = scopes_overlap(wanted, existing.get("scope") or ["**"])
        if hits:
            overlapping.append({
                "claim_id": existing["claim_id"],
                "agent": existing["agent"],
                "task": existing["task"],
                "since": existing["created_at"],
                "overlapping_scope": [f"{a} <-> {b}" for a, b in hits[:6]],
            })
    return {
        "project": project,
        "scope": wanted,
        "clear": not overlapping,
        "overlapping": overlapping,
        "advice": (
            "Nobody has announced this ground; claim it before you start."
            if not overlapping else
            "Somebody is already here. Message them before editing these files."
        ),
    }
