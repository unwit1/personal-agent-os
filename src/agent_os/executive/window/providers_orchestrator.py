"""Orchestrator run status as outstanding items: gates and parked nodes."""

from __future__ import annotations

from typing import Any, Callable


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
    for run in list_runs() or []:
        run_id = run.get("run_id")
        if not run_id or run.get("state") == "COMPLETE":
            continue
        try:
            run_status = status(run_id)
        except (KeyError, ValueError, OSError):
            continue
        items.extend(_gates_as_items(run_id, run_status))
        items.extend(_parked_nodes_as_items(run_id, run_status))
    return items


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
        if node["state"] not in ("FAILED_FINAL", "CANCELLED"):
            continue
        if node["state"] == "CANCELLED" and (node.get("wait_reason") or "").endswith("rejected by user"):
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
