"""Engine-facing glue for free-first routing (FreeComputeBroker, IMP-0015).

Pure functions over ``free_routing`` / ``router``: no model calls, no network.
Only ``FreeInputs.load_default`` reads disk, and it never calls
``free_catalog.discover``. See docs/free-compute-broker.md, "Engine
integration (free_routing_enabled)".
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..storage import load_json
from . import control_plane, free_catalog, free_policy, free_quota, free_routing, router
from .model import PROVIDER_FAILURES
from .store import orchestrator_home
from .workload import SENSITIVITY


def task_view(record: dict, node: dict) -> dict:
    """Map a node to the ``free_routing`` task shape. No field is invented."""
    requirements = node.get("requirements") or {}
    sensitivity = requirements.get("sensitivity")
    if sensitivity not in SENSITIVITY:
        sensitivity = "internal"
    deployment = requirements.get("deployment")
    if isinstance(deployment, str):
        deployment = [deployment]
    if deployment and "api" not in deployment:
        sensitivity = "private"  # free providers run under "api"; fail eligibility with a named reason
    validators = node.get("validators") or (record.get("policy") or {}).get("default_validators")
    return {
        "role": node.get("role"),
        "effort": node.get("effort"),
        "capability_class": node.get("capability_class"),
        "scope": node.get("scope"),
        "validators": validators,
        "task_family": node.get("task_family") or node.get("role"),
        "sensitivity": sensitivity,
        "run_id": record.get("id") or record.get("run_id"),
        "node_id": node.get("id"),
        "lane": "priority",
    }


class _RefusingGovernor:
    def can_spend(self, model: str, retry: int = 0) -> tuple[bool, str]:
        return False, "free quota unavailable"

    def remaining(self) -> dict:
        return {}


@dataclass
class FreeInputs:
    catalog: dict
    specializations: list
    governor: Any
    project_policy: dict

    @classmethod
    def load_default(cls, home: Path | None = None) -> "FreeInputs":
        try:
            home = Path(home) if home is not None else orchestrator_home()
            base = home / "free-compute"
            catalog = free_catalog._read_cache(free_catalog._cache_path(home)) or {"models": []}
            try:
                specializations = load_json(base / "specialization.json")
            except FileNotFoundError:
                specializations = []
            if not isinstance(specializations, list):
                specializations = []
            try:
                overrides = load_json(base / "policy-overrides.json")
            except FileNotFoundError:
                overrides = {}
            policy = free_policy.load(overrides=overrides)
            try:
                account = load_json(base / "account.json")
            except FileNotFoundError:
                account = {}
            high = account.get("high_allowance") if isinstance(account, dict) else None
            governor = free_quota.Governor(policy, high_tier=high, home=home)
            project_policy = dict(policy)
            project_policy["protected_globs"] = control_plane.protected_globs()
            project_policy["source"] = f"policy:openrouter/free-model-allowance@v{policy.get('version')}"
            return cls(catalog, specializations, governor, project_policy)
        except Exception:
            try:
                globs = control_plane.protected_globs()
            except Exception:
                globs = []
            return cls({"models": []}, [], _RefusingGovernor(), {"protected_globs": globs})


def decide_for_node(record: dict, node: dict, inputs: FreeInputs) -> dict:
    try:
        return free_routing.decide(
            task_view(record, node), catalog=inputs.catalog, specializations=inputs.specializations,
            governor=inputs.governor, project_policy=inputs.project_policy)
    except Exception as exc:
        view: dict = {}
        try:
            view = task_view(record, node)
        except Exception:
            pass
        decision = free_routing.decide({}, catalog={"models": []}, specializations=[], governor=_RefusingGovernor(),
                                       project_policy={})
        decision.update({
            "task_family": str(view.get("task_family") or ""),
            "role": view.get("role"),
            "effort": view.get("effort") or "medium",
            "route": "escalate",
            "reason": f"free routing error: {type(exc).__name__}",
        })
        return decision


def selection_for(decision: dict, registry: router.ProviderRegistry, *, role: str,
                  availability: dict | None = None, excluded: list | None = None,
                  excluded_classes: dict | None = None, running: dict | None = None,
                  requirements: dict | None = None) -> tuple[dict | None, str | None]:
    if decision.get("route") != "free":
        return None, "not a free route"
    slug = decision["model"]
    serving = [p["id"] for p in registry.providers if slug in (p.get("models") or {}).values()]
    if not serving:
        return None, f"no registry provider serves {slug}"
    selection = router.select(
        registry, capability_class=decision["capability_class"], effort=decision["effort"], role=role,
        availability=availability, excluded=excluded, excluded_classes=excluded_classes, running=running,
        override={"model": slug}, requirements=requirements)
    if selection.get("resolved") and not selection.get("waiting"):
        if selection.get("model") == slug:
            return {**selection, "overridden": False, "reason": "free route: " + str(decision.get("reason")),
                    "free_route": True}, None
        return None, f"free model {slug} not selectable on this node"
    rejected = selection.get("rejected") or {}
    for provider_id in serving:
        if provider_id in rejected:
            return None, f"free provider {provider_id}: {rejected[provider_id]}"
    return None, selection.get("reason")


def free_exclusions(node: dict, registry: router.ProviderRegistry) -> dict[str, list[str]]:
    state = node.get("free_route") or {}
    tried = {t for t in state.get("tried") or [] if isinstance(t, str)}
    result: dict[str, list[str]] = {}
    for provider_id in state.get("free_providers") or []:
        provider = registry.get(provider_id)
        if provider is None:
            continue
        classes = [key for key, value in (provider.get("models") or {}).items() if value in tried]
        merged = result.setdefault(provider_id, [])
        merged.extend(key for key in classes if key not in merged)
    return {key: value for key, value in result.items() if value}


def after_failure(node: dict, failure: dict, registry: router.ProviderRegistry, governor: Any) -> dict:
    decision = dict(node["free_route"])
    kind = failure.get("kind") if isinstance(failure, dict) else None
    if kind in PROVIDER_FAILURES:  # the provider failed, so an alternate on it could not launch
        decision["alternates_used"] = decision.get("alternate_free_max", free_routing.DEFAULT_ECONOMICS["alternate_free_max"])
    step = free_routing.escalate(
        decision, failure, registry=registry, governor=governor, role=node["role"], effort=node["effort"],
        requirements=node.get("requirements"))
    route = step.get("route")
    if route == "free":
        return {"action": "free", "decision": step}
    if route in ("router", "wait"):
        capability_class = (step.get("selection") or {}).get("capability_class") if route == "router" else None
        return {"action": "router", "capability_class": capability_class or node.get("capability_class"),
                "effort": node["effort"], "decision": step, "reason": step.get("reason")}
    return {"action": "exhausted", "decision": step}
