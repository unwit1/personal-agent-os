"""Provider-neutral model profiles and workload requirements (IMP-0015, Phase 0).

A provider registry entry may carry a ``profile`` describing *how* its models
are deployed and behave, independent of vendor:

```json
"profile": {
  "deployment": "local",              # subscription | api | serverless | gpu_pod | local
  "modalities": ["text", "code"],     # text code vision image audio multimodal embedding
  "open_weights": true,
  "license": "apache-2.0",
  "refusal_profile": "abliterated",   # standard | low | abliterated | unknown
  "context_window": 131072,
  "revision": "sha or tag"
}
```

A workload states ``requirements`` against those fields. Hard keys filter
providers; ``prefer_*`` keys only order otherwise-usable candidates ahead of
cost. The router stays vendor-neutral: it compares declared fields, never
names.

The refusal profile is a behavioural characteristic, not a quality score
(roadmap: "Do not treat uncensored or abliterated as a quality score"); measured
capability evidence still decides competence. Nothing here authorizes an
action: consequential writes, spending and secret access stay behind the
deterministic policy gates regardless of which model is chosen.
"""

from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

DEPLOYMENTS = ("subscription", "api", "serverless", "gpu_pod", "local")
MODALITIES = ("text", "code", "vision", "image", "audio", "multimodal", "embedding")
REFUSAL_PROFILES = ("standard", "low", "abliterated", "unknown")

# Hard requirement keys -> profile field; list values mean "any of".
HARD_KEYS = {"deployment": "deployment", "refusal_profile": "refusal_profile", "open_weights": "open_weights", "modalities": "modalities"}
SOFT_KEYS = {"prefer_deployment": "deployment", "prefer_refusal_profile": "refusal_profile"}

_SUBSCRIPTION_ADAPTERS = {"claude_code", "codex_cli"}
_LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1", "0.0.0.0"}


def default_deployment(adapter: Any, options: dict[str, Any] | None) -> str:
    """Infer deployment from the adapter when the registry does not say."""
    options = options or {}
    if adapter in _SUBSCRIPTION_ADAPTERS:
        return "subscription"
    base_url = str(options.get("base_url") or "")
    if base_url:
        host = (urlparse(base_url).hostname or "").lower()
        return "local" if host in _LOCAL_HOSTS else "api"
    if adapter in {"anthropic_api", "openai_api"}:
        return "api"
    return "subscription" if adapter else "api"


def _as_list(value: Any) -> list[str]:
    if value is None:
        return []
    items = value if isinstance(value, (list, tuple, set)) else str(value).split(",")
    return [str(item).strip().lower() for item in items if str(item).strip()]


def normalize_profile(raw: Any, adapter: Any = None, options: dict[str, Any] | None = None) -> dict[str, Any]:
    raw = raw if isinstance(raw, dict) else {}
    deployment = str(raw.get("deployment") or default_deployment(adapter, options)).lower()
    modalities = [item for item in _as_list(raw.get("modalities")) if item in MODALITIES] or ["text", "code"]
    refusal = str(raw.get("refusal_profile") or "standard").lower()
    context_window = raw.get("context_window")
    return {
        "deployment": deployment if deployment in DEPLOYMENTS else "api",
        "modalities": modalities,
        "open_weights": bool(raw.get("open_weights", deployment in {"local", "gpu_pod", "serverless"})),
        "license": str(raw["license"]) if raw.get("license") else None,
        "refusal_profile": refusal if refusal in REFUSAL_PROFILES else "unknown",
        "context_window": int(context_window) if isinstance(context_window, (int, float)) and context_window > 0 else None,
        "revision": str(raw["revision"]) if raw.get("revision") else None,
    }


def normalize_requirements(raw: Any) -> dict[str, Any]:
    """Validate workload requirements; unknown keys or values fail loudly so a
    typo cannot silently widen routing."""
    if not raw:
        return {}
    if not isinstance(raw, dict):
        raise ValueError("requirements must be an object")
    allowed = {"deployment": DEPLOYMENTS, "prefer_deployment": DEPLOYMENTS, "refusal_profile": REFUSAL_PROFILES,
               "prefer_refusal_profile": REFUSAL_PROFILES, "modalities": MODALITIES}
    out: dict[str, Any] = {}
    for key, value in raw.items():
        if key == "open_weights":
            out[key] = value if isinstance(value, bool) else str(value).strip().lower() in {"1", "true", "yes"}
            continue
        if key not in allowed:
            raise ValueError(f"unknown requirement {key!r} (known: {', '.join(sorted([*allowed, 'open_weights']))})")
        values = _as_list(value)
        bad = [item for item in values if item not in allowed[key]]
        if bad or not values:
            raise ValueError(f"requirement {key}: invalid value(s) {bad or value!r}; allowed: {', '.join(allowed[key])}")
        out[key] = values
    return out


def profile_problem(profile: dict[str, Any], requirements: dict[str, Any]) -> str | None:
    """Why a provider's profile fails the hard requirements, or None."""
    for key, field in HARD_KEYS.items():
        if key not in requirements:
            continue
        wanted, actual = requirements[key], profile.get(field)
        if key == "open_weights":
            if bool(actual) != bool(wanted):
                return f"profile open_weights={bool(actual)} but workload requires {bool(wanted)}"
        elif key == "modalities":
            missing = [item for item in wanted if item not in (actual or [])]
            if missing:
                return f"profile lacks modality {', '.join(missing)}"
        elif actual not in wanted:
            return f"profile {field}={actual} not in required {'/'.join(wanted)}"
    return None


def preference_rank(profile: dict[str, Any], requirements: dict[str, Any]) -> int:
    """0 when every soft preference matches; +1 per unmatched preference."""
    misses = 0
    for key, field in SOFT_KEYS.items():
        if key in requirements and profile.get(field) not in requirements[key]:
            misses += 1
    return misses


def parse_pairs(pairs: list[str] | None) -> dict[str, Any]:
    """CLI helper: ``["deployment=local,gpu_pod", "open_weights=true"]``."""
    raw: dict[str, Any] = {}
    for pair in pairs or []:
        key, sep, value = pair.partition("=")
        if not sep:
            raise ValueError(f"expected key=value, got {pair!r}")
        raw[key.strip()] = value.strip()
    return normalize_requirements(raw)


def endpoint_entry(
    provider_id: str,
    *,
    base_url: str,
    model: str,
    classes: list[str],
    refusal_profile: str = "standard",
    deployment: str | None = None,
    open_weights: bool | None = None,
    license: str | None = None,
    context_window: int | None = None,
    secret_ref: str | None = None,
    cost: float = 0.25,
    max_concurrency: int = 2,
    modalities: list[str] | None = None,
    roles: list[str] | None = None,
    revision: str | None = None,
) -> dict[str, Any]:
    """Registry entry for an OpenAI-compatible endpoint (vLLM, Ollama, LM
    Studio, llama.cpp server, TGI, a RunPod/serverless proxy): the plug-in path
    for an open-weight or abliterated model without code changes.

    Such workers have no repository tools, so they serve ``inline`` tasks
    (self-contained prompts, e.g. rendered context contracts) until measured
    evidence justifies more.
    """
    from .router import MODEL_CLASSES

    if not provider_id or not base_url or not model:
        raise ValueError("provider id, base_url and model are required")
    bad = [item for item in classes if item not in MODEL_CLASSES]
    if bad or not classes:
        raise ValueError(f"classes must be among {MODEL_CLASSES}, got {classes}")
    if secret_ref:
        from .secret_refs import parse

        parse(secret_ref)
    profile_raw: dict[str, Any] = {"refusal_profile": refusal_profile, "modalities": modalities or ["text", "code"]}
    for key, value in (("deployment", deployment), ("open_weights", open_weights), ("license", license), ("context_window", context_window), ("revision", revision)):
        if value is not None:
            profile_raw[key] = value
    profile = normalize_profile(profile_raw, "openai_api", {"base_url": base_url})
    if refusal_profile not in REFUSAL_PROFILES:
        raise ValueError(f"refusal_profile must be one of {REFUSAL_PROFILES}")
    options: dict[str, Any] = {"base_url": base_url.rstrip("/"), "send_reasoning_effort": False}
    if secret_ref:
        options["secret_ref"] = secret_ref
    return {
        "id": provider_id,
        "adapter": "openai_api",
        "enabled": True,
        "models": {item: model for item in classes},
        "roles": list(roles or ["inline"]),
        "costs": {item: float(cost) for item in classes},
        "max_concurrency": int(max_concurrency),
        "options": options,
        "profile": {key: value for key, value in profile.items() if value is not None},
    }
