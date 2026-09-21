from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Callable

from .candidates import stage_candidates
from .changes import capture_change, get_change, google_safe_projection, list_changes, promote_change, search_changes, update_change
from .chat import context as chat_context
from .chat import latest_project_handoff, project_status, skills_match
from .compiler import compile_context
from .forms import form_issue_payload, route_form
from .handoffs import create_handoff
from .index import search
from .mail import get_message as mail_get_message, search as mail_search, status as mail_status, sync as mail_sync
from .improvements import capture_improvement, get_improvement, issue_payload, list_improvements, search_improvements, update_improvement
from .registry import get_project, git_status, identify_project, load_state, projects
from .skills import discover, match, metadata
from .contracts import BEGIN_INPUT, CONTINUE_INPUT, FINISH_INPUT, ABORT_INPUT, validate_contract
from .lifecycle import begin_task, continue_task, finish_task, abort_task, task_status


TOOL_SCHEMAS: dict[str, dict[str, Any]] = {
    "agent.begin_task": {"description": "Required preflight for each controlled task, including ordinary prompts. Returns a task ID and selective context.", "inputSchema": BEGIN_INPUT},
    "agent.continue_task": {"description": "Continue an active task with context deltas; reset_context reloads context after compaction; resume reopens an aborted task.", "inputSchema": CONTINUE_INPUT},
    "agent.finish_task": {"description": "Required structured postflight. Stages evidenced sanitized findings, handoff and review status without promoting memory.", "inputSchema": FINISH_INPUT},
    "agent.abort_task": {"description": "Record interrupted or failed work with safe classifications and recovery guidance.", "inputSchema": ABORT_INPUT},
    "agent.task_status": {"description": "Inspect local task status and pending sanitized postflight for recovery.", "inputSchema": {"type": "object", "properties": {"task_id": {"type": "string"}}, "required": ["task_id"], "additionalProperties": False}},
    "agent.context": {
        "description": "Advanced read-only fallback: compact project context. Prefer agent.begin_task for normal work.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The user's technical request."},
                "project_hint": {"type": ["string", "null"]},
                "token_budget": {"type": "integer", "minimum": 250, "default": 2200},
                "include_handoff": {"type": "boolean", "default": True},
            },
            "required": ["query"],
        },
    },
    "agent.capture_candidates": {
        "description": "Stage evidenced durable findings for curation. This never promotes canonical memory.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project": {"type": "string"},
                "task_summary": {"type": "string"},
                "candidates": {"type": "array", "items": {"type": "object"}},
                "source_agent": {"type": ["string", "null"]},
                "source_session": {"type": ["string", "null"]},
            },
            "required": ["project", "task_summary", "candidates"],
        },
    },
    "agent.search": {
        "description": "Run a focused lexical search only when agent.context is insufficient.",
        "inputSchema": {"type": "object", "properties": {"query": {"type": "string"}, "scope": {"type": ["string", "null"]}, "limit": {"type": "integer", "default": 8}}, "required": ["query"]},
    },
    "agent.project_status": {
        "description": "Return compact repository status and freshness without broad retrieval.",
        "inputSchema": {"type": "object", "properties": {"project_hint": {"type": ["string", "null"]}, "query": {"type": "string", "default": ""}}},
    },
    "agent.skills_match": {
        "description": "Return matching skill metadata, not full skill bodies.",
        "inputSchema": {"type": "object", "properties": {"query": {"type": "string"}, "project_hint": {"type": ["string", "null"]}}, "required": ["query"]},
    },
    "agent.latest_handoff": {
        "description": "Retrieve the latest relevant project handoff.",
        "inputSchema": {"type": "object", "properties": {"project_hint": {"type": ["string", "null"]}, "query": {"type": "string", "default": ""}}},
    },
    "change.capture": {
        "description": "Capture one sanitized project change with deterministic deduplication.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project": {"type": "string"}, "title": {"type": "string"}, "request_summary": {"type": "string"},
                "change_type": {"type": "string", "default": "other"}, "components": {"type": "array", "items": {"type": "string"}},
                "repository_files": {"type": "array", "items": {"type": "string"}}, "source_kind": {"type": "string", "default": "chat"},
                "external_key": {"type": ["string", "null"]}, "google_eligible": {"type": "boolean", "default": False},
                "reusable_candidate": {"type": "boolean", "default": False}
            },
            "required": ["project", "title", "request_summary"],
        },
    },
    "improvement.capture": {
        "description": "Capture a compact evidence-backed improvement candidate; never verified memory.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project": {"type": "string"}, "title": {"type": "string"}, "category": {"type": "string"},
                "observation": {"type": "string"}, "suggested_direction": {"type": "string"},
                "acceptance": {"type": "array", "items": {"type": "string"}}, "subsystem": {"type": ["string", "null"]},
                "priority": {"type": "string", "default": "medium"}, "evidence": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["project", "title", "category", "observation", "suggested_direction", "acceptance"],
        },
    },
    "mail.search": {
        "description": "Search the local read-only personal mail index and return compact relevant snippets.",
        "inputSchema": {"type": "object", "properties": {"query": {"type": "string"}, "limit": {"type": "integer", "default": 10}}, "required": ["query"]},
    },
    "mail.get_message": {
        "description": "Get one message already present in the local mail index. Full body is opt-in.",
        "inputSchema": {"type": "object", "properties": {"uid": {"type": "string"}, "mailbox": {"type": "string", "default": "INBOX"}, "include_body": {"type": "boolean", "default": False}}, "required": ["uid"]},
    },
    "mail.sync_status": {
        "description": "Return local iCloud Mail configuration/index status without exposing credentials.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    "mail.sync": {
        "description": "Incrementally synchronize recent iCloud messages into the local read-only index.",
        "inputSchema": {"type": "object", "properties": {"limit": {"type": "integer", "default": 500}}},
    },
    "form.route": {
        "description": "Route a sanitized work-form fingerprint; persistence is local-only and explicit.",
        "inputSchema": {"type": "object", "properties": {"candidate": {"type": "object"}, "persist": {"type": "boolean", "default": False}, "queue_dir": {"type": ["string", "null"]}}, "required": ["candidate"]},
    },
}


def methods() -> dict[str, Callable[..., Any]]:
    available = {
        "agent.begin_task": begin_task,
        "agent.continue_task": continue_task,
        "agent.finish_task": lambda task_id, postflight: finish_task(task_id, postflight),
        "agent.abort_task": abort_task,
        "agent.task_status": task_status,
        "project.list": lambda: projects(),
        "project.identify": lambda path: identify_project(Path(path)),
        "project.status": lambda project: {"state": load_state(get_project(project)), "git": git_status(get_project(project))},
        "project.context": compile_context,
        "memory.search": search,
        "skill.search": lambda query, project=None: [
            metadata(skill)
            for skill in match(
                query,
                discover(
                    Path(get_project(project)["path"]) if project else None,
                    load_state(get_project(project)).get("skill_roots", []) if project else (),
                ),
            )
        ],
        "agent.start_session": compile_context,
        "agent.finish_session": create_handoff,
        "change.capture": capture_change,
        "change.get": get_change,
        "change.list": list_changes,
        "change.update": update_change,
        "change.search": search_changes,
        "change.for_project": search_changes,
        "change.verify": lambda project, change_id, validation_summary, tests: update_change(project, change_id, status="VERIFIED", validation_summary=validation_summary, implementation={"tests": tests}),
        "change.promote": promote_change,
        "change.google_safe_projection": google_safe_projection,
        "improvement.capture": capture_improvement,
        "improvement.get": get_improvement,
        "improvement.list": list_improvements,
        "improvement.update": update_improvement,
        "improvement.search": search_improvements,
        "improvement.issue_payload": issue_payload,
        "mail.search": mail_search,
        "mail.get_message": mail_get_message,
        "mail.sync_status": mail_status,
        "mail.sync": mail_sync,
        "form.route": route_form,
        "form.issue_payload": form_issue_payload,
    }
    # Retain legacy aliases; lifecycle tools own normal orchestration.
    available.update(
        {
            "agent.context": chat_context,
            "agent.capture_candidates": lambda project=None, project_id=None, task_summary="", candidates=(), source_agent=None, source_session=None: stage_candidates(project_id or project or "", task_summary, candidates, source_agent, source_session),
            "agent.search": search,
            "agent.project_status": project_status,
            "agent.skills_match": skills_match,
            "agent.latest_handoff": latest_project_handoff,
        }
    )
    return available


def _mcp_result(value: Any, error: bool = False) -> dict[str, Any]:
    return {"content": [{"type": "text", "text": json.dumps(value, default=str, ensure_ascii=False)}], "isError": error}


def _handle_mcp(request: dict[str, Any], available: dict[str, Callable[..., Any]]) -> dict[str, Any] | None:
    method = request.get("method")
    request_id = request.get("id")
    if method == "notifications/initialized":
        return None
    if method == "initialize":
        params = request.get("params", {})
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocolVersion": params.get("protocolVersion", "2025-06-18"),
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": {"name": "personal-agent-os", "version": "0.1.0"},
                "instructions": "Mandatory controlled lifecycle: agent.begin_task -> work -> agent.finish_task; agent.continue_task adds a turn and agent.abort_task records failure. Every prompt receives an envelope; ordinary prompts load no project context. Follow project-local policy. Postflight contains sanitized engineering summaries, evidence and validation, never raw history or hidden chain-of-thought. MCP instructions require client cooperation; only the controlled gateway technically wraps execution.",
            },
        }
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": request_id, "result": {"tools": [{"name": name, **schema} for name, schema in TOOL_SCHEMAS.items()]}}
    if method == "tools/call":
        params = request.get("params", {})
        name = params.get("name")
        if name not in TOOL_SCHEMAS or name not in available:
            return {"jsonrpc": "2.0", "id": request_id, "result": _mcp_result({"error": f"Unknown tool: {name}"}, error=True)}
        try:
            arguments = params.get("arguments", {})
            if not isinstance(arguments, dict):
                raise ValueError("tool arguments must be an object")
            if name in {"agent.begin_task", "agent.continue_task", "agent.finish_task", "agent.abort_task", "agent.task_status"}:
                validate_contract(arguments, TOOL_SCHEMAS[name]["inputSchema"], "arguments")
            return {"jsonrpc": "2.0", "id": request_id, "result": _mcp_result(available[name](**arguments))}
        except Exception as exc:
            message = "Lifecycle request failed; check arguments and task status" if name in {"agent.begin_task", "agent.continue_task", "agent.finish_task", "agent.abort_task", "agent.task_status"} else str(exc)
            return {"jsonrpc": "2.0", "id": request_id, "result": _mcp_result({"error": message}, error=True)}
    return None


def serve() -> int:
    available = methods()
    for line in sys.stdin:
        try:
            request = json.loads(line)
            method = request.get("method")
            mcp_response = _handle_mcp(request, available)
            if mcp_response is not None:
                print(json.dumps(mcp_response, default=str), flush=True)
                continue
            if method == "notifications/initialized":
                continue
            if method == "rpc.discover":
                result = sorted(available)
            elif method not in available:
                raise KeyError(f"Unknown method: {method}")
            else:
                params = request.get("params", {})
                result = available[method](**params) if isinstance(params, dict) else available[method](*params)
            response = {"jsonrpc": "2.0", "id": request.get("id"), "result": result}
        except Exception as exc:
            response = {"jsonrpc": "2.0", "id": None, "error": {"code": -32000, "message": str(exc)}}
        print(json.dumps(response, default=str), flush=True)
    return 0
