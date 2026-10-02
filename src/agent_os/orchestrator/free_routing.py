"""Free-first routing with validator-gated escalation (FreeComputeBroker).

Pure and deterministic: no model calls, no network, no ledger writes. ``decide``
routes verifiable low-risk work to a free OpenRouter model when eligibility,
data policy and quota allow; otherwise it returns ``route="escalate"``.
``escalate`` walks the fixed ladder (alternate free model -> local/already-paid
-> cheap paid -> frontier); rungs past the free pool come only from
``router.select`` over the caller's registry, so a paid route is never named
unless the caller's registry supplies it. See docs/free-compute-broker.md.
"""
from __future__ import annotations

import fnmatch
from typing import Any, Iterable, Mapping

from ..capabilities import CAPABILITY_CLASSES, rank as class_rank
from . import free_catalog, free_specialization, router
from .model import INTEGRATED_ROLES
from .model_profile import is_paid
from .workload import SENSITIVITY, SENSITIVITY_DEPLOYMENTS

SCHEMA_VERSION = "agent-os/free-route-decision/v1"
DEFAULT_ALLOWED_SENSITIVITY = ("public", "internal")
LOW_EFFORTS = frozenset({"low", "medium"})
SWARM_LANES = frozenset({"swarm", "backfill"})
SECRET_GLOBS = ("**/secrets/**", "**/.env*", "**/*.pem", "**/*.key", "**/credentials*")
BACKFILL_ONLY_SLUGS = frozenset({"openrouter/free"})
# Rungs after the free pool: (name, minimum capability class). Each rung asks
# router.select for at least the task's class, so classes only grow.
ROUTER_RUNGS = (("local_or_already_paid", None), ("cheap_paid", "balanced"), ("frontier", "frontier"))
LOCAL_DEPLOYMENTS = ["local", "subscription"]
DEFAULT_ECONOMICS = {"pass_value": 1.0, "request_cost": 0.05, "validation_cost": 0.05, "alternate_free_max": 1,
                     "explore_share": 0.1}


def _glob_match(path: str, pattern: str) -> bool:
    path = path.replace("\\", "/")
    path = path[2:] if path.startswith("./") else path
    if fnmatch.fnmatch(path, pattern):
        return True
    # "**/x" also matches "x" at the repository root.
    return pattern.startswith("**/") and fnmatch.fnmatch(path, pattern[3:])


def _task_paths(task: Mapping[str, Any]) -> list[str]:
    paths: list[str] = []
    for key in ("scope", "paths", "attachments"):
        value = task.get(key)
        for item in [value] if isinstance(value, str) else (value or []):
            path = item.get("path") if isinstance(item, Mapping) else item
            if path:
                paths.append(str(path))
    return paths


def eligible(task: Mapping[str, Any], *, sensitivity: str, protected_globs: Iterable[str],
             allowed_sensitivity: Iterable[str] | None = None) -> tuple[bool, list[str]]:
    """Model-independent low-risk/verifiable rule: ``(True, [])`` or
    ``(False, failed_checks)`` naming every failed check."""
    failed: list[str] = []
    validators = task.get("validators")
    if not validators or not isinstance(validators, (list, tuple)):
        failed.append("not verifiable: no declared validators")
    role = task.get("role")
    lane = task.get("lane") or "priority"
    if role not in INTEGRATED_ROLES and not (role == "inline" and lane in SWARM_LANES):
        failed.append(f"not low-risk: role {role}")
    effort = task.get("effort") or "medium"
    if effort not in LOW_EFFORTS:
        failed.append(f"not low-risk: effort {effort}")
    globs = [str(g) for g in protected_globs or []]
    paths = _task_paths(task)
    secret = sorted({p for p in paths if any(_glob_match(p, g) for g in SECRET_GLOBS)})
    if secret or task.get("secret_refs") or task.get("uses_secrets"):
        failed.append("secret paths or references: " + ", ".join(secret or ["secret_refs"]))
    protected = sorted({p for p in paths if p not in secret and any(_glob_match(p, g) for g in globs)})
    if protected:
        failed.append("protected paths: " + ", ".join(protected))
    allowed = set(DEFAULT_ALLOWED_SENSITIVITY if allowed_sensitivity is None else allowed_sensitivity)
    allowed -= {"private", "secret"}  # never free-eligible, whatever the policy says
    if sensitivity not in SENSITIVITY or sensitivity not in allowed:
        failed.append(f"sensitivity {sensitivity} not allowed")
    return not failed, failed


def _data_policy(model: Mapping[str, Any], project_policy: Mapping[str, Any]) -> dict[str, Any]:
    resolver = project_policy.get("data_policy_for")
    if callable(resolver):
        policy = resolver(model.get("slug"), model.get("revision"))
    else:
        policy = model.get("data_policy")
    return dict(policy) if isinstance(policy, Mapping) else {}


def data_policy_check(model: Mapping[str, Any], sensitivity: str,
                      project_policy: Mapping[str, Any]) -> tuple[bool, str]:
    """Whether the model's data policy is compatible with the project policy.
    Returns (allowed, the policy fact that allowed or refused it)."""
    if sensitivity == "public":
        return True, "data_policy:not required for public work"
    if project_policy.get("allow_training_endpoints") is True:
        return True, "data_policy:allow_training_endpoints=true (project policy)"
    policy = _data_policy(model, project_policy)
    trains = policy.get("trains_on_prompts")
    source = policy.get("source") or "unknown"
    if trains is False:
        verified = policy.get("verified_at")
        return True, f"data_policy:trains_on_prompts=false ({source}" + (f", verified {verified})" if verified else ")")
    if trains is None:
        return False, "data_policy: unknown"
    return False, f"data_policy: trains_on_prompts ({source})"


def _catalog_models(catalog: Any) -> list[dict[str, Any]]:
    models = catalog.get("models") if isinstance(catalog, Mapping) else catalog
    return [dict(m) for m in models or [] if isinstance(m, Mapping) and m.get("slug")]


def _model_problem(model: Mapping[str, Any], task: Mapping[str, Any]) -> str | None:
    if not free_catalog.is_free(model.get("pricing")):
        return "not free"
    if model.get("slug") in BACKFILL_ONLY_SLUGS and task.get("lane") != "backfill":
        return "backfill-only pseudo-model"
    needed = task.get("estimated_tokens")
    if isinstance(needed, (int, float)) and isinstance(model.get("context_length"), (int, float)) \
            and model["context_length"] < needed:
        return "context too short"
    if task.get("needs_tools") and not model.get("supports_tools"):
        return "no tools"
    if task.get("needs_structured_output") and not model.get("supports_structured_output"):
        return "no structured output"
    return None


def _wilson_low(records: Iterable[Mapping[str, Any]], family: str, slug: str) -> float:
    lows = [(r.get("wilson95") or [None])[0] for r in records if r.get("task_family") == family and r.get("model") == slug]
    return max((low for low in lows if low is not None), default=0.0)


def _status(records: Iterable[Mapping[str, Any]], family: str, model: Mapping[str, Any]) -> str | None:
    """Status of the record ``free_specialization.rank`` uses for ``model``:
    the catalog revision's record when sampled, else the best revision."""
    mine = [r for r in records if r.get("task_family") == family and r.get("model") == model.get("slug")]
    current = [r for r in mine if model.get("revision") is not None and r.get("revision") == model.get("revision")]
    statuses = {r.get("status") for r in current or mine}
    return "proven" if "proven" in statuses else next(iter(sorted(s for s in statuses if s)), None)


def _economics(project_policy: Mapping[str, Any]) -> dict[str, float]:
    return {key: float(project_policy.get(key, default)) for key, default in DEFAULT_ECONOMICS.items()}


def expected_value(wilson_low: float, economics: Mapping[str, float]) -> float:
    """Wilson low bound times the value of a pass, minus quota + validation cost."""
    return round(wilson_low * economics["pass_value"] - economics["request_cost"] - economics["validation_cost"], 6)


def _ladder(capability_class: str, alternates: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    rungs = [] if alternates is None else [{"rung": "alternate_free", "candidates": [a["model"] for a in alternates]}]
    for name, minimum in ROUTER_RUNGS:
        rungs.append({"rung": name, "capability_class": _stronger(capability_class, minimum)})
    return rungs


def _stronger(capability_class: str, minimum: str | None) -> str:
    if minimum is None or class_rank(capability_class) >= class_rank(minimum):
        return capability_class
    return minimum


def _quota(governor: Any) -> dict[str, Any] | None:
    remaining = getattr(governor, "remaining", None)
    return dict(remaining()) if callable(remaining) else None


def decide(task: Mapping[str, Any], *, catalog: Any, specializations: Iterable[Mapping[str, Any]], governor: Any,
           project_policy: Mapping[str, Any]) -> dict[str, Any]:
    """Free route decision for one task. Never calls a model."""
    records = list(specializations or [])
    family = str(task.get("task_family") or "")
    sensitivity = str(task.get("sensitivity") or "internal")
    capability_class = str(task.get("capability_class") or "fast")
    if capability_class not in CAPABILITY_CLASSES or capability_class == "deterministic":
        capability_class = "fast"
    economics = _economics(project_policy)
    decision: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "task_family": family,
        "sensitivity": sensitivity,
        "route": "escalate",
        "model": None,
        "revision": None,
        "reason": "",
        "eligibility": {"low_risk_verifiable": False, "failed_checks": []},
        "policy_allowed_by": [],
        "catalog_snapshot": (catalog.get("snapshot_id") or catalog.get("catalog_version")) if isinstance(catalog, Mapping) else None,
        "quota": None,
        "capability_class": capability_class,
        "role": task.get("role"),
        "effort": task.get("effort") or "medium",
        "rung": None,
        "alternates": [],
        "alternates_used": 0,
        "alternate_free_max": int(economics["alternate_free_max"]),
        "tried": [],
        "history": [],
        "verified_outputs": list(task.get("verified_outputs") or []),
        "ladder": _ladder(capability_class, None),
    }

    def escalated(reason: str) -> dict[str, Any]:
        decision["reason"] = reason
        return decision

    ok, failed = eligible(task, sensitivity=sensitivity, protected_globs=project_policy.get("protected_globs") or [],
                          allowed_sensitivity=project_policy.get("allowed_sensitivity"))
    decision["eligibility"] = {"low_risk_verifiable": ok, "failed_checks": failed}
    if any(check.startswith("secret paths") for check in failed):
        decision["sensitivity"] = "secret"  # escalation rungs must keep secret work local
    if not ok:
        return escalated("; ".join(failed))
    if project_policy.get("free_routing_enabled") is False:
        return escalated("free routing disabled by project policy")

    usable: dict[str, dict[str, Any]] = {}
    refused: dict[str, str] = {}
    data_reason: dict[str, str] = {}
    for model in _catalog_models(catalog):
        problem = _model_problem(model, task)
        if problem is None:
            allowed, why = data_policy_check(model, sensitivity, project_policy)
            if allowed:
                usable[model["slug"]] = model
                data_reason[model["slug"]] = why
                continue
            problem = why
        refused[model["slug"]] = problem
    if not usable:
        reasons = sorted(set(refused.values()))
        if reasons == ["data_policy: unknown"]:
            return escalated("data_policy: unknown")
        return escalated("no usable free model" + (f" ({'; '.join(reasons)})" if reasons else ": catalog empty"))

    pool = {"models": list(usable.values())}
    # rank/canary_pick read records too, so keep only models usable right now.
    ordered = [slug for slug in free_specialization.rank(records, family, pool) if slug in usable]
    lane = task.get("lane") or "priority"
    if lane not in SWARM_LANES:  # priority work never rides canary/under-sampled models
        ordered = [slug for slug in ordered if _status(records, family, usable[slug]) == "proven"]
    seed = task.get("seed") or f"{task.get('run_id')}|{task.get('node_id')}"
    rate = economics["explore_share"] if lane in SWARM_LANES else 0.0
    canary = free_specialization.canary_pick(records, family, pool, rate, seed)
    canary = canary if canary in usable else None
    candidates = ([canary] if canary else []) + [slug for slug in ordered if slug != canary]
    if not candidates:
        if lane not in SWARM_LANES:
            return escalated(f"no proven free model for {family} (priority lane)")
        return escalated(f"no proven or canary free model for {family}")

    decision["quota"] = _quota(governor)
    chosen, quota_reasons = None, []
    for slug in candidates:
        allowed, why = governor.can_spend(slug)
        if allowed:
            chosen = slug
            break
        quota_reasons.append(why)
    if chosen is None:
        return escalated("quota: " + (quota_reasons[-1] if quota_reasons else "unavailable"))

    model = usable[chosen]
    low = _wilson_low(records, family, chosen)
    alternates = [
        {"model": slug, "wilson_low": _wilson_low(records, family, slug),
         "expected_value": expected_value(_wilson_low(records, family, slug), economics)}
        for slug in candidates if slug != chosen
    ]
    kind = "canary pick" if chosen == canary else "specialist"
    decision.update({
        "route": "free",
        "model": chosen,
        "revision": model.get("revision"),
        "rung": "free",
        "reason": f"{kind}: wilson95 low {low:.3f} for {family}",
        "policy_allowed_by": [
            str(project_policy.get("source") or "project_policy"),
            f"sensitivity:{sensitivity}<=allowed",
            data_reason[chosen],
            f"validators:{len(task.get('validators') or [])} declared",
        ],
        "alternates": alternates,
        "tried": [chosen],
        "ladder": _ladder(capability_class, alternates),
    })
    return decision


def _failure(failure: Any) -> dict[str, Any]:
    if isinstance(failure, Mapping):
        return dict(failure)
    return {"kind": str(failure) if failure else "escalated"}


def _merge_outputs(previous: list[Any], new: Iterable[Any]) -> list[Any]:
    merged = list(previous)
    for item in new or []:
        if item not in merged:
            merged.append(item)
    return merged


def escalate(decision: Mapping[str, Any], failure: Any, *, registry: router.ProviderRegistry, governor: Any = None,
             **select_kwargs: Any) -> dict[str, Any]:
    """Next ladder step after ``failure`` on ``decision``.

    Verified partial outputs (``decision["verified_outputs"]`` plus
    ``failure["verified_outputs"]``) are carried forward. Never calls a model."""
    failed = _failure(failure)
    step = dict(decision)
    step["verified_outputs"] = _merge_outputs(list(decision.get("verified_outputs") or []), failed.get("verified_outputs"))
    step["history"] = list(decision.get("history") or []) + [{
        "rung": decision.get("rung"),
        "model": decision.get("model"),
        "provider": decision.get("provider"),
        "failure": failed.get("kind"),
    }]
    step["tried"] = list(decision.get("tried") or [])
    step["escalated"] = True
    ladder = list(decision.get("ladder") or [])
    names = [rung["rung"] for rung in ladder]
    current = decision.get("rung")
    start = names.index(current) if current in names and current != "alternate_free" else -1
    if current == "alternate_free":
        start = names.index("alternate_free") - 1  # another alternate may remain
    used = int(decision.get("alternates_used") or 0)
    for rung in ladder[start + 1:]:
        if rung["rung"] == "alternate_free":
            if used >= int(decision.get("alternate_free_max", DEFAULT_ECONOMICS["alternate_free_max"])):
                continue
            for alternate in decision.get("alternates") or []:
                slug = alternate["model"]
                if slug in step["tried"] or alternate.get("expected_value", 0) <= 0:
                    continue
                if governor is not None and not governor.can_spend(slug)[0]:
                    continue
                step.update({
                    "route": "free", "rung": "alternate_free", "model": slug, "provider": None, "selection": None,
                    "paid": False, "alternates_used": used + 1, "tried": step["tried"] + [slug],
                    "reason": f"alternate free model: expected value {alternate['expected_value']:.3f} > 0",
                })
                return step
            continue
        kwargs = {"effort": decision.get("effort") or "medium", "role": decision.get("role") or "implementer",
                  **select_kwargs}
        requirements = dict(kwargs.get("requirements") or {})
        deployments = requirements.get("deployment")
        if isinstance(deployments, str):
            deployments = [deployments]
        if rung["rung"] == "local_or_already_paid":
            deployments = [d for d in deployments or LOCAL_DEPLOYMENTS if d in LOCAL_DEPLOYMENTS]
        floor = SENSITIVITY_DEPLOYMENTS.get(str(decision.get("sensitivity") or "internal"))
        if floor:  # private/secret work never leaves its deployment floor on any rung
            deployments = [d for d in deployments or floor if d in floor]
        if deployments is not None:
            if not deployments:
                continue
            requirements["deployment"] = deployments
            kwargs["requirements"] = requirements
        kwargs["capability_class"] = rung["capability_class"]
        selection = router.select(registry, **kwargs)
        if selection.get("waiting"):
            step.update({"route": "wait", "reason": f"{rung['rung']}: {selection.get('reason')}"})
            return step
        if not selection.get("resolved"):
            continue
        key = f"{selection['provider']}:{selection['model']}"
        if key in step["tried"]:
            continue  # same route as a weaker rung; it already failed
        provider = registry.get(selection["provider"]) or {}
        step.update({
            "route": "router", "rung": rung["rung"], "model": selection["model"], "provider": selection["provider"],
            "revision": None, "selection": selection, "paid": is_paid(provider), "tried": step["tried"] + [key],
            "reason": f"{rung['rung']}: {selection.get('reason')}",
        })
        return step
    step.update({"route": "exhausted", "rung": "exhausted", "model": None, "provider": None, "selection": None,
                 "reason": "escalation ladder exhausted"})
    return step
