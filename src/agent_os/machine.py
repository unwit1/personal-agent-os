"""Machine-local resolution of project checkout locations.

Canonical registry data in Git stores portable project identity. Absolute
checkout locations differ per machine, so they are resolved here from a
gitignored local override, self-identification, or discovery across a small set
of registered search roots. Nothing in this module writes to canonical state.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from .paths import ROOT


LOCAL_CONFIG_ENV = "AGENT_OS_LOCAL_CONFIG"
LOCAL_CONFIG_PATH = ROOT / ".agent-local" / "machine.json"
HOME_CONFIG_PATH = Path.home() / ".agent-os" / "config.json"


def _read(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def config_sources() -> list[Path]:
    """Lowest precedence first."""
    sources = [HOME_CONFIG_PATH, LOCAL_CONFIG_PATH]
    override = os.environ.get(LOCAL_CONFIG_ENV)
    if override:
        sources.append(Path(override).expanduser())
    return sources


def local_config() -> dict[str, Any]:
    project_paths: dict[str, str] = {}
    search_roots: list[str] = []
    for source in config_sources():
        data = _read(source)
        paths = data.get("project_paths")
        if isinstance(paths, dict):
            project_paths.update({str(key): str(value) for key, value in paths.items()})
        roots = data.get("search_roots")
        if isinstance(roots, list):
            search_roots.extend(str(item) for item in roots)
    return {"project_paths": project_paths, "search_roots": search_roots}


REPOSITORY_PREFIX = "repo/"


def resolve_user_path(location: str) -> Path:
    """Resolve a machine-independent location declared in canonical state.

    Canonical registries store `~`, `${VAR}`, and `repo/` locations so one entry
    describes every machine. Expansion belongs here with the rest of the
    machine-local resolution rather than in each caller.
    """
    text = str(location).replace("\\", "/")
    if text.casefold().startswith(REPOSITORY_PREFIX):
        return ROOT.joinpath(*text[len(REPOSITORY_PREFIX):].split("/"))
    return Path(os.path.expandvars(text)).expanduser()


DEFAULT_HOME_ROOTS = ("Projects", "GitHub", "repos", "source/repos", "dev")


def search_roots(canonical_paths: list[str] | None = None) -> list[Path]:
    """Bounded discovery roots. Never the drive root and never a crawl."""
    candidates = [Path(item).expanduser() for item in local_config()["search_roots"]]
    candidates.append(ROOT.parent)
    candidates.extend(Path.home() / item for item in DEFAULT_HOME_ROOTS)
    for value in canonical_paths or []:
        parent = Path(value).expanduser().parent
        if parent.name:
            candidates.append(parent)
    roots: list[Path] = []
    seen: set[str] = set()
    for candidate in candidates:
        try:
            resolved = candidate.resolve()
        except OSError:
            continue
        key = str(resolved).casefold()
        if key in seen or resolved.parent == resolved or not resolved.is_dir():
            continue
        seen.add(key)
        roots.append(resolved)
    return roots


def _discover(directory: str, roots: list[Path]) -> Path | None:
    wanted = directory.casefold()
    for root in roots:
        try:
            entries = list(root.iterdir())
        except OSError:
            continue
        for entry in entries:
            if entry.is_dir() and entry.name.casefold() == wanted:
                return entry
    return None


def resolve_path(project: dict[str, Any], roots: list[Path] | None = None) -> tuple[Path, str]:
    """Return the effective local checkout path and how it was resolved."""
    project_id = str(project.get("id", ""))
    canonical = str(project.get("path") or "")
    override = local_config()["project_paths"].get(project_id)
    if override:
        return Path(override).expanduser(), "local_override"
    if project.get("canonical_owner") == "this_repository":
        return ROOT, "this_repository"
    if canonical and Path(canonical).expanduser().is_dir():
        return Path(canonical).expanduser(), "registry_path"
    directory = str(project.get("directory") or "") or (Path(canonical).name if canonical else project_id)
    if directory:
        found = _discover(directory, roots if roots is not None else search_roots([canonical] if canonical else []))
        if found:
            return found, "discovered"
    return Path(canonical or ROOT / directory), "unresolved"


def describe() -> dict[str, Any]:
    config = local_config()
    return {
        "root": str(ROOT),
        "config_sources": [
            {"path": str(source), "exists": source.exists()} for source in config_sources()
        ],
        "search_roots": [str(item) for item in search_roots()],
        "project_path_overrides": sorted(config["project_paths"]),
    }


def write_override(project_id: str, path: str | None, search_root: str | None = None) -> dict[str, Any]:
    """Record a machine-local checkout location. Never touches canonical state."""
    data = _read(LOCAL_CONFIG_PATH) or {"schema_version": 1}
    paths = data.setdefault("project_paths", {})
    roots = data.setdefault("search_roots", [])
    if path is not None:
        paths[project_id] = str(Path(path).expanduser())
    elif project_id in paths:
        del paths[project_id]
    if search_root:
        resolved = str(Path(search_root).expanduser())
        if resolved not in roots:
            roots.append(resolved)
    LOCAL_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    LOCAL_CONFIG_PATH.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n"
    )
    return {"written": str(LOCAL_CONFIG_PATH), "project_paths": paths, "search_roots": roots}
