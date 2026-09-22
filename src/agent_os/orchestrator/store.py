"""Local persistence for orchestrated runs.

Run records hold compact structured state: node states, selections, worktree
ownership, validator evidence, review findings, and checkpoints. They never
hold a transcript, and string values are redacted for obvious secrets before
they are written. The records carry machine-specific paths and process IDs, so
they live in the gitignored local runtime tree, not in canonical Git state;
durable outcomes reach Git through handoffs.
"""

from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path
from typing import Any, Iterator

from ..local_paths import is_gitignored_local_path
from ..paths import ROOT
from ..storage import load_json, write_json
from ..timestamps import utc_now_iso as now
from .model import RUN_SCHEMA


HOME_ENV = "AGENT_OS_ORCHESTRATOR_HOME"
DEFAULT_HOME = ROOT / ".agent-local" / "orchestrator"

# Carrying conversation forward is the cost staged work exists to avoid; the
# same rule the staged workflow runner enforces applies here, recursively.
FORBIDDEN_KEYS = frozenset({"transcript", "messages", "history", "conversation"})

_SECRET_PATTERNS = (
    re.compile(r"\b(sk-(?:ant-)?[A-Za-z0-9_-]{12,})"),
    re.compile(r"\b(gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})"),
    re.compile(r"\b(xox[baprs]-[A-Za-z0-9-]{10,})"),
    re.compile(r"(?i)((?:api[_-]?key|access[_-]?token|password|secret|authorization)\s*[:=]\s*)(\S+)"),
    re.compile(r"(?i)(bearer\s+)([A-Za-z0-9._-]{12,})"),
)
MAX_EVENT_DETAIL = 400


class StoreError(ValueError):
    pass


def orchestrator_home() -> Path:
    configured = os.environ.get(HOME_ENV)
    return Path(configured).expanduser() if configured else DEFAULT_HOME


def redact(text: Any, limit: int | None = None) -> str:
    value = str(text if text is not None else "")
    for pattern in _SECRET_PATTERNS:
        if pattern.groups >= 2:
            value = pattern.sub(lambda match: match.group(1) + "[redacted]", value)
        else:
            value = pattern.sub("[redacted]", value)
    if limit is not None and len(value) > limit:
        value = value[: max(limit - 1, 0)] + "…"
    return value


def _scrub(value: Any, path: str = "") -> Any:
    if isinstance(value, dict):
        forbidden = FORBIDDEN_KEYS.intersection(value)
        if forbidden:
            raise StoreError(
                "run state must not carry conversation context: "
                + ", ".join(f"{path}.{key}".lstrip(".") for key in sorted(forbidden))
            )
        return {key: _scrub(item, f"{path}.{key}") for key, item in value.items()}
    if isinstance(value, list):
        return [_scrub(item, f"{path}[]") for item in value]
    if isinstance(value, str):
        return redact(value)
    return value


def _pid_alive(pid: int | None) -> bool:
    if not pid:
        return False
    if os.name == "nt":
        import ctypes

        process_query_limited_information = 0x1000
        still_active = 259
        handle = ctypes.windll.kernel32.OpenProcess(process_query_limited_information, False, int(pid))
        if not handle:
            return False
        try:
            code = ctypes.c_ulong()
            if not ctypes.windll.kernel32.GetExitCodeProcess(handle, ctypes.byref(code)):
                return False
            return code.value == still_active
        finally:
            ctypes.windll.kernel32.CloseHandle(handle)
    try:
        os.kill(int(pid), 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False
    return True


pid_alive = _pid_alive


class RunStore:
    """Filesystem store: ``<home>/runs/<run_id>/{state.json,events.jsonl,workers/}``."""

    def __init__(self, home: Path | None = None) -> None:
        self.home = Path(home or orchestrator_home()).expanduser()
        if not is_gitignored_local_path(self.home):
            raise StoreError("orchestrator state must stay outside canonical Git state or under .agent-local")

    # -- paths -------------------------------------------------------------

    def run_dir(self, run_id: str) -> Path:
        return self.home / "runs" / run_id

    def state_path(self, run_id: str) -> Path:
        return self.run_dir(run_id) / "state.json"

    def events_path(self, run_id: str) -> Path:
        return self.run_dir(run_id) / "events.jsonl"

    def worker_dir(self, run_id: str, node_id: str, attempt: int) -> Path:
        path = self.run_dir(run_id) / "workers" / f"{node_id}-{attempt}"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def worktree_root(self, layout: str = "legacy") -> Path:
        # Short layout keeps worker checkouts shallow enough for Windows paths.
        return self.home / ("wt" if layout == "short" else "worktrees")

    # -- state -------------------------------------------------------------

    def exists(self, run_id: str) -> bool:
        return self.state_path(run_id).exists()

    def load(self, run_id: str) -> dict[str, Any]:
        path = self.state_path(run_id)
        if not path.exists():
            raise KeyError(f"unknown orchestrated run: {run_id}")
        record = load_json(path)
        if record.get("schema") != RUN_SCHEMA:
            raise StoreError(f"unsupported orchestrated run schema in {path}")
        return record

    def save(self, record: dict[str, Any]) -> dict[str, Any]:
        record["updated_at"] = now()
        clean = _scrub(record)
        write_json(self.state_path(record["run_id"]), clean)
        record.clear()
        record.update(clean)
        return record

    def list_runs(self) -> list[dict[str, Any]]:
        runs_root = self.home / "runs"
        if not runs_root.exists():
            return []
        items = []
        for path in sorted(runs_root.glob("*/state.json")):
            try:
                record = load_json(path)
            except (OSError, json.JSONDecodeError):
                continue
            items.append(
                {
                    "run_id": record.get("run_id"),
                    "goal": str(record.get("goal", ""))[:160],
                    "project": record.get("project"),
                    "state": record.get("state"),
                    "updated_at": record.get("updated_at"),
                }
            )
        return sorted(items, key=lambda item: item.get("updated_at") or "", reverse=True)

    # -- events ------------------------------------------------------------

    def append_event(self, run_id: str, kind: str, node: str | None = None, detail: Any = None) -> dict[str, Any]:
        event = {"at": now(), "seq": time.time_ns(), "type": kind, "node": node, "detail": redact(detail, MAX_EVENT_DETAIL) if detail is not None else None}
        path = self.events_path(run_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8", newline="") as handle:
            handle.write(json.dumps(event, ensure_ascii=False, separators=(",", ":")) + "\n")
        return event

    def read_events(self, run_id: str, after_seq: int = 0, limit: int = 500) -> list[dict[str, Any]]:
        path = self.events_path(run_id)
        if not path.exists():
            return []
        events: list[dict[str, Any]] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if int(event.get("seq", 0)) > after_seq:
                events.append(event)
        return events[-limit:]

    # -- driver ownership ----------------------------------------------------

    def driver_path(self, run_id: str) -> Path:
        return self.run_dir(run_id) / "driver.json"

    def driver(self, run_id: str) -> dict[str, Any]:
        path = self.driver_path(run_id)
        try:
            data = load_json(path)
        except (OSError, json.JSONDecodeError):
            return {"active": False}
        alive = pid_alive(data.get("pid"))
        return {**data, "active": alive}

    def acquire_driver(self, run_id: str, owner: str) -> bool:
        """Record that this process drives the run. A live driver elsewhere wins."""
        current = self.driver(run_id)
        if current.get("active") and current.get("pid") != os.getpid():
            return False
        write_json(self.driver_path(run_id), {"pid": os.getpid(), "owner": owner, "since": now()})
        return True

    def release_driver(self, run_id: str) -> None:
        current = self.driver(run_id)
        if current.get("pid") == os.getpid():
            try:
                self.driver_path(run_id).unlink()
            except FileNotFoundError:
                pass

    def iter_worker_files(self, run_id: str) -> Iterator[Path]:
        root = self.run_dir(run_id) / "workers"
        if root.exists():
            yield from root.rglob("*")
