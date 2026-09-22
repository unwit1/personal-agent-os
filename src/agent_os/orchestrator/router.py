"""Deterministic model routing: capability class + effort -> provider/model/effort.

The router reads the machine-local provider registry (the same
``~/.agent-os/providers.json`` the staged workflow runner uses) extended with
adapter, effort-map, concurrency, and role fields. It never names a provider or
a model itself and never spends a model call to decide which model to launch.

Precedence, highest first:

1. an explicit user override stored in run state (node > role > run);
2. providers that are enabled, available, not excluded for this node, under
   their concurrency limit, and allowed for the role;
3. the requested capability class, shifted by the run's economy/quality
   preference, falling back to the nearest *stronger* class a provider covers
   and only then to a weaker one.

Every selection carries a compact explanation so the choice is observable.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..capabilities import CAPABILITY_CLASSES, load_providers, rank


MODEL_CLASSES = tuple(item for item in CAPABILITY_CLASSES if item != "deterministic")


def normalize_provider(raw: dict[str, Any], order: int) -> dict[str, Any] | None:
    if not isinstance(raw, dict) or not raw.get("id"):
        return None
    models = raw.get("models") if isinstance(raw.get("models"), dict) else {}
    effort_map = raw.get("effort_map") if isinstance(raw.get("effort_map"), dict) else {}
    roles = raw.get("roles")
    return {
        "id": str(raw["id"]),
        "enabled": bool(raw.get("enabled", True)),
        "adapter": raw.get("adapter"),
        "executable": raw.get("executable"),
        "models": {key: str(value) for key, value in models.items() if value and not str(value).startswith("<")},
        "effort_map": {key: str(value) for key, value in effort_map.items() if value and not str(value).startswith("<")},
        "max_concurrency": max(int(raw.get("max_concurrency", 1) or 1), 1),
        "priority": int(raw.get("priority", order)),
        "roles": list(roles) if isinstance(roles, list) else None,
        "env_allowlist": list(raw.get("env_allowlist") or []),
        "options": dict(raw.get("options") or {}),
    }


class ProviderRegistry:
    def __init__(self, path: Path | None = None, providers: list[dict[str, Any]] | None = None) -> None:
        if providers is not None:
            raw = {"configured": True, "path": "<inline>", "providers": providers}
        else:
            raw = load_providers(path)
        self.path = raw["path"]
        self.configured = raw["configured"]
        normalized = [normalize_provider(item, index) for index, item in enumerate(raw["providers"])]
        self.providers = sorted((item for item in normalized if item), key=lambda item: item["priority"])

    def get(self, provider_id: str) -> dict[str, Any] | None:
        for provider in self.providers:
            if provider["id"] == provider_id:
                return provider
        return None

    def describe(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "configured": self.configured,
            "providers": [
                {
                    "id": item["id"],
                    "enabled": item["enabled"],
                    "adapter": item["adapter"],
                    "models": item["models"],
                    "effort_map": item["effort_map"],
                    "max_concurrency": item["max_concurrency"],
                    "roles": item["roles"],
                }
                for item in self.providers
            ],
        }


def shift_class(capability_class: str, preference: str) -> str:
    """Economy lowers one rung, quality raises one; model work stays >= fast."""
    if capability_class == "deterministic":
        return capability_class
    position = rank(capability_class)
    if preference == "economy":
        position -= 1
    elif preference == "quality":
        position += 1
    position = max(rank("fast"), min(position, len(CAPABILITY_CLASSES) - 1))
    return CAPABILITY_CLASSES[position]


def _class_candidates(capability_class: str) -> list[str]:
    """Requested class first, then stronger classes, then weaker ones."""
    position = rank(capability_class)
    stronger = [item for item in MODEL_CLASSES if rank(item) > position]
    weaker = [item for item in reversed(MODEL_CLASSES) if rank(item) < position]
    exact = [capability_class] if capability_class in MODEL_CLASSES else []
    return exact + stronger + weaker


def resolve_effort(provider: dict[str, Any], effort: str) -> str | None:
    if effort in provider["effort_map"]:
        return provider["effort_map"][effort]
    if effort == "none":
        return None
    return effort


def select(
    registry: ProviderRegistry,
    *,
    capability_class: str,
    effort: str,
    role: str,
    preference: str = "balanced",
    availability: dict[str, bool] | None = None,
    excluded: list[str] | None = None,
    avoid: list[str] | None = None,
    running: dict[str, int] | None = None,
    override: dict[str, Any] | None = None,
    require_avoid: bool = False,
) -> dict[str, Any]:
    """Choose a provider/model/effort for one node. Pure and deterministic.

    ``avoid`` lists providers to prefer against (the author, for an independent
    review); with ``require_avoid`` they are excluded outright.
    """
    availability = availability or {}
    excluded_set = set(excluded or [])
    avoid_set = set(avoid or [])
    running = running or {}
    override = {key: value for key, value in (override or {}).items() if value}
    target_class = shift_class(capability_class, preference)
    notes: list[str] = []
    if target_class != capability_class:
        notes.append(f"{preference} preference moved {capability_class} to {target_class}")

    def usable(provider: dict[str, Any], *, ignore_capacity: bool = False) -> str | None:
        if not provider["enabled"]:
            return "disabled"
        if availability.get(provider["id"]) is False:
            return "unavailable"
        if provider["id"] in excluded_set:
            return "excluded after a provider failure on this node"
        if provider["roles"] is not None and role not in provider["roles"]:
            return f"not configured for role {role}"
        if require_avoid and provider["id"] in avoid_set:
            return "an independent reviewer must use a different provider"
        if not ignore_capacity and running.get(provider["id"], 0) >= provider["max_concurrency"]:
            return "at its concurrency limit"
        return None

    rejected: dict[str, str] = {}

    if override.get("provider"):
        provider = registry.get(str(override["provider"]))
        problem = "not configured" if provider is None else usable(provider)
        if provider is not None and problem is None:
            model = override.get("model") or _model_for(provider, target_class)[0]
            if model:
                return _selection(
                    provider,
                    model=str(model),
                    capability_class=target_class,
                    effort=str(override.get("effort") or effort),
                    reason="user override",
                    overridden=True,
                    notes=notes,
                )
            problem = f"covers no model for {target_class}"
        if problem == "at its concurrency limit":
            return {"resolved": False, "waiting": True, "reason": f"override provider {override['provider']} is {problem}"}
        notes.append(f"override provider {override['provider']} ignored: {problem}")

    ordered = sorted(registry.providers, key=lambda item: (item["id"] in avoid_set, item["priority"]))
    waiting = False
    for candidate_class in _class_candidates(target_class):
        for provider in ordered:
            problem = usable(provider)
            if problem:
                rejected.setdefault(provider["id"], problem)
                if problem == "at its concurrency limit":
                    waiting = True
                continue
            model = provider["models"].get(candidate_class)
            if not model:
                continue
            reason = "configured model for requested class"
            if candidate_class != target_class:
                reason = f"no enabled provider covers {target_class}; nearest covered class {candidate_class}"
            if override.get("model") and not override.get("provider"):
                model = str(override["model"])
                reason = "user model override"
            if provider["id"] in avoid_set:
                notes.append("no distinct provider available; review independence is session-level only")
            return _selection(
                provider,
                model=model,
                capability_class=candidate_class,
                effort=str(override.get("effort") or effort),
                reason=reason,
                overridden=bool(override),
                notes=notes,
            )
    if waiting:
        return {"resolved": False, "waiting": True, "reason": "every suitable provider is at its concurrency limit", "rejected": rejected}
    if not registry.configured:
        reason = "no provider registry is configured on this machine"
    elif not registry.providers:
        reason = "the provider registry lists no providers"
    else:
        reason = f"no usable provider covers {target_class} or any fallback class"
    return {"resolved": False, "waiting": False, "reason": reason, "rejected": rejected, "notes": notes}


def _model_for(provider: dict[str, Any], capability_class: str) -> tuple[str | None, str | None]:
    for candidate in _class_candidates(capability_class):
        if provider["models"].get(candidate):
            return provider["models"][candidate], candidate
    return None, None


def _selection(
    provider: dict[str, Any],
    *,
    model: str,
    capability_class: str,
    effort: str,
    reason: str,
    overridden: bool,
    notes: list[str],
) -> dict[str, Any]:
    return {
        "resolved": True,
        "provider": provider["id"],
        "adapter": provider["adapter"],
        "model": model,
        "capability_class": capability_class,
        "effort": effort,
        "provider_effort": resolve_effort(provider, effort),
        "overridden": overridden,
        "reason": reason,
        "notes": notes,
    }
