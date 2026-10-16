"""Proactive watcher: one read-only sweep over the Dashboard event outbox and RTEC-HR knowledge.

Never sends anything and never edits Dashboard records. It writes only local
Event Bus entries, route-log entries and its own state file. Every source is
optional; a missing source is reported in the state file, not raised.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from . import routing

STATE_NAME = "watcher-state.json"
SOURCE = "applicant-watcher"
CONSUMER = "router"
KNOWLEDGE_SUFFIXES = {".md", ".json", ".yaml", ".yml", ".txt"}
_RESPONSE_HINTS = ("reply", "response", "message", "email", "mail", "received")


def state_path(home: Path | str | None = None) -> Path:
    from .window.confirm import window_home

    return window_home(home) / STATE_NAME


def load_state(home: Path | str | None = None) -> dict[str, Any]:
    try:
        data = json.loads(state_path(home).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def _write_state(state: dict[str, Any], home: Path | str | None) -> None:
    path = state_path(home)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")
    os.replace(tmp, path)


def _default_knowledge_root() -> Path | None:
    env = os.environ.get("RTEC_HR_KNOWLEDGE_DIR")
    if env:
        return Path(env)
    try:
        from ..registry import get_project

        root = Path(get_project("rtec-hr-process-model")["path"])
    except Exception:  # noqa: BLE001 -- the checkout is optional
        return None
    return root


def knowledge_fingerprint(root: Path | None) -> dict[str, Any] | None:
    """Newest mtime and file count of the RTEC-HR knowledge files, or None if absent."""
    if root is None or not root.is_dir():
        return None
    count, newest = 0, 0
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if not d.startswith(".")]
        for name in filenames:
            if Path(name).suffix.lower() not in KNOWLEDGE_SUFFIXES:
                continue
            try:
                mtime = (Path(dirpath) / name).stat().st_mtime_ns
            except OSError:
                continue
            count += 1
            newest = max(newest, mtime)
    return {"files": count, "newest_mtime_ns": newest}


def _event_type_for(applicant_event_type: str) -> str:
    text = (applicant_event_type or "").lower()
    if any(hint in text for hint in _RESPONSE_HINTS):
        return "communication.received"
    return "context.changed"


def _publish_applicant_event(bus, raw: dict[str, Any]) -> bool:
    """Publish one Dashboard event; returns True when newly appended."""
    event_id = str(raw.get("event_id") or "")
    if not event_id:
        raise ValueError("applicant event has no event_id")
    kwargs: dict[str, Any] = {
        "domain": "work",
        "sensitivity": "sensitive",
        "provenance": [f"rtec-dashboard:{event_id}"],
    }
    if raw.get("applicant_ref"):
        kwargs["subject"] = str(raw["applicant_ref"])
    created_at = raw.get("created_at")
    if created_at:
        try:
            datetime.fromisoformat(str(created_at).replace("Z", "+00:00"))
            kwargs["occurred_at"] = str(created_at)
        except ValueError:
            pass
    payload = {
        "kind": "applicant_event",
        "dashboard_event_id": event_id,
        "dashboard_event_type": raw.get("event_type"),
        "applicant_ref": raw.get("applicant_ref"),
        "source_component": raw.get("source_component"),
        "details": raw.get("payload") if isinstance(raw.get("payload"), dict) else {},
    }
    _, created = bus.publish(_event_type_for(str(raw.get("event_type") or "")), SOURCE, event_id, payload, **kwargs)
    return created


def sweep_once(
    bus=None,
    *,
    pending_events: Callable[..., dict[str, Any]] | None = None,
    acknowledge_event: Callable[[str], Any] | None = None,
    knowledge_root: Path | str | None = None,
    home: Path | str | None = None,
    now: datetime | None = None,
    limit: int = 100,
) -> dict[str, Any]:
    """Run one sweep and return (and persist) its state."""
    if bus is None:
        from .event_bus import EventBus

        bus = EventBus()
    if pending_events is None or acknowledge_event is None:
        from .. import rtec_applicants

        pending_events = pending_events or rtec_applicants.pending_events
        acknowledge_event = acknowledge_event or rtec_applicants.acknowledge_event
    now = now or datetime.now(timezone.utc)
    previous = load_state(home)
    errors: list[str] = []
    sources: dict[str, str] = {}
    counts = {"applicant_events_seen": 0, "applicant_events_published": 0, "applicant_events_acked": 0,
              "knowledge_refresh_events": 0, "routed": 0}

    # (a) Dashboard applicant events: ack only after a successful publish.
    try:
        batch = pending_events(limit=limit)
        sources["applicants"] = "ok"
    except FileNotFoundError as exc:
        batch = {"results": []}
        sources["applicants"] = f"unavailable: {exc}"
    except Exception as exc:  # noqa: BLE001 -- sources are optional
        batch = {"results": []}
        sources["applicants"] = "error"
        errors.append(f"applicants: {type(exc).__name__}: {exc}")
    for raw in batch.get("results") or []:
        counts["applicant_events_seen"] += 1
        try:
            if _publish_applicant_event(bus, raw):
                counts["applicant_events_published"] += 1
        except Exception as exc:  # noqa: BLE001
            errors.append(f"publish {raw.get('event_id')}: {type(exc).__name__}: {exc}")
            continue
        try:
            result = acknowledge_event(str(raw["event_id"]))
            if not isinstance(result, dict) or result.get("acknowledged", True):
                counts["applicant_events_acked"] += 1
            else:
                errors.append(f"ack {raw.get('event_id')}: {result.get('reason')}")
        except Exception as exc:  # noqa: BLE001
            errors.append(f"ack {raw.get('event_id')}: {type(exc).__name__}: {exc}")

    # (b) RTEC-HR knowledge files: record, never ingest.
    root = Path(knowledge_root) if knowledge_root is not None else _default_knowledge_root()
    fingerprint = knowledge_fingerprint(root)
    if fingerprint is None:
        sources["knowledge"] = "unavailable"
        fingerprint = previous.get("knowledge")
    else:
        sources["knowledge"] = "ok"
        before = previous.get("knowledge")
        if before is not None and before != fingerprint:
            try:
                _, created = bus.publish(
                    "context.changed", SOURCE, f"knowledge_refresh_needed:{fingerprint['newest_mtime_ns']}:{fingerprint['files']}",
                    {"kind": "knowledge_refresh_needed", "files": fingerprint["files"]},
                    domain="work", sensitivity="personal", occurred_at=now.isoformat(),
                )
                counts["knowledge_refresh_events"] += int(created)
            except Exception as exc:  # noqa: BLE001
                errors.append(f"knowledge: {type(exc).__name__}: {exc}")
                fingerprint = before  # retry on the next sweep

    # Route everything newly published (and anything pending from earlier sweeps).
    try:
        counts["routed"] = len(routing.dispatch_pending(bus, consumer=CONSUMER))
    except Exception as exc:  # noqa: BLE001
        errors.append(f"routing: {type(exc).__name__}: {exc}")

    state = {
        "last_sweep": now.isoformat(),
        "counts": counts,
        "new_events": counts["applicant_events_published"] + counts["knowledge_refresh_events"],
        "errors": errors,
        "sources": sources,
        "knowledge": fingerprint,
    }
    try:
        _write_state(state, home)
    except OSError as exc:
        state["errors"] = [*errors, f"state: {exc}"]
    return state


def watch(interval: float, *, sweep: Callable[[], dict[str, Any]] = sweep_once, sleep=None, max_sweeps: int | None = None) -> None:
    """Sweep forever (or max_sweeps times), never dying on one bad sweep."""
    import time

    sleep = sleep or time.sleep
    done = 0
    while max_sweeps is None or done < max_sweeps:
        try:
            sweep()
        except Exception:  # noqa: BLE001
            pass
        done += 1
        if max_sweeps is None or done < max_sweeps:
            sleep(interval)


def watcher_items(home: Path | str | None = None) -> list[dict[str, Any]]:
    """Command-center item: only when the last sweep had errors or new events."""
    state = load_state(home)
    if not state or not (state.get("errors") or state.get("new_events")):
        return []
    counts = state.get("counts") or {}
    parts = [f"last sweep {state.get('last_sweep')}",
             f"{counts.get('applicant_events_published', 0)} new applicant events"]
    if counts.get("knowledge_refresh_events"):
        parts.append("RTEC-HR knowledge changed; refresh needed")
    if state.get("errors"):
        parts.append(f"{len(state['errors'])} errors: " + "; ".join(state["errors"][:3]))
    return [{"id": "watcher_status", "tab": "work", "kind": "watcher_status", "title": "Watcher status",
             "why": "; ".join(parts), "source": "watcher", "context": {"state": state}}]
