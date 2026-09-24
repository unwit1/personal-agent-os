from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from .registry import get_project
from .paths import ROOT


_PROJECT_ID = "job-applicant-dashboard"
_HEALTH_RELATIVE = Path("Config") / "fillout_sync_health.json"
_OPENINGS_RELATIVE = Path("Config") / "openings_settings.json"
_PATHS_RELATIVE = Path("Config") / "paths_settings.json"
_DB_NAME = "dashboard.db"
_AUDIT_PATH = ROOT / ".agent-local" / "rtec-applicant-access.jsonl"
_AUDIT_MAX_ROWS = 10000
_AUDIT_METADATA_KEYS = {
    "result_count",
    "status_filter",
    "limit",
    "offset",
    "found",
    "query_present",
    "query_length",
    "event_count",
    "schema_ready",
    "configured",
    "transit_group_count",
    "office_position_count",
    "status",
    "database_present",
    "agent_ref_schema_ready",
    "pending_event_count",
    "acknowledged",
    "reason",
}

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


def _audit_access(action: str, *, applicant_ref: str | None = None,
                  metadata: dict[str, Any] | None = None) -> None:
    """Persist a privacy-safe local audit entry or fail closed.

    Applicant-bearing adapter reads depend on this succeeding. The record may
    contain the opaque agent_ref and coarse operational metadata, but never
    names, email addresses, search text, notes, filenames/paths, source keys,
    document content, or restricted self-ID data.
    """
    import os
    import uuid

    safe_metadata: dict[str, Any] = {}
    for key, value in (metadata or {}).items():
        if not isinstance(key, str) or key not in _AUDIT_METADATA_KEYS:
            continue
        if value is None or isinstance(value, (str, int, float, bool)):
            safe_metadata[key] = value

    entry = {
        "schema_version": 1,
        "audit_id": "audit-" + uuid.uuid4().hex,
        "created_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "action": str(action),
        "applicant_ref": applicant_ref or None,
        "metadata": safe_metadata,
    }

    try:
        _AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
        existing: list[str] = []
        if _AUDIT_PATH.exists():
            with _AUDIT_PATH.open("r", encoding="utf-8") as handle:
                existing = [line for line in handle if line.strip()]
        existing.append(json.dumps(entry, sort_keys=True, separators=(",", ":")) + "\n")
        existing = existing[-_AUDIT_MAX_ROWS:]
        tmp = _AUDIT_PATH.with_suffix(_AUDIT_PATH.suffix + ".tmp")
        with tmp.open("w", encoding="utf-8", newline="\n") as handle:
            handle.writelines(existing)
        os.replace(tmp, _AUDIT_PATH)
    except Exception as exc:
        raise RuntimeError(
            "Applicant access audit could not be recorded; access denied."
        ) from exc


def _audit_health(action: str, metadata: dict[str, Any] | None = None) -> None:
    """Best-effort audit for non-applicant health/configuration reads."""
    try:
        _audit_access(action, metadata=metadata)
    except RuntimeError:
        # Health/readiness checks contain no applicant rows; they remain useful
        # for diagnosing the audit subsystem itself.
        pass


def _project_root() -> Path:
    return Path(get_project(_PROJECT_ID)["path"])


def _db_path() -> Path:
    return _project_root() / _DB_NAME


def _health_path() -> Path:
    return _project_root() / _HEALTH_RELATIVE


def _load_local_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def _resolve_document_path(value: Any, kind: str) -> Path | None:
    text = str(value or "").strip()
    if not text:
        return None
    path = Path(text)
    if path.is_absolute():
        return path

    root = _project_root()
    paths = _load_local_json(root / _PATHS_RELATIVE)
    if kind in {"application", "resume"}:
        base = str(paths.get("applications_dir") or "").strip()
        if base:
            return Path(base) / path
    if kind == "restricted_compliance":
        base = str(paths.get("aap_forms_dir") or "").strip()
        if base:
            return Path(base) / path
    return root / path


def _file_metadata(
    value: Any,
    kind: str,
    include_type: bool = True,
    presence_only: bool = False,
) -> dict[str, Any]:
    path = _resolve_document_path(value, kind)
    present = bool(str(value or "").strip())
    result: dict[str, Any] = {"recorded": present, "exists": False}
    if path is None:
        return result
    try:
        stat = path.stat()
    except OSError:
        return result
    result["exists"] = path.is_file()
    if not result["exists"] or presence_only:
        return result
    result["size_bytes"] = int(stat.st_size)
    result["modified_at"] = datetime.fromtimestamp(
        stat.st_mtime
    ).astimezone().isoformat(timespec="seconds")
    if include_type:
        result["extension"] = path.suffix.lower()
    return result


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
            _audit_access(
                "applicant.list",
                metadata={
                    "result_count": 0,
                    "status_filter": status,
                    "limit": limit,
                    "offset": offset,
                },
            )
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
        result = {
            "count": len(rows),
            "results": [_row_projection(row) for row in rows],
            "status_filter": status,
            "limit": limit,
            "offset": offset,
        }
        _audit_access(
            "applicant.list",
            metadata={
                "result_count": len(rows),
                "status_filter": status,
                "limit": limit,
                "offset": offset,
            },
        )
        return result
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
            _audit_access(
                "applicant.search",
                metadata={
                    "result_count": 0,
                    "status_filter": status,
                    "query_present": True,
                    "query_length": len(query),
                    "limit": limit,
                },
            )
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
        result = {
            "count": len(rows),
            "results": [_row_projection(row) for row in rows],
            "query": query,
            "status_filter": status,
        }
        _audit_access(
            "applicant.search",
            metadata={
                "result_count": len(rows),
                "status_filter": status,
                "query_present": True,
                "query_length": len(query),
                "limit": limit,
            },
        )
        return result
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
            _audit_access(
                "applicant.get_summary",
                applicant_ref=ref,
                metadata={"found": False},
            )
            return None
        raw = _row_projection(row)
    finally:
        conn.close()

    _audit_access(
        "applicant.get_summary",
        applicant_ref=ref,
        metadata={"found": True},
    )
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


def get_document_metadata(applicant_ref: str) -> dict[str, Any] | None:
    """Return document presence/file metadata without paths or content."""
    ref = str(applicant_ref or "").strip()
    if not ref:
        raise ValueError("applicant_ref is required")
    conn = _connect_readonly()
    try:
        _require_agent_ref_schema(conn)
        present = _table_columns(conn, "applicants")
        desired = [
            column for column in ("agent_ref", "pdf_path", "resume_path", "aa_pdf_path")
            if column in present
        ]
        row = conn.execute(
            f"SELECT {', '.join(desired)} FROM applicants WHERE agent_ref = ?",
            (ref,),
        ).fetchone()
        if row is None:
            _audit_access(
                "applicant.get_document_metadata",
                applicant_ref=ref,
                metadata={"found": False},
            )
            return None
        raw = dict(row)
    finally:
        conn.close()

    _audit_access(
        "applicant.get_document_metadata",
        applicant_ref=ref,
        metadata={"found": True},
    )
    return {
        "applicant_ref": ref,
        "application": _file_metadata(raw.get("pdf_path"), "application"),
        "resume": _file_metadata(raw.get("resume_path"), "resume"),
        # Restricted form metadata is deliberately coarser: ordinary Agent
        # tools may know a compliance artifact exists but do not need its
        # filename, extension, path, size, or content.
        "restricted_compliance_form": _file_metadata(
            raw.get("aa_pdf_path"),
            "restricted_compliance",
            include_type=False,
            presence_only=True,
        ),
    }


def get_timeline(applicant_ref: str, limit: int = 100) -> dict[str, Any] | None:
    """Return metadata-only Dashboard events for one opaque applicant ref.

    Coverage begins when the local event-outbox migration was introduced; this
    is not a reconstruction of all earlier applicant history.
    """
    ref = str(applicant_ref or "").strip()
    if not ref:
        raise ValueError("applicant_ref is required")
    limit = _bounded_limit(limit)
    conn = _connect_readonly()
    try:
        tables = {
            str(row["name"])
            for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
        if "applicants" not in tables:
            return None
        _require_agent_ref_schema(conn)
        applicant = conn.execute(
            "SELECT applicant_key FROM applicants WHERE agent_ref = ?", (ref,)
        ).fetchone()
        if applicant is None:
            _audit_access(
                "applicant.get_timeline",
                applicant_ref=ref,
                metadata={"found": False},
            )
            return None
        if "agent_events" not in tables:
            _audit_access(
                "applicant.get_timeline",
                applicant_ref=ref,
                metadata={"found": True, "event_count": 0, "schema_ready": False},
            )
            return {
                "applicant_ref": ref,
                "count": 0,
                "events": [],
                "coverage": "outbox_schema_not_yet_available",
            }
        rows = conn.execute(
            "SELECT event_id, event_type, source_component, created_at, "
            "payload_json, sensitivity, acknowledged_at "
            "FROM agent_events WHERE applicant_key = ? "
            "ORDER BY created_at DESC, event_id DESC LIMIT ?",
            (applicant["applicant_key"], limit),
        ).fetchall()
    finally:
        conn.close()

    events = []
    for row in reversed(rows):
        payload: dict[str, Any] = {}
        try:
            parsed = json.loads(row["payload_json"] or "{}")
            if isinstance(parsed, dict):
                payload = parsed
        except json.JSONDecodeError:
            pass
        events.append(
            {
                "event_id": row["event_id"],
                "event_type": row["event_type"],
                "source_component": row["source_component"],
                "created_at": row["created_at"],
                "payload": payload,
                "sensitivity": row["sensitivity"],
                "acknowledged_at": row["acknowledged_at"] or None,
            }
        )
    _audit_access(
        "applicant.get_timeline",
        applicant_ref=ref,
        metadata={"found": True, "event_count": len(events), "schema_ready": True},
    )
    return {
        "applicant_ref": ref,
        "count": len(events),
        "events": events,
        "coverage": "events_recorded_since_outbox_migration_only",
    }


def openings_status() -> dict[str, Any]:
    """Return organization-level openings configuration, never candidate fit."""
    path = _project_root() / _OPENINGS_RELATIVE
    data = _load_local_json(path)
    if not data:
        _audit_health("applicant.openings", {"configured": False})
        return {
            "source": "dashboard_local_config",
            "configured": False,
            "transit_driver_groups": [],
            "office_positions": {},
        }

    groups = data.get("transit_driver_groups")
    if not isinstance(groups, list):
        groups = []
    groups = [str(item).strip() for item in groups if str(item).strip()]

    office = data.get("office_positions")
    if not isinstance(office, dict):
        office = {}
    office_safe = {
        str(key): bool(value)
        for key, value in office.items()
        if isinstance(key, str)
    }

    result: dict[str, Any] = {
        "source": "dashboard_local_config",
        "configured": True,
        "transit_driver_groups": sorted(set(groups), key=str.casefold),
        "office_positions": office_safe,
    }
    for key in ("max_drive_minutes", "nearby_offer_minutes"):
        value = data.get(key)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            result[key] = value
    try:
        result["config_modified_at"] = datetime.fromtimestamp(
            path.stat().st_mtime
        ).astimezone().isoformat(timespec="seconds")
    except OSError:
        pass
    _audit_health(
        "applicant.openings",
        {
            "configured": True,
            "transit_group_count": len(result["transit_driver_groups"]),
            "office_position_count": len(result["office_positions"]),
        },
    )
    return result


def get_status(applicant_ref: str) -> dict[str, Any] | None:
    summary = get_summary(applicant_ref)
    if summary is None:
        _audit_access(
            "applicant.get_status",
            applicant_ref=applicant_ref,
            metadata={"found": False},
        )
        return None
    _audit_access(
        "applicant.get_status",
        applicant_ref=applicant_ref,
        metadata={"found": True},
    )
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
    _audit_access(
        "applicant.pending_actions",
        metadata={"result_count": len(results), "limit": _bounded_limit(limit)},
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
                "last_transition_at",
                "processed_count",
                "warning_count",
                "error_class",
                "source_row_count",
                "source_modified_at",
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
        _audit_health("applicant.sync_status", {"status": health["status"]})
        _audit_health(
        "applicant.sync_status",
        {
            "status": health.get("status"),
            "database_present": bool(health.get("database_present")),
            "agent_ref_schema_ready": bool(health.get("agent_ref_schema_ready")),
            "pending_event_count": int((health.get("outbox") or {}).get("pending_count") or 0),
        },
    )
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
            _audit_access(
                "applicant.events",
                metadata={"result_count": 0, "schema_ready": False, "limit": limit},
            )
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
        _audit_access(
            "applicant.events",
            metadata={"result_count": len(results), "schema_ready": True, "limit": limit},
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
        _audit_access(
            "applicant.event_ack",
            metadata={"acknowledged": False, "reason": "database_unavailable"},
        )
        return {"acknowledged": False, "reason": "database_unavailable"}

    # This one integration bookkeeping operation requires a writable connection.
    conn = sqlite3.connect(path)
    try:
        table = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='agent_events'"
        ).fetchone()
        if not table:
            _audit_access(
                "applicant.event_ack",
                metadata={"acknowledged": False, "reason": "outbox_schema_unavailable"},
            )
            return {"acknowledged": False, "reason": "outbox_schema_unavailable"}
        exists = conn.execute(
            "SELECT 1 FROM agent_events WHERE event_id = ?", (event_id,)
        ).fetchone()
        if not exists:
            _audit_access(
                "applicant.event_ack",
                metadata={"acknowledged": False, "reason": "event_not_found"},
            )
            return {"acknowledged": False, "reason": "event_not_found"}
        acknowledged_at = datetime.now().astimezone().isoformat(timespec="seconds")
        conn.execute(
            "UPDATE agent_events SET acknowledged_at = "
            "CASE WHEN acknowledged_at = '' THEN ? ELSE acknowledged_at END "
            "WHERE event_id = ?",
            (acknowledged_at, event_id),
        )
        conn.commit()
        _audit_access(
            "applicant.event_ack",
            metadata={"acknowledged": True},
        )
        return {"acknowledged": True, "event_id": event_id}
    finally:
        conn.close()
