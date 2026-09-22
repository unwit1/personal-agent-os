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


def _context_packet(project: str | None, task: str, budget: int) -> str:
    if not project:
        return ""
    try:
        from ..compiler import compile_context

        packet = compile_context(project, task, token_budget=budget, include_handoff=False)
    except Exception:
        return ""
    state = packet.get("state") or {}
    lines = []
    if packet.get("summary"):
        lines.append(f"Project summary: {packet['summary']}")
    for key in ("constraints", "validation_commands"):
        values = state.get(key) or []
        if values:
            lines.append(f"{key.replace('_', ' ').capitalize()}:")
            lines.extend(f"- {item}" for item in values[:8])
    return "\n".join(lines)[: budget * 4]


def _contract(role: str) -> str:
    if role == "planner":
        example = {
            "status": "done",
            "summary": "one line",
            "tasks": [
                {
                    "id": "short-kebab-id",
                    "goal": "bounded goal",
                    "role": "implementer | test_author",
                    "depends_on": [],
                    "scope": ["repo/relative/path"],
                    "capability_class": "fast | balanced | reasoning",
                    "effort": "low | medium | high",
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
            "status": "done | needs_decision",
            "summary": "one line",
            "outputs": ["files you created or changed"],
            "question": "only when status is needs_decision",
        }
    return (
        "When you finish, end your reply with exactly one fenced block tagged "
        f"`{RESULT_FENCE}` containing JSON shaped like:\n\n"
        f"```{RESULT_FENCE}\n{json.dumps(example, indent=2)}\n```\n"
    )


def build(run: dict[str, Any], node: dict[str, Any], *, diff: str | None = None, findings: list[dict[str, Any]] | None = None) -> str:
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
            "- If a decision would materially change the requested outcome, stop and report status needs_decision with a question.",
        ]
        validators = [item for item in node.get("validators") or [] if item.get("kind") == "command"]
        if validators:
            lines.append("- Your work will be validated with:")
            lines += [f"    {item['command'] if isinstance(item['command'], str) else ' '.join(item['command'])}" for item in validators]
        lines.append("")
    if role == "reviewer":
        lines += [
            "You are an independent reviewer. Do not edit files. Inspect the change below and the worktree.",
            "Report concrete, evidenced problems only. An approval with no findings must still be a structured result.",
            "",
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
        lines += [
            "Do not edit files. Produce a small plan (at most the policy limit) of bounded tasks.",
            "Give tasks that can run in parallel disjoint `scope` paths; express ordering with depends_on.",
            "Prefer the cheapest capability class that can do each task.",
            "",
        ]
    context = _context_packet(run.get("project"), node["goal"], int(node.get("context_budget", 1200)))
    if context:
        lines += ["Project context:", context, ""]
    lines.append(_contract(role))
    return "\n".join(lines)
