"""Read-only Model & Compute view for the orchestrator GUI (IMP-0015).

Roadmap "Observability / UI": one page showing the model registry with
profiles, newly discovered catalog models, GPU prices, measured throughput,
the eval queue, refusal telemetry and shadow-foreman comparisons. Everything
here reads local state only: GPU inventory comes from the cache (``compute
inventory`` refreshes it), so opening the page never triggers a network call
or a model call, and nothing on it can provision, spend or change routing.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .store import orchestrator_home


def _cached_inventory(home: Path) -> dict[str, Any]:
    from .compute import _cache_path

    try:
        data = json.loads(_cache_path("runpod", home).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"provider": "runpod", "offers": [], "fetched_at": None, "note": "no cached inventory; run: agent-os orchestrate compute inventory"}
    return {"provider": "runpod", "fetched_at": data.get("fetched_at"), "offers": (data.get("offers") or [])[:12]}


def build(home: Path | None = None, registry: Any = None) -> dict[str, Any]:
    from . import evalqueue, foreman, radar, refusal, throughput
    from .router import ProviderRegistry

    home = Path(home or orchestrator_home())
    registry = registry or ProviderRegistry(discover=False)
    providers = [{"id": item["id"], "adapter": item["adapter"], "enabled": item["enabled"], "roles": item["roles"],
                  "classes": sorted(item["models"]), "models": sorted(set(item["models"].values())), **(item.get("profile") or {})}
                 for item in registry.providers]
    queue = list(evalqueue.current(home).values())
    statuses: dict[str, int] = {}
    for entry in queue:
        statuses[entry.get("status", "queued")] = statuses.get(entry.get("status", "queued"), 0) + 1
    catalog = radar.catalog_summary(home, limit=10)
    abliterated = radar.catalog_summary(home, refusal_profile="abliterated", limit=5)
    shadow = foreman.report(home)
    return {
        "providers": providers,
        "catalog": {"size": catalog.get("catalog_size", 0), "top": catalog.get("models", []), "abliterated": abliterated.get("models", [])},
        "inventory": _cached_inventory(home),
        "throughput": throughput.load(home)[-10:],
        "eval_queue": {"total": len(queue), "by_status": statuses,
                       "recent": sorted(queue, key=lambda entry: entry.get("at") or "", reverse=True)[:8]},
        "refusals": refusal.summary(home),
        "foreman": shadow.get("foremen", {}),
        "note": "read-only: nothing here provisions, spends or changes routing; paid compute needs an approved budget with a job hard cap",
    }
