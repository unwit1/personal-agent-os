"""Context-economy measurement: how provider input behaves across calls.

IMP-0018 Phase 0. Reads each run's ``telemetry.jsonl`` and the *sizes* of the
files under ``workers/<node>-<attempt>/`` and reports four metrics: per-worker
input amplification, long-session context growth, worker fan-out cost and
checkpoint-resume overhead. Design: docs/orchestrator-os/self-audit/context-economy.md.

Deterministic and offline: no network, no model calls, no randomness. The
output holds aggregates and a closed set of labels only. Node ids, worker
directory names, prompts and transcripts never enter it, and worker files are
never opened (``os.stat`` sizes only). ``generated_at`` is the only
nondeterministic field.
"""

from __future__ import annotations

import json
import math
import os
import re
import statistics
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from .ledger import read_events
from .store import orchestrator_home
from .usage import ESTIMATE_METHOD, estimate_tokens

SCHEMA = "personal-agent/orchestrator-context-economy/v1"
PRIVACY_RULE = "max80-no-whitespace"
RUN_ID = re.compile(r"^run-\d{8}T\d{6}Z-[0-9a-f]{6}$")
MODEL_EVENTS = frozenset({"model_completed", "model_failed"})
FILE_KEYS = {"prompt.md": "prompt", "stdout.log": "stdout", "stderr.log": "stderr", "last-message.md": "last_message"}
BUCKETS = ("1", "2-3", "4+")
PLANNER = "planner"


# -- small helpers -----------------------------------------------------------


def _violates(text: str) -> bool:
    return len(text) > 80 or re.search(r"\s", text) is not None


def _int(value: Any) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    return value


def _ratio(numerator: float, denominator: float) -> float | None:
    return round(numerator / denominator, 4) if denominator else None


def _stats(values: list[float]) -> dict[str, Any]:
    n = len(values)
    if not n:
        return {"count": 0, "median": None, "p90": None, "min": None, "max": None}
    ordered = sorted(values)
    fix = lambda v: round(v, 4) if isinstance(v, float) else v  # noqa: E731
    return {
        "count": n,
        "median": fix(statistics.median(ordered)),
        "p90": fix(ordered[math.ceil(0.9 * n) - 1]),
        "min": fix(ordered[0]),
        "max": fix(ordered[-1]),
    }


def _bucket_of(count: int) -> str:
    return "1" if count == 1 else "2-3" if count <= 3 else "4+"


def _exponent(cumulative: list[int]) -> float | None:
    points = [(math.log(j), math.log(c)) for j, c in enumerate(cumulative, 1) if c > 0]
    if len(points) < 3:
        return None
    mx = sum(x for x, _ in points) / len(points)
    my = sum(y for _, y in points) / len(points)
    var = sum((x - mx) ** 2 for x, _ in points)
    return round(sum((x - mx) * (y - my) for x, y in points) / var, 4) if var else None


class _Labels:
    """Sanitizes telemetry labels so one odd string cannot block a report."""

    def __init__(self) -> None:
        self.sanitized = 0
        self.seen: set[str] = set()

    def __call__(self, value: Any) -> str:
        label = "unknown" if value is None or value == "" else str(value)
        if _violates(label):
            self.sanitized += 1
            label = "other"
        self.seen.add(label)
        return label


# -- reading one run ---------------------------------------------------------


def _classify(usage: dict[str, Any]) -> tuple[str, int | None]:
    """Return (category, provider input). Category is eligible or an exclusion."""
    if usage.get("source") == "synthetic":
        return "synthetic", None
    accuracy = usage.get("accuracy")
    if accuracy == "estimated":
        return "estimated", None
    if accuracy != "exact":
        return "unavailable", None
    total = _int(usage.get("input_tokens"))
    cache = (_int(usage.get("cache_read_tokens")) or 0) + (_int(usage.get("cache_write_tokens")) or 0)
    if total is None:
        parts = [_int(usage.get(key)) for key in ("uncached_input_tokens", "cache_read_tokens", "cache_write_tokens")]
        total = sum(p or 0 for p in parts) if any(p is not None for p in parts) else None
    if total is None or total < 0 or cache > total:
        return "inconsistent", None
    return "eligible", total


def _read_run(run_dir: Path, labels: _Labels, cov: dict[str, Any], forbidden: set[str]) -> dict[str, Any]:
    events, bad = read_events(run_dir / "telemetry.jsonl")
    cov["malformed_lines"] += bad
    cov["events"] += len(events)
    run: dict[str, Any] = {"calls": [], "checkpoints": [], "resumes": [], "pauses": 0, "started": False,
                           "retries": 0, "escalations": 0, "fallbacks": 0, "workers": []}
    for event in events:
        kind, data, seq = event.get("type"), event.get("data") or {}, int(event.get("seq") or 0)
        node = event.get("node")
        node = str(node) if node else None
        if node:
            forbidden.add(node)
        if kind in MODEL_EVENTS:
            usage = data.get("usage") if isinstance(data.get("usage"), dict) else {}
            category, tokens_in = _classify(usage)
            cov["calls"] += 1
            if category == "synthetic":
                cov["synthetic_calls_excluded"] += 1
            elif usage.get("accuracy") == "exact":
                cov["exact_calls"] += 1
            else:
                cov["unreported_calls"] += 1
            if category != "eligible":
                cov["excluded"][category] += 1
            else:
                cov["eligible_calls"] += 1
            prompt = _int(data.get("prompt_tokens_estimate"))
            if prompt is None and _int(data.get("prompt_chars")) is not None:
                prompt = estimate_tokens(data["prompt_chars"])
            if category == "eligible" and not (prompt and prompt > 0):
                cov["calls_without_prompt_estimate"] += 1
            provider, model = labels(data.get("provider")), labels(data.get("model"))
            run["calls"].append({
                "node": node, "seq": seq, "attempt": _int(data.get("attempt")),
                "role": labels(data.get("role")), "cls": labels(data.get("capability_class")),
                "provider": provider, "model": model, "category": category,
                "input": tokens_in, "output": _int(usage.get("output_tokens")) or 0,
                "cache_read": _int(usage.get("cache_read_tokens")) or 0,
                "prompt": prompt if prompt and prompt > 0 else None,
            })
        elif kind == "run_started":
            run["started"] = True
        elif kind == "run_paused":
            run["pauses"] += 1
        elif kind == "run_resumed":
            run["resumes"].append(seq)
        elif kind == "checkpoint_created":
            run["checkpoints"].append((node, seq))
        elif kind in {"retry", "model_escalated", "fallback"}:
            key = {"retry": "retries", "model_escalated": "escalations", "fallback": "fallbacks"}[kind]
            run[key] += 1
    run["eligible"] = [c for c in run["calls"] if c["category"] == "eligible"]
    run["nodes"] = _node_series(run["eligible"])
    _read_workers(run_dir, run, forbidden)
    return run


def _node_series(eligible: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    nodes: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for call in eligible:
        if call["node"]:
            nodes[call["node"]].append(call)
    for series in nodes.values():
        series.sort(key=lambda c: (c["attempt"] or 0, c["seq"]))
    return nodes


def _read_workers(run_dir: Path, run: dict[str, Any], forbidden: set[str]) -> None:
    """Record file sizes per (node, attempt) via stat only. Files are never opened."""
    root = run_dir / "workers"
    if not root.is_dir():
        return
    by_key = {(c["node"], c["attempt"]): c for c in sorted(run["calls"], key=lambda c: c["seq"])}
    for entry in sorted(os.scandir(root), key=lambda e: e.name):
        if not entry.is_dir():
            continue
        forbidden.add(entry.name)
        node, _, suffix = entry.name.rpartition("-")
        if not node or not suffix.isdigit():
            run["workers"].append(None)
            continue
        forbidden.add(node)
        call = by_key.get((node, int(suffix)))
        sizes: dict[str, list[int]] = defaultdict(list)
        for item in sorted(os.scandir(entry.path), key=lambda e: e.name):
            if item.is_file():
                sizes[FILE_KEYS.get(item.name, "other")].append(item.stat().st_size)
        run["workers"].append({"role": call["role"] if call else "unknown", "prompt": call["prompt"] if call else None, "sizes": sizes})


# -- metrics -----------------------------------------------------------------


def _group(calls: list[dict[str, Any]]) -> dict[str, Any]:
    defined = [c for c in calls if c["prompt"]]
    positive = [c for c in calls if c["input"] > 0]
    sum_input, sum_output = sum(c["input"] for c in calls), sum(c["output"] for c in calls)
    return {
        "count": len(calls),
        "sum_input": sum_input,
        "sum_prompt_estimate": sum(c["prompt"] for c in defined),
        "sum_output": sum_output,
        "pooled_amplification": _ratio(sum(c["input"] for c in defined), sum(c["prompt"] for c in defined)),
        "pooled_output_ratio": _ratio(sum_output, sum_input),
        "amplification": _stats([c["input"] / c["prompt"] for c in defined]),
        "output_ratio": _stats([c["output"] / c["input"] for c in positive]),
        "cache_read_share": _stats([c["cache_read"] / c["input"] for c in positive]),
    }


def _amplification(runs: list[dict[str, Any]]) -> dict[str, Any]:
    eligible = [c for run in runs for c in run["eligible"]]
    by_role: dict[str, list] = defaultdict(list)
    by_class: dict[str, list] = defaultdict(list)
    for call in eligible:
        by_role[call["role"]].append(call)
        by_class[call["cls"]].append(call)
    return {
        "all": _group(eligible),
        "by_role": {k: _group(v) for k, v in sorted(by_role.items())},
        "by_capability_class": {k: _group(v) for k, v in sorted(by_class.items())},
    }


def _growth(runs: list[tuple[str, dict[str, Any]]]) -> dict[str, Any]:
    acc = {b: {"nodes": 0, "calls": 0, "sum_input": 0, "first": [], "last": [], "growth": []} for b in BUCKETS}
    by_run: dict[str, Any] = {}
    for run_id, run in runs:
        node_bucket = {n: _bucket_of(len(s)) for n, s in run["nodes"].items()}
        per_bucket = {**{b: 0 for b in BUCKETS}, "none": 0}
        for node, series in run["nodes"].items():
            slot = acc[node_bucket[node]]
            first, last = series[0]["input"], series[-1]["input"]
            slot["nodes"] += 1
            slot["calls"] += len(series)
            slot["sum_input"] += sum(c["input"] for c in series)
            slot["first"].append(first)
            slot["last"].append(last)
            if len(series) >= 2 and first > 0:
                slot["growth"].append(last / first)
        cumulative, total = [], 0
        for call in sorted(run["eligible"], key=lambda c: c["seq"]):
            total += call["input"]
            cumulative.append(total)
            per_bucket[node_bucket.get(call["node"], "none") if call["node"] else "none"] += call["input"]
        by_run[run_id] = {"calls": len(cumulative), "cumulative_input": cumulative,
                          "growth_exponent": _exponent(cumulative), "input_by_node_bucket": per_bucket}
    buckets = {b: {"nodes": a["nodes"], "calls": a["calls"], "sum_input": a["sum_input"],
                   "first_input": _stats(a["first"]), "last_input": _stats(a["last"]),
                   "growth_ratio": _stats(a["growth"])} for b, a in acc.items()}
    return {"by_node_bucket": buckets, "by_run": by_run}


def _fanout_raw(run: dict[str, Any]) -> dict[str, Any]:
    roles: dict[str, set] = defaultdict(set)
    for call in run["calls"]:
        if call["role"] != PLANNER and call["node"]:
            roles[call["role"]].add(call["node"])
    workers = [c for c in run["eligible"] if c["role"] != PLANNER]
    deltas = [c["input"] - c["prompt"] for c in workers if c["prompt"]]
    return {
        "worker_nodes": {r: len(n) for r, n in sorted(roles.items())},
        "planner_input": sum(c["input"] for c in run["eligible"] if c["role"] == PLANNER),
        "worker_input": sum(c["input"] for c in workers),
        "duplicated_fixed_overhead": sum(deltas),
        "deltas": deltas,
        "repeat_attempt_input": sum(c["input"] for s in run["nodes"].values() for c in s[1:]),
        "retries": run["retries"], "escalations": run["escalations"], "fallbacks": run["fallbacks"],
    }


def _fanout_view(raw: dict[str, Any]) -> dict[str, Any]:
    return {
        "worker_nodes": raw["worker_nodes"],
        "worker_nodes_total": sum(raw["worker_nodes"].values()),
        "planner_input": raw["planner_input"],
        "worker_input": raw["worker_input"],
        "fanout_input_ratio": _ratio(raw["worker_input"], raw["planner_input"]),
        "duplicated_fixed_overhead": raw["duplicated_fixed_overhead"],
        "overhead_share": _ratio(raw["duplicated_fixed_overhead"], raw["worker_input"]),
        "overhead_per_worker_call": _stats(raw["deltas"]),
        "negative_overhead_calls": sum(1 for d in raw["deltas"] if d < 0),
        "repeat_attempt_input": raw["repeat_attempt_input"],
        "retries": raw["retries"], "escalations": raw["escalations"], "fallbacks": raw["fallbacks"],
    }


def _fanout(runs: list[tuple[str, dict[str, Any]]]) -> dict[str, Any]:
    raws = [(run_id, _fanout_raw(run)) for run_id, run in runs]
    total: dict[str, Any] = {"worker_nodes": defaultdict(int), "deltas": []}
    for key in ("planner_input", "worker_input", "duplicated_fixed_overhead", "repeat_attempt_input", "retries", "escalations", "fallbacks"):
        total[key] = sum(raw[key] for _, raw in raws)
    for _, raw in raws:
        total["deltas"].extend(raw["deltas"])
        for role, count in raw["worker_nodes"].items():
            total["worker_nodes"][role] += count
    total["worker_nodes"] = dict(sorted(total["worker_nodes"].items()))
    return {"by_run": {run_id: _fanout_view(raw) for run_id, raw in raws}, "totals": _fanout_view(total)}


def _resume_run(run: dict[str, Any]) -> dict[str, Any]:
    starts = sorted(run["resumes"])
    bounds = starts[1:] + [math.inf]
    resume_input = first_input = cold = warm_nodes = 0
    for start, end in zip(starts, bounds):
        seen_first: set[str] = set()
        warm_set: set[str] = set()
        for call in sorted(run["eligible"], key=lambda c: c["seq"]):
            if not start < call["seq"] < end:
                continue
            node = call["node"]
            warm = (node is not None and (any(n == node and s < start for n, s in run["checkpoints"])
                                          or any(c["node"] == node and c["seq"] < start for c in run["calls"]))) \
                or (call["attempt"] or 0) > 1
            if not warm:
                cold += call["input"]
                continue
            resume_input += call["input"]
            if node is None or node not in seen_first:
                first_input += call["input"]
                if node is not None:
                    seen_first.add(node)
            if node is not None:
                warm_set.add(node)
        warm_nodes += len(warm_set)
    return {"resumes": len(starts), "pauses": run["pauses"], "checkpoints": len(run["checkpoints"]), "warm_nodes": warm_nodes,
            "run_input": sum(c["input"] for c in run["eligible"]), "resume_overhead_input": resume_input,
            "resume_first_input": first_input, "cold_resume_input": cold}


def _resume_view(raw: dict[str, Any]) -> dict[str, Any]:
    return {**raw, "resume_share": _ratio(raw["resume_overhead_input"], raw["run_input"]),
            "resume_first_share": _ratio(raw["resume_first_input"], raw["run_input"])}


def _resume(runs: list[tuple[str, dict[str, Any]]]) -> dict[str, Any]:
    raws = {run_id: _resume_run(run) for run_id, run in runs if run["resumes"]}
    keys = ("resumes", "pauses", "checkpoints", "warm_nodes", "run_input", "resume_overhead_input", "resume_first_input", "cold_resume_input")
    total = {k: sum(r[k] for r in raws.values()) for k in keys}
    return {"by_run": {k: _resume_view(v) for k, v in raws.items()}, "totals": _resume_view(total)}


def _worker_files(runs: list[dict[str, Any]]) -> dict[str, Any]:
    sizes: dict[str, dict[str, list[int]]] = defaultdict(lambda: defaultdict(list))
    per_token: list[float] = []
    for run in runs:
        for worker in (w for w in run["workers"] if w):
            for key, values in worker["sizes"].items():
                sizes[worker["role"]][key].extend(values)
            if worker["prompt"] and worker["sizes"].get("prompt"):
                per_token.append(worker["sizes"]["prompt"][0] / worker["prompt"])
    return {
        "by_role": {role: {key: {"sum_bytes": sum(v), "size": _stats(v)} for key, v in sorted(files.items())}
                    for role, files in sorted(sizes.items())},
        "prompt_bytes_per_estimated_token": _stats(per_token),
    }


# -- public API --------------------------------------------------------------


def build(run_dirs: Iterable[Path]) -> dict[str, Any]:
    labels = _Labels()
    forbidden: set[str] = set()
    cov: dict[str, Any] = {
        "runs": 0, "malformed_runs": 0, "runs_without_run_started": 0, "events": 0, "malformed_lines": 0,
        "calls": 0, "exact_calls": 0, "unreported_calls": 0, "synthetic_calls_excluded": 0,
        "eligible_calls": 0, "calls_without_prompt_estimate": 0,
        "excluded": {"estimated": 0, "unavailable": 0, "synthetic": 0, "inconsistent": 0},
        "sanitized_labels": 0, "unparsed_worker_dirs": 0,
    }
    runs: list[tuple[str, dict[str, Any]]] = []
    for run_dir in sorted(Path(p) for p in run_dirs):
        if not RUN_ID.match(run_dir.name):
            cov["malformed_runs"] += 1
            continue
        run = _read_run(run_dir, labels, cov, forbidden)
        cov["runs"] += 1
        cov["runs_without_run_started"] += 0 if run["started"] else 1
        cov["unparsed_worker_dirs"] += sum(1 for w in run["workers"] if w is None)
        runs.append((run_dir.name, run))
    cov["sanitized_labels"] = labels.sanitized
    bodies = [run for _, run in runs]
    models: dict[str, set[str]] = defaultdict(set)
    for run in bodies:
        for call in run["calls"]:
            if call["category"] != "synthetic":
                models[call["provider"]].add(call["model"])
    result = {
        "schema": SCHEMA,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "estimate_method": ESTIMATE_METHOD,
        "runs": [run_id for run_id, _ in runs],
        "coverage": cov,
        "amplification": _amplification(bodies),
        "session_growth": _growth(runs),
        "fanout": _fanout(runs),
        "resume": _resume(runs),
        "worker_files": _worker_files(bodies),
        "provider_models": {p: sorted(m) for p, m in sorted(models.items())},
        "privacy": {"rule": PRIVACY_RULE, "strings_checked": 0, "passed": False},
    }
    checked = _scan(result, forbidden - labels.seen)
    result["privacy"].update({"strings_checked": checked, "passed": True})
    return result


def assert_aggregate_only(report: dict[str, Any], forbidden: Iterable[str] = ()) -> None:
    """Raise ValueError if any key or string value breaks the privacy rule.

    A string violates it when longer than 80 characters, containing whitespace,
    or equal to a member of ``forbidden`` (node ids, worker dir names). The error
    names the JSON path, never the offending text.
    """
    _scan(report, forbidden)


def _scan(report: dict[str, Any], forbidden: Iterable[str]) -> int:
    """Walk the report; return the number of strings checked."""
    banned = set(forbidden)
    count = 0

    def walk(item: Any, path: str) -> None:
        nonlocal count
        if isinstance(item, dict):
            for index, (key, value) in enumerate(item.items()):
                here = f"{path}.#{index}"
                if not isinstance(key, str):
                    raise ValueError(f"non-string key at {here}")
                count += 1
                if _violates(key) or key in banned:
                    raise ValueError(f"privacy rule violated by key at {here}")
                walk(value, f"{path}.{key}")
        elif isinstance(item, (list, tuple)):
            for index, value in enumerate(item):
                walk(value, f"{path}[{index}]")
        elif isinstance(item, str):
            count += 1
            if _violates(item) or item in banned:
                raise ValueError(f"privacy rule violated by value at {path}")

    walk(report, "$")
    return count


def report(home: Path | None = None, out: Path | None = None) -> dict[str, Any]:
    root = Path(home or orchestrator_home())
    run_dirs = [p for p in sorted((root / "runs").glob("*")) if p.is_dir()] if (root / "runs").is_dir() else []
    result = build(run_dirs)
    assert_aggregate_only(result)
    if out:
        target = Path(out)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    return result
