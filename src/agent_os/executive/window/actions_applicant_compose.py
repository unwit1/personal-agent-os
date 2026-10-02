"""Compose-producing applicant actions: they draft an email and never send it."""
from __future__ import annotations

from typing import Any

from . import actions_executive, registry

KINDS = ["county_openings"]
SCHEMA = {"applicant_ref": "string"}
DEFAULT_DURATION_MINUTES = 30
SLOT_COUNT = 3
NO_EMAIL_WARNING = "no email address on file for this applicant"


def _default_gateway() -> Any:
    return actions_executive._default_gateway()


def _get(row: Any, key: str) -> Any:
    return row.get(key) if isinstance(row, dict) else getattr(row, key, None)


def _find_entry(item: dict[str, Any], params: dict[str, Any]) -> dict[str, Any]:
    ref = str((params or {}).get("applicant_ref") or "").strip()
    if not ref:
        raise ValueError("applicant_ref is required")
    context = (item or {}).get("context") or {}
    for entry in context.get("applicants") or []:
        if entry.get("applicant_ref") == ref:
            return entry
    raise ValueError("applicant_ref is not in this county's applicants: " + ref)


def _county(item: dict[str, Any], entry: dict[str, Any]) -> str:
    context = (item or {}).get("context") or {}
    return str(context.get("county") or entry.get("county") or "").strip()


def _applicant_email(gateway: Any, ref: str) -> str:
    for applicant, _review in gateway.ranked(0):
        if _get(applicant, "applicant_ref") == ref:
            return str(_get(applicant, "email") or "").strip()
    return ""


def _compose(kind: str, to: str, subject: str, body: str, ref: str, county: str,
             warnings: list[str] | None = None) -> dict[str, Any]:
    compose: dict[str, Any] = {"to": to, "subject": subject, "body": body, "kind": kind,
                               "applicant_ref": ref}
    if county:
        compose["county"] = county
    if warnings:
        compose["warnings"] = warnings
    return {"compose": compose}


def _reach_out(item: dict[str, Any], params: dict[str, Any], *, confirm: bool) -> dict[str, Any]:
    entry = _find_entry(item, params)
    ref = entry["applicant_ref"]
    county = _county(item, entry)
    to = _applicant_email(_default_gateway(), ref)
    name = entry.get("name") or "there"
    position = entry.get("position") or "an open position"
    where = " in " + county + " County" if county else ""
    message = str(params.get("message") or "").strip()
    subject = "Your application for " + position
    body = ("Hello " + name + ",\n\nThank you for applying for " + position + where + ". "
            "We would like to learn more about you. Are you still interested, and when is a good "
            "time to talk?\n")
    if message:
        body += "\n" + message + "\n"
    return _compose("outreach", to, subject, body, ref, county, None if to else [NO_EMAIL_WARNING])


def _invite_interview(item: dict[str, Any], params: dict[str, Any], *, confirm: bool) -> dict[str, Any]:
    entry = _find_entry(item, params)
    ref = entry["applicant_ref"]
    county = _county(item, entry)
    gateway = _default_gateway()
    to = _applicant_email(gateway, ref)
    manager = gateway.manager_for(ref)
    if not manager:
        raise ValueError("no area manager found to schedule an interview for " + ref)
    slots = list(gateway.suggest_slots(manager, DEFAULT_DURATION_MINUTES, SLOT_COUNT))
    if not slots:
        raise ValueError("no interview slots available for " + ref)
    subject, body = gateway.render_outreach(
        name=entry.get("name") or "",
        position=entry.get("position") or "",
        slots=slots,
        interview_type=str(params.get("interview_type") or "phone"),
        location=str(params.get("location") or ""),
        duration_minutes=DEFAULT_DURATION_MINUTES,
        message="",
        county=county,
    )
    return _compose("interview", to, subject, body, ref, county, None if to else [NO_EMAIL_WARNING])


def _line(label: str, values: list[Any]) -> str:
    values = [str(v) for v in values if v]
    return "- " + label + ": " + "; ".join(values) if values else ""


def _manager_body(manager_name: str, county: str, entry: dict[str, Any], note: str) -> str:
    name = entry.get("name") or "An applicant"
    position = entry.get("position") or "an open position"
    reasons = entry.get("review_reasons") or {}
    criteria = []
    for c in reasons.get("criteria") or []:
        text = str(c.get("criterion")) + ": " + str(c.get("met"))
        if c.get("evidence"):
            text += " (" + str(c.get("evidence")) + ")"
        criteria.append(text)
    score, recommendation = entry.get("score"), entry.get("recommendation")
    head = []
    if score is not None:
        head.append("Score: " + str(score) + "/100")
    if recommendation:
        head.append("recommendation: " + str(recommendation))
    screening = [
        "- " + ", ".join(head) if head else "",
        "- Summary: " + str(reasons["summary"]) if reasons.get("summary") else "",
        _line("Strengths", reasons.get("strengths") or []),
        _line("Concerns", reasons.get("concerns") or []),
        _line("Criteria", criteria),
        _line("Match reasons", entry.get("match_reasons") or []),
    ]
    screening = [line for line in screening if line]
    parts = ["Hello " + (manager_name or "there") + ",", "",
             name + " applied for " + position + " and is a candidate for the " + county
             + " County opening.", ""]
    if screening:
        parts += ["Dashboard screening (advisory):", *screening, ""]
    if note:
        parts += [note, ""]
    tail = [
        "Submitted: " + str(entry["submitted"]) if entry.get("submitted") else "",
        "Status: " + str(entry["status"]) if entry.get("status") else "",
        "City: " + str(entry["city"]) if entry.get("city") else "",
    ]
    parts.append("   ".join(t for t in tail if t))
    return "\n".join(parts).rstrip() + "\n"


def _email_manager(item: dict[str, Any], params: dict[str, Any], *, confirm: bool) -> dict[str, Any]:
    entry = _find_entry(item, params)
    ref = entry["applicant_ref"]
    county = _county(item, entry)
    manager = _default_gateway().manager_for_county(county)
    to = str((manager or {}).get("email") or "").strip()
    if not to:
        raise ValueError("no area manager email found for " + county + " County")
    name = entry.get("name") or "applicant"
    position = entry.get("position") or "open position"
    subject = "Applicant for " + position + ": " + name + " (" + county + " County)"
    body = _manager_body(str((manager or {}).get("name") or ""), county, entry,
                         str(params.get("note") or "").strip())
    return _compose("manager", to, subject, body, ref, county)


def register(reg: registry.Registry) -> None:
    reg.register_action("applicant.reach_out", "Reach out", KINDS, _reach_out,
                        consequential=False,
                        description="Draft an outreach email to the applicant (compose only)",
                        params_schema=dict(SCHEMA, message="string"))
    reg.register_action("applicant.invite_interview", "Invite to interview", KINDS,
                        _invite_interview, consequential=False,
                        description="Draft an interview invitation with suggested slots (compose only)",
                        params_schema=dict(SCHEMA, interview_type="string", location="string"))
    reg.register_action("applicant.email_manager", "Email county manager", KINDS, _email_manager,
                        consequential=False,
                        description="Draft an email to the county's area manager with the "
                                    "applicant's Dashboard criteria",
                        params_schema=dict(SCHEMA, note="string"))
