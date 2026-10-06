"""Actions for reviewing staged candidate memories in the Executive window."""

from __future__ import annotations

from typing import Any, Callable

from ... import candidates
from . import registry

STATUS: Callable[[str], dict[str, Any]] | None = None
CURATE: Callable[..., dict[str, Any]] | None = None


def _record(item: dict[str, Any]) -> tuple[str, str, dict[str, Any]]:
    context = item.get("context") or {}
    project = context.get("project")
    cid = context.get("candidate_id")
    if not project or not cid:
        raise ValueError("missing candidate context")
    status = (STATUS or candidates.candidate_status)(project)
    record = next((candidate for candidate in status.get("candidates", []) if candidate.get("id") == cid), None)
    if record is None:
        raise ValueError(f"unknown candidate: {cid}")
    state = record.get("status")
    if state != "candidate":
        raise ValueError(f"candidate already {state}")
    return project, cid, record


def _curate(item: dict[str, Any], params: dict[str, Any], *, confirm: bool, action: str) -> dict[str, Any]:
    project, cid, record = _record(item)
    if confirm:
        return {"project": project, "candidate_id": cid, "action": action,
                "curation": (CURATE or candidates.curate_candidates)(project, [cid], action)}
    note = (
        "Promotes this candidate if it passes the curator checks (evidence, confidence >= 0.7, non-material kind)."
        if action == "promote"
        else "Marks this candidate rejected; nothing is promoted."
    )
    return {
        "project": project,
        "candidate_id": cid,
        "action": action,
        "candidate": {key: record.get(key) for key in ("kind", "statement", "evidence", "confidence", "task_summary")},
        "note": note,
    }


def _accept(item: dict[str, Any], params: dict[str, Any], *, confirm: bool) -> dict[str, Any]:
    return _curate(item, params, confirm=confirm, action="promote")


def _reject(item: dict[str, Any], params: dict[str, Any], *, confirm: bool) -> dict[str, Any]:
    return _curate(item, params, confirm=confirm, action="reject")


def register(reg: registry.Registry) -> None:
    reg.register_action(
        "candidate.accept", "Accept", ["memory_candidate"], _accept,
        consequential=True,
        description="Promote a staged candidate memory after Confirm (curator checks still apply)",
        params_schema={},
    )
    reg.register_action(
        "candidate.reject", "Reject", ["memory_candidate"], _reject,
        consequential=True,
        description="Reject a staged candidate memory after Confirm",
        params_schema={},
    )
