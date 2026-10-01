"""The sole boundary between Applicant Executive and the Applicant Dashboard."""

from __future__ import annotations

import importlib
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Protocol

from agent_os import rtec_applicants


_APPLICANT_FIELDS = ("name", "position", "submitted", "status", "county", "city")
_MATCH_FIELDS = ("match", "pending", "primary", "alternates", "reasons", "groups", "group_label", "manager")
_REVIEW_FIELDS = ("summary", "strengths", "concerns")
_REVIEWABLE = {"New", "Interested", "Interview Requested", "Clarification Requested"}


def _value(obj: Any, key: str, default: Any = None) -> Any:
    return obj.get(key, default) if isinstance(obj, dict) else getattr(obj, key, default)


def _project(applicant: Any) -> dict[str, Any]:
    """Allow only ordinary recruiting fields to cross the gateway."""
    ref = _value(applicant, "applicant_ref") or _value(applicant, "agent_ref")
    if not ref:
        raise ValueError("Dashboard applicant has no opaque applicant_ref")
    result = {"applicant_ref": str(ref)}
    result.update({key: _value(applicant, key) for key in _APPLICANT_FIELDS})
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
            refs_by_key = {
                row["applicant_key"]: row["agent_ref"]
                for row in conn.execute("SELECT applicant_key, agent_ref FROM applicants")
            }
        finally:
            conn.close()
        result = []
        for applicant, review in rows:
            if _value(applicant, "status") not in _REVIEWABLE:
                continue
            ref = _value(applicant, "applicant_ref") or _value(applicant, "agent_ref")
            if not ref:
                key = _value(applicant, "applicant_key")
                if not key:
                    continue
                ref = refs_by_key.get(key)
            if not ref:
                continue
            safe = _project({"applicant_ref": ref, **{
                field: _value(applicant, field) for field in _APPLICANT_FIELDS
            }})
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


class SyntheticDashboardGateway:
    """In-memory gateway fixture with no imports from the Dashboard or Outlook."""

    def __init__(self, applicants: list[dict[str, Any]] | None = None,
                 reviews: dict[str, dict[str, Any]] | None = None,
                 managers: dict[str, Any] | None = None,
                 calendar: dict[Any, list[datetime]] | None = None) -> None:
        self.applicants = {str(a.get("applicant_ref") or a.get("agent_ref")): dict(a) for a in (applicants or [])}
        self.reviews = reviews or {}
        self.managers = managers or {}
        self.calendar = calendar or {}
        self.busy: dict[Any, list[tuple[datetime, datetime]]] = {}
        self.calls: list[tuple[str, tuple[Any, ...]]] = []
        self.drafts: list[dict[str, Any]] = []
        self.sent: list[dict[str, Any]] = []

    def _call(self, name: str, *args: Any) -> None:
        self.calls.append((name, args))

    def ranked(self, min_score: int = 0) -> list[tuple[dict[str, Any], dict[str, Any]]]:
        self._call("ranked", min_score)
        rows = [(_project(a), _review(self.reviews[ref])) for ref, a in self.applicants.items()
                if ref in self.reviews and a.get("status") in _REVIEWABLE
                and self.reviews[ref].get("score", 0) >= min_score]
        return sorted(rows, key=lambda row: row[1]["score"], reverse=True)

    def match_for(self, applicant: dict[str, Any]) -> dict[str, Any]:
        ref = _value(applicant, "applicant_ref")
        self._call("match_for", ref)
        match = self.applicants[ref].get("match", {})
        return {key: match.get(key) for key in _MATCH_FIELDS}

    def manager_for(self, applicant: dict[str, Any]) -> Any:
        ref = _value(applicant, "applicant_ref")
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
