"""Provider for applicant executive needs-action groups as outstanding work items."""
from __future__ import annotations

from typing import Any, Callable

_FORBIDDEN_KEYS = {"gender", "race", "ethnicity", "veteran", "disability", "eeo", "self_id"}


def _is_clean(obj: Any) -> bool:
    """Recursively check that obj contains no forbidden keys."""
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key in _FORBIDDEN_KEYS:
                return False
            if not _is_clean(value):
                return False
    elif isinstance(obj, (list, tuple)):
        for item in obj:
            if not _is_clean(item):
                return False
    return True


def _clean_dict(obj: Any) -> Any:
    """Recursively remove forbidden keys from dicts, preserving structure."""
    if isinstance(obj, dict):
        return {k: _clean_dict(v) for k, v in obj.items() if k not in _FORBIDDEN_KEYS}
    if isinstance(obj, (list, tuple)):
        return [_clean_dict(item) for item in obj]
    return obj


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

        # Ensure no forbidden keys
        if not _is_clean(context):
            context = _clean_dict(context)

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
