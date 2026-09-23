"""Simple Mode: the orchestrator's state in plain English.

Pure functions from engine state to what a non-technical user sees: overall
status, discrete progress steps, agent status, friendly problem cards, the
activity feed, the efficiency dashboard, and the single recommended next
action ("Tell me what to press"). The GUI only renders these; keeping them
here makes them testable without a browser and keeps policy out of the GUI.

Progress is never a made-up percentage: steps come from real workflow states.
"""

from __future__ import annotations

from typing import Any

from .ledger import PROVIDER_NAMES, describe, provider_name

ACTIVE = frozenset({"CLAIMED", "LAUNCHING", "RUNNING", "WAITING_FOR_RESULT", "VALIDATING"})
EDITING = frozenset({"implementer", "test_author"})

OVERALL = {
    "CREATED": ("READY", "Ready to start"),
    "PLANNING": ("WORKING", "Planning the work"),
    "READY": ("WORKING", "Getting the next step ready"),
    "RUNNING": ("WORKING", "Working"),
    "VALIDATING": ("WORKING", "Running tests"),
    "REVIEWING": ("WORKING", "Reviewing the work"),
    "INTEGRATING": ("WORKING", "Combining finished work"),
    "APPROVAL_REQUIRED": ("NEEDS YOU", "Waiting for your decision"),
    "PAUSED": ("PAUSED", "Paused"),
    "BLOCKED": ("STOPPED", "Stopped: something needs attention"),
    "FAILED": ("STOPPED", "Stopped: something went wrong"),
    "COMPLETE": ("DONE", "Finished"),
}

# ---------------------------------------------------------------------------
# Problem cards
# ---------------------------------------------------------------------------

GATE_CARDS: dict[str, dict[str, Any]] = {
    "consequential_repository_write": {
        "title": "The work is finished and ready to save",
        "what": "The change passed its tests and an independent review. It is saved on a separate branch.",
        "changed": "Your main branch has not been changed yet.",
        "recommended": {"label": "Approve Commit", "decision": "approve", "does": "Adds the finished work to your main branch."},
        "options": [{"label": "Keep It Separate", "decision": "reject", "does": "Leaves the work on its own branch; nothing on main changes."}],
        "explain": "Agents work on copies of your project. When everything passes, the result waits here so you decide when it becomes part of your main branch.",
    },
    "semantic_merge_conflict": {
        "title": "I found two different versions of the same work",
        "what": "Two parts of this job changed the same files in different ways, so I could not combine them automatically.",
        "changed": "Nothing has been changed yet. Both versions are kept.",
        "recommended": {"label": "Use Newer Version", "decision": "approve", "does": "Redoes this part on top of the newest combined work."},
        "options": [{"label": "Skip", "decision": "reject", "does": "Stops this part. The run stops so you can look."}],
        "explain": "This happens when two agents edit the same file at the same time. Redoing the later part on top of the finished one is the safe fix.",
    },
    "unresolved_review_findings": {
        "title": "The reviewer still has concerns",
        "what": "After the allowed rounds of fixes, the independent reviewer still reports problems with this change.",
        "changed": "Nothing has been added to your main branch.",
        "recommended": {"label": "Don't Use This Change", "decision": "reject", "does": "Stops this part so it can be looked at; nothing is saved to main."},
        "options": [{"label": "Accept Anyway", "decision": "approve", "does": "Uses the change even though the reviewer has concerns (recorded)."}],
        "explain": "A second agent checks every change. When fixes do not satisfy it, a person should decide rather than let agents go back and forth forever.",
    },
    "agent_needs_decision": {
        "title": "An agent needs you to decide something",
        "what": "The agent stopped instead of guessing, because the choice would change the result.",
        "changed": "The agent's partial work is saved. Nothing on main has changed.",
        "recommended": {"label": "Answer and Continue", "decision": "approve", "does": "Sends your answer to the agent and continues.", "needs_note": True},
        "options": [{"label": "Skip This Part", "decision": "reject", "does": "Cancels this part of the job."}],
        "explain": "Agents are told to ask when a decision would materially change the outcome.",
    },
    "policy_restricted_action": {
        "title": "This change has no tests to check it",
        "what": "No test command ran for this change, so there is no evidence it works.",
        "changed": "Nothing has been added to your main branch.",
        "recommended": {"label": "Don't Use It", "decision": "reject", "does": "Stops this part; nothing is saved to main."},
        "options": [{"label": "Use It Without Tests", "decision": "approve", "does": "Accepts the change without test evidence (recorded)."}],
        "explain": "Work is only combined automatically when tests pass. Without tests, you decide.",
    },
    "budget_exhausted": {
        "title": "This run has used its agent budget",
        "what": "The run started the maximum number of agent sessions it is allowed.",
        "changed": "Finished work is kept. Nothing on main has changed.",
        "recommended": {"label": "Allow More", "decision": "approve", "does": "Raises the limit so the run can continue (uses more model time)."},
        "options": [{"label": "Stop Here", "decision": "reject", "does": "Keeps what is finished and stops."}],
        "explain": "The limit stops a run from using model time without end.",
    },
}
for _kind, _verb in (("destructive_action", "delete or overwrite something"), ("credential_or_secret_entry", "use a password or secret"), ("consequential_external_write", "change something outside this computer")):
    GATE_CARDS[_kind] = {
        "title": f"This step would {_verb}",
        "what": "The plan marked this step as needing your permission.",
        "changed": "Nothing has been done yet.",
        "recommended": {"label": "Skip This Step", "decision": "reject", "does": "Does not run the step."},
        "options": [{"label": "Allow This Step", "decision": "approve", "does": "Runs the step."}],
        "explain": "Steps with lasting effects always wait for a person.",
    }

FAILURE_TEXT = {
    "quota": "{who} has run out of usage for now.",
    "unavailable": "{who} could not be started on this computer.",
    "invalid_model": "{who} rejected the model it was given.",
    "timeout": "{who} took too long and was stopped.",
    "malformed": "{who} did not return a usable answer.",
    "interrupted": "The program driving this run stopped while {who} was working.",
    "validator_failed": "The change still fails its tests after every allowed attempt.",
    "process_error": "{who} stopped with an error.",
    "cancelled": "This part was cancelled.",
    "merge_conflict": "This part conflicted with other finished work.",
}


def gate_card(gate: dict[str, Any], node: dict[str, Any] | None = None) -> dict[str, Any]:
    template = GATE_CARDS.get(gate["kind"]) or {
        "title": "Something needs your decision",
        "what": gate.get("reason") or "",
        "changed": "Nothing has been changed yet.",
        "recommended": {"label": "Approve", "decision": "approve", "does": "Continues."},
        "options": [{"label": "Decline", "decision": "reject", "does": "Stops this part."}],
        "explain": "",
    }
    card = {key: (dict(value) if isinstance(value, dict) else value) for key, value in template.items()}
    if gate["kind"] == "agent_needs_decision":
        card["what"] = f"The agent asks: {gate.get('reason')}"
    card.update(
        kind="gate",
        gate_id=gate["id"],
        advanced={"gate": gate["id"], "kind": gate["kind"], "reason": gate.get("reason"), "node": gate.get("node"), "opened": gate.get("created_at"), "node_goal": (node or {}).get("goal")},
    )
    return card


def failure_card(node: dict[str, Any]) -> dict[str, Any]:
    failures = node.get("failures") or []
    kind = failures[-1]["kind"] if failures else "process_error"
    who = provider_name(node.get("provider") or (failures[-1].get("provider") if failures else None))
    if who == "a local step":
        who = "The agent"
    what = FAILURE_TEXT.get(kind, "{who} could not finish.").format(who=who)
    if (node.get("wait_reason") or "").startswith("no provider"):
        cause = FAILURE_TEXT.get(kind, "").format(who=who) if failures else ""
        what = (cause + " " if cause else "") + "No other available agent can do this part right now."
    return {
        "kind": "failure",
        "node": node["id"],
        "title": f"This part could not be finished: {node['goal'][:90]}",
        "what": what,
        "changed": "Partial work is saved on its own branch. Nothing on your main branch has changed.",
        "recommended": {"label": "Try Again", "action": "retry", "does": "Tries this part again, on another agent if one is available."},
        "options": [{"label": "Start Fresh", "action": "fresh", "does": "Sets this run aside and starts the roadmap task again from the beginning."}],
        "explain": "Agents sometimes fail for reasons that go away on a retry: usage limits, a slow network, or a model that returned something unusable. Every attempt is limited, so retrying cannot loop forever.",
        "advanced": {"node": node["id"], "state": node["state"], "wait_reason": node.get("wait_reason"), "failures": failures[-3:]},
    }


# ---------------------------------------------------------------------------
# Progress
# ---------------------------------------------------------------------------


def _step(label: str, status: str, detail: str | None = None) -> dict[str, Any]:
    return {"label": label, "status": status, "detail": detail}


def work_steps(run: dict[str, Any]) -> list[dict[str, Any]]:
    """Discrete progress for the current work unit, from real node states.

    status: done | active | pending | waiting (needs you) | failed | skipped
    """
    nodes = run["nodes"]
    state = run["state"]
    gates = [gate for gate in run["gates"] if gate["status"] == "open"]
    planner = next((node for node in nodes if node["role"] == "planner"), None)
    editors = [node for node in nodes if node["role"] in EDITING]
    reviewers = [node for node in nodes if node["role"] == "reviewer"]
    repairs = [node for node in nodes if node["role"] == "repairer"]
    steps = []

    if planner is None:
        steps.append(_step("Plan", "skipped", "tasks were given; no planning needed"))
    elif planner["state"] == "PASSED":
        steps.append(_step("Plan", "done", f"{len(editors)} task(s) planned"))
    elif planner["state"] in {"FAILED_FINAL", "CANCELLED"}:
        steps.append(_step("Plan", "failed", planner.get("wait_reason")))
    elif planner["state"] in ACTIVE:
        steps.append(_step("Plan", "active", f"{provider_name(planner.get('provider'))} is planning"))
    else:
        steps.append(_step("Plan", "pending"))

    def count(predicate) -> int:
        return sum(1 for node in editors if predicate(node))

    implemented = count(lambda node: node["state"] in {"VALIDATING", "WAITING_FOR_REVIEW", "NEEDS_REPAIR", "PASSED", "APPROVAL_REQUIRED"} or node["integrated"])
    tested = count(lambda node: bool((node.get("validation") or {}).get("passed")))
    reviewed = count(lambda node: node["state"] == "PASSED" and (not node["review"]["reviewers"] or node["review"]["reviewers"][-1]["verdict"] == "approved" or node["review"]["accepted_by_user"]))
    integrated = count(lambda node: node["integrated"])
    total = len(editors)
    failed = [node for node in editors if node["state"] in {"FAILED_FINAL", "CANCELLED"}]

    def phase(label: str, finished: int, active: bool, failed_here: bool = False) -> dict[str, Any]:
        if total == 0:
            return _step(label, "pending")
        detail = f"{finished} of {total}"
        if finished >= total:
            return _step(label, "done", detail)
        if failed_here:
            return _step(label, "failed", detail)
        return _step(label, "active" if active else "pending", detail)

    running_edit = any(node["state"] in ACTIVE - {"VALIDATING"} for node in editors)
    steps.append(phase("Implement", implemented, running_edit, any(not (node.get("validation") or {}) for node in failed)))
    steps.append(phase("Test", tested, any(node["state"] == "VALIDATING" for node in editors), any((node.get("validation") or {}).get("passed") is False for node in failed)))
    steps.append(phase("Review", reviewed, any(node["state"] in ACTIVE for node in reviewers) or any(node["state"] == "WAITING_FOR_REVIEW" for node in editors)))
    if not repairs:
        steps.append(_step("Fix findings", "skipped" if total and reviewed >= total else "pending", "nothing to fix" if total and reviewed >= total else None))
    else:
        done_repairs = sum(1 for node in repairs if node["state"] == "PASSED")
        status = "active" if any(node["state"] in ACTIVE or node["state"] in {"PENDING", "RUNNABLE", "FAILED_RETRYABLE"} for node in repairs) else ("failed" if any(node["state"] == "FAILED_FINAL" for node in repairs) else "done")
        steps.append(_step("Fix findings", status, f"{done_repairs} of {len(repairs)} fix round(s)"))
    landing_gate = next((gate for gate in gates if gate["kind"] == "consequential_repository_write"), None)
    final = run.get("final") or {}
    if landing_gate:
        steps.append(_step("Commit", "waiting", "waiting for your approval"))
    elif state == "COMPLETE":
        landed = final.get("landed") or {}
        if landed.get("ok"):
            steps.append(_step("Commit", "done", f"added to {run.get('base_ref') or 'main'}"))
        elif landed:
            steps.append(_step("Commit", "failed", landed.get("reason")))
        else:
            steps.append(_step("Commit", "done", "saved on the run's branch"))
    else:
        steps.append(_step("Commit", "active" if total and integrated >= total and not final.get("validation") else "pending", f"{integrated} of {total} combined" if total else None))
    return steps


def prep_steps(prep: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not prep:
        return []
    return [_step(item["label"], {"done": "done", "active": "active", "failed": "failed", "skipped": "skipped"}.get(item["status"], "pending"), item.get("detail")) for item in prep["steps"]]


def agent_status(run: dict[str, Any] | None, providers: list[dict[str, Any]], driving: bool, git_dirty: bool | None) -> list[dict[str, Any]]:
    rows = []
    nodes = (run or {}).get("nodes") or []
    for provider in providers:
        pid = provider["id"]
        name = PROVIDER_NAMES.get(pid, pid)
        probe = provider.get("probe") or {}
        mine = [node for node in nodes if node.get("provider") == pid and node["state"] in ACTIVE]
        if not provider.get("enabled", True) or probe.get("available") is False:
            status, detail = "Unavailable", probe.get("reason") or "not installed or disabled"
        elif mine:
            node = mine[0]
            status = "Reviewing" if node["role"] == "reviewer" else ("Planning" if node["role"] == "planner" else "Working")
            detail = f"{node['id']} ({node.get('model')}, effort {node.get('provider_effort')})"
        elif run and run["state"] not in {"COMPLETE", "PAUSED", "BLOCKED", "CREATED"} and any(node["state"] == "WAITING_FOR_REVIEW" for node in nodes):
            status, detail = "Waiting", "may review the next change"
        else:
            status, detail = "Idle", None
        rows.append({"agent": name, "status": status, "detail": detail})
    if run is None:
        rows.append({"agent": "Agent OS", "status": "Idle", "detail": None})
    elif run["state"] in {"COMPLETE"}:
        rows.append({"agent": "Agent OS", "status": "Done", "detail": None})
    elif driving:
        rows.append({"agent": "Agent OS", "status": "Monitoring", "detail": "driving the run"})
    elif run["state"] in {"PAUSED", "APPROVAL_REQUIRED", "BLOCKED"}:
        rows.append({"agent": "Agent OS", "status": "Waiting", "detail": "waiting for you"})
    else:
        rows.append({"agent": "Agent OS", "status": "Not running", "detail": "press Resume to continue"})
    if git_dirty is not None:
        rows.append({"agent": "Git", "status": "Has unsaved changes" if git_dirty else "Clean", "detail": "agents cannot see uncommitted changes" if git_dirty else None})
    return rows


def current_task(run: dict[str, Any]) -> str:
    nodes = run["nodes"]
    for role in ("planner", "implementer", "test_author", "repairer", "reviewer"):
        for node in nodes:
            if node["role"] == role and node["state"] in ACTIVE:
                if role == "planner":
                    return "Planning the work into small tasks"
                if role == "reviewer":
                    return f"Reviewing: {nodes_goal(nodes, node.get('subject'))}"
                if role == "repairer":
                    return f"Fixing review findings: {nodes_goal(nodes, node.get('subject'))}"
                return node["goal"][:160]
    waiting = next((node for node in nodes if node["state"] in {"PENDING", "RUNNABLE", "FAILED_RETRYABLE"}), None)
    if run["state"] == "COMPLETE":
        return "All tasks finished"
    open_gates = [gate for gate in run.get("gates") or [] if gate["status"] == "open"]
    if open_gates:
        return "Waiting for you: " + GATE_CARDS.get(open_gates[0]["kind"], {}).get("title", "a decision").lower()
    return (waiting["goal"][:160] if waiting else run["goal"].splitlines()[0][:160])


def nodes_goal(nodes: list[dict[str, Any]], node_id: str | None) -> str:
    node = next((item for item in nodes if item["id"] == node_id), None)
    return (node or {}).get("goal", node_id or "")[:140]


# ---------------------------------------------------------------------------
# Views
# ---------------------------------------------------------------------------


def efficiency_view(report: dict[str, Any] | None) -> dict[str, Any] | None:
    """Dashboard numbers. Every number carries its accuracy label."""
    if not report:
        return None
    calls = report["model_calls"]
    tokens = report["tokens"]
    context = report["context"]
    avoided = report["avoided"]
    counts = report["counts"]
    exact = tokens["exact"]
    # With no provider-reported call, token totals are unknown, not zero.
    measured = exact["calls"] > 0

    def tok(value: int) -> int | None:
        return value if measured else None

    rows = [
        {"label": "Model calls", "value": calls["total"], "accuracy": "measured", "help": "Times an AI model (Claude or Codex) was started for this run."},
        {"label": "Highest-cost model calls", "value": calls["expensive"], "accuracy": "measured", "help": "Calls on the reasoning or frontier tier, the most expensive settings."},
        {"label": "Local / no-model steps", "value": counts["local_operations"], "accuracy": "measured", "help": "Work done by plain code or reused results instead of a model."},
        {"label": "Input tokens (provider-reported)", "value": tok(exact["input"]), "accuracy": "exact", "help": "Tokens the models read, as reported by the provider. Includes cached tokens."},
        {"label": "  of which cache reads", "value": tok(exact["cache_read"]), "accuracy": "exact", "help": "Input tokens served from the provider's prompt cache (cheaper, but still usage)."},
        {"label": "Output tokens (provider-reported)", "value": tok(exact["output"]), "accuracy": "exact", "help": "Tokens the models wrote, as reported by the provider."},
        {"label": "Calls with no token report", "value": tokens["unavailable_calls"], "accuracy": "measured", "help": "Model calls whose provider did not report usage. Their tokens are not in the totals."},
        {"label": "Estimated tokens avoided", "value": avoided["tokens_estimate"] if avoided["estimated_events"] else None, "accuracy": "estimated", "help": "Only counted where an avoided call has a measured cost to compare with. Blank means no defensible estimate yet."},
        {"label": "Model calls avoided", "value": avoided["model_calls"], "accuracy": "measured", "help": "Calls that were not needed because work was reused, done locally, or skipped."},
        {"label": "Cache hits", "value": counts["cache_hits"], "accuracy": "measured", "help": "Earlier results reused instead of redoing the work."},
        {"label": "Skill reuse", "value": counts["skill_reuse"], "accuracy": "measured", "help": "Tasks handled by an existing reusable skill."},
        {"label": "Context items considered", "value": context["candidate_items"], "accuracy": "measured", "help": "Project documents that could have been sent to a model."},
        {"label": "Context items sent", "value": context["selected_items"], "accuracy": "measured", "help": "The compact pieces Orchestrator actually put in prompts."},
        {"label": "Context reduction", "value": context["reduction_pct"], "unit": "%", "accuracy": "estimated", "help": "Context reduction means Orchestrator found only the parts relevant to this task instead of sending the whole set of project documents. Measured in characters, estimated in tokens."},
        {"label": "Provider escalations", "value": counts["escalations"], "accuracy": "measured", "help": "Times a task moved to a stronger (more expensive) setting because tests failed."},
        {"label": "Retries", "value": counts["retries"], "accuracy": "measured", "help": "Attempts repeated after a failure."},
        {"label": "Loop guards triggered", "value": counts["loop_guards"], "accuracy": "measured", "help": "Times Orchestrator stopped a repeat that would have wasted work."},
    ]
    if tokens["provider_reported_cost_usd"]:
        rows.insert(6, {"label": "Provider-reported cost (list price)", "value": tokens["provider_reported_cost_usd"], "unit": "USD", "accuracy": "exact", "help": "Claude Code reports a list-price cost per call. Codex does not report cost. Plans billed by subscription are not charged this amount."})
    if tokens["synthetic"]["calls"]:
        rows.append({"label": "Synthetic test calls (not real usage)", "value": tokens["synthetic"]["calls"], "accuracy": "synthetic", "help": "Scripted test workers. Their token numbers are excluded from the totals above."})
    gap = report["prompt_vs_actual"]
    if gap.get("agent_overhead_tokens_estimate"):
        rows.append({"label": "Tokens agents spent beyond the prompt", "value": gap["agent_overhead_tokens_estimate"], "accuracy": "estimated", "help": "Provider-reported input minus the size of the prompt Orchestrator wrote. This is the agent tool's own instructions plus files it chose to read. It is usually most of the cost."})
    return {"rows": rows, "report": report}


def run_view(run: dict[str, Any], events: list[dict[str, Any]], efficiency: dict[str, Any] | None, providers: list[dict[str, Any]], *, driving: bool, prep: dict[str, Any] | None = None, git_dirty: bool | None = None) -> dict[str, Any]:
    overall, headline = OVERALL.get(run["state"], ("WORKING", run["state"].title()))
    active = any(node["state"] in ACTIVE for node in run["nodes"])
    if run["state"] not in {"COMPLETE", "PAUSED", "APPROVAL_REQUIRED", "BLOCKED", "CREATED"} and not driving and not active:
        overall, headline = "INTERRUPTED", "Not running: the program driving this run stopped"
    if run["state"] not in {"COMPLETE", "PAUSED", "APPROVAL_REQUIRED", "BLOCKED", "CREATED"} and not driving and active:
        overall, headline = "INTERRUPTED", "An agent may still be working, but nothing is collecting its result"
    nodes = {node["id"]: node for node in run["nodes"]}
    problems = [gate_card(gate, nodes.get(gate.get("node") or "")) for gate in run["gates"] if gate["status"] == "open"]
    if run["state"] == "BLOCKED":
        problems += [failure_card(node) for node in run["nodes"] if node["state"] in {"FAILED_FINAL", "CANCELLED"}]
        if not problems:
            problems.append({"kind": "failure", "node": None, "title": "The combined work fails its final tests", "what": run.get("state_reason") or "", "changed": "Nothing on your main branch has changed.", "recommended": {"label": "Try Again", "action": "retry_final", "does": "Runs one more fix attempt."}, "options": [{"label": "Start Fresh", "action": "fresh", "does": "Starts this roadmap task again."}], "explain": "", "advanced": {"state_reason": run.get("state_reason")}})
    origin = run.get("origin") or {}
    stage = {"id": origin.get("stage_id"), "title": origin.get("stage_title")} if origin.get("kind") == "roadmap" else None
    return {
        "run_id": run["run_id"],
        "overall": overall,
        "headline": headline,
        "stage": stage,
        "current_task": current_task(run),
        "steps": [*prep_steps(prep), *work_steps(run)],
        "tasks": {"done": sum(1 for node in run["nodes"] if node["role"] in EDITING and node["integrated"]), "total": sum(1 for node in run["nodes"] if node["role"] in EDITING)},
        "agents": agent_status(run, providers, driving, git_dirty),
        "problems": problems,
        "activity": [{"at": event["at"], "text": describe(event), "type": event["type"]} for event in events[-60:]],
        "efficiency": efficiency_view(efficiency),
        "summary": run_summary(run, efficiency) if run["state"] == "COMPLETE" else None,
        "telemetry_warning": run.get("telemetry_warning"),
        "auto_continue": run.get("auto_continue"),
    }


def run_summary(run: dict[str, Any], report: dict[str, Any] | None) -> dict[str, Any]:
    editors = [node for node in run["nodes"] if node["role"] in EDITING]
    files = set()
    for node in editors:
        files.update((node.get("validation") or {}).get("changed_files") or [])
    report = report or {}
    calls = (report.get("model_calls") or {}).get("by_provider") or {}
    tests = report.get("tests") or {}
    tokens = (report.get("tokens") or {}).get("exact") or {}
    avoided = report.get("avoided") or {}
    final = run.get("final") or {}
    return {
        "title": "ROADMAP RUN COMPLETE" if (run.get("origin") or {}).get("kind") == "roadmap" else "RUN COMPLETE",
        "tasks_completed": sum(1 for node in editors if node["integrated"]),
        "files_changed": len(files),
        "tests": {"runs": tests.get("runs"), "passed": tests.get("tests_passed"), "failed": tests.get("tests_failed"), "reused": tests.get("reused")},
        "commits": (report.get("counts") or {}).get("commits"),
        "calls_by_agent": {PROVIDER_NAMES.get(key, key): value for key, value in calls.items()},
        "local_operations": (report.get("counts") or {}).get("local_operations"),
        "tokens_used_exact": tokens.get("input", 0) + tokens.get("output", 0) if tokens.get("calls") else None,
        "calls_without_token_report": (report.get("tokens") or {}).get("unavailable_calls"),
        "tokens_avoided_estimate": avoided.get("tokens_estimate") if avoided.get("estimated_events") else None,
        "model_calls_avoided": avoided.get("model_calls"),
        "landed": final.get("landed"),
        "how_to_land": (final.get("summary") or {}).get("how_to_land"),
    }


def usage_view(report: dict[str, Any]) -> dict[str, Any]:
    """Cross-run usage in plain words; every row keeps its accuracy label."""
    totals = report["totals"]
    coverage = report["coverage"]
    gap = report["prompt_vs_provider_input"]
    measured = totals["exact_calls"] > 0
    rows = [
        {"label": "Runs with model use", "value": report["runs_counted"], "accuracy": "measured", "help": "Orchestrated runs on this computer that recorded telemetry."},
        {"label": "Model calls", "value": totals["calls"], "accuracy": "measured", "help": "Every time Claude or Codex was started."},
        {"label": "Input tokens (provider-reported)", "value": totals["input"] if measured else None, "accuracy": "exact", "help": "All tokens the models read, including cached ones."},
        {"label": "Output tokens (provider-reported)", "value": totals["output"] if measured else None, "accuracy": "exact", "help": "Tokens the models wrote."},
        {"label": "Calls with no token report", "value": coverage["calls_without_token_report"], "accuracy": "measured", "help": "Their tokens are not in the totals above."},
        {"label": "Share of input that was agent-tool overhead", "value": round(100 * gap["overhead_share_estimate"], 1) if gap.get("overhead_share_estimate") is not None else None, "unit": "%", "accuracy": "estimated", "help": "How much of what the models read was the agent tool's own instructions and exploration rather than the task Orchestrator wrote."},
        {"label": "Highest-cost model calls", "value": sum(report["expensive_tier_calls_by_role"].values()), "accuracy": "measured", "help": "Calls on the reasoning or frontier tier."},
        {"label": "Model calls avoided", "value": sum(report["model_calls_avoided_by_category"].values()), "accuracy": "measured", "help": "Calls not needed because work was reused, skipped or done locally."},
    ]
    if totals["cost_usd"]:
        rows.insert(4, {"label": "Claude list-price cost", "value": totals["cost_usd"], "unit": "USD", "accuracy": "exact", "help": "Reported by Claude Code at list price. Codex reports no cost; subscription plans are not billed this way."})
    return {"rows": rows, "report": report}


# ---------------------------------------------------------------------------
# Tell me what to press
# ---------------------------------------------------------------------------


def advise(home: dict[str, Any], run_view_: dict[str, Any] | None, prep: dict[str, Any] | None = None) -> dict[str, Any]:
    """One recommended action for the current state. ``target`` names the
    button the GUI should highlight."""
    if prep and prep.get("state") == "running":
        return {"target": None, "message": f"Nothing needs your attention. {prep.get('message') or 'Getting ready...'}"}
    providers = home.get("providers") or []
    if providers and not any((item.get("probe") or {}).get("available", True) and item.get("enabled", True) for item in providers):
        return {"target": "settings", "message": "Press Settings. No coding agent (Claude or Codex) is available on this computer yet."}
    if run_view_:
        overall = run_view_["overall"]
        problems = run_view_["problems"]
        if problems:
            card = problems[0]
            label = card["recommended"]["label"]
            return {"target": f"problem:{card.get('gate_id') or card.get('node') or 'final'}", "message": f"Press {label}. {card['title']}."}
        if overall == "PAUSED":
            return {"target": "resume", "message": "Press Resume. The run is paused."}
        if overall == "INTERRUPTED":
            return {"target": "resume", "message": "Press Resume. The previous run was interrupted."}
        if overall == "WORKING":
            busy = [row for row in run_view_["agents"] if row["status"] in {"Working", "Reviewing", "Planning"}]
            who = busy[0]["agent"] if busy else "Agent OS"
            doing = busy[0]["status"].lower() if busy else "working"
            return {"target": None, "message": f"Nothing needs your attention. {who} is still {doing}."}
        if overall == "DONE":
            if home.get("next_stage"):
                return {"target": "continue", "message": "Press Continue Roadmap. The last task is finished and the next one is ready."}
            return {"target": None, "message": "Nothing to do. Every eligible roadmap stage is complete."}
    unfinished = home.get("unfinished_runs") or []
    if unfinished:
        state = unfinished[0].get("state")
        if state in {"APPROVAL_REQUIRED", "BLOCKED"}:
            return {"target": "view-progress", "message": "Press View Progress. An earlier run is waiting for your decision."}
        return {"target": "continue", "message": "Press Continue Roadmap. It will resume the run that was interrupted."}
    if home.get("next_stage"):
        note = " Your project has uncommitted changes; the agents will not see them." if home.get("dirty") else ""
        return {"target": "continue", "message": f"Press Continue Roadmap. Everything is ready.{note}"}
    if home.get("roadmap") is None:
        return {"target": "start-task", "message": "Press Start Specific Task. This project has no roadmap file I can read."}
    return {"target": None, "message": "Nothing to do. Every eligible roadmap stage is complete."}
