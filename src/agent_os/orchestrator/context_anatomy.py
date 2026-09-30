"""Context anatomy: what every prompt in a run spends its tokens on (IMP-0018 Phase 0).

Deterministic, no model call. Given a goal and a plan (e.g. a real foreman
plan from ``foreman eval``), build every prompt the engine would send --
planner, one implementer/test author per task, one reviewer per task (with a
synthetic diff of the task's scope), one repairer -- exactly as prompts.py
builds them, then report:

* tokens per prompt section (goal, rules, map, project context, contract,
  siblings, diff, ...), estimated as chars / 3.5;
* per-call harness overhead (the adapter's measured context_overhead_tokens);
* **fan-out duplication**: prompt text repeated verbatim across the run's
  worker prompts (the same parent context copied into every worker);
* **context amplification**: total input tokens processed by the run's calls
  divided by the unique tokens they contain (IMP-0018's core metric).

Estimates are labelled as estimates; they rank waste, they do not bill it.
"""

from __future__ import annotations

import copy
import re
from collections import Counter
from pathlib import Path
from typing import Any

from . import planner, prompts
from .model import merge_policy

CHARS_PER_TOKEN = 3.5
# Section markers in prompts.py output, in the order they appear.
MARKERS = [
    ("header", r"^You are the "),
    ("goal", r"^Overall goal:"),
    ("assignment", r"^Your assignment"),
    ("worker_rules", r"^Rules:$"),
    ("reviewer_rules", r"^You are an independent reviewer"),
    ("siblings", r"^Other tasks in this run cover"),
    ("diff", r"^Change under review:"),
    ("findings", r"^Address these review findings"),
    ("planner_rules", r"^Do not edit files\."),
    ("repo_map", r"^Repository layout"),
    ("planner_rules_2", r"^Then break the goal into the"),
    ("project_context", r"^Project context:"),
    ("contract", r"^When you finish, end your reply"),
]


def tokens(text: str) -> int:
    return int(round(len(text) / CHARS_PER_TOKEN))


def sections(prompt: str) -> dict[str, int]:
    """Token estimate per section (a section runs until the next marker)."""
    lines = prompt.splitlines()
    current, out = "header", Counter()
    for line in lines:
        for name, pattern in MARKERS:
            if re.match(pattern, line):
                current = name
                break
        out[current] += tokens(line + "\n")
    return dict(out)


def _synthetic_diff(scope: list[str], lines_per_file: int = 40) -> str:
    out = []
    for path in scope[:3]:
        out += [f"diff --git a/{path} b/{path}", f"--- a/{path}", f"+++ b/{path}", "@@ -1,3 +1,{n} @@".format(n=lines_per_file)]
        out += [f"+    line {i} of the change in {path.split('/')[-1]}" for i in range(lines_per_file)]
    return "\n".join(out)


def build_run(goal: str, plan: dict[str, Any], repo: Path, *, project: str | None = None, policy: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """Every prompt of one run: [{"role", "node", "prompt"}]."""
    from .repomap import build as build_map

    policy = merge_policy({"planning": "auto", **(policy or {})})
    nodes = planner.planner_plan(goal, policy["planner_capability_class"], policy["planner_effort"])
    record = {"run_id": "anatomy", "goal": goal, "project": project, "policy": policy, "nodes": nodes, "order": list(nodes)}
    calls = []
    repo_map = build_map(repo, goal)["text"] if policy.get("planner_repo_map") else None
    calls.append({"role": "planner", "node": "plan", "prompt": prompts.build_measured(record, nodes["plan"], repo_map=repo_map, cwd=str(repo))[0]})
    added, _ = planner.expand(nodes, "plan", copy.deepcopy(plan), policy["max_planned_tasks"], approved_commands=[], project_commands=[])
    record["order"] = list(nodes)
    for node_id in added:
        node = nodes[node_id]
        calls.append({"role": node["role"], "node": node_id, "prompt": prompts.build_measured(record, node, cwd=str(repo))[0]})
        reviewer = {**node, "id": f"{node_id}.review", "role": "reviewer", "subject": node_id}
        calls.append({"role": "reviewer", "node": reviewer["id"], "prompt": prompts.build_measured(record, reviewer, diff=_synthetic_diff(node["scope"]), cwd=str(repo))[0]})
    if added:
        first = nodes[added[0]]
        repairer = {**first, "id": f"{first['id']}.repair", "role": "repairer"}
        findings = [{"id": "R1-1", "severity": "medium", "path": (first["scope"] or ["?"])[0], "summary": "example finding", "recommended_action": "fix it"}]
        calls.append({"role": "repairer", "node": repairer["id"], "prompt": prompts.build_measured(record, repairer, findings=findings, cwd=str(repo))[0]})
    return calls


def run_calls(run_dir: Path) -> list[dict[str, Any]]:
    """The prompts a finished run actually sent: workers/<node>-<attempt>/prompt.md,
    roles from the run record."""
    import json

    run_dir = Path(run_dir)
    try:
        record = json.loads((run_dir / "state.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        record = {"nodes": {}}
    nodes = record.get("nodes") or {}
    calls = []
    for worker in sorted((run_dir / "workers").glob("*/prompt.md")):
        node_id = worker.parent.name.rsplit("-", 1)[0]
        role = (nodes.get(node_id) or {}).get("role") or "unknown"
        calls.append({"role": role, "node": worker.parent.name, "prompt": worker.read_text(encoding="utf-8", errors="replace")})
    return calls


def analyze_run(run_dir: Path, harness_tokens: int = 6000) -> dict[str, Any]:
    """IMP-0018 Phase 0 metrics for a real run from its saved prompts."""
    calls = run_calls(run_dir)
    if not calls:
        return {"calls": 0, "note": f"no saved prompts under {Path(run_dir) / 'workers'}"}
    return {"run": Path(run_dir).name, **analyze(calls, harness_tokens)}


def analyze(calls: list[dict[str, Any]], harness_tokens: int = 6000) -> dict[str, Any]:
    """Section totals, fan-out duplication and amplification for one run."""
    per_role: dict[str, Counter] = {}
    totals = Counter()
    for call in calls:
        parts = sections(call["prompt"])
        per_role.setdefault(call["role"], Counter()).update(parts)
        totals.update(parts)
    workers = [call for call in calls if call["role"] != "planner"]
    line_counts = Counter(line for call in workers for line in set(call["prompt"].splitlines()) if len(line) > 20)
    duplicated = sum(tokens(line + "\n") * (count - 1) for line, count in line_counts.items() if count > 1)
    worker_tokens = sum(tokens(call["prompt"]) for call in workers)
    unique_lines = {line for call in calls for line in call["prompt"].splitlines()}
    unique = sum(tokens(line + "\n") for line in unique_lines) + harness_tokens  # the harness counted once as "needed"
    processed = sum(tokens(call["prompt"]) + harness_tokens for call in calls)
    top_repeats = sorted(((tokens(line + "\n") * (count - 1), count, line[:90]) for line, count in line_counts.items() if count > 1), reverse=True)[:8]
    return {
        "calls": len(calls),
        "by_role_calls": dict(Counter(call["role"] for call in calls)),
        "prompt_tokens_total": sum(tokens(call["prompt"]) for call in calls),
        "harness_tokens_total": harness_tokens * len(calls),
        "input_tokens_processed": processed,
        "unique_tokens": unique,
        "context_amplification": round(processed / unique, 2) if unique else None,
        "worker_fanout_duplicated_tokens": duplicated,
        "worker_fanout_duplication_share": round(duplicated / worker_tokens, 3) if worker_tokens else None,
        "sections_total": dict(totals.most_common()),
        "sections_by_role": {role: dict(counter.most_common()) for role, counter in per_role.items()},
        "top_repeated_lines": [{"tokens_wasted": waste, "copies": count, "line": line} for waste, count, line in top_repeats],
        "note": "estimates (chars/3.5); harness tokens are per call and mostly cache-served",
    }
