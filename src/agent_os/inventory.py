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


def _scan_roots(registered: dict[Path, str]) -> list[Path]:
    """Every distinct parent directory that actually holds a registered project.

    Registered projects legitimately live under several parents (for example a
    GitHub directory and a Projects directory), so inventory covers each of them
    and nothing else. Unrelated parts of the drive are never walked.
    """
    roots: list[Path] = []
    seen: set[str] = set()
    for path in registered:
        parent = path.parent
        key = str(parent).casefold()
        if key in seen or not parent.is_dir():
            continue
        seen.add(key)
        roots.append(parent)
    return sorted(roots, key=lambda item: str(item).casefold())


def _normalize_remote(value: str | None) -> str | None:
    if not value:
        return None
    return value.strip().removesuffix(".git").rstrip("/").casefold()


def _describe(path: Path, registered: dict[Path, str], by_remote: dict[str, str]) -> dict[str, Any] | None:
    try:
        names = {item.name for item in path.iterdir() if item.is_file()}
    except OSError:
        return None
    remote = _remote(path)
    resolved = path.resolve()
    registered_as = registered.get(resolved)
    alternate = False
    if not registered_as:
        # A second clone of a registered repository is the same project, not an
        # unregistered one. Identity follows the repository, not the directory.
        registered_as = by_remote.get(_normalize_remote(remote) or "")
        alternate = bool(registered_as)
    return {
        "name": path.name,
        "path": str(path),
        "registered_as": registered_as,
        "alternate_checkout": alternate,
        "git": (path / ".git").exists(),
        "remote": remote,
        "documentation": sorted(name for name in names if name.casefold() in {"readme.md", "agents.md", "claude.md"}),
        "sensitive_markers": sorted(
            name
            for name in names
            if name.casefold() in SENSITIVE_NAMES or Path(name).suffix.casefold() in SENSITIVE_SUFFIXES
        ),
    }


def scan(projects_root: Path | None = None) -> dict[str, Any]:
    known = projects()
    registered = {Path(item["path"]).resolve(): item["id"] for item in known}
    by_remote = {
        normalized: item["id"]
        for item in known
        if (normalized := _normalize_remote(item.get("repository")))
    }
    roots = [projects_root.resolve()] if projects_root is not None else _scan_roots(registered)
    found: list[dict[str, Any]] = []
    seen: set[str] = set()
    for root in roots:
        try:
            entries = sorted((item for item in root.iterdir() if item.is_dir()), key=lambda item: item.name.casefold())
        except OSError:
            continue
        for path in entries:
            key = str(path.resolve()).casefold()
            if key in seen:
                continue
            seen.add(key)
            described = _describe(path, registered, by_remote)
            if described:
                found.append(described)
    missing = sorted(str(path) for path, _ in registered.items() if not path.is_dir())
    return {
        "projects_roots": [str(item) for item in roots],
        "projects_root": str(roots[0]) if roots else None,
        "projects": found,
        "unregistered": [item["path"] for item in found if not item["registered_as"]],
        "unresolved_registered": missing,
        "note": "Sensitive markers are filenames only; their contents were not read.",
    }
