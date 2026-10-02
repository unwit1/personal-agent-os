"""Append-only free-request ledger and quota governor for FreeComputeBroker.

All allowance figures come from the versioned provider-policy record passed in;
nothing here hard-codes a provider limit. The ledger stores no prompt/output text.
"""
from __future__ import annotations

import json
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Mapping

from .store import orchestrator_home

EVENT_SCHEMA = "agent-os/free-quota-event/v1"
OUTCOMES = frozenset(
    {"success", "invalid_output", "validator_failed", "rate_limited", "quota_exhausted",
     "provider_error", "timeout", "context_overflow"}
)
# Outcomes that indicate the endpoint (not the output) failed.
ENDPOINT_FAILURES = frozenset({"rate_limited", "quota_exhausted", "provider_error", "timeout"})
FORBIDDEN_KEYS = frozenset({"prompt", "output", "text", "content", "completion", "messages", "response"})
DEFAULT_RETRY_BUDGET = 1


def ledger_path(home: Path | None = None) -> Path:
    return (Path(home) if home is not None else orchestrator_home()) / "free-compute" / "ledger.jsonl"


def _iso(moment: datetime) -> str:
    return moment.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def record(event: Mapping[str, Any], home: Path | None = None) -> dict[str, Any]:
    """Append one event line; fills schema_version, ts and event_id when absent."""
    leaked = FORBIDDEN_KEYS & set(event)
    if leaked:
        raise ValueError(f"ledger events must not carry prompt/output text: {sorted(leaked)}")
    if event.get("type") is None and event.get("outcome") not in OUTCOMES:
        raise ValueError(f"unknown outcome: {event.get('outcome')!r}")
    entry = dict(event)
    entry.setdefault("schema_version", EVENT_SCHEMA)
    entry.setdefault("ts", _iso(datetime.now(timezone.utc)))
    if entry.get("type") is None:
        stamp = (_parse(entry["ts"]) or datetime.now(timezone.utc)).strftime("%Y%m%dT%H%M%SZ")
        entry.setdefault("event_id", f"FQE-{stamp}-{secrets.token_hex(4)}")
    path = ledger_path(home)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(entry, sort_keys=True) + "\n")
    return entry


def read_events(home: Path | None = None) -> list[dict[str, Any]]:
    path = ledger_path(home)
    if not path.exists():
        return []
    events = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            item = json.loads(line)
        except ValueError:
            continue
        if isinstance(item, dict):
            events.append(item)
    return events


class Governor:
    def __init__(
        self,
        policy: Mapping[str, Any],
        *,
        high_tier: bool | None = False,
        reserve: int | None = None,
        retry_budget: int | None = None,
        now: Callable[[], datetime] | None = None,
        home: Path | None = None,
        events: list[dict[str, Any]] | None = None,
        backoff_base: float = 30.0,
        backoff_cap: float = 900.0,
        failure_threshold: int = 2,
    ) -> None:
        self.policy = policy
        self.high_tier = high_tier is True  # unknown tier counts as low
        self.reserve = int(policy.get("reserve_requests", 0) if reserve is None else reserve)
        self.retry_budget = int(
            policy.get("retry_budget", DEFAULT_RETRY_BUDGET) if retry_budget is None else retry_budget
        )
        self._now = now or (lambda: datetime.now(timezone.utc))
        self.home = home
        self.backoff_base = float(backoff_base)
        self.backoff_cap = float(backoff_cap)
        self.failure_threshold = max(1, int(failure_threshold))
        self._events = list(events) if events is not None else read_events(home)

    # -- policy-derived figures -------------------------------------------
    @property
    def allowance(self) -> int:
        key = "daily_free_requests_high" if self.high_tier else "daily_free_requests_low"
        return int(self.policy[key])

    @property
    def rpm(self) -> int:
        return int(self.policy["free_rpm"])

    def _attempts(self) -> list[dict[str, Any]]:
        return [e for e in self._events if not e.get("type")]

    def last_reset(self, now: datetime | None = None) -> datetime:
        moment = (now or self._now()).astimezone(timezone.utc)
        clock = str(self.policy.get("reset") or "00:00Z").rstrip("Zz")
        hour, _, minute = clock.partition(":")
        boundary = moment.replace(hour=int(hour or 0), minute=int(minute or 0), second=0, microsecond=0)
        return boundary if boundary <= moment else boundary - timedelta(days=1)

    def next_reset(self, now: datetime | None = None) -> datetime:
        return self.last_reset(now) + timedelta(days=1)

    def _charged(self, event: Mapping[str, Any]) -> bool:
        if self.policy.get("failed_requests_count", True):
            return True
        return event.get("outcome") not in ENDPOINT_FAILURES | {"context_overflow"}

    def _spent(self, now: datetime) -> int:
        since = self.last_reset(now)
        return sum(
            1 for e in self._attempts()
            if (ts := _parse(e.get("ts"))) and since <= ts <= now and self._charged(e)
        )

    def _minute_used(self, now: datetime) -> int:
        start = now - timedelta(seconds=60)
        return sum(1 for e in self._attempts() if (ts := _parse(e.get("ts"))) and start < ts <= now)

    # -- public API --------------------------------------------------------
    def record(self, event: Mapping[str, Any]) -> dict[str, Any]:
        entry = record(event, self.home)
        self._events.append(entry)
        return entry

    def remaining(self, now: datetime | None = None) -> dict[str, Any]:
        moment = now or self._now()
        return {
            "daily_left": max(0, self.allowance - self._spent(moment) - self.reserve),
            "minute_left": max(0, self.rpm - self._minute_used(moment)),
            "reset_at": _iso(self.next_reset(moment)),
        }

    def expiring_capacity(self, now: datetime | None = None) -> int:
        """Requests (above the reserve) that will expire unused at the next reset."""
        return self.remaining(now)["daily_left"]

    def consecutive_failures(self, model: str) -> int:
        count = 0
        for event in reversed(self._attempts()):
            if event.get("model") != model:
                continue
            if event.get("outcome") not in ENDPOINT_FAILURES:
                break
            count += 1
        return count

    def backoff_seconds(self, failures: int) -> float:
        if failures < self.failure_threshold:
            return 0.0
        return min(self.backoff_cap, self.backoff_base * (2 ** (failures - self.failure_threshold)))

    def backoff_until(self, model: str) -> datetime | None:
        delay = self.backoff_seconds(self.consecutive_failures(model))
        if not delay:
            return None
        last = max(
            (ts for e in self._attempts() if e.get("model") == model and (ts := _parse(e.get("ts")))),
            default=None,
        )
        return last + timedelta(seconds=delay) if last else None

    def can_spend(self, model: str, retry: int = 0) -> tuple[bool, str]:
        now = self._now()
        if retry > self.retry_budget:
            return False, f"retry budget exhausted ({retry} > {self.retry_budget})"
        until = self.backoff_until(model)
        if until is not None and now < until:
            return False, f"backoff until {_iso(until)} after {self.consecutive_failures(model)} consecutive failures"
        left = self.remaining(now)
        if left["daily_left"] <= 0:
            return False, f"daily allowance reached (reserve {self.reserve} held back)"
        if left["minute_left"] <= 0:
            return False, "per-minute limit reached"
        return True, "ok"
