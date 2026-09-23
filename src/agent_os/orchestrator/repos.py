"""Repository chooser for the GUI: find the user's Git repositories, and
create a new one.

Discovery looks in the usual places (``~/GitHub``, ``~/Projects``,
``~/source/repos``, ``~/Documents/GitHub``), plus every registered project's
checkout, two folder levels deep. Extra checkouts that Git itself calls
worktrees, and anything under ``.agent-local``/``node_modules``, are left out
so one repository shows once. Read-only: listing never changes anything.

Creating a repository makes a folder, ``git init -b main``, a README and one
local commit. Publishing to GitHub is opt-in (a checkbox the user ticks) and
creates a **private** repository through the ``gh`` CLI.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

SKIP_DIRS = {".agent-local", "node_modules", ".venv", "venv", "__pycache__", ".git", "dist", "build"}
_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._ -]{0,79}$")


def default_roots() -> list[Path]:
    home = Path.home()
    return [path for path in (home / "GitHub", home / "Projects", home / "source" / "repos", home / "Documents" / "GitHub") if path.is_dir()]


def _git(repo: Path, *args: str, timeout: float = 10) -> str:
    try:
        completed = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, timeout=timeout,
                                   creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    except (OSError, subprocess.TimeoutExpired):
        return ""
    return completed.stdout.strip() if completed.returncode == 0 else ""


def _candidates(roots: list[Path], depth: int = 2) -> list[Path]:
    found: list[Path] = []

    def visit(folder: Path, level: int) -> None:
        git = folder / ".git"
        if git.is_dir():  # a main checkout (a worktree has a .git *file*)
            found.append(folder)
            return
        if git.exists() or level >= depth:
            return
        try:
            children = sorted(child for child in folder.iterdir() if child.is_dir() and child.name not in SKIP_DIRS and not child.name.startswith("."))
        except OSError:
            return
        for child in children:
            visit(child, level + 1)

    for root in roots:
        visit(root, 0)
    return found


def describe(repo: Path, project: str | None = None) -> dict[str, Any]:
    last = _git(repo, "log", "-1", "--format=%cI")
    return {
        "name": repo.name,
        "path": str(repo),
        "project": project,
        "branch": _git(repo, "branch", "--show-current") or None,
        "last_commit": last or None,
        "remote": _git(repo, "remote", "get-url", "origin") or None,
    }


def list_repositories(roots: list[Path] | None = None, registered: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    if registered is None:
        try:
            from ..registry import projects

            registered = projects()
        except Exception:
            registered = []
    by_path: dict[str, str] = {}
    not_git: list[dict[str, Any]] = []
    for entry in registered:
        path = Path(str(entry.get("path") or ""))
        if (path / ".git").is_dir():
            by_path.setdefault(os.path.normcase(str(path.resolve())), entry["id"])  # first registered entry names the folder
        elif path.is_dir() and not (path / ".git").exists():
            not_git.append({"name": path.name, "path": str(path), "project": entry["id"], "git": False})
    paths = {os.path.normcase(str(path.resolve())): path for path in _candidates(list(roots) if roots is not None else default_roots())}
    for key in by_path:
        paths.setdefault(key, Path(key))
    items = [describe(path, by_path.get(key)) | {"git": True} for key, path in paths.items()]
    items.sort(key=lambda item: item["last_commit"] or "", reverse=True)
    return items + sorted(not_git, key=lambda item: item["name"].lower())


def create_repository(name: str, parent: str | Path | None = None, *, description: str = "", github: bool = False) -> dict[str, Any]:
    name = str(name or "").strip()
    if not _NAME.match(name):
        raise ValueError("use a short name: letters, numbers, spaces, dots, dashes or underscores")
    base = Path(parent).expanduser() if parent else (default_roots() or [Path.home() / "GitHub"])[0]
    target = base / name
    if target.exists():
        raise ValueError(f"{target} already exists; pick another name")
    base.mkdir(parents=True, exist_ok=True)
    target.mkdir()
    try:
        if not _run(["git", "init", "-b", "main"], target):
            raise RuntimeError("git init failed")
        (target / "README.md").write_text(f"# {name}\n\n{description.strip()}\n" if description.strip() else f"# {name}\n", encoding="utf-8")
        (target / ".gitignore").write_text(".agent-local/\n__pycache__/\n*.pyc\n.venv/\nnode_modules/\n", encoding="utf-8")
        _run(["git", "add", "README.md", ".gitignore"], target)
        if not _run(["git", "commit", "-m", "Initial commit"], target):
            raise RuntimeError("the first commit failed; set your Git name and email (git config --global user.name / user.email)")
    except Exception:
        shutil.rmtree(target, ignore_errors=True)
        raise
    result = describe(target) | {"created": True, "github": None}
    if github:
        result["github"] = publish_to_github(target, name, description)
        result["remote"] = _git(target, "remote", "get-url", "origin") or None
    return result


def publish_to_github(target: Path, name: str, description: str = "") -> dict[str, Any]:
    """Create a private GitHub repository and push ``main``. Only called when
    the user ticked the box."""
    if shutil.which("gh") is None:
        return {"ok": False, "message": "GitHub CLI (gh) is not installed; the repository was created locally only"}
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", name).strip("-")
    command = ["gh", "repo", "create", slug, "--private", "--source", str(target), "--push"]
    if description.strip():
        command += ["--description", description.strip()[:300]]
    try:
        completed = subprocess.run(command, capture_output=True, text=True, timeout=120, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"ok": False, "message": f"GitHub publish failed: {type(exc).__name__}"}
    if completed.returncode != 0:
        return {"ok": False, "message": (completed.stderr or completed.stdout).strip()[:300] or "GitHub publish failed"}
    return {"ok": True, "message": (completed.stdout or "").strip()[:300]}


def _run(command: list[str], cwd: Path) -> bool:
    try:
        return subprocess.run(command, cwd=cwd, capture_output=True, text=True, timeout=60, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)).returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False
