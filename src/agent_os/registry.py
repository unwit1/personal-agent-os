from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from .machine import resolve_path, search_roots
from .paths import REGISTRY_PATH, ROOT
from .storage import load_json


def canonical_projects() -> list[dict[str, Any]]:
    """Registry entries exactly as stored in Git, without local path resolution."""
    return load_json(REGISTRY_PATH)["projects"]


def projects() -> list[dict[str, Any]]:
    """Registry entries with `path` resolved to this machine's checkout location."""
    entries = canonical_projects()
    roots = search_roots([str(entry.get("path") or "") for entry in entries])
    resolved = []
    for entry in entries:
        local_path, source = resolve_path(entry, roots)
        resolved.append({**entry, "path": str(local_path), "path_source": source})
    return resolved


def get_project(project_id: str) -> dict[str, Any]:
    normalized = project_id.casefold()
    for project in projects():
        names = {project["id"].casefold(), project["name"].casefold(), *(str(alias).casefold() for alias in project.get("aliases", []))}
        if normalized in names:
            return get_project(project["redirect_to"]) if project.get("redirect_to") else project
    raise KeyError(f"Unknown project: {project_id}")


def identify_project(path: Path) -> dict[str, Any] | None:
    resolved = path.resolve()
    candidates = []
    for project in projects():
        project_path = Path(project["path"]).resolve()
        try:
            resolved.relative_to(project_path)
            canonical = get_project(project["redirect_to"]) if project.get("redirect_to") else project
            candidates.append((len(project_path.parts), canonical))
        except ValueError:
            continue
    return max(candidates, default=(0, None), key=lambda item: item[0])[1]


def load_state(project: dict[str, Any]) -> dict[str, Any]:
    return load_json(ROOT / project["state_file"])


def git_status(project: dict[str, Any]) -> dict[str, Any]:
    path = Path(project["path"])
    if not (path / ".git").exists():
        return {"available": False, "reason": "not a Git repository"}
    result = subprocess.run(
        ["git", "-C", str(path), "status", "--short", "--branch"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    return {
        "available": result.returncode == 0,
        "returncode": result.returncode,
        "output": result.stdout.strip(),
        "error": result.stderr.strip(),
    }
