"""Persistent proactive watch graph for Agent OS.

Git stores durable watch definitions; high-frequency observations belong in local
SQLite. This module is intentionally provider-neutral so browser captures,
future search workers, RSS readers, APIs, and agents can all use the same model.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fingerprints import text_sha256
from .paths import ROOT

WATCH_DIR = ROOT / "knowledge" / "personal" / "watching"
WATCH_INDEX = WATCH_DIR / "index.json"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _slug(value: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return value[:80] or "watch"


def _load() -> dict[str, Any]:
    if not WATCH_INDEX.exists():
        return {"schema_version": "agent-os/watch-graph/v1", "targets": []}
    value = json.loads(WATCH_INDEX.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("watch index must contain an object")
    value.setdefault("schema_version", "agent-os/watch-graph/v1")
    value.setdefault("targets", [])
    return value


def _save(value: dict[str, Any]) -> None:
    WATCH_DIR.mkdir(parents=True, exist_ok=True)
    WATCH_INDEX.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def add_target(target: dict[str, Any]) -> dict[str, Any]:
    source_id = str(target.get("source_id") or "").strip()
    url = str(target.get("url") or target.get("canonical_url") or "").strip()
    title = str(target.get("title") or "").strip()
    target_type = str(target.get("target_type") or target.get("content_type") or "topic").strip()
    if not (source_id or url or title):
        raise ValueError("watch target requires source_id, url, or title")

    identity = source_id or url or f"{target_type}:{title.lower()}"
    watch_id = "watch-" + text_sha256(identity, 16)
    data = _load()
    existing = next((x for x in data["targets"] if x.get("watch_id") == watch_id), None)
    record = {
        "watch_id": watch_id,
        "kind": target_type,
        "title": title or source_id or url,
        "source_id": source_id,
        "url": url,
        "site": str(target.get("site") or "").strip(),
        "author": str(target.get("author") or "").strip(),
        "status": str(target.get("status") or "active"),
        "priority": str(target.get("priority") or "normal"),
        "refresh_policy": target.get("refresh_policy") or {"mode": "adaptive", "minimum_minutes": 60},
        "search_queries": list(target.get("search_queries") or []),
        "related_projects": list(target.get("related_projects") or []),
        "related_topics": list(target.get("related_topics") or []),
        "notify_policy": target.get("notify_policy") or {"mode": "meaningful_changes"},
        "metadata": dict(target.get("metadata") or {}),
        "provenance": dict(target.get("provenance") or {}),
        "updated_at": _now(),
    }
    if existing:
        record["created_at"] = existing.get("created_at") or _now()
        for key in ("search_queries", "related_projects", "related_topics"):
            record[key] = list(dict.fromkeys(list(existing.get(key) or []) + list(record[key])))
        data["targets"][data["targets"].index(existing)] = record
    else:
        record["created_at"] = _now()
        data["targets"].append(record)
    _save(data)
    return record


def add_browser_follow(capture: dict[str, Any]) -> dict[str, Any]:
    metadata = dict(capture.get("metadata") or {})
    return add_target({
        "source_id": capture.get("source_id"),
        "url": capture.get("canonical_url") or capture.get("url"),
        "title": capture.get("title"),
        "author": capture.get("author"),
        "site": capture.get("site"),
        "target_type": metadata.get("follow_target_type") or capture.get("content_type"),
        "metadata": metadata,
        "provenance": {
            "source": "browser_capture",
            "captured_at": capture.get("captured_at"),
            "discovered_from": metadata.get("discovered_from") or capture.get("url"),
            "device": capture.get("device"),
        },
    })


def list_targets(*, status: str | None = None) -> list[dict[str, Any]]:
    targets = list(_load()["targets"])
    if status:
        targets = [x for x in targets if x.get("status") == status]
    return sorted(targets, key=lambda x: (x.get("priority") != "high", x.get("title", "").lower()))


def remove_target(watch_id: str) -> bool:
    data = _load()
    before = len(data["targets"])
    data["targets"] = [x for x in data["targets"] if x.get("watch_id") != watch_id]
    if len(data["targets"]) == before:
        return False
    _save(data)
    return True
