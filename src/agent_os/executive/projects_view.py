"""Project metadata and resumable session identities, never transcript text."""
from __future__ import annotations

import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .. import chat, registry
from ..machine import resolve_path, search_roots
from ..orchestrator import cloud_lane, model_profile, usage_hub


def project_path(project: str) -> Path:
    value = registry.get_project(project).get("path")
    if not value or not Path(value).is_dir():
        raise ValueError("project has no local checkout")
    return Path(value).resolve()


def _same_path(left: Any, right: Any) -> bool:
    if not left or not right:
        return False
    return str(Path(str(left)).resolve()).casefold() == str(Path(str(right)).resolve()).casefold()


def _modified(path: Path) -> str:
    return datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat(timespec="seconds")


def _claude_sessions(path: Path, home: Path) -> list[dict]:
    # Claude replaces every non-alphanumeric cwd character, including spaces.
    slug = re.sub(r"[^a-zA-Z0-9]", "-", str(path))
    out = []
    for source in (home / ".claude" / "projects" / slug).glob("*.jsonl"):
        try:
            out.append({"id": source.stem, "modified_at": _modified(source)})
        except OSError:
            continue
    return sorted(out, key=lambda p: p["modified_at"], reverse=True)


def _codex_sessions(path: Path, home: Path) -> list[dict]:
    out = []
    for source in (home / ".codex" / "sessions").rglob("*.jsonl"):
        try:
            with source.open(encoding="utf-8") as handle:
                # A bounded first line; never scan messages later in the file.
                event = json.loads(handle.readline(65536))
            payload = event.get("payload") or {}
            if event.get("type") == "session_meta" and payload.get("id") and _same_path(payload.get("cwd"), path):
                out.append({"id": payload["id"], "modified_at": _modified(source)})
        except (OSError, ValueError, AttributeError):
            continue
    return sorted(out, key=lambda p: p["modified_at"], reverse=True)


def _git(path: Path, runner: Any) -> dict | None:
    if not (path / ".git").exists():
        return None
    def run(*args: str) -> str:
        done = runner(["git", *args], cwd=str(path), capture_output=True, text=True,
                      encoding="utf-8", errors="replace", timeout=15)
        return done.stdout.strip() if done.returncode == 0 else ""
    try:
        branch = run("rev-parse", "--abbrev-ref", "HEAD")
        counts = run("rev-list", "--left-right", "--count", "HEAD...@{upstream}").split()
        ahead, behind = map(int, counts) if len(counts) == 2 else (None, None)
        dirty = len(run("status", "--porcelain").splitlines())
        return {"branch": branch or None, "ahead": ahead, "behind": behind, "dirty": dirty}
    except (OSError, subprocess.SubprocessError, ValueError):
        return None


def projects(*, home: Path | str | None = None, state_home: Path | None = None, entries: list[dict] | None = None,
             runner: Any = None, resolver: Any = None, handoff_reader: Any = None) -> list[dict]:
    """Inventory can be embedded with explicit homes, registry and fake git."""
    user_home = Path(home) if home is not None else Path.home()
    state_home = state_home if state_home is not None else usage_hub._home()
    entries = registry.canonical_projects() if entries is None else entries
    roots = search_roots([p.get("path") or "" for p in entries]) if resolver is None else []
    clouds = cloud_lane.sessions(state_home)
    rows = []
    for entry in entries:
        local, _source = (resolver or resolve_path)(entry, roots)
        path = Path(local).resolve() if local and Path(local).is_dir() else None
        # Canonical identity still carries sensitivity when the checkout is missing.
        sensitive = model_profile.is_sensitive({}, str(path or entry.get("path") or entry.get("directory") or entry["id"]), state_home)
        handoff = (handoff_reader or chat.latest_project_handoff)(entry["id"])
        summary = {key: handoff[key] for key in ("created_at", "completed", "remaining", "decisions", "validation") if key in handoff} if handoff else None
        rows.append({"id": entry["id"], "name": entry.get("name") or entry["id"], "path": str(path) if path else None,
                     "sensitive": sensitive, "git": _git(path, runner or subprocess.run) if path else None, "handoff": summary,
                     "claude_sessions": _claude_sessions(path, user_home) if path else [],
                     "codex_sessions": _codex_sessions(path, user_home) if path else [],
                     "cloud_sessions": [{key: s.get(key) for key in ("session_id", "url", "at", "branch")}
                                        for s in clouds if path and _same_path(s.get("repo"), path)]})
    return rows


def resume_command(kind: str, session_id: str, path: Path | str, *, popen: Any = None) -> dict:
    if kind not in {"claude", "codex", "cloud"}:
        raise ValueError("kind must be claude, codex or cloud")
    if not isinstance(session_id, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,199}", session_id):
        raise ValueError("invalid session id")
    if not Path(path).is_dir():
        raise ValueError("project checkout is missing")
    argv = {"claude": ["claude", "--resume", session_id], "codex": ["codex", "resume", session_id],
            "cloud": ["claude", "--teleport", session_id]}[kind]
    (popen or subprocess.Popen)(argv, cwd=str(Path(path).resolve()),
                                creationflags=getattr(subprocess, "CREATE_NEW_CONSOLE", 0))
    return {"opened": True, "kind": kind, "session_id": session_id}
