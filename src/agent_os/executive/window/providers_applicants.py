"""Provider for applicant executive needs-action groups as outstanding work items."""
from __future__ import annotations

from typing import Any, Callable


def applicant_items(needs_action: Callable[..., dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    """Convert applicant needs-action groups to work items.

    Each group (grouped by administrative reason) becomes one work item with:
    - id: stable identifier based on the reason
    - tab: 'work'
    - kind: 'applicant_group'
    - title: human-readable description
    - why: count and reason
    - source: 'applicant_executive'
    - age_days: oldest item's age
    - context: group data with only whitelisted fields
    """
    if needs_action is None:
        from .. import applicants as ex
        needs_action = ex.needs_action

    data = needs_action()
    items: list[dict[str, Any]] = []

    for group in data.get("groups", []):
        reason = group.get("reason", "")
        count = group.get("count", 0)
        next_step = group.get("next_step", "")
        group_items = group.get("items", [])

        if not reason or not group_items:
            continue

        # Compute age_days as the maximum from items
        age_days = None
        for item in group_items:
            item_age = item.get("age_days")
            if item_age is not None:
                if age_days is None or item_age > age_days:
                    age_days = item_age

        # Build context with only whitelisted fields
        context = {
            "reason": reason,
            "count": count,
            "next_step": next_step,
            "applicants": [
                {
                    "applicant_ref": item.get("applicant_ref"),
                    "name": item.get("name"),
                    "position": item.get("position"),
                    "status": item.get("status"),
                    "submitted": item.get("submitted"),
                    "age_days": item.get("age_days"),
                }
                for item in group_items
            ],
        }

        work_item = {
            "id": f"applicants:{reason}",
            "tab": "work",
            "kind": "applicant_group",
            "title": reason.replace("_", " ").title(),
            "why": f"{count} applicant{'s' if count != 1 else ''}: {next_step}",
            "source": "applicant_executive",
            "age_days": age_days,
            "context": context,
        }

        items.append(work_item)

    return items
