"""Actions for the applicant executive: plan, approve, and reach out."""

from __future__ import annotations

from typing import Any, Callable

from .. import applicants as ex
from . import registry

GATEWAY_FACTORY: Callable[[], Any] = None
STORE_FACTORY: Callable[[], Any] = None


def _default_gateway() -> Any:
    if GATEWAY_FACTORY is not None:
        return GATEWAY_FACTORY()
    from ..gateway import LocalDashboardGateway
    return LocalDashboardGateway()


def _default_store() -> Any:
    if STORE_FACTORY is not None:
        return STORE_FACTORY()
    from ..outbox import OutboxStore
    return OutboxStore()


def _plan_interviews(item: dict[str, Any], params: dict[str, Any], *, confirm: bool) -> dict[str, Any]:
    """Plan interview outreach for applicants in a group.

    params: applicant_refs (list), opening, interview_type, location, duration_minutes
    """
    applicant_refs = params.get("applicant_refs", [])
    opening = params.get("opening", "")
    interview_type = params.get("interview_type", "")
    location = params.get("location", "")
    duration_minutes = params.get("duration_minutes", 0)

    gateway = _default_gateway()
    store = _default_store()

    batch = ex.plan_outreach(
        applicant_refs,
        opening,
        interview_type,
        location,
        int(duration_minutes),
        gateway=gateway,
        store=store,
    )
    return {
        "batch_id": batch["batch_id"],
        "state": batch["state"],
        "items": [ex._preview(i) | {"state": i["state"]} for i in batch["items"]],
        "excluded": batch.get("excluded", []),
    }


def approve_preview(batch_id: str, choices: Any, *, store: Any) -> dict[str, Any]:
    """What approving would record; reads the batch and changes nothing."""
    try:
        batch = store.load(batch_id)
    except KeyError:
        raise ex.ApprovalError(f"unknown batch: {batch_id}") from None
    if batch["state"] != ex.PENDING_APPROVAL:
        raise ex.ApprovalError(f"batch {batch_id} is {batch['state']}, not {ex.PENDING_APPROVAL}")
    return {
        "batch_id": batch["batch_id"],
        "state": batch["state"],
        "choices": choices,
        "items": [ex._preview(i) | {"state": i["state"]} for i in batch["items"]],
    }


def _approve_batch(item: dict[str, Any], params: dict[str, Any], *, confirm: bool) -> dict[str, Any]:
    """Approve a pending batch with operator choices for each applicant.

    params: batch_id, choices (dict of applicant_ref -> "confirm", "drop", or list of slot times)
    On confirm=False: previews the choices against the batch and changes nothing.
    On confirm=True: records the choices and moves the batch to APPROVED.
    """
    batch_id = params.get("batch_id", "")
    choices = params.get("choices", {})

    store = _default_store()
    if not confirm:
        return approve_preview(batch_id, choices, store=store)

    batch = ex.approve_batch(
        batch_id,
        choices,
        gateway=_default_gateway(),
        store=store,
    )
    return {
        "batch_id": batch["batch_id"],
        "state": batch["state"],
        "items": [ex._preview(i) | {"state": i["state"]} for i in batch["items"]],
        "excluded": batch.get("excluded", []),
    }


def _reach_out(item: dict[str, Any], params: dict[str, Any], *, confirm: bool) -> dict[str, Any]:
    """Send interview outreach emails.

    params: batch_id
    On confirm=False: returns preview without calling gateway.send_now
    On confirm=True: sends through gateway and returns summary
    """
    batch_id = params.get("batch_id", "")

    gateway = _default_gateway()
    store = _default_store()

    result = ex.send_batch(
        batch_id,
        confirm=confirm,
        gateway=gateway,
        store=store,
    )
    return result


def _send_batch(item: dict[str, Any], params: dict[str, Any], *, confirm: bool) -> dict[str, Any]:
    """Send an APPROVED batch; a dry-run until the operator clicks Confirm.

    params: batch_id
    """
    batch_id = params.get("batch_id", "")
    store = _default_store()
    if not confirm:
        return ex.send_batch(batch_id, confirm=False, store=store)
    return ex.send_batch(batch_id, confirm=True, gateway=_default_gateway(), store=store)


def _browser_execute(item: dict[str, Any], params: dict[str, Any], *, confirm: bool) -> dict[str, Any]:
    """Run browser actions with the consequential gate opened, only after Confirm.

    params: session_id, actions, issued_by, wait_seconds
    """
    if not confirm:
        return {
            "session_id": params.get("session_id"),
            "actions": params.get("actions") or [],
            "approved_consequential": True,
        }
    from ... import browser_control

    return browser_control.execute(
        str(params.get("session_id") or ""),
        list(params.get("actions") or []),
        issued_by=str(params.get("issued_by") or "agent-os"),
        approved_consequential=True,
        wait_seconds=params.get("wait_seconds", browser_control.DEFAULT_WAIT_SECONDS),
    )


def register(reg: registry.Registry) -> None:
    """Register the applicant executive actions with the registry."""
    reg.register_action(
        "executive.plan_interviews",
        "Plan Interviews",
        ["applicant_group"],
        _plan_interviews,
        consequential=False,
        description="Create a batch of interview outreach for selected applicants",
    )

    reg.register_action(
        "executive.approve_batch",
        "Approve Batch",
        ["applicant_group"],
        _approve_batch,
        consequential=True,
        description="Approve a pending batch with per-applicant decisions",
    )

    # Model-requested consequential steps (MCP executive.send with confirm_send,
    # browser.execute with approved_consequential) land here as pending records;
    # only the operator's Confirm runs them. No provider emits these item kinds.
    reg.register_action(
        "executive.send_batch",
        "Send Batch",
        ["executive_batch"],
        _send_batch,
        consequential=True,
        description="Send an approved interview outreach batch",
    )

    reg.register_action(
        "browser.execute_consequential",
        "Run Browser Action",
        ["browser_command"],
        _browser_execute,
        consequential=True,
        description="Run browser actions that the browser safety gate paused",
    )

    # executive.reach_out is not registered: after a batch is approved each
    # applicant is sent with applicant.reach_out (compose, then Send).
