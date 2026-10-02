"""Disposable free-worker fan-out and checkpointable backfill planning.

Pure planning: nothing here calls a model. ``plan_fanout`` returns bounded,
task-scoped worker specs only when validation is cheap; ``aggregate`` keeps the
first deterministic-validator-passing result; ``plan_backfill`` spends only the
governor's expiring capacity on useful queued work and checkpoints progress.
"""
from __future__ import annotations

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping

from . import free_routing
from .store import orchestrator_home

FANOUT_SCHEMA = "agent-os/free-fanout-worker/v1"
CHECKPOINT_SCHEMA = "agent-os/free-backfill-checkpoint/v1"
DEFAULT_MAX_VALIDATOR_COST = 0.05
BACKFILL_KINDS = frozenset({"tests", "docs", "static_review", "eval_sample", "triage", "metadata"})
DEFAULT_BATCH_SIZE = 4
# Plain validator categories, recognised from a declared category or command text.
_CATEGORY_PATTERNS = (
    ("test", re.compile(r"\b(unittest|pytest|tox|nose|test)s?\b", re.I)),
    ("lint", re.compile(r"\b(ruff|flake8|pylint|eslint|mypy|lint)\b", re.I)),
    ("schema", re.compile(r"\b(schema|jsonschema|validate)\b", re.I)),
)
PLAIN_CATEGORIES = frozenset(name for name, _ in _CATEGORY_PATTERNS)


class FanoutPlan(list):
    """List of worker specs; ``reason`` explains an empty plan."""

    def __init__(self, workers: Iterable[dict[str, Any]] = (), reason: str = "") -> None:
        super().__init__(workers)
        self.reason = reason


class BackfillPlan(dict):
    """Mapping with ``batches``, ``requests``, ``capacity``, ``skipped`` and ``reason``."""


def _category(validator: Any) -> str | None:
    if isinstance(validator, Mapping):
        declared = validator.get("category")
        if declared:
            return str(declared) if declared in PLAIN_CATEGORIES else None
        if validator.get("kind") not in (None, "command"):
            return None
        command = validator.get("command") or validator.get("name") or ""
        text = " ".join(str(part) for part in command) if isinstance(command, (list, tuple)) else str(command)
    else:
        text = str(validator)
    for name, pattern in _CATEGORY_PATTERNS:
        if pattern.search(text):
            return name
    return None


def _cheap_validation(task: Mapping[str, Any], max_cost: float) -> tuple[bool, str]:
    validators = task.get("validators")
    if not validators or not isinstance(validators, (list, tuple)):
        return False, "no declared validators"
    if any(_category(v) is None for v in validators):
        return False, "validation not plain test/lint/schema"
    cost = task.get("estimated_validator_cost")
    if not isinstance(cost, (int, float)) or isinstance(cost, bool):
        return False, "validator cost unknown"
    if cost >= max_cost:
        return False, f"validation expensive ({cost} >= {max_cost})"
    return True, "ok"


def plan_fanout(task: Mapping[str, Any], *, n: int, governor: Any, max_concurrency: int, catalog: Any,
                specializations: Iterable[Mapping[str, Any]], project_policy: Mapping[str, Any] | None = None,
                max_validator_cost: float = DEFAULT_MAX_VALIDATOR_COST) -> FanoutPlan:
    """Bounded free-worker specs for one task, or an empty plan carrying a reason."""
    policy = dict(project_policy or {})
    cheap, why = _cheap_validation(task, max_validator_cost)
    if not cheap:
        return FanoutPlan(reason=why)
    ok, failed = free_routing.eligible(
        task, sensitivity=str(task.get("sensitivity") or "internal"),
        protected_globs=policy.get("protected_globs") or [], allowed_sensitivity=policy.get("allowed_sensitivity"))
    if not ok:
        return FanoutPlan(reason="not free-eligible: " + "; ".join(failed))
    left = dict(governor.remaining())
    quota = min(int(left.get("daily_left", 0)), int(left.get("minute_left", 0)))
    count = min(int(n), int(max_concurrency), quota)
    if count <= 0:
        return FanoutPlan(reason=f"no capacity (n={n}, max_concurrency={max_concurrency}, quota={quota})")
    scoped = dict(task)
    scoped.setdefault("lane", "swarm")
    decision = free_routing.decide(scoped, catalog=catalog, specializations=specializations, governor=governor,
                                   project_policy=policy)
    if decision["route"] != "free":
        return FanoutPlan(reason="routing escalated: " + decision["reason"])
    models = [decision["model"]] + [a["model"] for a in decision["alternates"]]
    entries = catalog.get("models") if isinstance(catalog, Mapping) else catalog
    by_slug = {m.get("slug"): m for m in entries or []}
    workers = []
    for index in range(count):
        slug = models[index % len(models)]
        workers.append({
            "schema_version": FANOUT_SCHEMA,
            "worker": index,
            "of": count,
            "task_id": task.get("id") or task.get("node_id"),
            "task_family": task.get("task_family"),
            "model": slug,
            "revision": (by_slug.get(slug) or {}).get("revision"),
            "scope": list(task.get("scope") or []),
            "validators": list(task["validators"]),
            "retry_budget": 0,
            "disposable": True,
        })
    return FanoutPlan(workers)


def aggregate(results: Iterable[Mapping[str, Any]], validator: Callable[[Mapping[str, Any]], Any]) -> dict[str, Any]:
    """Map-reduce: first result the deterministic validator passes wins (no voting)."""
    checked = 0
    for result in results:
        checked += 1
        outcome = validator(result)
        passed = outcome.get("passed") if isinstance(outcome, Mapping) else bool(outcome)
        if passed:
            return {"accepted": True, "result": result, "checked": checked}
    return {"accepted": False, "result": None, "checked": checked}


def checkpoint_path(home: Path | None = None) -> Path:
    return (Path(home) if home is not None else orchestrator_home()) / "free-compute" / "backfill-checkpoint.json"


def load_checkpoint(home: Path | None = None) -> dict[str, Any]:
    try:
        data = json.loads(checkpoint_path(home).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        data = {}
    if not isinstance(data, Mapping):
        data = {}
    return {"schema_version": CHECKPOINT_SCHEMA, "done": [str(i) for i in data.get("done") or []],
            "cursor": data.get("cursor")}


def _save(checkpoint: Mapping[str, Any], home: Path | None, now: datetime | None = None) -> None:
    path = checkpoint_path(home)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = dict(checkpoint)
    payload["updated_at"] = now.isoformat() if now else None
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    os.replace(temp, path)


def record_done(item_ids: Iterable[str], home: Path | None = None) -> dict[str, Any]:
    """Mark queue items completed so a rerun skips them."""
    checkpoint = load_checkpoint(home)
    done = list(checkpoint["done"])
    done.extend(str(i) for i in item_ids if str(i) not in done)
    checkpoint["done"] = done
    _save(checkpoint, home)
    return checkpoint


def plan_backfill(queue: Iterable[Mapping[str, Any]], governor: Any, now: datetime | None = None, *,
                  home: Path | None = None, batch_size: int = DEFAULT_BATCH_SIZE) -> BackfillPlan:
    """Plan useful queued work within expiring capacity only. Makes no calls."""
    items = [i for i in queue or [] if isinstance(i, Mapping) and i.get("id") is not None]
    checkpoint = load_checkpoint(home)
    done = set(checkpoint["done"])
    pending = [i for i in items if str(i["id"]) not in done and i.get("kind") in BACKFILL_KINDS]
    skipped = [str(i["id"]) for i in items if str(i["id"]) in done]
    plan = BackfillPlan(batches=[], requests=0, capacity=0, skipped=skipped, reason="")
    if not pending:
        plan["reason"] = "no useful queued items"
        return plan
    capacity = max(0, int(governor.expiring_capacity(now)))  # the reserve is already excluded
    plan["capacity"] = capacity
    if capacity <= 0:
        plan["reason"] = "no expiring capacity"
        return plan
    groups: dict[tuple[str, str], list[Mapping[str, Any]]] = {}
    for item in pending:  # insertion order keeps queue priority
        key = str(item.get("batch_key") or item.get("task_family") or "")
        groups.setdefault((item["kind"], key), []).append(item)
    size = max(1, int(batch_size))
    batches: list[dict[str, Any]] = []
    for (kind, key), members in groups.items():
        for start in range(0, len(members), size):
            batches.append({"kind": kind, "batch_key": key,
                            "item_ids": [str(m["id"]) for m in members[start:start + size]]})
    batches = batches[:capacity]
    plan["batches"] = batches
    plan["requests"] = len(batches)
    planned = [i for b in batches for i in b["item_ids"]]
    if planned:
        checkpoint["cursor"] = planned[-1]
        _save(checkpoint, home, now)
    plan["reason"] = "ok"
    return plan
