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
from .coordination import (
    check as check_claims,
    claim as make_claim,
    heartbeat as claim_heartbeat,
    message as claim_message,
    release as release_claim,
    acknowledge as acknowledge_note,
    claim_task,
    complete_task,
    delegate,
    inbox as work_inbox,
    list_reviews,
    list_tasks,
    note as work_note,
    request_review,
    requeue_task,
    submit_review,
    status as claims_status,
)
from .documents import cache_status_safe
from .forms import form_issue_payload, route_form
from .handoffs import create_handoff
from .index import search
from .orchestrator.service import MCP_TOOL_SCHEMAS as ORCHESTRATE_TOOL_SCHEMAS
from .orchestrator.service import mcp_methods as orchestrate_methods
from .mail import account_status as mail_account_status, get_message as mail_get_message, get_thread as mail_get_thread, list_accounts as mail_accounts, search as mail_search, status as mail_status, sync as mail_sync
from .improvements import capture_improvement, get_improvement, issue_payload, list_improvements, search_improvements, update_improvement
from .profile import compact_profile as profile_retrieve, profile_status
from .registry import get_project, git_status, identify_project, load_state, projects
from .skills import discover, match, metadata
from .workflows import (
    complete_stage as workflow_complete_stage,
    list_runs as workflow_list_runs,
    list_workflows,
    prepare_stage as workflow_prepare_stage,
    run_stage as workflow_run_stage,
    start as workflow_start,
    status as workflow_status,
)


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
    "work.check": {
        "description": "Before editing, see which other agents have announced work overlapping your scope. Announces nothing.",
        "inputSchema": {"type": "object", "properties": {"project": {"type": "string"}, "scope": {"type": "array", "items": {"type": "string"}}}, "required": ["project"]},
    },
    "work.claim": {
        "description": "Announce what you are about to work on and receive any overlapping claims. Advisory: it records and reports, it does not lock.",
        "inputSchema": {"type": "object", "properties": {"project": {"type": "string"}, "task": {"type": "string"}, "agent": {"type": "string"}, "scope": {"type": "array", "items": {"type": "string"}}, "lease_minutes": {"type": "integer", "default": 90}}, "required": ["project", "task", "agent"]},
    },
    "work.note": {
        "description": "Leave a note for whoever works this project next, even if no agent has claimed it. Use when the agent you need to reach never announced itself.",
        "inputSchema": {"type": "object", "properties": {"project": {"type": "string"}, "text": {"type": "string"}, "sender": {"type": "string"}, "about": {"type": ["string", "null"]}}, "required": ["project", "text", "sender"]},
    },
    "work.inbox": {
        "description": "Read notes other agents left for this project. Check this before starting work.",
        "inputSchema": {"type": "object", "properties": {"project": {"type": ["string", "null"]}, "include_acknowledged": {"type": "boolean", "default": False}}},
    },
    "work.acknowledge": {
        "description": "Mark a note read, optionally replying, so it stops being repeated.",
        "inputSchema": {"type": "object", "properties": {"note_id": {"type": "string"}, "agent": {"type": "string"}, "reply": {"type": ["string", "null"]}}, "required": ["note_id", "agent"]},
    },
    "work.status": {
        "description": "List work other agents are doing right now on this machine.",
        "inputSchema": {"type": "object", "properties": {"project": {"type": ["string", "null"]}}},
    },
    "work.heartbeat": {
        "description": "Keep a claim alive during long work and collect replies from other agents.",
        "inputSchema": {"type": "object", "properties": {"claim_id": {"type": "string"}}, "required": ["claim_id"]},
    },
    "work.release": {
        "description": "Release a claim when the work is finished.",
        "inputSchema": {"type": "object", "properties": {"claim_id": {"type": "string"}, "note": {"type": ["string", "null"]}}, "required": ["claim_id"]},
    },
    "work.message": {
        "description": "Leave a note for the agent holding a claim, so overlapping work is negotiated rather than raced.",
        "inputSchema": {"type": "object", "properties": {"claim_id": {"type": "string"}, "text": {"type": "string"}, "sender": {"type": "string"}}, "required": ["claim_id", "text", "sender"]},
    },
    "work.delegate": {
        "description": "Create an idempotent delegated task with optional scope, assignee, and task dependencies.",
        "inputSchema": {"type": "object", "properties": {"project": {"type": "string"}, "task_key": {"type": "string"}, "title": {"type": "string"}, "requester": {"type": "string"}, "assignee": {"type": ["string", "null"]}, "scope": {"type": "array", "items": {"type": "string"}}, "depends_on": {"type": "array", "items": {"type": "string"}}, "review_required": {"type": "boolean", "description": "Require an approved independent peer review before completion."}}, "required": ["project", "task_key", "title", "requester"]},
    },
    "work.tasks": {
        "description": "List local delegated tasks and their resumable status.",
        "inputSchema": {"type": "object", "properties": {"project": {"type": ["string", "null"]}, "status": {"type": ["string", "null"]}}},
    },
    "work.task_claim": {
        "description": "Claim a delegated task when its dependencies are complete.",
        "inputSchema": {"type": "object", "properties": {"task_id": {"type": "string"}, "agent": {"type": "string"}}, "required": ["task_id", "agent"]},
    },
    "work.task_complete": {
        "description": "Complete a delegated task with validation evidence from its assigned agent.",
        "inputSchema": {"type": "object", "properties": {"task_id": {"type": "string"}, "agent": {"type": "string"}, "validation": {"type": "string"}, "result": {"type": ["string", "null"]}}, "required": ["task_id", "agent", "validation"]},
    },
    "work.task_requeue": {
        "description": "Return interrupted in-progress delegated work to the queue without deleting task or review records.",
        "inputSchema": {"type": "object", "properties": {"task_id": {"type": "string"}, "agent": {"type": "string"}, "reason": {"type": "string"}}, "required": ["task_id", "agent", "reason"]},
    },
    "work.review_request": {
        "description": "Create an idempotent peer-review request linked to exactly one delegated task ID or commit fingerprint.",
        "inputSchema": {"type": "object", "properties": {"project": {"type": "string"}, "review_key": {"type": "string"}, "requester": {"type": "string"}, "task_id": {"type": ["string", "null"]}, "commit_fingerprint": {"type": ["string", "null"]}, "reviewer": {"type": ["string", "null"]}, "changed_files": {"type": "array", "items": {"type": "string"}}}, "required": ["project", "review_key", "requester"]},
    },
    "work.reviews": {
        "description": "List bounded peer-review requests and independent verdict metadata.",
        "inputSchema": {"type": "object", "properties": {"project": {"type": ["string", "null"]}, "status": {"type": ["string", "null"]}}},
    },
    "work.review_submit": {
        "description": "Submit one independent peer-review verdict with bounded findings and validation evidence.",
        "inputSchema": {"type": "object", "properties": {"review_id": {"type": "string"}, "reviewer": {"type": "string"}, "verdict": {"type": "string"}, "validation": {"type": "string"}, "findings": {"type": "array", "items": {"type": "string"}}}, "required": ["review_id", "reviewer", "verdict", "validation"]},
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
    "mail.accounts": {
        "description": "List configured mail accounts (iCloud, EarthLink, ...) with provider, read-only state and whether a credential is available. Never returns credentials.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    "mail.account_status": {
        "description": "One mail account: last authentication result, mailboxes, last sync, counts, capability mode, sanitized errors.",
        "inputSchema": {"type": "object", "properties": {"account_id": {"type": "string"}}, "required": ["account_id"]},
    },
    "mail.search": {
        "description": "Search the local read-only mail index across accounts and archives. Returns compact results with stable ids (msg_...), thread ids and source attribution (account:mailbox). Filters are optional.",
        "inputSchema": {"type": "object", "properties": {
            "query": {"type": "string", "description": "words to match (all must appear); empty lists recent mail"},
            "limit": {"type": "integer", "default": 10},
            "accounts": {"type": "array", "items": {"type": "string"}}, "providers": {"type": "array", "items": {"type": "string"}},
            "mailboxes": {"type": "array", "items": {"type": "string"}}, "source_kinds": {"type": "array", "items": {"type": "string"}, "description": "live_imap, pst_archive"},
            "sender": {"type": "string"}, "recipient": {"type": "string"},
            "after": {"type": "string", "description": "ISO date, inclusive"}, "before": {"type": "string", "description": "ISO date, exclusive"}},
            "required": ["query"]},
    },
    "mail.get_message": {
        "description": "Get one indexed message by stable id (msg_...), or by uid + mailbox (+ account_id). Full body is opt-in.",
        "inputSchema": {"type": "object", "properties": {
            "id": {"type": "string"}, "uid": {"type": "string"}, "mailbox": {"type": "string", "default": "INBOX"}, "account_id": {"type": "string"},
            "include_body": {"type": "boolean", "default": False}, "include_sources": {"type": "boolean", "default": True}, "include_attachments": {"type": "boolean", "default": True}}},
    },
    "mail.get_thread": {
        "description": "Get a conversation (References/In-Reply-To) by thread id (thr_...) or any message id in it. Bodies are opt-in.",
        "inputSchema": {"type": "object", "properties": {"thread_id": {"type": "string"}, "message_id": {"type": "string"}, "include_body": {"type": "boolean", "default": False}, "limit": {"type": "integer", "default": 50}}},
    },
    "mail.sync_status": {
        "description": "Mail sync status for every account (or one account_id): configured, credential available, authentication, last sync, caught up, capability mode. Never exposes credentials.",
        "inputSchema": {"type": "object", "properties": {"account_id": {"type": "string"}}},
    },
    "mail.sync": {
        "description": "Incrementally synchronize mail into the local read-only index: one account_id, or all enabled accounts. New messages up to limit per mailbox; backfill pulls that many older ones.",
        "inputSchema": {"type": "object", "properties": {"account_id": {"type": "string"}, "mailbox": {"type": "string"}, "limit": {"type": "integer", "default": 200}, "backfill": {"type": "integer", "default": 0}}},
    },
    "document.cache_status": {
        "description": "Report local document-cache size and age as counts only. The cache is workstation-local and its contents are never returned.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    "profile.retrieve": {
        "description": "Retrieve only the durable personal-profile slice a task touches, with diagnostics. Never returns the whole profile.",
        "inputSchema": {"type": "object", "properties": {"task": {"type": "string"}, "limit": {"type": "integer", "default": 5}, "minimum_score": {"type": "integer", "default": 3}}, "required": ["task"]},
    },
    "profile.status": {
        "description": "Describe what profile context is indexed, by domain, without returning the profile itself.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    "workflow.list": {
        "description": "List available staged workflow manifests.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    "workflow.start": {
        "description": "Start or resume a staged workflow run. Resuming an existing run is idempotent.",
        "inputSchema": {"type": "object", "properties": {"workflow_id": {"type": "string"}, "run_id": {"type": ["string", "null"]}}, "required": ["workflow_id"]},
    },
    "workflow.next": {
        "description": "Answer 'what do I run next?' from persisted stage state: the next stage, its provider-neutral capability class, and a ready-to-paste prompt.",
        "inputSchema": {"type": "object", "properties": {"workflow_id": {"type": "string"}, "run_id": {"type": "string"}}, "required": ["workflow_id", "run_id"]},
    },
    "workflow.stage": {
        "description": "Compile one stage's own token-budgeted context packet. Carries no previous transcript.",
        "inputSchema": {"type": "object", "properties": {"workflow_id": {"type": "string"}, "run_id": {"type": "string"}, "stage_id": {"type": ["string", "null"]}}, "required": ["workflow_id", "run_id"]},
    },
    "workflow.run_stage": {
        "description": "Advance one stage. Deterministic stages execute and validate locally; others are prepared and handed back with a recommended capability class.",
        "inputSchema": {"type": "object", "properties": {"workflow_id": {"type": "string"}, "run_id": {"type": "string"}, "stage_id": {"type": ["string", "null"]}}, "required": ["workflow_id", "run_id"]},
    },
    "workflow.complete_stage": {
        "description": "Record an agent-run stage outcome. The declared validator, not the caller's confidence, decides whether it passed.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "workflow_id": {"type": "string"},
                "run_id": {"type": "string"},
                "stage_id": {"type": "string"},
                "outputs": {"type": "array", "items": {"type": "string"}},
                "checkpoint": {"type": ["string", "null"]},
                "passed": {"type": ["boolean", "null"]},
                "detail": {"type": ["string", "null"]},
            },
            "required": ["workflow_id", "run_id", "stage_id"],
        },
    },
    "workflow.runs": {
        "description": "List staged workflow runs recorded for a project.",
        "inputSchema": {"type": "object", "properties": {"project_id": {"type": "string"}}, "required": ["project_id"]},
    },
    "form.route": {
        "description": "Route a sanitized work-form fingerprint; persistence is local-only and explicit.",
        "inputSchema": {"type": "object", "properties": {"candidate": {"type": "object"}, "persist": {"type": "boolean", "default": False}, "queue_dir": {"type": ["string", "null"]}}, "required": ["candidate"]},
    },
}

TOOL_SCHEMAS.update(ORCHESTRATE_TOOL_SCHEMAS)


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
        "mail.accounts": mail_accounts,
        "mail.account_status": mail_account_status,
        "mail.search": mail_search,
        "mail.get_message": mail_get_message,
        "mail.get_thread": mail_get_thread,
        "mail.sync_status": mail_status,
        "mail.sync": mail_sync,
        "document.cache_status": cache_status_safe,
        "profile.retrieve": profile_retrieve,
        "profile.status": profile_status,
        "workflow.list": list_workflows,
        "workflow.start": lambda workflow_id, run_id=None: workflow_start(workflow_id, run_id),
        "workflow.next": workflow_status,
        "workflow.stage": workflow_prepare_stage,
        "workflow.run_stage": workflow_run_stage,
        "workflow.complete_stage": workflow_complete_stage,
        "workflow.runs": workflow_list_runs,
        "form.route": route_form,
        "form.issue_payload": form_issue_payload,
    }
    # These aliases are deliberately small: regular-chat clients should normally
    # need only agent.context and agent.capture_candidates.
    available.update(
        {
            "agent.context": chat_context,
            "work.check": check_claims,
            "work.claim": make_claim,
            "work.status": claims_status,
            "work.note": work_note,
            "work.inbox": work_inbox,
            "work.acknowledge": acknowledge_note,
            "work.heartbeat": claim_heartbeat,
            "work.release": release_claim,
            "work.message": claim_message,
            "work.delegate": delegate,
            "work.tasks": list_tasks,
            "work.task_claim": claim_task,
            "work.task_complete": complete_task,
            "work.task_requeue": requeue_task,
            "work.review_request": request_review,
            "work.reviews": list_reviews,
            "work.review_submit": submit_review,
            "agent.capture_candidates": lambda project=None, project_id=None, task_summary="", candidates=(), source_agent=None, source_session=None: stage_candidates(project_id or project or "", task_summary, candidates, source_agent, source_session),
            "agent.search": search,
            "agent.project_status": project_status,
            "agent.skills_match": skills_match,
            "agent.latest_handoff": latest_project_handoff,
        }
    )
    available.update(orchestrate_methods())
    return available


SERVER_INFO = {"name": "personal-agent-os", "version": "0.1.0"}
SERVER_CAPABILITIES = {"tools": {"listChanged": False}}
# Newest first. `initialize` echoes the client's version when it is supported and
# otherwise offers the newest one, which is what the MCP lifecycle requires.
SUPPORTED_PROTOCOL_VERSIONS = ("2025-06-18", "2025-03-26", "2024-11-05")
INSTRUCTIONS = (
    "Use agent.context first for substantial project work. It retrieves compact context only. "
    "Use agent.capture_candidates to stage evidence-backed findings; it never promotes canonical memory."
)


def negotiate_protocol_version(requested: Any) -> str:
    return requested if requested in SUPPORTED_PROTOCOL_VERSIONS else SUPPORTED_PROTOCOL_VERSIONS[0]


def _mcp_result(value: Any, error: bool = False) -> dict[str, Any]:
    return {"content": [{"type": "text", "text": json.dumps(value, default=str, ensure_ascii=False)}], "isError": error}


def _ok(request_id: Any, result: Any) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def _handle_mcp(request: dict[str, Any], available: dict[str, Callable[..., Any]]) -> dict[str, Any] | None:
    method = request.get("method")
    request_id = request.get("id")
    # Notifications carry no id and must never get a response.
    if isinstance(method, str) and method.startswith("notifications/"):
        return None
    if method == "initialize":
        params = request.get("params", {})
        requested = params.get("protocolVersion") if isinstance(params, dict) else None
        return _ok(
            request_id,
            {
                "protocolVersion": negotiate_protocol_version(requested),
                "capabilities": SERVER_CAPABILITIES,
                "serverInfo": SERVER_INFO,
                "instructions": INSTRUCTIONS,
            },
        )
    if method == "server/discover":
        # Additive discovery alias. It reports the same identity and capabilities
        # as `initialize` so no client needs a provider-specific code path.
        return _ok(
            request_id,
            {
                "protocolVersion": SUPPORTED_PROTOCOL_VERSIONS[0],
                "supportedVersions": list(SUPPORTED_PROTOCOL_VERSIONS),
                "capabilities": SERVER_CAPABILITIES,
                "serverInfo": SERVER_INFO,
                "instructions": INSTRUCTIONS,
            },
        )
    if method == "ping":
        return _ok(request_id, {})
    if method == "tools/list":
        return _ok(request_id, {"tools": [{"name": name, **schema} for name, schema in TOOL_SCHEMAS.items()]})
    if method == "tools/call":
        params = request.get("params", {})
        name = params.get("name") if isinstance(params, dict) else None
        if name not in TOOL_SCHEMAS or name not in available:
            return _ok(request_id, _mcp_result({"error": f"Unknown tool: {name}"}, error=True))
        try:
            arguments = params.get("arguments", {})
            if arguments is None:
                arguments = {}
            if not isinstance(arguments, dict):
                raise ValueError("tool arguments must be an object")
            return _ok(request_id, _mcp_result(available[name](**arguments)))
        except Exception as exc:
            return _ok(request_id, _mcp_result({"error": str(exc)}, error=True))
    if isinstance(method, str) and (method.startswith(("resources/", "prompts/", "completion/", "logging/")) or method == "tools/listChanged"):
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {"code": -32601, "message": f"Method not supported: {method}"},
        }
    return None


def serve() -> int:
    available = methods()
    for line in sys.stdin:
        if not line.strip():
            continue
        request_id = None
        try:
            request = json.loads(line)
            if not isinstance(request, dict):
                raise ValueError("request must be a JSON-RPC object")
            request_id = request.get("id")
            method = request.get("method")
            mcp_response = _handle_mcp(request, available)
            if mcp_response is not None:
                print(json.dumps(mcp_response, default=str), flush=True)
                continue
            if isinstance(method, str) and method.startswith("notifications/"):
                continue
            if method == "rpc.discover":
                result = sorted(available)
            elif method not in available:
                raise KeyError(f"Unknown method: {method}")
            else:
                params = request.get("params", {})
                result = available[method](**params) if isinstance(params, dict) else available[method](*params)
            response = {"jsonrpc": "2.0", "id": request_id, "result": result}
        except json.JSONDecodeError as exc:
            response = {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": str(exc)}}
        except KeyError as exc:
            response = {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32601, "message": str(exc)}}
        except Exception as exc:
            response = {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32000, "message": str(exc)}}
        if request_id is None and "error" not in response:
            continue
        print(json.dumps(response, default=str), flush=True)
    return 0
