from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from .registry import projects


SENSITIVE_NAMES = {
    "config.json",
    "settings.json",
    "service_account.json",
    "credentials.json",
    "dashboard.db",
    "overtime.db",
}
SENSITIVE_SUFFIXES = {".xls", ".xlsx", ".xlsb", ".db", ".sqlite", ".sqlite3"}


def _remote(path: Path) -> str | None:
    if not (path / ".git").exists():
        return None
    result = subprocess.run(
        ["git", "-C", str(path), "remote", "get-url", "origin"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    return result.stdout.strip() or None


def scan(projects_root: Path | None = None) -> dict[str, Any]:
    registered = {Path(item["path"]).resolve(): item["id"] for item in projects()}
    if projects_root is None:
        projects_root = Path(next(iter(registered))).parent
    found = []
    for path in sorted((item for item in projects_root.iterdir() if item.is_dir()), key=lambda item: item.name.casefold()):
        names = {item.name for item in path.iterdir() if item.is_file()}
        sensitive_markers = sorted(
            name
            for name in names
            if name.casefold() in SENSITIVE_NAMES or Path(name).suffix.casefold() in SENSITIVE_SUFFIXES
        )
        found.append(
            {
                "name": path.name,
                "path": str(path),
                "registered_as": registered.get(path.resolve()),
                "git": (path / ".git").exists(),
                "remote": _remote(path),
                "documentation": sorted(
                    name for name in names if name.casefold() in {"readme.md", "agents.md", "claude.md"}
                ),
                "sensitive_markers": sensitive_markers,
            }
        )
    return {
        "projects_root": str(projects_root),
        "projects": found,
        "unregistered": [item["path"] for item in found if not item["registered_as"]],
        "note": "Sensitive markers are filenames only; their contents were not read.",
    }
