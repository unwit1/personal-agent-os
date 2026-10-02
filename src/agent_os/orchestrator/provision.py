"""Gated compute provisioning (IMP-0015 slice 2, DEC-0042): provision/status/stop/destroy/reconcile.

Implemented and tested against the fake provider only; any other provider ends in
``blocked`` and nothing is reserved or launched. Every operation returns the
persisted job record (``<home>/compute-jobs/<job_id>.json``) and moves it through
one persisted lifecycle (TRANSITIONS). The spend reservation is written to the
ledger *before* the provider is called (write-ahead, like IMP-0013).
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from ..storage import write_json
from . import budget, secret_refs
from .store import orchestrator_home

TRANSITIONS: dict[str, set[str]] = {
    "requested": {"reserved", "blocked", "failed"},
    "blocked": {"requested"},
    "reserved": {"launching", "failed"},
    "launching": {"running", "failed"},
    "running": {"stopping", "failed"},
    "stopping": {"stopped", "failed"},
    "stopped": {"destroyed", "failed"},
    "destroyed": {"reconciled"},
    "failed": {"destroyed", "reconciled"},
    "reconciled": set(),
}
JOB_ID = re.compile(r"^[a-z0-9][a-z0-9-]{2,63}$")
REQUEST_KEYS = {"provider", "gpu", "hourly_usd", "estimate", "max_runtime_seconds", "budget", "job_id", "secret_ref"}


def _iso(clock: Callable[[], float]) -> str:
    return datetime.fromtimestamp(clock(), timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _jobs_dir(home: Path | None) -> Path:
    return Path(home or orchestrator_home()) / "compute-jobs"


def _job_path(job_id: str, home: Path | None) -> Path:
    return _jobs_dir(home) / f"{job_id}.json"


def _load(job_id: str, home: Path | None) -> dict[str, Any]:
    path = _job_path(job_id, home)
    if not path.exists():
        raise KeyError(f"unknown compute job {job_id!r}")
    return json.loads(path.read_text(encoding="utf-8"))


def _save(record: dict[str, Any], home: Path | None) -> dict[str, Any]:
    write_json(_job_path(record["job_id"], home), record)
    return record


def _transition(job: dict[str, Any], new_state: str, reason: str | None = None, *, clock: Callable[[], float] = time.time) -> dict[str, Any]:
    """Move ``job`` to ``new_state`` if the table allows it; append to history."""
    old = job["state"]
    if new_state not in TRANSITIONS.get(old, set()):
        raise ValueError(f"illegal compute job transition {old} -> {new_state}")
    if old == "launching" and new_state == "failed" and not job.get("instance_id"):
        raise ValueError("launching -> failed requires a known instance_id")
    job["state"] = new_state
    job.setdefault("history", []).append({"at": _iso(clock), "from": old, "to": new_state, "reason": reason})
    return job


def _canonical(request: dict[str, Any]) -> str:
    return json.dumps(request, sort_keys=True, separators=(",", ":"))


def _number(value: Any, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a number")
    return float(value)


def _validate(request: dict[str, Any]) -> dict[str, Any]:
    """Raise ValueError for a bad request (nothing persisted); return the normalized fields."""
    if not isinstance(request, dict):
        raise ValueError("request must be an object")
    unknown = sorted(set(request) - REQUEST_KEYS)
    if unknown:
        raise ValueError(f"unknown or credential-looking request keys {unknown}; pass credentials only as secret_ref=secrets://<provider>/<name>")
    for key in ("provider", "gpu"):
        if not isinstance(request.get(key), str) or not request[key].strip():
            raise ValueError(f"{key} is required and must be a string")
    hourly = _number(request.get("hourly_usd"), "hourly_usd")
    if hourly <= 0:
        raise ValueError("hourly_usd must be greater than 0")
    est = request.get("estimate")
    if not isinstance(est, dict) or not {"low", "expected", "high"} <= set(est):
        raise ValueError("estimate must be {low, expected, high}")
    low, expected, high = (_number(est[k], f"estimate.{k}") for k in ("low", "expected", "high"))
    if not (0 <= low <= expected <= high) or high <= 0:
        raise ValueError("estimate needs 0 <= low <= expected <= high and high > 0")
    cap = request.get("max_runtime_seconds")
    if cap is not None and _number(cap, "max_runtime_seconds") <= 0:
        raise ValueError("max_runtime_seconds must be greater than 0")
    if request.get("budget") is not None and not isinstance(request["budget"], dict):
        raise ValueError("budget must be an object")
    job_id = request.get("job_id")
    if job_id is None:
        job_id = "cj-" + hashlib.sha256(_canonical(request).encode()).hexdigest()[:12]
    elif not isinstance(job_id, str) or not JOB_ID.match(job_id):
        raise ValueError("job_id must match ^[a-z0-9][a-z0-9-]{2,63}$")
    ref = request.get("secret_ref")
    if ref is not None:
        secret_refs.parse(ref)  # ValueError unless a secrets:// reference
    return {"job_id": job_id, "hourly_usd": hourly, "estimate": {"low": low, "expected": expected, "high": high},
            "max_runtime_request": None if cap is None else float(cap)}


def _resolve_provider(name: str, provider: Any, clock: Callable[[], float], hourly: float = 1.0) -> Any:
    if provider is not None:
        return provider
    if name != "fake":
        raise ValueError(f"no adapter for provider {name!r} in slice 2")
    from .compute_fake import FakeProvider

    return FakeProvider(hourly_usd=hourly, clock=clock)


def _spec(job: dict[str, Any]) -> dict[str, Any]:
    return {"name": job["job_id"], "gpu": job["gpu"], "hourly_usd": job["hourly_usd"],
            "max_runtime_seconds": job["max_runtime_seconds"], "secret_ref": job.get("secret_ref")}


def _launch_or_lookup(provider: Any, job: dict[str, Any]) -> str:
    """Find an instance already created under this job's name before launching (resume-safe)."""
    for instance_id, instance in (getattr(provider, "instances", None) or {}).items():
        if instance.get("name") == job["job_id"]:
            return instance_id
    return provider.launch(_spec(job))["instance_id"]


def _block(job: dict[str, Any], reason: str, clock: Callable[[], float], home: Path | None, gate: str | None = None) -> dict[str, Any]:
    job["reason"] = reason
    if gate:
        job["gate"] = gate
    _transition(job, "blocked", reason, clock=clock)
    return _save(job, home)


def _check_gate(job: dict[str, Any], request: dict[str, Any], budget_home: Path | None) -> str | None:
    gate = budget.effective(request.get("budget"), budget_home)
    high = job["estimate"]["high"]
    if not gate["approved"]:
        return "budget not approved"
    if gate["job_hard_cap_usd"] is None or gate["project_usd"] is None:
        return "budget cap or project limit not set"
    if high > gate["job_hard_cap_usd"]:
        return f"estimate.high {high} exceeds job_hard_cap_usd {gate['job_hard_cap_usd']}"
    if high > gate["project_usd"]:
        return f"estimate.high {high} exceeds remaining project budget {gate['project_usd']}"
    return None


def _max_runtime(job: dict[str, Any], requested: float | None) -> int:
    limit = job["estimate"]["high"] / job["hourly_usd"] * 3600
    return math.floor(min(requested, limit) if requested is not None else limit)


def _finish_stop(job: dict[str, Any], provider: Any, reason: str, clock: Callable[[], float], home: Path | None) -> dict[str, Any]:
    if job["state"] == "running":
        _transition(job, "stopping", reason, clock=clock)
        _save(job, home)
    if job["state"] == "stopping":
        provider.stop(job["instance_id"])
        _apply_poll(job, provider.poll(job["instance_id"]))
        _transition(job, "stopped", reason, clock=clock)
    return _save(job, home)


def _apply_poll(job: dict[str, Any], polled: dict[str, Any]) -> None:
    job["runtime_seconds"] = polled.get("runtime_seconds")
    job["cost_usd"] = polled.get("cost_usd")


def _advance(job: dict[str, Any], request: dict[str, Any] | None, provider: Any, clock: Callable[[], float],
             home: Path | None, budget_home: Path | None) -> dict[str, Any]:
    if job["state"] == "requested":
        if budget.open_reservation(job["job_id"], budget_home) <= 0:
            reason = _check_gate(job, request or {}, budget_home)
            if reason is None and job["max_runtime_seconds"] <= 0:
                reason = "max_runtime_seconds would be 0"
            if reason:
                return _block(job, reason, clock, home)
            budget.reserve(job["estimate"]["high"], job_id=job["job_id"], provider=job["provider"], home=budget_home)
        job["reservation_usd"] = job["estimate"]["high"]
        _transition(job, "reserved", clock=clock)
        _save(job, home)
    if job["state"] == "reserved":
        _transition(job, "launching", clock=clock)
        _save(job, home)
    if job["state"] == "launching":
        try:
            instance_id = _launch_or_lookup(provider, job)
        except Exception as exc:  # the instance may exist: stay launching, keep the reservation
            job["reason"] = f"launch error: {type(exc).__name__}: {str(exc)[:200]}"
            job["launch_attempts"] = int(job.get("launch_attempts") or 0) + 1
            return _save(job, home)
        job["instance_id"] = instance_id
        job["launch_attempts"] = int(job.get("launch_attempts") or 0) + 1
        job["auto_stop_epoch"] = clock() + job["max_runtime_seconds"]
        job["auto_stop_at"] = datetime.fromtimestamp(job["auto_stop_epoch"], timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        job["reason"] = None
        _transition(job, "running", clock=clock)
        _save(job, home)
        if job.get("stop_requested"):
            return _finish_stop(job, provider, "stop_requested", clock, home)
    return job


def provision(request: dict[str, Any], *, provider: Any = None, home: Path | None = None, budget_home: Path | None = None,
              clock: Callable[[], float] | None = None) -> dict[str, Any]:
    clock = clock or time.time
    fields = _validate(request)
    job_id = fields["job_id"]
    digest = hashlib.sha256(_canonical({k: v for k, v in request.items() if k != "job_id"}).encode()).hexdigest()
    path = _job_path(job_id, home)
    if path.exists():
        job = _load(job_id, home)
        if job.get("request_hash") != digest:
            raise ValueError(f"conflict: job {job_id!r} already exists with a different request")
        if job["state"] == "blocked":
            _transition(job, "requested", "retry", clock=clock)
            job["reason"] = None
            job.pop("gate", None)
            _save(job, home)
    else:
        high = fields["estimate"]["high"]
        job = {"job_id": job_id, "provider": request["provider"], "gpu": request["gpu"], "hourly_usd": fields["hourly_usd"],
               "estimate": fields["estimate"], "reservation_usd": 0.0, "max_runtime_seconds": None, "auto_stop_at": None,
               "instance_id": None, "state": "requested", "runtime_seconds": None, "cost_usd": None, "reason": None,
               "reconcile": None, "history": [], "secret_ref": request.get("secret_ref"), "request_hash": digest}
        job["history"].append({"at": _iso(clock), "from": None, "to": "requested", "reason": None})
        job["max_runtime_seconds"] = _max_runtime(job, fields["max_runtime_request"])
        _save(job, home)
    if job["state"] not in ("requested", "reserved", "launching"):
        return job
    if job["state"] == "requested" and job["provider"] != "fake":
        return _block(job, f"approval_required: provider {job['provider']!r} needs operator approval (no real adapter in slice 2)",
                      clock, home, gate="approval_required")
    if job["state"] == "requested":
        job["max_runtime_seconds"] = _max_runtime(job, fields["max_runtime_request"])
    return _advance(job, request, _resolve_provider(job["provider"], provider, clock, job["hourly_usd"]), clock, home, budget_home)


def status(job_id: str, *, provider: Any = None, home: Path | None = None, budget_home: Path | None = None,
           clock: Callable[[], float] | None = None) -> dict[str, Any]:
    clock = clock or time.time
    job = _load(job_id, home)
    if not job.get("instance_id") or job["state"] not in ("running", "stopping"):
        return job
    provider = _resolve_provider(job["provider"], provider, clock, job["hourly_usd"])
    polled = provider.poll(job["instance_id"])
    _apply_poll(job, polled)
    overdue = clock() >= float(job.get("auto_stop_epoch") or math.inf)
    if job["state"] == "running" and (overdue or polled["state"] != "running"):
        return _finish_stop(job, provider, "auto_stop" if overdue else "provider_stopped", clock, home)
    if job["state"] == "stopping":
        return _finish_stop(job, provider, "resume_stop", clock, home)
    return _save(job, home)


def stop(job_id: str, *, provider: Any = None, home: Path | None = None, budget_home: Path | None = None,
         clock: Callable[[], float] | None = None) -> dict[str, Any]:
    clock = clock or time.time
    job = _load(job_id, home)
    state = job["state"]
    if state in ("requested", "reserved"):
        _transition(job, "failed", "cancelled", clock=clock)
        job["reason"] = "cancelled"
        _save(job, home)
        budget.release(job_id, home=budget_home, note="cancelled")
        return job
    if state == "launching":
        job["stop_requested"] = True
        return _save(job, home)
    if state in ("running", "stopping"):
        return _finish_stop(job, _resolve_provider(job["provider"], provider, clock, job["hourly_usd"]), "stop", clock, home)
    return job


def destroy(job_id: str, *, provider: Any = None, home: Path | None = None, budget_home: Path | None = None,
            clock: Callable[[], float] | None = None) -> dict[str, Any]:
    clock = clock or time.time
    job = _load(job_id, home)
    state = job["state"]
    if state in ("blocked", "destroyed", "reconciled"):
        return job
    if state in ("requested", "reserved"):
        _transition(job, "failed", "abandoned", clock=clock)
        _save(job, home)
        _transition(job, "destroyed", clock=clock)
        return _save(job, home)
    provider = _resolve_provider(job["provider"], provider, clock, job["hourly_usd"])
    if state == "launching":
        job["instance_id"] = _launch_or_lookup(provider, job)  # raises: stays launching, reservation held
        _transition(job, "failed", "abandoned_launch", clock=clock)
        _save(job, home)
    elif state in ("running", "stopping"):
        _finish_stop(job, provider, "destroy", clock, home)
    if job.get("instance_id"):
        provider.terminate(job["instance_id"])
        _apply_poll(job, provider.poll(job["instance_id"]))
    _transition(job, "destroyed", clock=clock)
    return _save(job, home)


def _ledger_kinds(job_id: str, budget_home: Path | None) -> set[str]:
    path = budget.budget_path(budget_home).parent / "spend.jsonl"
    kinds: set[str] = set()
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            try:
                entry = json.loads(line)
            except ValueError:
                continue
            if entry.get("job_id") == job_id:
                kinds.add(entry.get("kind"))
    return kinds


def reconcile(job_id: str, actual_usd: float | None = None, *, provider: Any = None, home: Path | None = None,
              budget_home: Path | None = None, clock: Callable[[], float] | None = None) -> dict[str, Any]:
    clock = clock or time.time
    job = _load(job_id, home)
    if job["state"] in ("blocked", "reconciled"):
        return job
    if job["state"] == "failed" and job.get("instance_id"):
        job = destroy(job_id, provider=provider, home=home, budget_home=budget_home, clock=clock)
    if job["state"] not in ("destroyed", "failed"):
        raise ValueError(f"cannot reconcile a job in state {job['state']!r}; destroy it first")
    actual = float(actual_usd if actual_usd is not None else (job.get("cost_usd") or 0.0))
    if actual < 0:
        raise ValueError("actual_usd must be >= 0")
    if "actual" not in _ledger_kinds(job_id, budget_home):
        budget.record_spend(actual, job_id=job_id, kind="actual", provider=job["provider"], home=budget_home)
    budget.release(job_id, home=budget_home, note="reconciled")
    est = job["estimate"]
    job["reconcile"] = {"actual_usd": actual, "estimate_expected": est["expected"], "variance_usd": round(actual - est["expected"], 4),
                        "within_band": est["low"] <= actual <= est["high"], "over_reservation": actual > est["high"]}
    _transition(job, "reconciled", clock=clock)
    return _save(job, home)
