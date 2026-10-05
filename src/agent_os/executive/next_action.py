"""Next action ranking and selection for executive queue items.

Pure functions operating on EXEC-0 queue items to rank, explain, and select
next actions for processing.
"""

from __future__ import annotations

from typing import Any

RANKING = "priority desc, then age_days desc, then queue item id asc"


def rank(queue_items: list[Any]) -> list[dict]:
    """Rank queue items by priority (desc), age_days (desc), then id (asc).

    Args:
        queue_items: list of queue item dicts with priority and age_days (optional)

    Returns:
        New sorted list of dicts (ignores non-dict entries).
    """
    # Filter to dicts only
    items = [item for item in queue_items if isinstance(item, dict)]

    def sort_key(item: dict) -> tuple:
        # Extract priority (default 0 if absent or non-numeric)
        priority = item.get("priority", 0)
        if not isinstance(priority, (int, float)) or isinstance(priority, bool):
            priority = 0

        # Extract age_days from window_item (default 0 if absent or non-numeric)
        window_item = item.get("window_item", {})
        age_days = window_item.get("age_days", 0) if isinstance(window_item, dict) else 0
        if not isinstance(age_days, (int, float)) or isinstance(age_days, bool):
            age_days = 0

        # Extract id as string
        item_id = str(item.get("id", ""))

        # Return tuple for sorting: negative priority (desc), negative age_days (desc), id (asc)
        return (-priority, -age_days, item_id)

    return sorted(items, key=sort_key)


def explain(queue_items: list[Any], item_id: Any) -> dict | None:
    """Explain the ranking position of a queue item.

    Args:
        queue_items: list of queue items to rank
        item_id: queue item id or window item id to find

    Returns:
        Dict with queue_item_id, entity_id, item_id, provider, source, kind, tab,
        reason, priority, age_days, rank, of, ranking; or None if not found.
    """
    ranked = rank(queue_items)
    item_id_str = str(item_id)

    # Find the item by queue_item id or window_item id
    found_item = None
    found_index = None
    for idx, item in enumerate(ranked):
        if not isinstance(item, dict):
            continue
        if item.get("id") == item_id_str:
            found_item = item
            found_index = idx
            break
        window_item = item.get("window_item", {})
        if isinstance(window_item, dict) and str(window_item.get("id")) == item_id_str:
            found_item = item
            found_index = idx
            break

    if found_item is None or found_index is None:
        return None

    window_item = found_item.get("window_item", {}) if isinstance(found_item.get("window_item"), dict) else {}

    # Extract numeric fields, defaulting to None if absent or non-numeric
    priority = found_item.get("priority")
    if not isinstance(priority, (int, float)) or isinstance(priority, bool):
        priority = None

    age_days = window_item.get("age_days")
    if not isinstance(age_days, (int, float)) or isinstance(age_days, bool):
        age_days = None

    return {
        "queue_item_id": found_item.get("id"),
        "entity_id": found_item.get("entity_id"),
        "item_id": str(window_item.get("id", "")),
        "provider": found_item.get("provider"),
        "source": found_item.get("source"),
        "kind": window_item.get("kind"),
        "tab": window_item.get("tab"),
        "reason": found_item.get("reason"),
        "priority": priority,
        "age_days": age_days,
        "rank": found_index + 1,
        "of": len(ranked),
        "ranking": RANKING,
    }


def next_item(queue_items: list[Any]) -> dict:
    """Get the top-ranked next action with context.

    Args:
        queue_items: list of queue items

    Returns:
        Dict with 'next' (top item or None), 'considered' (count of ranked items),
        'why' (explain result for top item or None).
    """
    ranked = rank(queue_items)

    top_item = ranked[0] if ranked else None
    why = None
    if top_item and isinstance(top_item, dict):
        top_id = top_item.get("id")
        if top_id:
            why = explain(queue_items, top_id)

    return {
        "next": top_item,
        "considered": len(ranked),
        "why": why,
    }
