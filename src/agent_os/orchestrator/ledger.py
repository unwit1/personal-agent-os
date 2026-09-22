"""Per-run efficiency telemetry: structured events, a readable transcript, and
a summary computed only from those events.

Files (gitignored runtime state, next to the run record):

    <home>/runs/<run_id>/telemetry.jsonl   one JSON object per event
    <home>/runs/<run_id>/transcript.log    the same events as plain English

Telemetry fails open. A write error never interrupts orchestration: the
ledger counts the failure, keeps the last error, and the run status shows a
warning instead.

Honesty rules enforced here:

* token counts keep the ``accuracy`` the provider gave them (``exact``,
  ``estimated``, ``unavailable``); the summary sums each accuracy separately
  and never folds estimates into measured totals;
* "avoided work" events carry an estimate only when the caller supplies a
  measured basis and a method; otherwise ``tokens_avoided_estimate`` is null
  and the event counts only the avoided call;
* the summary is derived from the event file alone, so it can be recomputed
  and reconciled after the fact.
"""

from __future__ import annotations

import json
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

from ..timestamps import utc_now_iso as now
from .store import FORBIDDEN_KEYS, redact


SCHEMA = "personal-agent/orchestrator-telemetry/v1"
EVENT_TYPES = frozenset(
    {
        "run_started",
        "roadmap_scanned",
        "task_selected",
        "handoff_loaded",
        "context_selected",
        "cache_hit",
        "skill_selected",
        "local_execution",
        "routing_decision",
        "model_selected",
        "model_started",
        "model_completed",
        "model_failed",
        "model_escalated",
        "retry",
        "fallback",
        "review_started",
        "review_completed",
        "tests_started",
        "tests_completed",
        "checkpoint_created",
        "commit_created",
        "tokens_recorded",
        "work_avoided",
        "loop_guard",
        "approval_required",
        "run_paused",
        "run_resumed",
        "run_completed",
        "run_failed",
        "note",
    }
)
EXPENSIVE_CLASSES = frozenset({"reasoning", "frontier"})
MAX_STRING = 300


class Ledger:
    def __init__(self, home_for: Any) -> None:
        """``home_for(run_id)`` returns the run directory."""
        self._dir = home_for
        self._lock = threading.Lock()
        self.failures: dict[str, int] = {}
        self.last_error: dict[str, str] = {}
        self.fail_writes = False  # tests flip this to prove telemetry fails open

    def paths(self, run_id: str) -> tuple[Path, Path]:
        base = Path(self._dir(run_id))
        return base / "telemetry.jsonl", base / "transcript.log"

    def emit(self, run_id: str, kind: str, node: str | None = None, /, **data: Any) -> dict[str, Any] | None:
        """Record one event. Returns the record, or ``None`` if it could not
        be written (the failure is counted, never raised)."""
        try:
            if kind not in EVENT_TYPES:
                raise ValueError(f"unknown telemetry event type {kind!r}")
            record = {
                "schema": SCHEMA,
                "at": now(),
                "seq": time.time_ns(),
                "run_id": run_id,
                "type": kind,
                "node": node,
                "data": _clean(data),
            }
            if self.fail_writes:
                raise OSError("telemetry writes disabled for testing")
            events_path, transcript_path = self.paths(run_id)
            with self._lock:
                events_path.parent.mkdir(parents=True, exist_ok=True)
                with events_path.open("a", encoding="utf-8", newline="") as handle:
                    handle.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")
                with transcript_path.open("a", encoding="utf-8", newline="") as handle:
                    handle.write(f"[{_clock(record['at'])}] {describe(record)}\n")
            return record
        except Exception as exc:  # telemetry must never break the run
            self.failures[run_id] = self.failures.get(run_id, 0) + 1
            self.last_error[run_id] = redact(f"{type(exc).__name__}: {exc}", 200)
            return None

    def warning(self, run_id: str) -> str | None:
        count = self.failures.get(run_id)
        if not count:
            return None
        return f"{count} telemetry record(s) could not be written ({self.last_error.get(run_id)}); the run itself is unaffected"

    def read(self, run_id: str) -> tuple[list[dict[str, Any]], int]:
        return read_events(self.paths(run_id)[0])


def read_events(path: Path) -> tuple[list[dict[str, Any]], int]:
    """Parse a telemetry file. Malformed lines are skipped and counted."""
    events: list[dict[str, Any]] = []
    malformed = 0
    try:
        lines = Path(path).read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        return [], 0
    except OSError:
        return [], 1
    for line in lines:
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            malformed += 1
            continue
        if not isinstance(record, dict) or record.get("schema") != SCHEMA or not isinstance(record.get("data"), dict):
            malformed += 1
            continue
        events.append(record)
    events.sort(key=lambda item: int(item.get("seq") or 0))
    return events, malformed


def _clean(value: Any, depth: int = 0) -> Any:
    if depth > 4:
        return None
    if isinstance(value, dict):
        bad = FORBIDDEN_KEYS.intersection(value) | {key for key in value if str(key).casefold() in {"prompt", "diff", "output", "stdout", "stderr"}}
        return {str(key): _clean(item, depth + 1) for key, item in value.items() if key not in bad}
    if isinstance(value, (list, tuple)):
        return [_clean(item, depth + 1) for item in list(value)[:50]]
    if isinstance(value, str):
        return redact(value, MAX_STRING)
    if value is None or isinstance(value, (bool, int, float)):
        return value
    return redact(str(value), MAX_STRING)


def _clock(stamp: str) -> str:
    try:
        return datetime.fromisoformat(stamp).astimezone().strftime("%H:%M:%S")
    except ValueError:
        return stamp[11:19]


# ---------------------------------------------------------------------------
# Plain English
# ---------------------------------------------------------------------------

PROVIDER_NAMES = {"claude-code": "Claude", "codex": "Codex"}
ROLE_WORDS = {"planner": "planning", "implementer": "implementation", "test_author": "writing tests", "reviewer": "review", "repairer": "fixing review findings"}


def provider_name(provider: str | None) -> str:
    if not provider:
        return "a local step"
    return PROVIDER_NAMES.get(provider, provider)


def _tokens(usage: dict[str, Any]) -> str:
    accuracy = usage.get("accuracy")
    if accuracy == "unavailable" or usage.get("input_tokens") is None:
        return "token use not reported by the provider"
    label = "" if accuracy == "exact" else f" ({accuracy})"
    return f"{usage.get('input_tokens', 0):,} in / {usage.get('output_tokens') or 0:,} out tokens{label}"


def describe(event: dict[str, Any]) -> str:
    """One beginner-friendly line for the activity feed and the transcript."""
    kind = event.get("type")
    data = event.get("data") or {}
    node = event.get("node")
    who = provider_name(data.get("provider"))
    role = ROLE_WORDS.get(str(data.get("role")), str(data.get("role") or "work"))
    if kind == "run_started":
        return f"Started {data.get('mode') or 'run'}" + (f" for {data['project']}" if data.get("project") else "")
    if kind == "roadmap_scanned":
        return f"Read the roadmap: {data.get('complete', 0)} of {data.get('total', 0)} stages complete"
    if kind == "task_selected":
        return f"Next task: {data.get('stage_id') or ''} {data.get('title') or ''}".strip()
    if kind == "handoff_loaded":
        return "Loaded the previous handoff" if data.get("found") else "No previous handoff found"
    if kind == "context_selected":
        reduction = data.get("reduction_pct")
        extra = f" ({reduction}% smaller than the full candidate context, estimated)" if reduction is not None else ""
        return f"Chose context for {node or 'the task'}: {data.get('selected_items', 0)} of {data.get('candidate_items', 0)} items{extra}"
    if kind == "cache_hit":
        return f"Reused an earlier result: {data.get('what') or 'cached result'}"
    if kind == "skill_selected":
        return f"Used reusable skill {data.get('skill')}"
    if kind == "local_execution":
        return f"Handled locally without a model: {data.get('what') or node or 'local step'}"
    if kind == "routing_decision":
        return f"{node}: chose {data.get('tier') or data.get('capability_class')} tier — {data.get('reason') or ''}".strip()
    if kind == "model_selected":
        return f"{who} selected for {role} ({data.get('model')}, effort {data.get('effort')})"
    if kind == "model_started":
        return f"{who} started {role}" + (f" on {node}" if node else "")
    if kind == "model_completed":
        return f"{who} finished {role}" + (f" on {node}" if node else "") + f" — {_tokens(data.get('usage') or {})}"
    if kind == "model_failed":
        return f"{who} could not finish {role}" + (f" on {node}" if node else "") + f" ({data.get('failure_kind')})"
    if kind == "model_escalated":
        return f"Moved {node} to a stronger setting ({data.get('to')}) because {data.get('reason') or 'validation failed'}"
    if kind == "retry":
        return f"Retrying {node} ({data.get('reason') or 'previous attempt failed'})"
    if kind == "fallback":
        return f"Switched {node} away from {provider_name(data.get('from_provider'))} ({data.get('reason')})"
    if kind == "review_started":
        return f"{who} started reviewing {data.get('subject') or node}"
    if kind == "review_completed":
        return f"Review of {data.get('subject') or node}: {data.get('verdict')}, {data.get('material_findings', 0)} finding(s) to fix"
    if kind == "tests_started":
        return f"Running tests for {node or 'the combined work'}"
    if kind == "tests_completed":
        counts = data.get("tests_run")
        detail = f"{data.get('tests_passed')} of {counts} tests passed" if counts is not None else ("tests passed" if data.get("passed") else "tests failed")
        return f"{detail} ({node or 'combined work'})"
    if kind == "checkpoint_created":
        return f"Saved progress for {node}"
    if kind == "commit_created":
        return f"Combined {node} into the run's result branch"
    if kind == "work_avoided":
        estimate = data.get("tokens_avoided_estimate")
        tail = f"; about {estimate:,} tokens (estimate)" if isinstance(estimate, int) else ""
        if not data.get("model_calls_avoided"):
            return f"Skipped repeat work: {data.get('reason')}{tail}"
        return f"Avoided {data.get('model_calls_avoided')} model call(s): {data.get('reason')}{tail}"
    if kind == "loop_guard":
        return f"Stopped a repeat: {data.get('reason')}"
    if kind == "approval_required":
        return f"Waiting for you: {data.get('title') or data.get('kind')}"
    if kind == "run_paused":
        return "Paused"
    if kind == "run_resumed":
        return "Resumed"
    if kind == "run_completed":
        return "Run complete"
    if kind == "run_failed":
        return f"Run stopped: {data.get('reason') or 'blocked'}"
    if kind == "tokens_recorded":
        return f"Recorded token use for {node}: {_tokens(data.get('usage') or {})}"
    return str(data.get("text") or kind)


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------


def summarize(events: Iterable[dict[str, Any]], malformed: int = 0) -> dict[str, Any]:
    """Efficiency summary computed only from telemetry events."""
    calls = {"total": 0, "failed": 0, "by_provider": {}, "by_class": {}, "expensive": 0, "roles": {}}
    tokens = {
        "exact": {"input": 0, "output": 0, "cache_read": 0, "cache_write": 0, "reasoning": 0, "calls": 0},
        "estimated": {"input": 0, "output": 0, "calls": 0},
        "unavailable_calls": 0,
        "synthetic": {"input": 0, "output": 0, "calls": 0},
        "provider_reported_cost_usd": 0.0,
    }
    prompt = {"calls": 0, "prompt_tokens_estimate": 0, "provider_input_tokens": 0}
    context = {"events": 0, "candidate_items": 0, "selected_items": 0, "candidate_tokens_estimate": 0, "selected_tokens_estimate": 0}
    avoided = {"events": 0, "model_calls": 0, "tokens_estimate": 0, "estimated_events": 0, "reasons": {}}
    counts = {key: 0 for key in ("local_operations", "cache_hits", "skill_reuse", "escalations", "retries", "fallbacks", "loop_guards", "checkpoints", "commits", "reviews", "approvals")}
    tests = {"runs": 0, "passed_runs": 0, "failed_runs": 0, "tests_run": 0, "tests_passed": 0, "tests_failed": 0, "reused": 0}
    routing: list[dict[str, Any]] = []
    first = last = None
    run_ids = set()
    total_events = 0
    for event in events:
        total_events += 1
        kind = event["type"]
        data = event.get("data") or {}
        run_ids.add(event.get("run_id"))
        first = first or event.get("at")
        last = event.get("at")
        if kind in {"model_completed", "model_failed"}:
            calls["total"] += 1
            if kind == "model_failed":
                calls["failed"] += 1
            provider = data.get("provider") or "unknown"
            capability = data.get("capability_class") or "unknown"
            calls["by_provider"][provider] = calls["by_provider"].get(provider, 0) + 1
            calls["by_class"][capability] = calls["by_class"].get(capability, 0) + 1
            calls["roles"][data.get("role") or "unknown"] = calls["roles"].get(data.get("role") or "unknown", 0) + 1
            if capability in EXPENSIVE_CLASSES:
                calls["expensive"] += 1
            usage = data.get("usage") or {}
            accuracy = usage.get("accuracy", "unavailable")
            if accuracy == "unavailable":
                tokens["unavailable_calls"] += 1
            elif usage.get("source") == "synthetic":
                tokens["synthetic"]["calls"] += 1
                tokens["synthetic"]["input"] += usage.get("input_tokens") or 0
                tokens["synthetic"]["output"] += usage.get("output_tokens") or 0
            elif accuracy == "exact":
                bucket = tokens["exact"]
                bucket["calls"] += 1
                bucket["input"] += usage.get("input_tokens") or 0
                bucket["output"] += usage.get("output_tokens") or 0
                bucket["cache_read"] += usage.get("cache_read_tokens") or 0
                bucket["cache_write"] += usage.get("cache_write_tokens") or 0
                bucket["reasoning"] += usage.get("reasoning_tokens") or 0
                if usage.get("cost_usd") is not None:
                    tokens["provider_reported_cost_usd"] = round(tokens["provider_reported_cost_usd"] + float(usage["cost_usd"]), 6)
            elif accuracy == "estimated":
                tokens["estimated"]["calls"] += 1
                tokens["estimated"]["input"] += usage.get("input_tokens") or 0
                tokens["estimated"]["output"] += usage.get("output_tokens") or 0
            if data.get("prompt_tokens_estimate") is not None:
                prompt["calls"] += 1
                prompt["prompt_tokens_estimate"] += int(data["prompt_tokens_estimate"])
                if accuracy == "exact" and usage.get("source") != "synthetic":
                    prompt["provider_input_tokens"] += usage.get("input_tokens") or 0
        elif kind == "context_selected":
            context["events"] += 1
            for key in ("candidate_items", "selected_items", "candidate_tokens_estimate", "selected_tokens_estimate"):
                context[key] += int(data.get(key) or 0)
        elif kind == "work_avoided":
            avoided["events"] += 1
            avoided["model_calls"] += int(data.get("model_calls_avoided") or 0)
            reason = str(data.get("category") or "other")
            avoided["reasons"][reason] = avoided["reasons"].get(reason, 0) + 1
            if isinstance(data.get("tokens_avoided_estimate"), int):
                avoided["estimated_events"] += 1
                avoided["tokens_estimate"] += data["tokens_avoided_estimate"]
        elif kind == "local_execution":
            counts["local_operations"] += 1
        elif kind == "cache_hit":
            counts["cache_hits"] += 1
            counts["local_operations"] += 1
        elif kind == "skill_selected":
            counts["skill_reuse"] += 1
        elif kind == "model_escalated":
            counts["escalations"] += 1
        elif kind == "retry":
            counts["retries"] += 1
        elif kind == "fallback":
            counts["fallbacks"] += 1
        elif kind == "loop_guard":
            counts["loop_guards"] += 1
        elif kind == "checkpoint_created":
            counts["checkpoints"] += 1
        elif kind == "commit_created":
            counts["commits"] += 1
        elif kind == "review_completed":
            counts["reviews"] += 1
        elif kind == "approval_required":
            counts["approvals"] += 1
        elif kind == "tests_completed":
            if data.get("reused"):
                tests["reused"] += 1
                continue
            tests["runs"] += 1
            tests["passed_runs" if data.get("passed") else "failed_runs"] += 1
            for key in ("tests_run", "tests_passed", "tests_failed"):
                tests[key] += int(data.get(key) or 0)
        elif kind == "routing_decision":
            routing.append({"node": event.get("node"), **{key: data.get(key) for key in ("role", "tier", "capability_class", "provider", "model", "effort", "reason")}})
    candidate = context["candidate_tokens_estimate"]
    selected = context["selected_tokens_estimate"]
    context["reduction_pct"] = round(100.0 * (candidate - selected) / candidate, 1) if candidate else None
    exploration = prompt["provider_input_tokens"] - prompt["prompt_tokens_estimate"] if prompt["provider_input_tokens"] else None
    return {
        "schema": "personal-agent/orchestrator-efficiency/v1",
        "run_ids": sorted(item for item in run_ids if item),
        "events": total_events,
        "malformed_lines": malformed,
        "first_event_at": first,
        "last_event_at": last,
        "model_calls": calls,
        "tokens": tokens,
        "prompt_vs_actual": {
            **prompt,
            "agent_overhead_tokens_estimate": exploration,
            "note": "prompt size is measured in characters and estimated in tokens; provider input is exact. "
            "The difference is the agent CLI's own system prompt, tool definitions and the files it chose to read.",
        },
        "context": context,
        "avoided": avoided,
        "counts": counts,
        "tests": tests,
        "routing": routing[-40:],
    }
