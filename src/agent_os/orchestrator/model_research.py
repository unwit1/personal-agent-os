"""Subscription model research: which included models fit which task family.

``orchestrate services research nanogpt`` re-reads the live subscription
catalog (``<subscription base>/models?detailed=true``, read-only), the plan's
allowance (``/usage``), and local evidence, and writes a ranked fit table to
``projects/personal-agent-os/research/model-services/nanogpt-fit.json``.

Evidence order inside each family, strongest first:

1. measured: pooled ``orchestrate foreman eval`` reports (planning) and
   capability observations from delegations and ``orchestrate eval``;
2. priors: cited public benchmarks in ``nanogpt-priors.json``;
3. declared capabilities (structured output, tool calling, reasoning,
   context) and recency, from the catalog.

Families are requirement filters over declared capabilities, so a new model
enters the table as soon as the vendor lists it. Rankings are advice for
choosing what to register and evaluate next; routing still uses the registry
and measured evidence.

``measure_multiplier`` finds a model's allowance multiplier (1x or 2x), which
the catalog does not expose: one short request, then the change in the weekly
``used`` units divided by the reported prompt tokens. Concurrent use of the
same account makes a reading noisy, so it reports the raw delta too.
"""

from __future__ import annotations

import json
import re
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

RESEARCH_DIR = Path(__file__).resolve().parents[3] / "projects" / "personal-agent-os" / "research" / "model-services"
SUBSCRIPTION_BASE = "https://nano-gpt.com/api/subscription/v1"
SECRET_REF = "secrets://nanogpt/subscription"
_UNCENSORED = re.compile(r"abliterat|obliterat|uncensor|derestrict|heretic|unshackled", re.I)

# Family -> (description, requirement over a catalog entry).
FAMILIES: dict[str, tuple[str, Callable[[dict[str, Any]], bool]]] = {
    "planning": ("foreman / planner: decomposes a goal into a JSON task plan",
                 lambda m: _cap(m, "structured_output") and _cap(m, "reasoning") and (m.get("context_length") or 0) >= 128_000),
    "coding_agent": ("multi-step coding with tools (needs a coding CLI bridge to edit files)",
                     lambda m: _cap(m, "tool_calling") and _cap(m, "reasoning") and (m.get("context_length") or 0) >= 200_000),
    "long_context": ("reading large inputs: repositories, document sets, transcripts",
                     lambda m: (m.get("context_length") or 0) >= 900_000),
    "extraction": ("schema-bound extraction and structured output",
                   lambda m: _cap(m, "structured_output")),
    "triage": ("fast, cheap classification, routing and short summaries",
               lambda m: (_price(m) or 1.0) <= 0.15 and (m.get("context_length") or 0) >= 128_000),
    "vision": ("image understanding", lambda m: _cap(m, "vision")),
    "uncensored_writing": ("content a standard model refuses; personal, non-sensitive use",
                           lambda m: bool(_UNCENSORED.search(str(m.get("id")))) or m.get("category") == "Uncensored"),
}


def _cap(model: dict[str, Any], name: str) -> bool:
    return bool((model.get("capabilities") or {}).get(name))


def _price(model: dict[str, Any]) -> float | None:
    value = (model.get("pricing") or {}).get("prompt")
    return float(value) if isinstance(value, (int, float)) else None


def _get(url: str, key: str | None = None, opener: Callable[..., Any] = urllib.request.urlopen) -> dict[str, Any]:
    headers = {"user-agent": "agent-os/1", **({"Authorization": f"Bearer {key}"} if key else {})}
    with opener(urllib.request.Request(url, headers=headers), timeout=60) as response:
        return json.loads(response.read().decode())


def load_priors(directory: Path | None = None) -> dict[str, Any]:
    try:
        return json.loads(((directory or RESEARCH_DIR) / "nanogpt-priors.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"models": {}, "sources": {}}


def measured_planning(reports: list[dict[str, Any]], model: str) -> dict[str, Any] | None:
    from .foreman_strategy import _pooled

    pooled = _pooled(model, reports)
    return pooled if pooled and pooled.get("cases") else None


def measured_capability(observations: list[dict[str, Any]], model: str) -> list[dict[str, Any]]:
    from .capability import summarize

    rows = []
    for record in summarize([item for item in observations if (item.get("model_resolved") or item.get("model")) == model]):
        metrics = record.get("metrics") or {}
        if metrics.get("sample_count"):
            rows.append({"task_family": record["key"].get("task_family"), "n": metrics["sample_count"],
                         "pass_rate": metrics.get("validator_pass_rate"), "wilson95": metrics.get("pass_rate_wilson95")})
    return rows


def _score(model: dict[str, Any], family: str, prior: dict[str, Any], planning: dict[str, Any] | None) -> tuple:
    """Sort key, best first: measured, then prior, then declared signals."""
    measured = None
    if family == "planning" and planning:
        # Wilson lower bound of the after-strategy rate: few cases rank lower.
        measured = planning.get("wilson_low")
    aa = prior.get("aa_index")
    return (
        -(measured if measured is not None else -1.0),
        -(float(aa) if isinstance(aa, (int, float)) else -1.0),
        -(model.get("context_length") or 0) if family == "long_context" else 0,
        (_price(model) or 9.9) if family == "triage" else 0,
        -int(model.get("created") or 0),
    )


def build_fit(models: list[dict[str, Any]], *, priors: dict[str, Any], reports: list[dict[str, Any]],
              observations: list[dict[str, Any]], usage: dict[str, Any] | None = None, top: int = 8) -> dict[str, Any]:
    prior_models = priors.get("models") or {}
    planning = {model["id"]: measured_planning(reports, model["id"]) for model in models}
    families = {}
    for family, (description, wanted) in FAMILIES.items():
        members = [model for model in models if wanted(model)]
        if family != "uncensored_writing":
            # Roleplay fine-tunes satisfy capability filters but are tuned for fiction.
            members = [model for model in members if model.get("category") != "Roleplay/storytelling models"]
        members.sort(key=lambda model: _score(model, family, prior_models.get(model["id"]) or {}, planning.get(model["id"])))
        rows = []
        for model in members[:top]:
            prior = prior_models.get(model["id"]) or {}
            rows.append({
                "id": model["id"],
                "context": model.get("context_length"),
                "capabilities": sorted(name for name, on in (model.get("capabilities") or {}).items() if on),
                "open_weights": model.get("open_weights"),
                "released": datetime.fromtimestamp(int(model["created"]), timezone.utc).date().isoformat() if model.get("created") else None,
                "measured": {key: value for key, value in {
                    "planning": planning.get(model["id"]) if family == "planning" else None,
                    "capability": measured_capability(observations, model["id"]) or None}.items() if value},
                "prior": {key: prior[key] for key in ("aa_index", "aa_version", "aa_note", "swe_bench_verified", "livebench_agentic_coding", "notes", "sources") if key in prior},
            })
        families[family] = {"description": description, "eligible": len(members), "ranked": rows}
    abliterated = [model["id"] for model in models if _UNCENSORED.search(str(model.get("id")))]
    return {
        "schema": "nanogpt-fit/1",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "catalog": {"models": len(models), "open_weights": sum(1 for model in models if model.get("open_weights")),
                    "categories": _count(model.get("category") or "(none)" for model in models), "uncensored_or_abliterated": abliterated},
        "allowance": _allowance(usage),
        "families": families,
        "evidence_order": ["measured (foreman eval, capability observations)", "cited priors (nanogpt-priors.json)", "declared capabilities and recency"],
        "sources": priors.get("sources") or {},
    }


def _count(values) -> dict[str, int]:
    out: dict[str, int] = {}
    for value in values:
        out[value] = out.get(value, 0) + 1
    return dict(sorted(out.items(), key=lambda pair: -pair[1]))


def _allowance(usage: dict[str, Any] | None) -> dict[str, Any] | None:
    if not usage:
        return None
    weekly = usage.get("weeklyInputTokens") or {}
    limits = usage.get("limits") or {}
    return {"weekly_input_units": limits.get("weeklyInputTokens"), "used": weekly.get("used"), "remaining": weekly.get("remaining"),
            "resets_at": datetime.fromtimestamp(weekly["resetAt"] / 1000, timezone.utc).isoformat(timespec="seconds") if weekly.get("resetAt") else None,
            "daily_input_units": limits.get("dailyInputTokens"), "daily_images": limits.get("dailyImages"),
            "overage_enabled": bool(usage.get("allowOverage") or (usage.get("routing") or {}).get("paidOverageEnabled")),
            "period_end": (usage.get("period") or {}).get("currentPeriodEnd")}


def measure_multiplier(model: str, *, key: str, base: str = SUBSCRIPTION_BASE, opener: Callable[..., Any] = urllib.request.urlopen,
                       settle: float = 3.0, sleep: Callable[[float], None] = time.sleep) -> dict[str, Any]:
    before = _get(base + "/usage", key, opener)["weeklyInputTokens"]["used"]
    body = json.dumps({"model": model, "messages": [{"role": "user", "content": "Count from one to twenty in words, comma separated. " * 20}],
                       "max_tokens": 16}).encode()
    request = urllib.request.Request(base + "/chat/completions", data=body, method="POST",
                                     headers={"Authorization": f"Bearer {key}", "content-type": "application/json", "user-agent": "agent-os/1"})
    with opener(request, timeout=120) as response:
        reply = json.loads(response.read().decode())
    sleep(settle)
    after = _get(base + "/usage", key, opener)["weeklyInputTokens"]["used"]
    prompt = int((reply.get("usage") or {}).get("prompt_tokens") or 0)
    delta = after - before
    ratio = round(delta / prompt, 2) if prompt else None
    # Plans charge 1x or 2x; anything else means other use of the account landed in between.
    noisy = ratio is None or ratio < 0.8 or ratio > 2.3 or abs(ratio - round(ratio)) > 0.2
    return {"model": model, "prompt_tokens": prompt, "allowance_delta": delta, "ratio": ratio,
            "multiplier": None if noisy else int(round(ratio)), "noisy": noisy, "measured_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}


def research(*, directory: Path | None = None, opener: Callable[..., Any] = urllib.request.urlopen, key: str | None = None,
             reports: list[dict[str, Any]] | None = None, observations: list[dict[str, Any]] | None = None,
             measure: list[str] | None = None, write: bool = True) -> dict[str, Any]:
    from .capability import read_observations
    from .foreman_strategy import _eval_reports
    from .secret_refs import resolve

    key = key if key is not None else resolve(SECRET_REF)
    models = _get(SUBSCRIPTION_BASE + "/models?detailed=true", key, opener).get("data") or []
    usage = None
    if key:
        try:
            usage = _get(SUBSCRIPTION_BASE + "/usage", key, opener)
        except Exception:
            usage = None
    fit = build_fit(models, priors=load_priors(directory), reports=_eval_reports(None) if reports is None else reports,
                    observations=read_observations() if observations is None else observations, usage=usage)
    if measure:
        if not key:
            raise ValueError(f"measuring multipliers needs the subscription key at {SECRET_REF}")
        fit["multipliers"] = [measure_multiplier(model, key=key, opener=opener) for model in measure]
    if write:
        path = (directory or RESEARCH_DIR) / "nanogpt-fit.json"
        previous = {}
        try:
            previous = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            pass
        if not measure and previous.get("multipliers"):
            fit["multipliers"] = previous["multipliers"]  # keep earlier readings
        path.write_text(json.dumps(fit, indent=1) + "\n", encoding="utf-8")
        fit["written"] = str(path)
    return fit
