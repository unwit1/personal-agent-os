"""Project action planning with goal, blockers, and next action synthesis.

Pure functions operating on project state dicts to extract, validate,
and rank project action planning metadata.
"""

from __future__ import annotations

import re
from datetime import date
from typing import Any

STALE_DAYS_DEFAULT = 30
REPEATED_DEFERRAL_THRESHOLD = 3
VAGUE_ACTIONS = frozenset({'tbd', 'todo', 'n/a', 'none', 'continue', 'keep going', 'next steps', 'work on it', 'progress', 'misc', 'various'})
_VAGUE_PREFIX = re.compile(r'^(work on|continue working on|continue with|continue on|keep working on|make progress on|progress on|look into|think about)\s+\S+(\s+\S+){0,2}$')


def is_vague_action(text: str) -> bool:
    """Check if text represents a vague action.

    Returns False for non-str or empty text. Otherwise normalizes the text:
    strip, lowercase, strip trailing '.!?', and collapse internal whitespace.
    Returns True if the normalized text is in VAGUE_ACTIONS or fully matches
    _VAGUE_PREFIX, else False.

    Args:
        text: Text to check

    Returns:
        True if text is a vague action, False otherwise
    """
    if not isinstance(text, str) or not text:
        return False

    normalized = text.strip().lower()
    normalized = normalized.rstrip('.!?')
    normalized = ' '.join(normalized.split())

    if normalized in VAGUE_ACTIONS:
        return True

    if _VAGUE_PREFIX.fullmatch(normalized):
        return True

    return False


def project_next_action(
    state: dict,
    *,
    today: date,
    stale_days: int = STALE_DAYS_DEFAULT,
    deferrals: int = 0,
) -> dict:
    """Extract and synthesize next action metadata from project state.

    Args:
        state: Project state dict with project, status, goal, summary, current_state,
            next_action, current_priorities, blockers, waiting_on, decisions_needed,
            delegable_work, updated_at
        today: Reference date for age_days calculation
        stale_days: Threshold for stalled flag
        deferrals: Number of times the project has been deferred; invalid values become 0

    Returns:
        Dict with project, status, goal, current_state, next_action, next_action_source,
        blockers, waiting_on, decisions_needed, delegable_work, updated_at, age_days, flags,
        suggested_next_action (when vague_next_action flag is set), and deferrals.

    Raises:
        TypeError: if state is not a dict
    """
    if not isinstance(state, dict):
        raise TypeError(f"state must be dict, got {type(state).__name__}")

    if isinstance(deferrals, bool) or not isinstance(deferrals, int) or deferrals < 0:
        deferrals = 0

    project = state.get("project")
    status = state.get("status")

    goal = state.get("goal", "")
    if not isinstance(goal, str) or not goal.strip():
        goal = state.get("summary")

    current_state = state.get("current_state", "")
    if not isinstance(current_state, str) or not current_state.strip():
        current_state = None

    next_action = None
    next_action_source = None

    next_action_val = state.get("next_action", "")
    if isinstance(next_action_val, str) and next_action_val.strip():
        next_action = next_action_val
        next_action_source = "next_action"
    else:
        current_priorities = state.get("current_priorities", [])
        if isinstance(current_priorities, list):
            for priority in current_priorities:
                if isinstance(priority, str) and priority.strip():
                    next_action = priority
                    next_action_source = "current_priorities"
                    break

    def extract_list_field(field_name: str) -> list:
        field = state.get(field_name, [])
        if not isinstance(field, list):
            return []
        return [item for item in field if isinstance(item, str) and item.strip()]

    blockers = extract_list_field("blockers")
    waiting_on = extract_list_field("waiting_on")
    decisions_needed = extract_list_field("decisions_needed")
    delegable_work = extract_list_field("delegable_work")

    updated_at = state.get("updated_at")
    age_days = None
    if updated_at and isinstance(updated_at, str):
        try:
            updated_date = date.fromisoformat(updated_at[:10])
            age_days = (today - updated_date).days
        except ValueError:
            age_days = None

    flags = []
    if next_action is None:
        flags.append("no_next_action")
    if age_days is not None and age_days > stale_days:
        flags.append("stalled")
    if age_days is None:
        flags.append("unknown_age")
    if blockers or waiting_on:
        flags.append("blocked")
    if decisions_needed:
        flags.append("needs_decision")
    if deferrals >= REPEATED_DEFERRAL_THRESHOLD:
        flags.append("repeatedly_deferred")

    suggested_next_action = None
    if next_action is not None and is_vague_action(next_action):
        flags.append("vague_next_action")
        current_priorities = state.get("current_priorities", [])
        if isinstance(current_priorities, list):
            for priority in current_priorities:
                if isinstance(priority, str) and priority.strip() and priority != next_action and not is_vague_action(priority):
                    suggested_next_action = priority
                    break
        if suggested_next_action is None:
            for item in delegable_work:
                if item and not is_vague_action(item):
                    suggested_next_action = item
                    break

    flags.sort()

    return {
        "project": project,
        "status": status,
        "goal": goal,
        "current_state": current_state,
        "next_action": next_action,
        "next_action_source": next_action_source,
        "blockers": blockers,
        "waiting_on": waiting_on,
        "decisions_needed": decisions_needed,
        "delegable_work": delegable_work,
        "updated_at": updated_at,
        "age_days": age_days,
        "flags": flags,
        "deferrals": deferrals,
        "suggested_next_action": suggested_next_action,
    }


def scan(
    states: list,
    *,
    today: date,
    stale_days: int = STALE_DAYS_DEFAULT,
    include_inactive: bool = False,
    deferrals: dict | None = None,
) -> dict:
    """Scan project states and return summary with activity flags.

    Args:
        states: List of project state dicts
        today: Reference date for age_days calculation
        stale_days: Threshold for stalled flag
        include_inactive: If False, filter to status == 'active' only
        deferrals: Optional mapping of project ids to deferral counts

    Returns:
        Dict with 'projects' (sorted list of project_next_action results),
        'stalled' (list of project ids flagged stalled),
        'no_next_action' (list of project ids flagged no_next_action),
        'needs_decision' (list of project ids flagged needs_decision),
        'blocked' (list of project ids flagged blocked),
        'vague_next_action' (list of project ids flagged vague_next_action),
        'repeatedly_deferred' (list of project ids flagged repeatedly_deferred),
        'stale_days' (threshold used)
    """
    projects_to_scan = []
    for state in states:
        if not isinstance(state, dict):
            continue
        if not include_inactive and state.get("status") != "active":
            continue
        projects_to_scan.append(state)

    project_results = [
        project_next_action(
            state,
            today=today,
            stale_days=stale_days,
            deferrals=(deferrals or {}).get(state.get("project"), 0),
        )
        for state in projects_to_scan
    ]

    project_results.sort(key=lambda x: str(x.get("project", "")))

    stalled = [p["project"] for p in project_results if "stalled" in p["flags"]]
    no_next_action = [p["project"] for p in project_results if "no_next_action" in p["flags"]]
    needs_decision = [p["project"] for p in project_results if "needs_decision" in p["flags"]]
    blocked = [p["project"] for p in project_results if "blocked" in p["flags"]]
    vague_next_action = [p["project"] for p in project_results if "vague_next_action" in p["flags"]]
    repeatedly_deferred = [p["project"] for p in project_results if "repeatedly_deferred" in p["flags"]]

    return {
        "projects": project_results,
        "stalled": stalled,
        "no_next_action": no_next_action,
        "needs_decision": needs_decision,
        "blocked": blocked,
        "vague_next_action": vague_next_action,
        "repeatedly_deferred": repeatedly_deferred,
        "stale_days": stale_days,
    }
