"""Per-worker Git branches and worktrees.

Every editing node gets its own branch and its own worktree under the Agent OS
local runtime directory, so concurrent agents can never share one writable
tree. The run keeps an integration branch/worktree that only receives merges of
validated work. Failed workers' branches and worktrees are left in place for
inspection and recovery; cleanup happens only after successful integration and
never force-deletes an unmerged branch.
"""

from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any


COMMITTER = ("-c", "user.name=Agent OS Orchestrator", "-c", "user.email=agent-os@localhost")
# Worker worktrees sit several directories below the main checkout; without
# long-path support a deep repository file overflows MAX_PATH on Windows and
# ``git worktree add`` fails half-way through the checkout.
LONG_PATHS = ("-c", "core.longpaths=true")
# Generated files a worker or validator leaves behind are never part of a
# change: committing them would fail the editable-scope check for nothing.
ARTIFACT_EXCLUDES = (
    ":(exclude,glob)**/__pycache__/**",
    ":(exclude,glob)**/*.pyc",
    ":(exclude,glob)**/.pytest_cache/**",
    ":(exclude,glob)**/.mypy_cache/**",
    ":(exclude,glob)**/.ruff_cache/**",
)
MAX_DIFF_CHARS = 60_000


class GitError(RuntimeError):
    pass


def git(args: list[str], cwd: Path | str, check: bool = True, identity: bool = False) -> subprocess.CompletedProcess:
    command = ["git", *LONG_PATHS, *(COMMITTER if identity else ()), *args]
    completed = subprocess.run(
        command,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdin=subprocess.DEVNULL,
        env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
    )
    if check and completed.returncode != 0:
        raise GitError(f"git {' '.join(args)} failed: {(completed.stderr or completed.stdout).strip()[:400]}")
    return completed


def repository_root(path: Path | str) -> Path:
    return Path(git(["rev-parse", "--show-toplevel"], path).stdout.strip())


def head_commit(path: Path | str) -> str:
    return git(["rev-parse", "HEAD"], path).stdout.strip()


def current_branch(path: Path | str) -> str | None:
    completed = git(["symbolic-ref", "--quiet", "--short", "HEAD"], path, check=False)
    return completed.stdout.strip() or None


def is_dirty(path: Path | str) -> bool:
    return bool(git(["status", "--porcelain"], path).stdout.strip())


def _safe_component(value: str) -> str:
    return "".join(char if char.isalnum() or char in "-_." else "-" for char in value)[:64]


def _short_component(value: str, keep: int) -> str:
    """A path segment of at most ``keep`` + 5 characters that stays unique."""
    safe = _safe_component(value)
    if len(safe) <= keep:
        return safe
    return f"{safe[:keep].rstrip('-_.')}-{hashlib.sha1(value.encode('utf-8')).hexdigest()[:4]}"


# ``legacy`` keeps the original <root>/<run-id>/<node-id> layout for runs
# created before short paths; ``short`` bounds every directory segment.
LAYOUTS = ("legacy", "short")


class WorktreeManager:
    def __init__(self, repository: Path | str, root: Path | str, run_id: str, layout: str = "legacy") -> None:
        self.repository = Path(repository)
        self.layout = layout if layout in LAYOUTS else "legacy"
        if self.layout == "short":
            self.root = Path(root) / hashlib.sha1(run_id.encode("utf-8")).hexdigest()[:8]
        else:
            self.root = Path(root) / _safe_component(run_id)
        self.run_id = run_id

    def _node_dir(self, node_id: str) -> str:
        return _short_component(node_id, 16) if self.layout == "short" else _safe_component(node_id)

    # -- naming ------------------------------------------------------------

    def branch_for(self, node_id: str, generation: int = 0) -> str:
        suffix = f"-g{generation}" if generation else ""
        return f"agent-os/{_safe_component(self.run_id)}/{_safe_component(node_id)}{suffix}"

    def path_for(self, node_id: str, generation: int = 0) -> Path:
        suffix = f"-g{generation}" if generation else ""
        return self.root / f"{self._node_dir(node_id)}{suffix}"

    @property
    def integration_branch(self) -> str:
        return f"agent-os/{_safe_component(self.run_id)}/integration"

    @property
    def integration_path(self) -> Path:
        return self.root / ("_int" if self.layout == "short" else "_integration")

    # -- inventory -----------------------------------------------------------

    def registered(self) -> dict[str, str]:
        """Map of registered worktree path (casefolded) -> branch."""
        output = git(["worktree", "list", "--porcelain"], self.repository).stdout
        entries: dict[str, str] = {}
        current: str | None = None
        for line in output.splitlines():
            if line.startswith("worktree "):
                current = str(Path(line[len("worktree "):]).resolve()).casefold()
                entries[current] = ""
            elif line.startswith("branch ") and current:
                entries[current] = line[len("branch "):].removeprefix("refs/heads/")
        return entries

    def is_registered(self, path: Path | str) -> bool:
        return str(Path(path).resolve()).casefold() in self.registered()

    def branch_exists(self, branch: str) -> bool:
        return git(["rev-parse", "--verify", "--quiet", f"refs/heads/{branch}"], self.repository, check=False).returncode == 0

    # -- lifecycle -----------------------------------------------------------

    def _add(self, path: Path, branch: str, base: str) -> dict[str, Any]:
        path.parent.mkdir(parents=True, exist_ok=True)
        if self.is_registered(path):
            return {"path": str(path), "branch": branch, "base_commit": base, "reused": True}
        if path.exists() and any(path.iterdir()):
            raise GitError(f"refusing to reuse unregistered non-empty directory {path}")
        created_branch = not self.branch_exists(branch)
        try:
            if created_branch:
                git(["worktree", "add", "-b", branch, str(path), base], self.repository)
            else:
                git(["worktree", "add", str(path), branch], self.repository)
        except GitError:
            # A failed checkout leaves a half-written directory and, for a new
            # branch, an empty branch; remove both so a retry starts clean.
            git(["worktree", "prune"], self.repository, check=False)
            if path.exists() and not self.is_registered(path):
                shutil.rmtree(path, ignore_errors=True)
            if created_branch and self.branch_exists(branch):
                git(["branch", "-D", branch], self.repository, check=False)
            raise
        return {"path": str(path), "branch": branch, "base_commit": base, "reused": False}

    def ensure_integration(self, base_commit: str) -> dict[str, Any]:
        return self._add(self.integration_path, self.integration_branch, base_commit)

    def integration_head(self) -> str:
        return head_commit(self.integration_path)

    def create(self, node_id: str, base_commit: str, generation: int = 0) -> dict[str, Any]:
        return self._add(self.path_for(node_id, generation), self.branch_for(node_id, generation), base_commit)

    def checkpoint(self, path: Path | str, message: str) -> str | None:
        """Commit everything the worker left behind. Returns the new commit or None."""
        git(["add", "-A", "--", ".", *ARTIFACT_EXCLUDES], path)
        if not git(["diff", "--cached", "--name-only"], path).stdout.strip():
            return None
        git(["commit", "--no-verify", "-m", message[:200]], path, identity=True)
        return head_commit(path)

    def changed_files(self, path: Path | str, base_commit: str) -> list[str]:
        output = git(["diff", "--name-only", f"{base_commit}..HEAD"], path).stdout
        return sorted({line.strip() for line in output.splitlines() if line.strip()})

    def diff(self, path: Path | str, base_commit: str, limit: int = MAX_DIFF_CHARS) -> str:
        text = git(["diff", "--stat", "--patch", f"{base_commit}..HEAD"], path).stdout
        if len(text) > limit:
            return text[:limit] + f"\n... diff truncated at {limit} characters; inspect the branch directly ...\n"
        return text

    def merge(self, branch: str, message: str) -> dict[str, Any]:
        """Merge a validated branch into the integration worktree, or report a conflict."""
        before = self.integration_head()
        completed = git(["merge", "--no-ff", "--no-edit", "-m", message[:200], branch], self.integration_path, check=False, identity=True)
        if completed.returncode == 0:
            return {"merged": True, "before": before, "commit": self.integration_head(), "conflicts": []}
        conflicts = git(["diff", "--name-only", "--diff-filter=U"], self.integration_path, check=False).stdout.split()
        git(["merge", "--abort"], self.integration_path, check=False)
        if self.integration_head() != before:
            git(["reset", "--hard", before], self.integration_path)
        return {
            "merged": False,
            "before": before,
            "commit": before,
            "conflicts": sorted(conflicts),
            "detail": (completed.stdout + completed.stderr).strip()[-400:],
        }

    def remove(self, path: Path | str, branch: str | None, delete_merged_branch: bool = True) -> dict[str, Any]:
        """Remove an integrated worker's worktree; delete its branch only if merged."""
        removed = False
        if self.is_registered(path):
            completed = git(["worktree", "remove", str(path)], self.repository, check=False)
            if completed.returncode != 0:
                # Untracked build artifacts only: tracked changes were committed
                # by the checkpoint before integration.
                if not git(["status", "--porcelain", "--untracked-files=no"], path, check=False).stdout.strip():
                    git(["worktree", "remove", "--force", str(path)], self.repository, check=False)
            removed = not self.is_registered(path)
        elif Path(path).exists() and not any(Path(path).iterdir()):
            shutil.rmtree(path, ignore_errors=True)
        branch_deleted = False
        if branch and delete_merged_branch and self.branch_exists(branch):
            branch_deleted = git(["branch", "-d", branch], self.repository, check=False).returncode == 0
        return {"removed": removed, "branch_deleted": branch_deleted}

    def is_ancestor(self, ancestor: str, descendant: str) -> bool:
        return git(["merge-base", "--is-ancestor", ancestor, descendant], self.repository, check=False).returncode == 0
