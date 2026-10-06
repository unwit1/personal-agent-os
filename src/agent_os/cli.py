from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .adapters import sync_adapters
from .browser_bridge import BridgeStore
from .browser_control import command_status as browser_command_status
from .browser_control import execute as browser_execute
from .browser_control import sessions as browser_sessions
from .browser_bridge_server import (
    DEFAULT_HOST as BROWSER_BRIDGE_HOST,
    DEFAULT_PORT as BROWSER_BRIDGE_PORT,
    TOKEN_PATH as BROWSER_BRIDGE_TOKEN_PATH,
    load_or_create_token as browser_bridge_token,
    serve as serve_browser_bridge,
)
from .candidates import candidate_status, curate_candidates, stage_candidates
from .changes import capture_change, get_change, google_safe_projection, list_changes, promote_change, update_change
from .compiler import compile_context
from .connectors import connector_conflicts, connector_credential_status, connector_events, connector_import_candidates, connector_provisioning_readiness, connector_reconcile_plan, connector_subscriber_ack, connector_subscriber_poll, import_connector_candidate, prune_stale_registrations, register_connector, set_registration_state, unregister_connector, verify_native_registrations
from .creator_profiles import (
    list_profiles as creator_list_profiles,
    pending_discovery as creator_pending_discovery,
    record_discovery as creator_record_discovery,
)
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
    list_tasks,
    list_reviews,
    note as work_note,
    request_review,
    requeue_task,
    submit_review,
    status as claims_status,
)
from ingester_engine.cache import DocumentCache
from .forms import form_issue_payload, route_form
from .handoffs import create_handoff
from .index import rebuild, search
from .inventory import scan
from .improvements import capture_improvement, get_improvement, issue_payload, list_improvements, search_improvements, update_improvement
from .launcher import install as install_launcher
from .launcher import status as launcher_status
from .launcher import verify as verify_launcher
from .machine import describe as describe_machine
from .machine import write_override
from .orchestrator.cli import dispatch as dispatch_orchestrate
from .orchestrator.cli import register as register_orchestrate
from .mcp_server import serve
from .maintenance import run as run_maintenance
from .recovery import get_checkpoint, inspect_recovery, list_checkpoints, resume_recovery
from .mail import cli as mail_cli
from .profile import compact_profile, profile_status
from .registry import get_project, git_status, identify_project, load_state, projects
from .review import assess
from .surfaces import health as integration_health
from .telemetry import LocalTelemetryStore, REPORT_GROUP_FIELDS, PROVIDER_USAGE_FORMATS, TelemetryEvent, token_counts_from_provider_usage
from .routing import install as install_routing
from .routing import status as routing_status
from .validation import validate
from .watching import add_target as watch_add_target, list_targets as watch_list_targets, remove_target as watch_remove_target
from .workflows import (
    complete_stage,
    list_runs,
    list_workflows,
    prepare_stage,
    run_stage,
    start as start_workflow,
    status as workflow_status,
)


def _print(value: object) -> None:
    print(json.dumps(value, indent=2, default=str, ensure_ascii=False))


def _load_object(path: str) -> dict:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("JSON input must be an object")
    return value


def _json_input(value: str) -> object:
    """Structured input: an inline JSON document or a path to a JSON file."""
    text = value.strip()
    if text[:1] not in ("[", "{", '"'):
        text = Path(value).read_text(encoding="utf-8")
    return json.loads(text)


def _executive_gateway():
    from .executive.gateway import LocalDashboardGateway

    return LocalDashboardGateway()


def _executive_store():
    from .executive import outbox

    return outbox.OutboxStore()


def _executive_event_bus():
    from .executive.event_bus import EventBus

    return EventBus()


def _project_deferral_counts() -> dict:
    try:
        from .executive import window_queue

        return window_queue.project_deferral_counts(_executive_event_bus())
    except Exception:
        return {}


def _executive_today_and_stale_days(args):
    """Resolve the --today and --stale-days options shared by executive commands."""
    from datetime import date
    from .executive import project_actions

    today = date.fromisoformat(args.today) if args.today else date.today()
    stale_days = args.stale_days if args.stale_days is not None else project_actions.STALE_DAYS_DEFAULT
    return today, stale_days


def _executive_window_queue(tab: str | None = None):
    from .executive.window.builtin import default_registry
    from .executive.window.confirm import ItemState, window_home

    return default_registry().queue(tab, state=ItemState(window_home()))


def _register_executive(commands) -> None:
    executive = commands.add_parser("executive")
    sub = executive.add_subparsers(dest="executive_command", required=True)
    route = sub.add_parser("route")
    route.add_argument("--consumer", default="router")
    route.add_argument("--rules", help="JSON object mapping event types to dispositions, inline or a file path")
    route_reason = sub.add_parser("route-reason")
    route_reason.add_argument("event_id")
    needs = sub.add_parser("needs-action")
    needs.add_argument("--limit", type=int, default=100)
    suggest = sub.add_parser("suggestions")
    suggest.add_argument("opening")
    plan = sub.add_parser("plan")
    plan.add_argument("--opening", required=True)
    plan.add_argument("--applicant-refs", required=True, help="JSON list of applicant_ref values, inline or a file path")
    plan.add_argument("--interview-type", required=True)
    plan.add_argument("--location", required=True)
    plan.add_argument("--duration-minutes", type=int, default=30)
    inspect = sub.add_parser("batch")
    inspect.add_argument("batch_id")
    approve = sub.add_parser("approve")
    approve.add_argument("batch_id")
    approve.add_argument(
        "--choices", required=True,
        help='JSON object: applicant_ref -> "confirm" | "drop" | [slot datetimes], inline or a file path',
    )
    send = sub.add_parser("send")
    send.add_argument("batch_id")
    send.add_argument("--confirm", action="store_true", help="actually send; without it the send is a dry-run")
    window = sub.add_parser("window")
    window.add_argument("--port", type=int, default=8770)
    window.add_argument("--no-open", action="store_true")
    next_action = sub.add_parser("next")
    next_action.add_argument("--tab", choices=["work", "personal"], default=None)
    explain = sub.add_parser("explain")
    explain.add_argument("item_id")
    explain.add_argument("--tab", choices=["work", "personal"], default=None)
    history = sub.add_parser("history")
    history.add_argument("item_id")
    history.add_argument("--tab", choices=["work", "personal"], default=None)
    project_next = sub.add_parser("project-next")
    project_next.add_argument("project")
    project_next.add_argument("--stale-days", type=int, default=None)
    project_next.add_argument("--today", type=str, default=None)
    project_scan = sub.add_parser("project-scan")
    project_scan.add_argument("--stale-days", type=int, default=None)
    project_scan.add_argument("--today", type=str, default=None)
    project_scan.add_argument("--all", action="store_true")
    rescue = sub.add_parser("rescue")
    rescue.add_argument("--tab", choices=["work", "personal"], default=None)
    rescue.add_argument("--today", type=str, default=None)
    rescue.add_argument("--stale-days", type=int, default=None)
    rescue.add_argument("--horizon-days", type=int, default=1)
    resume = sub.add_parser("resume")
    resume.add_argument("project")
    resume.add_argument("--today", type=str, default=None)
    resume.add_argument("--stale-days", type=int, default=None)
    brain_dump = sub.add_parser("brain-dump")
    brain_dump.add_argument("text", nargs="?", default=None)
    brain_dump.add_argument("--file", type=Path, default=None)
    brain_dump.add_argument("--stage-candidates", default=None)
    gaps = sub.add_parser("gaps")
    gaps.add_argument("gaps_json", help="JSON list of knowledge gaps, inline or a file path")
    gaps.add_argument("--budget", type=int, default=1)
    gaps.add_argument("--min-score", type=float, default=0.2)
    gaps.add_argument("--asked-id", action="append", default=[])
    gaps.add_argument("--enqueue", action="store_true")
    gaps.add_argument("--tab", choices=["work", "personal"], default="personal")
    gap_answer = sub.add_parser("gap-answer")
    gap_answer.add_argument("gap_id")
    gap_answer.add_argument("--answer", required=True)
    gap_answer.add_argument("--project", default=None)
    gap_answer.add_argument("--confirm", action="store_true")
    project_gaps = sub.add_parser("project-gaps")
    project_gaps.add_argument("--all", action="store_true")
    project_gaps.add_argument("--budget", type=int, default=3)
    project_gaps.add_argument("--min-score", type=float, default=0.2)
    project_gaps.add_argument("--enqueue", action="store_true")
    project_gaps.add_argument("--tab", choices=["work", "personal"], default="personal")


def _approval_state(batch: dict) -> dict:
    return {
        "batch_id": batch.get("batch_id"),
        "state": batch.get("state"),
        "approved_at": batch.get("approved_at"),
        "items": [
            {"applicant_ref": i.get("applicant_ref"), "state": i.get("state"), "decision": i.get("decision")}
            for i in batch.get("items", [])
        ],
    }


def _dispatch_executive(args) -> int:
    from .executive import applicants as ex

    cmd = args.executive_command
    if cmd == "route":
        from .executive import routing

        bus = _executive_event_bus()
        rules = _json_input(args.rules) if args.rules is not None else None
        if rules is not None and not isinstance(rules, dict):
            raise ValueError("--rules must be a JSON object")
        records = routing.dispatch_pending(bus, consumer=args.consumer, rules=rules)
        _print({"consumer": args.consumer, "dispatched": records})
    elif cmd == "route-reason":
        from .executive import routing

        _print({"event_id": args.event_id, "route": routing.route_reason(args.event_id, bus=_executive_event_bus())})
    elif cmd == "needs-action":
        _print(ex.needs_action(limit=args.limit))
    elif cmd == "suggestions":
        _print(ex.suggestions(args.opening, gateway=_executive_gateway()))
    elif cmd == "plan":
        refs = _json_input(args.applicant_refs)
        if not isinstance(refs, list):
            raise ValueError("--applicant-refs must be a JSON list")
        _print(ex.plan_outreach(
            refs, args.opening, args.interview_type, args.location, args.duration_minutes,
            gateway=_executive_gateway(), store=_executive_store(),
        ))
    elif cmd == "batch":
        _print(_executive_store().load(args.batch_id))
    elif cmd == "approve":
        choices = _json_input(args.choices)
        if not isinstance(choices, dict):
            raise ValueError("--choices must be a JSON object")
        _print(ex.approve_batch(args.batch_id, choices, gateway=_executive_gateway(), store=_executive_store()))
    elif cmd == "send":
        store = _executive_store()
        try:
            approval = _approval_state(store.load(args.batch_id))
        except KeyError:
            raise ValueError(f"unknown batch: {args.batch_id}") from None
        result = ex.send_batch(
            args.batch_id, confirm=args.confirm,
            gateway=_executive_gateway() if args.confirm else None, store=store,
        )
        _print({"approval": approval, "dry_run": not args.confirm, "result": result})
    elif cmd == "window":
        from .executive.window import server
        return server.serve(port=args.port, open_window=not args.no_open)
    elif cmd == "next":
        from .executive import next_action

        q = _executive_window_queue(args.tab)
        result = next_action.next_item(q["queue_items"], _executive_event_bus())
        _print({**result, "errors": q["errors"]})
    elif cmd == "explain":
        from .executive import next_action

        q = _executive_window_queue(args.tab)
        explanation = next_action.explain(q["queue_items"], args.item_id, _executive_event_bus())
        _print({"item_id": args.item_id, "explanation": explanation, "errors": q["errors"]})
    elif cmd == "history":
        from .executive import window_queue

        q = _executive_window_queue(args.tab)
        provenance = window_queue.item_provenance(q["queue_items"], _executive_event_bus(), args.item_id)
        _print({"item_id": args.item_id, "provenance": provenance, "errors": q["errors"]})
    elif cmd == "project-next":
        from . import registry
        from .executive import project_actions

        try:
            project = registry.get_project(args.project)
        except KeyError:
            raise ValueError(f"unknown project: {args.project}") from None

        state = registry.load_state(project)
        today, stale_days = _executive_today_and_stale_days(args)
        project_id = state.get("project") or args.project
        deferrals = _project_deferral_counts().get(project_id, 0)
        _print(project_actions.project_next_action(state, today=today, stale_days=stale_days, deferrals=deferrals))
    elif cmd == "project-scan":
        from . import registry
        from .executive import project_actions

        states = []
        errors = []
        for proj in registry.canonical_projects():
            if "state_file" not in proj:
                continue
            try:
                state = registry.load_state(proj)
                states.append(state)
            except Exception as exc:
                errors.append({"project": proj.get("id"), "error": str(exc)})

        today, stale_days = _executive_today_and_stale_days(args)
        result = project_actions.scan(
            states, today=today, stale_days=stale_days, include_inactive=args.all,
            deferrals=_project_deferral_counts(),
        )
        _print({**result, "errors": errors})
    elif cmd == "rescue":
        from datetime import date
        from .executive import rescue as rescue_mode
        from .executive.window import rescue_view

        q = _executive_window_queue(args.tab)
        today = date.fromisoformat(args.today) if args.today else date.today()
        results, errors = rescue_view.project_results(today, args.stale_days)

        _print({**rescue_mode.rescue(q["queue_items"], results, today=today, horizon_days=args.horizon_days),
                "errors": q["errors"] + errors})
    elif cmd == "resume":
        from . import registry
        from .executive import resumption

        try:
            project = registry.get_project(args.project)
        except KeyError:
            raise ValueError(f"unknown project: {args.project}") from None
        state = registry.load_state(project)
        today, stale_days = _executive_today_and_stale_days(args)
        _print(resumption.resumption_packet(state, today=today, stale_days=stale_days))
    elif cmd == "brain-dump":
        from . import registry
        from .executive import brain_dump

        if args.file is None and args.text is None:
            raise ValueError("provide text or --file")
        text = args.file.read_text(encoding="utf-8") if args.file is not None else args.text
        known_projects = [{"id": p.get("id"), "aliases": p.get("aliases", [])} for p in registry.canonical_projects()]
        result = brain_dump.process(text, known_projects=known_projects)
        if args.stage_candidates:
            from . import candidates

            staged = candidates.stage_candidates(
                args.stage_candidates, "Executive brain dump",
                [{"kind": "preference_candidate", "statement": record["text"],
                  "evidence": ["executive:brain-dump"], "confidence": record["confidence"]}
                 for record in result["records"]],
            )
            result["staging"] = staged
        _print(result)
    elif cmd == "gaps":
        from .executive import knowledge_gaps

        values = _json_input(args.gaps_json)
        if not isinstance(values, list):
            raise ValueError("gaps must be a JSON list")
        result = knowledge_gaps.select_questions(values, budget=args.budget, min_score=args.min_score,
                                                 asked_ids=args.asked_id)
        if args.enqueue:
            from .executive.window.gap_store import GapStore

            result["enqueued"] = GapStore().add(values, tab=args.tab)
        _print(result)
    elif cmd == "gap-answer":
        from .executive.window import actions_knowledge_gaps

        result = actions_knowledge_gaps.answer_gap(
            args.gap_id, args.answer, project=args.project, confirm=args.confirm
        )
        _print({"dry_run": not args.confirm, **result})
    elif cmd == "project-gaps":
        from . import registry
        from .executive import project_gaps, knowledge_gaps

        states = []
        errors = []
        for proj in registry.canonical_projects():
            if "state_file" not in proj:
                continue
            try:
                states.append(registry.load_state(proj))
            except Exception as exc:
                errors.append({"project": proj.get("id"), "error": str(exc)})

        gaps = project_gaps.project_gaps(states, include_inactive=args.all)
        result = {"gaps": gaps, **knowledge_gaps.select_questions(
            gaps, budget=args.budget, min_score=args.min_score
        ), "errors": errors}
        if args.enqueue:
            from .executive.window.gap_store import GapStore

            result["enqueued"] = GapStore().add(gaps, tab=args.tab)
        _print(result)
    return 0


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="agent-os")
    commands = root.add_subparsers(dest="command", required=True)
    commands.add_parser("projects")
    scan_projects = commands.add_parser("scan-projects")
    scan_projects.add_argument("--root")
    commands.add_parser("index")
    commands.add_parser("init")
    commands.add_parser("sync-adapters")
    browser_bridge = commands.add_parser(
        "browser-bridge",
        help="run the durable loopback bridge used by the browser capture userscript",
    )
    browser_bridge.add_argument("--host", default=BROWSER_BRIDGE_HOST)
    browser_bridge.add_argument("--port", type=int, default=BROWSER_BRIDGE_PORT)
    commands.add_parser(
        "browser-bridge-status",
        help="show local browser bridge database counts",
    )
    commands.add_parser(
        "browser-bridge-token",
        help="show the local browser bridge token for one-time userscript setup",
    )
    browser_sessions_p = commands.add_parser(
        "browser-sessions",
        help="list Firefox/Tampermonkey sessions registered with Agent OS",
    )
    browser_sessions_p.add_argument("--all", action="store_true")
    browser_sessions_p.add_argument("--active-within-seconds", type=int, default=90)
    browser_execute_p = commands.add_parser(
        "browser-execute",
        help="queue bounded browser actions for one registered session",
    )
    browser_execute_p.add_argument("session_id")
    browser_execute_p.add_argument("actions_json")
    browser_execute_p.add_argument("--issued-by", default="cli")
    browser_execute_p.add_argument("--approved-consequential", action="store_true")
    browser_execute_p.add_argument("--wait-seconds", type=float, default=12.0)
    browser_status_p = commands.add_parser(
        "browser-command-status",
        help="read a previously queued browser command result",
    )
    browser_status_p.add_argument("command_id")
    bridge_pending = commands.add_parser(
        "browser-bridge-pending",
        help="read durable browser events waiting for Knowledge Engine ingestion",
    )
    bridge_pending.add_argument("--limit", type=int, default=100)
    bridge_mark = commands.add_parser(
        "browser-bridge-mark-ingested",
        help="mark bridge events as consumed after downstream durable ingestion",
    )
    bridge_mark.add_argument("--event-id", action="append", default=[], required=True)
    commands.add_parser("install-routing")
    commands.add_parser("routing-status")
    integration = commands.add_parser("integration-health")
    integration.add_argument("--surface")
    integration.add_argument("--strict", action="store_true")
    connector_candidates = commands.add_parser(
        "connector-import-candidates",
        help="read-only inventory of local client MCP registrations for connector review",
    )
    connector_candidates.add_argument("--surface")
    connector_reconcile = commands.add_parser(
        "connector-reconcile-plan",
        help="read-only plan of connector registration actions per client surface; applies nothing",
    )
    connector_reconcile.add_argument("--surface")
    connector_creds = commands.add_parser(
        "connector-credential-status",
        help="read-only, presence-only check of connector credential references; never prints values",
    )
    connector_creds.add_argument("--surface")
    connector_conflicts_p = commands.add_parser(
        "connector-conflicts",
        help="read-only report of duplicate or conflicting connector registrations; never prints credentials",
    )
    connector_conflicts_p.add_argument("--surface")
    connector_provisioning_readiness_p = commands.add_parser(
        "connector-provisioning-readiness",
        help="read-only ready/blocked provisioning verdict per connector registration; never prints credentials",
    )
    connector_provisioning_readiness_p.add_argument("--surface")
    connector_events_p = commands.add_parser(
        "connector-events",
        help="read-only list of recent connector change events; never prints credentials",
    )
    connector_events_p.add_argument("--limit", type=int, default=50)
    connector_events_p.add_argument("--connector", dest="connector_id", default=None)
    connector_events_p.add_argument("--after-seq", dest="after_seq", type=int, default=None)
    connector_subscriber_poll_p = commands.add_parser(
        "connector-subscriber-poll",
        help="read-only poll for queued events for a subscriber",
    )
    connector_subscriber_poll_p.add_argument("subscriber_id")
    connector_subscriber_poll_p.add_argument("--limit", type=int, default=50)
    connector_subscriber_ack_p = commands.add_parser(
        "connector-subscriber-ack",
        help="acknowledge a connector event for a subscriber",
    )
    connector_subscriber_ack_p.add_argument("subscriber_id")
    connector_subscriber_ack_p.add_argument("--seq", type=int, required=True)
    connector_subscriber_ack_p.add_argument("--confirm-write", action="store_true", dest="confirm_write")
    connector_unregister = commands.add_parser(
        "connector-unregister",
        help="preview or remove a connector's registry metadata; never revokes credentials",
    )
    connector_unregister.add_argument("connector_id")
    connector_unregister.add_argument("--confirm-write", action="store_true")
    connector_prune_stale = commands.add_parser(
        "connector-prune-stale",
        help="Preview or remove registrations for surfaces no longer in the surface registry",
    )
    connector_prune_stale.add_argument("connector_id", nargs="?", default=None)
    connector_prune_stale.add_argument("--confirm-write", action="store_true")
    connector_verify_native = commands.add_parser(
        "connector-verify-native",
        help="Preview or confirm config-level verification of native client registrations",
    )
    connector_verify_native.add_argument("connector_id", nargs="?", default=None)
    connector_verify_native.add_argument("--confirm-write", action="store_true")
    connector_set_registration_state = commands.add_parser(
        "connector-set-registration-state",
        help="preview or update a connector's registration state for a surface; previews by default",
    )
    connector_set_registration_state.add_argument("connector_id")
    connector_set_registration_state.add_argument("surface_id")
    connector_set_registration_state.add_argument("state", choices=["desired", "disabled"])
    connector_set_registration_state.add_argument("--confirm-write", action="store_true")
    connector_register = commands.add_parser(
        "connector-register",
        help="preview or explicitly write provider-neutral connector metadata from a JSON file",
    )
    connector_register.add_argument("metadata_file")
    connector_register.add_argument("--confirm-write", action="store_true")
    connector_register.add_argument("--replace-existing", action="store_true")
    connector_import = commands.add_parser(
        "connector-import",
        help="review a discovered local MCP registration and optionally add its supplied metadata to Agent OS",
    )
    connector_import.add_argument("candidate_id")
    connector_import.add_argument("metadata_file")
    connector_import.add_argument("--reviewed", action="store_true")
    connector_import.add_argument("--confirm-write", action="store_true")
    connector_import.add_argument("--replace-existing", action="store_true")
    work_claim = commands.add_parser("work-claim")
    work_claim.add_argument("project")
    work_claim.add_argument("task")
    work_claim.add_argument("--agent", required=True)
    work_claim.add_argument("--scope", action="append", default=[])
    work_claim.add_argument("--lease-minutes", type=int, default=90)
    work_check = commands.add_parser("work-check")
    work_check.add_argument("project")
    work_check.add_argument("--scope", action="append", default=[])
    work_status = commands.add_parser("work-status")
    work_status.add_argument("--project")
    work_beat = commands.add_parser("work-heartbeat")
    work_beat.add_argument("claim_id")
    work_release = commands.add_parser("work-release")
    work_release.add_argument("claim_id")
    work_release.add_argument("--note")
    work_note_p = commands.add_parser("work-note")
    work_note_p.add_argument("project")
    work_note_p.add_argument("text")
    work_note_p.add_argument("--from-agent", required=True)
    work_note_p.add_argument("--about")
    work_inbox_p = commands.add_parser("work-inbox")
    work_inbox_p.add_argument("--project")
    work_inbox_p.add_argument("--all", action="store_true")
    work_ack = commands.add_parser("work-ack")
    work_ack.add_argument("note_id")
    work_ack.add_argument("--agent", required=True)
    work_ack.add_argument("--reply")
    work_message = commands.add_parser("work-message")
    work_message.add_argument("claim_id")
    work_message.add_argument("text")
    work_message.add_argument("--from-agent", required=True)
    work_delegate = commands.add_parser("work-delegate")
    work_delegate.add_argument("project")
    work_delegate.add_argument("task_key")
    work_delegate.add_argument("title")
    work_delegate.add_argument("--from-agent", required=True)
    work_delegate.add_argument("--to-agent")
    work_delegate.add_argument("--scope", action="append", default=[])
    work_delegate.add_argument("--depends-on", action="append", default=[])
    work_delegate.add_argument("--review-required", action="store_true")
    work_tasks = commands.add_parser("work-tasks")
    work_tasks.add_argument("--project")
    work_tasks.add_argument("--status", choices=("queued", "assigned", "in_progress", "completed", "cancelled"))
    work_task_claim = commands.add_parser("work-task-claim")
    work_task_claim.add_argument("task_id")
    work_task_claim.add_argument("--agent", required=True)
    work_task_complete = commands.add_parser("work-task-complete")
    work_task_complete.add_argument("task_id")
    work_task_complete.add_argument("--agent", required=True)
    work_task_complete.add_argument("--validation", required=True)
    work_task_complete.add_argument("--result")
    work_task_requeue = commands.add_parser("work-task-requeue")
    work_task_requeue.add_argument("task_id")
    work_task_requeue.add_argument("--agent", required=True)
    work_task_requeue.add_argument("--reason", required=True)
    work_review_request = commands.add_parser("work-review-request")
    work_review_request.add_argument("project")
    work_review_request.add_argument("review_key")
    work_review_request.add_argument("--from-agent", required=True)
    work_review_request.add_argument("--task-id")
    work_review_request.add_argument("--commit-fingerprint")
    work_review_request.add_argument("--reviewer")
    work_review_request.add_argument("--changed-file", action="append", default=[])
    work_reviews = commands.add_parser("work-reviews")
    work_reviews.add_argument("--project")
    work_reviews.add_argument("--status", choices=("requested", "approved", "changes_requested", "blocked"))
    work_review_submit = commands.add_parser("work-review-submit")
    work_review_submit.add_argument("review_id")
    work_review_submit.add_argument("--agent", required=True)
    work_review_submit.add_argument("--verdict", choices=("approved", "changes_requested", "blocked"), required=True)
    work_review_submit.add_argument("--validation", required=True)
    work_review_submit.add_argument("--finding", action="append", default=[])
    watch_add = commands.add_parser("watch-add", help="add or update a proactive watch target from JSON")
    watch_add.add_argument("target_file")
    watch_list = commands.add_parser("watch-list", help="list proactive watch targets")
    watch_list.add_argument("--status")
    watch_remove = commands.add_parser("watch-remove", help="remove a proactive watch target")
    watch_remove.add_argument("watch_id")
    creator_list = commands.add_parser("creator-list", help="list followed creator identity profiles")
    creator_list.add_argument("--status")
    commands.add_parser(
        "creator-discovery-pending",
        help="list creator profiles waiting for cross-provider identity discovery",
    )
    creator_record = commands.add_parser(
        "creator-discovery-record",
        help="merge provenance-bearing cross-provider findings into a creator profile",
    )
    creator_record.add_argument("creator_id")
    creator_record.add_argument("findings_file")
    commands.add_parser("validate")
    telemetry_report = commands.add_parser("telemetry-report")
    telemetry_report.add_argument("--path")
    telemetry_report.add_argument("--group-by", choices=sorted(REPORT_GROUP_FIELDS), default=None)
    telemetry_report.add_argument("--oversized-input-tokens", type=int, default=None)
    telemetry_record = commands.add_parser("telemetry-record")
    telemetry_record.add_argument("--path", default=None, help="store path; None means LocalTelemetryStore default")
    telemetry_record.add_argument("--project", required=True, help="maps to project_id")
    telemetry_record.add_argument("--category", required=True, help="maps to task_category")
    telemetry_record.add_argument("--capability", default=None, help="maps to capability_class")
    telemetry_record.add_argument("--execution-path", default=None, help="maps to execution_path")
    telemetry_record.add_argument("--provider", type=str, default=None)
    telemetry_record.add_argument("--model", type=str, default=None)
    telemetry_record.add_argument("--input-tokens", type=int, default=None)
    telemetry_record.add_argument("--cached-tokens", type=int, default=None)
    telemetry_record.add_argument("--reasoning-tokens", type=int, default=None)
    telemetry_record.add_argument("--output-tokens", type=int, default=None)
    telemetry_record.add_argument("--duration-ms", type=int, default=None)
    telemetry_record.add_argument("--items-processed", type=int, default=None)
    telemetry_record.add_argument("--retries", type=int, default=None)
    telemetry_record.add_argument("--escalations", type=int, default=None)
    validator_group = telemetry_record.add_mutually_exclusive_group()
    validator_group.add_argument("--validator-passed", action="store_true", dest="validator_passed_flag")
    validator_group.add_argument("--validator-failed", action="store_true", dest="validator_failed_flag")
    telemetry_record.add_argument("--override", action="store_true", default=None, help="the operator corrected or overrode this event's output")
    telemetry_record.add_argument("--usage-file", default=None, help="path to a JSON file holding a provider usage block or full provider response")
    telemetry_record.add_argument("--usage-format", choices=list(PROVIDER_USAGE_FORMATS), default=None, help="format of the provider usage in --usage-file")
    commands.add_parser("document-cache-status")
    commands.add_parser("document-cache-clear")
    cache_prune = commands.add_parser("document-cache-prune")
    cache_prune.add_argument("--max-bytes", type=int, default=536870912)
    cache_prune.add_argument("--max-age-days", type=int, default=90)
    commands.add_parser("profile-status")
    recovery_status = commands.add_parser("recovery-status")
    recovery_status.add_argument("--project")
    recovery_status.add_argument("--run-id")
    recovery_inspect = commands.add_parser("recovery-inspect")
    recovery_inspect.add_argument("--project")
    recovery_inspect.add_argument("--run-id")
    recovery_resume = commands.add_parser("recovery-resume")
    recovery_resume.add_argument("--project")
    recovery_resume.add_argument("--run-id")
    checkpoint_list = commands.add_parser("checkpoint-list")
    checkpoint_list.add_argument("--project")
    checkpoint_get = commands.add_parser("checkpoint-get")
    checkpoint_get.add_argument("project")
    checkpoint_get.add_argument("run_id")
    profile_retrieve = commands.add_parser("profile-retrieve")
    profile_retrieve.add_argument("task")
    profile_retrieve.add_argument("--limit", type=int, default=5)
    profile_retrieve.add_argument("--minimum-score", type=int, default=3)
    commands.add_parser("workflows")
    workflow_start = commands.add_parser("workflow-start")
    workflow_start.add_argument("workflow")
    workflow_start.add_argument("--run-id")
    workflow_runs = commands.add_parser("workflow-runs")
    workflow_runs.add_argument("project")
    workflow_next = commands.add_parser("workflow-next")
    workflow_next.add_argument("workflow")
    workflow_next.add_argument("--run-id", required=True)
    workflow_stage = commands.add_parser("workflow-stage")
    workflow_stage.add_argument("workflow")
    workflow_stage.add_argument("--run-id", required=True)
    workflow_stage.add_argument("--stage")
    workflow_run = commands.add_parser("workflow-run")
    workflow_run.add_argument("workflow")
    workflow_run.add_argument("--run-id", required=True)
    workflow_run.add_argument("--stage")
    workflow_run.add_argument("--telemetry-path", default=None)
    workflow_complete = commands.add_parser("workflow-complete")
    workflow_complete.add_argument("workflow")
    workflow_complete.add_argument("--run-id", required=True)
    workflow_complete.add_argument("--stage", required=True)
    workflow_complete.add_argument("--output", action="append", default=[])
    workflow_complete.add_argument("--checkpoint")
    workflow_complete.add_argument("--failed", action="store_true")
    workflow_complete.add_argument("--detail")
    workflow_complete.add_argument("--telemetry-path", default=None)
    workflow_complete.add_argument("--provider", default=None)
    workflow_complete.add_argument("--model", default=None)
    workflow_complete.add_argument("--input-tokens", type=int, default=None)
    workflow_complete.add_argument("--cached-tokens", type=int, default=None)
    workflow_complete.add_argument("--reasoning-tokens", type=int, default=None)
    workflow_complete.add_argument("--output-tokens", type=int, default=None)
    workflow_complete.add_argument("--duration-ms", type=int, default=None)
    workflow_complete.add_argument("--items-processed", type=int, default=None)
    workflow_complete.add_argument("--override", action="store_true", default=None,
                                   help="the operator corrected or overrode this stage's output")
    workflow_complete.add_argument("--usage-file", default=None,
                                   help="path to a JSON file holding a provider usage block or full provider response")
    workflow_complete.add_argument("--usage-format", choices=list(PROVIDER_USAGE_FORMATS), default=None,
                                   help="format of the provider usage in --usage-file")
    commands.add_parser("mcp")
    commands.add_parser("machine-status")
    local_path = commands.add_parser("set-local-path")
    local_path.add_argument("project")
    local_path.add_argument("--path")
    local_path.add_argument("--search-root")
    launcher_install = commands.add_parser("launcher-install")
    launcher_install.add_argument("--repository-path")
    commands.add_parser("launcher-status")
    commands.add_parser("launcher-verify")
    mail_cli.register(commands)
    maintenance = commands.add_parser("maintenance")
    maintenance.add_argument("--event", default="scheduled")
    maintenance.add_argument("--project")
    capture = commands.add_parser("capture-candidates")
    capture.add_argument("project")
    capture.add_argument("--task-summary", required=True)
    capture.add_argument("--candidates-json", required=True)
    curate = commands.add_parser("curate-candidates")
    curate.add_argument("project")
    curate.add_argument("--action", choices=("review", "reject", "promote"), default="review")
    curate.add_argument("--candidate-id", action="append", default=[])
    candidate_list = commands.add_parser("candidate-status")
    candidate_list.add_argument("project")
    change_capture = commands.add_parser("change-capture")
    change_capture.add_argument("project")
    change_capture.add_argument("--json", required=True)
    change_list = commands.add_parser("change-list")
    change_list.add_argument("project")
    change_list.add_argument("--status")
    change_show = commands.add_parser("change-show")
    change_show.add_argument("project")
    change_show.add_argument("change_id")
    change_update = commands.add_parser("change-update")
    change_update.add_argument("project")
    change_update.add_argument("change_id")
    change_update.add_argument("--json", required=True)
    change_export = commands.add_parser("change-export-safe")
    change_export.add_argument("project")
    change_export.add_argument("change_id")
    change_promote = commands.add_parser("change-promote")
    change_promote.add_argument("project")
    change_promote.add_argument("change_id")
    improvement_capture = commands.add_parser("improvement-capture")
    improvement_capture.add_argument("project")
    improvement_capture.add_argument("--json", required=True)
    improvement_list = commands.add_parser("improvement-list")
    improvement_list.add_argument("project")
    improvement_list.add_argument("--status")
    improvement_show = commands.add_parser("improvement-show")
    improvement_show.add_argument("project")
    improvement_show.add_argument("improvement_id")
    improvement_update = commands.add_parser("improvement-update")
    improvement_update.add_argument("project")
    improvement_update.add_argument("improvement_id")
    improvement_update.add_argument("--json", required=True)
    improvement_search = commands.add_parser("improvement-search")
    improvement_search.add_argument("project")
    improvement_search.add_argument("query")
    improvement_search.add_argument("--limit", type=int, default=8)
    improvement_issue = commands.add_parser("improvement-issue")
    improvement_issue.add_argument("project")
    improvement_issue.add_argument("improvement_id")
    form_route = commands.add_parser("form-route")
    form_route.add_argument("candidate")
    form_route.add_argument("--persist", action="store_true")
    form_route.add_argument("--queue")
    form_issue = commands.add_parser("form-issue")
    form_issue.add_argument("candidate")
    identify = commands.add_parser("identify")
    identify.add_argument("path", nargs="?", default=".")
    status = commands.add_parser("status")
    status.add_argument("project", nargs="?")
    lookup = commands.add_parser("search")
    lookup.add_argument("query")
    lookup.add_argument("--project")
    lookup.add_argument("--limit", type=int, default=8)
    context = commands.add_parser("context")
    context.add_argument("project")
    context.add_argument("task")
    context.add_argument("--token-budget", type=int, default=4000)
    handoff = commands.add_parser("handoff")
    handoff.add_argument("project")
    handoff.add_argument("--completed", action="append", default=[])
    handoff.add_argument("--remaining", action="append", default=[])
    handoff.add_argument("--validation", action="append", default=[])
    handoff.add_argument("--decision", action="append", default=[])
    review = commands.add_parser("review")
    review.add_argument("--changed-file", action="append", default=[])
    review.add_argument("--tests-failed", action="store_true")
    review.add_argument("--architecture-change", action="store_true")
    register_orchestrate(commands)
    _register_executive(commands)
    return root


def main(argv: list[str] | None = None) -> int:
    # A Windows pipe defaults to the ANSI code page, which cannot encode
    # characters such as "≥" in run summaries and crashed JSON output.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure") and (stream.encoding or "").lower() not in {"utf-8", "utf8"}:
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except (OSError, ValueError):
                pass
    args = parser().parse_args(argv)
    try:
        if args.command == "projects":
            _print(projects())
        elif args.command == "scan-projects":
            _print(scan(Path(args.root) if args.root else None))
        elif args.command == "index":
            _print(rebuild())
        elif args.command == "init":
            written = sync_adapters()
            index_result = rebuild()
            validation_result = validate()
            _print({"adapters": written, "index": index_result, "validation": validation_result})
            return 0 if validation_result["ok"] else 1
        elif args.command == "sync-adapters":
            _print({"written": sync_adapters()})
        elif args.command == "browser-bridge":
            return serve_browser_bridge(args.host, args.port)
        elif args.command == "browser-bridge-status":
            _print(BridgeStore().stats())
        elif args.command == "browser-bridge-token":
            _print({
                "token": browser_bridge_token(),
                "path": str(BROWSER_BRIDGE_TOKEN_PATH),
            })
        elif args.command == "browser-sessions":
            _print({
                "sessions": browser_sessions(
                    active_only=not args.all,
                    active_within_seconds=args.active_within_seconds,
                )
            })
        elif args.command == "browser-execute":
            actions = json.loads(args.actions_json)
            if not isinstance(actions, list):
                raise ValueError("actions_json must decode to a list")
            _print(browser_execute(
                args.session_id,
                actions,
                issued_by=args.issued_by,
                approved_consequential=args.approved_consequential,
                wait_seconds=args.wait_seconds,
            ))
        elif args.command == "browser-command-status":
            _print(browser_command_status(args.command_id))
        elif args.command == "browser-bridge-pending":
            _print({"events": BridgeStore().pending(args.limit)})
        elif args.command == "browser-bridge-mark-ingested":
            _print({"marked": BridgeStore().mark_ingested(args.event_id)})
        elif args.command == "install-routing":
            result = install_routing()
            _print(result)
            return 1 if result["conflicts"] else 0
        elif args.command == "routing-status":
            _print(routing_status())
        elif args.command == "integration-health":
            report = integration_health(args.surface)
            _print(report)
            return 1 if args.strict and not report["ok"] else 0
        elif args.command == "connector-import-candidates":
            _print(connector_import_candidates(args.surface))
        elif args.command == "connector-reconcile-plan":
            _print(connector_reconcile_plan(args.surface))
        elif args.command == "connector-credential-status":
            _print(connector_credential_status(args.surface))
        elif args.command == "connector-conflicts":
            _print(connector_conflicts(args.surface))
        elif args.command == "connector-provisioning-readiness":
            _print(connector_provisioning_readiness(args.surface))
        elif args.command == "connector-events":
            _print(connector_events(args.limit, args.connector_id, args.after_seq))
        elif args.command == "connector-subscriber-poll":
            _print(connector_subscriber_poll(args.subscriber_id, args.limit))
        elif args.command == "connector-subscriber-ack":
            _print(connector_subscriber_ack(args.subscriber_id, args.seq, confirm_write=args.confirm_write))
        elif args.command == "connector-unregister":
            _print(unregister_connector(args.connector_id, confirm_write=args.confirm_write))
        elif args.command == "connector-prune-stale":
            _print(prune_stale_registrations(args.connector_id, confirm_write=args.confirm_write))
        elif args.command == "connector-verify-native":
            _print(verify_native_registrations(args.connector_id, confirm_write=args.confirm_write))
        elif args.command == "connector-set-registration-state":
            _print(set_registration_state(args.connector_id, args.surface_id, args.state, confirm_write=args.confirm_write))
        elif args.command == "connector-register":
            _print(
                register_connector(
                    _load_object(args.metadata_file),
                    confirm_write=args.confirm_write,
                    replace_existing=args.replace_existing,
                )
            )
        elif args.command == "connector-import":
            _print(
                import_connector_candidate(
                    args.candidate_id,
                    _load_object(args.metadata_file),
                    reviewed=args.reviewed,
                    confirm_write=args.confirm_write,
                    replace_existing=args.replace_existing,
                )
            )
        elif args.command == "work-claim":
            result = make_claim(args.project, args.task, args.agent, args.scope, args.lease_minutes)
            _print(result)
            return 1 if result["conflicts"] else 0
        elif args.command == "work-check":
            result = check_claims(args.project, args.scope)
            _print(result)
            return 0 if result["clear"] else 1
        elif args.command == "work-status":
            _print(claims_status(args.project))
        elif args.command == "work-heartbeat":
            _print(claim_heartbeat(args.claim_id))
        elif args.command == "work-release":
            _print(release_claim(args.claim_id, args.note))
        elif args.command == "work-note":
            _print(work_note(args.project, args.text, args.from_agent, args.about))
        elif args.command == "work-inbox":
            result = work_inbox(args.project, args.all)
            _print(result)
            return 1 if result["waiting"] else 0
        elif args.command == "work-ack":
            _print(acknowledge_note(args.note_id, args.agent, args.reply))
        elif args.command == "work-message":
            _print(claim_message(args.claim_id, args.text, args.from_agent))
        elif args.command == "work-delegate":
            _print(delegate(args.project, args.task_key, args.title, args.from_agent, args.to_agent, args.scope, args.depends_on, review_required=args.review_required))
        elif args.command == "work-tasks":
            _print(list_tasks(args.project, args.status))
        elif args.command == "work-task-claim":
            _print(claim_task(args.task_id, args.agent))
        elif args.command == "work-task-complete":
            _print(complete_task(args.task_id, args.agent, args.validation, args.result))
        elif args.command == "work-task-requeue":
            _print(requeue_task(args.task_id, args.agent, args.reason))
        elif args.command == "work-review-request":
            _print(request_review(args.project, args.review_key, args.from_agent, task_id=args.task_id, commit_fingerprint=args.commit_fingerprint, reviewer=args.reviewer, changed_files=args.changed_file))
        elif args.command == "work-reviews":
            _print(list_reviews(args.project, args.status))
        elif args.command == "work-review-submit":
            _print(submit_review(args.review_id, args.agent, args.verdict, args.validation, args.finding))
        elif args.command == "watch-add":
            _print(watch_add_target(_load_object(args.target_file)))
        elif args.command == "watch-list":
            _print({"targets": watch_list_targets(status=args.status)})
        elif args.command == "watch-remove":
            _print({"removed": watch_remove_target(args.watch_id), "watch_id": args.watch_id})
        elif args.command == "creator-list":
            _print({"creators": creator_list_profiles(status=args.status)})
        elif args.command == "creator-discovery-pending":
            _print({"creators": creator_pending_discovery()})
        elif args.command == "creator-discovery-record":
            _print(creator_record_discovery(args.creator_id, _load_object(args.findings_file)))
        elif args.command == "validate":
            result = validate()
            _print(result)
            return 0 if result["ok"] else 1
        elif args.command == "telemetry-report":
            store = LocalTelemetryStore(Path(args.path) if args.path else None)
            _print(store.aggregate_report(group_by=args.group_by, oversized_input_tokens=args.oversized_input_tokens))
        elif args.command == "telemetry-record":
            # Validate --usage-file and --usage-format pairing
            if bool(args.usage_file) != bool(args.usage_format):
                raise ValueError("--usage-file and --usage-format must be provided together")

            # Validate --usage-file is not combined with explicit token flags
            if args.usage_file and any([
                args.input_tokens is not None,
                args.cached_tokens is not None,
                args.reasoning_tokens is not None,
                args.output_tokens is not None,
            ]):
                raise ValueError("use either --usage-file or explicit token flags")

            input_tokens = args.input_tokens
            cached_tokens = args.cached_tokens
            reasoning_tokens = args.reasoning_tokens
            output_tokens = args.output_tokens

            if args.usage_file:
                payload = json.loads(Path(args.usage_file).read_text(encoding="utf-8"))
                counts = token_counts_from_provider_usage(payload, args.usage_format)
                input_tokens = counts["input_tokens"]
                cached_tokens = counts["cached_tokens"]
                reasoning_tokens = counts["reasoning_tokens"]
                output_tokens = counts["output_tokens"]

            # Determine validator_passed value from mutually exclusive flags
            validator_passed = None
            if args.validator_passed_flag:
                validator_passed = True
            elif args.validator_failed_flag:
                validator_passed = False

            event = TelemetryEvent(
                project_id=args.project,
                task_category=args.category,
                capability_class=args.capability,
                execution_path=args.execution_path,
                provider=args.provider,
                model=args.model,
                input_tokens=input_tokens,
                cached_tokens=cached_tokens,
                reasoning_tokens=reasoning_tokens,
                output_tokens=output_tokens,
                duration_ms=args.duration_ms,
                items_processed=args.items_processed,
                retries=args.retries,
                escalations=args.escalations,
                validator_passed=validator_passed,
                correction_or_override=args.override if args.override else None,
            )

            store = LocalTelemetryStore(Path(args.path) if args.path else None)
            store.record(event)
            _print(event.as_dict())
        elif args.command == "document-cache-status":
            _print(DocumentCache().stats())
        elif args.command == "document-cache-clear":
            _print(DocumentCache().clear())
        elif args.command == "document-cache-prune":
            _print(DocumentCache().prune(args.max_bytes, args.max_age_days))
        elif args.command == "profile-status":
            _print(profile_status())
        elif args.command in {"recovery-status", "recovery-inspect"}:
            _print(inspect_recovery(args.project, args.run_id))
        elif args.command == "recovery-resume":
            _print(resume_recovery(args.project, args.run_id))
        elif args.command == "checkpoint-list":
            _print(list_checkpoints(args.project))
        elif args.command == "checkpoint-get":
            _print(get_checkpoint(args.project, args.run_id))

        elif args.command == "profile-retrieve":
            _print(compact_profile(args.task, limit=args.limit, minimum_score=args.minimum_score))
        elif args.command == "workflows":
            _print(list_workflows())
        elif args.command == "workflow-start":
            _print(start_workflow(args.workflow, args.run_id))
        elif args.command == "workflow-runs":
            _print(list_runs(args.project))
        elif args.command == "workflow-next":
            _print(workflow_status(args.workflow, args.run_id))
        elif args.command == "workflow-stage":
            _print(prepare_stage(args.workflow, args.run_id, args.stage))
        elif args.command == "workflow-run":
            store = LocalTelemetryStore(Path(args.telemetry_path)) if args.telemetry_path else None
            _print(run_stage(args.workflow, args.run_id, args.stage, telemetry_store=store))
        elif args.command == "workflow-complete":
            store = LocalTelemetryStore(Path(args.telemetry_path)) if args.telemetry_path else None

            # Validate --usage-file and --usage-format pairing
            if bool(args.usage_file) != bool(args.usage_format):
                raise ValueError("--usage-file and --usage-format must be provided together")

            # Validate --usage-file is not combined with explicit token flags
            if args.usage_file and any([
                args.input_tokens is not None,
                args.cached_tokens is not None,
                args.reasoning_tokens is not None,
                args.output_tokens is not None,
            ]):
                raise ValueError("use either --usage-file or explicit token flags")

            input_tokens = args.input_tokens
            cached_tokens = args.cached_tokens
            reasoning_tokens = args.reasoning_tokens
            output_tokens = args.output_tokens

            if args.usage_file:
                payload = json.loads(Path(args.usage_file).read_text(encoding="utf-8"))
                counts = token_counts_from_provider_usage(payload, args.usage_format)
                input_tokens = counts["input_tokens"]
                cached_tokens = counts["cached_tokens"]
                reasoning_tokens = counts["reasoning_tokens"]
                output_tokens = counts["output_tokens"]

            _print(
                complete_stage(
                    args.workflow,
                    args.run_id,
                    args.stage,
                    outputs=args.output,
                    checkpoint=args.checkpoint,
                    passed=False if args.failed else None,
                    detail=args.detail,
                    telemetry_store=store,
                    provider=args.provider,
                    model=args.model,
                    input_tokens=input_tokens,
                    cached_tokens=cached_tokens,
                    reasoning_tokens=reasoning_tokens,
                    output_tokens=output_tokens,
                    duration_ms=args.duration_ms,
                    items_processed=args.items_processed,
                    correction_or_override=args.override,
                )
            )
        elif args.command == "mcp":
            return serve()
        elif args.command == "machine-status":
            _print({"machine": describe_machine(), "projects": [{"id": item["id"], "path": item["path"], "path_source": item["path_source"]} for item in projects()]})
        elif args.command == "set-local-path":
            _print(write_override(args.project, args.path, args.search_root))
        elif args.command == "launcher-install":
            _print(install_launcher(Path(args.repository_path) if args.repository_path else None))
        elif args.command == "launcher-status":
            _print(launcher_status())
        elif args.command == "launcher-verify":
            result = verify_launcher()
            _print(result)
            return 0 if result["ok"] else 1
        elif args.command == "mail":
            return mail_cli.dispatch(args, _print)
        elif args.command == "maintenance":
            _print(run_maintenance(args.event, args.project))
        elif args.command == "capture-candidates":
            candidates = json.loads(args.candidates_json)
            if not isinstance(candidates, list):
                raise ValueError("--candidates-json must be a JSON list")
            _print(stage_candidates(args.project, args.task_summary, candidates))
        elif args.command == "curate-candidates":
            _print(curate_candidates(args.project, args.candidate_id, args.action))
        elif args.command == "candidate-status":
            _print(candidate_status(args.project))
        elif args.command == "change-capture":
            _print(capture_change(args.project, **_load_object(args.json)))
        elif args.command == "change-list":
            _print(list_changes(args.project, args.status))
        elif args.command == "change-show":
            _print(get_change(args.project, args.change_id))
        elif args.command == "change-update":
            _print(update_change(args.project, args.change_id, **_load_object(args.json)))
        elif args.command == "change-export-safe":
            _print(google_safe_projection(args.project, args.change_id))
        elif args.command == "change-promote":
            _print(promote_change(args.project, args.change_id))
        elif args.command == "improvement-capture":
            _print(capture_improvement(args.project, **_load_object(args.json)))
        elif args.command == "improvement-list":
            _print(list_improvements(args.project, args.status))
        elif args.command == "improvement-show":
            _print(get_improvement(args.project, args.improvement_id))
        elif args.command == "improvement-update":
            _print(update_improvement(args.project, args.improvement_id, **_load_object(args.json)))
        elif args.command == "improvement-search":
            _print(search_improvements(args.project, args.query, args.limit))
        elif args.command == "improvement-issue":
            _print(issue_payload(args.project, args.improvement_id))
        elif args.command == "form-route":
            _print(route_form(_load_object(args.candidate), args.persist, args.queue))
        elif args.command == "form-issue":
            _print(form_issue_payload(_load_object(args.candidate)))
        elif args.command == "identify":
            _print(identify_project(Path(args.path)))
        elif args.command == "status":
            project = get_project(args.project) if args.project else identify_project(Path.cwd())
            if not project:
                raise KeyError("Current directory is not a registered project; specify a project id")
            _print({"project": project, "state": load_state(project), "git": git_status(project)})
        elif args.command == "search":
            _print(search(args.query, args.project, args.limit))
        elif args.command == "context":
            _print(compile_context(args.project, args.task, args.token_budget))
        elif args.command == "handoff":
            path = create_handoff(args.project, args.completed, args.remaining, args.validation, args.decision)
            _print({"created": str(path)})
        elif args.command == "review":
            _print(assess(args.changed_file, args.tests_failed, args.architecture_change))
        elif args.command == "executive":
            return _dispatch_executive(args)
        elif args.command == "orchestrate":
            return dispatch_orchestrate(args, _print)
    except (KeyError, OSError, ValueError, ImportError) as exc:
        _print({"error": str(exc)})
        return 2
    return 0
