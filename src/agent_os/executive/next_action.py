"""Next action ranking and selection for executive queue items.

Pure functions operating on EXEC-0 queue items to rank, explain, and select
next actions for processing.
"""

from __future__ import annotations

from typing import Any

RANKING = (
    "domain weight desc (hiring, communications, approvals, projects, personal), "
    "then priority desc, then age_days desc, then queue item id asc"
)

# Highest weight first; matched as substrings of the item kind and source.
_DOMAIN_TERMS: tuple[tuple[int, tuple[str, ...]], ...] = (
    (5, ("applicant", "county", "opening", "candidate review", "candidate_review", "email reply", "email_reply")),
    (4, ("mail", "email", "3cx", "phone")),
    (3, ("approval", "gate", "orchestrator")),
    (2, ("project",)),
)


def domain_weight(item: dict) -> int:
    """Domain weight: hiring 5 > communications 4 > approvals 3 > projects 2 > personal 1."""
    window_item = item.get("window_item")
    window_item = window_item if isinstance(window_item, dict) else {}
    text = " ".join(
        value.lower()
        for value in (window_item.get("kind"), window_item.get("source"), item.get("source"))
        if isinstance(value, str)
    )
    for weight, terms in _DOMAIN_TERMS:
        if any(term in text for term in terms):
            return weight
    return 1


def rank(queue_items: list[Any]) -> list[dict]:
    """Rank queue items by domain weight, priority (desc), age_days (desc), then id (asc).

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
        return (-domain_weight(item), -priority, -age_days, item_id)

    return sorted(items, key=sort_key)


def explain(queue_items: list[Any], item_id: Any, bus: Any = None) -> dict | None:
    """Explain the ranking position of a queue item.

    Args:
        queue_items: list of queue items to rank
        item_id: queue item id or window item id to find
        bus: optional EventBus used to add payload-free entity event provenance

    Returns:
        Dict with queue_item_id, entity_id, item_id, provider, source, kind, tab,
        reason, priority, age_days, rank, of, ranking, and provenance; or None if not found.
    """
    ranked = rank(queue_items)
    item_id_str = str(item_id)

    # Find the item by queue_item id or window_item id
    for idx, item in enumerate(ranked):
        if item.get("id") == item_id_str:
            return _explain_ranked(ranked, idx, bus)
        window_item = item.get("window_item")
        if isinstance(window_item, dict) and "id" in window_item and str(window_item["id"]) == item_id_str:
            return _explain_ranked(ranked, idx, bus)
    return None


def _explain_ranked(ranked: list[dict], index: int, bus: Any = None) -> dict:
    """Explain the item at ``index`` of an already ranked list."""
    found_item = ranked[index]
    window_item = found_item.get("window_item") if isinstance(found_item.get("window_item"), dict) else {}

    # Extract numeric fields, defaulting to None if absent or non-numeric
    priority = found_item.get("priority")
    if not isinstance(priority, (int, float)) or isinstance(priority, bool):
        priority = None

    age_days = window_item.get("age_days")
    if not isinstance(age_days, (int, float)) or isinstance(age_days, bool):
        age_days = None

    entity_id = found_item.get("entity_id")
    events = bus.events(subject=entity_id) if bus is not None and entity_id else []
    created_event_id = next(
        (event.get("id") for event in events if event.get("type") == "task.created"),
        None,
    )

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
        "rank": index + 1,
        "of": len(ranked),
        "ranking": RANKING,
        "provenance": {
            "provider": found_item.get("provider"),
            "source": found_item.get("source"),
            "entity_id": entity_id,
            "created_event_id": created_event_id,
            "event_ids": [event.get("id") for event in events],
        },
    }


def next_item(queue_items: list[Any], bus: Any = None) -> dict:
    """Get the top-ranked next action with context.

    Args:
        queue_items: list of queue items
        bus: optional EventBus passed through to the explanation

    Returns:
        Dict with 'next' (top item or None), 'considered' (count of ranked items),
        'why' (explain result for top item or None).
    """
    eligible_items = [
        item
        for item in queue_items
        if isinstance(item, dict) and item.get("status") not in {"completed", "cancelled", "deferred"}
    ]
    ranked = rank(eligible_items)

    return {
        "next": ranked[0] if ranked else None,
        "considered": len(ranked),
        "why": _explain_ranked(ranked, 0, bus) if ranked else None,
    }
