"""Staged workflow orchestration.

Complex work is decomposed into stages so that a single expensive session does
not carry an entire job. Each stage declares the cheapest capability class that
could satisfy it, compiles its own context, and stops at a configured boundary
with a compact completion packet and an exact next prompt. Interrupted work
resumes from persisted stage state rather than from conversation memory.

Two execution modes share one lifecycle:

- deterministic stages run here and now, locally, with no model involved;
- every other stage is *prepared* -- context compiled, prompt generated,
  capability recommended -- and then handed to whatever agent is running, which
  reports the outcome back through `complete_stage`.

Escalation is evidence-driven: a stage moves up the capability ladder only
after its validator actually fails, and a stage that already succeeded is never
re-run at a higher class without an explicitly recorded reason.
"""

from __future__ import annotations

import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .capabilities import (
    CAPABILITY_CLASSES,
    EFFORTS,
    EXECUTION_PATHS,
    next_class,
    resolve as resolve_capability,
    select_execution_path,
)
from .compiler import compile_context
from .paths import ROOT
from .registry import get_project
from .storage import load_json, write_json


MANIFEST_SCHEMA = "personal-agent/workflow-manifest/v1"
WORKFLOW_DIR = ROOT / "workflows"
RUN_SCHEMA_VERSION = 1

STAGE_STATUSES = ("pending", "awaiting_agent", "complete", "failed", "blocked")
RUN_STATUSES = ("in_progress", "complete", "blocked")

# A run record holds stage outcomes and pointers, never conversation text. This
# is asserted by tests: carrying a transcript forward is the cost the staged
# orchestrator exists to avoid.
FORBIDDEN_RUN_KEYS = {"transcript", "messages", "history", "conversation"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# --------------------------------------------------------------------------
# Manifests
# --------------------------------------------------------------------------


def manifest_path(workflow_id: str) -> Path:
    return WORKFLOW_DIR / f"{workflow_id}.json"


def list_workflows() -> list[dict[str, Any]]:
    if not WORKFLOW_DIR.exists():
        return []
    items = []
    for path in sorted(WORKFLOW_DIR.glob("*.json")):
        try:
            manifest = load_json(path)
        except (OSError, json.JSONDecodeError):
            continue
        items.append(
            {
                "workflow_id": manifest.get("workflow_id"),
                "project": manifest.get("project"),
                "goal": manifest.get("goal"),
                "stages": [stage.get("stage_id") for stage in manifest.get("stages", [])],
            }
        )
    return items


def manifest_problems(manifest: Any) -> list[str]:
    """Deterministic structural validation, reused by `agent.py validate`."""
    problems: list[str] = []
    if not isinstance(manifest, dict):
        return ["manifest is not an object"]
    if manifest.get("schema") != MANIFEST_SCHEMA:
        problems.append("unsupported manifest schema")
    version = manifest.get("version")
    if not isinstance(version, int) or version < 1:
        problems.append("missing or invalid version")
    for key in ("workflow_id", "project", "goal"):
        if not str(manifest.get(key, "")).strip():
            problems.append(f"missing {key}")
    stages = manifest.get("stages")
    if not isinstance(stages, list) or not stages:
        problems.append("manifest declares no stages")
        return problems

    seen: set[str] = set()
    ids = [stage.get("stage_id") for stage in stages if isinstance(stage, dict)]
    for index, stage in enumerate(stages):
        if not isinstance(stage, dict):
            problems.append(f"stage[{index}]: not an object")
            continue
        stage_id = stage.get("stage_id", "")
        label = f"stage {stage_id or index}"
        if not stage_id:
            problems.append(f"{label}: missing stage_id")
        elif stage_id in seen:
            problems.append(f"{label}: duplicate stage_id")
        seen.add(stage_id)
        for key in ("goal", "stop_condition"):
            if not str(stage.get(key, "")).strip():
                problems.append(f"{label}: missing {key}")
        if not stage.get("expected_outputs"):
            problems.append(f"{label}: missing expected_outputs")
        if stage.get("capability_class") not in CAPABILITY_CLASSES:
            problems.append(f"{label}: unsupported capability_class")
        if stage.get("preferred_execution_path") not in EXECUTION_PATHS:
            problems.append(f"{label}: unsupported preferred_execution_path")
        available_paths = stage.get("available_execution_paths")
        if available_paths is not None:
            if not isinstance(available_paths, list) or not available_paths:
                problems.append(f"{label}: available_execution_paths must be a non-empty list")
            elif len(set(available_paths)) != len(available_paths):
                problems.append(f"{label}: available_execution_paths must be unique")
            else:
                invalid_paths = [path for path in available_paths if path not in EXECUTION_PATHS]
                if invalid_paths:
                    problems.append(f"{label}: unsupported available_execution_path {invalid_paths[0]}")
        if stage.get("effort", "low") not in EFFORTS:
            problems.append(f"{label}: unsupported effort")
        context = stage.get("required_context")
        if not isinstance(context, dict) or not str(context.get("task", "")).strip():
            problems.append(f"{label}: missing required_context.task")
        else:
            budget = context.get("token_budget")
            if not isinstance(budget, int) or budget < 250:
                problems.append(f"{label}: required_context.token_budget must be an integer >= 250")
        validator = stage.get("validator")
        if not isinstance(validator, dict) or validator.get("kind") not in {"command", "outputs_present", "none"}:
            problems.append(f"{label}: unsupported validator")
        elif validator["kind"] == "command" and not validator.get("command"):
            problems.append(f"{label}: command validator declares no command")
        # A deterministic stage that cannot be checked deterministically would
        # silently become an unverified model stage.
        if stage.get("capability_class") == "deterministic":
            if isinstance(validator, dict) and validator.get("kind") == "none":
                problems.append(f"{label}: a deterministic stage needs a validator")
        following = stage.get("next_stage")
        if following and following not in ids:
            problems.append(f"{label}: next_stage points at unknown stage {following}")
    return problems


def load_manifest(workflow_id: str) -> dict[str, Any]:
    path = manifest_path(workflow_id)
    if not path.exists():
        raise KeyError(f"unknown workflow: {workflow_id}")
    manifest = load_json(path)
    problems = manifest_problems(manifest)
    if problems:
        raise ValueError(f"invalid workflow manifest {workflow_id}: " + "; ".join(problems))
    return manifest


def stages_of(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    return list(manifest.get("stages", []))


def stage_of(manifest: dict[str, Any], stage_id: str) -> dict[str, Any]:
    for stage in stages_of(manifest):
        if stage.get("stage_id") == stage_id:
            return stage
    raise KeyError(f"unknown stage: {stage_id}")


def ordered_stage_ids(manifest: dict[str, Any]) -> list[str]:
    """Follow explicit next_stage links, falling back to declaration order.

    An explicit chain is authoritative; declaration order covers the common
    linear manifest that does not bother to link every stage.
    """
    stages = stages_of(manifest)
    if not stages:
        return []
    by_id = {stage["stage_id"]: stage for stage in stages}
    order: list[str] = []
    current = stages[0]["stage_id"]
    while current and current not in order:
        order.append(current)
        current = by_id.get(current, {}).get("next_stage")
    for stage in stages:
        if stage["stage_id"] not in order:
            order.append(stage["stage_id"])
    return order


# --------------------------------------------------------------------------
# Run state
# --------------------------------------------------------------------------


def runs_dir(project_id: str) -> Path:
    return ROOT / "projects" / project_id / "workflows"


def run_path(project_id: str, run_id: str) -> Path:
    return runs_dir(project_id) / f"{run_id}.json"


def _new_run(manifest: dict[str, Any], run_id: str) -> dict[str, Any]:
    return {
        "schema_version": RUN_SCHEMA_VERSION,
        "run_id": run_id,
        "workflow_id": manifest["workflow_id"],
        "project": manifest["project"],
        "goal": manifest["goal"],
        "status": "in_progress",
        "created_at": _now(),
        "updated_at": _now(),
        "max_escalations": int(manifest.get("max_escalations", 1)),
        "stages": {
            stage_id: {
                "status": "pending",
                "attempts": 0,
                "escalations": 0,
                "capability_class": stage_of(manifest, stage_id)["capability_class"],
                "execution_path": _stage_execution_path(stage_of(manifest, stage_id)),
                "outputs": [],
                "checkpoint": None,
                "validation": None,
                "escalation_reason": None,
                "completed_at": None,
            }
            for stage_id in ordered_stage_ids(manifest)
        },
    }


def _stage_execution_path(stage: dict[str, Any]) -> str:
    return select_execution_path(stage["preferred_execution_path"], stage.get("available_execution_paths"))


def start(workflow_id: str, run_id: str | None = None, resume: bool = True) -> dict[str, Any]:
    """Begin a run, or return the existing one so restarts are idempotent."""
    manifest = load_manifest(workflow_id)
    project_id = get_project(manifest["project"])["id"]
    identifier = run_id or f"{workflow_id}-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    path = run_path(project_id, identifier)
    if path.exists():
        if not resume:
            raise ValueError(f"run already exists: {identifier}")
        return load_json(path)
    record = _new_run(manifest, identifier)
    write_json(path, record)
    return record


def load_run(project_id: str, run_id: str) -> dict[str, Any]:
    path = run_path(get_project(project_id)["id"], run_id)
    if not path.exists():
        raise KeyError(f"unknown run: {run_id}")
    return load_json(path)


def _save(record: dict[str, Any]) -> dict[str, Any]:
    record["updated_at"] = _now()
    unexpected = FORBIDDEN_RUN_KEYS.intersection(record)
    if unexpected:
        raise ValueError("run state must not carry conversation context: " + ", ".join(sorted(unexpected)))
    write_json(run_path(record["project"], record["run_id"]), record)
    return record


def list_runs(project_id: str) -> list[dict[str, Any]]:
    directory = runs_dir(get_project(project_id)["id"])
    if not directory.exists():
        return []
    items = []
    for path in sorted(directory.glob("*.json")):
        try:
            record = load_json(path)
        except (OSError, json.JSONDecodeError):
            continue
        items.append(
            {
                "run_id": record.get("run_id"),
                "workflow_id": record.get("workflow_id"),
                "status": record.get("status"),
                "updated_at": record.get("updated_at"),
            }
        )
    return items


# --------------------------------------------------------------------------
# Stage selection
# --------------------------------------------------------------------------


def next_stage_id(manifest: dict[str, Any], record: dict[str, Any]) -> str | None:
    """The first stage in order that is not finished.

    A failed stage is returned again so it can be retried or escalated; a
    blocked stage stops the run rather than silently skipping work.
    """
    for stage_id in ordered_stage_ids(manifest):
        state = record["stages"].get(stage_id, {})
        if state.get("status") == "blocked":
            return None
        if state.get("status") != "complete":
            return stage_id
    return None


def _validate_stage(stage: dict[str, Any], state: dict[str, Any], cwd: Path) -> dict[str, Any]:
    """Run the stage's declared validator and report evidence, never a guess."""
    validator = stage.get("validator") or {"kind": "none"}
    kind = validator.get("kind")
    if kind == "command":
        command = [str(item) for item in validator.get("command", [])]
        try:
            completed = subprocess.run(
                command,
                cwd=str(cwd),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=(stage.get("limits") or {}).get("max_seconds", 900),
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            return {"kind": "command", "passed": False, "detail": f"validator could not run: {error}"}
        tail = (completed.stdout or completed.stderr or "").strip().splitlines()[-3:]
        return {
            "kind": "command",
            "passed": completed.returncode == 0,
            "returncode": completed.returncode,
            "detail": " | ".join(tail)[:400] or None,
        }
    if kind == "outputs_present":
        missing = [item for item in stage.get("expected_outputs", []) if item not in (state.get("outputs") or [])]
        return {
            "kind": "outputs_present",
            "passed": not missing,
            "detail": None if not missing else "missing outputs: " + ", ".join(missing),
        }
    return {"kind": "none", "passed": True, "detail": "stage declares no validator"}


# --------------------------------------------------------------------------
# Prompts and completion packets
# --------------------------------------------------------------------------


def build_prompt(manifest: dict[str, Any], stage: dict[str, Any], record: dict[str, Any]) -> str:
    """Generate the next prompt from persisted state, never from chat memory."""
    template = stage.get("next_prompt")
    if template:
        return (
            template.replace("{workflow_id}", manifest["workflow_id"])
            .replace("{run_id}", record["run_id"])
            .replace("{project}", manifest["project"])
            .replace("{stage_id}", stage["stage_id"])
        )
    context = stage.get("required_context", {})
    lines = [
        f"Continue workflow `{manifest['workflow_id']}` (run `{record['run_id']}`) on project `{manifest['project']}`.",
        "",
        f"Stage: {stage['stage_id']}",
        f"Goal: {stage['goal']}",
        "",
        "Compile this stage's own context first, and do not carry any earlier transcript:",
        "",
        f"    python agent.py workflow-stage {manifest['workflow_id']} --run-id {record['run_id']}",
        "",
        f"Work only within this stage. Stop when: {stage['stop_condition']}",
        "",
        "Expected outputs:",
    ]
    lines.extend(f"- {item}" for item in stage.get("expected_outputs", []))
    if stage.get("allowed_tools"):
        lines.extend(["", "Allowed tools: " + ", ".join(stage["allowed_tools"])])
    validator = stage.get("validator") or {}
    if validator.get("kind") == "command":
        lines.extend(["", "Validate with: " + " ".join(str(item) for item in validator.get("command", []))])
    lines.extend(
        [
            "",
            "When the stage is done, record the outcome so the next agent can resume:",
            "",
            f"    python agent.py workflow-complete {manifest['workflow_id']} --run-id {record['run_id']} "
            f"--stage {stage['stage_id']} --output \"<what you produced>\"",
        ]
    )
    return "\n".join(lines)


def prepare_stage(workflow_id: str, run_id: str, stage_id: str | None = None) -> dict[str, Any]:
    """Compile one stage's own context and return a ready-to-run packet.

    The packet is self-contained: it carries the stage contract, a freshly
    compiled context packet inside the stage's own token budget, the recommended
    capability class resolved against configured providers, and the exact next
    prompt. It deliberately carries nothing from any previous stage's reasoning.
    """
    manifest = load_manifest(workflow_id)
    record = load_run(manifest["project"], run_id)
    target = stage_id or next_stage_id(manifest, record)
    if target is None:
        return {
            "workflow_id": workflow_id,
            "run_id": run_id,
            "stage": None,
            "status": record["status"],
            "message": "no runnable stage remains",
        }
    stage = stage_of(manifest, target)
    state = record["stages"][target]
    required = stage.get("required_context", {})
    packet = compile_context(
        manifest["project"],
        required.get("task", stage["goal"]),
        token_budget=int(required.get("token_budget", 900)),
        include_handoff=bool(required.get("include_handoff", True)),
    )
    capability = state.get("capability_class", stage["capability_class"])
    execution_path = state.get("execution_path") or _stage_execution_path(stage)
    state["execution_path"] = execution_path
    return {
        "workflow_id": workflow_id,
        "run_id": run_id,
        "project": manifest["project"],
        "stage": {
            "stage_id": target,
            "goal": stage["goal"],
            "inputs": stage.get("inputs", []),
            "artifacts": stage.get("artifacts", []),
            "preferred_execution_path": stage["preferred_execution_path"],
            "available_execution_paths": stage.get("available_execution_paths", [stage["preferred_execution_path"]]),
            "execution_path": execution_path,
            "capability_class": capability,
            "effort": stage.get("effort", "low"),
            "allowed_tools": stage.get("allowed_tools", []),
            "limits": stage.get("limits", {}),
            "validator": stage.get("validator", {"kind": "none"}),
            "stop_condition": stage["stop_condition"],
            "expected_outputs": stage.get("expected_outputs", []),
            "checkpoint": stage.get("checkpoint"),
            "next_stage": stage.get("next_stage"),
        },
        "state": {
            "status": state["status"],
            "attempts": state["attempts"],
            "escalations": state["escalations"],
            "escalation_reason": state.get("escalation_reason"),
        },
        "recommended_capability": resolve_capability(capability),
        "context": packet,
        "context_tokens": packet["context_measurement"]["estimated_packet_tokens"],
        "next_prompt": build_prompt(manifest, stage, record),
    }


def _completion_packet(
    manifest: dict[str, Any],
    record: dict[str, Any],
    stage_id: str,
    validation: dict[str, Any],
) -> dict[str, Any]:
    """Compact stage-completion summary: outcome, then exactly what comes next."""
    state = record["stages"][stage_id]
    following = next_stage_id(manifest, record)
    packet: dict[str, Any] = {
        "workflow_id": manifest["workflow_id"],
        "run_id": record["run_id"],
        "project": manifest["project"],
        "completed_stage": {
            "stage_id": stage_id,
            "status": state["status"],
            "capability_class": state["capability_class"],
            "attempts": state["attempts"],
            "outputs": state["outputs"],
            "checkpoint": state["checkpoint"],
            "validation": validation,
        },
        "run_status": record["status"],
        "next_stage": None,
        "recommended_capability": None,
        "next_prompt": None,
    }
    if following is None:
        packet["message"] = (
            "workflow complete" if record["status"] == "complete" else "no runnable stage remains"
        )
        return packet
    following_stage = stage_of(manifest, following)
    following_state = record["stages"][following]
    capability = following_state.get("capability_class", following_stage["capability_class"])
    packet["next_stage"] = {
        "stage_id": following,
        "goal": following_stage["goal"],
        "capability_class": capability,
        "effort": following_stage.get("effort", "low"),
        "preferred_execution_path": following_stage["preferred_execution_path"],
        "execution_path": _stage_execution_path(following_stage),
        "stop_condition": following_stage["stop_condition"],
    }
    packet["recommended_capability"] = resolve_capability(capability)
    packet["next_prompt"] = build_prompt(manifest, following_stage, record)
    return packet


# --------------------------------------------------------------------------
# Execution
# --------------------------------------------------------------------------


def _finish_if_done(manifest: dict[str, Any], record: dict[str, Any]) -> None:
    if all(state["status"] == "complete" for state in record["stages"].values()):
        record["status"] = "complete"
    elif any(state["status"] == "blocked" for state in record["stages"].values()):
        record["status"] = "blocked"
    else:
        record["status"] = "in_progress"


def _escalate(record: dict[str, Any], stage_id: str, reason: str) -> bool:
    """Move a stage one rung up the ladder, on evidence, within policy."""
    state = record["stages"][stage_id]
    if state["escalations"] >= record["max_escalations"]:
        state["status"] = "blocked"
        state["escalation_reason"] = f"{reason}; escalation budget exhausted"
        return False
    promoted = next_class(state["capability_class"])
    if promoted is None:
        state["status"] = "blocked"
        state["escalation_reason"] = f"{reason}; already at the strongest capability class"
        return False
    state["capability_class"] = promoted
    state["escalations"] += 1
    state["status"] = "pending"
    state["escalation_reason"] = reason
    return True


def run_stage(workflow_id: str, run_id: str, stage_id: str | None = None) -> dict[str, Any]:
    """Advance the run by one stage.

    A deterministic stage is executed and validated here. Any other stage is
    prepared and handed over: the orchestrator stops at that boundary rather
    than pretending to run a model itself.
    """
    manifest = load_manifest(workflow_id)
    record = load_run(manifest["project"], run_id)
    target = stage_id or next_stage_id(manifest, record)
    if target is None:
        _finish_if_done(manifest, record)
        _save(record)
        return {
            "workflow_id": workflow_id,
            "run_id": run_id,
            "stage": None,
            "run_status": record["status"],
            "message": "workflow complete" if record["status"] == "complete" else "no runnable stage remains",
        }
    stage = stage_of(manifest, target)
    state = record["stages"][target]
    execution_path = state.get("execution_path") or _stage_execution_path(stage)
    state["execution_path"] = execution_path

    # Successful work is never redone by a stronger model on a whim.
    if state["status"] == "complete":
        return {
            "workflow_id": workflow_id,
            "run_id": run_id,
            "stage": target,
            "skipped": True,
            "reason": "stage already completed and validated; re-running requires an explicit recorded reason",
            "run_status": record["status"],
        }

    if execution_path != "deterministic":
        state["status"] = "awaiting_agent"
        _save(record)
        packet = prepare_stage(workflow_id, run_id, target)
        packet["message"] = "stage prepared; run it with the recommended capability, then report completion"
        return packet

    state["attempts"] += 1
    validation = _validate_stage(stage, state, ROOT)
    state["validation"] = validation
    if validation["passed"]:
        state["status"] = "complete"
        state["completed_at"] = _now()
        if stage.get("checkpoint"):
            state["checkpoint"] = stage["checkpoint"]
        if not state["outputs"]:
            state["outputs"] = list(stage.get("expected_outputs", []))
    else:
        state["status"] = "failed"
        _escalate(record, target, f"validator failed: {validation.get('detail') or 'no detail'}")
    _finish_if_done(manifest, record)
    _save(record)
    return _completion_packet(manifest, record, target, validation)


def complete_stage(
    workflow_id: str,
    run_id: str,
    stage_id: str,
    outputs: list[str] | None = None,
    checkpoint: str | None = None,
    passed: bool | None = None,
    detail: str | None = None,
) -> dict[str, Any]:
    """Record an agent-run stage's outcome and validate it deterministically.

    The caller reports what it produced; the validator, not the caller's
    confidence, decides whether the stage passed.
    """
    manifest = load_manifest(workflow_id)
    record = load_run(manifest["project"], run_id)
    if stage_id not in record["stages"]:
        raise KeyError(f"unknown stage: {stage_id}")
    stage = stage_of(manifest, stage_id)
    state = record["stages"][stage_id]
    state["execution_path"] = state.get("execution_path") or _stage_execution_path(stage)
    if state["status"] == "complete":
        return {
            "workflow_id": workflow_id,
            "run_id": run_id,
            "stage": stage_id,
            "skipped": True,
            "reason": "stage already completed; idempotent no-op",
            "run_status": record["status"],
        }
    state["attempts"] += 1
    # Partial work survives a failure: reported outputs are merged, never lost.
    state["outputs"] = list(dict.fromkeys([*state["outputs"], *(outputs or [])]))
    if checkpoint:
        state["checkpoint"] = checkpoint
    validation = _validate_stage(stage, state, ROOT)
    if passed is False:
        validation = {
            "kind": validation["kind"],
            "passed": False,
            "detail": detail or "the agent reported the stage as unfinished",
        }
    state["validation"] = validation
    if validation["passed"]:
        state["status"] = "complete"
        state["completed_at"] = _now()
    else:
        state["status"] = "failed"
        _escalate(record, stage_id, f"validator failed: {validation.get('detail') or 'no detail'}")
    _finish_if_done(manifest, record)
    _save(record)
    return _completion_packet(manifest, record, stage_id, validation)


def status(workflow_id: str, run_id: str) -> dict[str, Any]:
    """Answer 'what do I run next?' purely from persisted stage state."""
    manifest = load_manifest(workflow_id)
    record = load_run(manifest["project"], run_id)
    following = next_stage_id(manifest, record)
    summary = {
        "workflow_id": workflow_id,
        "run_id": run_id,
        "project": manifest["project"],
        "goal": manifest["goal"],
        "run_status": record["status"],
        "stages": [
            {
                "stage_id": stage_id,
                "status": record["stages"][stage_id]["status"],
                "capability_class": record["stages"][stage_id]["capability_class"],
                "attempts": record["stages"][stage_id]["attempts"],
                "escalations": record["stages"][stage_id]["escalations"],
            }
            for stage_id in ordered_stage_ids(manifest)
        ],
        "next_stage": None,
        "recommended_capability": None,
        "next_prompt": None,
    }
    if following is None:
        return summary
    stage = stage_of(manifest, following)
    capability = record["stages"][following].get("capability_class", stage["capability_class"])
    summary["next_stage"] = {
        "stage_id": following,
        "goal": stage["goal"],
        "capability_class": capability,
        "effort": stage.get("effort", "low"),
        "stop_condition": stage["stop_condition"],
    }
    summary["recommended_capability"] = resolve_capability(capability)
    summary["next_prompt"] = build_prompt(manifest, stage, record)
    return summary
