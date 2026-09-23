"""Model catalog: which models exist, which are new, which are outdated, and
which tier each provider should use -- kept current from local and online
sources without a model call.

Sources (each best-effort; a failing source is recorded, never fatal):

* local: the Codex CLI's own catalog (``~/.codex/models_cache.json``, which
  the CLI refreshes online), the provider registry, and the concrete model
  versions recent runs actually used (Claude reports the version behind an
  alias such as ``sonnet``);
* online: official vendor model pages (``MODEL_SOURCES``; override with
  ``~/.agent-os/model-sources.json``), fetched over HTTPS and scanned for
  model identifiers.

The catalog remembers when each model was first and last seen. A refresh
produces *notices* (a new model appeared, an alias started resolving to a new
version, a mapped model is now called older/legacy by its vendor) and
*proposals* (map a tier to a different model). Proposals change what runs and
what it costs, so they are applied only on request (``apply``), which writes a
per-tier ``model_overrides`` entry to the registry with a backup. Newer
versions within a tier's own family are still picked up automatically by the
adapters' discovery.

Nothing here decides quality on its own: ``trial`` runs a candidate on a real
small task, and the telemetry scorecard (usage_report) shows how each model
has done per role.
"""

from __future__ import annotations

import json
import re
import threading
import time
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from ..timestamps import utc_now_iso as now
from .store import orchestrator_home

MODEL_SOURCES: list[dict[str, str]] = [
    {"id": "anthropic-models", "provider": "claude-code", "url": "https://platform.claude.com/docs/en/models/overview", "pattern": r"claude-(?:opus|sonnet|haiku|fable)-\d+(?:-\d+)?(?:-\d{8})?"},
    {"id": "openai-codex-models", "provider": "codex", "url": "https://developers.openai.com/codex/models", "pattern": r"gpt-\d+(?:\.\d+)?-[a-z]+"},
    {"id": "openai-api-models", "provider": "codex", "url": "https://developers.openai.com/api/docs/models", "pattern": r"gpt-\d+(?:\.\d+)?-[a-z]+"},
]
STALE_AFTER = timedelta(hours=24)
FETCH_TIMEOUT = 20
OUTDATED_WORDS = ("older", "legacy", "deprecated", "retired", "retirement")
_CLAUDE_ID = re.compile(r"^claude-(?P<family>[a-z]+)-(?P<major>\d+)(?:-(?P<minor>\d{1,2}))?(?:-(?P<date>\d{8}))?$")
_GPT_ID = re.compile(r"^gpt-(?P<version>\d+(?:\.\d+)*)-(?P<family>[a-z]+)$")
_LOCK = threading.Lock()


def catalog_path() -> Path:
    return orchestrator_home() / "models" / "catalog.json"


def load() -> dict[str, Any]:
    try:
        return json.loads(catalog_path().read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"models": {}, "checks": [], "notices": [], "proposals": [], "trials": [], "aliases": {}, "refreshed_at": None}


def _save(catalog: dict[str, Any]) -> None:
    path = catalog_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(catalog, indent=1), encoding="utf-8")


def version_key(model_id: str) -> tuple[str, tuple[int, ...]] | None:
    """(family, version) for ordering models within a family."""
    match = _CLAUDE_ID.match(model_id)
    if match:
        return f"claude-{match['family']}", (int(match["major"]), int(match["minor"] or 0), int(match["date"] or 0))
    match = _GPT_ID.match(model_id)
    if match:
        return f"gpt-{match['family']}", tuple(int(part) for part in match["version"].split("."))
    return None


def is_outdated(description: str | None) -> bool:
    text = (description or "").casefold()
    return any(word in text for word in OUTDATED_WORDS)


# ---------------------------------------------------------------------------
# Sources
# ---------------------------------------------------------------------------


def sources() -> list[dict[str, str]]:
    override = Path.home() / ".agent-os" / "model-sources.json"
    try:
        data = json.loads(override.read_text(encoding="utf-8-sig"))
        if isinstance(data, list) and all(isinstance(item, dict) and item.get("url") for item in data):
            return data
    except (OSError, json.JSONDecodeError):
        pass
    return list(MODEL_SOURCES)


def fetch_online(source: dict[str, str], opener=None) -> dict[str, Any]:
    started = time.monotonic()
    try:
        request = urllib.request.Request(source["url"], headers={"User-Agent": "agent-os-model-catalog/1"})
        with (opener or urllib.request.urlopen)(request, timeout=FETCH_TIMEOUT) as response:
            body = response.read(3_000_000).decode("utf-8", "replace")
        ids = sorted(set(re.findall(source["pattern"], body)))
        return {"source": source["id"], "provider": source.get("provider"), "url": source["url"], "ok": bool(ids), "ids": ids, "error": None if ids else "no model identifiers found", "seconds": round(time.monotonic() - started, 2)}
    except Exception as exc:
        return {"source": source["id"], "provider": source.get("provider"), "url": source["url"], "ok": False, "ids": [], "error": f"{type(exc).__name__}: {exc}"[:200], "seconds": round(time.monotonic() - started, 2)}


def codex_local(cache_path: Path | None = None) -> dict[str, Any]:
    path = cache_path or Path.home() / ".codex" / "models_cache.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {"source": "codex-cli-catalog", "provider": "codex", "ok": False, "models": [], "error": f"{type(exc).__name__}: {exc}"[:200]}
    models = []
    for item in data.get("models") or []:
        if not isinstance(item, dict) or not item.get("slug"):
            continue
        models.append({
            "id": str(item["slug"]),
            "description": str(item.get("description") or "")[:200],
            "visible": item.get("visibility", "list") == "list",
            "priority": item.get("priority"),
            "reasoning_levels": [level.get("effort") for level in item.get("supported_reasoning_levels") or [] if isinstance(level, dict)],
            "context_window": item.get("context_window"),
        })
    return {"source": "codex-cli-catalog", "provider": "codex", "ok": True, "models": models, "fetched_at": data.get("fetched_at"), "error": None}


def resolved_versions(home: Path | None = None, limit_files: int = 200) -> dict[str, dict[str, str]]:
    """Concrete model versions recent runs used, per (provider, requested model)."""
    from .ledger import read_events

    root = Path(home or orchestrator_home())
    files = sorted(root.glob("runs/*/telemetry.jsonl"), key=lambda path: path.stat().st_mtime)[-limit_files:]
    seen: dict[str, dict[str, str]] = {}
    for path in files:
        for event in read_events(path)[0]:
            data = event.get("data") or {}
            usage = data.get("usage") or {}
            resolved = usage.get("model_resolved")
            if event["type"] == "model_completed" and resolved and data.get("provider") and data.get("model"):
                seen.setdefault(data["provider"], {})[data["model"]] = {"resolved": resolved, "at": event.get("at")}
    return seen


# ---------------------------------------------------------------------------
# Refresh
# ---------------------------------------------------------------------------


def refresh(*, online: bool = True, registry: Any = None, opener=None, codex_cache: Path | None = None) -> dict[str, Any]:
    """Merge every source into the catalog; record notices and proposals."""
    from .router import ProviderRegistry

    with _LOCK:
        catalog = load()
        first = not catalog["models"]
        stamp = now()
        checks: list[dict[str, Any]] = []
        found: dict[str, dict[str, Any]] = {}

        local = codex_local(codex_cache)
        checks.append({key: local.get(key) for key in ("source", "provider", "ok", "error")} | {"count": len(local["models"]), "at": stamp})
        for item in local["models"]:
            found.setdefault(item["id"], {"provider": "codex", "sources": set()}).update({k: v for k, v in item.items() if k != "id"})
            found[item["id"]]["sources"].add("codex-cli-catalog")
        if online:
            for source in sources():
                result = fetch_online(source, opener)
                checks.append({key: result.get(key) for key in ("source", "provider", "url", "ok", "error", "seconds")} | {"count": len(result["ids"]), "at": stamp})
                for model_id in result["ids"]:
                    found.setdefault(model_id, {"provider": result["provider"], "sources": set()})["sources"].add(result["source"])

        notices: list[dict[str, Any]] = []
        for model_id, info in found.items():
            entry = catalog["models"].get(model_id)
            if entry is None:
                entry = {"provider": info.get("provider"), "first_seen": stamp, "sources": []}
                catalog["models"][model_id] = entry
                if not first and info.get("visible", True):
                    notices.append({"kind": "new_model", "model": model_id, "provider": info.get("provider"), "text": f"New model available: {model_id}" + (f" — {info['description']}" if info.get("description") else ""), "at": stamp})
            entry["last_seen"] = stamp
            entry["sources"] = sorted(set(entry.get("sources") or []) | info["sources"])
            for key in ("description", "visible", "priority", "reasoning_levels", "context_window"):
                if key in info:
                    entry[key] = info[key]
            entry["outdated"] = is_outdated(entry.get("description"))
            entry.pop("missing_since", None)

        # A model that a source used to list, and that source (read fine this
        # time) no longer lists, is probably being retired.
        succeeded = {check["source"] for check in checks if check.get("ok")}
        for model_id, entry in catalog["models"].items():
            if model_id in found:
                continue
            gone = succeeded.intersection(entry.get("sources") or [])
            if gone and not entry.get("missing_since"):
                entry["missing_since"] = stamp
                entry["outdated"] = True
                notices.append({"kind": "model_missing", "model": model_id, "provider": entry.get("provider"), "text": f"{model_id} is no longer listed by {', '.join(sorted(gone))} (it may be retired)", "at": stamp})

        # Aliases (e.g. Claude's "sonnet") silently move to new versions.
        for provider, models in resolved_versions().items():
            for alias, observed in models.items():
                key = f"{provider}:{alias}"
                previous = (catalog["aliases"].get(key) or {}).get("resolved")
                if previous and previous != observed["resolved"]:
                    notices.append({"kind": "alias_moved", "provider": provider, "model": alias, "text": f"{alias} now runs {observed['resolved']} (was {previous})", "at": stamp})
                catalog["aliases"][key] = observed

        registry = registry or ProviderRegistry()
        proposals = propose(catalog, registry)
        known = {item["id"] for item in catalog["proposals"] if item.get("status") in {"applied", "dismissed"}}
        catalog["proposals"] = [item for item in catalog["proposals"] if item.get("status") in {"applied", "dismissed"}] + [item for item in proposals if item["id"] not in known]
        catalog["checks"] = (catalog["checks"] + checks)[-60:]
        catalog["notices"] = (catalog["notices"] + notices)[-50:]
        catalog["refreshed_at"] = stamp
        catalog["online"] = online
        _save(catalog)
        return {**view(catalog, registry), "new_notices": notices}


def is_stale(catalog: dict[str, Any] | None = None) -> bool:
    catalog = catalog or load()
    stamp = catalog.get("refreshed_at")
    if not stamp:
        return True
    try:
        return datetime.now(timezone.utc) - datetime.fromisoformat(stamp) > STALE_AFTER
    except ValueError:
        return True


def refresh_if_stale(**kwargs: Any) -> dict[str, Any] | None:
    return refresh(**kwargs) if is_stale() else None


# ---------------------------------------------------------------------------
# Proposals
# ---------------------------------------------------------------------------


def newest_in_family(catalog: dict[str, Any], model_id: str) -> str | None:
    """A newer listed version of the same family (e.g. claude-sonnet-5 ->
    claude-sonnet-5-1), or None."""
    key = version_key(model_id)
    if key is None:
        return None
    best = None
    for other, entry in catalog["models"].items():
        other_key = version_key(other)
        if other_key and other_key[0] == key[0] and other_key[1] > key[1] and entry.get("visible", True) and not entry.get("outdated"):
            if best is None or other_key[1] > version_key(best)[1]:
                best = other
    return best


TIER_WORDS = {
    "frontier": ("frontier", "most demanding", "hardest", "most capable", "most intelligent"),
    "fast": ("fast", "affordable", "easier", "efficient", "mini", "small", "lightweight"),
    "balanced": ("workhorse", "everyday", "balanced", "general", "coding"),
}


def described_tier(description: str | None) -> str | None:
    """The tier a vendor's own description puts a model in, if it says."""
    text = (description or "").casefold()
    for tier in ("frontier", "fast", "balanced"):
        if any(word in text for word in TIER_WORDS[tier]):
            return tier
    return None


def propose(catalog: dict[str, Any], registry: Any) -> list[dict[str, Any]]:
    """Tier changes worth a human decision, each with the evidence behind it.

    * a tier mapped to a model its vendor now calls older/legacy: propose the
      current model the vendor describes for the same kind of work (never a
      stronger, costlier tier);
    * a tier whose model (or the version an alias actually ran) has a newer
      listed version in the same line: propose that version.
    """
    proposals = []
    for provider in registry.providers:
        models = provider.get("models") or {}
        for tier, model in models.items():
            entry = catalog["models"].get(model)
            if entry and entry.get("outdated"):
                wanted = "balanced" if tier == "reasoning" else tier
                candidates = [
                    other for other, info in sorted(catalog["models"].items(), key=lambda item: (item[1].get("priority") or 999))
                    if info.get("provider") == provider["id"] and info.get("visible", True) and not info.get("outdated")
                    and other != model and described_tier(info.get("description")) == wanted
                ]
                if candidates:
                    choice = candidates[0]
                    why = f"{model} is no longer listed by the vendor" if entry.get("missing_since") else f"the vendor now describes {model} as \"{entry.get('description')}\""
                    proposals.append(_proposal(provider["id"], tier, model, choice, f"{why}; {choice} is described as \"{catalog['models'][choice].get('description')}\""))
                continue
            observed = ((catalog.get("aliases") or {}).get(f"{provider['id']}:{model}") or {}).get("resolved")
            basis = model if entry else observed
            newer = newest_in_family(catalog, basis) if basis else None
            if newer and newer not in models.values():
                ran = f" ({model} currently runs {observed})" if observed and not entry else ""
                proposals.append(_proposal(provider["id"], tier, model, newer, f"a newer version of the same model line is listed: {newer}{ran}"))
    return proposals


def _proposal(provider: str, tier: str, current: str, candidate: str, reason: str) -> dict[str, Any]:
    return {
        "id": f"{provider}:{tier}:{candidate}",
        "provider": provider,
        "tier": tier,
        "current": current,
        "candidate": candidate,
        "reason": reason,
        "status": "open",
        "created_at": now(),
    }


def decide(proposal_id: str, apply_it: bool, registry_file: Path | None = None) -> dict[str, Any]:
    """Apply (write ``model_overrides`` to the registry, with a backup) or
    dismiss a proposal."""
    from ..capabilities import registry_path

    with _LOCK:
        catalog = load()
        proposal = next((item for item in catalog["proposals"] if item["id"] == proposal_id), None)
        if proposal is None:
            raise KeyError(f"unknown proposal {proposal_id}")
        if apply_it:
            path = Path(registry_file or registry_path())
            raw = json.loads(path.read_text(encoding="utf-8-sig"))
            backup = path.with_name(f"{path.name}.bak-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}")
            backup.write_text(json.dumps(raw, indent=2), encoding="utf-8")
            entry = next((item for item in raw.get("providers") or [] if item.get("id") == proposal["provider"]), None)
            if entry is None:
                raise KeyError(f"provider {proposal['provider']} is not in {path}")
            entry.setdefault("model_overrides", {})[proposal["tier"]] = proposal["candidate"]
            path.write_text(json.dumps(raw, indent=2), encoding="utf-8")
            proposal.update(status="applied", decided_at=now(), backup=str(backup))
        else:
            proposal.update(status="dismissed", decided_at=now())
        _save(catalog)
        return proposal


# ---------------------------------------------------------------------------
# View
# ---------------------------------------------------------------------------


def view(catalog: dict[str, Any] | None = None, registry: Any = None) -> dict[str, Any]:
    from .router import ProviderRegistry

    catalog = catalog or load()
    registry = registry or ProviderRegistry()
    tiers = []
    for provider in registry.providers:
        for tier in ("fast", "balanced", "reasoning", "frontier"):
            model = (provider.get("models") or {}).get(tier)
            if not model:
                continue
            entry = catalog["models"].get(model) or {}
            alias = (catalog.get("aliases") or {}).get(f"{provider['id']}:{model}") or {}
            tiers.append({
                "provider": provider["id"], "tier": tier, "model": model, "runs_as": alias.get("resolved"),
                "description": entry.get("description"), "outdated": bool(entry.get("outdated")),
                "overridden": tier in (provider.get("model_overrides") or {}),
            })
    return {
        "refreshed_at": catalog.get("refreshed_at"),
        "stale": is_stale(catalog),
        "checks": catalog.get("checks", [])[-8:],
        "tiers": tiers,
        "notices": catalog.get("notices", [])[-10:],
        "proposals": [item for item in catalog.get("proposals", []) if item.get("status") == "open"],
        "trials": catalog.get("trials", [])[-10:],
        "known_models": len(catalog.get("models") or {}),
    }


def record_trial(result: dict[str, Any]) -> None:
    with _LOCK:
        catalog = load()
        catalog.setdefault("trials", []).append(result)
        catalog["trials"] = catalog["trials"][-40:]
        _save(catalog)


# ---------------------------------------------------------------------------
# Trials
# ---------------------------------------------------------------------------


def trial(provider: str, model: str, tier: str, *, timeout: float = 600) -> dict[str, Any]:
    """Run ``model`` as ``provider``'s ``tier`` model on the benchmark's small
    code change (real calls; spends usage) and record what happened: whether
    the model is usable on this account, whether the change was delivered,
    and exact tokens. A trial is evidence for a proposal, never an automatic
    switch."""
    import tempfile
    import shutil

    from . import benchmark
    from .router import ProviderRegistry

    base = ProviderRegistry()
    if base.get(provider) is None:
        raise KeyError(f"provider {provider} is not configured")
    providers = [dict(item, models={**item["models"], tier: model}) if item["id"] == provider else item for item in base.providers]
    registry = ProviderRegistry(providers=providers, discover=False)
    root = orchestrator_home() / "models" / "trials" / f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{provider}-{tier}"
    root.mkdir(parents=True, exist_ok=True)
    repo = benchmark.build_fixture(root)
    engine = benchmark._engine(root / "state", registry)
    task = {"id": "farewell", "goal": "Add farewell(name) to app/greet.py returning 'Goodbye, <name>!' and a unit test", "scope": ["app/greet.py", "tests/test_greet.py"], "capability_class": tier, "effort": "low"}
    started = time.monotonic()
    summary = engine.create_run("model trial", repository=repo, tasks=[task], policy=benchmark._policy(default_validators=[benchmark.TEST_VALIDATOR]), overrides={"roles": {"implementer": {"provider": provider}}})
    engine.start(summary["run_id"], True)
    final = engine.run_loop(summary["run_id"], max_seconds=timeout)
    events = engine.ledger.read(summary["run_id"])[0]
    calls = [event["data"] for event in events if event["type"] in {"model_completed", "model_failed"} and event["data"].get("role") == "implementer"]
    candidate_calls = [call for call in calls if call.get("provider") == provider and call.get("model") == model]
    failures = sorted({call.get("failure_kind") for call in candidate_calls if call.get("failure_kind")})
    usage = [call["usage"] for call in candidate_calls if (call.get("usage") or {}).get("accuracy") == "exact"]
    result = {
        "provider": provider, "model": model, "tier": tier, "at": now(),
        "usable": bool(candidate_calls) and not any(kind in {"invalid_model", "unavailable"} for kind in failures),
        "delivered": benchmark._delivered(repo, final, *benchmark.CHECKS["farewell"]),
        "state": final["state"],
        "candidate_calls": len(candidate_calls),
        "failure_kinds": failures,
        "escalations": sum(1 for event in events if event["type"] == "model_escalated"),
        "input_tokens": sum(item.get("input_tokens") or 0 for item in usage),
        "output_tokens": sum(item.get("output_tokens") or 0 for item in usage),
        "seconds": round(time.monotonic() - started, 1),
        "transcript": str(engine.ledger.paths(summary["run_id"])[1]),
    }
    record_trial(result)
    with _LOCK:
        catalog = load()
        for proposal in catalog.get("proposals", []):
            if proposal["provider"] == provider and proposal["tier"] == tier and proposal["candidate"] == model:
                proposal.setdefault("trials", []).append({key: result[key] for key in ("at", "usable", "delivered", "input_tokens", "escalations", "failure_kinds")})
        _save(catalog)
    shutil.rmtree(repo, ignore_errors=True)
    return result
