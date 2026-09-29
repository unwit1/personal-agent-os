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
        # Fail closed: when the target cannot be resolved, apply the guard
        # (mutation testing showed the old False here disabled it; DEC-0012).
        return True


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


# -- negative evidence is append-only (policy control_plane.negative_evidence) --

RECORDS = "projects/personal-agent-os/orchestrator-os/records/"
FAILURES = RECORDS + "failures/"
OUTCOME_DIRS = (RECORDS + "experiments/", RECORDS + "evaluations/")
NEGATIVE_OUTCOMES = {"rejected", "inconclusive", "regressed"}
MUTABLE_FIELDS = {"status", "updated_at"}
# Counters that may grow (more occurrences add evidence) but never shrink.
MONOTONIC_FIELDS = {"recurrence"}


def _append_only(old: Any, new: Any, where: str) -> list[str]:
    """Differences that remove or rewrite existing content. New keys, longer
    text that keeps the old text as a prefix, and extra list items are fine."""
    if isinstance(old, dict):
        if not isinstance(new, dict):
            return [f"{where or 'record'} changed type"]
        problems = []
        for key, value in old.items():
            if key in MUTABLE_FIELDS and not where:
                continue
            if key not in new:
                problems.append(f"{where}{key} removed")
            elif key in MONOTONIC_FIELDS and not where and isinstance(value, (int, float)) and isinstance(new[key], (int, float)):
                if new[key] < value:
                    problems.append(f"{key} decreased")
            else:
                problems += _append_only(value, new[key], f"{where}{key}.")
        return problems
    if isinstance(old, list):
        if not isinstance(new, list):
            return [f"{where.rstrip('.')} changed type"]
        missing = [item for item in old if item not in new]
        return [f"{where.rstrip('.')} lost {len(missing)} item(s)"] if missing else []
    if isinstance(old, str) and isinstance(new, str):
        return [] if new.startswith(old) else [f"{where.rstrip('.')} rewritten (only appending is allowed)"]
    return [] if old == new else [f"{where.rstrip('.')} changed"]


def _base_json(repo: Path, base: str, path: str) -> Any:
    import subprocess

    completed = subprocess.run(["git", "show", f"{base}:{path}"], cwd=repo, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if completed.returncode != 0:
        return None
    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError:
        return None


def negative_evidence_changes(repo: Path | str, base: str, changed: Iterable[str], allowed: Iterable[str] = ()) -> list[str]:
    """Violations of the append-only rule for FAIL records and for EXP/EVR
    records whose outcome was negative at ``base``."""
    repo = Path(repo)
    grants = [str(item) for item in allowed or []]
    problems = []
    for path in changed:
        normalized = path.replace("\\", "/")
        if not normalized.endswith(".json") or any(_match(normalized, grant) for grant in grants):
            continue
        in_failures = normalized.startswith(FAILURES)
        if not in_failures and not normalized.startswith(OUTCOME_DIRS):
            continue
        old = _base_json(repo, base, normalized)
        if old is None:
            continue  # new record: adding evidence is always allowed
        if not in_failures and str((old or {}).get("outcome")) not in NEGATIVE_OUTCOMES:
            continue
        current = repo / normalized
        if not current.exists():
            problems.append(f"{normalized}: negative evidence deleted")
            continue
        try:
            new = json.loads(current.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            problems.append(f"{normalized}: negative evidence made unreadable")
            continue
        problems += [f"{normalized}: {item}" for item in _append_only(old, new, "")]
    return problems


def negative_evidence_check(repo: Path | str, base: str, changed: list[str], allowed: Iterable[str] = ()) -> dict[str, Any]:
    hits = negative_evidence_changes(repo, base, changed, allowed)
    return {"name": "negative-evidence", "kind": "scope", "passed": not hits,
            "detail": None if not hits else "negative evidence is append-only (supersede, never erase): " + "; ".join(hits[:5])}


# -- external publication requires approval (policy approval_required_for) --

PUBLISH_PATTERNS = (
    r"\bgit\s+push\b",
    r"\b(?:npm|pnpm|yarn)\s+publish\b",
    r"\btwine\s+upload\b",
    r"\bpoetry\s+publish\b",
    r"\bgh\s+(?:release\s+create|pr\s+create|repo\s+create|gist\s+create)\b",
    r"\bcurl\b[^\n]*(?:-X\s*(?:POST|PUT|PATCH)|--data\b|\s-d\s|--upload-file|-T\s)",
    r"\bInvoke-(?:WebRequest|RestMethod)\b[^\n]*-Method\s+(?:Post|Put|Patch)",
    r"\bdocker\s+push\b",
)
# Tool patterns for CLIs that support deny rules (Claude Code --disallowedTools).
DISALLOWED_PUBLISH_TOOLS = ("Bash(git push:*)", "Bash(npm publish:*)", "Bash(pnpm publish:*)", "Bash(yarn publish:*)", "Bash(twine upload:*)",
                            "Bash(poetry publish:*)", "Bash(gh release create:*)", "Bash(gh pr create:*)", "Bash(gh repo create:*)", "Bash(docker push:*)")


def _commands(text: str) -> list[str]:
    """Commands a worker actually executed: Codex --json command_execution
    items, or plain-log lines in shell-prompt form ("$ git push"). Prose in
    final messages ("I did not run git push") is never treated as a command;
    for CLIs without a command transcript the tool-level deny rule applies."""
    found = []
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("{"):
            if "command_execution" not in line:
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            item = event.get("item") if isinstance(event.get("item"), dict) else {}
            if item.get("type") == "command_execution" and item.get("command"):
                found.append(str(item["command"]))
        elif line.startswith(("$ ", "> ", "PS> ")):
            found.append(line.split(" ", 1)[1])
    return found


def publication_attempts(texts: Iterable[str]) -> list[str]:
    import re

    hits = []
    for text in texts:
        for command in _commands(text or ""):
            if any(re.search(pattern, command, re.IGNORECASE) for pattern in PUBLISH_PATTERNS):
                hits.append(command[:160])
    return hits


def publication_check(paths: Iterable[str | Path]) -> dict[str, Any]:
    """Fails when a worker transcript shows an attempted publishing command
    (push, package upload, outbound POST). Publication is an operator-gated
    action; a worker attempting it fails validation whatever its sandbox did."""
    texts = []
    for path in paths:
        try:
            texts.append(Path(path).read_text(encoding="utf-8", errors="replace"))
        except OSError:
            continue
    hits = publication_attempts(texts)
    return {"name": "publication-guard", "kind": "scope", "passed": not hits,
            "detail": None if not hits else "external publication requires operator approval; worker attempted: " + "; ".join(hits[:3])}
