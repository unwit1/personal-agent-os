"""Pure adaptive-concurrency controller for a rented vLLM provider.

Given live vLLM metrics (running, waiting, KV-cache usage) it returns the next
``max_concurrency``. It does no I/O: streak counters travel in a ``memory`` dict
so callers can persist them, and every call returns a decision dict for telemetry.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class ConcurrencyPolicy:
    minimum: int = 2
    maximum: int = 32
    start: int = 4
    step_up: int = 2
    kv_raise_below: float = 0.70
    kv_backoff_above: float = 0.90
    raise_after: int = 2
    backoff_after: int = 1


def _clamp(value: int, policy: ConcurrencyPolicy) -> int:
    return max(policy.minimum, min(policy.maximum, int(value)))


def _number(metrics: Mapping[str, Any] | None, key: str) -> float | None:
    if not metrics:
        return None
    value = metrics.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def next_limit(
    current: int,
    metrics: Mapping[str, Any] | None,
    memory: Mapping[str, Any] | None,
    policy: ConcurrencyPolicy | None = None,
) -> tuple[int, dict[str, int], dict[str, Any]]:
    """Return ``(limit, memory, decision)`` for the next concurrency limit."""
    policy = policy or ConcurrencyPolicy()
    current = _clamp(current, policy)
    memory = memory or {}
    up = max(0, int(memory.get("up", 0) or 0))
    down = max(0, int(memory.get("down", 0) or 0))

    running = _number(metrics, "running")
    waiting = _number(metrics, "waiting")
    kv_usage = _number(metrics, "kv_usage")

    def result(limit: int, up_n: int, down_n: int, reason: str):
        decision = {
            "from": current,
            "to": limit,
            "reason": reason,
            "running": running,
            "waiting": waiting,
            "kv_usage": kv_usage,
        }
        return limit, {"up": up_n, "down": down_n}, decision

    if running is None or waiting is None or kv_usage is None:
        return result(current, up, down, "no_metrics")

    saturated = kv_usage >= policy.kv_backoff_above
    if waiting > 0 or saturated:
        down += 1
        if down >= policy.backoff_after:
            if saturated:
                return result(max(policy.minimum, current // 2), 0, 0, "backoff_kv")
            return result(max(policy.minimum, current - policy.step_up), 0, 0, "backoff_queue")
        return result(current, 0, down, "hold")

    if kv_usage < policy.kv_raise_below and running >= current - 1:
        up += 1
        if up >= policy.raise_after and current < policy.maximum:
            return result(min(policy.maximum, current + policy.step_up), 0, 0, "raise")
        return result(current, up, 0, "hold")

    return result(current, 0, 0, "hold")
