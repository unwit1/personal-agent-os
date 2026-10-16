"""AI browser routines in the Executive window.

Outstanding items: routine runs paused for approval, runs that failed or were
blocked, and results the routine flagged for the operator. Approving a paused
action is consequential (preview, then Confirm); the run then resumes in the
background from the same model session.
"""

from __future__ import annotations

from typing import Any, Callable

from agent_os import browser_routines

KIND_APPROVAL = "browser_routine_approval"
KIND_ISSUE = "browser_routine_issue"
KIND_REPORT = "browser_routine_report"


def _describe(actions: list[dict[str, Any]]) -> str:
    parts = []
    for action in actions or []:
        op = action.get("op", "")
        target = action.get("selector") or action.get("url") or ""
        parts.append(f"{op} {target}".strip())
    return "; ".join(parts)


def browser_routine_items(list_runs: Callable[..., list[dict[str, Any]]] | None = None) -> list[dict[str, Any]]:
    runs = (list_runs or browser_routines.list_runs)(limit=100)
    items: list[dict[str, Any]] = []
    seen_issue_for: set[str] = set()
    for run in runs:  # newest first
        if run.get("resolved"):
            continue
        name = run.get("routine_name") or run.get("routine_id")
        base = {
            "tab": run.get("tab") or "personal",
            "source": "browser routines",
            "run_id": run["run_id"],
            "routine_id": run.get("routine_id"),
            "due": None,
            "age": run.get("finished_at") or run.get("started_at"),
        }
        status = run.get("status")
        if status == "needs_approval" and run.get("pending_approval"):
            pending = run["pending_approval"]
            items.append({
                **base,
                "id": f"browser-routine:{run['run_id']}:approval",
                "kind": KIND_APPROVAL,
                "title": f'Routine "{name}" is waiting for your approval',
                "why": pending.get("reason") or _describe(pending.get("actions") or []),
                "context": {
                    "action": _describe(pending.get("actions") or []),
                    "page": pending.get("url"),
                    "progress": run.get("summary"),
                },
            })
        elif status in {"failed", "blocked"}:
            # Only the latest problem per routine; older ones are superseded.
            if run.get("routine_id") in seen_issue_for:
                continue
            seen_issue_for.add(run.get("routine_id"))
            items.append({
                **base,
                "id": f"browser-routine:{run['run_id']}:issue",
                "kind": KIND_ISSUE,
                "title": f'Routine "{name}" {"needs you (blocked)" if status == "blocked" else "failed"}',
                "why": run.get("summary") or run.get("error") or status,
                "context": {"error": run.get("error"), "findings": run.get("findings")},
            })
        elif status == "done" and run.get("notify"):
            items.append({
                **base,
                "id": f"browser-routine:{run['run_id']}:report",
                "kind": KIND_REPORT,
                "title": f"{name}: {(run.get('summary') or 'finished')[:90]}",
                "why": "; ".join(run.get("findings") or []) or run.get("summary") or "",
                "context": {"findings": run.get("findings"), "summary": run.get("summary")},
            })
    return items


def _approve(item: dict[str, Any], params: dict[str, Any], *, confirm: bool) -> dict[str, Any]:
    run = browser_routines.get_run(item["run_id"])
    pending = run.get("pending_approval") or {}
    if not confirm:
        return {
            "routine": run.get("routine_name"),
            "will_allow": _describe(pending.get("actions") or []),
            "page": pending.get("url"),
            "reason": pending.get("reason"),
            "note": "Only this exact action is approved; the routine then continues in the background.",
        }
    browser_routines.approve_run(item["run_id"])
    browser_routines.spawn_detached(["resume", item["run_id"]])
    return {"status": "approved", "resuming": item["run_id"]}


def _decline(item: dict[str, Any], params: dict[str, Any], *, confirm: bool) -> dict[str, Any]:
    run = browser_routines.decline_run(item["run_id"])
    return {"status": run["status"]}


def _retry(item: dict[str, Any], params: dict[str, Any], *, confirm: bool) -> dict[str, Any]:
    browser_routines.resolve_run(item["run_id"])
    run_id = browser_routines.start_run(item["routine_id"], trigger="executive")
    return {"status": "started", "run_id": run_id}


def _acknowledge(item: dict[str, Any], params: dict[str, Any], *, confirm: bool) -> dict[str, Any]:
    browser_routines.resolve_run(item["run_id"])
    return {"status": "resolved"}


def register(registry: Any) -> None:
    registry.register_action(
        "browser_routine.approve", "Approve this action", [KIND_APPROVAL], _approve, consequential=True,
        description="Allow the routine's paused browser action once and resume the routine",
    )
    registry.register_action(
        "browser_routine.decline", "Decline", [KIND_APPROVAL], _decline, consequential=False,
        description="Stop the routine run without performing the paused action",
    )
    registry.register_action(
        "browser_routine.retry", "Run again", [KIND_ISSUE, KIND_REPORT], _retry, consequential=False,
        description="Start the routine again now",
    )
    registry.register_action(
        "browser_routine.acknowledge", "Done", [KIND_ISSUE, KIND_REPORT], _acknowledge, consequential=False,
        description="Mark this routine result as handled",
    )
