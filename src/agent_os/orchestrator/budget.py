"""Operator-approved compute budget and spend ledger (IMP-0015).

Roadmap invariant 6 / acceptance 5: no paid job starts merely because a model
proposes it, and a hard job budget cannot be exceeded silently. The budget is
machine-wide operator policy in ``~/.agent-os/budget.json`` (next to the provider registry, shared by every checkout):

    {"project_usd": 10, "job_hard_cap_usd": 5, "approved": true, "set_by": "operator", ...}

Every change is appended to ``budget-history.jsonl`` (never rewritten).
Changing the budget is a ``spending_limit_change`` (policy
approval_required_for): only the operator sets it, through
``orchestrate budget set``; autonomous agents read it and never raise it.

Actual or reserved spend is appended to ``spend.jsonl``; ``remaining`` is
project budget minus recorded spend. ``effective`` merges a workload's own
budget with the machine budget and can only *tighten* it: the job cap is the
smaller of the two, the project limit is the remaining machine budget, and a
paid job is approved only if the machine budget is approved.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from ..timestamps import utc_now_iso


def _home(home: Path | None) -> Path:
    """Machine-wide, next to the provider registry (~/.agent-os), not the
    per-checkout orchestrator home: one budget for every clone and worktree."""
    if home:
        return Path(home)
    configured = os.environ.get("AGENT_OS_BUDGET_HOME")
    if configured:
        return Path(configured)
    from ..capabilities import registry_path

    return registry_path().parent


def budget_path(home: Path | None = None) -> Path:
    return _home(home) / "budget.json"


def load(home: Path | None = None) -> dict[str, Any]:
    try:
        data = json.loads(budget_path(home).read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def set_budget(project_usd: float, job_hard_cap_usd: float, *, set_by: str = "operator", note: str | None = None,
               home: Path | None = None) -> dict[str, Any]:
    """Operator action: set and approve the budget; appends to the history."""
    from ..storage import write_json

    project_usd, job_hard_cap_usd = float(project_usd), float(job_hard_cap_usd)
    if project_usd < 0 or job_hard_cap_usd < 0:
        raise ValueError("budgets must be >= 0")
    if job_hard_cap_usd > project_usd:
        raise ValueError("the per-job hard cap cannot exceed the project budget")
    previous = load(home)
    record = {"project_usd": project_usd, "job_hard_cap_usd": job_hard_cap_usd, "approved": True, "set_by": set_by,
              "set_at": utc_now_iso(), "note": note, "currency": "USD"}
    write_json(budget_path(home), record)
    with (_home(home) / "budget-history.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps({"at": record["set_at"], "previous": previous or None, "current": record}) + "\n")
    return {**record, "spent_usd": spent(home), "remaining_usd": remaining(home)}


def record_spend(amount_usd: float, *, job_id: str, kind: str = "actual", provider: str | None = None, note: str | None = None,
                 home: Path | None = None) -> dict[str, Any]:
    if kind not in {"actual", "reserved", "release"}:
        raise ValueError("kind must be actual, reserved or release")
    entry = {"at": utc_now_iso(), "job_id": job_id, "kind": kind, "amount_usd": round(float(amount_usd), 4), "provider": provider, "note": note}
    path = _home(home) / "spend.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry) + "\n")
    return entry


def spent(home: Path | None = None) -> float:
    """Actual spend plus open reservations (a release cancels a reservation)."""
    path = _home(home) / "spend.jsonl"
    total = 0.0
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            try:
                entry = json.loads(line)
            except ValueError:
                continue
            amount = float(entry.get("amount_usd") or 0)
            total += -amount if entry.get("kind") == "release" else amount
    return round(max(total, 0.0), 4)


def remaining(home: Path | None = None) -> float | None:
    project = load(home).get("project_usd")
    return None if project is None else round(max(float(project) - spent(home), 0.0), 4)


def effective(workload_budget: dict[str, Any] | None, home: Path | None = None) -> dict[str, Any]:
    """The budget a quote is gated on: the machine budget, tightened by any
    workload-level limits, never loosened."""
    machine = load(home)
    workload_budget = workload_budget or {}
    caps = [value for value in (machine.get("job_hard_cap_usd"), workload_budget.get("job_hard_cap_usd")) if value is not None]
    left = remaining(home)
    projects = [value for value in (left, workload_budget.get("project_usd")) if value is not None]
    return {
        "approved": bool(machine.get("approved")),
        "job_hard_cap_usd": min(caps) if caps else None,
        "project_usd": min(projects) if projects else None,
        "source": "machine budget" if machine else "none configured",
    }


def open_reservation(job_id: str, home: Path | None = None) -> float:
    """Sum of reserved minus released amounts for job_id."""
    path = _home(home) / "spend.jsonl"
    total = 0.0
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            try:
                entry = json.loads(line)
            except ValueError:
                continue
            if entry.get("job_id") != job_id:
                continue
            amount = float(entry.get("amount_usd") or 0)
            kind = entry.get("kind")
            if kind == "reserved":
                total += amount
            elif kind == "release":
                total -= amount
    return round(max(total, 0.0), 4)


def reserve(amount_usd: float, *, job_id: str, provider: str | None = None, note: str | None = None,
            home: Path | None = None) -> dict[str, Any]:
    """Idempotent reservation: returns existing reservation if present, otherwise writes new one."""
    existing = open_reservation(job_id, home)
    if existing > 0:
        return {"reused": True, "amount_usd": existing}
    entry = record_spend(amount_usd, job_id=job_id, kind="reserved", provider=provider, note=note, home=home)
    return {**entry, "reused": False}


def release(job_id: str, *, home: Path | None = None, note: str | None = None) -> dict[str, Any]:
    """Record release for the open amount when > 0; otherwise no-op."""
    amount = open_reservation(job_id, home)
    if amount > 0:
        entry = record_spend(amount, job_id=job_id, kind="release", note=note, home=home)
        return {**entry, "released_usd": amount}
    return {"released_usd": 0.0}


def show(home: Path | None = None) -> dict[str, Any]:
    machine = load(home)
    return {**(machine or {"approved": False, "note": "no budget set; paid options require: agent-os orchestrate budget set --project-usd N --job-cap-usd M"}),
            "spent_usd": spent(home), "remaining_usd": remaining(home), "path": str(budget_path(home))}
