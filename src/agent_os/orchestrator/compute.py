"""Compute Broker, read-only slice: GPU inventory and pricing (IMP-0015 Phase 2).

Provider-neutral interface: an inventory source returns normalized GPU
offers ``{provider, gpu_id, name, vram_gb, tier, usd_per_hour}``; the broker
filters them against a workload and turns them into quote.py options. The
scheduler and quote engine never see vendor-specific fields.

First source: RunPod's public GraphQL ``gpuTypes`` (secure and community
prices; 0 means the tier does not offer that GPU). A key is optional
(``secrets://runpod/default``) and only sent when configured. Results are
cached under ``<orchestrator home>/compute-inventory/`` with a timestamp so
repeated quotes do not re-query.

Nothing here provisions, reserves or spends: provisioning is a later,
budget-gated slice (quote.budget_gate).
"""

from __future__ import annotations

import json
import time
import urllib.request
from pathlib import Path
from typing import Any, Callable

from ..timestamps import utc_now_iso
from .store import orchestrator_home

RUNPOD_GRAPHQL = "https://api.runpod.io/graphql"
RUNPOD_SECRET = "secrets://runpod/default"
GPU_QUERY = "query { gpuTypes { id displayName memoryInGb securePrice communityPrice secureCloud communityCloud } }"
CACHE_SECONDS = 6 * 3600


def _cache_path(provider: str, home: Path | None = None) -> Path:
    return Path(home or orchestrator_home()) / "compute-inventory" / f"{provider}.json"


def normalize_runpod(payload: dict[str, Any]) -> list[dict[str, Any]]:
    offers = []
    for item in ((payload.get("data") or {}).get("gpuTypes") or []):
        if not isinstance(item, dict):
            continue
        for tier, price_key, flag_key in (("secure", "securePrice", "secureCloud"), ("community", "communityPrice", "communityCloud")):
            price = item.get(price_key)
            if not isinstance(price, (int, float)) or price <= 0 or item.get(flag_key) is False:
                continue
            offers.append({"provider": "runpod", "gpu_id": str(item.get("id")), "name": str(item.get("displayName") or item.get("id")),
                           "vram_gb": item.get("memoryInGb"), "tier": tier, "usd_per_hour": float(price)})
    offers.sort(key=lambda offer: (offer["usd_per_hour"], -(offer["vram_gb"] or 0)))
    return offers


def runpod_inventory(*, refresh: bool = False, home: Path | None = None, opener: Callable[..., Any] | None = None,
                     now: Callable[[], float] = time.time) -> dict[str, Any]:
    """Live (or cached) RunPod GPU offers. Never raises for network errors;
    returns ``{"offers": [], "error": ...}`` so quoting degrades gracefully."""
    cache = _cache_path("runpod", home)
    if not refresh and cache.exists():
        try:
            cached = json.loads(cache.read_text(encoding="utf-8"))
            if now() - float(cached.get("fetched_epoch", 0)) < CACHE_SECONDS:
                return {**cached, "source": "cache"}
        except (OSError, ValueError):
            pass
    from .secret_refs import resolve

    headers = {"content-type": "application/json", "user-agent": "agent-os/1"}
    key = resolve(RUNPOD_SECRET)
    if key:
        headers["authorization"] = f"Bearer {key}"
    request = urllib.request.Request(RUNPOD_GRAPHQL, data=json.dumps({"query": GPU_QUERY}).encode(), headers=headers, method="POST")
    try:
        with (opener or urllib.request.urlopen)(request, timeout=30) as response:
            payload = json.loads(response.read().decode())
    except Exception as exc:  # network/provider failure is data, not a crash
        return {"provider": "runpod", "offers": [], "error": f"{type(exc).__name__}: {str(exc)[:200]}", "source": "live"}
    if payload.get("errors"):
        return {"provider": "runpod", "offers": [], "error": str(payload["errors"])[:300], "source": "live"}
    result = {"provider": "runpod", "fetched_at": utc_now_iso(), "fetched_epoch": now(), "authenticated": bool(key), "offers": normalize_runpod(payload)}
    from ..storage import write_json

    write_json(cache, result)
    return {**result, "source": "live"}


INVENTORIES: dict[str, Callable[..., dict[str, Any]]] = {"runpod": runpod_inventory}


def inventory(provider: str = "runpod", **kwargs: Any) -> dict[str, Any]:
    if provider not in INVENTORIES:
        raise ValueError(f"unknown compute provider {provider!r}; known: {sorted(INVENTORIES)}")
    return INVENTORIES[provider](**kwargs)


def gpu_options(offers: list[dict[str, Any]], workload: dict[str, Any], *, gen_tokens_per_second: float | None = None,
                train_tokens_per_second: float | None = None, limit: int = 5, tiers: tuple[str, ...] = ("secure", "community"),
                startup_minutes: float = 8.0, idle_minutes: float = 10.0) -> list[dict[str, Any]]:
    """Cheapest offers that meet the workload's VRAM floor, as quote options.

    Throughput must be supplied by the caller (measured or taken from the
    serving engine's benchmark for this model and GPU); the broker does not
    invent it. Without throughput no priced options are produced.
    """
    training = workload.get("type") in {"training", "fine_tune", "adapter_training"}
    rate = train_tokens_per_second if training else gen_tokens_per_second
    if not rate:
        return []
    floor = float((workload.get("resources") or {}).get("vram_gb") or 0)
    gpus = int((workload.get("resources") or {}).get("gpus") or 1)
    chosen = [offer for offer in offers if offer["tier"] in tiers and (offer["vram_gb"] or 0) >= floor][:limit]
    key = "train_tokens_per_second" if training else "gen_tokens_per_second"
    return [{"kind": "gpu_pod", "id": f"{offer['provider']}:{offer['name']}:{offer['tier']}", "gpu_hourly_usd": offer["usd_per_hour"], "gpus": gpus,
             key: float(rate), "startup_minutes": startup_minutes, "idle_minutes": idle_minutes, "vram_gb": offer["vram_gb"]} for offer in chosen]
