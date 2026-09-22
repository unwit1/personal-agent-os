"""Dependency-aware task graphs.

Plans come from three places, cheapest first:

1. explicit tasks supplied by the caller (no model call at all);
2. ``planning: single`` -- one implementer node for the whole goal;
3. ``planning: auto`` -- a read-only planner node whose structured output is
   expanded into the graph.

Whatever the source, the graph is validated the same way: unique IDs, known
dependencies, no cycles, bounded size.

A planner is a model, so its proposals are data, not authority: a validator or
deterministic step it proposes survives only when the command is approved (the
project's canonical validation commands, or the run policy's
``approved_commands`` patterns), and then runs as an argument list, never
through a shell.
"""

from __future__ import annotations

import re
import shlex
from typing import Any

from .model import EDITING_ROLES, PlanError, new_node


PLANNER_ID = "plan"
PLANNABLE_ROLES = ("implementer", "test_author")
TASK_KEYS = {
    "id", "goal", "role", "depends_on", "scope", "capability_class", "effort", "execution_path",
    "command", "validators", "approval_gate", "review_required", "expected_outputs", "context_budget", "ladder",
}
_SHELL_META = re.compile(r"[;&|<>`$\n\r%^]")


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
        ladder=task.get("ladder"),
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


def planner_plan(goal: str, capability_class: str = "balanced", effort: str = "medium") -> dict[str, dict[str, Any]]:
    node = new_node(
        PLANNER_ID,
        f"Decompose into small, independently verifiable batches: {goal}",
        "planner",
        capability_class=capability_class,
        effort=effort,
        context_budget=1600,
    )
    return {node["id"]: node}


def approved_argv(command: Any, patterns: list[str], project_commands: list[str] | None = None) -> list[str] | None:
    """The argument list for an approved command, or None.

    A command is approved when it contains no shell metacharacters and either
    equals one of the project's canonical validation commands or fully matches
    one of ``patterns``.
    """
    if isinstance(command, list):
        text = " ".join(str(item) for item in command)
    elif isinstance(command, str):
        text = command
    else:
        return None
    text = " ".join(text.split())
    if not text or _SHELL_META.search(text):
        return None
    known = {" ".join(str(item).split()) for item in project_commands or []}
    if text not in known and not any(re.fullmatch(pattern, text) for pattern in patterns):
        return None
    try:
        return shlex.split(text, posix=True)
    except ValueError:
        return None


def _planned_validators(task: dict[str, Any], patterns: list[str], project_commands: list[str], notes: list[str]) -> list[dict[str, Any]]:
    proposed = task.get("validators") or []
    if not isinstance(proposed, list):
        return []
    validators = []
    for index, item in enumerate(proposed[:4], start=1):
        command = item.get("command") if isinstance(item, dict) else item
        argv = approved_argv(command, patterns, project_commands)
        if argv is None:
            notes.append(f"{task.get('id')}: dropped unapproved validator {str(command)[:80]!r}")
            continue
        validators.append({"kind": "command", "command": argv, "name": f"planned-{index}"})
    return validators


def expand(
    nodes: dict[str, dict[str, Any]],
    planner_id: str,
    structured: dict[str, Any] | None,
    max_tasks: int,
    *,
    approved_commands: list[str] | None = None,
    project_commands: list[str] | None = None,
) -> tuple[list[str], list[str]]:
    """Add a planner's proposed tasks to the graph.

    Returns the new node IDs and notes about proposals that were adjusted
    (unapproved commands dropped or demoted to model work).
    """
    tasks = (structured or {}).get("tasks")
    if not isinstance(tasks, list) or not tasks:
        raise PlanError("planner result has no tasks")
    if len(tasks) > max_tasks:
        raise PlanError(f"planner proposed {len(tasks)} tasks; the policy allows {max_tasks}")
    patterns = list(approved_commands or [])
    project = list(project_commands or [])
    notes: list[str] = []
    added: dict[str, dict[str, Any]] = {}
    for task in tasks:
        if not isinstance(task, dict):
            raise PlanError("each planned task must be an object")
        task = {key: value for key, value in task.items() if key in TASK_KEYS}
        task.pop("approval_gate", None)  # gates are the caller's policy, not the planner's
        task["validators"] = _planned_validators(task, patterns, project, notes)
        if task.get("execution_path") == "deterministic":
            argv = approved_argv(task.get("command"), patterns, project)
            if argv is None:
                # A model-proposed shell command is not an approved runner; it
                # would bypass review of what actually executes.
                raise PlanError(f"planner task {task.get('id')}: deterministic command is not approved: {str(task.get('command'))[:120]!r}")
            task["command"] = argv
            task["capability_class"] = "deterministic"
            task["effort"] = "none"
            task.pop("ladder", None)
        node = node_from_task(task, extra_depends=[planner_id], origin="planner")
        if node["id"] in nodes or node["id"] in added:
            raise PlanError(f"planner proposed duplicate id {node['id']}")
        if node["capability_class"] == "frontier":
            # Frontier work is the operator's call, not the planner's.
            node["capability_class"] = node["requested_capability_class"] = "reasoning"
            node["ladder"] = [rung for rung in node["ladder"] if rung["capability_class"] != "frontier"] or [{"capability_class": "reasoning", "effort": node["effort"]}]
            node["ladder"][0] = {"capability_class": "reasoning", "effort": node["effort"]}
        added[node["id"]] = node
    combined = {**nodes, **added}
    check_graph(combined)
    nodes.update(added)
    return list(added), notes


def editing(node: dict[str, Any]) -> bool:
    return node["role"] in EDITING_ROLES
