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
    return {"batch_id": batch["batch_id"], "count": len(batch["items"])}


def _approve_batch(item: dict[str, Any], params: dict[str, Any], *, confirm: bool) -> dict[str, Any]:
    """Approve a pending batch with operator choices for each applicant.

    params: batch_id, choices (dict of applicant_ref -> "confirm", "drop", or list of slot times)
    """
    batch_id = params.get("batch_id", "")
    choices = params.get("choices", {})

    gateway = _default_gateway()
    store = _default_store()

    batch = ex.approve_batch(
        batch_id,
        choices,
        gateway=gateway,
        store=store,
    )
    return {"batch_id": batch["batch_id"], "state": batch["state"]}


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


def register(reg: registry.Registry) -> None:
    """Register the three applicant executive actions with the registry."""
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
        consequential=False,
        description="Approve a pending batch with per-applicant decisions",
    )

    reg.register_action(
        "executive.reach_out",
        "Send Outreach",
        ["applicant_group"],
        _reach_out,
        consequential=True,
        description="Send approved interview outreach emails to applicants",
    )
