"""Operator-approved API budget and spend ledger for per-token API delegation.

Separate from host-plan (subscription CLI) usage and from the GPU compute budget
in budget.py. Keeps track of API spend for Anthropic/OpenAI providers.

Files:
- api-budget.json: current budget (total_usd, call_cap_usd, approved, set_by, set_at, note, currency, kind)
- api-budget-history.jsonl: append-only history of budget changes
- api-spend.jsonl: append-only ledger of API calls and their costs
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..timestamps import utc_now_iso
from ..storage import write_json
from .budget import _home


def api_budget_path(home: Path | None = None) -> Path:
    return _home(home) / "api-budget.json"


def load(home: Path | None = None) -> dict[str, Any]:
    try:
        data = json.loads(api_budget_path(home).read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def set_api_budget(total_usd: float, call_cap_usd: float, *, set_by: str = "operator", note: str | None = None,
                   home: Path | None = None) -> dict[str, Any]:
    """Operator action: set and approve the API budget; appends to the history."""
    total_usd, call_cap_usd = float(total_usd), float(call_cap_usd)
    if total_usd < 0 or call_cap_usd < 0:
        raise ValueError("budgets must be >= 0")
    if call_cap_usd > total_usd:
        raise ValueError("the per-call cap cannot exceed the total budget")
    previous = load(home)
    record = {"total_usd": total_usd, "call_cap_usd": call_cap_usd, "approved": True, "set_by": set_by,
              "set_at": utc_now_iso(), "note": note, "currency": "USD", "kind": "api"}
    write_json(api_budget_path(home), record)
    with (_home(home) / "api-budget-history.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps({"at": record["set_at"], "previous": previous or None, "current": record}) + "\n")
    return {**record, "spent_usd": api_spent(home), "remaining_usd": api_remaining(home)}


def record_api_spend(amount_usd: float, *, call_id: str, provider: str, model: str | None = None,
                     accuracy: str | None = None, note: str | None = None, home: Path | None = None) -> dict[str, Any]:
    """Record an API call's spend; appends to the spend ledger."""
    entry = {"at": utc_now_iso(), "call_id": call_id, "provider": provider, "model": model,
             "amount_usd": round(float(amount_usd), 6), "accuracy": accuracy, "note": note}
    path = _home(home) / "api-spend.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry) + "\n")
    return entry


def api_spent(home: Path | None = None) -> float:
    """Sum of all recorded API spend; skips malformed lines."""
    path = _home(home) / "api-spend.jsonl"
    total = 0.0
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            try:
                entry = json.loads(line)
                if not isinstance(entry, dict):
                    continue
                amount = float(entry.get("amount_usd") or 0)
                total += amount
            except (ValueError, TypeError):
                continue
    return round(total, 6)


def api_remaining(home: Path | None = None) -> float | None:
    """Remaining API budget; None when no budget set, else max(total_usd - spent, 0)."""
    budget = load(home)
    total = budget.get("total_usd")
    return None if total is None else round(max(float(total) - api_spent(home), 0.0), 6)


def check(home: Path | None = None) -> dict[str, Any]:
    """Check if API delegation is allowed under the current budget."""
    budget = load(home)
    call_cap = budget.get("call_cap_usd")
    remaining = api_remaining(home)

    if not budget.get("approved"):
        return {
            "allowed": False,
            "reason": "no API budget set; run: agent-os orchestrate api-budget set --total-usd N --call-cap-usd M",
            "remaining_usd": remaining,
            "call_cap_usd": call_cap,
        }

    if remaining is not None and remaining <= 0:
        return {
            "allowed": False,
            "reason": "API budget exhausted",
            "remaining_usd": remaining,
            "call_cap_usd": call_cap,
        }

    return {
        "allowed": True,
        "reason": "within API budget",
        "remaining_usd": remaining,
        "call_cap_usd": call_cap,
    }


def is_api_provider(provider: dict[str, Any]) -> bool:
    """Check if a provider uses API deployment (Anthropic/OpenAI style)."""
    from . import model_profile

    profile = provider.get("profile") or model_profile.normalize_profile(None, provider.get("adapter"), provider.get("options"))
    return str(profile.get("deployment") or "") == "api"
