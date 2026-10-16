"""Model service catalog: loader, validator, presets and read-only discovery.

The catalog (schema ``personal-agent/model-service-catalog/v1``, spec in
``projects/personal-agent-os/research/model-services/SCHEMA.md``) describes
hosted model services: their endpoints, plans, billing, privacy and terms.
This module turns a catalog record into a provider registry entry *preview*
(``preset_entry`` for OpenAI-compatible endpoints, ``bridge_entry`` for
coding plans usable only through Claude Code) and lists an endpoint's models
with one read-only GET (``discover``).

Nothing here writes the provider registry; ``service.add_model_endpoint``
does that, and only with ``write=True``. Entries hold secret *references*;
a key value never appears in a return value, an error, a cache file or a log.
"""

from __future__ import annotations

import copy
import json
import re
import urllib.error
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlsplit

from ..paths import ROOT
from . import endpoints, model_profile, secret_refs

SCHEMA = "personal-agent/model-service-catalog/v1"
CATALOG_PATH = ROOT / "projects" / "personal-agent-os" / "research" / "model-services" / "catalog.json"
NOT_COMPILED = "catalog not compiled yet"

CATEGORIES = ("subscription_allowance", "hosted_api", "custom_hosting", "gateway")
INTEGRATION_STATUSES = ("preset_ready", "preset_restricted", "bridge_claude_code", "catalog_only", "deferred")
PROTOCOLS = ("openai_chat", "anthropic_messages", "vendor")
SERVICE_MODALITIES = (*model_profile.MODALITIES, "rerank", "tts", "asr", "video")
FINDING_STATUSES = ("confirmed", "contradicted", "unverified")
MEDIA_TASKS = ("image_generation", "image_editing", "asr", "diarization", "tts", "voice_clone", "embedding", "rerank")
TASK_FAMILIES = ("coding", "automation", "research", "extraction", "lore", "creative")
ANY_CLIENT = "any openai-compatible client"
BRIDGE_ALIASES = ("haiku", "sonnet", "opus")
BRIDGE_CLASSES = {"fast": "haiku", "balanced": "sonnet", "reasoning": "opus"}
CACHE_DIR = "service-models"

_ID = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
# Null is meaningful for these fields, so they need no ``unknown`` entry.
_NULL_MEANS_NONE = {"base_model", "refusal_evidence", "abliteration_method", "vs_base", "hf_repo", "notes", "catalog_model"}


# ---------------------------------------------------------------------------
# Loading and validation
# ---------------------------------------------------------------------------


def load(path: str | Path | None = None) -> dict[str, Any]:
    target = Path(path) if path else CATALOG_PATH
    if not target.exists():
        raise FileNotFoundError(f"model service {NOT_COMPILED}: {target} does not exist (the catalog-data task compiles it)")
    catalog = json.loads(target.read_text(encoding="utf-8-sig"))
    if not isinstance(catalog, dict):
        raise ValueError(f"model service catalog {target} must be a JSON object")
    return catalog


def _today(today: date | str | None) -> date:
    if today is None:
        return date.today()
    return today if isinstance(today, date) else date.fromisoformat(str(today))


def _parse_date(value: Any) -> date | None:
    if not isinstance(value, str) or not _DATE.match(value):
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _interval(catalog: dict[str, Any]) -> int:
    value = catalog.get("review_interval_days")
    return value if isinstance(value, int) and not isinstance(value, bool) and value > 0 else 60


def is_stale(reviewed_at: Any, interval_days: int, today: date | str | None = None) -> bool:
    reviewed = _parse_date(reviewed_at)
    return reviewed is None or _today(today) - reviewed > timedelta(days=interval_days)


def _check_sources(where: str, record: dict[str, Any], errors: list[str], need_official: bool) -> None:
    sources = record.get("sources")
    if not isinstance(sources, list) or not sources:
        errors.append(f"{where}: needs at least one source")
        return
    for index, source in enumerate(sources):
        if not isinstance(source, dict) or not isinstance(source.get("url"), str) or not source["url"].startswith(("http://", "https://")):
            errors.append(f"{where}: sources[{index}] needs an http(s) url")
            continue
        if not isinstance(source.get("official"), bool):
            errors.append(f"{where}: sources[{index}].official must be true or false")
        if _parse_date(source.get("accessed")) is None:
            errors.append(f"{where}: sources[{index}].accessed must be YYYY-MM-DD")
    if need_official and not any(isinstance(item, dict) and item.get("official") is True for item in sources):
        errors.append(f"{where}: needs at least one official source")


def _check_enum(where: str, field: str, value: Any, allowed: tuple[str, ...], errors: list[str], nullable: bool = False) -> None:
    if value is None and nullable:
        return
    if value not in allowed:
        errors.append(f"{where}: {field} {value!r} is not one of {', '.join(allowed)}")


def _check_unknown(where: str, record: dict[str, Any], errors: list[str], warnings: list[str]) -> None:
    unknown = record.get("unknown", [])
    if not isinstance(unknown, list) or not all(isinstance(item, str) for item in unknown):
        errors.append(f"{where}: unknown must be a list of field names")
        return
    unlisted = [key for key, value in record.items() if value is None and key not in unknown and key not in _NULL_MEANS_NONE]
    if unlisted:
        warnings.append(f"{where}: null field(s) {', '.join(sorted(unlisted))} not listed in unknown")


def _check_billing(where: str, billing: Any, errors: list[str]) -> None:
    if not isinstance(billing, dict):
        errors.append(f"{where}: billing must be an object")
        return
    _check_enum(where, "billing.mode", billing.get("mode"), model_profile.BILLING_MODES, errors)
    _check_enum(where, "billing.overage", billing.get("overage"), model_profile.OVERAGE, errors)
    allowance = billing.get("allowance")
    if allowance is not None:
        if not isinstance(allowance, dict):
            errors.append(f"{where}: billing.allowance must be an object or null")
        else:
            _check_enum(where, "billing.allowance.unit", allowance.get("unit"), model_profile.ALLOWANCE_UNITS, errors)
            _check_enum(where, "billing.allowance.reset_window", allowance.get("reset_window"), model_profile.RESET_WINDOWS, errors)
            amount = allowance.get("amount")
            if amount is not None and (isinstance(amount, bool) or not isinstance(amount, (int, float))):
                errors.append(f"{where}: billing.allowance.amount must be a number or null")
    triggers = billing.get("metered_triggers", [])
    if not isinstance(triggers, list) or not all(isinstance(item, str) for item in triggers):
        errors.append(f"{where}: billing.metered_triggers must be a list of strings")


def _clients(plan: dict[str, Any]) -> list[str] | None:
    clients = plan.get("allowed_clients")
    return [str(item) for item in clients] if isinstance(clients, list) else None


def _any_client(clients: list[str] | None) -> bool:
    return clients is None or any(item.strip().lower() == ANY_CLIENT for item in clients)


def _lists_claude_code(clients: list[str] | None) -> bool:
    return clients is not None and any(item.strip().lower() == "claude code" for item in clients)


def _check_service(service: dict[str, Any], model_ids: set[str], errors: list[str], warnings: list[str]) -> None:
    sid = service.get("id")
    where = f"service {sid}"
    if not isinstance(sid, str) or not _ID.match(sid):
        errors.append(f"{where}: id must be kebab-case")
    if not service.get("name"):
        errors.append(f"{where}: name is required")
    _check_enum(where, "category", service.get("category"), CATEGORIES, errors)
    _check_enum(where, "integration_status", service.get("integration_status"), INTEGRATION_STATUSES, errors)
    _check_enum(where, "deployment", service.get("deployment"), model_profile.DEPLOYMENTS, errors)
    modalities = service.get("modalities", [])
    if not isinstance(modalities, list):
        errors.append(f"{where}: modalities must be a list")
    else:
        for item in modalities:
            _check_enum(where, "modality", item, SERVICE_MODALITIES, errors)
    if _parse_date(service.get("reviewed_at")) is None:
        errors.append(f"{where}: reviewed_at must be YYYY-MM-DD")
    _check_sources(where, service, errors, need_official=True)
    _check_unknown(where, service, errors, warnings)

    endpoint_ids: set[str] = set()
    protocols: set[str] = set()
    for endpoint in service.get("endpoints") or []:
        eid = endpoint.get("id") if isinstance(endpoint, dict) else None
        ewhere = f"{where} endpoint {eid}"
        if not isinstance(eid, str) or not eid:
            errors.append(f"{where}: every endpoint needs an id")
            continue
        if eid in endpoint_ids:
            errors.append(f"{ewhere}: duplicate endpoint id")
        endpoint_ids.add(eid)
        _check_enum(ewhere, "protocol", endpoint.get("protocol"), PROTOCOLS, errors)
        protocols.add(str(endpoint.get("protocol")))
        try:
            endpoints.validate_base_url(endpoint.get("base_url"))
            if not str(endpoint["base_url"]).startswith("https://"):
                warnings.append(f"{ewhere}: base_url is not https")
            if str(endpoint["base_url"]).endswith("/"):
                errors.append(f"{ewhere}: base_url must not end with '/'")
        except ValueError as exc:
            errors.append(f"{ewhere}: {exc}")
        _check_enum(ewhere, "path_style", endpoint.get("path_style", "auto"), endpoints.PATH_STYLES, errors)
        models_path = endpoint.get("models_path")
        if models_path is not None and (not isinstance(models_path, str) or not models_path.startswith("/")):
            errors.append(f"{ewhere}: models_path must be null or a path beginning with '/' (relative to the api root)")
        if endpoint.get("models_list_requires_auth") not in (True, False, None):
            errors.append(f"{ewhere}: models_list_requires_auth must be true, false or null")
        if endpoint.get("secret_ref") is not None:
            try:
                secret_refs.parse(endpoint["secret_ref"])
            except ValueError as exc:
                errors.append(f"{ewhere}: {exc}")
        elif endpoint.get("protocol") in ("openai_chat", "anthropic_messages"):
            warnings.append(f"{ewhere}: no secret_ref")

    plan_ids: set[str] = set()
    automation = []
    for plan in service.get("plans") or []:
        pid = plan.get("id") if isinstance(plan, dict) else None
        pwhere = f"{where} plan {pid}"
        if not isinstance(pid, str) or not pid:
            errors.append(f"{where}: every plan needs an id")
            continue
        if pid in plan_ids:
            errors.append(f"{pwhere}: duplicate plan id")
        plan_ids.add(pid)
        if plan.get("endpoint") is not None and plan["endpoint"] not in endpoint_ids:
            errors.append(f"{pwhere}: endpoint {plan['endpoint']!r} is not an endpoint of this service")
        _check_billing(pwhere, plan.get("billing"), errors)
        if plan.get("automation_allowed") not in (True, False, None):
            errors.append(f"{pwhere}: automation_allowed must be true, false or null")
        clients = plan.get("allowed_clients")
        if clients is not None and (not isinstance(clients, list) or not all(isinstance(item, str) for item in clients)):
            errors.append(f"{pwhere}: allowed_clients must be null or a list of strings")
        price = plan.get("usd_per_month")
        if price is not None and (isinstance(price, bool) or not isinstance(price, (int, float))):
            errors.append(f"{pwhere}: usd_per_month must be a number or null")
        automation.append((plan.get("automation_allowed"), _clients(plan)))

    privacy = service.get("privacy")
    if not isinstance(privacy, dict):
        errors.append(f"{where}: privacy must be an object")
    else:
        _check_enum(where, "privacy.training_on_prompts", privacy.get("training_on_prompts"), model_profile.TRAINING_ON_PROMPTS, errors)
        _check_enum(where, "privacy.weights_location", privacy.get("weights_location"), model_profile.WEIGHTS_LOCATIONS, errors)
        if privacy.get("zdr") not in (True, False, None):
            errors.append(f"{where}: privacy.zdr must be true, false or null")

    status = service.get("integration_status")
    if status in ("preset_ready", "preset_restricted") and "openai_chat" not in protocols:
        errors.append(f"{where}: integration_status {status} needs an openai_chat endpoint")
    if status == "preset_ready" and not any(allowed is True and _any_client(clients) for allowed, clients in automation):
        errors.append(f"{where}: integration_status preset_ready needs a plan with automation_allowed true and no client restriction")
    if status == "bridge_claude_code" and "anthropic_messages" not in protocols:
        errors.append(f"{where}: integration_status bridge_claude_code needs an anthropic_messages endpoint")

    for model in service.get("models") or []:
        mwhere = f"{where} model {model.get('id') if isinstance(model, dict) else model!r}"
        if not isinstance(model, dict) or not model.get("id"):
            errors.append(f"{where}: every model needs an id")
            continue
        _check_enum(mwhere, "refusal_profile", model.get("refusal_profile", "unknown"), model_profile.REFUSAL_PROFILES, errors)
        linked = model.get("catalog_model")
        if linked is not None and linked not in model_ids:
            errors.append(f"{mwhere}: catalog_model {linked!r} is not in the catalog's models")
        if model.get("refusal_profile") == "abliterated" and not model.get("refusal_evidence") and linked is None:
            errors.append(f"{mwhere}: refusal_profile abliterated needs refusal_evidence (link a catalog model that documents it)")

    for finding in service.get("findings") or []:
        _check_enum(where, "finding status", finding.get("status") if isinstance(finding, dict) else None, FINDING_STATUSES, errors)


def validate(catalog: dict[str, Any], today: date | str | None = None) -> dict[str, list[str]]:
    """Errors break presets or the spec's ground rules; warnings (staleness,
    unlisted nulls) ask for a review."""
    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(catalog, dict):
        return {"errors": ["catalog must be a JSON object"], "warnings": []}
    if catalog.get("schema") != SCHEMA:
        errors.append(f"schema must be {SCHEMA}")
    interval = _interval(catalog)
    if catalog.get("review_interval_days") != interval:
        errors.append("review_interval_days must be a positive integer")
    if _parse_date(catalog.get("reviewed_at")) is None:
        errors.append("reviewed_at must be YYYY-MM-DD")
    elif is_stale(catalog["reviewed_at"], interval, today):
        warnings.append(f"catalog reviewed_at {catalog['reviewed_at']} is older than {interval} days")

    models = catalog.get("models") or []
    model_ids: set[str] = set()
    for model in models:
        mid = model.get("id") if isinstance(model, dict) else None
        where = f"model {mid}"
        if not isinstance(mid, str) or not mid:
            errors.append("every model needs an id")
            continue
        if mid in model_ids:
            errors.append(f"{where}: duplicate model id")
        model_ids.add(mid)
        _check_enum(where, "refusal_profile", model.get("refusal_profile"), model_profile.REFUSAL_PROFILES, errors)
        if model.get("refusal_profile") == "abliterated" and not model.get("refusal_evidence"):
            errors.append(f"{where}: refusal_profile abliterated needs refusal_evidence (never infer it from a name)")
        for family in model.get("suggested_prior_task_families") or []:
            _check_enum(where, "suggested_prior_task_family", family, TASK_FAMILIES, errors)
        _check_sources(where, model, errors, need_official=False)
        _check_unknown(where, model, errors, warnings)

    services = catalog.get("services")
    if not isinstance(services, list):
        errors.append("services must be a list")
        services = []
    seen: set[str] = set()
    for service in services:
        if not isinstance(service, dict):
            errors.append("every service must be an object")
            continue
        sid = service.get("id")
        if sid in seen:
            errors.append(f"service {sid}: duplicate service id")
        seen.add(sid)
        _check_service(service, model_ids, errors, warnings)
        if _parse_date(service.get("reviewed_at")) and is_stale(service["reviewed_at"], interval, today):
            warnings.append(f"service {sid}: stale (reviewed_at {service['reviewed_at']} is older than {interval} days)")

    for model in models:
        if isinstance(model, dict):
            for served in model.get("served_by") or []:
                if isinstance(served, dict) and served.get("service") not in seen:
                    warnings.append(f"model {model.get('id')}: served_by service {served.get('service')!r} is not in the catalog")

    media_ids: set[str] = set()
    for item in catalog.get("media") or []:
        mid = item.get("id") if isinstance(item, dict) else None
        where = f"media {mid}"
        if not isinstance(mid, str) or not mid:
            errors.append("every media record needs an id")
            continue
        if mid in media_ids:
            errors.append(f"{where}: duplicate media id")
        media_ids.add(mid)
        _check_enum(where, "task", item.get("task"), MEDIA_TASKS, errors)
        _check_sources(where, item, errors, need_official=False)
        _check_unknown(where, item, errors, warnings)
        for served in item.get("served_by") or []:
            if isinstance(served, dict) and served.get("service") not in seen:
                warnings.append(f"{where}: served_by service {served.get('service')!r} is not in the catalog")
    return {"errors": errors, "warnings": warnings}


# ---------------------------------------------------------------------------
# Summaries
# ---------------------------------------------------------------------------


def _catalog(catalog: dict[str, Any] | None) -> dict[str, Any]:
    return catalog if catalog is not None else load()


def _service(catalog: dict[str, Any], service_id: str) -> dict[str, Any]:
    for item in catalog.get("services") or []:
        if isinstance(item, dict) and item.get("id") == service_id:
            return item
    raise ValueError(f"unknown model service {service_id!r} (see `agent-os orchestrate services list`)")


def _plan_summary(plan: dict[str, Any]) -> dict[str, Any]:
    profile = model_profile.normalize_profile({"billing": plan.get("billing")})
    return {
        "id": plan.get("id"), "name": plan.get("name"), "usd_per_month": plan.get("usd_per_month"), "endpoint": plan.get("endpoint"),
        "billing": profile["billing"], "allowance_summary": model_profile.allowance_summary(profile),
        "automation_allowed": plan.get("automation_allowed"), "allowed_clients": plan.get("allowed_clients"),
        "needs_ack": plan.get("automation_allowed") is None, "notes": plan.get("notes"),
    }


def services(catalog: dict[str, Any] | None = None, category: str | None = None, status: str | None = None,
             today: date | str | None = None) -> list[dict[str, Any]] | dict[str, Any]:
    """One summary row per service. When the catalog file does not exist yet,
    returns ``{"error": "catalog not compiled yet", ...}`` instead of raising."""
    if catalog is None:
        try:
            catalog = load()
        except FileNotFoundError as exc:
            return {"error": NOT_COMPILED, "detail": str(exc), "path": str(CATALOG_PATH), "services": []}
    interval = _interval(catalog)
    rows = []
    for item in catalog.get("services") or []:
        if not isinstance(item, dict):
            continue
        if category and item.get("category") != category:
            continue
        if status and item.get("integration_status") != status:
            continue
        rows.append({
            "id": item.get("id"), "name": item.get("name"), "category": item.get("category"),
            "integration_status": item.get("integration_status"), "integration_notes": item.get("integration_notes"),
            "deployment": item.get("deployment"),
            "plans": [_plan_summary(plan) for plan in item.get("plans") or [] if isinstance(plan, dict)],
            "restrictions": item.get("restrictions"), "privacy": item.get("privacy"),
            "endpoints": [{"id": ep.get("id"), "protocol": ep.get("protocol"), "base_url": ep.get("base_url")}
                          for ep in item.get("endpoints") or [] if isinstance(ep, dict)],
            "reviewed_at": item.get("reviewed_at"), "stale": is_stale(item.get("reviewed_at"), interval, today),
        })
    return rows


def show(service_id: str, catalog: dict[str, Any] | None = None, today: date | str | None = None) -> dict[str, Any]:
    catalog = _catalog(catalog)
    record = copy.deepcopy(_service(catalog, service_id))
    record["stale"] = is_stale(record.get("reviewed_at"), _interval(catalog), today)
    record["plan_summaries"] = [_plan_summary(plan) for plan in record.get("plans") or [] if isinstance(plan, dict)]
    return record


# ---------------------------------------------------------------------------
# Presets
# ---------------------------------------------------------------------------


def _endpoint(service: dict[str, Any], endpoint_id: str) -> dict[str, Any]:
    for item in service.get("endpoints") or []:
        if item.get("id") == endpoint_id:
            return item
    known = ", ".join(str(item.get("id")) for item in service.get("endpoints") or []) or "none"
    raise ValueError(f"service {service['id']} has no endpoint {endpoint_id!r} (endpoints: {known})")


def _plan(service: dict[str, Any], plan_id: str) -> dict[str, Any]:
    for item in service.get("plans") or []:
        if item.get("id") == plan_id:
            return item
    known = ", ".join(str(item.get("id")) for item in service.get("plans") or []) or "none"
    raise ValueError(f"service {service['id']} has no plan {plan_id!r} (plans: {known})")


def _of_protocol(service: dict[str, Any], protocol: str) -> list[dict[str, Any]]:
    return [item for item in service.get("endpoints") or [] if item.get("protocol") == protocol]


def _select(service: dict[str, Any], protocol: str, endpoint: str | None, plan: str | None) -> tuple[dict[str, Any], dict[str, Any] | None]:
    plans = [item for item in service.get("plans") or [] if isinstance(item, dict)]
    plan_rec = _plan(service, plan) if plan else None
    if endpoint:
        ep = _endpoint(service, endpoint)
    elif plan_rec is not None and plan_rec.get("endpoint"):
        ep = _endpoint(service, plan_rec["endpoint"])
    else:
        matching = _of_protocol(service, protocol)
        default = [item for item in matching if item.get("id") == "default"]
        if not matching:
            raise ValueError(f"service {service['id']} has no {protocol} endpoint")
        ep = (default or matching)[0]
    if plan_rec is None:
        for item in plans:
            if item.get("endpoint") in (ep.get("id"), None):
                plan_rec = item
                break
    if plan_rec is not None and plan_rec.get("endpoint") not in (None, ep.get("id")):
        raise ValueError(f"plan {plan_rec['id']} of {service['id']} bills through endpoint {plan_rec['endpoint']!r}, not {ep.get('id')!r}; "
                         f"pass --endpoint {plan_rec['endpoint']} or choose another plan")
    return ep, plan_rec


def _check_terms(service: dict[str, Any], plan: dict[str, Any] | None, ack_terms: bool, today: date | str | None) -> dict[str, Any] | None:
    """Apply ``automation_allowed``; return the ``terms_ack`` record or None."""
    allowed = plan.get("automation_allowed") if plan is not None else None
    label = f"{service['id']} plan {plan['id']}" if plan is not None else f"{service['id']} (no plan documented)"
    if allowed is False:
        raise ValueError(f"{label}: the terms do not allow automated use; no preset is offered ({service.get('integration_notes') or 'see the catalog sources'})")
    if allowed is None and not ack_terms:
        sources = ", ".join(item.get("url", "") for item in service.get("sources") or [] if isinstance(item, dict) and item.get("official"))
        raise ValueError(f"{label}: the terms for automated use are unclear; read them ({sources or 'see the catalog sources'}) "
                         "and pass ack_terms=True (--ack-terms) to record that you did")
    if ack_terms:
        return {"service": service["id"], "plan": plan["id"] if plan is not None else None, "at": _today(today).isoformat()}
    return None


def _model_facts(catalog: dict[str, Any], service: dict[str, Any], model: str) -> dict[str, Any]:
    facts: dict[str, Any] = {"refusal_profile": "unknown", "open_weights": None, "license": None, "context_window": None, "modalities": None}
    listed = next((item for item in service.get("models") or [] if isinstance(item, dict) and item.get("id") == model), None)
    linked = None
    if listed and listed.get("catalog_model"):
        linked = next((item for item in catalog.get("models") or [] if isinstance(item, dict) and item.get("id") == listed["catalog_model"]), None)
    # The linked catalog model is authoritative for weights, license and
    # refusal profile; the service's own record for the context it serves.
    for record in (listed, linked):
        if not record:
            continue
        for key in ("open_weights", "license"):
            if record.get(key) is not None:
                facts[key] = record[key]
        if record.get("refusal_profile") in model_profile.REFUSAL_PROFILES:
            facts["refusal_profile"] = record["refusal_profile"]
    for record in (linked, listed):
        if record and isinstance(record.get("context_window"), int):
            facts["context_window"] = record["context_window"]
    if listed and isinstance(listed.get("modalities"), list):
        facts["modalities"] = [item for item in listed["modalities"] if item in model_profile.MODALITIES] or None
    if facts["refusal_profile"] == "abliterated" and not (linked and linked.get("refusal_evidence")):
        facts["refusal_profile"] = "unknown"
    return facts


def _provider_id(service_id: str, endpoint_id: str, provider_id: str | None) -> str:
    return provider_id or (service_id if endpoint_id == "default" else f"{service_id}-{endpoint_id}")


def _secret_ref(service_id: str, ep: dict[str, Any]) -> str:
    """The endpoint's secret_ref, defaulting to ``secrets://<service>/<endpoint>``.

    An entry without one would make the adapter fall back to its vendor key
    (e.g. OPENAI_API_KEY) and send it to a third-party host."""
    ref = ep.get("secret_ref") or f"{secret_refs.SCHEME}{service_id}/{ep.get('id') or 'default'}"
    secret_refs.parse(ref)
    return ref


def preset_entry(service_id: str, *, model: str, classes: list[str], endpoint: str | None = None, plan: str | None = None,
                 provider_id: str | None = None, roles: list[str] | None = None, cost: float = 1.0, max_concurrency: int = 2,
                 ack_terms: bool = False, today: date | str | None = None, catalog: dict[str, Any] | None = None) -> dict[str, Any]:
    """A registry entry for an ``openai_chat`` endpoint (adapter ``openai_api``).

    Refuses when the plan's terms forbid automation, when they are unclear and
    ``ack_terms`` is not given, or when the plan is limited to named clients.
    The entry never carries provider-selection or routing request parameters.
    """
    catalog = _catalog(catalog)
    service = _service(catalog, service_id)
    ep, plan_rec = _select(service, "openai_chat", endpoint, plan)
    if ep.get("protocol") != "openai_chat":
        hint = f"; use bridge_entry (`agent-os orchestrate services bridge {service_id}`)" if ep.get("protocol") == "anthropic_messages" else ""
        raise ValueError(f"endpoint {ep.get('id')} of {service_id} speaks {ep.get('protocol')}, not openai_chat{hint}")
    clients = _clients(plan_rec) if plan_rec is not None else None
    if not _any_client(clients):
        message = f"{service_id} plan {plan_rec['id']} may only be used through {', '.join(clients or [])}, not an OpenAI-compatible client"
        if _lists_claude_code(clients) and _of_protocol(service, "anthropic_messages"):
            message += f"; use bridge_entry (`agent-os orchestrate services bridge {service_id} --plan {plan_rec['id']}`) to run it through Claude Code"
        raise ValueError(message)
    terms_ack = _check_terms(service, plan_rec, ack_terms, today)
    if service.get("integration_status") in ("catalog_only", "deferred"):
        raise ValueError(f"{service_id} is {service['integration_status']}: {service.get('integration_notes') or 'no automated preset is offered'}")
    facts = _model_facts(catalog, service, model)
    entry = model_profile.endpoint_entry(
        _provider_id(service_id, str(ep["id"]), provider_id), base_url=ep["base_url"], model=model, classes=list(classes),
        refusal_profile=facts["refusal_profile"], deployment=service.get("deployment"), open_weights=facts["open_weights"],
        license=facts["license"], context_window=facts["context_window"], secret_ref=_secret_ref(service_id, ep), cost=cost,
        max_concurrency=max_concurrency, modalities=facts["modalities"], roles=roles,
        billing=copy.deepcopy(plan_rec["billing"]) if plan_rec is not None and isinstance(plan_rec.get("billing"), dict) else None,
        privacy=copy.deepcopy(service["privacy"]) if isinstance(service.get("privacy"), dict) else None,
        path_style=ep.get("path_style") or "auto",
    )
    entry["options"]["catalog"] = {"service": service_id, "endpoint": ep["id"], "plan": plan_rec["id"] if plan_rec is not None else None}
    if terms_ack is not None:
        entry["options"]["terms_ack"] = terms_ack
    return entry


def bridge_entry(service_id: str, *, plan: str | None = None, models: dict[str, str] | None = None, provider_id: str | None = None,
                 roles: list[str] | None = None, cost: float = 1.0, ack_terms: bool = False, today: date | str | None = None,
                 catalog: dict[str, Any] | None = None) -> dict[str, Any]:
    """A ``claude_code`` entry that points Claude Code at the service's
    ``anthropic_messages`` endpoint. ``models`` maps Claude Code aliases
    (haiku/sonnet/opus) to the vendor's model ids."""
    catalog = _catalog(catalog)
    service = _service(catalog, service_id)
    if plan:
        plan_rec = _plan(service, plan)
    else:
        plan_rec = next((item for item in service.get("plans") or [] if isinstance(item, dict) and _lists_claude_code(_clients(item))), None)
    anthropic = _of_protocol(service, "anthropic_messages")
    if plan_rec is not None and _lists_claude_code(_clients(plan_rec)) and anthropic:
        # A plan that names Claude Code is used through the service's
        # Anthropic endpoint, even when its billing endpoint is openai_chat.
        bound = next((item for item in anthropic if item.get("id") == plan_rec.get("endpoint")), None)
        ep = bound or next((item for item in anthropic if item.get("id") == "default"), anthropic[0])
    else:
        ep, plan_rec = _select(service, "anthropic_messages", None, plan_rec["id"] if plan_rec is not None else None)
    if ep.get("protocol") != "anthropic_messages":
        raise ValueError(f"plan {plan_rec['id'] if plan_rec else plan} of {service_id} bills through {ep.get('protocol')} endpoint {ep.get('id')}; "
                         "a Claude Code bridge needs an anthropic_messages endpoint")
    clients = _clients(plan_rec) if plan_rec is not None else None
    if not (_any_client(clients) or _lists_claude_code(clients)):
        raise ValueError(f"{service_id} plan {plan_rec['id']} may only be used through {', '.join(clients or [])}, which does not include Claude Code")
    terms_ack = _check_terms(service, plan_rec, ack_terms, today)
    endpoints.validate_base_url(ep.get("base_url"))
    secret_ref = _secret_ref(service_id, ep)
    mapping = dict(models or {})
    bad = [alias for alias in mapping if alias not in BRIDGE_ALIASES]
    if bad:
        raise ValueError(f"model map keys must be among {', '.join(BRIDGE_ALIASES)}, got {', '.join(bad)}")
    for alias, value in mapping.items():
        if not isinstance(value, str) or not value.strip() or any(char.isspace() for char in value.strip()):
            raise ValueError(f"model map value for {alias} must be a model id without spaces")
    env = {"ANTHROPIC_BASE_URL": str(ep["base_url"]).rstrip("/")}
    for alias, value in mapping.items():
        env[f"ANTHROPIC_DEFAULT_{alias.upper()}_MODEL"] = value.strip()
    classes = {cls: alias for cls, alias in BRIDGE_CLASSES.items() if not mapping or alias in mapping}
    profile_raw: dict[str, Any] = {"deployment": service.get("deployment") or "subscription", "open_weights": False, "refusal_profile": "unknown"}
    if plan_rec is not None and isinstance(plan_rec.get("billing"), dict):
        profile_raw["billing"] = copy.deepcopy(plan_rec["billing"])
    if isinstance(service.get("privacy"), dict):
        profile_raw["privacy"] = copy.deepcopy(service["privacy"])
    profile = model_profile.normalize_profile(profile_raw, "claude_code")
    options: dict[str, Any] = {"env": env, "secret_env": {"ANTHROPIC_AUTH_TOKEN": secret_ref},
                               "catalog": {"service": service_id, "endpoint": ep["id"], "plan": plan_rec["id"] if plan_rec is not None else None}}
    if terms_ack is not None:
        options["terms_ack"] = terms_ack
    return {
        "id": provider_id or f"{service_id}-claude-code",
        "adapter": "claude_code",
        "enabled": True,
        "executable": "claude",
        "models": classes,
        "roles": list(roles or ["inline", "planner"]),
        "costs": {cls: float(cost) for cls in classes},
        "max_concurrency": 2,
        "options": options,
        "profile": {key: value for key, value in profile.items() if value is not None},
    }


# ---------------------------------------------------------------------------
# Discovery (read-only)
# ---------------------------------------------------------------------------


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """A redirect could carry the Authorization header to another host."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: D401 - urllib hook
        return None


def _default_opener(request: urllib.request.Request, timeout: float):
    return urllib.request.build_opener(_NoRedirect).open(request, timeout=timeout)


def _scrub(text: str, key: str | None) -> str:
    return text.replace(key, "<redacted>") if key else text


def _discovery_endpoint(service: dict[str, Any], endpoint: str | None) -> dict[str, Any]:
    if endpoint:
        return _endpoint(service, endpoint)
    items = [item for item in service.get("endpoints") or [] if isinstance(item, dict)]
    for item in items:
        if item.get("id") == "default":
            return item
    listed = [item for item in items if item.get("models_path")]
    if listed or items:
        return (listed or items)[0]
    raise ValueError(f"service {service['id']} has no endpoints")


def _cache_path(home: str | Path | None, service_id: str, endpoint_id: str) -> Path:
    from .store import orchestrator_home

    root = Path(home) if home else orchestrator_home()
    return root / CACHE_DIR / f"{service_id}--{endpoint_id}.json"


def _parse_models(payload: Any) -> list[dict[str, Any]]:
    items = payload.get("data") if isinstance(payload, dict) and isinstance(payload.get("data"), list) else \
        payload.get("models") if isinstance(payload, dict) and isinstance(payload.get("models"), list) else \
        payload if isinstance(payload, list) else None
    if items is None:
        raise ValueError("model list response has no data array")
    models = []
    for item in items:
        if isinstance(item, str):
            models.append({"id": item, "owned_by": None, "context_length": None})
        elif isinstance(item, dict) and isinstance(item.get("id"), str):
            length = next((item[key] for key in ("context_length", "context_window", "max_model_len") if isinstance(item.get(key), int)), None)
            models.append({"id": item["id"], "owned_by": item.get("owned_by") if isinstance(item.get("owned_by"), str) else None, "context_length": length})
    return models


def discover(service_id: str, endpoint: str | None = None, *, opener: Callable[..., Any] | None = None,
             resolve: Callable[[str], str | None] | None = None, home: str | Path | None = None,
             catalog: dict[str, Any] | None = None, timeout: float = 20) -> list[dict[str, Any]]:
    """GET the endpoint's model list (never POST) and cache it under
    ``<orchestrator home>/service-models/``. Authorization is sent only to the
    endpoint's own host, and only when a key is needed or configured."""
    catalog = _catalog(catalog)
    service = _service(catalog, service_id)
    ep = _discovery_endpoint(service, endpoint)
    models_path = ep.get("models_path")
    if not models_path:
        raise ValueError(f"endpoint {ep.get('id')} of {service_id} documents no model list (models_path is null)")
    base_url = ep.get("base_url")
    endpoints.validate_base_url(base_url)
    url = endpoints.url(base_url, "models", ep.get("path_style") or "auto", {"models": models_path})
    secret_ref = _secret_ref(service_id, ep)
    key = (resolve or secret_refs.resolve)(secret_ref)
    if ep.get("models_list_requires_auth") is True and not key:
        raise ValueError(f"listing models for {service_id} {ep['id']} needs an API key; store it with `agent-os orchestrate secrets set {secret_ref}`")
    headers = {"Accept": "application/json", "User-Agent": "agent-os/1"}
    if key and urlsplit(url).hostname == urlsplit(base_url).hostname:
        headers["Authorization"] = f"Bearer {key}"
    request = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with (opener or _default_opener)(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8", errors="replace"))
    except urllib.error.HTTPError as exc:
        exc.close()
        raise ValueError(_scrub(f"model list request GET {url} failed: HTTP {exc.code} {exc.reason or ''}".strip(), key)) from None
    except urllib.error.URLError as exc:
        raise ValueError(_scrub(f"model list request GET {url} failed: {exc.reason}", key)) from None
    except json.JSONDecodeError:
        raise ValueError(f"model list response from {url} is not JSON") from None
    models = _parse_models(payload)
    if key and key in json.dumps(models):
        models = json.loads(_scrub(json.dumps(models), key))
    from ..storage import write_json

    write_json(_cache_path(home, service_id, str(ep["id"])), {
        "fetched_at": datetime.now(timezone.utc).isoformat(), "service": service_id, "endpoint": ep["id"], "models": models,
    })
    return models


def cached_models(service_id: str, endpoint: str | None = None, home: str | Path | None = None,
                  catalog: dict[str, Any] | None = None) -> dict[str, Any] | None:
    """The last ``discover`` result ``{fetched_at, service, endpoint, models}``, or None."""
    if endpoint is None:
        try:
            endpoint = str(_discovery_endpoint(_service(_catalog(catalog), service_id), None)["id"])
        except (FileNotFoundError, ValueError):
            endpoint = "default"
    path = _cache_path(home, service_id, endpoint)
    try:
        cached = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return None
    return cached if isinstance(cached, dict) else None
