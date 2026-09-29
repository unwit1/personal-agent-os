"""Trusted control/evaluation plane boundary (docs/orchestrator-os/CONSTITUTION.md §4).

Experimental candidates may *propose* changes to evaluators, policy,
authorization, holdouts or promotion thresholds; they may not land them on
their own. This module is the deterministic enforcement point: the validator
step of every orchestrated node that targets this repository fails when the
candidate's diff touches a protected path, unless the *operator* granted that
path in the run policy (``protected_paths_allowed``) when creating the run.
Planners cannot set run policy, and workers cannot edit the run record, so a
candidate cannot grant itself the exception.

The protected globs are read from the policy file in the trusted checkout that
is running Agent OS (``ROOT``), never from the candidate's worktree, so editing
the policy inside a worktree does not weaken the check. If the policy file is
missing or unreadable the built-in floor below still applies (fail closed).
"""

from __future__ import annotations

import fnmatch
import json
from pathlib import Path
from typing import Any, Iterable

from ..paths import ROOT

POLICY_PATH = ROOT / "policy" / "orchestrator-os.policy.json"
PROJECT_ID = "personal-agent-os"
# Minimum protection that survives a deleted or corrupted policy file.
FLOOR = (
    "policy/**",
    "src/agent_os/orchestrator/control_plane.py",
    "src/agent_os/orchestrator/validators.py",
    "projects/personal-agent-os/orchestrator-os/evals/holdout/**",
    "projects/personal-agent-os/orchestrator-os/evals/evaluators/**",
)


def load_policy(path: Path | None = None) -> dict[str, Any]:
    try:
        data = json.loads(Path(path or POLICY_PATH).read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def protected_globs(policy: dict[str, Any] | None = None) -> list[str]:
    policy = load_policy() if policy is None else policy
    declared = ((policy.get("control_plane") or {}).get("protected_paths")) or []
    return sorted(set(FLOOR) | {str(item) for item in declared if isinstance(item, str)})


def _match(path: str, pattern: str) -> bool:
    path = path.replace("\\", "/")
    while path.startswith("./"):
        path = path[2:]
    if pattern.endswith("/**"):
        prefix = pattern[:-3]
        return path == prefix or path.startswith(prefix + "/")
    return fnmatch.fnmatchcase(path, pattern)


def protected_changes(changed: Iterable[str], allowed: Iterable[str] = (), policy: dict[str, Any] | None = None) -> list[str]:
    globs = protected_globs(policy)
    grants = [str(item) for item in allowed or []]
    hits = []
    for path in changed:
        if any(_match(path, pattern) for pattern in globs) and not any(_match(path, grant) for grant in grants):
            hits.append(path)
    return hits


def applies_to(repository: str | Path | None, project: str | None) -> bool:
    if project == PROJECT_ID:
        return True
    try:
        return repository is not None and Path(repository).resolve() == ROOT.resolve()
    except OSError:
        return False


def check(changed: list[str], allowed: Iterable[str] = (), policy: dict[str, Any] | None = None) -> dict[str, Any]:
    """Validator evidence item. ``kind: scope`` keeps it out of the declared
    validator count and the validation cache, like the editable-scope check."""
    hits = protected_changes(changed, allowed, policy)
    return {
        "name": "control-plane",
        "kind": "scope",
        "passed": not hits,
        "detail": None if not hits else "candidate edits protected control/evaluation plane (operator grant required): " + ", ".join(hits[:10]),
    }
