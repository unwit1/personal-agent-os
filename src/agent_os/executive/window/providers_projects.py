"""Project state as outstanding items, including vague next actions."""

from __future__ import annotations

import hashlib
from datetime import date
from typing import Any, Callable

from agent_os.executive import project_actions


def project_items(
    load_projects: Callable[[], list[tuple[dict, dict]]] | None = None,
    today: date | None = None,
    stale_days: int = project_actions.STALE_DAYS_DEFAULT,
    deferral_counts: Callable[[], dict[str, int]] | None = None,
) -> list[dict[str, Any]]:
    """Return outstanding items for active projects with flags.

    For each active project (status == "active"), derive next action, blockers,
    and flags via project_next_action(); emit items for decisions_needed, stalled,
    blocked, no_next_action, vague_next_action, and repeatedly_deferred flags. A
    blocked project emits one item with its normalized blockers and waiting-on
    details. Deferral counts may be provided by deferral_counts; repeated deferrals
    emit a project item.

    Args:
        load_projects: Callable returning list of (registry_entry, state) tuples.
            Defaults to _load_projects() which iterates canonical_projects(),
            loads state_file for each, and skips any entry whose load raises.
        today: Reference date for age_days calculation. Defaults to date.today().
        stale_days: Threshold for stalled flag. Defaults to STALE_DAYS_DEFAULT.
        deferral_counts: Callable returning project deferral counts. Defaults to
            counts from the local Event Bus, with failures treated as no counts.

    Returns:
        List of dicts (project queue items) with id, kind, title, why, score, tab,
        source, context, and age_days (if int), sorted by project id.
    """
    if load_projects is None:
        load_projects = _load_projects
    if today is None:
        today = date.today()
    if deferral_counts is None:
        deferral_counts = _default_deferral_counts
    try:
        counts = deferral_counts()
        if not isinstance(counts, dict):
            counts = {}
    except Exception:
        counts = {}

    items: list[dict[str, Any]] = []

    # One entry per project id, in project-id order. Window item ids are built
    # from the project id, so a second registry entry for the same project (for
    # example an alternate checkout) is skipped rather than duplicating items;
    # the first entry in registry order wins.
    projects_by_pid: dict[str, tuple[dict, dict]] = {}
    for registry_entry, state in load_projects():
        if state.get("status") != "active":
            continue
        pid = state.get("project") or registry_entry.get("id")
        if pid:
            projects_by_pid.setdefault(pid, (registry_entry, state))

    for pid in sorted(projects_by_pid):
        registry_entry, state = projects_by_pid[pid]
        name = registry_entry.get("name") or pid
        tab = "personal" if registry_entry.get("tab") == "personal" else "work"

        result = project_actions.project_next_action(
            state, today=today, stale_days=stale_days, deferrals=counts.get(pid, 0)
        )
        flags = result.get("flags", [])
        age_days = result.get("age_days")
        base = {
            "tab": tab,
            "source": f"Project {pid}",
            **({"age_days": age_days} if isinstance(age_days, int) else {}),
        }

        # Decisions needed items (score 3).
        if "needs_decision" in flags:
            for decision_text in result.get("decisions_needed", []):
                decision_id = hashlib.sha1(decision_text.encode("utf-8")).hexdigest()[:10]
                items.append(
                    {
                        **base,
                        "id": f"project:{pid}:decision:{decision_id}",
                        "kind": "project_decision",
                        "title": decision_text,
                        "why": f"Decision needed for {name}",
                        "score": 3,
                        "context": {"project": pid, "decision": decision_text},
                    }
                )

        # Stalled project item (score 2).
        if "stalled" in flags:
            items.append(
                {
                    **base,
                    "id": f"project:{pid}:stalled",
                    "kind": "project_stalled",
                    "title": f"{name} is stalled",
                    "why": f"No update in {age_days} days (stalled after {stale_days})",
                    "score": 2,
                    "context": {"project": pid},
                }
            )

        # Blocked project item (score 2), with normalized blocker details.
        if "blocked" in flags:
            blockers = result.get("blockers", [])
            waiting_on = result.get("waiting_on", [])
            sections = []
            if blockers:
                sections.append("Blocked by: " + "; ".join(blockers))
            if waiting_on:
                sections.append("Waiting on: " + "; ".join(waiting_on))
            items.append(
                {
                    **base,
                    "id": f"project:{pid}:blocked",
                    "kind": "project_blocked",
                    "title": f"{name} is blocked",
                    "why": " | ".join(sections),
                    "score": 2,
                    "context": {"project": pid},
                }
            )

        # Repeatedly deferred project item (score 2).
        if "repeatedly_deferred" in flags:
            n = result.get("deferrals")
            items.append(
                {
                    **base,
                    "id": f"project:{pid}:repeatedly-deferred",
                    "kind": "project_repeatedly_deferred",
                    "title": f"{name} keeps getting deferred",
                    "why": f"Deferred {n} times; record a concrete next step or drop it",
                    "score": 2,
                    "context": {"project": pid},
                }
            )

        # No next action item (score 1).
        if "no_next_action" in flags:
            items.append(
                {
                    **base,
                    "id": f"project:{pid}:no-next-action",
                    "kind": "project_no_next_action",
                    "title": f"{name} has no next action",
                    "why": "No next action or current priority recorded in state.json",
                    "score": 1,
                    "context": {"project": pid},
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
                    **base,
                    "id": f"project:{pid}:vague-next-action",
                    "kind": "project_vague_next_action",
                    "title": f"{name} next action is vague",
                    "why": why,
                    "score": 1,
                    "context": {"project": pid},
                }
            )

        # A concrete action is useful queue work when no other project issue
        # needs attention. Unknown age is informational and does not suppress it.
        action = result.get("next_action")
        trimmed_action = action.strip() if isinstance(action, str) else ""
        if (
            trimmed_action
            and project_actions.is_vague_action(trimmed_action) is False
            and set(flags).issubset({"unknown_age"})
        ):
            action_id = hashlib.sha1(trimmed_action.encode("utf-8")).hexdigest()[:10]
            items.append(
                {
                    **base,
                    "id": f"project:{pid}:next-action:{action_id}",
                    "kind": "project_next_action",
                    "title": trimmed_action,
                    "why": f"Next action for {name}",
                    "score": 1,
                    "context": {"project": pid},
                }
            )

    return items


def _default_deferral_counts() -> dict[str, int]:
    """Return per-project deferral counts from the local Event Bus, if available."""
    try:
        from agent_os.executive import window_queue
        from agent_os.executive.window import registry

        return window_queue.project_deferral_counts(registry.REGISTRY.event_bus)
    except Exception:
        return {}


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
