"""Price and benchmark evidence used to compare configured model tiers."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

from ..timestamps import utc_now_iso
from .models import version_key
from .store import orchestrator_home

CACHE_SHARE = 0.9
OUTPUT_RATIO = 0.02
DESIGN_TIERS = ("reasoning", "frontier")
IMPLEMENTATION_TIERS = ("fast", "balanced")


def evidence_path() -> Path:
    return orchestrator_home() / "models" / "evidence.json"


def load_evidence() -> dict:
    try:
        value = json.loads(evidence_path().read_text(encoding="utf-8"))
        return value if isinstance(value, dict) and isinstance(value.get("models"), dict) else {"models": {}}
    except (OSError, json.JSONDecodeError):
        return {"models": {}}


def save_evidence(evidence: dict) -> None:
    path = evidence_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(evidence, indent=1), encoding="utf-8")


def record_evidence(
    model_id: str,
    *,
    provider: str | None = None,
    price: dict | None = None,
    benchmarks: dict | None = None,
    source: str | None = None,
) -> dict:
    evidence = load_evidence()
    entry = evidence["models"].setdefault(model_id, {})
    if provider is not None:
        entry["provider"] = provider
    for field, updates in (("price", price), ("benchmarks", benchmarks)):
        if updates is not None:
            current = entry.setdefault(field, {})
            current.update({key: value for key, value in updates.items() if value is not None})
    if source:
        sources = entry.setdefault("sources", [])
        if source not in sources:
            sources.append(source)
    entry["updated_at"] = utc_now_iso()
    save_evidence(evidence)
    return entry


def _number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def effective_price(price: dict) -> float | None:
    if not isinstance(price, dict) or not all(_number(price.get(key)) for key in ("input", "cached_input", "output")):
        return None
    return round((1 - CACHE_SHARE) * price["input"] + CACHE_SHARE * price["cached_input"] + OUTPUT_RATIO * price["output"], 6)


def resolve_model(provider_id: str, model: str, evidence: dict) -> str | None:
    models = evidence.get("models") or {}
    if model in models:
        return model
    if provider_id != "claude-code":
        return None
    candidates = []
    family = f"claude-{model}"
    for key in models:
        parsed = version_key(key)
        if parsed and parsed[0] == family:
            candidates.append((parsed[1], key))
    return max(candidates)[1] if candidates else None


def tier_costs(registry_providers: list[dict], evidence: dict) -> dict:
    result: dict[str, dict] = {"costs": {}, "tiers": {}}
    tiers = dict.fromkeys(tier for provider in registry_providers for tier in (provider.get("models") or {}))
    model_entries = evidence.get("models") or {}
    for tier in tiers:
        models: dict[str, str] = {}
        missing: list[str] = []
        scored: list[tuple[str, float]] = []
        design = tier in DESIGN_TIERS
        for provider in registry_providers:
            provider_id = provider.get("id")
            configured = (provider.get("models") or {}).get(tier)
            if not configured:
                continue
            resolved = resolve_model(provider_id, configured, evidence)
            if resolved is None:
                missing.append(f"{provider_id}:{configured} model")
                continue
            models[provider_id] = resolved
            entry = model_entries.get(resolved) or {}
            price = effective_price(entry.get("price") or {})
            if price is None:
                missing.append(f"{provider_id}:{resolved} price")
                continue
            if design:
                index = (entry.get("benchmarks") or {}).get("intelligence_index")
                if not _number(index):
                    missing.append(f"{provider_id}:{resolved} intelligence_index")
                    continue
                cost = round((100 - index) + price / 1000, 6)
            else:
                cost = price
            scored.append((provider_id, cost))
        state: dict[str, Any] = {"status": "needs_evidence" if missing else "ok", "winner": None, "models": models, "missing": missing}
        if not missing and scored:
            winner, _ = min(scored, key=lambda item: item[1])
            state["winner"] = winner
            for provider_id, cost in scored:
                result["costs"].setdefault(provider_id, {})[tier] = cost
        result["tiers"][tier] = state
    return result
