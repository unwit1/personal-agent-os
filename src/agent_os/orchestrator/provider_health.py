"""Machine-wide provider health: quota cooldowns and a failure-window breaker.

The engine already recorded quota cooldowns (``provider-cooldowns.json`` in
the orchestrator home) and routed around cooling providers; this module makes
that shared by every caller (engine runs, ``orchestrate delegate``,
``orchestrate eval``) and adds (IMP-0005):

* broader reset parsing: "try again at 9:12 PM", "resets 7:10pm",
  "resets Oct 3, 6pm", "retry after 30 seconds", "in 2 hours", and an HTTP
  ``Retry-After`` value (seconds);
* a breaker for repeated non-quota provider failures (``unavailable``): three
  within ten minutes open a fifteen-minute cooldown, after which the provider
  is probed again (half-open by expiry), following the pybreaker state
  machine subsumed in retry.py (DEC-0009).

A cooldown is advice to routing, never an authorization decision.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

BREAKER_FAILURES = 3
BREAKER_WINDOW = timedelta(minutes=10)
BREAKER_COOLDOWN = timedelta(minutes=15)
DEFAULT_QUOTA_COOLDOWN = timedelta(hours=1)
MONTHS = {name: index for index, name in enumerate(("jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"), start=1)}
_TIME = r"(\d{1,2})(?::(\d{2}))?\s*([ap])\.?m\.?"


def cooldown_path(home: Path) -> Path:
    return Path(home) / "provider-cooldowns.json"


def _clock(hour: str, minute: str | None, meridiem: str) -> tuple[int, int]:
    return int(hour) % 12 + (12 if meridiem.lower() == "p" else 0), int(minute or 0)


def quota_reset(detail: str, current: datetime | None = None, retry_after: float | None = None) -> str:
    """Reset time (UTC ISO) from a provider's quota message; one hour if none."""
    local_now = (current or datetime.now(timezone.utc)).astimezone()
    text = (detail or "").lower()
    reset: datetime | None = None
    if retry_after is not None:
        reset = local_now + timedelta(seconds=max(0.0, retry_after))
    if reset is None:
        match = re.search(r"(?:retry|try again) (?:after|in) (\d+)\s*(second|sec|minute|min|hour|hr)s?", text) or re.search(r"\bin (\d+)\s*(second|sec|minute|min|hour|hr)s?\b", text)
        if match:
            unit = match[2]
            seconds = int(match[1]) * (3600 if unit.startswith(("hour", "hr")) else 60 if unit.startswith("min") else 1)
            reset = local_now + timedelta(seconds=seconds)
    if reset is None:
        match = re.search(r"resets?\s+(?:on\s+)?([a-z]{3})[a-z]*\.?\s+(\d{1,2}),?\s*(?:at\s+)?" + _TIME, text)
        if match and match[1] in MONTHS:
            hour, minute = _clock(match[3], match[4], match[5])
            reset = local_now.replace(month=MONTHS[match[1]], day=int(match[2]), hour=hour, minute=minute, second=0, microsecond=0)
            if reset <= local_now:
                reset = reset.replace(year=reset.year + 1)
    if reset is None:
        match = re.search(r"(?:try again at|resets?(?: at)?)\s+" + _TIME, text)
        if match:
            hour, minute = _clock(match[1], match[2], match[3])
            reset = local_now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if reset <= local_now:
                reset += timedelta(days=1)
    if reset is None:
        reset = local_now + DEFAULT_QUOTA_COOLDOWN
    return reset.astimezone(timezone.utc).isoformat(timespec="seconds")


def read(home: Path) -> dict[str, Any]:
    try:
        data = json.loads(cooldown_path(home).read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def _write(home: Path, data: dict[str, Any]) -> None:
    path = cooldown_path(home)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=1), encoding="utf-8")


def write_cooldown(home: Path, provider: str, until: str, reason: str) -> None:
    data = read(home)
    entry = data.get(provider) if isinstance(data.get(provider), dict) else {}
    data[provider] = {**entry, "until": until, "reason": reason}
    _write(home, data)


def cooling(home: Path, current: datetime | None = None) -> set[str]:
    moment = current or datetime.now(timezone.utc)
    result = set()
    for provider, entry in read(home).items():
        try:
            if datetime.fromisoformat(entry["until"]) > moment:
                result.add(provider)
        except (KeyError, TypeError, ValueError):
            continue
    return result


def record_quota(home: Path, provider: str, detail: str, current: datetime | None = None, retry_after: float | None = None) -> str:
    until = quota_reset(detail, current, retry_after)
    write_cooldown(home, provider, until, f"quota: {detail[:180]}")
    return until


def record_unavailable(home: Path, provider: str, detail: str, current: datetime | None = None) -> str | None:
    """Count an 'unavailable' failure; open the breaker (cooldown) on the
    third within the window. Returns the cooldown end when it opens."""
    moment = current or datetime.now(timezone.utc)
    data = read(home)
    entry = data.get(provider) if isinstance(data.get(provider), dict) else {}
    recent = [stamp for stamp in entry.get("failures", []) if _parse(stamp) and moment - _parse(stamp) <= BREAKER_WINDOW]
    recent.append(moment.isoformat(timespec="seconds"))
    entry["failures"] = recent[-BREAKER_FAILURES:]
    opened = None
    if len(recent) >= BREAKER_FAILURES:
        opened = (moment + BREAKER_COOLDOWN).isoformat(timespec="seconds")
        entry.update(until=opened, reason=f"breaker open after {len(recent)} unavailable failures in {int(BREAKER_WINDOW.total_seconds() // 60)} min: {detail[:120]}", failures=[])
    data[provider] = entry
    _write(home, data)
    return opened


def _parse(stamp: Any) -> datetime | None:
    try:
        return datetime.fromisoformat(str(stamp))
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# Learned model availability: the account cannot use a model the vendor lists
# ---------------------------------------------------------------------------

UNAVAILABLE_MODEL_TTL = timedelta(days=7)  # re-check later: plans and access change


def unavailable_models_path(registry_dir: Path) -> Path:
    """Next to the provider registry: machine-wide, shared by every checkout."""
    return Path(registry_dir) / "unavailable-models.json"


def record_unavailable_model(registry_dir: Path, provider: str, model: str, detail: str, current: datetime | None = None) -> None:
    """An ``invalid_model`` failure (e.g. "model is not supported when using
    Codex with a ChatGPT account"): stop routing that model for this provider
    until the entry expires. Narrowing only; never adds or swaps a model."""
    if not provider or not model:
        return
    path = unavailable_models_path(registry_dir)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        data = {}
    now = current or datetime.now(timezone.utc)
    data.setdefault(provider, {})[model] = {"at": now.isoformat(), "until": (now + UNAVAILABLE_MODEL_TTL).isoformat(), "detail": str(detail)[:300]}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=1), encoding="utf-8")


def learned_unavailable(registry_dir: Path, current: datetime | None = None) -> dict[str, set[str]]:
    try:
        data = json.loads(unavailable_models_path(registry_dir).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    now = current or datetime.now(timezone.utc)
    out: dict[str, set[str]] = {}
    for provider, models in (data or {}).items():
        for model, entry in (models or {}).items():
            until = _parse((entry or {}).get("until"))
            if until is None or until > now:
                out.setdefault(str(provider), set()).add(str(model))
    return out
