"""Start and control orchestrator coding runs from the Command Center.

Every coding task goes through the Orchestrator so it gets its routing, budgets,
review and records. Starting spends model usage, so it only happens on Confirm.
"""

from __future__ import annotations

import re
import threading
from pathlib import Path
from typing import Any

from . import registry

PREVIEW_NOTE = (
    "Starts an orchestrator run that plans, codes, tests and reviews on its own branch; "
    "nothing is merged without you."
)

_START_PATTERNS = (
    re.compile(r"^\s*(?:please\s+)?start\s+a\s+coding\s+task\s*:\s*(?P<goal>.+?)\s*$", re.IGNORECASE | re.DOTALL),
    re.compile(r"^\s*code\s*:\s*(?P<goal>.+?)\s+in\s+(?P<repo>\S+)\s*[.!]?\s*$", re.IGNORECASE | re.DOTALL),
    re.compile(r"^\s*(?:please\s+)?have\s+the\s+orchestrator\s+(?P<goal>.+?)\s*$", re.IGNORECASE | re.DOTALL),
)


def start_item() -> dict[str, Any]:
    """Synthetic item for coding.start; a new run has no provider item yet."""
    return {"id": "coding-start", "kind": "coding_start", "title": "Start a coding task"}


def parse_coding_request(text: str) -> dict[str, Any] | None:
    """Recognise 'start a coding task: X', 'code: X in R', 'have the orchestrator X'."""
    for pattern in _START_PATTERNS:
        match = pattern.match(text or "")
        if match:
            goal = re.sub(r"\s+", " ", match.group("goal")).strip(" .")
            if goal:
                return {"goal": goal, "repo": (match.groupdict().get("repo") or "").strip() or None}
    return None


def _resolve(repo: Any, project: Any) -> tuple[str, str | None]:
    """Return (checkout path, registered project id or None) for a project id or path."""
    from agent_os import registry as project_registry

    candidate = str(repo or project or "").strip()
    if not candidate:
        raise ValueError("repo is required: name a registered project or a path")
    try:
        entry = project_registry.get_project(candidate)
    except KeyError:
        entry = None
    if entry is not None:
        path = entry.get("path")
        if not path or not Path(str(path)).is_dir():
            raise ValueError(f"project {entry['id']} has no local checkout")
        return str(Path(str(path)).resolve()), entry["id"]
    path = Path(candidate).expanduser()
    if not path.is_dir():
        raise ValueError(f"unknown project or missing folder: {candidate}")
    project_id = str(project).strip() if project else None
    return str(path.resolve()), project_id or None


def _routing_preview() -> dict[str, Any]:
    """Provider picks and cost estimate when cheaply available; never raises."""
    try:
        from agent_os.orchestrator import service

        info = service.providers()
    except Exception:
        return {}
    out: dict[str, Any] = {}
    if isinstance(info, dict):
        picks = info.get("providers") if isinstance(info.get("providers"), list) else info.get("picks")
        if isinstance(picks, list):
            out["providers"] = [
                (p.get("id") or p.get("provider")) if isinstance(p, dict) else p for p in picks
            ]
        for key in ("estimate", "quote", "cost_estimate"):
            if key in info:
                out["cost_estimate"] = info[key]
                break
    return out


def _drive(run_id: str) -> None:
    from agent_os.orchestrator import service

    try:
        service.engine().run_loop(run_id, owner="command-center")
    except Exception:
        pass  # the run records its own failure; the request already returned


def _start(item: dict, params: dict, *, confirm: bool) -> dict:
    goal = params.get("goal")
    goal = goal.strip() if isinstance(goal, str) else ""
    if not goal:
        raise ValueError("goal must be a non-empty string")
    path, project_id = _resolve(params.get("repo"), params.get("project"))
    from agent_os.orchestrator import model_profile

    if not confirm:
        return {
            "goal": goal,
            "repo": path,
            "project": project_id,
            "sensitive": model_profile.is_sensitive({}, path),
            "routing": _routing_preview(),
            "note": PREVIEW_NOTE,
        }
    from agent_os.orchestrator import service

    summary = service.start_recommended(goal, path, project_id, policy={})
    run_id = summary["run_id"]
    threading.Thread(target=_drive, args=(run_id,), name=f"coding-run-{run_id[:8]}", daemon=True).start()
    return {"run_id": run_id, "goal": goal, "repo": path, "project": project_id}


def _run_id(item: dict) -> str:
    run_id = (item.get("context") or {}).get("run_id")
    if not run_id:
        raise ValueError("missing run id")
    return str(run_id)


def _control(action: str):
    def handler(item: dict, params: dict, *, confirm: bool) -> dict:
        run_id = _run_id(item)
        if action == "stop" and not confirm:
            return {"run_id": run_id, "note": "Stops this run; its workers are cancelled and the run cannot be continued."}
        from agent_os.orchestrator import service

        summary = service.control(run_id, action)
        return {"run_id": run_id, "state": summary.get("state"), "paused": summary.get("paused")}

    return handler


def register(reg: registry.Registry) -> None:
    reg.register_action(
        "coding.start", "Start coding task", [],
        _start,
        consequential=True,
        description="Start an orchestrator coding run for a goal in a project or folder (preview first; starts only on Confirm)",
        params_schema={"goal": {"type": "string"}, "repo": {"type": "string"}, "project": {"type": "string"}},
    )
    reg.register_action("coding.pause", "Pause", ["coding_run"], _control("pause"), consequential=False,
                        description="Pause this orchestrator run", params_schema={})
    reg.register_action("coding.resume", "Resume", ["coding_run"], _control("resume"), consequential=False,
                        description="Resume this paused orchestrator run", params_schema={})
    reg.register_action("coding.stop", "Stop", ["coding_run"], _control("stop"), consequential=True,
                        description="Stop this orchestrator run (preview first; stops only on Confirm)", params_schema={})
