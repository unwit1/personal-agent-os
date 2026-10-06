"""Find missing project state details as deterministic knowledge gaps."""

from __future__ import annotations


FACTORS = {
    "goal": {"utility": 0.8, "recurrence": 0.5, "confidence_gap": 1.0, "urgency": 0.3, "interruption_cost": 0.1},
    "next_action": {"utility": 0.9, "recurrence": 0.5, "confidence_gap": 1.0, "urgency": 0.6, "interruption_cost": 0.1},
    "blockers": {"utility": 0.5, "recurrence": 0.3, "confidence_gap": 0.8, "urgency": 0.2, "interruption_cost": 0.1},
}

_QUESTIONS = {
    "goal": "What is the goal of project {project}?",
    "next_action": "What is the next concrete action for project {project}?",
    "blockers": "Is anything blocking project {project}? (list blockers, or none)",
}


def _nonempty_string(value):
    return isinstance(value, str) and bool(value.strip())


def project_gaps(states, *, include_inactive=False) -> list[dict]:
    """Return missing goal, next-action, and blocker details for projects."""
    gaps = []
    for state in states:
        if not isinstance(state, dict):
            continue
        project = state.get("project")
        if not _nonempty_string(project):
            continue
        if not include_inactive and state.get("status") != "active":
            continue

        missing = []
        if not (_nonempty_string(state.get("goal")) or _nonempty_string(state.get("summary"))):
            missing.append("goal")

        priorities = state.get("current_priorities", [])
        has_priority = isinstance(priorities, list) and any(_nonempty_string(item) for item in priorities)
        if not _nonempty_string(state.get("next_action")) and not has_priority:
            missing.append("next_action")

        if "blockers" not in state or not isinstance(state["blockers"], list):
            missing.append("blockers")

        for field in missing:
            gaps.append({
                "id": f"project-gap:{project}:{field}",
                "question": _QUESTIONS[field].format(project=project),
                "topic": f"project:{field}",
                "project": project,
                "source": "project_state",
                "field": field,
                **FACTORS[field],
            })

    field_order = {field: index for index, field in enumerate(FACTORS)}
    gaps.sort(key=lambda gap: (gap["project"], field_order[gap["field"]]))
    return gaps
