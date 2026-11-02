"""``orchestrator <action> ...`` -- the standalone command line.

Same actions, arguments and exit codes as ``agent-os orchestrate <action>``;
both parse with ``orchestrator_os.cli.register``. A leading ``orchestrate`` is
accepted so old scripts keep working.
"""

from __future__ import annotations

import argparse
import json
import sys

from .cli import dispatch, register


def _emit(value: object) -> None:
    print(json.dumps(value, indent=2, default=str, ensure_ascii=False))


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure") and (stream.encoding or "").lower() not in {"utf-8", "utf8"}:
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except (OSError, ValueError):
                pass
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv[:1] != ["orchestrate"]:
        argv = ["orchestrate", *argv]
    parser = argparse.ArgumentParser(prog="orchestrator", description="Orchestrator OS")
    register(parser.add_subparsers(dest="command", required=True))
    args = parser.parse_args(argv)
    try:
        return dispatch(args, _emit)
    except (KeyError, OSError, ValueError, ImportError) as exc:
        _emit({"error": str(exc)})
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
