"""The sole boundary between Applicant Executive and the Applicant Dashboard."""

from __future__ import annotations

import importlib
import json
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Protocol

from agent_os import rtec_applicants


_APPLICANT_FIELDS = ("name", "position", "submitted", "status", "county", "city", "email")
_MATCH_FIELDS = ("match", "pending", "primary", "alternates", "reasons", "groups", "group_label", "manager")
_REVIEW_FIELDS = ("summary", "strengths", "concerns")
_REVIEWABLE = {"New", "Interested", "Interview Requested", "Clarification Requested"}
_SENT_KINDS = ("outreach", "interview", "manager")
_NOTE_LIMIT = 500
_OPENING_CHANGES = ("close", "quit", "new")
_COUNT_MAX = 20
_KEEP_INTERVIEW = {"Interviewing", "Offered", "Hired"}
SENT_STATUS_BY_KIND = {
    "outreach": ("Interested", "Outreach email sent (Executive window)"),
    "interview": ("Interview Requested", "Interview invitation sent (Executive window)"),
    "manager": (None, "Applicant details emailed to area manager (Executive window)"),
}


class DashboardGatewayError(RuntimeError):
    """The Dashboard or a needed Dashboard function is unavailable."""


def _status_after_send(kind: str, current: Any) -> str | None:
    target = SENT_STATUS_BY_KIND[kind][0]
    if kind == "outreach":
        return target if current == "New" else None
    if kind == "interview":
        return None if current in _KEEP_INTERVIEW or current == target else target
    return None


def _manager_view(manager: Any) -> dict[str, str] | None:
    if manager is None:
        return None
    name = str(_value(manager, "name", "") or "").strip()
    email = str(_value(manager, "email", "") or "").strip()
    return {"name": name, "email": email} if email else None


def _value(obj: Any, key: str, default: Any = None) -> Any:
    return obj.get(key, default) if isinstance(obj, dict) else getattr(obj, key, default)


def _project(applicant: Any) -> dict[str, Any]:
    """Allow only ordinary recruiting fields to cross the gateway."""
    ref = _value(applicant, "applicant_ref") or _value(applicant, "agent_ref")
    if not ref:
        raise ValueError("Dashboard applicant has no opaque applicant_ref")
    result = {"applicant_ref": str(ref)}
    result.update({key: _value(applicant, key) for key in _APPLICANT_FIELDS})
    if not result["county"]:
        result["county"] = _value(applicant, "county_preference")
    return result


def _review(review: Any) -> dict[str, Any]:
    raw = _value(review, "result_json") or {}
    if isinstance(raw, str):
        raw = json.loads(raw)
    if not isinstance(raw, dict):
        raw = {}
    result = {key: raw.get(key) for key in _REVIEW_FIELDS}
    criteria = raw.get("criteria", raw.get("per_criterion", []))
    if isinstance(criteria, list):
        result["criteria"] = [
            {key: item.get(key) for key in ("criterion", "met", "evidence")}
            for item in criteria if isinstance(item, dict)
        ]
    return {
        "score": _value(review, "score"),
        "recommendation": _value(review, "recommendation"),
        "result_json": result,
    }


def _county_name(county: Any) -> str:
    text = " ".join(str(county or "").split())
    if text.casefold().endswith(" county"):
        text = text[:-7].strip()
    if not text:
        raise ValueError("county is required")
    return text


def _opening_count(value: Any) -> int:
    if isinstance(value, dict):
        value = value.get("open_count", value.get("count", 0))
    try:
        return max(0, int(value or 0))
    except (TypeError, ValueError):
        return 0


def _group_text(group: Any) -> str | None:
    if isinstance(group, (list, tuple)):
        group = group[0] if group else None
    if isinstance(group, dict):
        group = group.get("group_label") or group.get("label") or group.get("name")
    return str(group) if group else None


def _opening_view(count: int, label: str | None) -> dict[str, Any]:
    return {"open": count > 0, "open_count": count, "group_label": label}


def _after_count(county: str, change: str, count: int, before: int) -> int:
    if change not in _OPENING_CHANGES:
        raise ValueError(f"Unknown opening change: {change}")
    if isinstance(count, bool) or not isinstance(count, int) or not 1 <= count <= _COUNT_MAX:
        raise ValueError(f"count must be 1 to {_COUNT_MAX}")
    if change == "close":
        if before < 1:
            raise ValueError(f"No open positions in {county} to close")
        return 0
    return before + count


def _opening_summary(county: str, change: str, before: int, after: int) -> str:
    lead = {"close": f"Closed the opening in {county} County",
            "quit": f"A driver quit in {county} County",
            "new": f"New opening in {county} County"}[change]
    return f"{lead}: openings {before} to {after}."


def _opening_preview(county: str, change: str, count: int, before: int, label: str | None) -> dict[str, Any]:
    after = _after_count(county, change, count, before)
    return {"county": county, "change": change, "count": count,
            "before": _opening_view(before, label),
            "after": _opening_view(after, label),
            "affects": [county], "summary": _opening_summary(county, change, before, after)}


def _opening_entry(state: dict[str, dict[str, Any]], county: str) -> dict[str, Any]:
    entry = state.get(_county_name(county).casefold())
    if entry is None:
        raise ValueError(f"Unknown county: {county}")
    return entry


class DashboardGateway(Protocol):
    def ranked(self, min_score: int = 0) -> list[tuple[dict[str, Any], dict[str, Any]]]: ...
    def match_for(self, applicant: dict[str, Any]) -> dict[str, Any]: ...
    def manager_for(self, applicant: dict[str, Any]) -> Any: ...
    def suggest_slots(self, manager: Any, duration_minutes: int, count: int) -> list[tuple[datetime, str]]: ...
    def render_outreach(self, name: str, position: str, slots: list[Any], interview_type: str,
                        location: str, duration_minutes: int, message: str, county: str) -> tuple[str, str]: ...
    def record_outreach_drafted(self, applicant_key: str, slots: list[Any], interview_type: str,
                                location: str, duration_minutes: int, draft_path: str, area_manager: Any) -> Any: ...
    def send_now(self, applicant_key: str, kind: str, to_addr: str, subject: str, body: str) -> Any: ...
    def record_applicant_sent(self, applicant_ref: str, kind: str, to_addr: str, subject: str) -> str: ...
    def set_applicant_status(self, applicant_ref: str, status: str | None, note: str) -> str: ...
    def manager_for_county(self, county: str) -> dict[str, str] | None: ...
    def open_counties(self, today: date | None = None) -> list[dict[str, Any]]: ...
    def preview_opening_change(self, county: str, change: str, *, count: int = 1) -> dict[str, Any]: ...
    def apply_opening_change(self, county: str, change: str, *, count: int = 1) -> dict[str, Any]: ...


class LocalDashboardGateway:
    """Lazy Dashboard adapter. Internal keys and raw rows never leave this module."""

    def __init__(self) -> None:
        self._raw_by_ref: dict[str, Any] = {}

    @staticmethod
    def _module(name: str) -> Any:
        root = Path(rtec_applicants._project_root())
        if not root.is_dir():
            raise FileNotFoundError("Applicant Dashboard checkout is unavailable")
        root_text = str(root)
        if root_text not in sys.path:
            sys.path.insert(0, root_text)
        return importlib.import_module(name)

    @staticmethod
    def _from_ref(ref: str) -> dict[str, Any]:
        if not ref:
            raise ValueError("applicant_ref is required")
        conn = rtec_applicants._connect_readonly()
        try:
            rtec_applicants._require_agent_ref_schema(conn)
            row = conn.execute(
                "SELECT * FROM applicants WHERE agent_ref = ?", (ref,)
            ).fetchone()
            if row is None:
                raise KeyError("Unknown applicant_ref")
            return dict(row)
        finally:
            conn.close()

    def _raw(self, applicant: dict[str, Any] | str) -> Any:
        ref = applicant if isinstance(applicant, str) else _value(applicant, "applicant_ref")
        if not ref:
            raise ValueError("applicant_ref is required")
        if ref not in self._raw_by_ref:
            self._raw_by_ref[ref] = self._from_ref(ref)
        return self._raw_by_ref[ref]

    def ranked(self, min_score: int = 0) -> list[tuple[dict[str, Any], dict[str, Any]]]:
        rows = self._module("candidate_review").ranked(min_score)
        conn = rtec_applicants._connect_readonly()
        try:
            rtec_applicants._require_agent_ref_schema(conn)
            contact_by_key = {
                row["applicant_key"]: dict(row)
                for row in conn.execute(
                    "SELECT applicant_key, agent_ref, email, county_preference FROM applicants"
                )
            }
        finally:
            conn.close()
        result = []
        for applicant, review in rows:
            if _value(applicant, "status") not in _REVIEWABLE:
                continue
            key = _value(applicant, "applicant_key")
            contact = contact_by_key.get(key, {})
            ref = _value(applicant, "applicant_ref") or _value(applicant, "agent_ref")
            if not ref:
                ref = contact.get("agent_ref")
            if not ref:
                continue
            public_fields = {
                field: _value(applicant, field) for field in (*_APPLICANT_FIELDS, "county_preference")
            }
            public_fields["email"] = public_fields["email"] or contact.get("email")
            if not public_fields["county"] and not public_fields["county_preference"]:
                public_fields["county_preference"] = contact.get("county_preference")
            safe = _project({"applicant_ref": ref, **public_fields})
            result.append((safe, _review(review)))
        return result

    def match_for(self, applicant: dict[str, Any]) -> dict[str, Any]:
        match = self._module("opening_match").match_for(self._raw(applicant))
        return {key: match.get(key) for key in _MATCH_FIELDS}

    def manager_for(self, applicant: dict[str, Any]) -> Any:
        return self._module("interview_calendar").manager_for_applicant(self._raw(applicant))

    def suggest_slots(self, manager: Any, duration_minutes: int, count: int) -> list[tuple[datetime, str]]:
        return self._module("interview_calendar").suggest_slots(manager, duration_minutes, count)

    def render_outreach(self, name: str, position: str, slots: list[Any], interview_type: str,
                        location: str, duration_minutes: int, message: str, county: str) -> tuple[str, str]:
        return self._module("interview_outreach").render_outreach(
            name, position, slots, interview_type, location, duration_minutes, message, county
        )

    def record_outreach_drafted(self, applicant_key: str, slots: list[Any], interview_type: str,
                                location: str, duration_minutes: int, draft_path: str, area_manager: Any) -> Any:
        key = self._raw(applicant_key)["applicant_key"]
        return self._module("interview_outreach").record_outreach_drafted(
            key, slots, interview_type, location, duration_minutes, draft_path, area_manager
        )

    def send_now(self, applicant_key: str, kind: str, to_addr: str, subject: str, body: str) -> Any:
        key = self._raw(applicant_key)["applicant_key"]
        return self._module("email_sender").send_now(key, kind, to_addr, subject, body)

    def _apply_status(self, key: str, status: str) -> None:
        database = self._module("database")
        for name in ("set_status", "update_applicant_status"):
            fn = getattr(database, name, None)
            if fn is not None:
                fn(key, status)
                return
        raise DashboardGatewayError("applicant status update is not available in this Dashboard checkout")

    def _journal(self, key: str, text: str) -> str:
        fn = getattr(self._module("database"), "add_journal_entry", None)
        if fn is None:
            raise DashboardGatewayError("applicant journal is not available in this Dashboard checkout")
        entry = fn(key, text)
        return "" if entry is None else str(entry)

    def record_applicant_sent(self, applicant_ref: str, kind: str, to_addr: str, subject: str) -> str:
        if kind not in _SENT_KINDS:
            raise ValueError(f"Unknown send kind: {kind}")
        raw = self._raw(applicant_ref)
        key = raw["applicant_key"]
        new_status = _status_after_send(kind, raw.get("status"))
        if new_status:
            self._apply_status(key, new_status)
        text = f"{SENT_STATUS_BY_KIND[kind][1]}: {subject} -> {to_addr}"
        return self._journal(key, text[:_NOTE_LIMIT])

    def set_applicant_status(self, applicant_ref: str, status: str | None, note: str) -> str:
        if status is not None and status not in rtec_applicants._ALLOWED_STATUSES:
            raise ValueError(f"Status not allowed: {status}")
        note = " ".join(str(note or "").split())
        if not note or len(note) > _NOTE_LIMIT:
            raise ValueError(f"note must be 1 to {_NOTE_LIMIT} characters")
        key = self._raw(applicant_ref)["applicant_key"]
        if status is not None:
            self._apply_status(key, status)
        return self._journal(key, note)

    def manager_for_county(self, county: str) -> dict[str, str] | None:
        if not str(county or "").strip():
            raise ValueError("county is required")
        fn = getattr(self._module("area_managers"), "manager_for_county", None)
        if fn is None:
            raise DashboardGatewayError("area manager lookup is not available in this Dashboard checkout")
        return _manager_view(fn(county))

    def _opening_state(self, today: date | None = None) -> tuple[Any, Any, dict[str, dict[str, Any]]]:
        openings = self._module("openings")
        for name in ("load_settings", "evaluate", "open_groups_in_range"):
            if getattr(openings, name, None) is None:
                raise DashboardGatewayError("openings lookup is not available in this Dashboard checkout")
        settings = openings.load_settings()
        evaluated = openings.evaluate(settings, today or date.today())
        if not isinstance(evaluated, dict):
            raise DashboardGatewayError("openings evaluate returned an unexpected shape")
        state: dict[str, dict[str, Any]] = {}
        for raw_name, value in evaluated.items():
            if not raw_name:
                continue
            name = _county_name(raw_name)
            count = _opening_count(value)
            label = _group_text(openings.open_groups_in_range(settings, name)) if count else None
            state[name.casefold()] = {"county": name, "open_count": count, "group_label": label}
        return openings, settings, state

    def open_counties(self, today: date | None = None) -> list[dict[str, Any]]:
        _, _, state = self._opening_state(today)
        rows = [dict(row) for row in state.values() if row["open_count"] >= 1]
        return sorted(rows, key=lambda row: row["county"].casefold())

    def preview_opening_change(self, county: str, change: str, *, count: int = 1) -> dict[str, Any]:
        _, _, state = self._opening_state()
        entry = _opening_entry(state, county)
        return _opening_preview(entry["county"], change, count, entry["open_count"], entry["group_label"])

    def apply_opening_change(self, county: str, change: str, *, count: int = 1) -> dict[str, Any]:
        _, _, state = self._opening_state()
        entry = _opening_entry(state, county)
        _opening_preview(entry["county"], change, count, entry["open_count"], entry["group_label"])
        # The Dashboard's settings structure for openings (transit_driver_groups, boolean per
        # group?) and its save function are not verified, so nothing is written until they are.
        raise DashboardGatewayError("openings save is not available in this Dashboard checkout")


class SyntheticDashboardGateway:
    """In-memory gateway fixture with no imports from the Dashboard or Outlook."""

    def __init__(self, applicants: list[dict[str, Any]] | None = None,
                 reviews: dict[str, dict[str, Any]] | None = None,
                 managers: dict[str, Any] | None = None,
                 calendar: dict[Any, list[datetime]] | None = None,
                 managers_by_county: dict[str, Any] | None = None,
                 openings: dict[str, Any] | None = None) -> None:
        self.applicants = {str(a.get("applicant_ref") or a.get("agent_ref")): dict(a) for a in (applicants or [])}
        self.reviews = reviews or {}
        self.managers = managers or {}
        self.calendar = calendar or {}
        self.busy: dict[Any, list[tuple[datetime, datetime]]] = {}
        self.calls: list[tuple[str, tuple[Any, ...]]] = []
        self.drafts: list[dict[str, Any]] = []
        self.sent: list[dict[str, Any]] = []
        self.managers_by_county = {str(k).casefold(): v for k, v in (managers_by_county or {}).items()}
        self.status_log: list[dict[str, Any]] = []
        self.openings: dict[str, dict[str, Any]] = {}
        for name, value in (openings or {}).items():
            label = value.get("group_label") if isinstance(value, dict) else None
            self.openings[_county_name(name)] = {"open_count": _opening_count(value), "group_label": label}

    def _call(self, name: str, *args: Any) -> None:
        self.calls.append((name, args))

    def ranked(self, min_score: int = 0) -> list[tuple[dict[str, Any], dict[str, Any]]]:
        self._call("ranked", min_score)
        rows = [(_project(a), _review(self.reviews[ref])) for ref, a in self.applicants.items()
                if ref in self.reviews and a.get("status") in _REVIEWABLE
                and self.reviews[ref].get("score", 0) >= min_score]
        return sorted(rows, key=lambda row: row[1]["score"], reverse=True)

    def match_for(self, applicant: dict[str, Any]) -> dict[str, Any]:
        ref = applicant if isinstance(applicant, str) else _value(applicant, "applicant_ref")
        self._call("match_for", ref)
        match = self.applicants[ref].get("match", {})
        return {key: match.get(key) for key in _MATCH_FIELDS}

    def manager_for(self, applicant: dict[str, Any]) -> Any:
        ref = applicant if isinstance(applicant, str) else _value(applicant, "applicant_ref")
        self._call("manager_for", ref)
        return self.managers.get(ref)

    def suggest_slots(self, manager: Any, duration_minutes: int, count: int) -> list[tuple[datetime, str]]:
        self._call("suggest_slots", manager, duration_minutes, count)
        duration = timedelta(minutes=duration_minutes)
        available = [slot for slot in self.calendar.get(manager, []) if all(
            slot + duration <= start or slot >= end for start, end in self.busy.get(manager, [])
        )]
        return [(slot, "available") for slot in sorted(available)[:count]]

    def render_outreach(self, name: str, position: str, slots: list[Any], interview_type: str,
                        location: str, duration_minutes: int, message: str, county: str) -> tuple[str, str]:
        self._call("render_outreach", name, position, slots, interview_type, location, duration_minutes, message, county)
        subject = f"Interview invitation: {position}"
        body = f"Hello {name},\n{message}\n{interview_type} at {location} ({duration_minutes} minutes).\n"
        body += "\n".join(str(slot) for slot in slots)
        return subject, body

    def record_outreach_drafted(self, applicant_key: str, slots: list[Any], interview_type: str,
                                location: str, duration_minutes: int, draft_path: str, area_manager: Any) -> str:
        self._call("record_outreach_drafted", applicant_key, slots, interview_type, location,
                   duration_minutes, draft_path, area_manager)
        if applicant_key not in self.applicants:
            raise KeyError("Unknown applicant_ref")
        draft_id = f"synthetic-draft-{len(self.drafts) + 1}"
        self.drafts.append({"id": draft_id, "applicant_ref": applicant_key})
        return draft_id

    def send_now(self, applicant_key: str, kind: str, to_addr: str, subject: str, body: str) -> str:
        self._call("send_now", applicant_key, kind, to_addr, subject, body)
        if applicant_key not in self.applicants:
            raise KeyError("Unknown applicant_ref")
        email_id = f"synthetic-email-{len(self.sent) + 1}"
        self.sent.append({"id": email_id, "applicant_ref": applicant_key, "kind": kind})
        return email_id

    def _log_status(self, ref: str, status: str | None, text: str) -> str:
        entry_id = f"synthetic-journal-{len(self.status_log) + 1}"
        self.status_log.append({"id": entry_id, "applicant_ref": ref, "status": status, "note": text})
        if status is not None:
            self.applicants[ref]["status"] = status
        return entry_id

    def record_applicant_sent(self, applicant_ref: str, kind: str, to_addr: str, subject: str) -> str:
        self._call("record_applicant_sent", applicant_ref, kind, to_addr, subject)
        if kind not in _SENT_KINDS:
            raise ValueError(f"Unknown send kind: {kind}")
        if applicant_ref not in self.applicants:
            raise KeyError("Unknown applicant_ref")
        new_status = _status_after_send(kind, self.applicants[applicant_ref].get("status"))
        text = f"{SENT_STATUS_BY_KIND[kind][1]}: {subject} -> {to_addr}"
        return self._log_status(applicant_ref, new_status, text[:_NOTE_LIMIT])

    def set_applicant_status(self, applicant_ref: str, status: str | None, note: str) -> str:
        self._call("set_applicant_status", applicant_ref, status, note)
        if status is not None and status not in rtec_applicants._ALLOWED_STATUSES:
            raise ValueError(f"Status not allowed: {status}")
        note = " ".join(str(note or "").split())
        if not note or len(note) > _NOTE_LIMIT:
            raise ValueError(f"note must be 1 to {_NOTE_LIMIT} characters")
        if applicant_ref not in self.applicants:
            raise KeyError("Unknown applicant_ref")
        return self._log_status(applicant_ref, status, note)

    def manager_for_county(self, county: str) -> dict[str, str] | None:
        self._call("manager_for_county", county)
        if not str(county or "").strip():
            raise ValueError("county is required")
        return _manager_view(self.managers_by_county.get(str(county).strip().casefold()))

    def _opening_lookup(self, county: str) -> tuple[str, dict[str, Any]]:
        county = _county_name(county)
        for name, entry in self.openings.items():
            if name.casefold() == county.casefold():
                return name, entry
        raise ValueError(f"Unknown county: {county}")

    def open_counties(self, today: date | None = None) -> list[dict[str, Any]]:
        self._call("open_counties", today)
        rows = [{"county": name, "open_count": e["open_count"], "group_label": e["group_label"]}
                for name, e in self.openings.items() if e["open_count"] >= 1]
        return sorted(rows, key=lambda row: row["county"].casefold())

    def preview_opening_change(self, county: str, change: str, *, count: int = 1) -> dict[str, Any]:
        self._call("preview_opening_change", county, change, count)
        name, entry = self._opening_lookup(county)
        return _opening_preview(name, change, count, entry["open_count"], entry["group_label"])

    def apply_opening_change(self, county: str, change: str, *, count: int = 1) -> dict[str, Any]:
        self._call("apply_opening_change", county, change, count)
        name, entry = self._opening_lookup(county)
        preview = _opening_preview(name, change, count, entry["open_count"], entry["group_label"])
        new_count = preview["after"]["open_count"]
        entry["open_count"] = new_count
        group = {"county": name, "open_count": new_count, "group_label": entry["group_label"]} if new_count else None
        return {"county": name, "change": change, "count": count, "applied": True,
                "before": preview["before"], "after": preview["after"], "group": group}
