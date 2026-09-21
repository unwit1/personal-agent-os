"""Provider-neutral restart recovery and incremental work primitives.

The records written here are deliberately local and compact.  They describe a
checkout and a unit of work well enough for a different coding agent to resume
it, but never persist prompts, transcripts, source text, or private imported
content.  Git remains the canonical home for schemas and deterministic code;
``.agent-local/recovery`` is disposable runtime state.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .paths import ROOT
from .storage import load_json, write_json


CHECKPOINT_SCHEMA_VERSION = 1
LEDGER_SCHEMA_VERSION = 1
FORBIDDEN_KEYS = {"transcript", "messages", "history", "conversation", "prompt", "chain_of_thought"}
MAX_CHECKPOINT_BYTES = 64 * 1024


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _digest(value: Any, length: int = 16) -> str:
    blob = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()[:length]


def stable_id(kind: str, semantic_identity: str) -> str:
    """A deterministic ID based on meaning, never a checkout path or clock."""
    clean_kind = "".join(ch if ch.isalnum() or ch in "-_" else "-" for ch in kind).strip("-") or "item"
    normalized = " ".join(str(semantic_identity).strip().casefold().split())
    return f"{clean_kind}-{_digest({'kind': clean_kind, 'identity': normalized})}"


def _git(repo: Path, *args: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", *args], cwd=str(repo), capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=20,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return result.stdout.rstrip() if result.returncode == 0 else None


def _remote(repo: Path) -> str | None:
    value = _git(repo, "config", "--get", "remote.origin.url")
    if not value:
        return None
    return value.removesuffix(".git").rstrip("/").casefold()


def repository_identity(repo: Path = ROOT) -> dict[str, Any]:
    repo = Path(repo).resolve()
    remote = _remote(repo)
    top_level = _git(repo, "rev-parse", "--show-toplevel")
    # A remote is the cross-checkout identity.  The fallback is explicitly
    # marked local-only rather than pretending a filesystem path is canonical.
    semantic = remote or (top_level or repo.name).casefold()
    return {
        "kind": "git" if top_level else "directory",
        "remote": remote,
        "repository_id": stable_id("repository", semantic),
        "local_only": remote is None,
    }


def stable_project_id(repo: Path = ROOT, preferred: str | None = None) -> str:
    if preferred:
        return preferred
    remote = _remote(Path(repo))
    if remote:
        try:
            registry = load_json(ROOT / "projects" / "registry.json")
            for project in registry.get("projects", []):
                candidate = str(project.get("repository") or "").removesuffix(".git").rstrip("/").casefold()
                if candidate and candidate == remote:
                    return str(project["id"])
        except (OSError, json.JSONDecodeError, KeyError):
            pass
    return stable_id("project", repository_identity(repo)["repository_id"])


def _sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError:
        return "unreadable"
    return digest.hexdigest()


def _status_inventory(repo: Path) -> dict[str, list[str]]:
    raw = _git(repo, "status", "--porcelain=v1", "-z", "--untracked-files=all")
    inventory = {"modified": [], "staged": [], "untracked": [], "deleted": [], "renamed": []}
    if raw is None:
        return inventory
    fields = raw.split("\0")
    index = 0
    while index < len(fields):
        entry = fields[index]
        index += 1
        if not entry:
            continue
        code, path = entry[:2], entry[3:]
        # In porcelain -z, rename/copy source follows the destination.
        old = None
        if "R" in code or "C" in code:
            old = fields[index] if index < len(fields) else None
            index += 1
            inventory["renamed"].append(f"{old or '?'} -> {path}")
        if code == "??":
            inventory["untracked"].append(path)
            continue
        if "D" in code:
            inventory["deleted"].append(path)
        if code[0] not in {" ", "?"}:
            inventory["staged"].append(path)
        if code[1] not in {" ", "?"}:
            inventory["modified"].append(path)
    return {key: sorted(set(values)) for key, values in inventory.items()}


def working_tree_fingerprint(repo: Path = ROOT) -> dict[str, Any]:
    """Hash status and diffs without putting any source content in a record."""
    repo = Path(repo).resolve()
    inventory = _status_inventory(repo)
    untracked_hashes = {
        name: _sha256_path(repo / name) for name in inventory["untracked"] if (repo / name).is_file()
    }
    payload = {
        "head": _git(repo, "rev-parse", "HEAD"),
        "branch": _git(repo, "branch", "--show-current"),
        "base_commit": _git(repo, "merge-base", "HEAD", "@{upstream}"),
        "inventory": inventory,
        "unstaged_diff": _git(repo, "diff", "--no-ext-diff", "--binary") or "",
        "staged_diff": _git(repo, "diff", "--cached", "--no-ext-diff", "--binary") or "",
        "untracked_hashes": untracked_hashes,
    }
    # Only fixed-length digests leave this function. The patch text is scoped
    # to this local calculation and never written into the checkpoint.
    return {
        "algorithm": "sha256",
        "value": _digest(payload, 64),
        "head": payload["head"],
        "branch": payload["branch"],
        "base_commit": payload["base_commit"],
        "inventory": inventory,
        "untracked_hashes": untracked_hashes,
    }


def runtime_dir(repo: Path = ROOT) -> Path:
    return Path(repo) / ".agent-local" / "recovery"


def checkpoint_path(project_id: str, run_id: str, repo: Path = ROOT) -> Path:
    return runtime_dir(repo) / "checkpoints" / project_id / f"{run_id}.json"


def _assert_compact(record: dict[str, Any]) -> None:
    def walk(value: Any) -> None:
        if isinstance(value, dict):
            bad = FORBIDDEN_KEYS.intersection(value)
            if bad:
                raise ValueError("checkpoint must not persist transcripts or prompts: " + ", ".join(sorted(bad)))
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)
    walk(record)
    if len(json.dumps(record, separators=(",", ":"), ensure_ascii=True).encode("utf-8")) > MAX_CHECKPOINT_BYTES:
        raise ValueError("checkpoint exceeds compact recovery budget")


def create_checkpoint(
    *, project_id: str | None = None, workflow_id: str, run_id: str,
    stage_id: str | None, completed_stages: list[str] | None = None,
    unresolved_work: list[str] | None = None, validation_state: dict[str, Any] | None = None,
    tests_run: list[dict[str, Any]] | None = None, known_failures: list[str] | None = None,
    decisions: list[str] | None = None, next_action: str | None = None,
    recommended_capability_class: str | None = None, touched_files: list[str] | None = None,
    origin: dict[str, str] | None = None, repo: Path = ROOT,
) -> dict[str, Any]:
    """Create/update the one durable local checkpoint for a workflow run."""
    repo = Path(repo).resolve()
    project = stable_project_id(repo, project_id)
    fingerprint = working_tree_fingerprint(repo)
    path = checkpoint_path(project, run_id, repo)
    previous: dict[str, Any] = {}
    try:
        if path.exists():
            previous = load_json(path)
    except (OSError, json.JSONDecodeError):
        previous = {}
    inventory = fingerprint["inventory"]
    observed = sorted({*inventory["modified"], *inventory["staged"], *inventory["deleted"], *inventory["renamed"]})
    record = {
        "schema_version": CHECKPOINT_SCHEMA_VERSION,
        "checkpoint_id": previous.get("checkpoint_id") or stable_id("checkpoint", f"{project}:{workflow_id}:{run_id}"),
        "run_id": run_id,
        "project_id": project,
        "workflow_id": workflow_id,
        "stage_id": stage_id,
        "created_at": previous.get("created_at") or _now(),
        "updated_at": _now(),
        "repository": repository_identity(repo),
        "branch": fingerprint["branch"],
        "base_commit": fingerprint["base_commit"] or fingerprint["head"],
        "last_known_head": fingerprint["head"],
        "working_tree_fingerprint": fingerprint,
        "touched_files": sorted(set(touched_files or observed)),
        "newly_created_untracked_files": inventory["untracked"],
        "completed_stages": sorted(set(completed_stages or [])),
        "current_stage": stage_id,
        "unresolved_work": list(unresolved_work or []),
        "validation_state": validation_state or {},
        "tests_run": list(tests_run or []),
        "known_failures": list(known_failures or []),
        "decisions": list(decisions or []),
        "next_action": next_action or "Inspect recovery status before continuing.",
        "recommended_capability_class": recommended_capability_class or "deterministic",
        "origin": origin or {},
    }
    _assert_compact(record)
    write_json(path, record)
    return record


def list_checkpoints(project_id: str | None = None, repo: Path = ROOT) -> list[dict[str, Any]]:
    repo = Path(repo).resolve()
    base = runtime_dir(repo) / "checkpoints"
    roots = [base / project_id] if project_id else list(base.glob("*")) if base.exists() else []
    result: list[dict[str, Any]] = []
    for directory in roots:
        if not directory.exists():
            continue
        for path in directory.glob("*.json"):
            try:
                item = load_json(path)
                result.append({key: item.get(key) for key in ("checkpoint_id", "project_id", "workflow_id", "run_id", "current_stage", "updated_at")})
            except (OSError, json.JSONDecodeError):
                result.append({"path": str(path), "status": "corrupted"})
    return sorted(result, key=lambda item: str(item.get("updated_at", "")), reverse=True)


def get_checkpoint(project_id: str, run_id: str, repo: Path = ROOT) -> dict[str, Any]:
    return load_json(checkpoint_path(project_id, run_id, repo))


def latest_checkpoint(project_id: str | None = None, repo: Path = ROOT) -> dict[str, Any] | None:
    items = list_checkpoints(project_id, repo)
    valid = [item for item in items if item.get("checkpoint_id")]
    if not valid:
        return None
    return get_checkpoint(valid[0]["project_id"], valid[0]["run_id"], repo)


def _recovery_status(checkpoint: dict[str, Any], current: dict[str, Any], repo: Path) -> tuple[str, bool, str | None]:
    saved = checkpoint.get("working_tree_fingerprint") or {}
    if checkpoint.get("repository", {}).get("repository_id") != repository_identity(repo)["repository_id"]:
        return "conflicting_changes_requiring_review", False, "checkpoint belongs to a different repository"
    if saved.get("value") == current.get("value"):
        return "interrupted_resumable_task", True, None
    if saved.get("branch") != current.get("branch") or saved.get("head") != current.get("head"):
        return "interrupted_task_with_external_changes", False, "branch or HEAD moved after checkpoint"
    saved_files = set(checkpoint.get("touched_files") or []) | set(checkpoint.get("newly_created_untracked_files") or [])
    current_files = set().union(*[set(values) for values in current["inventory"].values()])
    if saved_files and saved_files.issubset(current_files):
        return "interrupted_task_with_additional_safe_edits", True, "working tree has additional non-overlapping edits"
    return "conflicting_changes_requiring_review", False, "checkpointed edits were changed or removed"


def inspect_recovery(project_id: str | None = None, run_id: str | None = None, repo: Path = ROOT) -> dict[str, Any]:
    repo = Path(repo).resolve()
    project = stable_project_id(repo, project_id)
    path = checkpoint_path(project, run_id, repo) if run_id else None
    try:
        checkpoint = get_checkpoint(project, run_id, repo) if run_id else latest_checkpoint(project, repo)
    except (OSError, json.JSONDecodeError, KeyError) as error:
        return {"status": "corrupted_checkpoint", "safe_to_continue": False, "detail": str(error)}
    current = working_tree_fingerprint(repo)
    dirty = any(current["inventory"].values())
    if checkpoint is None:
        return {
            "status": "ambiguous_local_work" if dirty else "clean_new_task",
            "safe_to_continue": not dirty,
            "project_id": project,
            "working_tree": current,
            "detail": "local changes have no matching Agent OS checkpoint" if dirty else None,
        }
    status, safe, detail = _recovery_status(checkpoint, current, repo)
    return {
        "status": status,
        "safe_to_continue": safe,
        "detail": detail,
        "checkpoint": checkpoint,
        "working_tree": current,
        "continuation": {
            "project_id": checkpoint["project_id"],
            "workflow_id": checkpoint["workflow_id"],
            "run_id": checkpoint["run_id"],
            "completed_stages": checkpoint["completed_stages"],
            "current_stage": checkpoint["current_stage"],
            "validation_state": checkpoint["validation_state"],
            "next_action": checkpoint["next_action"],
            "recommended_capability_class": checkpoint["recommended_capability_class"],
        },
    }


def resume_recovery(project_id: str | None = None, run_id: str | None = None, repo: Path = ROOT) -> dict[str, Any]:
    result = inspect_recovery(project_id, run_id, repo)
    if not result.get("safe_to_continue"):
        result["resumed"] = False
        return result
    result["resumed"] = result["status"] != "clean_new_task"
    return result


def checkpoint_workflow_record(record: dict[str, Any], repo: Path = ROOT) -> dict[str, Any] | None:
    """Project P0.1 stage state into a local P0.4 checkpoint at safe boundaries."""
    if not (Path(repo) / ".git").exists():
        return None  # Fixtures and non-repositories keep P0.1's old contract.
    stages = record.get("stages", {})
    completed = [stage_id for stage_id, state in stages.items() if state.get("status") == "complete"]
    current = next((stage_id for stage_id, state in stages.items() if state.get("status") != "complete"), None)
    state = stages.get(current, {}) if current else {}
    validation = state.get("validation") or {}
    failures = [str(validation.get("detail"))] if validation and not validation.get("passed", True) and validation.get("detail") else []
    return create_checkpoint(
        project_id=record.get("project"), workflow_id=record["workflow_id"], run_id=record["run_id"],
        stage_id=current, completed_stages=completed,
        unresolved_work=[] if current is None else [f"Complete stage {current}"],
        validation_state=validation, known_failures=failures,
        next_action=(f"Run workflow-stage {record['workflow_id']} --run-id {record['run_id']}" if current else "Workflow complete."),
        recommended_capability_class=state.get("capability_class", "deterministic"), repo=repo,
    )


class IncrementalLedger:
    """A local, idempotent processed-state ledger reusable by any connector."""

    def __init__(self, source_identity: str, *, kind: str = "source", repo: Path = ROOT) -> None:
        self.repo = Path(repo).resolve()
        self.source_id = stable_id(kind, source_identity)
        self.path = runtime_dir(self.repo) / "ledgers" / f"{self.source_id}.json"
        self.source_fingerprint = _digest({"kind": kind, "source": source_identity}, 64)

    def _load(self) -> dict[str, Any]:
        try:
            record = load_json(self.path)
            if record.get("schema_version") == LEDGER_SCHEMA_VERSION:
                return record
        except (OSError, json.JSONDecodeError):
            pass
        return {"schema_version": LEDGER_SCHEMA_VERSION, "source_id": self.source_id,
                "source_fingerprint": self.source_fingerprint, "updated_at": _now(), "cursor": None, "items": {}}

    def _save(self, record: dict[str, Any]) -> None:
        record["updated_at"] = _now()
        write_json(self.path, record)

    def claim(self, item_identity: str, item_fingerprint: str, processor_version: str) -> dict[str, Any]:
        record = self._load()
        item_id = stable_id("item", item_identity)
        existing = record["items"].get(item_id)
        if existing and existing.get("status") == "success" and existing.get("fingerprint") == item_fingerprint and existing.get("processor_version") == processor_version:
            return {"action": "skip", "item_id": item_id, "reason": "already processed"}
        retries = int(existing.get("retry_count", 0)) if existing else 0
        record["items"][item_id] = {"fingerprint": item_fingerprint, "processor_version": processor_version,
                                    "status": "processing", "retry_count": retries, "last_processed_at": None}
        self._save(record)
        return {"action": "process", "item_id": item_id}

    def complete(self, item_id: str, *, cursor: str | None = None) -> None:
        record = self._load()
        item = record["items"].get(item_id)
        if not item:
            raise KeyError(f"unknown item: {item_id}")
        item["status"] = "success"
        item["last_processed_at"] = _now()
        if cursor is not None:
            record["cursor"] = cursor
        self._save(record)

    def fail(self, item_id: str, detail: str) -> None:
        record = self._load()
        item = record["items"].get(item_id)
        if not item:
            raise KeyError(f"unknown item: {item_id}")
        item["status"] = "failed"
        item["retry_count"] = int(item.get("retry_count", 0)) + 1
        item["failure"] = detail[:500]
        self._save(record)

    def status(self) -> dict[str, Any]:
        record = self._load()
        counts: dict[str, int] = {}
        for item in record["items"].values():
            counts[item["status"]] = counts.get(item["status"], 0) + 1
        return {"source_id": self.source_id, "source_fingerprint": record["source_fingerprint"],
                "cursor": record.get("cursor"), "counts": counts}
