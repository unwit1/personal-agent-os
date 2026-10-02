from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from agent_os.orchestrator import service

from .confirm import ItemState, window_home

DECIDE = service.decide


def _parse_hours_or_until(params: dict[str, Any]) -> str:
    """Return ISO datetime string: until if given, else now + hours (default 24)."""
    if "until" in params:
        value = params["until"]
        if isinstance(value, str):
            return value
        if isinstance(value, datetime):
            return value.isoformat()
        raise ValueError("until must be ISO datetime or datetime object")
    hours = params.get("hours", 24)
    if not isinstance(hours, (int, float)):
        raise ValueError("hours must be a number")
    now = datetime.now(timezone.utc)
    until = now + timedelta(hours=hours)
    return until.isoformat()


def _approve_gate(item: dict[str, Any], params: dict[str, Any], *, confirm: bool) -> dict[str, Any]:
    """Approve an orchestrator gate."""
    run_id = item.get("run_id")
    gate_id = item.get("gate_id")
    if not run_id or not gate_id:
        raise ValueError("item must have run_id and gate_id")

    preview = {
        "run_id": run_id,
        "gate_id": gate_id,
        "approve": True,
        "gate_summary": item.get("gate_summary", ""),
    }

    if confirm:
        return DECIDE(run_id, gate_id, True, params.get("note"))
    return preview


def _decline_gate(item: dict[str, Any], params: dict[str, Any], *, confirm: bool) -> dict[str, Any]:
    """Decline an orchestrator gate."""
    run_id = item.get("run_id")
    gate_id = item.get("gate_id")
    if not run_id or not gate_id:
        raise ValueError("item must have run_id and gate_id")

    preview = {
        "run_id": run_id,
        "gate_id": gate_id,
        "approve": False,
        "gate_summary": item.get("gate_summary", ""),
    }

    if confirm:
        return DECIDE(run_id, gate_id, False, params.get("note"))
    return preview


def _dismiss_item(item: dict[str, Any], params: dict[str, Any], *, confirm: bool) -> dict[str, Any]:
    """Dismiss an item."""
    item_id = item.get("id")
    if not item_id:
        raise ValueError("item must have id")

    state = ItemState(window_home())
    state.dismiss(item_id)
    return {"dismissed": True}


def _snooze_item(item: dict[str, Any], params: dict[str, Any], *, confirm: bool) -> dict[str, Any]:
    """Snooze an item until a time."""
    item_id = item.get("id")
    if not item_id:
        raise ValueError("item must have id")

    until_iso = _parse_hours_or_until(params)

    state = ItemState(window_home())
    state.snooze(item_id, until_iso)
    return {"snoozed_until": until_iso}


def register(registry: Any) -> None:
    """Register orchestrator gate approval/decline and item dismiss/snooze actions."""
    registry.register_action(
        "orchestrator.approve_gate",
        "Approve",
        ["orchestrator_gate"],
        _approve_gate,
        consequential=True,
        description="Approve an orchestrator gate decision",
        params_schema={"note": {"type": "string"}},
    )
    registry.register_action(
        "orchestrator.decline_gate",
        "Decline",
        ["orchestrator_gate"],
        _decline_gate,
        consequential=True,
        description="Decline an orchestrator gate decision",
        params_schema={"note": {"type": "string"}},
    )
    registry.register_action(
        "item.dismiss",
        "Dismiss",
        "*",
        _dismiss_item,
        consequential=False,
        description="Dismiss an item permanently",
    )
    registry.register_action(
        "item.snooze",
        "Snooze",
        "*",
        _snooze_item,
        consequential=False,
        description="Snooze an item for a period",
        params_schema={"until": {"type": "string"}, "hours": {"type": "number"}},
    )
