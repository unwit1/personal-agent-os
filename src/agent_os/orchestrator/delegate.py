"""One-shot, read-only delegation: ``agent-os orchestrate delegate``.

Coding runs need worktrees, review and integration. Much meta-work does not:
inventory, classification, schema comparison, cross-referencing. Those are
single read-only calls whose output can be checked objectively. This module
sends one such task through the same router and provider adapters the engine
uses -- no provider or model is named here -- validates the answer against an
output contract, and records a capability observation (task family x role x
provider x concrete model x effort) so routing can later be driven by measured
Agent OS outcomes instead of priors (docs/orchestrator-os/CONSTITUTION.md, §6).

The worker runs with ``read_only=True`` (the adapter's read-only sandbox /
permission mode). It cannot edit the repository, so there is nothing to review
or integrate; the contract check is the validator.
"""

from __future__ import annotations

import json
import time
import uuid
from pathlib import Path
from typing import Any

from ..timestamps import utc_now_iso
from . import capability
from .adapters import ADAPTERS
from .adapters.base import AgentLaunchRequest, AgentResult, extract_structured
from .router import ProviderRegistry, select
from .store import orchestrator_home

ROLE = "analyst"
CONTRACT_TYPES = {"object": dict, "array": list, "string": str, "number": (int, float), "integer": int, "boolean": bool}
RESULT_INSTRUCTIONS = (
    "\n\n---\nYou are a read-only analyst. Do not modify any files.\n"
    "End your answer with exactly one fenced ```json block containing the result object"
    " that satisfies this contract (keys and JSON types):\n{contract}\n"
)


def check_contract(value: Any, contract: dict[str, Any] | None) -> list[str]:
    """Minimal, dependency-free output contract: required keys, JSON types, and
    for arrays of objects, required item keys and allowed enum values.

    ``{"required": {"items": "array"}, "items": {"required": {"id": "string"},
    "enums": {"status": ["a", "b"]}, "min_items": 1}}``
    """
    if not contract:
        return [] if isinstance(value, dict) else ["no JSON object in output"]
    if not isinstance(value, dict):
        return ["no JSON object in output"]
    errors: list[str] = []
    for key, kind in (contract.get("required") or {}).items():
        if key not in value:
            errors.append(f"missing key {key}")
        elif not isinstance(value[key], CONTRACT_TYPES.get(kind, object)) or (kind in {"number", "integer"} and isinstance(value[key], bool)):
            errors.append(f"{key} is not {kind}")
    for key, rule in contract.items():
        if key in {"required"} or not isinstance(rule, dict) or not isinstance(value.get(key), list):
            continue
        items = value[key]
        if len(items) < int(rule.get("min_items", 0)):
            errors.append(f"{key} has {len(items)} items, expected at least {rule['min_items']}")
        for index, item in enumerate(items):
            if not isinstance(item, dict):
                errors.append(f"{key}[{index}] is not an object")
                continue
            for field, kind in (rule.get("required") or {}).items():
                if field not in item or not isinstance(item[field], CONTRACT_TYPES.get(kind, object)):
                    errors.append(f"{key}[{index}].{field} missing or not {kind}")
            for field, allowed in (rule.get("enums") or {}).items():
                if field in item and item[field] not in allowed:
                    errors.append(f"{key}[{index}].{field}={item[field]!r} not in {allowed}")
        if "expected_ids" in rule:
            got = {str(item.get("id")) for item in items if isinstance(item, dict)}
            missing = [item for item in rule["expected_ids"] if item not in got]
            if missing:
                errors.append(f"{key} missing ids: {', '.join(missing[:10])}")
    return errors[:25]


def _availability(registry: ProviderRegistry) -> dict[str, bool]:
    result = {}
    for provider in registry.providers:
        factory = ADAPTERS.get(provider.get("adapter") or "")
        result[provider["id"]] = bool(factory and factory(provider).probe().available)
    return result


def delegate(
    prompt: str,
    *,
    task_family: str,
    capability_class: str = "fast",
    effort: str = "low",
    contract: dict[str, Any] | None = None,
    provider: str | None = None,
    model: str | None = None,
    cwd: str | Path = ".",
    timeout_seconds: int = 900,
    registry: ProviderRegistry | None = None,
    record: bool = True,
    home: Path | None = None,
) -> dict[str, Any]:
    """Route, run, validate and record one read-only task. Never raises for a
    worker failure; the outcome is in the returned record."""
    registry = registry or ProviderRegistry()
    override = {"provider": provider, "model": model} if (provider or model) else None
    choice = select(registry, capability_class=capability_class, effort=effort, role=ROLE, availability=_availability(registry), override=override)
    call_id = f"DLG-{uuid.uuid4().hex[:12]}"
    root = Path(home or orchestrator_home()) / "delegations" / call_id
    root.mkdir(parents=True, exist_ok=True)
    outcome: dict[str, Any] = {"id": call_id, "task_family": task_family, "role": ROLE, "requested_class": capability_class, "effort": effort, "selection": choice, "started_at": utc_now_iso()}
    if not choice.get("resolved"):
        outcome.update(status="unroutable", errors=[choice.get("reason") or "no provider"], result=None)
        return _finish(outcome, root, record, home)
    prompt_path = root / "prompt.md"
    prompt_path.write_text(prompt + RESULT_INSTRUCTIONS.format(contract=json.dumps(contract or {"<any>": "object"})), encoding="utf-8")
    entry = registry.get(choice["provider"]) or {}
    adapter = ADAPTERS[choice["adapter"]](entry)
    request = AgentLaunchRequest(
        run_id=call_id, node_id="delegate", role="planner", cwd=str(Path(cwd).resolve()), prompt_path=str(prompt_path),
        output_dir=str(root), capability_class=choice["capability_class"], effort=effort, model=choice["model"],
        provider_effort=choice.get("provider_effort"), read_only=True, timeout_seconds=timeout_seconds,
    )
    started = time.monotonic()
    try:
        handle = adapter.start(request)
        while adapter.poll(handle).running:
            if time.monotonic() - started > timeout_seconds:
                adapter.cancel(handle)
                break
            time.sleep(1.0)
        result: AgentResult = adapter.collect(handle)
    except Exception as exc:  # provider/environment failure is data, not a crash
        result = AgentResult(outcome="failed", failure_kind="unavailable", detail=f"{type(exc).__name__}: {exc}"[:400])
    seconds = round(time.monotonic() - started, 2)
    structured = result.structured
    if structured is None and result.outcome == "completed":
        full = handle.result_path and Path(handle.result_path).exists() and Path(handle.result_path).read_text(encoding="utf-8", errors="replace")
        structured = extract_structured(full or result.summary)
    errors = [] if result.outcome != "completed" else check_contract(structured, contract)
    status = "failed" if result.outcome != "completed" else ("passed" if not errors else "contract_failed")
    if result.outcome != "completed":
        errors = [f"{result.failure_kind}: {result.detail or ''}".strip()]
    (root / "result.json").write_text(json.dumps(structured, indent=1) if structured is not None else "null", encoding="utf-8")
    outcome.update(
        status=status, errors=errors, seconds=seconds, usage=result.usage,
        model_resolved=(result.usage or {}).get("model_resolved") or choice["model"],
        result_path=str(root / "result.json"), result=structured,
    )
    return _finish(outcome, root, record, home)


def _finish(outcome: dict[str, Any], root: Path, record: bool, home: Path | None) -> dict[str, Any]:
    outcome["finished_at"] = utc_now_iso()
    summary = {key: value for key, value in outcome.items() if key != "result"}
    (root / "outcome.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    if record:
        selection = outcome.get("selection") or {}
        usage = outcome.get("usage") or {}
        capability.record_observation({
            "call_id": outcome["id"], "task_family": outcome["task_family"], "role": outcome["role"],
            "provider": selection.get("provider"), "model": selection.get("model"),
            "model_resolved": outcome.get("model_resolved"), "capability_class": selection.get("capability_class"),
            "effort": outcome["effort"], "toolset": "read_only", "status": outcome["status"],
            "validator_passed": outcome["status"] == "passed", "repairs": 0,
            "failure_type": None if outcome["status"] == "passed" else (outcome.get("errors") or ["unknown"])[0][:120],
            "seconds": outcome.get("seconds"), "input_tokens": usage.get("input_tokens"),
            "output_tokens": usage.get("output_tokens"), "cost_usd": usage.get("cost_usd"),
            "usage_accuracy": usage.get("accuracy"), "at": outcome["finished_at"],
        }, home=home)
    return outcome
