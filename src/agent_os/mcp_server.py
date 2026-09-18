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
from .improvements import capture_improvement, get_improvement, issue_payload, list_improvements, search_improvements, update_improvement
from .registry import get_project, git_status, identify_project, load_state, projects
from .skills import discover, match, metadata


TOOL_SCHEMAS: dict[str, dict[str, Any]] = {
    "agent.context": {
        "description": "Resolve one likely project and return a compact, token-budgeted context packet. Use this first for substantial project work.",
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
    "form.route": {
        "description": "Route a sanitized work-form fingerprint; persistence is local-only and explicit.",
        "inputSchema": {"type": "object", "properties": {"candidate": {"type": "object"}, "persist": {"type": "boolean", "default": False}, "queue_dir": {"type": ["string", "null"]}}, "required": ["candidate"]},
    },
}


def methods() -> dict[str, Callable[..., Any]]:
    available = {
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
        "form.route": route_form,
        "form.issue_payload": form_issue_payload,
    }
    # These aliases are deliberately small: regular-chat clients should normally
    # need only agent.context and agent.capture_candidates.
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
                "instructions": "Use agent.context first for substantial project work. It retrieves compact context only. Use agent.capture_candidates to stage evidence-backed findings; it never promotes canonical memory.",
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
            return {"jsonrpc": "2.0", "id": request_id, "result": _mcp_result(available[name](**arguments))}
        except Exception as exc:
            return {"jsonrpc": "2.0", "id": request_id, "result": _mcp_result({"error": str(exc)}, error=True)}
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
