"""Actions for opening project resumption packets from Executive window project items."""

from __future__ import annotations

from datetime import date
from typing import Callable

from . import registry

LOAD_STATE: Callable[[str], dict] | None = None
TODAY: Callable[[], date] | None = None


def _load_state(project: str) -> dict:
    if LOAD_STATE is not None:
        return LOAD_STATE(project)
    from agent_os import registry as project_registry

    try:
        entry = project_registry.get_project(project)
    except KeyError:
        raise ValueError(f"unknown project: {project}") from None
    return project_registry.load_state(entry)


def _today() -> date:
    return TODAY() if TODAY is not None else date.today()


def _resume(item: dict, params: dict, *, confirm: bool) -> dict:
    pid = (item.get("context") or {}).get("project")
    if not pid:
        raise ValueError("missing project id")
    state = _load_state(pid)
    from agent_os.executive.resumption import resumption_packet

    packet = resumption_packet(state, today=_today())
    return {"project": pid, "packet": packet}


def register(reg: registry.Registry) -> None:
    reg.register_action(
        "project.resume", "Resume",
        ["project_decision", "project_stalled", "project_no_next_action", "project_vague_next_action"],
        _resume,
        consequential=False,
        description="Open a compact resumption packet for this project (read-only)",
        params_schema={},
    )
