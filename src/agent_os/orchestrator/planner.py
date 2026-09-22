"""Dependency-aware task graphs.

Plans come from three places, cheapest first:

1. explicit tasks supplied by the caller (no model call at all);
2. ``planning: single`` -- one implementer node for the whole goal;
3. ``planning: auto`` -- a read-only planner node at a modest capability class
   whose structured output is expanded into the graph.

Whatever the source, the graph is validated the same way: unique IDs, known
dependencies, no cycles, bounded size.
"""

from __future__ import annotations

from typing import Any

from .model import EDITING_ROLES, PlanError, new_node


PLANNER_ID = "plan"
PLANNABLE_ROLES = ("implementer", "test_author")
TASK_KEYS = {
    "id", "goal", "role", "depends_on", "scope", "capability_class", "effort", "execution_path",
    "command", "validators", "approval_gate", "review_required", "expected_outputs", "context_budget",
}


def node_from_task(task: dict[str, Any], *, extra_depends: list[str] | None = None, origin: str = "plan") -> dict[str, Any]:
    if not isinstance(task, dict):
        raise PlanError("each task must be an object")
    unknown = sorted(set(task) - TASK_KEYS)
    if unknown:
        raise PlanError(f"task {task.get('id')}: unsupported fields {unknown}")
    role = task.get("role", "implementer")
    if role not in PLANNABLE_ROLES:
        raise PlanError(f"task {task.get('id')}: role must be one of {PLANNABLE_ROLES}")
    execution_path = task.get("execution_path", "model")
    return new_node(
        str(task.get("id") or ""),
        str(task.get("goal") or ""),
        role,
        depends_on=[*(extra_depends or []), *list(task.get("depends_on") or [])],
        scope=task.get("scope"),
        capability_class=task.get("capability_class", "deterministic" if execution_path == "deterministic" else "balanced"),
        effort=task.get("effort", "none" if execution_path == "deterministic" else "medium"),
        execution_path=execution_path,
        command=task.get("command"),
        validators=task.get("validators"),
        approval_gate=task.get("approval_gate"),
        review_required=task.get("review_required"),
        expected_outputs=task.get("expected_outputs"),
        context_budget=int(task.get("context_budget", 1200)),
        origin=origin,
    )


def check_graph(nodes: dict[str, dict[str, Any]]) -> None:
    for node in nodes.values():
        for dependency in node["depends_on"]:
            if dependency not in nodes:
                raise PlanError(f"node {node['id']} depends on unknown node {dependency}")
            if dependency == node["id"]:
                raise PlanError(f"node {node['id']} depends on itself")
    visiting: set[str] = set()
    done: set[str] = set()

    def visit(node_id: str, trail: list[str]) -> None:
        if node_id in done:
            return
        if node_id in visiting:
            raise PlanError("dependency cycle: " + " -> ".join([*trail, node_id]))
        visiting.add(node_id)
        for dependency in nodes[node_id]["depends_on"]:
            visit(dependency, [*trail, node_id])
        visiting.discard(node_id)
        done.add(node_id)

    for node_id in nodes:
        visit(node_id, [])


def explicit_plan(tasks: list[dict[str, Any]], max_tasks: int) -> dict[str, dict[str, Any]]:
    if not isinstance(tasks, list) or not tasks:
        raise PlanError("an explicit plan needs at least one task")
    if len(tasks) > max_tasks:
        raise PlanError(f"plan has {len(tasks)} tasks; the policy allows {max_tasks}")
    nodes: dict[str, dict[str, Any]] = {}
    for task in tasks:
        node = node_from_task(task)
        if node["id"] in nodes:
            raise PlanError(f"duplicate task id {node['id']}")
        nodes[node["id"]] = node
    check_graph(nodes)
    return nodes


def single_plan(goal: str, validators: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    node = new_node("implement", goal, "implementer", validators=validators)
    return {node["id"]: node}


def planner_plan(goal: str) -> dict[str, dict[str, Any]]:
    node = new_node(
        PLANNER_ID,
        f"Decompose into a small dependency-aware plan: {goal}",
        "planner",
        capability_class="balanced",
        effort="medium",
        context_budget=1600,
    )
    return {node["id"]: node}


def expand(nodes: dict[str, dict[str, Any]], planner_id: str, structured: dict[str, Any] | None, max_tasks: int) -> list[str]:
    """Add a planner's proposed tasks to the graph. Returns the new node IDs."""
    tasks = (structured or {}).get("tasks")
    if not isinstance(tasks, list) or not tasks:
        raise PlanError("planner result has no tasks")
    if len(tasks) > max_tasks:
        raise PlanError(f"planner proposed {len(tasks)} tasks; the policy allows {max_tasks}")
    added: dict[str, dict[str, Any]] = {}
    for task in tasks:
        if isinstance(task, dict) and task.get("execution_path") == "deterministic":
            # A model-proposed shell command is not an approved deterministic
            # runner; it would bypass review of what actually executes.
            raise PlanError(f"planner task {task.get('id')}: deterministic commands must come from the caller, not a model")
        node = node_from_task({key: value for key, value in task.items() if key in TASK_KEYS}, extra_depends=[planner_id], origin="planner")
        if node["id"] in nodes or node["id"] in added:
            raise PlanError(f"planner proposed duplicate id {node['id']}")
        if node["capability_class"] == "frontier":
            node["capability_class"] = node["requested_capability_class"] = "reasoning"
        added[node["id"]] = node
    combined = {**nodes, **added}
    check_graph(combined)
    nodes.update(added)
    return list(added)


def editing(node: dict[str, Any]) -> bool:
    return node["role"] in EDITING_ROLES
