"""Plan headroom: how much of each subscription allowance is left.

provider_health.py reacts after a provider refuses (quota cooldowns); this
module looks ahead, so routing can spend the plan with room before one runs out
and use allowance that is about to reset unused. Sources, all read-only:

* Codex (ChatGPT plan): the last ``rate_limits`` object Codex writes into its
  session logs (``~/.codex/sessions/**.jsonl`` token_count events): primary
  (5-hour) and secondary (weekly) ``used_percent`` with ``resets_at``. Free.
* Claude Code (Claude plan): the ``rate_limit_event`` that ``claude -p
  --output-format stream-json`` emits. Read by a one-line Haiku probe at most
  every ``CLAUDE_EVERY`` seconds, in the background (a few tokens of the
  5-hour window).
* NanoGPT subscription: ``GET <subscription base>/usage`` with the endpoint
  key: weekly (and daily, when set) input-token windows and the overage flag.
  Free. Every NanoGPT provider shares one account allowance, keyed by its
  secret reference.

``assess`` turns windows into a routing state:

* ``exhausted``: a window is >= 98% used. The router skips the provider until
  that window resets.
* ``tight``: under 15% left in a window, or well ahead of an even pace with
  under half left. Cost x3, so providers with room win.
* ``expiring``: a window resets within 10% of its length with over 40% unused.
  Cost x0.6, so allowance that would be lost gets used.
* ``ok`` / ``unknown``: cost unchanged.

Headroom is advice to routing, never an authorization decision.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import threading
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

CODEX_EVERY = 60
NANOGPT_EVERY = 300
CLAUDE_EVERY = 1200
STALE_AFTER = 6 * 3600  # older snapshots say nothing about the current window
EXHAUSTED_AT = 0.98
TIGHT_LEFT = 0.15
EXPIRING_SHARE = 0.10
EXPIRING_UNUSED = 0.40
MULTIPLIERS = {"tight": 3.0, "expiring": 0.6}

_LOCK = threading.Lock()
_PROBING: set[str] = set()


def cache_path(home: Path) -> Path:
    return Path(home) / "headroom.json"


def _iso(epoch: float | None) -> str | None:
    if epoch is None:
        return None
    return datetime.fromtimestamp(float(epoch), timezone.utc).isoformat(timespec="seconds")


def _epoch(stamp: Any) -> float | None:
    if stamp is None:
        return None
    if isinstance(stamp, (int, float)):
        return float(stamp) / 1000 if stamp > 1e11 else float(stamp)
    try:
        return datetime.fromisoformat(str(stamp).replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None


def window(name: str, used: float | None, resets_at: float | None, minutes: float | None) -> dict[str, Any]:
    return {"name": name, "used": None if used is None else round(max(0.0, float(used)), 6),
            "resets_at": _iso(resets_at), "minutes": minutes}


def _named(minutes: float | None, fallback: str) -> str:
    return {300: "5h", 1440: "daily", 10080: "weekly"}.get(int(minutes or 0), fallback)


# -- parsers (pure) -------------------------------------------------------

def parse_codex(rate_limits: dict[str, Any], observed_at: float | None = None) -> dict[str, Any]:
    windows = []
    for key, fallback in (("primary", "5h"), ("secondary", "weekly")):
        item = rate_limits.get(key) or {}
        if item.get("used_percent") is None:
            continue
        minutes = item.get("window_minutes")
        windows.append(window(_named(minutes, fallback), float(item["used_percent"]) / 100, _epoch(item.get("resets_at")), minutes))
    credits = rate_limits.get("credits") or {}
    overage = "metered" if credits.get("unlimited") or credits.get("has_credits") else "blocked"
    return {"source": "codex session log", "plan": rate_limits.get("plan_type"), "windows": windows, "overage": overage,
            "observed_at": _iso(observed_at or time.time())}


def parse_claude(event: dict[str, Any], observed_at: float | None = None) -> dict[str, Any]:
    info = event.get("rate_limit_info") or {}
    windows = []
    for key, minutes in (("five_hour", 300), ("seven_day", 10080)):
        item = (info.get("unifiedWindows") or {}).get(key) or {}
        if item.get("utilization") is None:
            continue
        windows.append(window(_named(minutes, key), float(item["utilization"]), _epoch(item.get("resetsAt")), minutes))
    overage = "metered" if info.get("isUsingOverage") or info.get("overageStatus") == "allowed" else "blocked"
    return {"source": "claude rate_limit_event", "windows": windows, "overage": overage, "observed_at": _iso(observed_at or time.time())}


def parse_nanogpt(payload: dict[str, Any], observed_at: float | None = None) -> dict[str, Any]:
    limits = payload.get("limits") or {}
    windows = []
    for key, limit_key, minutes in (("weeklyInputTokens", "weeklyInputTokens", 10080), ("dailyInputTokens", "dailyInputTokens", 1440)):
        item = payload.get(key)
        limit = limits.get(limit_key)
        if not isinstance(item, dict) or not limit:
            continue
        # used / limit, not percentUsed: sources disagree on its scale.
        windows.append(window(_named(minutes, key), float(item.get("used") or 0) / float(limit), _epoch(item.get("resetAt")), minutes))
        windows[-1].update(used_units=item.get("used"), limit_units=limit)
    routing = payload.get("routing") or {}
    overage = "metered" if payload.get("allowOverage") or routing.get("paidOverageEnabled") else "blocked"
    return {"source": "nanogpt subscription usage", "active": payload.get("active"), "windows": windows, "overage": overage,
            "observed_at": _iso(observed_at or time.time())}


# -- readers (I/O) --------------------------------------------------------

def read_codex(sessions: Path | None = None) -> dict[str, Any] | None:
    """The newest ``rate_limits`` in the newest Codex session logs."""
    root = sessions or Path.home() / ".codex" / "sessions"
    if not root.is_dir():
        return None
    files = sorted(root.rglob("*.jsonl"), key=lambda path: path.stat().st_mtime, reverse=True)[:3]
    for path in files:
        try:
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        for line in reversed(lines):
            if '"rate_limits"' not in line:
                continue
            try:
                event = json.loads(line)
            except ValueError:
                continue
            limits = (event.get("payload") or {}).get("rate_limits")
            if isinstance(limits, dict):
                return parse_codex(limits, _epoch(event.get("timestamp")) or path.stat().st_mtime)
    return None


def probe_claude(run: Callable[..., Any] = subprocess.run, executable: str | None = None) -> dict[str, Any] | None:
    """One Haiku turn to read the Claude plan's rate_limit_event."""
    exe = executable or shutil.which("claude")
    if not exe:
        return None
    # Measure the subscription, not an API key or a bridged coding plan.
    env = {key: value for key, value in os.environ.items()
           if key not in {"ANTHROPIC_API_KEY", "ANTHROPIC_BASE_URL", "ANTHROPIC_AUTH_TOKEN"}}
    try:
        done = run([exe, "-p", "--output-format", "stream-json", "--verbose", "--model", "haiku", "--max-turns", "1"],
                   input="Reply with OK.", capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120, env=env)
    except (OSError, subprocess.SubprocessError):
        return None
    for line in (done.stdout or "").splitlines():
        if '"rate_limit_event"' in line:
            try:
                return parse_claude(json.loads(line))
            except ValueError:
                return None
    return None


def read_nanogpt(base_url: str, secret_ref: str, opener: Callable[..., Any] = urllib.request.urlopen) -> dict[str, Any] | None:
    from .secret_refs import resolve

    key = resolve(secret_ref)
    if not key:
        return None
    request = urllib.request.Request(base_url.rstrip("/") + "/usage", headers={"Authorization": f"Bearer {key}", "user-agent": "agent-os/1"})
    try:
        with opener(request, timeout=30) as response:
            return parse_nanogpt(json.loads(response.read().decode()))
    except Exception:
        return None


# -- provider mapping, cache, assessment ----------------------------------

def source_key(provider: dict[str, Any]) -> str | None:
    """Which allowance a registry entry draws on, or None when untracked."""
    adapter = provider.get("adapter")
    options = provider.get("options") or {}
    if adapter == "codex_cli":
        return "codex"
    if adapter == "claude_code":
        bridged = (options.get("env") or {}).get("ANTHROPIC_BASE_URL") or options.get("secret_env")
        return None if bridged else "claude"
    catalog = options.get("catalog") or {}
    if catalog.get("service") == "nanogpt" and catalog.get("endpoint") == "subscription" and options.get("secret_ref"):
        return f"nanogpt|{options.get('base_url')}|{options['secret_ref']}"
    return None


def _load(home: Path) -> dict[str, Any]:
    try:
        data = json.loads(cache_path(home).read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def _save(home: Path, data: dict[str, Any]) -> None:
    path = cache_path(home)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(f".{os.getpid()}.{threading.get_ident()}.tmp")
    temp.write_text(json.dumps(data, indent=1, sort_keys=True), encoding="utf-8")
    os.replace(temp, path)


def _store(home: Path, key: str, snapshot: dict[str, Any] | None, now: float) -> None:
    with _LOCK:
        data = _load(home)
        entry = data.get(key) or {}
        entry["checked_at"] = _iso(now)
        if snapshot is not None:
            entry["snapshot"] = snapshot
        data[key] = entry
        _save(home, data)


def refresh(providers: list[dict[str, Any]], home: Path, *, now: float | None = None, force: bool = False,
            background: bool = True, readers: dict[str, Callable[..., Any]] | None = None) -> dict[str, Any]:
    """Refresh stale sources for these providers; returns ``{source: entry}``.
    The Claude probe runs in a daemon thread unless ``background`` is False."""
    current = time.time() if now is None else now
    readers = readers or {}
    wanted = {key for key in (source_key(item) for item in providers if item.get("enabled", True)) if key}
    cached = _load(home)
    for key in sorted(wanted):
        checked = _epoch((cached.get(key) or {}).get("checked_at")) or 0
        if key == "codex":
            every, read = CODEX_EVERY, lambda: (readers.get("codex") or read_codex)()
        elif key == "claude":
            every, read = CLAUDE_EVERY, lambda: (readers.get("claude") or probe_claude)()
        else:
            _, base_url, secret_ref = key.split("|", 2)
            every, read = NANOGPT_EVERY, (lambda base_url=base_url, secret_ref=secret_ref: (readers.get("nanogpt") or read_nanogpt)(base_url, secret_ref))
        if not force and current - checked < every:
            continue
        if key == "claude" and background:
            with _LOCK:
                if key in _PROBING:
                    continue
                _PROBING.add(key)

            def probe(read=read, key=key) -> None:
                try:
                    _store(home, key, read(), time.time())
                finally:
                    with _LOCK:
                        _PROBING.discard(key)

            threading.Thread(target=probe, daemon=True).start()
            continue
        _store(home, key, read(), current)
    return {key: value for key, value in _load(home).items() if key in wanted}


def assess(snapshot: dict[str, Any] | None, now: float | None = None) -> dict[str, Any]:
    """Routing state for one allowance snapshot."""
    current = time.time() if now is None else now
    if not snapshot or not snapshot.get("windows"):
        return {"state": "unknown", "multiplier": 1.0, "detail": "no usage data"}
    observed = _epoch(snapshot.get("observed_at")) or 0
    if current - observed > STALE_AFTER:
        return {"state": "unknown", "multiplier": 1.0, "detail": f"usage data from {snapshot.get('observed_at')} is stale"}
    states = []
    for item in snapshot["windows"]:
        used, resets, minutes = item.get("used"), _epoch(item.get("resets_at")), item.get("minutes")
        if used is None:
            continue
        if resets is not None and resets <= current:
            used, resets = 0.0, None  # that window has reset since it was observed; its new end is unknown
        left = 1.0 - used
        span = float(minutes or 0) * 60
        remaining_share = (resets - current) / span if resets is not None and span else None
        label = f"{item['name']} {used:.0%} used" + (f", resets {item.get('resets_at')}" if resets is not None else "")
        if used >= EXHAUSTED_AT:
            states.append(("exhausted", label, item.get("resets_at")))
        elif left < TIGHT_LEFT or (remaining_share is not None and used - (1 - remaining_share) > 0.25 and left < 0.5):
            states.append(("tight", label, None))
        elif remaining_share is not None and remaining_share <= EXPIRING_SHARE and left > EXPIRING_UNUSED:
            states.append(("expiring", label, None))
        else:
            states.append(("ok", label, None))
    if not states:
        return {"state": "unknown", "multiplier": 1.0, "detail": "no usage data"}
    for state in ("exhausted", "tight", "expiring"):
        hits = [item for item in states if item[0] == state]
        if hits:
            # A tight window outranks an expiring one: never spend into a limit.
            until = max((item[2] for item in hits if item[2]), default=None) if state == "exhausted" else None
            return {"state": state, "multiplier": MULTIPLIERS.get(state, 1.0), "detail": "; ".join(item[1] for item in states),
                    **({"until": until} if until else {})}
    return {"state": "ok", "multiplier": 1.0, "detail": "; ".join(item[1] for item in states)}


def for_providers(providers: list[dict[str, Any]], home: Path, *, now: float | None = None, refresh_sources: bool = True,
                  force: bool = False, background: bool = True, readers: dict[str, Callable[..., Any]] | None = None) -> dict[str, dict[str, Any]]:
    """``{provider_id: assessment}`` for every provider with a tracked allowance."""
    entries = (refresh(providers, home, now=now, force=force, background=background, readers=readers)
               if refresh_sources else _load(home))
    out: dict[str, dict[str, Any]] = {}
    for provider in providers:
        key = source_key(provider)
        if key is None:
            continue
        snapshot = (entries.get(key) or {}).get("snapshot")
        out[provider["id"]] = {**assess(snapshot, now), "source": key.split("|", 1)[0], "windows": (snapshot or {}).get("windows", []),
                               "overage": (snapshot or {}).get("overage")}
    return out
