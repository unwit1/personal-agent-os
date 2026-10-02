"""Applicant review and individual decisions for the Executive window."""
from __future__ import annotations

from typing import Any, Callable

GATEWAY_FACTORY: Callable[[], Any] | None = None

ADVISORY_LABEL = "Dashboard AI review: advisory; you decide"
DECLINE_STATUS = "Denied"
HOLD_NOTE = "Held by operator (Executive window)"
DECLINE_NOTE = "Declined by operator (Executive window)"

AVAILABLE_DECISIONS = [
    {"decision": "reach_out", "action_id": "applicant.reach_out", "label": "Reach out"},
    {"decision": "invite_interview", "action_id": "applicant.invite_interview", "label": "Invite to interview"},
    {"decision": "email_manager", "action_id": "applicant.email_manager", "label": "Email county manager"},
    {"decision": "decline", "action_id": "applicant.decline", "label": "Decline"},
    {"decision": "hold", "action_id": "applicant.hold", "label": "Hold"},
]

_PARAMS_SCHEMA = {
    "type": "object",
    "properties": {
        "applicant_ref": {"type": "string", "description": "Opaque applicant reference from the county group"},
        "note": {"type": "string", "description": "Optional note for the Dashboard journal"},
    },
    "required": ["applicant_ref"],
}
_REVIEW_SCHEMA = {
    "type": "object",
    "properties": {"applicant_ref": _PARAMS_SCHEMA["properties"]["applicant_ref"]},
    "required": ["applicant_ref"],
}


def _gateway() -> Any:
    if GATEWAY_FACTORY is not None:
        return GATEWAY_FACTORY()
    from ..gateway import LocalDashboardGateway

    return LocalDashboardGateway()


def _ref(params: dict[str, Any]) -> str:
    ref = str(params.get("applicant_ref") or "").strip()
    if not ref:
        raise ValueError("applicant_ref is required")
    return ref


def _find(gateway: Any, ref: str) -> tuple[dict[str, Any], dict[str, Any]]:
    for applicant, review in gateway.ranked(0):
        if str(applicant.get("applicant_ref")) == ref:
            return applicant, review
    raise KeyError("Unknown applicant_ref")


def _review_panel(gateway: Any, ref: str) -> dict[str, Any]:
    applicant, review = _find(gateway, ref)
    detail = review.get("result_json") or {}
    match = gateway.match_for(ref) or {}
    panel = {
        "applicant_ref": ref,
        "name": applicant.get("name"),
        "position": applicant.get("position"),
        "status": applicant.get("status"),
        "submitted": applicant.get("submitted"),
        "county": applicant.get("county"),
        "city": applicant.get("city"),
        "email": applicant.get("email"),
        "score": review.get("score"),
        "recommendation": review.get("recommendation"),
        "summary": detail.get("summary"),
        "strengths": list(detail.get("strengths") or []),
        "concerns": list(detail.get("concerns") or []),
        "criteria": [
            {key: c.get(key) for key in ("criterion", "met", "evidence")}
            for c in (detail.get("criteria") or [])
        ],
        "match": {
            "match": match.get("match"),
            "alternates": list(match.get("alternates") or []),
            "reasons": match.get("reasons"),
            "group_label": match.get("group_label"),
        },
        "label": ADVISORY_LABEL,
        "available_decisions": [dict(d) for d in AVAILABLE_DECISIONS],
    }
    return _jsonable(panel)


def _jsonable(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_jsonable(v) for v in value]
    return str(value)


def applicant_review(item: dict[str, Any], params: dict[str, Any], *, confirm: bool) -> dict[str, Any]:
    return _review_panel(_gateway(), _ref(params))


def _decision(status: str | None, default_note: str, key: str) -> Callable[..., dict[str, Any]]:
    def handler(item: dict[str, Any], params: dict[str, Any], *, confirm: bool) -> dict[str, Any]:
        ref = _ref(params)
        gateway = _gateway()
        applicant, _review = _find(gateway, ref)
        name = applicant.get("name")
        if not confirm:
            return {"applicant_ref": ref, "name": name, "new_status": status}
        note = " ".join(str(params.get("note") or "").split()) or default_note
        journal_id = gateway.set_applicant_status(ref, status, note)
        return {key: True, "applicant_ref": ref, "name": name, "new_status": status, "journal_id": journal_id}

    return handler


def register(reg: Any) -> None:
    reg.register_action(
        "applicant.review",
        "Review applicant",
        ["county_openings"],
        applicant_review,
        consequential=False,
        description="Show the allowlisted Dashboard review for an applicant and the available decisions",
        params_schema=_REVIEW_SCHEMA,
    )
    reg.register_action(
        "applicant.decline",
        "Decline applicant",
        ["county_openings"],
        _decision(DECLINE_STATUS, DECLINE_NOTE, "declined"),
        consequential=True,
        description="Set the applicant's Dashboard status to Denied (preview, then Confirm)",
        params_schema=_PARAMS_SCHEMA,
    )
    reg.register_action(
        "applicant.hold",
        "Hold applicant",
        ["county_openings"],
        _decision(None, HOLD_NOTE, "held"),
        consequential=True,
        description="Record a hold note in the Dashboard journal; status is unchanged (preview, then Confirm)",
        params_schema=_PARAMS_SCHEMA,
    )
