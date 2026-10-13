"""Actions for opening project resumption packets from Executive window project items."""

from __future__ import annotations

from datetime import date
from typing import Callable

from . import registry

LOAD_STATE: Callable[[str], dict] | None = None
WRITE_STATE: Callable[[str, dict], None] | None = None
TODAY: Callable[[], date] | None = None


def _load_state(project: str) -> dict:
    if LOAD_STATE is not None:
        return LOAD_STATE(project)
    from agent_os import registry as project_registry

    try:
        entry = project_registry.get_project(project)
    except KeyError:
        raise ValueError(f"unknown project: {project}") from None
    try:
        return project_registry.load_state(entry)
    except OSError:
        raise ValueError(f"no state for project: {project}") from None


def _today() -> date:
    return TODAY() if TODAY is not None else date.today()


def _write_state(project: str, state: dict) -> None:
    if WRITE_STATE is not None:
        WRITE_STATE(project, state)
        return
    from agent_os import paths, registry as project_registry, storage

    try:
        entry = project_registry.get_project(project)
    except KeyError:
        raise ValueError(f"unknown project: {project}") from None
    storage.write_json(paths.ROOT / entry["state_file"], state)


def _resume(item: dict, params: dict, *, confirm: bool) -> dict:
    pid = (item.get("context") or {}).get("project")
    if not pid:
        raise ValueError("missing project id")
    state = _load_state(pid)
    from agent_os.executive.resumption import resumption_packet

    packet = resumption_packet(state, today=_today())
    return {"project": pid, "packet": packet}


def _set_next_action(item: dict, params: dict, *, confirm: bool) -> dict:
    pid = (item.get("context") or {}).get("project")
    if not pid:
        raise ValueError("missing project id")
    next_action = params.get("next_action")
    next_action = next_action.strip() if isinstance(next_action, str) else ""
    if not next_action:
        raise ValueError("next_action must be a non-empty string")
    from agent_os.executive.project_actions import is_vague_action

    if is_vague_action(next_action):
        raise ValueError("next_action is too vague; name a concrete step")
    state = _load_state(pid)
    updated = {**state, "next_action": next_action, "updated_at": _today().isoformat()}
    if not confirm:
        return {
            "project": pid, "before": state.get("next_action"), "after": next_action,
            "note": "Writes next_action and updated_at to this project's state.json on Confirm.",
        }
    _write_state(pid, updated)
    return {"project": pid, "next_action": next_action, "updated_at": updated["updated_at"]}


def _resolve_decision(item: dict, params: dict, *, confirm: bool) -> dict:
    context = item.get("context") or {}
    pid = context.get("project")
    if not pid:
        raise ValueError("missing project id")
    decision = context.get("decision")
    if not decision:
        raise ValueError("missing decision text")
    resolution = params.get("resolution")
    resolution = resolution.strip() if isinstance(resolution, str) else ""
    if not resolution:
        raise ValueError("resolution must be a non-empty string")
    state = _load_state(pid)
    decisions = list(state.get("decisions_needed") or [])
    if decision not in decisions:
        raise ValueError(f"decision no longer open: {decision}")
    decisions.remove(decision)
    resolved_on = _today().isoformat()
    updated = {
        **state,
        "decisions_needed": decisions,
        "decisions_resolved": list(state.get("decisions_resolved") or []) + [
            {"decision": decision, "resolution": resolution, "resolved_on": resolved_on}
        ],
        "updated_at": resolved_on,
    }
    if not confirm:
        return {
            "project": pid, "decision": decision, "resolution": resolution,
            "remaining_decisions": updated["decisions_needed"],
            "note": "Removes the decision from decisions_needed and records it in decisions_resolved on Confirm.",
        }
    _write_state(pid, updated)
    return {"project": pid, "decision": decision, "resolution": resolution, "resolved_on": resolved_on}


def register(reg: registry.Registry) -> None:
    reg.register_action(
        "project.resume", "Resume",
        ["project_decision", "project_stalled", "project_no_next_action", "project_vague_next_action", "project_repeatedly_deferred", "project_blocked"],
        _resume,
        consequential=False,
        description="Open a compact resumption packet for this project (read-only)",
        params_schema={},
    )
    reg.register_action(
        "project.set_next_action", "Set next action",
        ["project_stalled", "project_no_next_action", "project_vague_next_action", "project_repeatedly_deferred", "project_blocked"],
        _set_next_action,
        consequential=True,
        description="Record this project's next action in its state.json (preview first; writes only on Confirm)",
        params_schema={"next_action": {"type": "string"}},
    )
    reg.register_action(
        "project.resolve_decision", "Resolve decision", ["project_decision"],
        _resolve_decision,
        consequential=True,
        description="Record the resolution of a decision this project owes in its state.json (preview first; writes only on Confirm)",
        params_schema={"resolution": {"type": "string"}},
    )
