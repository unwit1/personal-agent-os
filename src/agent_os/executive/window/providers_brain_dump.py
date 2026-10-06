"""Brain-dump records as items in the Executive window."""

from __future__ import annotations

from .brain_dump_store import BrainDumpStore


def brain_dump_items(store=None) -> list[dict]:
    """Return open brain-dump records in the window item format."""
    if store is None:
        store = BrainDumpStore()

    items = []
    for record in store.records():
        record_id = record["id"]
        record_type = record.get("type")
        project = record.get("project")
        candidates = []
        clarification = record.get("clarification")
        if clarification:
            candidates = clarification.get("candidates") or []
            reason = clarification.get("reason")
            if candidates:
                why = f"Which project? ({reason}; candidates: {', '.join(candidates)})"
            else:
                why = f"Which project? ({reason})"
            kind = "brain_dump_clarification"
        else:
            why = f"Brain dump {record_type}"
            if project:
                why += f" for {project}"
            kind = "brain_dump_record"

        items.append({
            "id": f"brain-dump:{record_id}",
            "kind": kind,
            "title": record["text"],
            "tab": record["tab"],
            "score": 1,
            "source": "Brain dump",
            "sensitivity": "personal",
            "why": why,
            "context": {
                "record_id": record_id,
                "type": record_type,
                "project": project,
                "candidates": candidates,
            },
        })
    return items
