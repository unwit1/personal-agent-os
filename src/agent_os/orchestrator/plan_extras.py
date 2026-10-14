"""One-time plan extras: promotional credits and saved usage resets.

Vendors grant one-off extras that no usage API reports: a Claude Code cloud
session credit, a saved Claude usage reset, banked Codex resets. This module
keeps a small operator-maintained record of them in
``~/.agent-os/plan-extras.json``, merged over researched defaults, and turns
them plus live headroom (headroom.py) into advice:

* a saved reset is worth redeeming when its plan is exhausted (or tight) with
  hours left before the window resets, and work is waiting;
* an unexpired cloud credit makes long, autonomous, non-sensitive GitHub tasks
  cheaper in a Claude cloud session (cloud_lane.py) than on the local plan.

Nothing here redeems anything. Redemption happens in the vendor's own UI or
CLI (``redeem``), never from a script: a reset is single-use and cannot be
undone, so the operator always clicks it.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STATUSES = ("unknown", "available", "used", "expired")
NEARLY_FULL = 0.90  # a tight plan earns reset advice only once a window is this full

# Researched 2026-10-14 (sources in docs/command-center.md). "unknown" status:
# the vendors show availability only in their own UI.
DEFAULTS: dict[str, dict[str, Any]] = {
    "claude-cloud-credit": {
        "plan": "claude", "kind": "credit", "status": "unknown",
        "title": "Claude Code cloud-session credit ($100 Pro, $250 Max)",
        "expires": "2026-11-04T23:59:59+00:00",
        "applies_to": "Claude Code cloud sessions only; spent before plan limits",
        "redeem": {"kind": "url", "target": "https://claude.ai/settings/usage", "label": "See balance"},
    },
    "claude-saved-reset": {
        "plan": "claude", "kind": "reset", "status": "unknown",
        "title": "Claude saved usage reset (one-time, Opus 5.5 launch)",
        "expires": "2026-10-22T23:59:59+00:00",
        "applies_to": "resets the current usage limits once",
        "redeem": {"kind": "url", "target": "https://claude.ai/settings/usage", "label": "Settings > Usage > Reset for free"},
    },
    "claude-limit-reset": {
        "plan": "claude", "kind": "reset", "status": "unknown",
        "title": "Claude Code /limit-reset (5-hour window only; gradual rollout)",
        "expires": None,
        "applies_to": "clears the 5-hour session limit, not the weekly cap",
        "redeem": {"kind": "terminal", "target": "claude", "label": "Run /limit-reset in Claude Code"},
    },
    "codex-banked-reset": {
        "plan": "codex", "kind": "reset", "status": "unknown",
        "title": "Codex banked usage reset",
        "expires": None,
        "applies_to": "resets Codex usage limits once per banked reset",
        "redeem": {"kind": "terminal", "target": "codex", "label": "Run /usage in Codex and redeem"},
    },
}

# Headroom provider id -> extras plan key.
PLAN_OF_SOURCE = {"claude": "claude", "codex": "codex"}


def path(home: Path) -> Path:
    return Path(home) / "plan-extras.json"


def _parse(stamp: Any) -> datetime | None:
    if not stamp:
        return None
    try:
        moment = datetime.fromisoformat(str(stamp).replace("Z", "+00:00"))
    except ValueError:
        return None
    return moment if moment.tzinfo else moment.replace(tzinfo=timezone.utc)


def load(home: Path, now: datetime | None = None) -> dict[str, dict[str, Any]]:
    """Defaults merged with the operator's record; past expiry reads as expired."""
    current = now or datetime.now(timezone.utc)
    try:
        stored = json.loads(path(home).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        stored = {}
    extras: dict[str, dict[str, Any]] = {}
    for key in {*DEFAULTS, *(stored if isinstance(stored, dict) else {})}:
        item = {**DEFAULTS.get(key, {}), **((stored or {}).get(key) or {})}
        expires = _parse(item.get("expires"))
        if expires and expires < current and item.get("status") != "used":
            item["status"] = "expired"
        extras[key] = {"id": key, **item}
    return dict(sorted(extras.items()))


def set_status(home: Path, key: str, status: str, note: str | None = None) -> dict[str, Any]:
    if status not in STATUSES:
        raise ValueError(f"status must be one of {STATUSES}")
    if key not in DEFAULTS:
        try:
            known = json.loads(path(home).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            known = {}
        if key not in known:
            raise ValueError(f"unknown extra {key!r}; known: {sorted(DEFAULTS)}")
    target = path(home)
    try:
        data = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        data = {}
    entry = data.setdefault(key, {})
    entry["status"] = status
    entry["updated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    if note:
        entry["note"] = note
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(data, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    return load(home)[key]


def advice(extras: dict[str, dict[str, Any]], plans: dict[str, dict[str, Any]], *, now: datetime | None = None,
           waiting_work: bool = True) -> list[dict[str, Any]]:
    """Suggestions from extras and headroom (``{provider_id: assessment}``)."""
    current = now or datetime.now(timezone.utc)
    usable = [item for item in extras.values() if item.get("status") in ("unknown", "available")]
    by_plan: dict[str, dict[str, Any]] = {}
    for assessment in plans.values():
        plan = PLAN_OF_SOURCE.get(str(assessment.get("source")))
        if plan and plan not in by_plan:
            by_plan[plan] = assessment
    out: list[dict[str, Any]] = []
    for plan, assessment in sorted(by_plan.items()):
        state = assessment.get("state")
        if state not in ("exhausted", "tight") or not waiting_work:
            continue
        resets = [item for item in usable if item.get("plan") == plan and item.get("kind") == "reset"]
        if not resets:
            continue
        wait = _hours_until(assessment, current)
        nearly_full = any((item.get("used") or 0) >= NEARLY_FULL for item in assessment.get("windows") or [])
        if state == "tight" and not nearly_full:
            continue  # burning fast but not blocked: a single-use reset is worth more later
        if wait is None or wait < 2:
            continue  # the window resets soon anyway; keep the reset
        out.append({"kind": "redeem_reset", "plan": plan, "state": state, "hours_until_reset": wait,
                    "extras": [item["id"] for item in resets],
                    "message": f"{plan} plan is {state}" + (f" for about {wait:.1f} more hours" if wait is not None else "")
                               + f"; a saved reset may be available ({', '.join(item['title'] for item in resets)}).",
                    "redeem": resets[0].get("redeem")})
    credit = next((item for item in usable if item["id"] == "claude-cloud-credit"), None)
    expires = _parse((credit or {}).get("expires"))
    if credit and expires and expires > current:
        days = (expires - current).total_seconds() / 86400
        out.append({"kind": "use_cloud_credit", "plan": "claude", "days_left": round(days, 1), "extras": [credit["id"]],
                    "message": f"Claude cloud credit expires in {days:.0f} days: send long, autonomous, non-sensitive GitHub tasks "
                               "to a Claude cloud session (orchestrate cloud submit) to spend it before your plan.",
                    "redeem": credit.get("redeem")})
    return out


def _hours_until(assessment: dict[str, Any], current: datetime) -> float | None:
    if assessment.get("until"):
        until = _parse(assessment["until"])
        return round((until - current).total_seconds() / 3600, 1) if until else None
    resets = [_parse(item.get("resets_at")) for item in assessment.get("windows") or [] if item.get("used") is not None]
    resets = [item for item in resets if item and item > current]
    if not resets:
        return None
    # The binding window is the most used one.
    windows = sorted((item for item in assessment.get("windows") or [] if item.get("resets_at")), key=lambda item: -(item.get("used") or 0))
    binding = _parse(windows[0]["resets_at"]) if windows else None
    return round(((binding or min(resets)) - current).total_seconds() / 3600, 1)
