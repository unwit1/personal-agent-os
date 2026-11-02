"""Deterministic offline before/after comparison for the IMP-0018 `shared_prefix` flag.

Builds every prompt of one synthetic run with the flag off and on, models provider prompt
caching from the longest common character prefix with any earlier prompt, writes each
variant as synthetic telemetry and measures it with the read-only context_economy harness.
No network, no model calls, no clock in the figures."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
from typing import Any

from . import context_anatomy, context_economy
from .ledger import SCHEMA as TELEMETRY_SCHEMA

HARNESS_TOKENS = 6000  # fixed provider-side overhead per call (system prompt, tool schemas)
SOURCE = "fixture"  # anything but "synthetic", which context_economy excludes
RUN_IDS = {"before": "run-20261001T000000Z-000001", "after": "run-20261001T000001Z-000002"}
GOAL = "Add a retry budget to the job scheduler and document it"
PLAN = {
    "status": "done",
    "summary": "Planned 6 tasks",
    "tasks": [
        {"id": "budget-core", "goal": "Implement the retry budget", "role": "implementer", "scope": ["src/scheduler/budget.py"]},
        {"id": "budget-tests", "goal": "Test the retry budget", "role": "test_author", "scope": ["tests/test_budget.py"]},
        {"id": "queue-hook", "goal": "Consult the budget before requeue", "role": "implementer", "scope": ["src/scheduler/queue.py"]},
        {"id": "queue-tests", "goal": "Test the requeue hook", "role": "test_author", "scope": ["tests/test_queue.py"]},
        {"id": "config-key", "goal": "Add the budget config key", "role": "implementer", "scope": ["src/scheduler/config.py"]},
        {"id": "docs", "goal": "Document the retry budget", "role": "implementer", "scope": ["docs/scheduler.md"]},
    ],
}


def _common_prefix_chars(left: str, right: str) -> int:
    size = min(len(left), len(right))
    index = 0
    while index < size and left[index] == right[index]:
        index += 1
    return index


def _model_calls(calls: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Deterministic provider usage per call: cache reads cover the longest shared prefix
    with any earlier prompt, plus the harness overhead after the first call."""
    out: list[dict[str, Any]] = []
    seen: list[str] = []
    for call in calls:
        prompt = call["prompt"]
        prompt_tokens = context_anatomy.tokens(prompt)
        total = prompt_tokens + HARNESS_TOKENS
        shared = max((_common_prefix_chars(prompt, earlier) for earlier in seen), default=0)
        cache_read = context_anatomy.tokens(prompt[:shared]) + HARNESS_TOKENS if seen else 0
        cache_read = min(cache_read, total)
        out.append({"role": call["role"], "node": call["node"], "prompt_tokens": prompt_tokens, "input": total, "cache_read": cache_read})
        seen.append(prompt)
    return out


def _write_run(out_dir: Path, run_id: str, modelled: list[dict[str, Any]]) -> Path:
    run_dir = Path(out_dir) / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    lines = [{"schema": TELEMETRY_SCHEMA, "at": "2026-10-01T00:00:00+00:00", "seq": 1, "run_id": run_id, "type": "run_started", "node": None, "data": {}}]
    for seq, call in enumerate(modelled, 2):
        usage = {"accuracy": "exact", "source": SOURCE, "input_tokens": call["input"], "uncached_input_tokens": call["input"] - call["cache_read"],
                 "cache_read_tokens": call["cache_read"], "cache_write_tokens": 0, "output_tokens": 0, "cost_usd": None}
        lines.append({"schema": TELEMETRY_SCHEMA, "at": "2026-10-01T00:00:00+00:00", "seq": seq, "run_id": run_id, "type": "model_completed",
                      "node": call["node"], "data": {"role": call["role"], "capability_class": "standard", "provider": SOURCE, "model": "fixture", "attempt": 1,
                                                     "prompt_chars": call["prompt_tokens"] * 4, "prompt_tokens_estimate": call["prompt_tokens"], "usage": usage}})
    (run_dir / "telemetry.jsonl").write_text("\n".join(json.dumps(line, sort_keys=True) for line in lines) + "\n", encoding="utf-8")
    return run_dir


def _variant(repo: Path, out_dir: Path, name: str, shared: bool) -> dict[str, Any]:
    calls = context_anatomy.build_run(GOAL, PLAN, repo, project=None, policy={"shared_prefix": shared, "planner_repo_map": False})
    modelled = _model_calls(calls)
    run_dir = _write_run(out_dir, RUN_IDS[name], modelled)
    report = context_economy.build([run_dir])
    workers = [c for c in modelled if c["role"] != "planner"]
    total_input = sum(c["input"] for c in modelled)
    cache_read = sum(c["cache_read"] for c in modelled)
    worker_input = sum(c["input"] for c in workers)
    worker_cache = sum(c["cache_read"] for c in workers)
    return {
        "shared_prefix": shared,
        "calls": len(modelled),
        "total_input_tokens": total_input,
        "cache_read_tokens": cache_read,
        "uncached_input_tokens": total_input - cache_read,
        "cache_read_share": round(cache_read / total_input, 4) if total_input else None,
        "worker_input_tokens": worker_input,
        "worker_uncached_input_tokens": worker_input - worker_cache,
        "worker_cache_read_share": round(worker_cache / worker_input, 4) if worker_input else None,
        "duplicated_fixed_overhead": report["fanout"]["totals"]["duplicated_fixed_overhead"],
        "eligible_calls": report["coverage"]["eligible_calls"],
        "economy": {"amplification": report["amplification"]["all"], "fanout": report["fanout"]["totals"]},
    }


def compare(repo: Path, out_dir: Path) -> dict[str, Any]:
    repo, out_dir = Path(repo), Path(out_dir)
    before = _variant(repo, out_dir, "before", False)
    after = _variant(repo, out_dir, "after", True)
    delta = {
        "total_input_tokens": after["total_input_tokens"] - before["total_input_tokens"],
        "uncached_input_tokens": after["uncached_input_tokens"] - before["uncached_input_tokens"],
        "worker_uncached_input_tokens": after["worker_uncached_input_tokens"] - before["worker_uncached_input_tokens"],
        "cache_read_share": round(after["cache_read_share"] - before["cache_read_share"], 4),
        "duplicated_fixed_overhead": after["duplicated_fixed_overhead"] - before["duplicated_fixed_overhead"],
    }
    return {"harness_tokens": HARNESS_TOKENS, "before": before, "after": after, "delta": delta}


def main() -> int:
    repo = Path(__file__).resolve().parents[3]
    with tempfile.TemporaryDirectory() as tmp:
        print(json.dumps(compare(repo, Path(tmp)), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
