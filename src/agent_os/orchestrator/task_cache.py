"""Task cache route for P0.5 deterministic execution policy.

Implements docs/orchestrator-os/task-cache-route.md: a reviewed, integrated
patch from an earlier run may replace a worker (and its review) for an
identical node, but only after the patch is re-proven on the current tree.
"""

from __future__ import annotations

import hashlib
import json
import tempfile
from pathlib import Path

TASK_CACHE_POLICY_VERSION = 1


def normalize_goal(goal: str) -> str:
    """Strip goal and collapse whitespace runs to single spaces."""
    goal = goal.strip()
    goal = " ".join(goal.split())
    return goal


def task_cache_key(
    goal: str, scope: list[str], base_files: dict[str, str | None], validators: list, role: str
) -> str:
    """Compute the task cache key as lowercase hex sha256 of canonical JSON.

    Args:
        goal: node goal (will be normalized)
        scope: sorted list of node scope paths
        base_files: mapping of scope paths to git object ids (or null if absent)
        validators: list of validator commands in declared order
        role: node role

    Returns:
        lowercase hex sha256 of the canonical JSON representation
    """
    obj = {
        "policy_version": TASK_CACHE_POLICY_VERSION,
        "goal": normalize_goal(goal),
        "scope": sorted(scope),
        "base_files": dict(sorted(base_files.items())),
        "validators": validators,
        "role": role,
    }

    json_str = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    json_bytes = json_str.encode("utf-8")
    return hashlib.sha256(json_bytes).hexdigest()


def eligible_for_record(node: dict, review: dict | None, patch_paths: list[str]) -> bool:
    """Check if a node is eligible to be recorded in the task cache.

    A node is eligible only when all of:
    - role is 'implementer' or 'test_author'
    - execution_path is 'model'
    - review verdict is 'approved' with no open material findings
    - patch_paths is non-empty
    - every patch path is in node['scope']

    Args:
        node: orchestrator node dict with 'role', 'execution_path', 'scope'
        review: review dict with 'verdict' and 'findings', or None
        patch_paths: list of paths that were changed

    Returns:
        True if eligible to record, False otherwise
    """
    if node.get("role") not in ("implementer", "test_author"):
        return False

    if node.get("execution_path") != "model":
        return False

    if review is None:
        return False

    if review.get("verdict") != "approved":
        return False

    if not patch_paths:
        return False

    scope = node.get("scope", [])
    for patch_path in patch_paths:
        if patch_path not in scope:
            return False

    findings = review.get("findings", [])
    for finding in findings:
        if finding.get("severity") == "material" and finding.get("state") != "resolved":
            return False

    return True


class TaskCacheStore:
    """Storage for task cache entries in a local directory.

    Entries are stored as JSON files at <root>/<key>.json, written atomically
    via a temp file and os.replace.
    """

    def __init__(self, root: Path) -> None:
        """Initialize the task cache store.

        Args:
            root: Path to the directory where cache files will be stored
        """
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def lookup(self, key: str) -> dict | None:
        """Look up a cache entry by key.

        Returns the entry dict if found and valid, None if missing, corrupt,
        or has a mismatched policy_version.

        Args:
            key: The cache key (hex sha256)

        Returns:
            The cache entry dict, or None if not found or invalid
        """
        path = self.root / f"{key}.json"

        if not path.exists():
            return None

        try:
            entry = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None

        if entry.get("policy_version") != TASK_CACHE_POLICY_VERSION:
            return None

        return entry

    def record(self, key: str, patch: str, evidence: list[dict], meta: dict) -> Path:
        """Record a cache entry atomically.

        Writes the entry to a temp file in the same directory, then uses
        os.replace to atomically move it to the final location. Does not
        overwrite an existing entry for the same key.

        Args:
            key: The cache key (hex sha256)
            patch: Unified diff patch text
            evidence: List of validator evidence dicts
            meta: Metadata dict (run_id, node_id, created_at, etc.)

        Returns:
            Path to the written file
        """
        path = self.root / f"{key}.json"

        if path.exists():
            return path

        entry = {
            "schema": "personal-agent/orchestrator-task-cache/v1",
            "policy_version": TASK_CACHE_POLICY_VERSION,
            "key": key,
            "patch": patch,
            "validator_evidence": evidence,
            "metadata": meta,
        }

        json_str = json.dumps(entry, ensure_ascii=False)

        with tempfile.NamedTemporaryFile(
            mode="w", dir=self.root, delete=False, suffix=".tmp", encoding="utf-8"
        ) as tmp:
            tmp.write(json_str)
            tmp_path = tmp.name

        tmp_path_obj = Path(tmp_path)
        tmp_path_obj.replace(path)

        return path
