"""One facade over the engine for every surface: CLI, MCP, and the local API.

Keeping the surfaces thin means scheduling, routing, gating and validation
policy exist in exactly one place (the engine). Each process holds a single
engine so live worker handles are shared by every caller in that process.
"""

from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any

from ..capabilities import registry_path
from ..storage import write_json
from .engine import Orchestrator


_ENGINE: Orchestrator | None = None
_ENGINE_LOCK = threading.Lock()


def engine() -> Orchestrator:
    global _ENGINE
    with _ENGINE_LOCK:
        if _ENGINE is None:
            _ENGINE = Orchestrator()
        return _ENGINE


def set_engine(value: Orchestrator | None) -> None:
    """Tests and embedding hosts may supply their own engine."""
    global _ENGINE
    with _ENGINE_LOCK:
        _ENGINE = value


# ---------------------------------------------------------------------------
# Providers
# ---------------------------------------------------------------------------


def providers() -> dict[str, Any]:
    return engine().reload_providers()


def suggest_providers(write: bool = False, path: str | None = None, force: bool = False) -> dict[str, Any]:
    """Probe installed coding CLIs and suggest (optionally write) registry entries.

    Existing entries are preserved unless ``force`` is set: the registry is the
    operator's data, and an automatic probe must not silently rewrite it.
    """
    from .adapters import suggested_registry

    suggestion = suggested_registry()
    target = Path(path).expanduser() if path else registry_path()
    result: dict[str, Any] = {"path": str(target), "suggested": suggestion, "written": False}
    if not write:
        return result
    try:
        existing = json.loads(target.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        existing = {}
    current = existing.get("providers") if isinstance(existing.get("providers"), list) else []
    by_id = {str(item.get("id")): item for item in current if isinstance(item, dict)}
    added, kept = [], []
    for entry in suggestion["providers"]:
        clean = {key: value for key, value in entry.items() if not key.startswith("_")}
        if clean["id"] in by_id and not force:
            kept.append(clean["id"])
            continue
        by_id[clean["id"]] = clean
        added.append(clean["id"])
    existing["providers"] = list(by_id.values())
    existing.setdefault("schema_version", 1)
    write_json(target, existing)
    engine().reload_providers()
    result.update({"written": True, "added": added, "kept_existing": kept})
    return result


# ---------------------------------------------------------------------------
# Runs
# ---------------------------------------------------------------------------


def create(
    goal: str,
    repository: str | None = None,
    project: str | None = None,
    tasks: list[dict[str, Any]] | None = None,
    policy: dict[str, Any] | None = None,
    overrides: dict[str, Any] | None = None,
    run_id: str | None = None,
    start: bool = False,
    auto_continue: bool | None = None,
) -> dict[str, Any]:
    orchestrator = engine()
    summary = orchestrator.create_run(
        goal, repository=repository, project=project, tasks=tasks, policy=policy, overrides=overrides, run_id=run_id
    )
    if start or auto_continue is not None:
        summary = orchestrator.start(summary["run_id"], auto_continue)
    return summary


def start_recommended(goal: str, repository: str | None = None, project: str | None = None, policy: dict[str, Any] | None = None) -> dict[str, Any]:
    """Create a planned run with Auto Continue on; the caller then drives it."""
    merged = dict(policy or {})
    merged.setdefault("planning", "auto")
    merged["auto_continue"] = True
    return create(goal, repository=repository, project=project, policy=merged, start=True, auto_continue=True)


def status(run_id: str) -> dict[str, Any]:
    return engine().status(run_id)


def list_runs() -> list[dict[str, Any]]:
    return engine().list_runs()


def step(run_id: str) -> dict[str, Any]:
    return engine().step(run_id)


def advance(run_id: str, max_seconds: float | None = 60.0, max_ticks: int | None = None) -> dict[str, Any]:
    """Drive the run for a bounded time. Honest about what happens next: when
    this call returns, nothing keeps running the run in this process."""
    summary = engine().run_loop(run_id, max_seconds=max_seconds, max_ticks=max_ticks, owner="advance")
    summary["driver_note"] = (
        "this call has returned; unless another orchestrator process is driving the run, "
        "running workers are collected on the next advance/run call"
    )
    return summary


def control(run_id: str, action: str) -> dict[str, Any]:
    orchestrator = engine()
    actions = {
        "start": lambda: orchestrator.start(run_id),
        "pause": lambda: orchestrator.pause(run_id),
        "resume": lambda: orchestrator.resume(run_id),
        "stop": lambda: orchestrator.stop(run_id),
        "auto_continue_on": lambda: orchestrator.set_auto_continue(run_id, True),
        "auto_continue_off": lambda: orchestrator.set_auto_continue(run_id, False),
    }
    if action not in actions:
        raise ValueError(f"unknown control action {action!r}; expected one of {sorted(actions)}")
    return actions[action]()


def decide(run_id: str, gate_id: str, approve: bool, note: str | None = None) -> dict[str, Any]:
    return engine().decide(run_id, gate_id, approve, note)


def retry(run_id: str, node_id: str) -> dict[str, Any]:
    return engine().retry(run_id, node_id)


def reassign(run_id: str, node_id: str, provider: str, model: str | None = None, effort: str | None = None) -> dict[str, Any]:
    return engine().reassign(run_id, node_id, provider, model, effort)


def review_again(run_id: str, node_id: str) -> dict[str, Any]:
    return engine().review_again(run_id, node_id)


def override(
    run_id: str,
    provider: str | None = None,
    model: str | None = None,
    effort: str | None = None,
    role: str | None = None,
    node: str | None = None,
    clear: bool = False,
) -> dict[str, Any]:
    return engine().set_override(run_id, provider=provider, model=model, effort=effort, role=role, node=node, clear=clear)


def result(run_id: str) -> dict[str, Any]:
    return engine().result(run_id)


def events(run_id: str, after_seq: int = 0, limit: int = 200) -> list[dict[str, Any]]:
    return engine().events(run_id, after_seq, limit)


# ---------------------------------------------------------------------------
# MCP registration
# ---------------------------------------------------------------------------


def _schema(properties: dict[str, Any], required: list[str]) -> dict[str, Any]:
    return {"type": "object", "properties": properties, "required": required}


_RUN = {"run_id": {"type": "string"}}

MCP_TOOL_SCHEMAS: dict[str, dict[str, Any]] = {
    "orchestrate.providers": {
        "description": "List configured coding-agent providers, their probe status, and the models the router would choose.",
        "inputSchema": _schema({}, []),
    },
    "orchestrate.create": {
        "description": "Create an orchestrated multi-agent coding run. Omit tasks to let a planner decompose the goal (Start Recommended).",
        "inputSchema": _schema(
            {
                "goal": {"type": "string"},
                "repository": {"type": ["string", "null"]},
                "project": {"type": ["string", "null"]},
                "tasks": {"type": ["array", "null"], "items": {"type": "object"}},
                "policy": {"type": ["object", "null"]},
                "overrides": {"type": ["object", "null"]},
                "run_id": {"type": ["string", "null"]},
                "start": {"type": "boolean", "default": False},
                "auto_continue": {"type": ["boolean", "null"]},
            },
            ["goal"],
        ),
    },
    "orchestrate.status": {"description": "Inspect an orchestrated run: state, agents, validators, findings, gates.", "inputSchema": _schema(_RUN, ["run_id"])},
    "orchestrate.list": {"description": "List orchestrated runs on this machine.", "inputSchema": _schema({}, [])},
    "orchestrate.advance": {
        "description": "Drive a run for a bounded time (Auto Continue runs until complete, paused, gated or blocked). Returns when the bound is reached.",
        "inputSchema": _schema({**_RUN, "max_seconds": {"type": "number", "default": 60}, "max_ticks": {"type": ["integer", "null"]}}, ["run_id"]),
    },
    "orchestrate.control": {
        "description": "Start, pause, resume, stop, or toggle Auto Continue on a run.",
        "inputSchema": _schema({**_RUN, "action": {"type": "string", "enum": ["start", "pause", "resume", "stop", "auto_continue_on", "auto_continue_off"]}}, ["run_id", "action"]),
    },
    "orchestrate.decide": {
        "description": "Approve or reject an open approval gate.",
        "inputSchema": _schema({**_RUN, "gate_id": {"type": "string"}, "approve": {"type": "boolean"}, "note": {"type": ["string", "null"]}}, ["run_id", "gate_id", "approve"]),
    },
    "orchestrate.retry": {"description": "Retry a failed or blocked node.", "inputSchema": _schema({**_RUN, "node_id": {"type": "string"}}, ["run_id", "node_id"])},
    "orchestrate.reassign": {
        "description": "Move a node to another configured provider/model/effort.",
        "inputSchema": _schema({**_RUN, "node_id": {"type": "string"}, "provider": {"type": "string"}, "model": {"type": ["string", "null"]}, "effort": {"type": ["string", "null"]}}, ["run_id", "node_id", "provider"]),
    },
    "orchestrate.review_again": {"description": "Request another independent review of a validated, not-yet-integrated node.", "inputSchema": _schema({**_RUN, "node_id": {"type": "string"}}, ["run_id", "node_id"])},
    "orchestrate.override": {
        "description": "Set a provider/model/effort override for the run, a role, or a node. Never edits manifests.",
        "inputSchema": _schema(
            {**_RUN, "provider": {"type": ["string", "null"]}, "model": {"type": ["string", "null"]}, "effort": {"type": ["string", "null"]}, "role": {"type": ["string", "null"]}, "node": {"type": ["string", "null"]}, "clear": {"type": "boolean", "default": False}},
            ["run_id"],
        ),
    },
    "orchestrate.result": {"description": "Collect the final (or current) result of a run: integration branch, validation, findings, usage.", "inputSchema": _schema(_RUN, ["run_id"])},
}


def mcp_methods() -> dict[str, Any]:
    return {
        "orchestrate.providers": providers,
        "orchestrate.create": create,
        "orchestrate.status": status,
        "orchestrate.list": list_runs,
        "orchestrate.advance": advance,
        "orchestrate.control": control,
        "orchestrate.decide": decide,
        "orchestrate.retry": retry,
        "orchestrate.reassign": reassign,
        "orchestrate.review_again": review_again,
        "orchestrate.override": override,
        "orchestrate.result": result,
    }
