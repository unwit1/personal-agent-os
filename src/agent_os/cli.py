from __future__ import annotations

import argparse
import json
import getpass
from pathlib import Path

from .adapters import sync_adapters
from .candidates import candidate_status, curate_candidates, stage_candidates
from .changes import capture_change, get_change, google_safe_projection, list_changes, promote_change, update_change
from .compiler import compile_context
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
from .mcp_server import serve
from .maintenance import run as run_maintenance
from .mail import health as mail_health, setup_icloud, status as mail_status, sync as mail_sync, search as mail_search
from .registry import get_project, git_status, identify_project, load_state, projects
from .review import assess
from .surfaces import health as integration_health
from .routing import install as install_routing
from .routing import status as routing_status
from .validation import validate
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


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="agent-os")
    commands = root.add_subparsers(dest="command", required=True)
    commands.add_parser("projects")
    scan_projects = commands.add_parser("scan-projects")
    scan_projects.add_argument("--root")
    commands.add_parser("index")
    commands.add_parser("init")
    commands.add_parser("sync-adapters")
    commands.add_parser("install-routing")
    commands.add_parser("routing-status")
    integration = commands.add_parser("integration-health")
    integration.add_argument("--surface")
    integration.add_argument("--strict", action="store_true")
    commands.add_parser("validate")
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
    workflow_complete = commands.add_parser("workflow-complete")
    workflow_complete.add_argument("workflow")
    workflow_complete.add_argument("--run-id", required=True)
    workflow_complete.add_argument("--stage", required=True)
    workflow_complete.add_argument("--output", action="append", default=[])
    workflow_complete.add_argument("--checkpoint")
    workflow_complete.add_argument("--failed", action="store_true")
    workflow_complete.add_argument("--detail")
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
    mail_cmd = commands.add_parser("mail")
    mail_sub = mail_cmd.add_subparsers(dest="mail_command", required=True)
    mail_setup = mail_sub.add_parser("setup")
    mail_setup.add_argument("provider", choices=("icloud",))
    mail_setup.add_argument("--email")
    mail_sub.add_parser("status")
    mail_sub.add_parser("health")
    mail_sync_cmd = mail_sub.add_parser("sync")
    mail_sync_cmd.add_argument("--limit", type=int, default=500)
    mail_search_cmd = mail_sub.add_parser("search")
    mail_search_cmd.add_argument("query")
    mail_search_cmd.add_argument("--limit", type=int, default=10)
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
    return root


def main(argv: list[str] | None = None) -> int:
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
        elif args.command == "validate":
            result = validate()
            _print(result)
            return 0 if result["ok"] else 1
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
            _print(run_stage(args.workflow, args.run_id, args.stage))
        elif args.command == "workflow-complete":
            _print(
                complete_stage(
                    args.workflow,
                    args.run_id,
                    args.stage,
                    outputs=args.output,
                    checkpoint=args.checkpoint,
                    passed=False if args.failed else None,
                    detail=args.detail,
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
            if args.mail_command == "setup":
                address = args.email or input("iCloud email: ").strip()
                password = getpass.getpass("Apple app-specific password: ")
                _print(setup_icloud(address, password))
            elif args.mail_command == "status":
                _print(mail_status())
            elif args.mail_command == "health":
                _print(mail_health())
            elif args.mail_command == "sync":
                _print(mail_sync(args.limit))
            elif args.mail_command == "search":
                _print(mail_search(args.query, args.limit))
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
    except (KeyError, OSError, ValueError) as exc:
        _print({"error": str(exc)})
        return 2
    return 0
