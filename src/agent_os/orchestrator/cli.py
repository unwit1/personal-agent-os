"""`agent-os orchestrate ...` -- headless control of orchestrated runs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from . import service


TERMINAL_EXIT = {"COMPLETE": 0, "PAUSED": 3, "APPROVAL_REQUIRED": 4, "BLOCKED": 5, "FAILED": 5}


def register(commands: argparse._SubParsersAction) -> None:
    orchestrate = commands.add_parser("orchestrate", help="multi-agent coding orchestrator")
    actions = orchestrate.add_subparsers(dest="orchestrate_action", required=True)

    providers = actions.add_parser("providers", help="show configured providers and routing recommendations")
    providers.add_argument("--suggest", action="store_true", help="probe installed coding CLIs and suggest registry entries")
    providers.add_argument("--write", action="store_true", help="with --suggest: add missing entries to the machine-local registry")
    providers.add_argument("--force", action="store_true", help="with --write: replace existing entries of the same id")
    providers.add_argument("--path")

    create = actions.add_parser("create", help="create a run")
    _create_arguments(create)
    create.add_argument("--start", action="store_true")
    create.add_argument("--auto-continue", action="store_true")

    recommended = actions.add_parser("start-recommended", help="plan, start with Auto Continue, and drive until a stop state")
    _create_arguments(recommended)
    recommended.add_argument("--max-seconds", type=float)
    recommended.add_argument("--no-drive", action="store_true", help="create and start, but return without driving")

    for name in ("status", "result", "step", "events", "pause", "resume", "stop"):
        parser = actions.add_parser(name)
        parser.add_argument("run_id")
        if name == "events":
            parser.add_argument("--after", type=int, default=0)
    actions.add_parser("list")

    start = actions.add_parser("start")
    start.add_argument("run_id")
    start.add_argument("--auto-continue", dest="auto_continue", action="store_true", default=None)
    start.add_argument("--no-auto-continue", dest="auto_continue", action="store_false")

    run = actions.add_parser("run", help="drive a run in the foreground (Auto Continue: until a stop state)")
    run.add_argument("run_id")
    run.add_argument("--max-seconds", type=float)
    run.add_argument("--max-ticks", type=int)

    for name in ("approve", "reject"):
        parser = actions.add_parser(name)
        parser.add_argument("run_id")
        parser.add_argument("gate_id")
        parser.add_argument("--note")

    for name in ("retry", "review-again"):
        parser = actions.add_parser(name)
        parser.add_argument("run_id")
        parser.add_argument("node_id")

    reassign = actions.add_parser("reassign")
    reassign.add_argument("run_id")
    reassign.add_argument("node_id")
    reassign.add_argument("--provider", required=True)
    reassign.add_argument("--model")
    reassign.add_argument("--effort")

    override = actions.add_parser("override", help="provider/model/effort override for the run, a role, or a node")
    override.add_argument("run_id")
    override.add_argument("--provider")
    override.add_argument("--model")
    override.add_argument("--effort")
    target = override.add_mutually_exclusive_group()
    target.add_argument("--role")
    target.add_argument("--node")
    override.add_argument("--clear", action="store_true")

    road = actions.add_parser("roadmap", help="show roadmap progress and the next eligible stage (no model call)")
    road.add_argument("--project")
    road.add_argument("--repo")

    cont = actions.add_parser("continue-roadmap", help="Continue Roadmap: resume unfinished work or start the next roadmap stage, then drive it")
    cont.add_argument("--project")
    cont.add_argument("--repo")
    cont.add_argument("--until-done", action="store_true", help="Auto Continue Until Done: after each stage completes and lands, start the next")
    cont.add_argument("--fresh", action="store_true", help="set aside unfinished runs instead of resuming them")
    cont.add_argument("--preference", choices=["economy", "balanced", "quality"])
    cont.add_argument("--no-drive", action="store_true", help="prepare and start, but return without driving")

    report = actions.add_parser("report", help="efficiency report for a run from its telemetry (tokens, calls, context, avoided work)")
    report.add_argument("run_id")
    report.add_argument("--transcript", action="store_true", help="print the human-readable run transcript instead")

    bench = actions.add_parser("benchmark", help="repeatable token-efficiency benchmark (offline by default; --live uses real providers)")
    bench.add_argument("--scenario", action="append", help="run only these scenarios (repeatable)")
    bench.add_argument("--live", action="store_true", help="use the machine's real providers (costs usage) for the small-code-change scenario")
    bench.add_argument("--out", help="directory for results.json and report.md")

    gui = actions.add_parser("gui", help="serve the local control GUI and API")
    gui.add_argument("--host", default="127.0.0.1")
    gui.add_argument("--port", type=int, default=8765)
    gui.add_argument("--no-browser", action="store_true")
    gui.add_argument("--project", help="registered project shown on the Simple Mode home screen")
    gui.add_argument("--repo", help="repository path for Simple Mode when the project is not registered")


def _create_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--goal", required=True)
    parser.add_argument("--repo", help="path inside the target Git repository")
    parser.add_argument("--project", help="registered Agent OS project id")
    parser.add_argument("--tasks", help="JSON file with an explicit task list")
    parser.add_argument("--policy", help="JSON file with run policy overrides")
    parser.add_argument("--set", action="append", default=[], metavar="KEY=VALUE", help="policy override; VALUE is parsed as JSON when possible")
    parser.add_argument("--validator", action="append", default=[], help="default validator command (shell string), repeatable")
    parser.add_argument("--run-id")


def _policy(args: argparse.Namespace) -> dict[str, Any]:
    policy: dict[str, Any] = {}
    if args.policy:
        policy.update(json.loads(Path(args.policy).read_text(encoding="utf-8-sig")))
    for item in args.set:
        key, _, raw = item.partition("=")
        try:
            policy[key.strip()] = json.loads(raw)
        except json.JSONDecodeError:
            policy[key.strip()] = raw
    if args.validator:
        policy["default_validators"] = [
            *policy.get("default_validators", []),
            *({"kind": "command", "command": command} for command in args.validator),
        ]
    return policy


def _tasks(args: argparse.Namespace) -> list[dict[str, Any]] | None:
    if not args.tasks:
        return None
    data = json.loads(Path(args.tasks).read_text(encoding="utf-8-sig"))
    return data.get("tasks") if isinstance(data, dict) else data


def dispatch(args: argparse.Namespace, emit) -> int:
    action = args.orchestrate_action
    if action == "providers":
        emit(service.suggest_providers(args.write, args.path, args.force) if args.suggest else service.providers())
        return 0
    if action == "create":
        emit(service.create(args.goal, args.repo, args.project, _tasks(args), _policy(args), run_id=args.run_id, start=args.start, auto_continue=True if args.auto_continue else None))
        return 0
    if action == "start-recommended":
        policy = _policy(args)
        tasks = _tasks(args)
        if tasks:
            summary = service.create(args.goal, args.repo, args.project, tasks, {**policy, "auto_continue": True}, run_id=args.run_id, start=True, auto_continue=True)
        else:
            summary = service.start_recommended(args.goal, args.repo, args.project, policy, run_id=args.run_id)
        if args.no_drive:
            emit(summary)
            return 0
        final = service.engine().run_loop(summary["run_id"], max_seconds=args.max_seconds, owner="cli")
        emit(final)
        return TERMINAL_EXIT.get(final["state"], 0)
    if action == "list":
        emit(service.list_runs())
        return 0
    if action == "status":
        emit(service.status(args.run_id))
        return 0
    if action == "result":
        emit(service.result(args.run_id))
        return 0
    if action == "events":
        emit(service.events(args.run_id, args.after))
        return 0
    if action == "step":
        emit(service.step(args.run_id))
        return 0
    if action == "start":
        emit(service.engine().start(args.run_id, args.auto_continue))
        return 0
    if action in {"pause", "resume", "stop"}:
        emit(service.control(args.run_id, action))
        return 0
    if action == "run":
        final = service.engine().run_loop(args.run_id, max_seconds=args.max_seconds, max_ticks=args.max_ticks, owner="cli")
        emit(final)
        return TERMINAL_EXIT.get(final["state"], 0)
    if action in {"approve", "reject"}:
        emit(service.decide(args.run_id, args.gate_id, action == "approve", args.note))
        return 0
    if action == "retry":
        emit(service.retry(args.run_id, args.node_id))
        return 0
    if action == "review-again":
        emit(service.review_again(args.run_id, args.node_id))
        return 0
    if action == "reassign":
        emit(service.reassign(args.run_id, args.node_id, args.provider, args.model, args.effort))
        return 0
    if action == "override":
        emit(service.override(args.run_id, args.provider, args.model, args.effort, args.role, args.node, args.clear))
        return 0
    if action == "roadmap":
        from .roadmap import overview

        emit(overview(service.engine(), args.project, args.repo))
        return 0
    if action == "continue-roadmap":
        from .roadmap import continue_roadmap, drive_campaign

        engine = service.engine()
        result = continue_roadmap(engine, args.project, args.repo, auto_until_done=args.until_done, preference=args.preference, fresh=args.fresh)
        if args.no_drive or result["action"] not in {"started", "resumed"}:
            emit(result)
            return 0 if result["action"] != "error" else 2
        if args.until_done:
            campaign = drive_campaign(engine, args.project, args.repo)
            emit({**result, "campaign": campaign, "final": engine.status(campaign.get("current_run") or result["run_id"])["state"]})
            return 0
        final = engine.run_loop(result["run_id"], owner="cli")
        emit({**result, "final_state": final["state"], "state_reason": final.get("state_reason")})
        return TERMINAL_EXIT.get(final["state"], 0)
    if action == "report":
        engine = service.engine()
        if args.transcript:
            path = engine.ledger.paths(args.run_id)[1]
            print(path.read_text(encoding="utf-8") if path.exists() else f"no transcript at {path}")
            return 0
        emit(engine.efficiency(args.run_id))
        return 0
    if action == "benchmark":
        from .benchmark import run_benchmark

        report = run_benchmark(args.scenario, live=args.live, out_dir=Path(args.out) if args.out else None)
        emit({"files": report["files"], "totals": report["totals"], "scenarios": [{key: item[key] for key in ("scenario", "scenario_passed", "model_calls", "model_calls_avoided", "local_operations", "cache_hits", "escalations", "runtime_s")} for item in report["scenarios"]]})
        return 0 if report["totals"]["passed"] == report["totals"]["scenarios"] else 1
    if action == "gui":
        from .server import serve

        return serve(args.host, args.port, open_browser=not args.no_browser, project=args.project, repository=args.repo)
    raise ValueError(f"unknown orchestrate action {action}")
