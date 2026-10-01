"""Free-model catalog for the FreeComputeBroker (IMP-0015).

Discovers which OpenRouter models are currently priced at zero. The pool is
whatever the provider reports, so models join or leave without a code edit;
no model slugs are hard-coded. Follows the ``compute.runpod_inventory``
pattern: injected opener, injectable clock, cached under
``<orchestrator home>/free-compute/catalog/`` and network failures returned as
``{"error": ...}`` data, never raised.
"""

from __future__ import annotations

import hashlib
import json
import time
import urllib.request
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Callable

from ..timestamps import utc_now_iso
from .store import orchestrator_home

OPENROUTER_MODELS_URL = "https://openrouter.ai/api/v1/models"
SCHEMA_VERSION = "agent-os/free-catalog-snapshot/v1"
CACHE_SECONDS = 6 * 3600
FREE_SUFFIX = ":free"
VOLATILE_FIELDS = ("first_seen", "last_seen", "last_verified")


def _cache_path(home: Path | None = None) -> Path:
    return Path(home or orchestrator_home()) / "free-compute" / "catalog" / "latest.json"


def _zero(value: Any) -> bool:
    if isinstance(value, bool) or value is None:
        return False
    try:
        return Decimal(str(value).strip()) == 0
    except (InvalidOperation, ValueError):
        return False


def is_free(pricing: Any) -> bool:
    """True when prompt and completion parse to 0 and no other priced
    dimension is non-zero. Missing, empty or malformed pricing is not free."""
    if not isinstance(pricing, dict) or "prompt" not in pricing or "completion" not in pricing:
        return False
    return all(_zero(value) for value in pricing.values())


def _model_free(item: dict[str, Any]) -> bool:
    return is_free(item.get("pricing")) or str(item.get("id") or "").endswith(FREE_SUFFIX)


def normalize_openrouter(payload: dict[str, Any]) -> list[dict[str, Any]]:
    models = []
    for item in (payload.get("data") or []) if isinstance(payload, dict) else []:
        if not isinstance(item, dict) or not item.get("id") or not _model_free(item):
            continue
        arch = item.get("architecture") if isinstance(item.get("architecture"), dict) else {}
        params = item.get("supported_parameters") if isinstance(item.get("supported_parameters"), list) else []
        canonical = item.get("canonical_slug") or None
        models.append({
            "slug": item["id"],
            "canonical_slug": canonical,
            "revision": canonical,
            "context_length": item.get("context_length"),
            "modalities": {"input": list(arch.get("input_modalities") or []), "output": list(arch.get("output_modalities") or [])},
            "supports_tools": "tools" in params,
            "supports_structured_output": "structured_outputs" in params or "response_format" in params,
            "pricing": dict(item["pricing"]) if isinstance(item.get("pricing"), dict) else {},
        })
    return sorted(models, key=lambda m: m["slug"])


def _stable(model: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in model.items() if k not in VOLATILE_FIELDS}


def catalog_hash(models: list[dict[str, Any]]) -> str:
    blob = json.dumps([_stable(m) for m in models], sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode()).hexdigest()


def diff(previous: dict[str, Any] | None, current: dict[str, Any] | None) -> dict[str, Any]:
    before = {m["slug"]: m for m in (previous or {}).get("models", [])}
    after = {m["slug"]: m for m in (current or {}).get("models", [])}
    changed = []
    for slug in sorted(before.keys() & after.keys()):
        old, new = _stable(before[slug]), _stable(after[slug])
        fields = {k: [old.get(k), new.get(k)] for k in sorted(old.keys() | new.keys()) if old.get(k) != new.get(k)}
        if fields:
            changed.append({"slug": slug, "fields": fields})
    return {"added": sorted(after.keys() - before.keys()), "removed": sorted(before.keys() - after.keys()), "changed": changed}


def _read_cache(cache: Path) -> dict[str, Any] | None:
    try:
        data = json.loads(cache.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) and isinstance(data.get("models"), list) else None


def discover(*, refresh: bool = False, home: Path | None = None, opener: Callable[..., Any] | None = None,
             now: Callable[[], float] = time.time) -> dict[str, Any]:
    """Versioned snapshot of current free models. Never raises; on failure
    returns the last good snapshot marked ``stale`` (or an empty one) plus
    ``error``."""
    cache = _cache_path(home)
    previous = _read_cache(cache)
    if not refresh and previous and now() - float(previous.get("fetched_epoch", 0)) < CACHE_SECONDS:
        return {**previous, "source": "cache"}
    request = urllib.request.Request(OPENROUTER_MODELS_URL, headers={"accept": "application/json", "user-agent": "agent-os/1"})
    try:
        with (opener or urllib.request.urlopen)(request, timeout=30) as response:
            payload = json.loads(response.read().decode())
        if not isinstance(payload, dict) or not isinstance(payload.get("data"), list):
            raise ValueError("unexpected models payload")
    except Exception as exc:  # network/provider failure is data, not a crash
        error = f"{type(exc).__name__}: {str(exc)[:200]}"
        if previous:
            return {**previous, "stale": True, "error": error, "source": "cache"}
        return {"schema_version": SCHEMA_VERSION, "provider": "openrouter", "models": [], "error": error, "source": "live"}
    fetched_at = utc_now_iso()
    seen = {m["slug"]: m for m in (previous or {}).get("models", [])}
    models = normalize_openrouter(payload)
    for model in models:
        model["first_seen"] = (seen.get(model["slug"]) or {}).get("first_seen") or fetched_at
        model["last_seen"] = fetched_at
    snapshot = {
        "schema_version": SCHEMA_VERSION,
        "provider": "openrouter",
        "catalog_version": catalog_hash(models),
        "fetched_at": fetched_at,
        "fetched_epoch": now(),
        "source_url": OPENROUTER_MODELS_URL,
        "models": models,
    }
    from ..storage import write_json

    write_json(cache, snapshot)
    return {**snapshot, "source": "live"}
