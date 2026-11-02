"""Quote and budget engine (IMP-0015, roadmap "Intelligent quote and budget engine").

Deterministic, no network, no spend. Given a workload (workload.py) and
candidate options -- a pay-per-token API, a temporary GPU pod, a serverless
GPU endpoint -- it estimates the **expected total cost of a verified success**
with low/expected/high bands, and says whether the budget policy allows it
to start.

Inputs are explicit prices (USD per million tokens; USD per GPU-hour), so a
live pricing adapter (RunPod inventory, a provider price page) only has to
supply numbers. Throughput and failure rates are estimates; the bands carry
that uncertainty instead of hiding it.

Budget gate (roadmap invariant 6, acceptance 5): a paid option is ``allowed``
only when the workload's budget is ``approved`` **and** the high estimate fits
the job hard cap (and the project budget, when set). Otherwise the quote says
``requires_approval`` with the reason. A quote never starts anything.
"""

from __future__ import annotations

import math
from typing import Any

SCHEMA = "personal-agent/compute-quote/v1"
# Relative uncertainty applied to throughput/runtime estimates.
BANDS = {"low": 0.75, "expected": 1.0, "high": 1.5}


def _retry_factor(failure_rate: float) -> float:
    """Expected attempts per verified success, geometric with a cap."""
    failure_rate = min(max(float(failure_rate), 0.0), 0.9)
    return 1.0 / (1.0 - failure_rate)


def api_option(option: dict[str, Any], workload: dict[str, Any]) -> dict[str, Any]:
    """Pay-per-token API: cost = tokens x price x expected attempts."""
    size = workload.get("size") or {}
    items = max(size.get("items") or 1, 1)
    tokens_in = (size.get("input_tokens") or 0) * items
    tokens_out = (size.get("output_tokens") or 0) * items
    price_in, price_out = float(option["price_in_per_mtok"]), float(option["price_out_per_mtok"])
    attempts = _retry_factor(option.get("failure_rate", 0.05))
    base = (tokens_in * price_in + tokens_out * price_out) / 1_000_000 * attempts
    return {"kind": "api", "id": option.get("id", "api"), "tokens_in": tokens_in, "tokens_out": tokens_out, "attempts_per_success": round(attempts, 3),
            "cost_usd": {band: round(base * (1.0 if band == "expected" else factor), 4) for band, factor in (("low", 0.9), ("expected", 1.0), ("high", 1.25))},
            "startup_minutes": 0.0}


def gpu_option(option: dict[str, Any], workload: dict[str, Any]) -> dict[str, Any]:
    """Temporary pod or serverless GPU. Runtime from throughput; adds startup
    (image pull + model load), idle tail, storage and expected retries."""
    size = workload.get("size") or {}
    hourly = float(option["gpu_hourly_usd"]) * max(int(option.get("gpus", 1)), 1)
    if workload.get("type") in {"training", "fine_tune", "adapter_training"}:
        work_tokens = (size.get("dataset_tokens") or 0) * max(size.get("epochs") or 1, 1)
        rate = float(option["train_tokens_per_second"])
    else:
        items = max(size.get("items") or 1, 1)
        work_tokens = ((size.get("input_tokens") or 0) * float(option.get("prefill_weight", 0.1)) + (size.get("output_tokens") or 0)) * items
        rate = float(option["gen_tokens_per_second"])
    if rate <= 0:
        raise ValueError("throughput must be > 0")
    serverless = option.get("kind") == "serverless"
    startup = float(option.get("startup_minutes", 1.0 if serverless else 8.0))
    idle = float(option.get("idle_minutes", 0.0 if serverless else 10.0))
    storage = float(option.get("storage_gb", 0)) * float(option.get("storage_usd_per_gb_hour", 0.0))
    attempts = _retry_factor(option.get("failure_rate", 0.1))
    costs, hours = {}, {}
    for band, factor in BANDS.items():
        run_hours = work_tokens / rate / 3600 * factor * attempts
        billed = run_hours + (startup + idle) / 60
        if serverless:
            billed = math.ceil(billed * 3600) / 3600  # per-second billing
        hours[band] = round(billed, 4)
        costs[band] = round(billed * (hourly + storage), 4)
    return {"kind": option.get("kind", "gpu_pod"), "id": option.get("id", "gpu"), "work_tokens": work_tokens, "attempts_per_success": round(attempts, 3),
            "billed_hours": hours, "cost_usd": costs, "startup_minutes": startup}


def budget_gate(cost_high: float, workload: dict[str, Any], budget_state: dict[str, Any] | None = None) -> dict[str, Any]:
    """``budget_state`` is the effective operator budget (budget.effective);
    without it the workload's own budget block applies."""
    budget = budget_state if budget_state is not None else (workload.get("budget") or {})
    if cost_high <= 0:
        return {"allowed": True, "requires_approval": False, "reason": "no paid spend"}
    if not budget.get("approved"):
        return {"allowed": False, "requires_approval": True, "reason": "paid option and the workload budget is not approved"}
    cap = budget.get("job_hard_cap_usd")
    if cap is None:
        return {"allowed": False, "requires_approval": True, "reason": "no job hard cap set"}
    if cost_high > cap:
        return {"allowed": False, "requires_approval": True, "reason": f"high estimate ${cost_high:.2f} exceeds job hard cap ${cap:.2f}"}
    project = budget.get("project_usd")
    if project is not None and cost_high > project:
        return {"allowed": False, "requires_approval": True, "reason": f"high estimate ${cost_high:.2f} exceeds project budget ${project:.2f}"}
    return {"allowed": True, "requires_approval": False, "reason": f"within job hard cap ${cap:.2f}"}


def quote(workload: dict[str, Any], options: list[dict[str, Any]], budget_state: dict[str, Any] | None = None) -> dict[str, Any]:
    """Price every option, rank by expected cost, attach the budget gate."""
    if not options:
        raise ValueError("at least one option is required")
    priced = []
    for option in options:
        kind = option.get("kind", "api")
        item = api_option(option, workload) if kind == "api" else gpu_option(option, workload)
        item["gate"] = budget_gate(item["cost_usd"]["high"], workload, budget_state)
        priced.append(item)
    priced.sort(key=lambda item: (item["cost_usd"]["expected"], item["cost_usd"]["high"]))
    best = priced[0]
    result = {"schema": SCHEMA, "workload_type": workload.get("type"), "options": priced, "recommended": best["id"],
              "recommended_gate": best["gate"], "budget": budget_state, "note": "estimate only; nothing was provisioned or spent"}
    apis = [item for item in priced if item["kind"] == "api"]
    gpus = [item for item in priced if item["kind"] != "api"]
    if apis and gpus:
        result["api_vs_gpu"] = {"cheapest_api": apis[0]["id"], "cheapest_gpu": gpus[0]["id"],
                                "gpu_saving_usd_expected": round(apis[0]["cost_usd"]["expected"] - gpus[0]["cost_usd"]["expected"], 4)}
    return result
