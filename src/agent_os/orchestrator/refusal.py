"""Refusal and non-answer telemetry (IMP-0015, Phase 0).

Refusals are first-class routing evidence: the roadmap asks to distinguish,
where evidence permits, *why* a worker did not do the task. ``classify`` is a
deterministic, conservative text classifier over a worker's answer when the
answer failed its contract (a passing answer is never a refusal):

* ``provider_policy`` -- the model declined on content/policy grounds;
* ``unsupported_capability`` -- it says it cannot do this kind of thing
  (no tool, no file access, no browsing, wrong modality);
* ``ambiguous_request`` -- it asked for clarification instead of answering;
* ``authorization`` -- it stopped for permission/authorization reasons;
* ``worker_failure`` -- none of the above: a genuine bad answer.

"Context collision" (irrelevant context derailing the worker) cannot be told
apart from text alone; it is left to the shadow comparison, which can see
whether a smaller contract succeeded.

``record`` appends one line per event to ``<home>/refusals.jsonl`` (local, not
Git); ``summary`` aggregates by provider, model and declared refusal profile
so routing can learn which models decline which task families. Nothing here
retries around a refusal: a benign task may be re-routed to another eligible
model or given a smaller *truthful* contract, never one that hides
safety-relevant facts (context_contract.ContextLaunderingError).
"""

from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

from ..timestamps import utc_now_iso

CATEGORIES = ("provider_policy", "unsupported_capability", "ambiguous_request", "authorization", "worker_failure")

_PATTERNS = [
    ("authorization", re.compile(r"\b(not authori[sz]ed|without (explicit )?(permission|authori[sz]ation)|need(s)? (your )?(permission|approval|authori[sz]ation))\b", re.I)),
    ("provider_policy", re.compile(r"(i (can(no|')t|won't|will not|am not able to|'m not able to) (help|assist|comply|provide|do that|fulfil)|"
                                   r"against (my|our|the) (guidelines|polic(y|ies)|usage policies)|i must decline|i'm sorry, but i can(no|')t|"
                                   r"not something i can (help|assist) with|violates? (the |our )?(content |usage )?polic)", re.I)),
    ("unsupported_capability", re.compile(r"(i (don't|do not) have (access to|the ability to)|i (can(no|')t|am unable to) (browse|access|open|read|run|execute|see) |"
                                          r"as a (text-based|language) model|no (tool|file system|internet) access)", re.I)),
    ("ambiguous_request", re.compile(r"(could you (please )?clarify|can you clarify|please (provide|specify) (more|which|the)|it'?s (not )?(unclear|ambiguous)|"
                                     r"what do you mean by)", re.I)),
]


def classify(text: str | None) -> str:
    """Category for a failed answer's text (see module docstring)."""
    head = (text or "")[:4000]
    for category, pattern in _PATTERNS:
        if pattern.search(head):
            return category
    return "worker_failure"


def refusals_path(home: Path) -> Path:
    return Path(home) / "refusals.jsonl"


def record(home: Path, *, category: str, task_family: str, selection: dict[str, Any], call_id: str | None = None,
           contract_digest: str | None = None, excerpt: str = "") -> dict[str, Any]:
    if category not in CATEGORIES:
        raise ValueError(f"unknown refusal category {category!r}")
    profile = selection.get("profile") or {}
    event = {"at": utc_now_iso(), "call_id": call_id, "task_family": task_family, "category": category,
             "provider": selection.get("provider"), "model": selection.get("model"),
             "deployment": profile.get("deployment"), "refusal_profile": profile.get("refusal_profile"),
             "contract_digest": contract_digest, "excerpt": " ".join(str(excerpt).split())[:160]}
    path = refusals_path(home)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + "\n")
    return event


def load(home: Path) -> list[dict[str, Any]]:
    path = refusals_path(home)
    if not path.exists():
        return []
    events = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            item = json.loads(line)
        except ValueError:
            continue
        if isinstance(item, dict):
            events.append(item)
    return events


def summary(home: Path) -> dict[str, Any]:
    by_route: dict[str, dict[str, Any]] = defaultdict(lambda: {"total": 0, "categories": defaultdict(int), "task_families": defaultdict(int)})
    events = load(home)
    for event in events:
        key = f"{event.get('provider')}/{event.get('model')}"
        bucket = by_route[key]
        bucket["refusal_profile"] = event.get("refusal_profile")
        bucket["total"] += 1
        bucket["categories"][event.get("category")] += 1
        bucket["task_families"][event.get("task_family")] += 1
    routes = {key: {**value, "categories": dict(value["categories"]), "task_families": dict(value["task_families"])} for key, value in by_route.items()}
    return {"events": len(events), "routes": dict(sorted(routes.items(), key=lambda item: -item[1]["total"]))}
