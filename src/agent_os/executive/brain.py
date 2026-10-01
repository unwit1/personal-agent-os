"""Deterministic facade over the Applicant Executive read flows.

``ExecutiveBrain`` combines needs_action, suggestions and batch status into one
briefing without calling any model. ``build_prompt`` is an explicit, separate
call that only formats already-projected fields into text; the brain never sends
that text anywhere, never triggers Dashboard reviews, and never sends mail.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime
from typing import Any, Mapping

from . import applicants

# Fields allowed into a prompt; everything else is dropped even if present.
_PROMPT_ITEM_FIELDS = ("applicant_ref", "name", "position", "status", "age_days")
_PROMPT_SUGGESTION_FIELDS = ("applicant_ref", "name", "position", "score", "recommendation")


def _item_states(batch: Mapping[str, Any]) -> dict[str, int]:
    counts = Counter(str(item.get("state") or "UNKNOWN") for item in batch.get("items", []))
    return dict(sorted(counts.items()))


def batch_status(batch: Mapping[str, Any]) -> dict[str, Any]:
    """Compact, whitelisted status of one persisted batch."""
    return {
        "batch_id": batch.get("batch_id"),
        "state": batch.get("state"),
        "opening": batch.get("opening"),
        "created_at": batch.get("created_at"),
        "item_count": len(batch.get("items", [])),
        "item_states": _item_states(batch),
        "excluded_count": len(batch.get("excluded", [])),
    }


class ExecutiveBrain:
    """Read-only, deterministic facade; ``store`` and ``gateway`` are injected."""

    def __init__(self, *, gateway: Any = None, store: Any = None) -> None:
        self._gateway = gateway
        self._store = store

    def needs_action(self, *, limit: int = 100, now: datetime | None = None) -> dict[str, Any]:
        return applicants.needs_action(limit=limit, now=now)

    def suggestions(self, opening: str) -> dict[str, Any]:
        return applicants.suggestions(opening, gateway=self._gateway)

    def batch_status(self, batch_id: str) -> dict[str, Any]:
        if self._store is None:
            raise ValueError("no outbox store configured")
        return batch_status(self._store.load(batch_id))

    def batches(self) -> list[dict[str, Any]]:
        """Status of every stored batch, when the store can list them."""
        if self._store is None or not hasattr(self._store, "list_batches"):
            return []
        return sorted(
            (batch_status(b) for b in self._store.list_batches()),
            key=lambda s: str(s["batch_id"]),
        )

    def briefing(self, opening: str | None = None, *, now: datetime | None = None) -> dict[str, Any]:
        """One deterministic snapshot; suggestions only when ``opening`` is given."""
        out: dict[str, Any] = {"needs_action": self.needs_action(now=now), "batches": self.batches()}
        if opening:
            out["suggestions"] = self.suggestions(opening)
        return out


def build_prompt(briefing: Mapping[str, Any], *, question: str = "") -> str:
    """Format a briefing into prompt text from whitelisted fields only.

    Pure string construction: it performs no model call and no Dashboard access.
    """
    lines = ["Applicant Executive briefing (advisory; the operator decides)."]
    needs = briefing.get("needs_action") or {}
    for group in needs.get("groups", []):
        lines.append(f"Needs action: {group.get('reason')} ({group.get('count')}): {group.get('next_step')}")
        for item in group.get("items", []):
            lines.append("  - " + "; ".join(f"{k}={item.get(k)}" for k in _PROMPT_ITEM_FIELDS))
    sug = briefing.get("suggestions") or {}
    if sug:
        lines.append(f"{sug.get('label')} for opening {sug.get('opening')}:")
        for entry in sug.get("suggestions", []):
            lines.append("  - " + "; ".join(f"{k}={entry.get(k)}" for k in _PROMPT_SUGGESTION_FIELDS))
        lines.append(f"Matching applicants without a review: {sug.get('unreviewed_matching_count')}")
    for batch in briefing.get("batches", []):
        lines.append(f"Batch {batch.get('batch_id')}: {batch.get('state')} {batch.get('item_states')}")
    if question:
        lines.append(f"Question: {question}")
    return "\n".join(lines)
