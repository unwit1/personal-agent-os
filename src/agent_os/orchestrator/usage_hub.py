"""One view of every plan's usage: the Command Center's Usage panel and
``orchestrate headroom`` read this.

* plans: allowance windows per subscription (headroom.py), one row per plan
  rather than per registry entry (every NanoGPT entry shares one allowance);
* free: OpenRouter free-model requests left today (free_quota.Governor);
* extras: one-time credits and saved resets, with advice (plan_extras.py);
* cloud: recent Claude cloud sessions (cloud_lane.py).

Read-only; the Claude probe runs in the background unless ``refresh``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

LABELS = {"claude": "Claude (Claude Code)", "codex": "ChatGPT (Codex)", "nanogpt": "NanoGPT subscription"}


def _home() -> Path:
    from ..capabilities import registry_path

    return registry_path().parent


def plans(providers: list[dict[str, Any]], home: Path, *, refresh: bool = False) -> list[dict[str, Any]]:
    from . import headroom

    per_provider = headroom.for_providers(providers, home, force=refresh, background=not refresh)
    rows: dict[str, dict[str, Any]] = {}
    for provider_id, plan in per_provider.items():
        source = str(plan.get("source"))
        row = rows.setdefault(source, {"plan": source, "label": LABELS.get(source, source), "providers": [], **{
            key: plan.get(key) for key in ("state", "multiplier", "detail", "windows", "overage", "until") if plan.get(key) is not None}})
        row["providers"].append(provider_id)
    return sorted(rows.values(), key=lambda row: row["plan"])


def free(home: Path | None = None, *, refresh: bool = False) -> dict[str, Any]:
    try:
        from .free_dispatch import FreeInputs

        if refresh:
            from . import free_catalog, openrouter_account

            openrouter_account.refresh(home)
            free_catalog.discover(refresh=True, home=home)
        inputs = FreeInputs.load_default(home)
        remaining = inputs.governor.remaining()
        allowance = getattr(inputs.governor, "allowance", None)
        # The broker's catalog holds only free models (free_catalog.normalize_openrouter).
        models = [item.get("slug") for item in (inputs.catalog.get("models") or []) if item.get("slug")]
        return {"provider": "openrouter", "daily_allowance": allowance, **remaining, "free_models": models,
                "note": "free requests count per day across all :free models; the broker refreshes its catalog with orchestrate free"}
    except Exception as exc:  # the broker is optional; report, do not fail
        return {"provider": "openrouter", "error": f"{type(exc).__name__}: {exc}"}


def summary(*, refresh: bool = False, home: Path | None = None, providers: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    from . import cloud_lane, plan_extras
    from .router import ProviderRegistry

    home = home or _home()
    providers = providers if providers is not None else ProviderRegistry().providers
    plan_rows = plans(providers, home, refresh=refresh)
    extras = plan_extras.load(home)
    by_provider = {provider_id: row for row in plan_rows for provider_id in row["providers"]}
    tips = plan_extras.advice(extras, {key: {**row, "source": row["plan"]} for key, row in by_provider.items()})
    return {
        "plans": plan_rows,
        "free": free(refresh=refresh),
        "extras": list(extras.values()),
        "advice": tips,
        "cloud_sessions": cloud_lane.sessions(home)[:10],
    }
