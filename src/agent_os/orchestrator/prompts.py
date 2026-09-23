"""Bounded worker prompts.

Each worker receives only its own assignment, scope, validators, a compact
project context packet, and an output contract. Prompts are written to the
local run directory (gitignored runtime state) and are never copied into the
run record or canonical Git state.
"""

from __future__ import annotations

import json
from typing import Any

from .adapters.base import RESULT_FENCE
from .usage import estimate_tokens


def _context_packet(project: str | None, task: str, budget: int) -> tuple[str, dict[str, Any] | None]:
    """The compact project context for a worker, plus how it was selected:
    how much registered project context existed (the candidate) and how much
    was actually put in the prompt."""
    if not project:
        return "", None
    try:
        from ..compiler import compile_context

        packet = compile_context(project, task, token_budget=budget, include_handoff=False)
    except Exception:
        return "", None
    state = packet.get("state") or {}
    lines = []
    if packet.get("summary"):
        lines.append(f"Project summary: {packet['summary']}")
    items = 0
    for key in ("constraints", "validation_commands"):
        values = state.get(key) or []
        if values:
            items += 1
            lines.append(f"{key.replace('_', ' ').capitalize()}:")
            lines.extend(f"- {item}" for item in values[:8])
    text = "\n".join(lines)[: budget * 4]
    measurement = packet.get("context_measurement") or {}
    return text, {
        "method": "candidate = every registered context file and skill for the project; selected = the compact slice placed in the prompt",
        "candidate_items": measurement.get("naive_all_registered_context_items"),
        "candidate_tokens_estimate": measurement.get("naive_all_registered_context_tokens"),
        "selected_items": items + (1 if packet.get("summary") else 0),
        "selected_tokens_estimate": estimate_tokens(text),
    }


def _contract(role: str) -> str:
    if role == "planner":
        example = {
            "status": "done",
            "summary": "one line",
            "tasks": [
                {
                    "id": "short-kebab-id",
                    "goal": "precise instruction: what to change, where, and how to know it is done",
                    "role": "implementer | test_author",
                    "depends_on": [],
                    "scope": ["repo/relative/file.py", "tests/test_file.py"],
                    "capability_class": "fast | balanced | reasoning",
                    "effort": "low | medium | high",
                    "validators": ["python -m unittest tests.test_file"],
                    "ladder": [
                        {"capability_class": "fast", "effort": "low"},
                        {"capability_class": "fast", "effort": "high"},
                        {"capability_class": "balanced", "effort": "medium"},
                    ],
                }
            ],
        }
    elif role == "reviewer":
        example = {
            "status": "done",
            "verdict": "approved | changes_requested | blocked",
            "summary": "one line",
            "findings": [
                {
                    "id": "1",
                    "severity": "critical | high | medium | low | info",
                    "path": "file/path",
                    "summary": "what is wrong",
                    "evidence": "why you believe it",
                    "recommended_action": "what to change",
                    "validator_needed": True,
                }
            ],
        }
    elif role == "repairer":
        example = {
            "status": "done | needs_decision",
            "summary": "one line",
            "dispositions": [{"id": "R1-1", "disposition": "fixed | rejected", "reason": "required when rejected"}],
            "question": "only when status is needs_decision",
        }
    else:
        example = {
            "status": "done | already_done | needs_decision",
            "summary": "one line",
            "outputs": ["files you created or changed"],
            "question": "only when status is needs_decision",
        }
    return (
        "When you finish, end your reply with exactly one fenced block tagged "
        f"`{RESULT_FENCE}` containing JSON shaped like:\n\n"
        f"```{RESULT_FENCE}\n{json.dumps(example, indent=2)}\n```\n"
    )


def _sibling_lines(run: dict[str, Any], node: dict[str, Any]) -> list[str]:
    """Other planned tasks, so a reviewer does not flag work that belongs to one of them."""
    nodes = run.get("nodes") or {}
    subject = node.get("subject")
    siblings = [
        other for other in nodes.values()
        if other.get("id") != subject and other.get("role") in {"implementer", "test_author"}
    ]
    if not siblings:
        return []
    lines = ["Other tasks in this run cover the following; do not report their work as missing here:"]
    lines += [f"- {other['id']}: {str(other.get('goal') or '')[:160]}" for other in siblings[:16]]
    return [*lines, ""]


def build(run: dict[str, Any], node: dict[str, Any], *, diff: str | None = None, findings: list[dict[str, Any]] | None = None) -> str:
    return build_measured(run, node, diff=diff, findings=findings)[0]


def build_measured(
    run: dict[str, Any], node: dict[str, Any], *, diff: str | None = None, findings: list[dict[str, Any]] | None = None
) -> tuple[str, dict[str, Any] | None]:
    """The prompt and the context-selection measurement behind it."""
    role = node["role"]
    lines = [
        f"You are the {role.replace('_', ' ')} for Agent OS orchestrated run `{run['run_id']}`.",
        "",
        f"Overall goal: {run['goal']}",
        f"Your assignment ({node['id']}): {node['goal']}",
        "",
    ]
    if role in {"implementer", "test_author", "repairer"}:
        scope = node.get("scope") or []
        lines += [
            "Rules:",
            "- Work only inside this worktree; another agent may be editing a different one.",
            "- Edit only paths inside your scope: " + (", ".join(scope) if scope else "(whole repository)"),
            "- Do not commit, push, merge, rebase, or delete branches; the orchestrator checkpoints your work.",
            "- Do not print, store, or request credentials or secrets.",
            "- Everything you need is in this prompt and the worktree. Do not consult Agent OS, memory, or other context",
            "  tools. Read only the files you need, make the change, run your validator once, and finish.",
            "- If a decision would materially change the requested outcome, stop and report status needs_decision with a question.",
            "- If the assignment is already fully done in this worktree, change nothing and report status already_done, citing the evidence in summary.",
        ]
        validators = [item for item in node.get("validators") or [] if item.get("kind") == "command"]
        if validators:
            lines.append("- Your work will be validated with:")
            lines += [f"    {item['command'] if isinstance(item['command'], str) else ' '.join(item['command'])}" for item in validators]
        lines.append("")
    if role == "reviewer":
        lines += [
            "You are an independent reviewer; another agent wrote this change. Do not edit files.",
            "Inspect the change below and the worktree. Review, in priority order:",
            "1. Correctness: bugs, broken edge cases, missing error handling at boundaries, tests that do not exercise the change.",
            "2. Waste: dead code, unused parameters or imports, logic an existing helper already covers, needless abstraction",
            "   or indirection, speculative features beyond the assignment. Prefer deleting code to adding it.",
            "3. Efficiency: repeated work, avoidable quadratic loops, extra subprocess, I/O, or model calls.",
            "4. Scope: edits unrelated to the assignment.",
            "Severity: critical/high = wrong behaviour, data loss, or security; medium = bad code that should be cut or",
            "simplified before merge; low/info = optional polish. Give the smallest concrete fix for each finding.",
            "Report evidenced problems only, not style preferences. An approval with no findings must still be a structured result.",
            "",
            *_sibling_lines(run, node),
            "Change under review:",
            "```diff",
            (diff or "(no diff)").rstrip(),
            "```",
            "",
        ]
    if role == "repairer" and findings:
        lines += ["Address these review findings (fix them, or reject one with a concrete reason):", ""]
        for item in findings:
            lines.append(f"- [{item['id']}] {item['severity']} {item.get('path') or ''}: {item['summary']}")
            if item.get("recommended_action"):
                lines.append(f"  recommended: {item['recommended_action']}")
        lines.append("")
    if role == "planner":
        limit = int((run.get("policy") or {}).get("max_planned_tasks", 16))
        lines += [
            "Do not edit files. Read enough of the repository to plan concretely, then break the goal into the",
            "smallest batches that can each be verified on their own. Cheap models run many small tasks in parallel;",
            "a stronger model reviews each one. Rules:",
            f"- At most {limit} tasks. Prefer several small tasks over a few large ones.",
            "- One concern per task, ideally 1-3 files. List every file a task may edit in `scope`.",
            "  Tasks that can run in parallel must have disjoint scopes; express ordering with depends_on.",
            "- Write each goal as a precise instruction that someone new to the code could finish without asking:",
            "  what to change, in which file and function, and what behaviour proves it is done.",
            "- capability_class: `fast` for mechanical, fully specified work (add a field or flag, tests for existing",
            "  behaviour, a bug with a known fix, docs); `balanced` for a multi-file feature or a bug needing",
            "  investigation; `reasoning` only for design decisions, concurrency, security, or cross-cutting refactors.",
            "  Default to `fast`. When design is needed, make one small `reasoning` task that writes the decision into",
            "  a file in its scope, and let `fast` tasks that depend on it do the implementation.",
            "- effort: `low` for mechanical work, `medium` normally, `high` only for reasoning tasks.",
            "- ladder (optional): escalation steps if validation fails, cheapest first. The default raises effort",
            "  before moving to a stronger class.",
            "- validators: a targeted test command per task, e.g. `python -m unittest tests.test_module`. Only plain",
            "  test commands are accepted; the project's full validation still runs on every task.",
            "- Skip work that is already done. Leave work that needs a human decision out of the plan and name it in",
            "  `summary` instead.",
            "",
        ]
    context, measurement = _context_packet(run.get("project"), node["goal"], int(node.get("context_budget", 1200)))
    if context:
        lines += ["Project context:", context, ""]
    lines.append(_contract(role))
    return "\n".join(lines), measurement
