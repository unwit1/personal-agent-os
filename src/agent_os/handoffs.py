from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .paths import ROOT
from .registry import get_project, git_status
from .storage import write_json


def create_handoff(
    project_id: str,
    completed: list[str],
    remaining: list[str],
    validation: list[str],
    decisions: list[str] | None = None,
) -> Path:
    project = get_project(project_id)
    now = datetime.now(timezone.utc)
    record: dict[str, Any] = {
        "schema_version": 1,
        "project": project["id"],
        "created_at": now.isoformat(),
        "git": git_status(project),
        "completed": completed,
        "decisions": decisions or [],
        "remaining": remaining,
        "validation": validation,
        "candidate_memories": [],
        "candidate_skills": [],
    }
    destination = ROOT / "projects" / project["id"] / "handoffs" / f"{now.strftime('%Y%m%dT%H%M%SZ')}.json"
    write_json(destination, record)
    return destination
