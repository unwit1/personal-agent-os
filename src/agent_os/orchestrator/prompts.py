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
            "status": "done | already_done | blocked_on_host | needs_decision",
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


# Prompt families that share one run-level prefix: every node of a family gets the same rules.
FAMILIES = {"implementer": "worker", "test_author": "worker", "repairer": "worker", "reviewer": "reviewer", "planner": "planner"}

_WORKER_RULES_HEAD = "- Work only inside this worktree; another agent may be editing a different one."
_WORKER_RULES_TAIL = (
    "- Do not commit, push, merge, rebase, or delete branches; the orchestrator checkpoints your work.",
    "- Do not start, resume, or control a nested Agent OS orchestrator run from this worker. Its Git metadata is shared with",
    "  the parent repository and is outside this worker's write boundary. If the assignment needs a host-level action",
    "  (restarting a server or client, running a nested orchestrator, installing software), do not ask a person: report",
    "  status blocked_on_host with that action in summary. The orchestrator defers the step and keeps the run moving.",
    "- Do not print, store, or request credentials or secrets.",
    "- Every command runs to completion before its output returns. If output is long or cut off, rerun it redirected to",
    "  a file in the worktree and read that file. Never wait on, poll, or inspect processes you did not start: other",
    "  python processes on this machine belong to the orchestrator.",
    "- Everything you need is in this prompt and the worktree. Do not consult Agent OS, memory, or other context",
    "  tools. Read only the files you need, make the change, run your validator once, and finish.",
    "- Run each shell command on its own from the worktree root, exactly as written (no cd, &&, ;, pipes or heredocs):",
    "  chained commands are denied as a whole. Read files with Read, Grep and Glob, not cat, head or sed.",
    "- If a command is denied, do not retry or work around it: the orchestrator runs your validators after you finish.",
    "  A denied command is not a host action; report status done when your change is complete.",
    "- If a decision would materially change the requested outcome, stop and report status needs_decision with a question.",
    "- If the assignment is already fully done in this worktree, change nothing and report status already_done, citing the evidence in summary.",
)
_REVIEWER_RULES = (
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
)


def _scope_line(node: dict[str, Any]) -> str:
    scope = node.get("scope") or []
    return "- Edit only paths inside your scope: " + (", ".join(scope) if scope else "(whole repository)")


def _validator_lines(node: dict[str, Any]) -> list[str]:
    validators = [item for item in node.get("validators") or [] if item.get("kind") == "command"]
    if not validators:
        return []
    return ["- Your work will be validated with:",
            *[f"    {item['command'] if isinstance(item['command'], str) else ' '.join(item['command'])}" for item in validators]]


def _operator_lines(run: dict[str, Any]) -> list[str]:
    messages = [item for item in run.get("operator_messages") or [] if str(item.get("text") or "").strip()][-5:]
    if not messages:
        return []
    return ["Messages from the operator (most recent last); follow them where they apply to your assignment:",
            *[f"- {str(item['text'])[:600]}" for item in messages], ""]


def _cwd_lines(cwd: str | None) -> list[str]:
    if not cwd:
        return []
    return [
        f"Your working directory is {cwd}. It is a complete checkout of the code you work on:",
        "use paths relative to it. Never read or edit the repository it is nested inside.",
        "",
    ]


def shared_prefix(run: dict[str, Any], family: str) -> str:
    """The run-level start of a prompt for one family ('worker', 'reviewer' or 'planner').

    Built only from run fields (goal, operator messages) and static rules, never from a node
    or a working directory, so it is byte-identical for every node of the family and a
    provider prompt cache can serve it. Per-node text follows it."""
    lines = [f"Overall goal: {run['goal']}", ""]
    if family == "worker":
        lines += ["Rules:", _WORKER_RULES_HEAD, *_WORKER_RULES_TAIL, ""]
    elif family == "reviewer":
        lines += [*_REVIEWER_RULES, ""]
    lines += _operator_lines(run)
    return "\n".join([*lines, ""])


def _node_blocks(run: dict[str, Any], node: dict[str, Any], diff: str | None, findings: list[dict[str, Any]] | None, repo_map: str | None, scope_map: str | None) -> list[str]:
    """Role-specific per-node blocks: reviewer diff and findings, repairer findings, planner instructions."""
    role = node["role"]
    lines: list[str] = []
    if scope_map and FAMILIES.get(role) == "worker":
        lines += [
            "Map of the files in your scope (built locally, no need to re-list them; open only what you need):",
            scope_map,
            "",
        ]
    if role == "reviewer":
        if scope_map:
            lines += [
                "Map of the reviewed task's scope files (built locally, no model call; open only what you need to check the change):",
                scope_map,
                "",
            ]
        lines += [
            *_sibling_lines(run, node),
            "Change under review:",
            "```diff",
            (diff or "(no diff)").rstrip(),
            "```",
            "",
        ]
        settled = [item for item in findings or [] if item.get("disposition") in {"follow_up", "rejected"}]
        findings = [item for item in findings or [] if item not in settled]
        if findings:
            lines += ["Earlier review rounds left these findings unresolved. Check each against the current change: report it again",
                      "(same id and summary) if it still applies, and do not approve while one does.", ""]
            for item in findings[-10:]:
                lines.append(f"- [{item['id']}] {item['severity']} {item.get('path') or ''}: {str(item['summary'])[:300]}")
            lines.append("")
        if settled:
            lines += ["Already decided (accepted as a follow-up, or rejected with a reason). Do not report these again unless the",
                      "current change makes one worse or the stated reason is wrong:", ""]
            for item in settled[-10:]:
                why = f" ({item['disposition_reason'][:120]})" if item.get("disposition_reason") else ""
                lines.append(f"- [{item['id']}] {item['disposition']} {item.get('path') or ''}: {str(item['summary'])[:160]}{why}")
            lines.append("")
    if role == "repairer" and findings:
        lines += ["Address these review findings (fix them, or reject one with a concrete reason):", ""]
        for item in findings:
            lines.append(f"- [{item['id']}] {item['severity']} {item.get('path') or ''}: {item['summary']}")
            if item.get("recommended_action"):
                lines.append(f"  recommended: {item['recommended_action']}")
        lines.append("")
    if role == "planner":
        lines += _planner_lines(run, repo_map)
    return lines


def build(run: dict[str, Any], node: dict[str, Any], *, diff: str | None = None, findings: list[dict[str, Any]] | None = None) -> str:
    return build_measured(run, node, diff=diff, findings=findings)[0]


def build_measured(
    run: dict[str, Any], node: dict[str, Any], *, diff: str | None = None, findings: list[dict[str, Any]] | None = None,
    repo_map: str | None = None,
    scope_map: str | None = None,
    cwd: str | None = None,
    prefix: str | None = None,
) -> tuple[str, dict[str, Any] | None]:
    """The prompt and the context-selection measurement behind it.

    With the run policy flag `shared_prefix` on, the prompt is the run-level prefix
    (`prefix`, else `shared_prefix(run, family)`) followed by the per-node text. The words are
    the same as with the flag off; only their order differs."""
    role = node["role"]
    fam = FAMILIES.get(role)
    shared = bool((run.get("policy") or {}).get("shared_prefix")) and fam is not None
    lines = [f"You are the {role.replace('_', ' ')} for Agent OS orchestrated run `{run['run_id']}`.", "", *_cwd_lines(cwd)]
    if shared:
        lines += [f"Your assignment ({node['id']}): {node['goal']}", ""]
        if fam == "worker":
            lines += [_scope_line(node), *_validator_lines(node), ""]
    else:
        lines += [f"Overall goal: {run['goal']}", f"Your assignment ({node['id']}): {node['goal']}", ""]
        if fam == "worker":
            lines += ["Rules:", _WORKER_RULES_HEAD, _scope_line(node), *_WORKER_RULES_TAIL, *_validator_lines(node), ""]
        elif fam == "reviewer":
            lines += [*_REVIEWER_RULES, ""]
    lines += _node_blocks(run, node, diff, findings, repo_map, scope_map)
    context, measurement = _context_packet(run.get("project"), node["goal"], int(node.get("context_budget", 1200)))
    if context:
        lines += ["Project context:", context, ""]
    if not shared:
        lines += _operator_lines(run)
    lines.append(_contract(role))
    text = "\n".join(lines)
    if shared:
        text = (prefix if prefix is not None else shared_prefix(run, fam)) + text
    return text, measurement


def _planner_lines(run: dict[str, Any], repo_map: str | None) -> list[str]:
    lines: list[str] = []
    limit = int((run.get("policy") or {}).get("max_planned_tasks", 16))
    if repo_map:
        budget = int((run.get("policy") or {}).get("planner_read_budget", 8))
        lines += [
            "Do not edit files. Start from the repository map below; it was built for this goal. Open only the files",
            f"you need to name each task's scope and test, usually no more than {budget}. Prefer Grep for a symbol over",
            "reading a whole file. Text quoted in the goal (roadmap, handoff) is authoritative: do not re-read it.",
            "Stop exploring as soon as every task names concrete files and a test command.",
            "",
            repo_map,
            "",
            "Then break the goal into the",
        ]
    else:
        lines.append("Do not edit files. Read enough of the repository to plan concretely, then break the goal into the")
    lines += [
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
        "- `available_execution_paths` may contain only `deterministic` and `model` today. Declare `deterministic`",
        "  only when you have an approved command that can perform the task; the orchestrator selects it first",
        "  and uses `model` only after command or validator failure. Cache and skill execution are not wired here.",
        "- A deterministic task may declare `fallback_execution_paths: [\"model\"]` only when its approved command",
        "  can make a useful attempt first; the model fallback runs only after a command or validator failure.",
        "  Keep the task's model `capability_class` and `effort` for that fallback.",
        "- ladder (optional): escalation steps if validation fails, cheapest first. The default raises effort",
        "  before moving to a stronger class.",
        "- validators: a targeted test command per task, e.g. `python -m unittest tests.test_module`. Only plain",
        "  test commands are accepted; the project's full validation still runs on every task.",
        "- Skip work that is already done. Leave work that needs a human decision out of the plan and name it in",
        "  `summary` instead.",
        "",
    ]
    return lines
