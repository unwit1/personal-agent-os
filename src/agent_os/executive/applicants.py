"""Applicant Executive read flows and the outreach plan/approve steps.

Business logic stays in the RTEC Applicant Dashboard and is reached only through
a ``DashboardGateway``. This module never sees internal applicant keys, never
requests AI reviews, never writes Dashboard drafts and never sends mail.
Applicant identity is the opaque ``applicant_ref`` everywhere.
"""
from __future__ import annotations

import json
import uuid
from datetime import date, datetime, timedelta
from typing import Any, Iterable, Mapping

from .. import rtec_applicants

ADVISORY_LABEL = "Dashboard AI review: advisory; you decide"
REVIEWABLE_STATUSES = ("New", "Interested", "Interview Requested", "Clarification Requested")

PENDING_APPROVAL = "PENDING_APPROVAL"
APPROVED = "APPROVED"
DEFAULT_SLOT_COUNT = 3
DEFAULT_MAX_BATCH_AGE = timedelta(hours=24)

_NEXT_STEPS = {
    "human_review_pending": "Review the application and decide whether to follow up.",
    "user_selected_for_follow_up": "Plan interview outreach for operator approval.",
    "interview_request_outstanding": "Check whether the applicant has replied to the interview request.",
    "clarification_response_outstanding": "Check whether the applicant has answered the clarification request.",
    "offer_response_outstanding": "Check whether the applicant has responded to the offer.",
}
_GENERIC_NEXT_STEP = "Open the applicant in the Dashboard and complete the administrative follow-up."
_REASON_ORDER = list(_NEXT_STEPS)

# Whitelisted applicant fields that may appear in Executive output.
_VIEW_FIELDS = ("applicant_ref", "name", "position", "submitted", "status", "county", "city")


class ApprovalError(ValueError):
    """An approval request was unknown, stale, repeated, or incomplete."""


# ---------------------------------------------------------------- helpers


def _get(obj: Any, key: str, default: Any = None) -> Any:
    if isinstance(obj, Mapping):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _project(applicant: Any) -> dict[str, Any]:
    return {key: _get(applicant, key) for key in _VIEW_FIELDS}


def _parse_when(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime(value.year, value.month, value.day)
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip().replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        pass
    for fmt in ("%m/%d/%Y %H:%M:%S", "%m/%d/%Y %H:%M", "%m/%d/%Y"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None


def _age_days(submitted: Any, now: datetime) -> int | None:
    when = _parse_when(submitted)
    if when is None:
        return None
    if when.tzinfo is not None:
        when = when.astimezone().replace(tzinfo=None)
    return max(0, (now.replace(tzinfo=None) - when).days)


def _norm(value: Any) -> str:
    return " ".join(str(value or "").split()).casefold()


def _opening_name(value: Any) -> str:
    if isinstance(value, Mapping):
        for key in ("opening", "name", "title", "position"):
            if value.get(key):
                return _norm(value[key])
        return ""
    return _norm(value)


def _fits(match: Any, opening: str) -> bool:
    """Dashboard fit rule: opening is the match or an alternate; pending never fits."""
    if not match or _get(match, "pending"):
        return False
    wanted = _norm(opening)
    if _opening_name(_get(match, "match")) == wanted:
        return True
    return any(_opening_name(alt) == wanted for alt in (_get(match, "alternates") or []))


def _clean_opening(opening: Any) -> str:
    if not isinstance(opening, str) or not opening.strip():
        raise ValueError("opening must be a non-empty string")
    return opening.strip()


def _jsonable(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Mapping):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_jsonable(v) for v in value]
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return str(value)


def _default_gateway() -> Any:
    from .gateway import LocalDashboardGateway

    return LocalDashboardGateway()


_PAGE_SIZE = 200


def _reviewable_applicants() -> dict[str, dict[str, Any]]:
    """Read-only administrative list of applicants in reviewable statuses.

    Pages one unfiltered list (offset until a short page) and filters by status
    here. ``list_applicants`` writes its own ``applicant.list`` access audit per
    page; that is accepted and is separate from the one ``executive.*`` record
    written per view.
    """
    found: dict[str, dict[str, Any]] = {}
    offset = 0
    while True:
        rows = rtec_applicants.list_applicants(limit=_PAGE_SIZE, offset=offset)["results"]
        for row in rows:
            ref = row.get("agent_ref")
            if ref and row.get("status") in REVIEWABLE_STATUSES:
                found[ref] = {
                    "applicant_ref": ref,
                    "name": row.get("name"),
                    "position": row.get("position"),
                    "submitted": row.get("submitted"),
                    "status": row.get("status"),
                    "county": row.get("county"),
                    "city": row.get("city"),
                }
        if len(rows) < _PAGE_SIZE:
            return found
        offset += len(rows)


# ---------------------------------------------------------------- needs_action


def needs_action(*, limit: int = 100, now: datetime | None = None) -> dict[str, Any]:
    """Group administrative pending actions by reason, with age and next step."""
    now = now or datetime.now()
    pending = rtec_applicants.pending_actions(limit=limit)
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in pending.get("results", []):
        reason = row.get("administrative_action") or "unknown"
        grouped.setdefault(reason, []).append(
            {
                "applicant_ref": row.get("applicant_ref"),
                "name": row.get("name"),
                "position": row.get("position"),
                "status": row.get("status"),
                "submitted": row.get("submitted"),
                "age_days": _age_days(row.get("submitted"), now),
            }
        )
    order = {reason: i for i, reason in enumerate(_REASON_ORDER)}
    groups = []
    for reason in sorted(grouped, key=lambda r: (order.get(r, len(order)), r)):
        items = sorted(
            grouped[reason],
            key=lambda i: (-1 if i["age_days"] is None else i["age_days"]),
            reverse=True,
        )
        groups.append(
            {
                "reason": reason,
                "count": len(items),
                "next_step": _NEXT_STEPS.get(reason, _GENERIC_NEXT_STEP),
                "items": items,
            }
        )
    return {"count": sum(g["count"] for g in groups), "groups": groups}


# ---------------------------------------------------------------- suggestions


def _review_fields(review: Any) -> dict[str, Any]:
    detail = _get(review, "result_json") or {}
    if isinstance(detail, str):
        try:
            detail = json.loads(detail)
        except ValueError:
            detail = {}
    criteria = [
        {
            "criterion": _get(c, "criterion"),
            "met": _get(c, "met"),
            "evidence": _get(c, "evidence"),
        }
        for c in (_get(detail, "criteria") or _get(detail, "criteria_results") or [])
    ]
    return {
        "score": _get(review, "score"),
        "recommendation": _get(review, "recommendation"),
        "review_reasons": {
            "summary": _get(detail, "summary"),
            "strengths": list(_get(detail, "strengths") or []),
            "concerns": list(_get(detail, "concerns") or []),
            "criteria": criteria,
        },
    }


def suggestions(opening: str, *, gateway: Any = None) -> dict[str, Any]:
    """Existing Dashboard AI reviews for applicants fitting ``opening``, best first."""
    opening = _clean_opening(opening)
    gateway = gateway or _default_gateway()
    roster = _reviewable_applicants()
    ranked = gateway.ranked(0)

    results: list[dict[str, Any]] = []
    reviewed: set[str] = set()
    for applicant, review in ranked:
        ref = _get(applicant, "applicant_ref")
        if not ref:
            continue
        reviewed.add(ref)
        if _get(applicant, "status") not in REVIEWABLE_STATUSES:
            continue
        match = gateway.match_for(ref)
        if not _fits(match, opening):
            continue
        entry = _project(applicant)
        entry.update(_review_fields(review))
        entry["match_reasons"] = list(_get(match, "reasons") or [])
        entry["label"] = ADVISORY_LABEL
        results.append(entry)
    results.sort(key=lambda e: (e["score"] is None, -(e["score"] or 0)))

    unreviewed = 0
    for ref in roster:
        if ref in reviewed:
            continue
        if _fits(gateway.match_for(ref), opening):
            unreviewed += 1

    rtec_applicants._audit_access(
        "executive.suggestions", metadata={"result_count": len(results)}
    )
    return {
        "opening": opening,
        "label": ADVISORY_LABEL,
        "count": len(results),
        "unreviewed_matching_count": unreviewed,
        "suggestions": results,
    }


# ---------------------------------------------------------------- plan_outreach


def _slot_records(slots: Iterable[Any]) -> list[dict[str, Any]]:
    return [{"start": _jsonable(when), "reason": reason} for when, reason in slots]


def plan_outreach(
    applicant_refs: list[str],
    opening: str,
    interview_type: str,
    location: str,
    duration_minutes: int,
    *,
    gateway: Any = None,
    store: Any,
    slot_count: int = DEFAULT_SLOT_COUNT,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Create one PENDING_APPROVAL batch. No Dashboard write, no send."""
    opening = _clean_opening(opening)
    if isinstance(applicant_refs, str) or not applicant_refs:
        raise ValueError("applicant_refs must be a non-empty list")
    if any(not isinstance(r, str) or not r.strip() for r in applicant_refs):
        raise ValueError("applicant_refs must be opaque reference strings")
    if len(set(applicant_refs)) != len(applicant_refs):
        raise ValueError("applicant_refs contains duplicates")
    if int(duration_minutes) <= 0:
        raise ValueError("duration_minutes must be positive")

    gateway = gateway or _default_gateway()
    roster = _reviewable_applicants()
    known = {r for r in applicant_refs if r in roster}
    unknown = [r for r in applicant_refs if r not in known]
    if unknown:
        raise ValueError(f"unknown or non-reviewable applicant_ref: {unknown[0]}")

    items: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = []
    for ref in applicant_refs:
        applicant = roster[ref]
        match = gateway.match_for(ref)
        if not _fits(match, opening):
            excluded.append(
                {
                    "applicant_ref": ref,
                    "reason": "opening_mismatch",
                    "match_reasons": list(_get(match, "reasons") or []),
                }
            )
            continue
        manager = gateway.manager_for(ref)
        if not manager:
            excluded.append({"applicant_ref": ref, "reason": "no_manager"})
            continue
        slots = list(gateway.suggest_slots(manager, int(duration_minutes), slot_count))
        if not slots:
            excluded.append({"applicant_ref": ref, "reason": "no_slots"})
            continue
        subject, body = gateway.render_outreach(
            name=applicant["name"],
            position=opening,
            slots=slots,
            interview_type=interview_type,
            location=location,
            duration_minutes=int(duration_minutes),
            message="",
            county=applicant["county"],
        )
        items.append(
            {
                "applicant_ref": ref,
                "name": applicant["name"],
                "county": applicant["county"],
                "manager": _jsonable(manager),
                "slots": _slot_records(slots),
                "subject": subject,
                "body": body,
                "state": "PLANNED",
            }
        )
    if not items:
        raise ValueError("no applicant can be planned for this opening; no batch created")

    batch = {
        "batch_id": "batch-" + uuid.uuid4().hex[:12],
        "state": PENDING_APPROVAL,
        "opening": opening,
        "interview_type": interview_type,
        "location": location,
        "duration_minutes": int(duration_minutes),
        "created_at": (now or datetime.now()).isoformat(timespec="seconds"),
        "items": items,
        "excluded": excluded,
    }
    store.save(batch)
    return batch


# ---------------------------------------------------------------- approve_batch


def _as_when(value: Any) -> datetime:
    when = _parse_when(value)
    if when is None:
        raise ApprovalError(f"unreadable slot: {value!r}")
    return when


def _slot_key(value: Any) -> datetime:
    when = _as_when(value)
    if when.tzinfo is not None:
        when = when.astimezone().replace(tzinfo=None)
    return when


def approve_batch(
    batch_id: str,
    choices: Mapping[str, Any],
    *,
    gateway: Any = None,
    store: Any,
    now: datetime | None = None,
    max_age: timedelta = DEFAULT_MAX_BATCH_AGE,
) -> dict[str, Any]:
    """Record the operator's per-item choices and move the batch to APPROVED.

    ``choices`` maps every item's applicant_ref to ``"confirm"``, ``"drop"``, or
    a list of offered slot datetimes (ISO strings or datetimes). Approval does
    not authorize delivery.
    """
    gateway = gateway or _default_gateway()
    now = now or datetime.now()
    try:
        batch = store.load(batch_id)
    except KeyError:
        raise ApprovalError(f"unknown batch: {batch_id}") from None
    if batch["state"] != PENDING_APPROVAL:
        raise ApprovalError(f"batch {batch_id} is {batch['state']}, not {PENDING_APPROVAL}")
    created = _parse_when(batch.get("created_at"))
    if created is None or now.replace(tzinfo=None) - created.replace(tzinfo=None) > max_age:
        raise ApprovalError(f"batch {batch_id} is stale; plan outreach again")

    refs = [item["applicant_ref"] for item in batch["items"]]
    if not isinstance(choices, Mapping):
        raise ApprovalError("choices must map applicant_ref to a decision")
    extra = [r for r in choices if r not in refs]
    if extra:
        raise ApprovalError(f"choice for unknown item: {extra[0]}")
    missing = [r for r in refs if r not in choices]
    if missing:
        raise ApprovalError(f"explicit choice required for every item; missing: {missing[0]}")

    duration = batch["duration_minutes"]
    decided: list[dict[str, Any]] = []
    for item in batch["items"]:
        ref = item["applicant_ref"]
        choice = choices[ref]
        out = dict(item)
        if choice == "drop":
            out.update(state="DROPPED", decision="dropped")
            decided.append(out)
            continue

        match = gateway.match_for(ref)
        if not _fits(match, batch["opening"]):
            out.update(state="HELD", decision="held", hold_reason="opening_no_longer_fits")
            decided.append(out)
            continue

        manager = gateway.manager_for(ref)
        if not manager:
            out.update(state="HELD", decision="held", hold_reason="no_manager")
            decided.append(out)
            continue
        fresh = list(gateway.suggest_slots(manager, duration, max(DEFAULT_SLOT_COUNT, len(item["slots"]))))
        fresh_keys = {_slot_key(when): (when, reason) for when, reason in fresh}
        original = [_slot_key(s["start"]) for s in item["slots"]]
        if choice == "confirm":
            wanted, changed = original, False
        elif isinstance(choice, (list, tuple)) and choice:
            wanted = [_slot_key(c) for c in choice]
            changed = wanted != original
        else:
            raise ApprovalError(f"invalid choice for {ref}: use 'confirm', 'drop' or offered slots")
        if len(set(wanted)) != len(wanted):
            raise ApprovalError(f"duplicate slots chosen for {ref}")
        unavailable = [w for w in wanted if w not in fresh_keys]
        if unavailable:
            raise ApprovalError(
                f"slot no longer available for {ref}; choose from fresh suggestions: "
                + ", ".join(when.isoformat() for when, _ in fresh)
            )
        slots = [fresh_keys[w] for w in wanted]
        if changed:
            subject, body = gateway.render_outreach(
                name=item["name"],
                position=batch["opening"],
                slots=slots,
                interview_type=batch["interview_type"],
                location=batch["location"],
                duration_minutes=duration,
                message="",
                county=item.get("county"),
            )
            out.update(subject=subject, body=body)
        out.update(state="APPROVED", decision="changed" if changed else "confirmed", slots=_slot_records(slots))
        decided.append(out)

    if not any(i["state"] == "APPROVED" for i in decided):
        raise ApprovalError("no item retained; nothing to approve")

    batch["items"] = decided
    batch["state"] = APPROVED
    batch["approved_at"] = now.isoformat(timespec="seconds")
    store.save(batch)
    return batch
