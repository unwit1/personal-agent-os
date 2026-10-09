"""`agent-os intake ...` commands."""

from __future__ import annotations

import argparse
from typing import Any, Callable


def register(commands: argparse._SubParsersAction) -> None:
    intake = commands.add_parser("intake", help="universal intake: connected sources -> scoped directories -> ingestion queue")
    sub = intake.add_subparsers(dest="intake_command", required=True)
    run = sub.add_parser("run", help="sync mail, rebuild correspondence directories and dossiers, queue everything, feed the Engine")
    run.add_argument("--no-sync", action="store_true")
    run.add_argument("--no-drain", action="store_true")
    run.add_argument("--drain-limit", type=int)
    run.add_argument("--classify-limit", type=int, help="model reviews per scope this run (0 = none)")
    sub.add_parser("status", help="queue counts per scope, source, flag and consumer")
    collect = sub.add_parser("collect", help="run the source adapters only")
    collect.add_argument("--source", action="append")
    drain = sub.add_parser("drain", help="ingest pending items into the scope's Engine knowledge base")
    drain.add_argument("--scope", choices=["work", "personal"], required=True)
    drain.add_argument("--limit", type=int)
    connect = sub.add_parser("connect-folder", help="watch a folder: its files join the given scope's queue")
    connect.add_argument("name")
    connect.add_argument("path")
    connect.add_argument("--scope", choices=["work", "personal"], required=True)
    connect.add_argument("--kind", default="document")
    sub.add_parser("settings", help="show intake settings")
    cls = sub.add_parser("classify", help="model review of undecided / personal-address mail (subscription)")
    cls.add_argument("--scope", choices=["work", "personal"], required=True)
    cls.add_argument("--limit", type=int, default=200)
    prom = sub.add_parser("promote", help="distill PII-free company knowledge candidates from work mail (subscription)")
    prom.add_argument("--batches", type=int, default=1)


def dispatch(args: argparse.Namespace, emit: Callable[[Any], None]) -> int:
    from . import collect, drain_engine, run, save_settings, settings, status

    command = args.intake_command
    if command == "run":
        emit(run(sync=not args.no_sync, drain=not args.no_drain, drain_limit=args.drain_limit, classify_limit=args.classify_limit))
    elif command == "status":
        emit(status())
    elif command == "collect":
        emit(collect(args.source))
    elif command == "drain":
        emit(drain_engine(args.scope, args.limit))
    elif command == "connect-folder":
        data = settings()
        data["folders"] = [f for f in data.get("folders", []) if f["name"] != args.name] + [
            {"name": args.name, "path": args.path, "scope": args.scope, "kind": args.kind}]
        save_settings(data)
        emit({"connected": args.name, "folders": data["folders"]})
    elif command == "settings":
        emit(settings())
    elif command == "classify":
        from .classify import classify

        emit(classify(args.scope, args.limit))
    elif command == "promote":
        from .promote import promote

        emit(promote(args.batches))
    return 0
