from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from .registry import get_project


_PROJECT_ID = "job-applicant-dashboard"
_HEALTH_RELATIVE = Path("Config") / "fillout_sync_health.json"
_DB_NAME = "dashboard.db"

# Explicit allowlists.  Never replace these with SELECT *: dashboard.db also
# contains local file paths, restricted-form references, free-text notes and
# other fields that ordinary Agent OS applicant tools do not need.
_LIST_COLUMNS = (
    "agent_ref",
    "name",
    "position",
    "submitted",
    "status",
    "county",
    "city",
    "county_preference",
)
_SUMMARY_COLUMNS = (
    "agent_ref",
    "name",
    "position",
    "submitted",
    "email",
    "status",
    "county",
    "city",
    "county_preference",
    "pdf_path",
    "resume_path",
    "aa_pdf_path",
    "denial_email_drafted_at",
    "denial_email_sent_at",
    "updated_at",
)
_ALLOWED_STATUSES = {
    "New",
    "Interested",
    "Interview Requested",
    "Clarification Requested",
    "Interviewing",
    "Offered",
    "Denied",
    "Disqualified",
    "Hired",
    "Inactive",
}


def _project_root() -> Path:
    return Path(get_project(_PROJECT_ID)["path"])


def _db_path() -> Path:
    return _project_root() / _DB_NAME


def _health_path() -> Path:
    return _project_root() / _HEALTH_RELATIVE


def _connect_readonly() -> sqlite3.Connection:
    path = _db_path()
    if not path.is_file():
        raise FileNotFoundError(f"Applicant Dashboard database not found: {path}")
    uri = path.resolve().as_uri() + "?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def _table_columns(conn: sqlite3.Connection, table: str) -> set[str]:
    return {str(row["name"]) for row in conn.execute(f"PRAGMA table_info({table})")}


def _existing_columns(conn: sqlite3.Connection, desired: tuple[str, ...]) -> tuple[str, ...]:
    present = _table_columns(conn, "applicants")
    return tuple(column for column in desired if column in present)


def _require_agent_ref_schema(conn: sqlite3.Connection) -> None:
    """Fail closed until the Dashboard has migrated opaque Agent references."""
    if "agent_ref" not in _table_columns(conn, "applicants"):
        raise RuntimeError(
            "Applicant Dashboard schema is not ready for Agent OS access. "
            "Launch/update the Dashboard once so the opaque agent_ref migration runs."
        )


def _bounded_limit(limit: int) -> int:
    return max(1, min(int(limit), 200))


def _clean_status(status: str | None) -> str | None:
    if status in (None, "", "All"):
        return None
    if status not in _ALLOWED_STATUSES:
        raise ValueError(f"Unsupported applicant status: {status}")
    return status


def _row_projection(row: sqlite3.Row) -> dict[str, Any]:
    return {key: row[key] for key in row.keys()}


def list_applicants(status: str | None = None, limit: int = 50, offset: int = 0) -> dict[str, Any]:
    """List normalized applicant workflow records without documents or notes."""
    status = _clean_status(status)
    limit = _bounded_limit(limit)
    offset = max(0, int(offset))
    conn = _connect_readonly()
    try:
        _require_agent_ref_schema(conn)
        columns = _existing_columns(conn, _LIST_COLUMNS)
        if not columns:
            return {"count": 0, "results": [], "status_filter": status}
        select = ", ".join(columns)
        if status:
            rows = conn.execute(
                f"SELECT {select} FROM applicants WHERE status = ? "
                "ORDER BY submitted DESC LIMIT ? OFFSET ?",
                (status, limit, offset),
            ).fetchall()
        else:
            rows = conn.execute(
                f"SELECT {select} FROM applicants "
                "ORDER BY submitted DESC LIMIT ? OFFSET ?",
                (limit, offset),
            ).fetchall()
        return {
            "count": len(rows),
            "results": [_row_projection(row) for row in rows],
            "status_filter": status,
            "limit": limit,
            "offset": offset,
        }
    finally:
        conn.close()


def search_applicants(query: str, status: str | None = None, limit: int = 50) -> dict[str, Any]:
    """Search basic administrative fields only.

    This is not a ranking function. Results are ordered by submission time,
    never by an inferred candidate score.
    """
    query = str(query or "").strip()
    if not query:
        return list_applicants(status=status, limit=limit)
    status = _clean_status(status)
    limit = _bounded_limit(limit)
    conn = _connect_readonly()
    try:
        _require_agent_ref_schema(conn)
        columns = _existing_columns(conn, _LIST_COLUMNS)
        present = _table_columns(conn, "applicants")
        searchable = [
            column
            for column in ("name", "position", "county", "city", "county_preference")
            if column in present
        ]
        if not columns or not searchable:
            return {"count": 0, "results": [], "query": query, "status_filter": status}
        where = "(" + " OR ".join(f"COALESCE({column}, '') LIKE ?" for column in searchable) + ")"
        params: list[Any] = [f"%{query}%"] * len(searchable)
        if status:
            where += " AND status = ?"
            params.append(status)
        params.append(limit)
        rows = conn.execute(
            f"SELECT {', '.join(columns)} FROM applicants WHERE {where} "
            "ORDER BY submitted DESC LIMIT ?",
            params,
        ).fetchall()
        return {
            "count": len(rows),
            "results": [_row_projection(row) for row in rows],
            "query": query,
            "status_filter": status,
        }
    finally:
        conn.close()


def get_summary(applicant_ref: str) -> dict[str, Any] | None:
    """Return one minimum-necessary administrative applicant summary.

    Local file paths and restricted-form locations are reduced to presence
    booleans. Free-text notes, denial/disqualification reasons, screening
    flags and restricted self-identification data are deliberately excluded.
    """
    ref = str(applicant_ref or "").strip()
    if not ref:
        raise ValueError("applicant_ref is required")
    conn = _connect_readonly()
    try:
        _require_agent_ref_schema(conn)
        columns = _existing_columns(conn, _SUMMARY_COLUMNS)
        row = conn.execute(
            f"SELECT {', '.join(columns)} FROM applicants WHERE agent_ref = ?",
            (ref,),
        ).fetchone()
        if row is None:
            return None
        raw = _row_projection(row)
    finally:
        conn.close()

    return {
        "applicant_ref": raw.get("agent_ref", ref),
        "name": raw.get("name", ""),
        "position": raw.get("position", ""),
        "submitted": raw.get("submitted", ""),
        "email": raw.get("email", ""),
        "status": raw.get("status", ""),
        "county": raw.get("county", ""),
        "city": raw.get("city", ""),
        "county_preference": raw.get("county_preference", ""),
        "documents": {
            "application_present": bool(raw.get("pdf_path")),
            "resume_present": bool(raw.get("resume_path")),
            # Boolean only: ordinary applicant tools never expose the separate
            # restricted document path or its contents.
            "restricted_compliance_form_present": bool(raw.get("aa_pdf_path")),
        },
        "communication_state": {
            "draft_prepared": bool(raw.get("denial_email_drafted_at")),
            "send_confirmed": bool(raw.get("denial_email_sent_at")),
        },
        "updated_at": raw.get("updated_at", ""),
    }


def get_status(applicant_ref: str) -> dict[str, Any] | None:
    summary = get_summary(applicant_ref)
    if summary is None:
        return None
    return {
        "applicant_ref": summary["applicant_ref"],
        "status": summary["status"],
        "updated_at": summary["updated_at"],
        "communication_state": summary["communication_state"],
    }


def pending_actions(limit: int = 100) -> dict[str, Any]:
    """Return administrative follow-up states, not employment recommendations."""
    rows = list_applicants(limit=_bounded_limit(limit))["results"]
    results: list[dict[str, Any]] = []
    for row in rows:
        status = row.get("status")
        action = None
        if status == "New":
            action = "human_review_pending"
        elif status == "Interested":
            action = "user_selected_for_follow_up"
        elif status == "Interview Requested":
            action = "interview_request_outstanding"
        elif status == "Clarification Requested":
            action = "clarification_response_outstanding"
        elif status == "Offered":
            action = "offer_response_outstanding"
        if action:
            results.append(
                {
                    "applicant_ref": row.get("agent_ref"),
                    "name": row.get("name"),
                    "position": row.get("position"),
                    "submitted": row.get("submitted"),
                    "status": status,
                    "administrative_action": action,
                }
            )
    return {"count": len(results), "results": results}


def sync_status() -> dict[str, Any]:
    """Return source health + outbox health without applicant rows."""
    root = _project_root()
    health: dict[str, Any] = {
        "provider": "fillout_via_google_bridge",
        "status": "unknown",
        "health_file_present": False,
    }
    path = _health_path()
    if path.is_file():
        try:
            loaded = json.loads(path.read_text(encoding="utf-8"))
            allowed = {
                "schema_version",
                "provider",
                "status",
                "last_check_at",
                "last_success_at",
                "processed_count",
                "warning_count",
                "error_class",
                "source_row_count",
                "header_column_count",
                "header_sha256",
                "source_config_sha256",
            }
            if isinstance(loaded, dict):
                health.update({key: loaded.get(key) for key in allowed if key in loaded})
                health["health_file_present"] = True
        except (OSError, UnicodeError, json.JSONDecodeError):
            health.update({"status": "degraded", "health_read_error": True})

    db_path = root / _DB_NAME
    health["database_present"] = db_path.is_file()
    if not db_path.is_file():
        health["status"] = "unavailable"
        health["outbox"] = {"pending_count": 0, "oldest_pending_at": None, "newest_pending_at": None}
        return health

    try:
        conn = _connect_readonly()
        try:
            tables = {
                str(row["name"])
                for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            }
            if "applicants" in tables:
                health["applicant_record_count"] = int(
                    conn.execute("SELECT COUNT(*) FROM applicants").fetchone()[0]
                )
                health["agent_ref_schema_ready"] = (
                    "agent_ref" in _table_columns(conn, "applicants")
                )
                if not health["agent_ref_schema_ready"] and health.get("status") != "unavailable":
                    health["status"] = "degraded"
            else:
                health["agent_ref_schema_ready"] = False
                if health.get("status") != "unavailable":
                    health["status"] = "degraded"
            if "agent_events" in tables:
                row = conn.execute(
                    "SELECT COUNT(*) AS pending_count, MIN(created_at) AS oldest_pending_at, "
                    "MAX(created_at) AS newest_pending_at "
                    "FROM agent_events WHERE acknowledged_at = ''"
                ).fetchone()
                health["outbox"] = {
                    "pending_count": int(row["pending_count"] or 0),
                    "oldest_pending_at": row["oldest_pending_at"],
                    "newest_pending_at": row["newest_pending_at"],
                }
            else:
                health["outbox"] = {
                    "pending_count": 0,
                    "oldest_pending_at": None,
                    "newest_pending_at": None,
                    "schema_present": False,
                }
                if health.get("status") != "unavailable":
                    health["status"] = "degraded"
        finally:
            conn.close()
    except sqlite3.Error:
        health["status"] = "degraded"
        health["database_read_error"] = True
    return health


def pending_events(limit: int = 100) -> dict[str, Any]:
    """Read pending outbox metadata using opaque applicant references only."""
    limit = _bounded_limit(limit)
    conn = _connect_readonly()
    try:
        tables = {
            str(row["name"])
            for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
        if "agent_events" not in tables:
            return {"count": 0, "results": [], "schema_ready": False}
        _require_agent_ref_schema(conn)
        rows = conn.execute(
            "SELECT e.event_id, a.agent_ref, e.event_type, e.source_component, "
            "e.created_at, e.payload_json, e.sensitivity "
            "FROM agent_events e LEFT JOIN applicants a "
            "ON a.applicant_key = e.applicant_key "
            "WHERE e.acknowledged_at = '' "
            "ORDER BY e.created_at, e.event_id LIMIT ?",
            (limit,),
        ).fetchall()
        results = []
        for row in rows:
            # If an event cannot resolve to an opaque ref, do not leak the
            # internal/filename-derived applicant_key as a fallback.
            if not row["agent_ref"]:
                continue
            payload: dict[str, Any] = {}
            try:
                parsed = json.loads(row["payload_json"] or "{}")
                if isinstance(parsed, dict):
                    payload = parsed
            except json.JSONDecodeError:
                pass
            results.append(
                {
                    "event_id": row["event_id"],
                    "applicant_ref": row["agent_ref"],
                    "event_type": row["event_type"],
                    "source_component": row["source_component"],
                    "created_at": row["created_at"],
                    "payload": payload,
                    "sensitivity": row["sensitivity"],
                }
            )
        return {"count": len(results), "results": results, "schema_ready": True}
    finally:
        conn.close()

def acknowledge_event(event_id: str) -> dict[str, Any]:
    """Acknowledge an integration event without changing applicant workflow state."""
    event_id = str(event_id or "").strip()
    if not event_id:
        raise ValueError("event_id is required")
    path = _db_path()
    if not path.is_file():
        return {"acknowledged": False, "reason": "database_unavailable"}

    # This one integration bookkeeping operation requires a writable connection.
    conn = sqlite3.connect(path)
    try:
        table = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='agent_events'"
        ).fetchone()
        if not table:
            return {"acknowledged": False, "reason": "outbox_schema_unavailable"}
        exists = conn.execute(
            "SELECT 1 FROM agent_events WHERE event_id = ?", (event_id,)
        ).fetchone()
        if not exists:
            return {"acknowledged": False, "reason": "event_not_found"}
        acknowledged_at = datetime.now().astimezone().isoformat(timespec="seconds")
        conn.execute(
            "UPDATE agent_events SET acknowledged_at = "
            "CASE WHEN acknowledged_at = '' THEN ? ELSE acknowledged_at END "
            "WHERE event_id = ?",
            (acknowledged_at, event_id),
        )
        conn.commit()
        return {"acknowledged": True, "event_id": event_id}
    finally:
        conn.close()
