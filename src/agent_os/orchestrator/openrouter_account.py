"""Read-only OpenRouter account/quota adapter for the FreeComputeBroker (IMP-0015).

Only GET requests to the allowlisted key and credits endpoints are ever sent;
there is no purchase, checkout or auto-recharge path. The API key is resolved
through ``secret_refs`` and used only in the Authorization header: it is never
returned, logged or embedded in error text. Failures are data, never raised.
"""

from __future__ import annotations

import json
import urllib.request
from typing import Any, Callable

from ..timestamps import utc_now_iso
from . import secret_refs

OPENROUTER_KEY_URL = "https://openrouter.ai/api/v1/key"
OPENROUTER_CREDITS_URL = "https://openrouter.ai/api/v1/credits"
DEFAULT_SECRET_REF = "secrets://openrouter/default"
ALLOWED_URLS = (OPENROUTER_KEY_URL, OPENROUTER_CREDITS_URL)
_INTERVAL_SECONDS = {"s": 1, "m": 60, "h": 3600, "d": 86400}


def _number(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def _get(url: str, key: str, opener: Callable[..., Any] | None) -> dict[str, Any]:
    if url not in ALLOWED_URLS:
        raise ValueError("url not in read-only allowlist")
    request = urllib.request.Request(
        url, method="GET",
        headers={"accept": "application/json", "user-agent": "agent-os/1", "Authorization": f"Bearer {key}"})
    with (opener or urllib.request.urlopen)(request, timeout=30) as response:
        payload = json.loads(response.read().decode())
    data = payload.get("data") if isinstance(payload, dict) else None
    if not isinstance(data, dict):
        raise ValueError("unexpected account payload")
    return data


def _scrub(text: str, key: str) -> str:
    return text.replace(key, "[redacted]") if key else text


def account_state(*, opener: Callable[..., Any] | None = None,
                  resolve: Callable[[str], str | None] = secret_refs.resolve,
                  secret_ref: str = DEFAULT_SECRET_REF) -> dict[str, Any]:
    try:
        key = resolve(secret_ref)
    except Exception:
        key = None
    if not key:
        return {"configured": False}
    state: dict[str, Any] = {
        "configured": True, "credits_total": None, "credits_used": None, "credits_remaining": None,
        "is_free_tier": None, "rate_limit": None, "usage": None, "fetched_at": utc_now_iso(), "error": None,
    }
    errors: list[str] = []
    try:
        info = _get(OPENROUTER_KEY_URL, key, opener)
        if isinstance(info.get("is_free_tier"), bool):
            state["is_free_tier"] = info["is_free_tier"]
        if isinstance(info.get("rate_limit"), dict):
            state["rate_limit"] = dict(info["rate_limit"])
        state["usage"] = _number(info.get("usage"))
    except Exception as exc:
        errors.append(f"key: {type(exc).__name__}: {_scrub(str(exc), key)[:200]}")
    try:
        credits = _get(OPENROUTER_CREDITS_URL, key, opener)
        total, used = _number(credits.get("total_credits")), _number(credits.get("total_usage"))
        state["credits_total"], state["credits_used"] = total, used
        if total is not None and used is not None:
            state["credits_remaining"] = round(total - used, 6)
    except Exception as exc:
        errors.append(f"credits: {type(exc).__name__}: {_scrub(str(exc), key)[:200]}")
    if errors:
        state["error"] = "; ".join(errors)
    return state


def _rpm(rate_limit: Any) -> float | None:
    if not isinstance(rate_limit, dict):
        return None
    requests, interval = _number(rate_limit.get("requests")), str(rate_limit.get("interval") or "")
    unit = _INTERVAL_SECONDS.get(interval[-1:]) if interval else None
    digits = interval[:-1]
    count = float(digits) if digits.replace(".", "", 1).isdigit() else (1.0 if not digits else None)
    if requests is None or unit is None or not count:
        return None
    return requests * 60.0 / (count * unit)


def topup_advice(state: dict[str, Any], policy: dict[str, Any]) -> dict[str, Any]:
    """Alert only when account evidence shows the high allowance is not active
    and a current (non-stale) policy requires credits for it."""
    advice: dict[str, Any] = {"alert": False, "reason": "", "shortfall_usd": 0.0, "discrepancies": []}
    policy = policy or {}
    free_rpm = _number(policy.get("free_rpm"))
    observed = _rpm(state.get("rate_limit")) if state.get("configured") else None
    if free_rpm is not None and observed is not None and observed != free_rpm:
        advice["discrepancies"].append(
            f"observed rate_limit {observed:g} rpm contradicts policy free_rpm {free_rpm:g}")
    if not state.get("configured"):
        advice["reason"] = "account not configured; no account evidence"
        return advice
    threshold = _number(policy.get("credit_threshold_usd"))
    if threshold is None:
        advice["reason"] = "policy does not require credits for the high allowance"
        return advice
    if policy.get("stale"):
        advice["reason"] = "policy is stale; cannot trigger a top-up alert"
        return advice
    total = _number(state.get("credits_total"))
    if total is None:
        advice["reason"] = "credits unreadable; high allowance tier unknown"
        return advice
    if total >= threshold:
        advice["reason"] = f"purchased credits {total:.2f} >= threshold {threshold:.2f}; high allowance active"
        return advice
    advice.update(alert=True, shortfall_usd=round(threshold - total, 6),
                  reason=f"purchased credits {total:.2f} < threshold {threshold:.2f}; high allowance not active")
    return advice
