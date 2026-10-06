"""Select one deadline, project, or queue action for executive rescue mode."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from agent_os.executive.next_action import rank


def _queue_action(item: dict, window: dict) -> dict:
    return {
        "title": window.get("title") or window.get("summary") or window.get("subject") or item.get("id"),
        "project": window.get("project"),
        "queue_item_id": item.get("id"),
        "due": window.get("due"),
    }


def rescue(
    queue_items: list[Any],
    project_results: list[Any],
    *,
    today: date,
    horizon_days: int = 1,
) -> dict:
    """Choose one concrete action, prioritizing near deadlines then projects."""
    queues = [item for item in queue_items if isinstance(item, dict)]
    projects = [item for item in project_results if isinstance(item, dict)]
    ranked = rank(queues)

    def result(basis: str | None, action: dict | None, why: str) -> dict:
        considered = len(queues) + len(projects)
        return {
            "mode": "rescue",
            "basis": basis,
            "action": action,
            "why": why[:200],
            "suppressed": considered - 1 if action is not None else considered,
            "then": "Finish this one step, then run `agent-os executive rescue` again.",
        }

    deadline_limit = today + timedelta(days=horizon_days)
    for item in ranked:
        window = item.get("window_item")
        if not isinstance(window, dict):
            continue
        due = window.get("due")
        if not isinstance(due, str):
            continue
        try:
            due_date = date.fromisoformat(due[:10])
        except ValueError:
            continue
        if due_date <= deadline_limit:
            return result("deadline", _queue_action(item, window),
                          "A ranked queue item has a deadline within the rescue horizon.")

    eligible = []
    for project in projects:
        flags = project.get("flags", [])
        flags = flags if isinstance(flags, (list, tuple, set, frozenset)) else []
        if project.get("status") != "active" or "blocked" in flags:
            continue
        if "vague_next_action" in flags:
            step = project.get("suggested_next_action")
            if not step:
                continue
        else:
            step = project.get("next_action")
            if not isinstance(step, str) or not step.strip():
                continue
        age = project.get("age_days")
        age_sort = age if isinstance(age, int) and not isinstance(age, bool) else 10**9
        eligible.append(("needs_decision" in flags, age_sort, str(project.get("project")), project, step))
    if eligible:
        eligible.sort(key=lambda entry: entry[:3])
        chosen = eligible[0]
        return result("project", {
            "title": chosen[4],
            "project": chosen[3].get("project"),
            "queue_item_id": None,
            "due": None,
        }, "An active project has a concrete next step ready.")

    if ranked:
        item = ranked[0]
        window = item.get("window_item")
        window = window if isinstance(window, dict) else {}
        return result("queue", _queue_action(item, window), "No near deadline or ready project step took priority, so take the top ranked queue item.")

    return result(None, None, "There is no deadline, project step, or queue item to resume.")
