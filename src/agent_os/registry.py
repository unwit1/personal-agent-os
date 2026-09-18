from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from .paths import REGISTRY_PATH, ROOT
from .storage import load_json


def projects() -> list[dict[str, Any]]:
    return load_json(REGISTRY_PATH)["projects"]


def get_project(project_id: str) -> dict[str, Any]:
    normalized = project_id.casefold()
    for project in projects():
        if normalized in {project["id"].casefold(), project["name"].casefold()}:
            return project
    raise KeyError(f"Unknown project: {project_id}")


def identify_project(path: Path) -> dict[str, Any] | None:
    resolved = path.resolve()
    candidates = []
    for project in projects():
        project_path = Path(project["path"]).resolve()
        try:
            resolved.relative_to(project_path)
            candidates.append((len(project_path.parts), project))
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
