"""Bounded retry with full-jitter backoff, Retry-After, and a circuit breaker.

Subsumed rather than depended on (DEC-0009, prior art PA-tenacity and
PA-pybreaker; operator preference to subsume, attribution below):

* backoff follows the "full jitter" scheme (sleep = random(0, min(cap,
  base * 2**attempt))), as in Tenacity's ``wait_random_exponential``;
* a server's ``Retry-After`` (seconds or HTTP date) wins over the computed
  delay, bounded by ``max_delay``;
* only retryable failures are retried: rate limits, overload and transient
  server/network errors; validation, auth and policy failures never are
  (constitution runtime rules, implementation-status RT-05/RT-06/RT-07);
* ``CircuitBreaker`` is the closed -> open -> half-open state machine of
  pybreaker (fail_max, reset_timeout), for providers that keep failing.

Attribution: algorithms adapted from Tenacity (Apache-2.0, jd/tenacity) and
pybreaker (BSD-3-Clause, danielfm/pybreaker).
"""

from __future__ import annotations

import random
import threading
import time
from dataclasses import dataclass, field
from email.utils import parsedate_to_datetime
from typing import Any, Callable, TypeVar

T = TypeVar("T")
RETRYABLE_STATUS = frozenset({408, 409, 425, 429, 500, 502, 503, 504, 529})
NEVER_RETRY_STATUS = frozenset({400, 401, 403, 404, 413, 422})


class RetryableError(Exception):
    """A failure worth retrying; ``retry_after`` is the server's hint in seconds."""

    def __init__(self, message: str, *, status: int | None = None, retry_after: float | None = None) -> None:
        super().__init__(message)
        self.status = status
        self.retry_after = retry_after


class CircuitOpenError(Exception):
    pass


def parse_retry_after(value: str | None, now: float | None = None) -> float | None:
    """Seconds to wait from a Retry-After header (delta-seconds or HTTP date)."""
    if not value:
        return None
    value = value.strip()
    try:
        return max(0.0, float(value))
    except ValueError:
        pass
    try:
        when = parsedate_to_datetime(value).timestamp()
    except (TypeError, ValueError):
        return None
    return max(0.0, when - (now if now is not None else time.time()))


def full_jitter(attempt: int, base: float = 1.0, cap: float = 60.0, rng: Callable[[], float] = random.random) -> float:
    return rng() * min(cap, base * (2 ** attempt))


@dataclass
class RetryPolicy:
    max_attempts: int = 4
    base_delay: float = 1.0
    max_delay: float = 60.0
    deadline: float | None = 300.0  # total seconds across attempts

    def call(self, fn: Callable[[], T], *, sleep: Callable[[float], None] = time.sleep, clock: Callable[[], float] = time.monotonic,
             rng: Callable[[], float] = random.random, on_retry: Callable[[int, float, Exception], None] | None = None) -> T:
        started = clock()
        attempt = 0
        while True:
            try:
                return fn()
            except RetryableError as exc:
                attempt += 1
                if attempt >= self.max_attempts:
                    raise
                delay = exc.retry_after if exc.retry_after is not None else full_jitter(attempt - 1, self.base_delay, self.max_delay, rng)
                delay = min(delay, self.max_delay)
                if self.deadline is not None and clock() - started + delay > self.deadline:
                    raise
                if on_retry:
                    on_retry(attempt, delay, exc)
                sleep(delay)


@dataclass
class CircuitBreaker:
    fail_max: int = 3
    reset_timeout: float = 300.0
    clock: Callable[[], float] = time.monotonic
    state: str = "closed"
    failures: int = 0
    opened_at: float | None = None
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def allow(self) -> bool:
        with self._lock:
            if self.state == "open" and self.opened_at is not None and self.clock() - self.opened_at >= self.reset_timeout:
                self.state = "half_open"
            return self.state != "open"

    def success(self) -> None:
        with self._lock:
            self.state, self.failures, self.opened_at = "closed", 0, None

    def failure(self) -> None:
        with self._lock:
            self.failures += 1
            if self.state == "half_open" or self.failures >= self.fail_max:
                self.state, self.opened_at = "open", self.clock()

    def call(self, fn: Callable[[], T]) -> T:
        if not self.allow():
            raise CircuitOpenError("circuit open")
        try:
            result = fn()
        except Exception:
            self.failure()
            raise
        self.success()
        return result

    def snapshot(self) -> dict[str, Any]:
        return {"state": self.state, "failures": self.failures, "opened_at": self.opened_at}
