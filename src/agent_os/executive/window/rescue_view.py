"""Build the Executive window's Rescue Mode view."""

from __future__ import annotations

from datetime import date

from agent_os import registry as project_registry
from agent_os.executive import project_actions


def project_results(today: date, stale_days: int | None = None) -> tuple[list[dict], list[dict]]:
    stale = stale_days if stale_days is not None else project_actions.STALE_DAYS_DEFAULT
    results: list[dict] = []
    errors: list[dict] = []
    for proj in project_registry.canonical_projects():
        if "state_file" not in proj:
            continue
        try:
            state = project_registry.load_state(proj)
            results.append(project_actions.project_next_action(state, today=today, stale_days=stale))
        except Exception as exc:
            errors.append({"project": proj.get("id"), "error": str(exc)})
    return results, errors


def rescue_view(
    registry,
    tab: str | None = None,
    state=None,
    *,
    today: date | None = None,
    horizon_days: int = 1,
    stale_days: int | None = None,
    projects: list | None = None,
) -> dict:
    today = today or date.today()
    q = registry.queue(tab, state=state)
    if projects is None:
        projects, project_errors = project_results(today, stale_days)
    else:
        project_errors = []
    from agent_os.executive.rescue import rescue

    result = rescue(q["queue_items"], projects, today=today, horizon_days=horizon_days)
    item_id = None
    action = result.get("action")
    if isinstance(action, dict) and action.get("queue_item_id") is not None:
        queue_item = next((item for item in q["queue_items"] if item.get("id") == action["queue_item_id"]), None)
        if queue_item is not None:
            window_item = queue_item.get("window_item")
            if isinstance(window_item, dict) and window_item.get("id") is not None:
                item_id = str(window_item["id"])
    return {**result, "item_id": item_id, "tab": tab, "errors": q["errors"] + project_errors}
