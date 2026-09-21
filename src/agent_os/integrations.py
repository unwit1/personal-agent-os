"""Provider-neutral integration health and cooperative lifecycle bridges."""
from __future__ import annotations

import shutil
from collections.abc import Iterable
from typing import Any

from .lifecycle import begin_task
from .routing import status as adapter_status, targets


STATUSES = {"fully_routed", "partially_bridged", "unavailable", "unknown"}


def _surface(
    surface_id: str,
    status: str,
    evidence: list[str],
    limitations: list[str],
    recommended_action: str,
    kind: str,
    provider: str | None = None,
) -> dict[str, Any]:
    if status not in STATUSES:
        raise ValueError("unsupported integration status")
    return {
        "id": surface_id,
        "kind": kind,
        "provider": provider,
        "status": status,
        "evidence": evidence,
        "limitations": limitations,
        "recommended_action": recommended_action,
    }


def _worker_surface(client: str) -> dict[str, Any]:
    available = bool(shutil.which(client))
    return _surface(
        f"worker.{client}",
        "fully_routed" if available else "unavailable",
        [f"{client} executable {'was found' if available else 'was not found'} on PATH."],
        [
            "The wrapper controls Agent OS preflight and postflight, but not the worker's own permissions or host account settings."
        ],
        f"Use agent-os {client} for controlled execution." if available else f"Install or configure {client}, then run agent-os {client}.",
        "controlled_worker",
        client,
    )


def _adapter_surfaces() -> list[dict[str, Any]]:
    current = adapter_status()
    records = []
    for (source, _destination), observed in zip(targets(), current, strict=True):
        matches = bool(observed.get("exists") and observed.get("matches"))
        label = source.parent.name if source.name == "SKILL.md" else source.stem
        records.append(
            _surface(
                f"adapter.{label}",
                "partially_bridged" if matches else "unavailable",
                ["Installed adapter matches its canonical source."] if matches else ["Installed adapter is missing or differs from its canonical source."],
                ["Instruction adapters require client cooperation and cannot intercept direct host execution."],
                "Use the controlled gateway where available; otherwise reconcile the adapter and use integration.bridge_start.",
                "instruction_adapter",
            )
        )
    return records


def _known_surfaces() -> list[dict[str, Any]]:
    surfaces = [
        _surface(
            "gateway.command",
            "fully_routed",
            ["agent-os run owns preflight, worker execution, and postflight or abort transitions."],
            ["A caller must supply a configured worker command."],
            "Use agent-os run for a provider-neutral controlled worker.",
            "controlled_gateway",
        ),
        _worker_surface("codex"),
        _worker_surface("claude"),
        _surface(
            "mcp.lifecycle",
            "partially_bridged",
            ["The MCP server exposes agent.begin_task, agent.continue_task, agent.finish_task, agent.abort_task, and integration.bridge_start."],
            ["An MCP host must configure the server and call these tools; MCP cannot silently wrap an unrelated host conversation."],
            "Configure the local MCP server and have the client call the lifecycle tools or integration.bridge_start.",
            "mcp",
        ),
        _surface(
            "hosted.chatgpt",
            "unavailable",
            ["No host interception API is configured for hosted ChatGPT in this repository."],
            ["Agent OS cannot invisibly intercept a hosted conversation or replace its running model."],
            "Use integration.bridge_start from a cooperative client, or continue through a controlled gateway.",
            "hosted_chat",
        ),
        _surface(
            "hosted.chatgpt_work",
            "unavailable",
            ["No host interception API is configured for ChatGPT Work in this repository."],
            ["Agent OS cannot invisibly intercept a Work task or hot-swap its running model."],
            "Use integration.bridge_start from a cooperative client, or continue through a controlled gateway.",
            "hosted_work",
        ),
    ]
    return [*surfaces, *_adapter_surfaces()]


def health(surface_ids: Iterable[str] | None = None) -> dict[str, Any]:
    """Return deterministic status for every known integration or requested IDs."""
    known = {item["id"]: item for item in _known_surfaces()}
    if isinstance(surface_ids, str):
        raise ValueError("surface ids must be an iterable of IDs, not one string")
    requested = list(surface_ids) if surface_ids is not None else list(known)
    if not all(isinstance(item, str) and item for item in requested):
        raise ValueError("surface ids must be non-empty strings")
    surfaces = [
        known.get(
            surface_id,
            _surface(
                surface_id,
                "unknown",
                ["No integration definition exists for this surface ID."],
                ["No routing or bridge capability can be inferred from an unregistered surface."],
                "Register a provider-neutral integration definition before relying on this surface.",
                "unknown",
            ),
        )
        for surface_id in dict.fromkeys(requested)
    ]
    counts = {status: sum(item["status"] == status for item in surfaces) for status in sorted(STATUSES)}
    return {"schema_version": 1, "surfaces": surfaces, "summary": counts}


def bridge_start(query: str, source_client: str, project_hint: str | None = None, token_budget: int = 1200) -> dict[str, Any]:
    """Start a cooperative task without claiming that the host was intercepted."""
    origin = health([source_client])["surfaces"][0]
    envelope = begin_task(query, source_client, project_hint=project_hint, token_budget=token_budget)
    return {
        "schema_version": 1,
        "bridge": "cooperative",
        "surface": origin,
        "task": {
            "task_id": envelope["task_id"],
            "routing": envelope["routing"],
            "privacy": envelope["privacy"],
            "context_mode": envelope["context_mode"],
            "context": envelope["context"],
            "measurement": envelope["measurement"],
        },
        "limitations": [
            "The cooperating client started this bridge explicitly; Agent OS did not intercept the host conversation.",
            "Finish with agent.finish_task or abort with agent.abort_task; observations are not promoted directly to canonical memory.",
        ],
        "recommended_action": "Continue with the returned task ID and submit structured postflight when the bounded work is complete.",
    }
