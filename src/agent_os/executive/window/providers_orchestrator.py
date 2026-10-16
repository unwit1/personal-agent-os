"""Orchestrator run status as outstanding items: gates and parked nodes."""

from __future__ import annotations

from typing import Any, Callable


_TERMINAL_RUN_STATES = frozenset({"COMPLETE", "FAILED"})
# list_runs is newest first; only this many finished runs are shown (and read).
_MAX_COMPLETED_ITEMS = 5


def orchestrator_items(
    list_runs: Callable[[], list[dict[str, Any]]] | None = None,
    status: Callable[[str], dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Return outstanding items for open approval gates and parked nodes.

    Both parameters default to agent_os.orchestrator.service functions and are
    injectable for testing.
    """
    if list_runs is None:
        from agent_os.orchestrator import service

        list_runs = service.list_runs
    if status is None:
        from agent_os.orchestrator import service

        status = service.status
    items: list[dict[str, Any]] = []
    completed_shown = 0
    for run in list_runs() or []:
        run_id = run.get("run_id")
        if not run_id:
            continue
        # COMPLETE and FAILED are terminal: a dead run has nothing the operator
        # can act on. A completed run shows its result branch until dismissed.
        if run.get("state") in _TERMINAL_RUN_STATES:
            if run.get("state") == "COMPLETE" and completed_shown < _MAX_COMPLETED_ITEMS:
                completed_shown += 1
                try:
                    items.append(_completed_run_item(run_id, status(run_id)))
                except (KeyError, ValueError, OSError):
                    pass
            continue
        try:
            run_status = status(run_id)
        except (KeyError, ValueError, OSError):
            continue
        items.append(_run_item(run_id, run_status, run))
        items.extend(_gates_as_items(run_id, run_status))
        items.extend(_parked_nodes_as_items(run_id, run_status))
    return items


def _short(text: Any, limit: int = 80) -> str:
    text = " ".join(str(text or "").split())
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def _run_item(run_id: str, run_status: dict[str, Any], run: dict[str, Any]) -> dict[str, Any]:
    """One item per non-terminal run: its goal, state and task progress."""
    progress = run_status.get("progress") or {}
    nodes = run_status.get("nodes") or []
    total = progress.get("total", len(nodes))
    passed = progress.get("passed", sum(1 for n in nodes if n.get("state") == "PASSED"))
    state = run_status.get("state") or run.get("state") or "UNKNOWN"
    paused = bool(run_status.get("paused"))
    label = "paused" if paused else str(state).lower().replace("_", " ")
    why = f"{label}: {passed} of {total} tasks done" if total else label
    return {
        "id": f"coding:{run_id}",
        "kind": "coding_run",
        "tab": "work",
        "title": _short(run_status.get("goal") or run.get("goal") or f"Coding run {run_id[:8]}"),
        "why": why,
        "source": f"Run {run_id[:8]}",
        "context": {"run_id": run_id, "state": state, "paused": paused, "passed": passed, "total": total},
    }


def _completed_run_item(run_id: str, run_status: dict[str, Any]) -> dict[str, Any]:
    """A finished run stays on the list, showing its result branch, until dismissed."""
    integration = run_status.get("integration") or {}
    final = run_status.get("final") or {}
    branch = integration.get("branch") or final.get("integration_branch")
    return {
        "id": f"coding_done:{run_id}",
        "kind": "coding_done",
        "tab": "work",
        "title": _short(f"Finished: {run_status.get('goal') or run_id[:8]}"),
        "why": f"Result branch: {branch}. Nothing is merged until you do it." if branch else "Run complete.",
        "source": f"Run {run_id[:8]}",
        "context": {"run_id": run_id, "branch": branch},
    }


def _gates_as_items(run_id: str, run_status: dict[str, Any]) -> list[dict[str, Any]]:
    """Convert open approval gates to outstanding items."""
    from agent_os.orchestrator.simple import gate_card

    items: list[dict[str, Any]] = []
    nodes_by_id = {node["id"]: node for node in run_status.get("nodes") or []}
    for gate in run_status.get("gates") or []:
        if gate.get("status") != "open":
            continue
        node = nodes_by_id.get(gate.get("node") or "")
        card = gate_card(gate, node)
        items.append(
            {
                "id": f"gate:{run_id}:{gate['id']}",
                "kind": "orchestrator_gate",
                "tab": "work",
                "title": card.get("title", "Approval needed"),
                "why": card.get("what", ""),
                "source": f"Run {run_id[:8]}",
                "context": {"run_id": run_id, "gate_id": gate["id"]},
            }
        )
    return items


def _parked_nodes_as_items(run_id: str, run_status: dict[str, Any]) -> list[dict[str, Any]]:
    """Convert parked/failed nodes to outstanding items."""
    from agent_os.orchestrator.simple import failure_card

    items: list[dict[str, Any]] = []
    for node in run_status.get("nodes") or []:
        # Only FAILED_FINAL needs the operator; CANCELLED nodes were stopped on
        # purpose and offer nothing to act on.
        if node["state"] != "FAILED_FINAL":
            continue
        if (node.get("wait_reason") or "").split(":")[0].endswith("rejected by user"):
            continue
        card = failure_card(node)
        items.append(
            {
                "id": f"parked:{run_id}:{node['id']}",
                "kind": "orchestrator_parked",
                "tab": "work",
                "title": card.get("title", f"Node {node['id']} needs attention"),
                "why": card.get("what", ""),
                "source": f"Run {run_id[:8]}",
                "context": {"run_id": run_id, "node_id": node["id"]},
            }
        )
    return items
