"""Provider-neutral browser control facade for Agent OS.

The browser bridge stores live Tampermonkey sessions and a durable command queue.
This module exposes bounded helpers that MCP/CLI clients can call without knowing
the HTTP bridge protocol.
"""

from __future__ import annotations

import time
from typing import Any

from .browser_bridge import BridgeStore


DEFAULT_WAIT_SECONDS = 12.0
MAX_WAIT_SECONDS = 30.0


def sessions(
    *,
    active_only: bool = True,
    active_within_seconds: int = 90,
    store: BridgeStore | None = None,
) -> list[dict[str, Any]]:
    bridge = store or BridgeStore()
    rows = bridge.list_sessions(active_within_seconds=active_within_seconds)
    return [row for row in rows if row.get("active")] if active_only else rows


def inspect(
    session_id: str,
    actions: list[dict[str, Any]] | None = None,
    *,
    issued_by: str = "agent-os",
    wait_seconds: float = DEFAULT_WAIT_SECONDS,
    store: BridgeStore | None = None,
) -> dict[str, Any]:
    """Run read-only browser actions.

    This intentionally permits only inspect/extract/wait so clients with
    read-only MCP permissions can use browser context without acquiring a
    general interaction capability.
    """
    requested = actions or [{"op": "inspect"}]
    if not isinstance(requested, list) or not requested:
        raise ValueError("actions must be a non-empty list")
    allowed = {"inspect", "extract", "wait"}
    for action in requested:
        if not isinstance(action, dict):
            raise ValueError("each browser action must be an object")
        op = str(action.get("op") or "").strip()
        if op not in allowed:
            raise ValueError(
                "browser.inspect accepts only read-only ops: inspect, extract, wait"
            )
    return execute(
        session_id,
        requested,
        issued_by=issued_by,
        approved_consequential=False,
        wait_seconds=wait_seconds,
        store=store,
    )


def execute(
    session_id: str,
    actions: list[dict[str, Any]],
    *,
    issued_by: str = "agent-os",
    approved_consequential: bool = False,
    wait_seconds: float = DEFAULT_WAIT_SECONDS,
    store: BridgeStore | None = None,
) -> dict[str, Any]:
    bridge = store or BridgeStore()
    command = bridge.enqueue_command(
        session_id,
        actions,
        issued_by=issued_by,
        approved_consequential=approved_consequential,
    )
    wait_seconds = max(0.0, min(float(wait_seconds), MAX_WAIT_SECONDS))
    if wait_seconds == 0:
        return command

    deadline = time.monotonic() + wait_seconds
    while time.monotonic() < deadline:
        current = bridge.command_status(command["command_id"])
        if current["state"] in {
            "completed",
            "failed",
            "approval_required",
            "cancelled",
        }:
            return current
        time.sleep(0.15)

    current = bridge.command_status(command["command_id"])
    current["timed_out_waiting"] = True
    current["message"] = (
        "Command is still pending or running. Call browser.command_status with "
        "the returned command_id instead of creating a duplicate command."
    )
    return current


def command_status(
    command_id: str,
    *,
    store: BridgeStore | None = None,
) -> dict[str, Any]:
    return (store or BridgeStore()).command_status(command_id)
