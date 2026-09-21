"""Provider-neutral capability classes and run-time provider resolution.

A stage declares the *class* of capability its work needs, never a vendor's
model name. Concrete models are resolved at execution time from whatever
providers this machine has configured, so a workflow authored on one computer
stays runnable on another, and a provider can be added or retired without
touching a manifest.

Nothing in this module may name a provider or a model. The provider registry is
data (`~/.agent-os/providers.json`, or an explicit path), not code.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from .machine import CONFIG_DIR


# Ordered cheapest to most expensive. Escalation walks this ladder one rung at a
# time so a failed cheap stage does not jump straight to the costliest option.
CAPABILITY_CLASSES: tuple[str, ...] = ("deterministic", "fast", "balanced", "reasoning", "frontier")

# How a stage prefers to be satisfied, tried in this order by policy.
EXECUTION_PATHS: tuple[str, ...] = ("deterministic", "cache", "skill", "model")

EFFORTS: tuple[str, ...] = ("none", "low", "medium", "high")

PROVIDER_REGISTRY_ENV = "AGENT_OS_PROVIDERS"
PROVIDER_REGISTRY_PATH = CONFIG_DIR / "providers.json"


def registry_path() -> Path:
    override = os.environ.get(PROVIDER_REGISTRY_ENV)
    return Path(override).expanduser() if override else PROVIDER_REGISTRY_PATH


class UnknownCapabilityClass(ValueError):
    pass


def rank(capability_class: str) -> int:
    try:
        return CAPABILITY_CLASSES.index(capability_class)
    except ValueError as exc:
        raise UnknownCapabilityClass(f"unsupported capability class: {capability_class}") from exc


def is_at_least(candidate: str, minimum: str) -> bool:
    return rank(candidate) >= rank(minimum)


def next_class(capability_class: str) -> str | None:
    """The next rung up, or None when already at the top of the ladder."""
    position = rank(capability_class)
    if position + 1 >= len(CAPABILITY_CLASSES):
        return None
    return CAPABILITY_CLASSES[position + 1]


def load_providers(path: Path | None = None) -> dict[str, Any]:
    """Read the machine-local provider registry, or report that there is none.

    An absent registry is a normal state, not an error: the orchestrator still
    recommends a capability class, and the operator chooses the model.
    """
    location = path or registry_path()
    try:
        data = json.loads(location.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return {"configured": False, "path": str(location), "providers": []}
    providers = data.get("providers")
    if not isinstance(providers, list):
        return {"configured": False, "path": str(location), "providers": []}
    return {"configured": True, "path": str(location), "providers": providers}


def resolve(capability_class: str, path: Path | None = None) -> dict[str, Any]:
    """Resolve a capability class to a concrete provider/model, if one exists.

    Returns an honest unresolved result rather than inventing a model name when
    no provider is configured or none covers the requested class.
    """
    rank(capability_class)
    registry = load_providers(path)
    for provider in registry["providers"]:
        if not isinstance(provider, dict) or not provider.get("enabled", True):
            continue
        models = provider.get("models")
        if not isinstance(models, dict):
            continue
        model = models.get(capability_class)
        if model:
            return {
                "capability_class": capability_class,
                "resolved": True,
                "provider": provider.get("id"),
                "model": model,
                "source": registry["path"],
            }
    return {
        "capability_class": capability_class,
        "resolved": False,
        "provider": None,
        "model": None,
        "reason": (
            "no provider is configured on this machine"
            if not registry["configured"]
            else "no configured provider covers this capability class"
        ),
        "source": registry["path"],
    }
