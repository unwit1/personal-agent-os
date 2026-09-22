"""Deterministic timestamp formatting shared by local state writers."""

from __future__ import annotations

from datetime import datetime, timezone


def utc_now_iso() -> str:
    """Return the current UTC time in the repository's ISO format."""

    return datetime.now(timezone.utc).isoformat()
