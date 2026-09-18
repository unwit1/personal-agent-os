from __future__ import annotations

import argparse
import json
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
from .mcp_server import serve
from .maintenance import run as run_maintenance
from .registry import get_project, git_status, identify_project, load_state, projects
from .review import assess
from .routing import install as install_routing
from .routing import status as routing_status
from .validation import validate


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
    commands.add_parser("validate")
    commands.add_parser("mcp")
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
        elif args.command == "validate":
            result = validate()
            _print(result)
            return 0 if result["ok"] else 1
        elif args.command == "mcp":
            return serve()
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
