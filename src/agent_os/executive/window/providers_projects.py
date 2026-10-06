"""Project state as outstanding items, including vague next actions."""

from __future__ import annotations

import hashlib
from datetime import date
from typing import Any, Callable


def project_items(
    load_projects: Callable[[], list[tuple[dict, dict]]] | None = None,
    today: date | None = None,
    stale_days: int | None = None,
) -> list[dict[str, Any]]:
    """Return outstanding items for active projects with flags.

    For each active project (status == "active"), derive next action, blockers,
    and flags via project_next_action(); emit items for decisions_needed, stalled,
    no_next_action, and vague_next_action flags, in that priority order per project.

    Args:
        load_projects: Callable returning list of (registry_entry, state) tuples.
            Defaults to _load_projects() which iterates canonical_projects(),
            loads state_file for each, and skips any entry whose load raises.
        today: Reference date for age_days calculation. Defaults to date.today().
        stale_days: Threshold for stalled flag. Defaults to STALE_DAYS_DEFAULT.

    Returns:
        List of dicts (project queue items) with id, kind, title, why, score, tab,
        source, context, and age_days (if int), sorted by project id.
    """
    from agent_os.executive import project_actions

    if load_projects is None:
        load_projects = _load_projects
    if today is None:
        today = date.today()
    if stale_days is None:
        stale_days = project_actions.STALE_DAYS_DEFAULT

    items: list[dict[str, Any]] = []
    projects_by_pid: dict[str, tuple[dict, dict]] = {}

    # Load and collect active projects.
    for registry_entry, state in load_projects():
        if state.get("status") != "active":
            continue
        pid = state.get("project") or registry_entry.get("id")
        if pid:
            projects_by_pid[pid] = (registry_entry, state)

    # Sort by project id and emit items for each.
    for pid in sorted(projects_by_pid.keys()):
        registry_entry, state = projects_by_pid[pid]
        name = registry_entry.get("name") or pid
        tab = "personal" if registry_entry.get("tab") == "personal" else "work"

        result = project_actions.project_next_action(state, today=today, stale_days=stale_days)
        flags = result.get("flags", [])
        age_days = result.get("age_days")

        # Decisions needed items (score 3).
        if "needs_decision" in flags:
            for decision_text in result.get("decisions_needed", []):
                decision_id = hashlib.sha1(decision_text.encode("utf-8")).hexdigest()[:10]
                items.append(
                    {
                        "id": f"project:{pid}:decision:{decision_id}",
                        "kind": "project_decision",
                        "title": decision_text,
                        "why": f"Decision needed for {name}",
                        "score": 3,
                        "tab": tab,
                        "source": f"Project {pid}",
                        "context": {"project": pid, "decision": decision_text},
                        **({"age_days": age_days} if isinstance(age_days, int) else {}),
                    }
                )

        # Stalled project item (score 2).
        if "stalled" in flags:
            items.append(
                {
                    "id": f"project:{pid}:stalled",
                    "kind": "project_stalled",
                    "title": f"{name} is stalled",
                    "why": f"No update in {age_days} days (stalled after {stale_days})"
                    if isinstance(age_days, int)
                    else f"Stalled after {stale_days} days",
                    "score": 2,
                    "tab": tab,
                    "source": f"Project {pid}",
                    "context": {"project": pid},
                    **({"age_days": age_days} if isinstance(age_days, int) else {}),
                }
            )

        # No next action item (score 1).
        if "no_next_action" in flags:
            items.append(
                {
                    "id": f"project:{pid}:no-next-action",
                    "kind": "project_no_next_action",
                    "title": f"{name} has no next action",
                    "why": "No next action or current priority recorded in state.json",
                    "score": 1,
                    "tab": tab,
                    "source": f"Project {pid}",
                    "context": {"project": pid},
                    **({"age_days": age_days} if isinstance(age_days, int) else {}),
                }
            )

        # Vague next action item (score 1).
        if "vague_next_action" in flags:
            suggested = result.get("suggested_next_action")
            why = (
                f"Next action '{result['next_action']}' is vague; suggested: {suggested}"
                if isinstance(suggested, str) and suggested
                else f"Next action '{result['next_action']}' is vague; record a concrete next step in state.json"
            )
            items.append(
                {
                    "id": f"project:{pid}:vague-next-action",
                    "kind": "project_vague_next_action",
                    "title": f"{name} next action is vague",
                    "why": why,
                    "score": 1,
                    "tab": tab,
                    "source": f"Project {pid}",
                    "context": {"project": pid},
                    **({"age_days": age_days} if isinstance(age_days, int) else {}),
                }
            )

    return items


def _load_projects() -> list[tuple[dict, dict]]:
    """Default load_projects: canonical projects with loaded state.

    Iterates agent_os.registry.canonical_projects(), skips entries without
    state_file, loads state via registry.load_state(), and silently skips any
    entry whose load raises an Exception.

    Returns:
        List of (registry_entry, state) tuples.
    """
    from agent_os import registry

    projects: list[tuple[dict, dict]] = []
    for entry in registry.canonical_projects():
        if not entry.get("state_file"):
            continue
        try:
            state = registry.load_state(entry)
            projects.append((entry, state))
        except Exception:
            continue
    return projects


