"""Versioned provider-policy records for free-compute quotas and data policies.

The canonical policy history lives in Git at
projects/personal-agent-os/orchestrator-os/provider-policy/openrouter-free.json.
It is append-only: a new version is added, earlier versions are never edited.

Operator overrides from orchestrator_home()/free-compute/policy-overrides.json
are merged at runtime and take precedence.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from ..storage import load_json


def _canonical_policy_path() -> Path:
    """Path to the canonical versioned provider-policy record in Git."""
    from ..paths import ROOT

    return ROOT / "projects/personal-agent-os/orchestrator-os/provider-policy/openrouter-free.json"


def _overrides_path(home: Path | None = None) -> Path:
    """Path to operator overrides in the orchestrator home."""
    if home is None:
        from .store import orchestrator_home

        home = orchestrator_home()
    return home / "free-compute" / "policy-overrides.json"


def load(path: Path | None = None, overrides: dict[str, Any] | None = None) -> dict[str, Any]:
    """Load the current versioned provider-policy record and merge operator overrides.

    Args:
        path: Path to the canonical policy file. Defaults to the Git-tracked location.
        overrides: Operator overrides as a dict. Defaults to loading from policy-overrides.json.

    Returns:
        The current policy version with an "overridden" field listing any overridden keys.
    """
    if path is None:
        path = _canonical_policy_path()

    record_data = load_json(path)
    if not isinstance(record_data, dict) or record_data.get("schema_version") != "agent-os/provider-policy-history/v1":
        raise ValueError(f"invalid policy history format in {path}")

    versions = record_data.get("versions", [])
    if not versions:
        raise ValueError(f"no policy versions in {path}")

    # Get the current version (highest version number)
    current = max(versions, key=lambda v: v.get("version", 0))

    if overrides is None:
        overrides_file = _overrides_path()
        try:
            overrides = load_json(overrides_file)
        except FileNotFoundError:
            overrides = {}
        except ValueError as exc:
            raise ValueError(f"invalid policy overrides in {overrides_file}: {exc}") from exc
        if not isinstance(overrides, dict):
            raise ValueError(f"invalid policy overrides in {overrides_file}: expected a JSON object")
    elif not isinstance(overrides, dict):
        raise ValueError("policy overrides must be a dict")

    # Merge overrides into a copy of the current policy
    result = dict(current)
    overridden_fields = []

    for key, value in overrides.items():
        if value is not None:  # None means "don't override"
            result[key] = value
            overridden_fields.append(key)

    result["overridden"] = overridden_fields
    return result


def is_stale(record: dict[str, Any], now: datetime | None = None, max_age_days: int | None = None) -> bool:
    """Check if a policy record is stale based on its verified_at timestamp.

    A record is stale if verified_at is older than max_age_days (default from record, or 30).

    Args:
        record: The policy record.
        now: Current time as a datetime; naive values are treated as UTC. Defaults to the real clock.
        max_age_days: Maximum age in days. Defaults to record's max_age_days field, or 30.

    Returns:
        True if the record's verified_at is missing, unparseable, or older than max_age_days.
    """
    if now is None:
        now = datetime.now(timezone.utc)
    elif now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)

    if max_age_days is None:
        max_age_days = record.get("max_age_days", 30)

    verified_at_str = record.get("verified_at")
    if not verified_at_str:
        return True

    try:
        verified_at = datetime.fromisoformat(verified_at_str.replace("Z", "+00:00"))
        if verified_at.tzinfo is None:
            verified_at = verified_at.replace(tzinfo=timezone.utc)
    except (ValueError, AttributeError):
        return True
    return now - verified_at > timedelta(days=max_age_days)


def allowance(record: dict[str, Any], *, high_tier: bool) -> dict[str, int]:
    """Get the daily and per-minute allowances for a quota tier.

    Args:
        record: The policy record.
        high_tier: If True, use high allowance; otherwise use low allowance.

    Returns:
        Dict with "daily" and "rpm" keys containing the allowance numbers.
    """
    daily = record.get("daily_free_requests_high") if high_tier else record.get("daily_free_requests_low")
    rpm = record.get("free_rpm")

    if daily is None or rpm is None:
        raise ValueError("policy record missing daily_free_requests_* or free_rpm")

    return {"daily": int(daily), "rpm": int(rpm)}
