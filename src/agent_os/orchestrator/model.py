"""Run, node, and policy vocabulary for orchestrated multi-agent runs.

Everything here is plain data so a run record can be persisted, diffed, and
resumed from disk. Nothing in this module names a provider or a model.
"""

from __future__ import annotations

import copy
import re
from typing import Any

from ..capabilities import CAPABILITY_CLASSES, EFFORTS, next_class
from ..timestamps import utc_now_iso as now


RUN_SCHEMA = "personal-agent/orchestrated-run/v1"

RUN_STATES = (
    "CREATED",
    "PLANNING",
    "READY",
    "RUNNING",
    "VALIDATING",
    "REVIEWING",
    "INTEGRATING",
    "APPROVAL_REQUIRED",
    "PAUSED",
    "BLOCKED",
    "FAILED",
    "COMPLETE",
)

NODE_STATES = (
    "PENDING",
    "RUNNABLE",
    "CLAIMED",
    "LAUNCHING",
    "RUNNING",
    "WAITING_FOR_RESULT",
    "VALIDATING",
    "NEEDS_REPAIR",
    "WAITING_FOR_REVIEW",
    "APPROVAL_REQUIRED",
    "PASSED",
    "FAILED_RETRYABLE",
    "FAILED_FINAL",
    "CANCELLED",
)

# Auto Continue keeps driving until the run reaches one of these.
STOP_STATES = frozenset({"COMPLETE", "PAUSED", "APPROVAL_REQUIRED", "BLOCKED", "FAILED"})
ACTIVE_NODE_STATES = frozenset({"CLAIMED", "LAUNCHING", "RUNNING", "WAITING_FOR_RESULT", "VALIDATING"})
DISPATCHABLE_NODE_STATES = frozenset({"PENDING", "RUNNABLE", "FAILED_RETRYABLE"})
FINISHED_NODE_STATES = frozenset({"PASSED", "FAILED_FINAL", "CANCELLED"})

ROLES = ("planner", "implementer", "test_author", "reviewer", "repairer")
EDITING_ROLES = frozenset({"implementer", "test_author", "repairer"})
# Roles whose output is integrated into the run's integration branch.
INTEGRATED_ROLES = frozenset({"implementer", "test_author"})

EXECUTION_PATHS = ("deterministic", "model")

APPROVAL_GATES = (
    "destructive_action",
    "credential_or_secret_entry",
    "consequential_external_write",
    "semantic_merge_conflict",
    "budget_exhausted",
    "policy_restricted_action",
    "unresolved_review_findings",
    "agent_needs_decision",
    "consequential_repository_write",
)

SEVERITIES = ("critical", "high", "medium", "low", "info")
DISPOSITIONS = ("open", "accepted", "rejected", "fixed")

FAILURE_KINDS = (
    "process_error",
    "quota",
    "unavailable",
    "invalid_model",
    "timeout",
    "malformed",
    "cancelled",
    "interrupted",
    "validator_failed",
    "merge_conflict",
)
# Failures that say something about the provider, not about the work: the
# unfinished node may move to another configured provider.
PROVIDER_FAILURES = frozenset({"quota", "unavailable", "invalid_model"})

PREFERENCES = ("economy", "balanced", "quality")
PLANNING_MODES = ("auto", "single", "explicit")
FINAL_INTEGRATION_MODES = ("branch", "merge_to_base")

# Commands a planner (a model) may propose as a validator or a deterministic
# step. Anything else must come from the caller or the project's canonical
# validation_commands. Matched against the whole command; shell metacharacters
# are never allowed, and matching commands run without a shell.
DEFAULT_APPROVED_COMMANDS = [
    r"python -m unittest( [A-Za-z0-9_./-]+)*( -v)?",
    r"python -m pytest( [A-Za-z0-9_./:\[\]-]+)*( -q| -x)*",
    r"python agent\.py validate",
]

DEFAULT_POLICY: dict[str, Any] = {
    "auto_continue": False,
    "max_parallel_editors": 6,
    "require_isolated_worktrees": True,
    "require_independent_review_for_model_edits": True,
    "require_distinct_review_provider": True,
    "validation_required_before_integration": True,
    "provider_failover": True,
    "max_stage_retries": 2,
    "max_escalations": 2,
    "max_review_rounds": 2,
    "max_final_repairs": 1,
    "material_severities": ["critical", "high", "medium"],
    "approval_gates": list(APPROVAL_GATES),
    "preference": "balanced",
    "planning": "auto",
    "max_planned_tasks": 16,
    "planner_capability_class": "balanced",
    "planner_effort": "high",
    "approved_commands": list(DEFAULT_APPROVED_COMMANDS),
    "final_integration": "branch",
    "max_launches": 40,
    "poll_interval_seconds": 2.0,
    "worker_timeout_seconds": 3600,
    "default_validators": [],
    "completion_validators": [],
    "announce_claims": True,
    "telemetry": True,
    "cleanup_worktrees": True,
}

_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$")


class PolicyError(ValueError):
    pass


class PlanError(ValueError):
    pass


def check_identifier(value: Any, label: str) -> str:
    text = str(value or "")
    if not _ID.match(text):
        raise PlanError(f"{label} must match {_ID.pattern}: {text!r}")
    return text


def merge_policy(overrides: dict[str, Any] | None = None, base: dict[str, Any] | None = None) -> dict[str, Any]:
    """Apply overrides to the default policy, rejecting unknown or invalid keys."""
    policy = copy.deepcopy(base if base is not None else DEFAULT_POLICY)
    for key, value in (overrides or {}).items():
        if key not in DEFAULT_POLICY:
            raise PolicyError(f"unknown run policy key: {key}")
        policy[key] = copy.deepcopy(value)
    _check_policy(policy)
    return policy


def _check_policy(policy: dict[str, Any]) -> None:
    for key in (
        "auto_continue",
        "require_isolated_worktrees",
        "require_independent_review_for_model_edits",
        "require_distinct_review_provider",
        "validation_required_before_integration",
        "provider_failover",
        "announce_claims",
        "telemetry",
        "cleanup_worktrees",
    ):
        if not isinstance(policy[key], bool):
            raise PolicyError(f"{key} must be boolean")
    for key in (
        "max_parallel_editors",
        "max_stage_retries",
        "max_escalations",
        "max_review_rounds",
        "max_final_repairs",
        "max_planned_tasks",
        "max_launches",
        "worker_timeout_seconds",
    ):
        if not isinstance(policy[key], int) or isinstance(policy[key], bool) or policy[key] < 0:
            raise PolicyError(f"{key} must be a non-negative integer")
    if policy["max_parallel_editors"] < 1:
        raise PolicyError("max_parallel_editors must be at least 1")
    if not policy["require_isolated_worktrees"]:
        # Concurrent editors sharing a writable tree is exactly what this
        # orchestrator exists to prevent; the flag is informational only.
        raise PolicyError("require_isolated_worktrees cannot be disabled")
    if not isinstance(policy["poll_interval_seconds"], (int, float)) or policy["poll_interval_seconds"] < 0:
        raise PolicyError("poll_interval_seconds must be a non-negative number")
    if policy["preference"] not in PREFERENCES:
        raise PolicyError(f"preference must be one of {PREFERENCES}")
    if policy["planning"] not in PLANNING_MODES:
        raise PolicyError(f"planning must be one of {PLANNING_MODES}")
    if policy["final_integration"] not in FINAL_INTEGRATION_MODES:
        raise PolicyError(f"final_integration must be one of {FINAL_INTEGRATION_MODES}")
    if policy["planner_capability_class"] not in CAPABILITY_CLASSES or policy["planner_capability_class"] == "deterministic":
        raise PolicyError("planner_capability_class must be a model capability class")
    if policy["planner_effort"] not in EFFORTS:
        raise PolicyError(f"planner_effort must be one of {EFFORTS}")
    approved = policy["approved_commands"]
    if not isinstance(approved, list) or any(not isinstance(item, str) for item in approved):
        raise PolicyError("approved_commands must be a list of regular expressions")
    for pattern in approved:
        try:
            re.compile(pattern)
        except re.error as exc:
            raise PolicyError(f"approved_commands: invalid pattern {pattern!r}: {exc}") from exc
    severities = policy["material_severities"]
    if not isinstance(severities, list) or any(item not in SEVERITIES for item in severities):
        raise PolicyError("material_severities must list known severities")
    gates = policy["approval_gates"]
    if not isinstance(gates, list) or any(item not in APPROVAL_GATES for item in gates):
        raise PolicyError("approval_gates must list known gate kinds")
    for key in ("default_validators", "completion_validators"):
        for validator in policy[key]:
            validator_problems(validator, key)


def validator_problems(validator: Any, label: str) -> None:
    if not isinstance(validator, dict):
        raise PolicyError(f"{label}: validator must be an object")
    kind = validator.get("kind")
    if kind == "command":
        command = validator.get("command")
        if not command or not isinstance(command, (list, str)):
            raise PolicyError(f"{label}: command validator needs a command")
    elif kind == "outputs_present":
        if not isinstance(validator.get("outputs"), list) or not validator["outputs"]:
            raise PolicyError(f"{label}: outputs_present validator needs outputs")
    elif kind != "none":
        raise PolicyError(f"{label}: unsupported validator kind {kind!r}")


def new_node(
    node_id: str,
    goal: str,
    role: str,
    *,
    depends_on: list[str] | None = None,
    scope: list[str] | None = None,
    capability_class: str = "balanced",
    effort: str = "medium",
    execution_path: str = "model",
    command: list[str] | str | None = None,
    validators: list[dict[str, Any]] | None = None,
    approval_gate: dict[str, Any] | None = None,
    review_required: bool | None = None,
    expected_outputs: list[str] | None = None,
    context_budget: int = 1200,
    subject: str | None = None,
    origin: str = "plan",
    ladder: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    check_identifier(node_id, "node id")
    if not str(goal or "").strip():
        raise PlanError(f"node {node_id}: missing goal")
    if role not in ROLES:
        raise PlanError(f"node {node_id}: unsupported role {role!r}")
    if capability_class not in CAPABILITY_CLASSES:
        raise PlanError(f"node {node_id}: unsupported capability_class {capability_class!r}")
    if effort not in EFFORTS:
        raise PlanError(f"node {node_id}: unsupported effort {effort!r}")
    if execution_path not in EXECUTION_PATHS:
        raise PlanError(f"node {node_id}: unsupported execution_path {execution_path!r}")
    if execution_path == "deterministic" and not command:
        raise PlanError(f"node {node_id}: a deterministic node needs a command")
    if capability_class == "deterministic" and execution_path != "deterministic":
        raise PlanError(f"node {node_id}: deterministic capability requires the deterministic execution path")
    for validator in validators or []:
        try:
            validator_problems(validator, f"node {node_id}")
        except PolicyError as exc:
            raise PlanError(str(exc)) from exc
    if approval_gate is not None:
        if not isinstance(approval_gate, dict) or approval_gate.get("kind") not in APPROVAL_GATES:
            raise PlanError(f"node {node_id}: approval_gate.kind must be one of {APPROVAL_GATES}")
    if not isinstance(context_budget, int) or context_budget < 250:
        raise PlanError(f"node {node_id}: context_budget must be an integer >= 250")
    rungs = check_ladder(node_id, ladder, capability_class, effort) if ladder else default_ladder(capability_class, effort, execution_path)
    stamp = now()
    return {
        "id": node_id,
        "goal": str(goal).strip()[:2000],
        "role": role,
        "origin": origin,
        "subject": subject,
        "depends_on": list(dict.fromkeys(depends_on or [])),
        "scope": normalize_scope(scope),
        "context_budget": context_budget,
        "capability_class": capability_class,
        "requested_capability_class": capability_class,
        "effort": effort,
        "requested_effort": effort,
        "ladder": rungs,
        "ladder_step": 0,
        "execution_path": execution_path,
        "command": command,
        "validators": list(validators or []),
        "approval_gate": approval_gate,
        "approval": None,
        "review_required": review_required,
        "expected_outputs": list(expected_outputs or []),
        "state": "PENDING",
        "wait_reason": None,
        "attempts": 0,
        "retries": 0,
        "escalations": 0,
        "failures": [],
        "excluded_providers": [],
        "selection": None,
        "worktree": None,
        "checkpoint": None,
        "process": None,
        "result": None,
        "validation": None,
        "review": {"rounds": 0, "findings": [], "reviewers": [], "accepted_by_user": False},
        "integrated": False,
        "integration": None,
        "claim_id": None,
        "created_at": stamp,
        "updated_at": stamp,
        "completed_at": None,
    }


def default_ladder(capability_class: str, effort: str, execution_path: str = "model") -> list[dict[str, str]]:
    """Cheapest-first escalation plan: more effort on the same model before a
    stronger model, then one class at a time."""
    if execution_path != "model" or capability_class == "deterministic":
        return []
    rungs = [{"capability_class": capability_class, "effort": effort}]
    if capability_class in {"fast", "balanced"} and effort in {"none", "low", "medium"}:
        rungs.append({"capability_class": capability_class, "effort": "high"})
    current = capability_class
    while True:
        promoted = next_class(current)
        if promoted is None:
            break
        rungs.append({"capability_class": promoted, "effort": "high" if promoted == "frontier" else "medium"})
        current = promoted
    return rungs


def check_ladder(node_id: str, ladder: Any, capability_class: str, effort: str) -> list[dict[str, str]]:
    """Validate a planned ladder. Its first rung is the node's own class/effort."""
    if not isinstance(ladder, list) or not ladder:
        raise PlanError(f"node {node_id}: ladder must be a non-empty list")
    rungs = []
    for rung in ladder[:6]:
        if not isinstance(rung, dict):
            raise PlanError(f"node {node_id}: each ladder rung must be an object")
        rung_class = rung.get("capability_class")
        rung_effort = rung.get("effort", "medium")
        if rung_class not in CAPABILITY_CLASSES or rung_class == "deterministic":
            raise PlanError(f"node {node_id}: ladder capability_class {rung_class!r} is not a model class")
        if rung_effort not in EFFORTS:
            raise PlanError(f"node {node_id}: ladder effort {rung_effort!r} is unsupported")
        rungs.append({"capability_class": rung_class, "effort": rung_effort})
    if rungs[0] != {"capability_class": capability_class, "effort": effort}:
        rungs.insert(0, {"capability_class": capability_class, "effort": effort})
    return rungs


def normalize_scope(scope: list[str] | None) -> list[str]:
    """Repository-relative, forward-slash, no trailing slash. Empty = whole repo."""
    cleaned: list[str] = []
    for item in scope or []:
        text = str(item).strip().replace("\\", "/").strip("/")
        if text.startswith("./"):
            text = text[2:]
        if not text or text == ".":
            return []
        if ".." in text.split("/"):
            raise PlanError(f"scope must stay inside the repository: {item!r}")
        cleaned.append(text)
    return list(dict.fromkeys(cleaned))


def scopes_overlap(first: list[str], second: list[str]) -> bool:
    """Two editable scopes overlap when either is the whole repository or one
    path is a prefix (by path segment) of the other."""
    if not first or not second:
        return True
    for left in first:
        for right in second:
            a, b = left.casefold(), right.casefold()
            if a == b or a.startswith(b + "/") or b.startswith(a + "/"):
                return True
    return False


def path_in_scope(path: str, scope: list[str]) -> bool:
    if not scope:
        return True
    candidate = path.replace("\\", "/").strip("/").casefold()
    for item in scope:
        prefix = item.casefold()
        if candidate == prefix or candidate.startswith(prefix + "/"):
            return True
    return False
