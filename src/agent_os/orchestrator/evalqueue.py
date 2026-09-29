"""Eval-queue runner: measure queued catalog models once they are served (IMP-0015).

The Research Radar (radar.py) queues licensed, adopted models with suggested
EVS suites in ``<home>/eval-queue.jsonl``. Once the operator serves one and
registers it (``orchestrate model-add``), ``run`` evaluates it through the
protected harness (``orchestrate eval``: incumbent route vs candidate route,
EVR written, CAP observations recorded) and appends the outcome to the queue.

Attribution guard: eval delegates with the ``analyst`` role. An endpoint
registered for ``inline`` only would be skipped by the router, which would
then answer the case with a *different* provider -- scoring the wrong model.
The runner therefore (1) refuses a candidate provider that does not allow the
``analyst`` role (register with ``model-add --roles inline,analyst``), and
(2) after each run checks that the candidate's recorded provider is the one
requested, marking the result ``invalid`` otherwise.

``plan`` is deterministic; ``run`` makes real model calls, bounded by
``max_calls`` per suite.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from ..timestamps import utc_now_iso
from .radar import queue_path

EVAL_ROLE = "analyst"


def entries(home: Path | None = None) -> list[dict[str, Any]]:
    path = queue_path(home)
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            item = json.loads(line)
        except ValueError:
            continue
        if isinstance(item, dict) and item.get("model_id"):
            rows.append(item)
    return rows


def current(home: Path | None = None) -> dict[tuple[str, str | None], dict[str, Any]]:
    """Latest queue state per (model_id, revision); the file is append-only."""
    state: dict[tuple[str, str | None], dict[str, Any]] = {}
    for row in entries(home):
        key = (row["model_id"], row.get("revision"))
        state[key] = {**state.get(key, {}), **row}
    return state


def _append(home: Path | None, entry: dict[str, Any]) -> None:
    path = queue_path(home)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")


def serving_provider(registry: Any, model_id: str) -> tuple[dict[str, Any] | None, str | None]:
    """First registered provider that serves exactly ``model_id``, and its class."""
    for provider in registry.providers:
        for capability, model in provider["models"].items():
            if model == model_id:
                return provider, capability
    return None, None


def plan(model_id: str | None = None, *, incumbent: str | None = None, registry: Any = None, home: Path | None = None) -> list[dict[str, Any]]:
    from .router import ProviderRegistry, select

    registry = registry or ProviderRegistry()
    state = current(home)
    # The default baseline must be an established route, never another
    # unproven catalog model still waiting for its own evaluation.
    unproven = {model for (model, _), item in state.items() if item.get("status") != "evaluated"}
    unproven_providers = [provider["id"] for provider in registry.providers if set(provider["models"].values()) & unproven]
    jobs = []
    for (queued_id, revision), item in sorted(state.items()):
        if model_id and queued_id != model_id:
            continue
        if item.get("status") not in {"queued", "error"}:
            continue
        provider, capability = serving_provider(registry, queued_id)
        job: dict[str, Any] = {"model_id": queued_id, "revision": revision, "suites": item.get("suggested_suites") or []}
        if provider is None:
            jobs.append({**job, "ready": False, "reason": "not served: register the endpoint with orchestrate model-add"})
            continue
        if provider["roles"] is not None and EVAL_ROLE not in provider["roles"]:
            jobs.append({**job, "ready": False, "reason": f"provider {provider['id']} lacks role {EVAL_ROLE}; re-register with --roles inline,{EVAL_ROLE} or eval would score another model"})
            continue
        if not job["suites"]:
            jobs.append({**job, "ready": False, "reason": "no suite covers this modality yet"})
            continue
        base = incumbent
        if not base:
            choice = select(registry, capability_class=capability or "fast", effort="low", role=EVAL_ROLE, excluded=[provider["id"], *unproven_providers])
            base = f"{choice['provider']}:{choice['model']}@{choice['capability_class']}" if choice.get("resolved") else None
        if not base:
            jobs.append({**job, "ready": False, "reason": "no incumbent route available; pass --incumbent provider[:model][@class]"})
            continue
        jobs.append({**job, "ready": True, "provider": provider["id"], "candidate": f"{provider['id']}:{queued_id}@{capability}", "incumbent": base})
    return jobs


def run(model_id: str | None = None, *, incumbent: str | None = None, max_calls: int = 6, registry: Any = None, home: Path | None = None,
        runner: Callable[..., dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    """Evaluate every ready job; append an outcome per job to the queue."""
    if runner is None:
        from . import eval as evaluation

        runner = evaluation.run
    outcomes = []
    for job in plan(model_id, incumbent=incumbent, registry=registry, home=home):
        if not job["ready"]:
            outcomes.append(job)
            continue
        evrs, problems = [], []
        for suite in job["suites"]:
            try:
                record = runner(suite, routes=[job["incumbent"], job["candidate"]], samples=1, max_calls=max_calls, write=True)
            except Exception as exc:
                problems.append(f"{suite}: {type(exc).__name__}: {str(exc)[:160]}")
                continue
            results = (record.get("metrics") or {}).get("results") or []
            candidate = next((item for item in results if item.get("ref") == job["candidate"]), None)
            if candidate is None or candidate.get("provider") != job["provider"]:
                problems.append(f"{suite}: candidate answered by {candidate.get('provider') if candidate else 'nobody'}, not {job['provider']} (result invalid)")
                continue
            evrs.append({"suite": suite, "evr": record.get("id") or record.get("written"), "outcome": record.get("outcome"),
                         "accuracy": candidate.get("accuracy"), "model_resolved": candidate.get("model_resolved")})
        status = "evaluated" if evrs and not problems else "invalid" if any("result invalid" in item for item in problems) else "error"
        entry = {"at": utc_now_iso(), "model_id": job["model_id"], "revision": job["revision"], "status": status,
                 "candidate": job["candidate"], "incumbent": job["incumbent"], "evrs": evrs, "problems": problems}
        _append(home, entry)
        outcomes.append({**job, **entry})
    return outcomes
