"""Cross-run usage report: ``agent-os orchestrate usage-report``.

Reads every run's ``telemetry.jsonl`` under the orchestrator home and
answers the P1.1 questions from provider-reported numbers only:

* which work consumes the most model usage (by role, tier, provider/model,
  run origin);
* where strong models are used, and for what;
* where retries, escalations, fallbacks and loop guards concentrate;
* how much provider input is the prompt Agent OS wrote versus agent-CLI
  overhead;
* how complete the data is (calls with exact vs missing token reports).

Synthetic (test/benchmark) calls are excluded from token totals and counted
separately. Nothing here is estimated except where a field says so.
"""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from .ledger import EXPENSIVE_CLASSES, read_events
from .store import orchestrator_home
from .usage import estimate_tokens

SCHEMA = "personal-agent/orchestrator-usage-report/v1"


def _bucket() -> dict[str, Any]:
    return {"calls": 0, "exact_calls": 0, "input": 0, "cache_read": 0, "cache_write": 0, "output": 0, "cost_usd": 0.0, "unreported_calls": 0}


def _add(bucket: dict[str, Any], usage: dict[str, Any]) -> None:
    bucket["calls"] += 1
    if usage.get("accuracy") != "exact":
        bucket["unreported_calls"] += 1
        return
    bucket["exact_calls"] += 1
    bucket["input"] += usage.get("input_tokens") or 0
    bucket["cache_read"] += usage.get("cache_read_tokens") or 0
    bucket["cache_write"] += usage.get("cache_write_tokens") or 0
    bucket["output"] += usage.get("output_tokens") or 0
    if usage.get("cost_usd") is not None:
        bucket["cost_usd"] = round(bucket["cost_usd"] + float(usage["cost_usd"]), 6)


def telemetry_files(home: Path | None = None) -> list[Path]:
    root = Path(home or orchestrator_home())
    return sorted(root.glob("runs/*/telemetry.jsonl")) + sorted(root.glob("benchmarks/*/state/*/orchestrator/runs/*/telemetry.jsonl"))


def build(files: Iterable[Path], since: str | None = None, include_benchmarks: bool = False) -> dict[str, Any]:
    by_role: dict[str, dict] = defaultdict(_bucket)
    by_tier: dict[str, dict] = defaultdict(_bucket)
    by_model: dict[str, dict] = defaultdict(_bucket)
    by_origin: dict[str, dict] = defaultdict(_bucket)
    totals = _bucket()
    synthetic_calls = 0
    expensive: dict[str, int] = defaultdict(int)
    friction: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    avoided: dict[str, int] = defaultdict(int)
    prompt = {"calls": 0, "prompt_tokens_estimate": 0, "provider_input": 0}
    runs: list[dict[str, Any]] = []
    malformed = 0
    for path in files:
        if not include_benchmarks and "benchmarks" in path.parts:
            continue
        events, bad = read_events(path)
        malformed += bad
        if since:
            events = [event for event in events if str(event.get("at") or "") >= since]
        if not events:
            continue
        run_id = events[0].get("run_id")
        origin = "roadmap" if any(event["type"] == "task_selected" for event in events) else "task"
        run_bucket = _bucket()
        for event in events:
            data = event.get("data") or {}
            kind = event["type"]
            if kind in {"model_completed", "model_failed"}:
                usage = data.get("usage") or {}
                if usage.get("source") == "synthetic":
                    synthetic_calls += 1
                    continue
                role = str(data.get("role") or "unknown")
                tier = str(data.get("capability_class") or "unknown")
                model = f"{data.get('provider')}/{data.get('model')}"
                for bucket in (totals, run_bucket, by_role[role], by_tier[tier], by_model[model], by_origin[origin]):
                    _add(bucket, usage)
                if tier in EXPENSIVE_CLASSES:
                    expensive[role] += 1
                if usage.get("accuracy") == "exact" and data.get("prompt_chars") is not None:
                    prompt["calls"] += 1
                    prompt["prompt_tokens_estimate"] += estimate_tokens(int(data["prompt_chars"]))
                    prompt["provider_input"] += usage.get("input_tokens") or 0
            elif kind in {"retry", "model_escalated", "fallback", "loop_guard"}:
                key = data.get("guard") or data.get("reason") or data.get("from_provider") or "?"
                friction[kind][str(key)[:60]] += 1
            elif kind == "work_avoided":
                avoided[str(data.get("category") or "other")] += int(data.get("model_calls_avoided") or 0)
        runs.append({"run_id": run_id, "origin": origin, "first_event": events[0].get("at"), **{key: run_bucket[key] for key in ("calls", "exact_calls", "input", "output", "cost_usd", "unreported_calls")}})
    overhead = prompt["provider_input"] - prompt["prompt_tokens_estimate"] if prompt["provider_input"] else None
    ranked = sorted(runs, key=lambda item: item["input"], reverse=True)
    return {
        "schema": SCHEMA,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "since": since,
        "runs_counted": len(runs),
        "malformed_lines": malformed,
        "totals": totals,
        "coverage": {
            "calls_with_exact_tokens": totals["exact_calls"],
            "calls_without_token_report": totals["unreported_calls"],
            "synthetic_calls_excluded": synthetic_calls,
        },
        "by_role": dict(by_role),
        "by_tier": dict(by_tier),
        "by_provider_model": dict(by_model),
        "by_origin": dict(by_origin),
        "expensive_tier_calls_by_role": dict(expensive),
        "friction": {kind: dict(values) for kind, values in friction.items()},
        "model_calls_avoided_by_category": dict(avoided),
        "prompt_vs_provider_input": {
            **prompt,
            "agent_overhead_tokens_estimate": overhead,
            "overhead_share_estimate": round(overhead / prompt["provider_input"], 3) if overhead is not None else None,
            "note": "prompt tokens are characters/4 (estimated); provider input is exact",
        },
        "top_runs_by_input": ranked[:10],
    }


def report(home: Path | None = None, since: str | None = None, include_benchmarks: bool = False, out: Path | None = None) -> dict[str, Any]:
    result = build(telemetry_files(home), since, include_benchmarks)
    target = Path(out) if out else Path(home or orchestrator_home()) / "reports" / f"usage-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, indent=2), encoding="utf-8")
    result["file"] = str(target)
    return result
