"""Staged candidate memories as items in the Executive window."""

from __future__ import annotations

from typing import Callable

from ... import candidates, registry as project_registry


PROJECTS: Callable[[], list[str]] | None = None
STATUS: Callable[[str], dict] | None = None


def candidate_items() -> list[dict]:
    """Return unresolved staged candidate memories in window item format."""
    projects = PROJECTS or (lambda: [p["id"] for p in project_registry.canonical_projects()])
    status = STATUS or candidates.candidate_status
    items: list[dict] = []
    for pid in sorted(projects()):
        try:
            result = status(pid)
        except (KeyError, ValueError, OSError):
            continue
        records = sorted(
            (record for record in result["candidates"] if record.get("status") == "candidate"),
            key=lambda record: record["id"],
        )
        for record in records:
            items.append({
                "id": f"candidate:{pid}:{record['id']}",
                "kind": "memory_candidate",
                "title": record["statement"],
                "tab": "work",
                "source": "Candidate memory",
                "sensitivity": "personal",
                "why": f"{record['kind']} staged from: {record.get('task_summary') or 'unknown'}",
                "context": {
                    "project": pid,
                    "candidate_id": record["id"],
                    "kind": record["kind"],
                    "evidence": list(record.get("evidence") or []),
                    "confidence": record.get("confidence"),
                },
            })
    return items
