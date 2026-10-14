"""Claude Code cloud sessions as an execution lane.

A cloud session runs on Anthropic's infrastructure, keeps going with this PC
off, and can be watched or steered from any device (claude.ai/code, the
Claude app). While a promotional cloud credit lasts (plan_extras.py), cloud
sessions spend it before the plan's own limits, so long autonomous tasks are
cheaper there than on the local plan.

``claude --cloud "task"`` refuses to start without an interactive terminal,
so ``submit`` runs it under a Windows pseudo-console (pywinpty), reads the
``View: https://claude.ai/code/session_...`` line it prints, and returns once
the CLI exits (about 10 seconds). Follow-ups use the documented
non-interactive form ``claude -p MESSAGE --cloud SESSION --output-format
json``. Results come back as a ``claude/`` branch or PR, or with ``claude
--teleport SESSION``; there is no status API, so the ledger records links and
the operator (or a later teleport) reads the outcome.

Guards, checked before anything is uploaded:

* sensitive repositories (model_profile.is_sensitive) never go to the cloud;
* the folder must already be trusted by Claude Code: a trust prompt aborts
  the submit and is never answered here;
* on native Windows the CLI uploads uncommitted changes to tracked files as
  they are when it bundles the repository, so a dirty working tree is refused
  unless ``allow_dirty``.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

ANSI = re.compile(r"\x1b\[[0-9;?]*[ -/]*[@-~]|\x1b\][^\x07\x1b]*(\x07|\x1b\\)|\x1b[=>()][0-9A-Za-z]?")
VIEW = re.compile(r"https://claude\.ai/code/((?:session|cse)_[A-Za-z0-9]+)")
TRUST = re.compile(r"trust\s*this\s*folder", re.I)
STRIPPED_ENV = ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_BASE_URL")


class CloudLaneError(RuntimeError):
    pass


def ledger_path(home: Path) -> Path:
    return Path(home) / "cloud-sessions.jsonl"


def _env() -> dict[str, str]:
    env = {key: value for key, value in os.environ.items() if key not in STRIPPED_ENV}
    env.setdefault("TERM", "xterm-256color")
    return env


def _git(repo: Path, *args: str) -> str:
    done = subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
    if done.returncode:
        raise CloudLaneError(f"git {' '.join(args)} failed: {(done.stderr or done.stdout).strip()[:300]}")
    return done.stdout


def preflight(repo: Path, *, allow_dirty: bool = False, sensitive: bool | None = None) -> dict[str, Any]:
    """Why ``repo`` may or may not go to a cloud session."""
    from .model_profile import is_sensitive

    repo = Path(repo).resolve()
    if not (repo / ".git").exists():
        raise CloudLaneError(f"{repo} is not the root of a git repository")
    if (is_sensitive({}, str(repo)) if sensitive is None else sensitive):
        raise CloudLaneError(f"{repo.name} holds sensitive data (sensitive_data policy); cloud sessions are not allowed for it")
    dirty = [line[3:] for line in _git(repo, "status", "--porcelain", "--untracked-files=no").splitlines() if line.strip()]
    if dirty and not allow_dirty:
        raise CloudLaneError(f"{len(dirty)} uncommitted tracked change(s) would be uploaded as they are (e.g. {dirty[0]}); commit or stash first")
    branch = _git(repo, "rev-parse", "--abbrev-ref", "HEAD").strip()
    remote = _git(repo, "remote").split()
    return {"repo": str(repo), "branch": branch, "remote": remote[0] if remote else None, "dirty": dirty,
            "note": "clones the GitHub remote at this branch when the Claude GitHub App is installed; otherwise uploads a bundle of this checkout"}


def _record(home: Path, entry: dict[str, Any]) -> None:
    path = ledger_path(home)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, sort_keys=True) + "\n")


def sessions(home: Path) -> list[dict[str, Any]]:
    """Ledger entries, newest first, with follow-up entries folded in."""
    try:
        lines = ledger_path(home).read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    out: dict[str, dict[str, Any]] = {}
    for line in lines:
        try:
            item = json.loads(line)
        except ValueError:
            continue
        sid = item.get("session_id")
        if not sid:
            continue
        if item.get("event") == "followup":
            out.setdefault(sid, {"session_id": sid}).setdefault("followups", []).append({"at": item.get("at"), "ok": item.get("ok")})
        else:
            out[sid] = {**out.get(sid, {}), **item}
    return sorted(out.values(), key=lambda item: str(item.get("at") or ""), reverse=True)


def _spawn_pty(argv: list[str], cwd: str, env: dict[str, str]):
    from winpty import PtyProcess  # optional dependency: pip install pywinpty

    return PtyProcess.spawn(argv, cwd=cwd, env=env, dimensions=(50, 220))


def submit(repo: Path, task: str, *, home: Path, allow_dirty: bool = False, timeout: float = 180.0,
           spawn: Callable[..., Any] = _spawn_pty, executable: str | None = None, sensitive: bool | None = None) -> dict[str, Any]:
    """Start a Claude cloud session for ``task`` on ``repo``; returns its id and links."""
    if not task.strip():
        raise CloudLaneError("task is empty")
    info = preflight(repo, allow_dirty=allow_dirty, sensitive=sensitive)
    exe = executable or shutil.which("claude")
    if not exe:
        raise CloudLaneError("the claude CLI is not on PATH")
    proc = spawn([exe, "--cloud", task], info["repo"], _env())
    chunks: list[str] = []

    def drain() -> None:
        while True:
            try:
                data = proc.read(4096)
            except (EOFError, OSError):
                return
            if data:
                chunks.append(data)

    threading.Thread(target=drain, daemon=True).start()
    started, session_id, error = time.monotonic(), None, None
    try:
        while time.monotonic() - started < timeout:
            text = ANSI.sub("", "".join(chunks))
            match = VIEW.search(text)
            if match:
                session_id = match.group(1)
                break
            if TRUST.search(text):
                error = "Claude Code has not trusted this folder yet: open `claude` in it once and accept the prompt, then retry"
                break
            if not proc.isalive():
                time.sleep(0.5)
                text = ANSI.sub("", "".join(chunks))
                match = VIEW.search(text)
                session_id = match.group(1) if match else None
                if not session_id:
                    error = "claude exited without creating a cloud session: " + " ".join(text.split())[-400:]
                break
            time.sleep(0.5)
        else:
            error = f"no cloud session link after {int(timeout)} s"
    finally:
        if proc.isalive():
            proc.terminate(force=True)
    if error:
        raise CloudLaneError(error)
    entry = {"event": "submit", "session_id": session_id, "url": f"https://claude.ai/code/{session_id}",
             "teleport": f"claude --teleport {session_id}", "repo": info["repo"], "branch": info["branch"],
             "task": task[:500], "at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    _record(home, entry)
    return entry


def send(session_id: str, message: str, *, home: Path, run: Callable[..., Any] = subprocess.run,
         executable: str | None = None) -> dict[str, Any]:
    """Queue a follow-up message into a running cloud session."""
    exe = executable or shutil.which("claude")
    if not exe:
        raise CloudLaneError("the claude CLI is not on PATH")
    done = run([exe, "-p", message, "--cloud", session_id, "--output-format", "json"], capture_output=True, text=True,
               encoding="utf-8", errors="replace", timeout=120, env=_env())
    try:
        result = json.loads((done.stdout or "").strip() or "{}")
    except ValueError:
        result = {}
    ok = bool(result.get("ok"))
    _record(home, {"event": "followup", "session_id": session_id, "ok": ok, "at": datetime.now(timezone.utc).isoformat(timespec="seconds")})
    if not ok:
        raise CloudLaneError(result.get("error") or (done.stderr or done.stdout or "send failed").strip()[:400])
    return result
