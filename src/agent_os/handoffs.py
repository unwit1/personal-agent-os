from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .paths import ROOT
from .locking import canonical_write
from .privacy import require_private_safe
from .registry import get_project, git_status
from .storage import write_json


@canonical_write
def create_handoff(
    project_id: str,
    completed: list[str],
    remaining: list[str],
    validation: list[str],
    decisions: list[str] | None = None,
    task_id: str | None = None,
) -> Path:
    project = get_project(project_id)
    require_private_safe({"completed": completed, "remaining": remaining, "validation": validation, "decisions": decisions, "task_id": task_id}, "handoff")
    if task_id:
        import re
        if not re.fullmatch(r"TASK-[a-f0-9]{32}", task_id):
            raise ValueError("invalid handoff task id")
        existing = next((ROOT / "projects" / project["id"] / "handoffs").glob(f"*-{task_id}.json"), None)
        if existing:
            return existing
    now = datetime.now(timezone.utc)
    record: dict[str, Any] = {
        "schema_version": 1,
        "project": project["id"],
        "created_at": now.isoformat(),
        "git": {"available": git_status(project).get("available", False)},
        "completed": completed,
        "decisions": decisions or [],
        "remaining": remaining,
        "validation": validation,
        "candidate_memories": [],
        "candidate_skills": [],
        "task_id": task_id,
    }
    suffix = f"-{task_id}" if task_id else ""
    destination = ROOT / "projects" / project["id"] / "handoffs" / f"{now.strftime('%Y%m%dT%H%M%S%fZ')}{suffix}.json"
    write_json(destination, record)
    return destination
