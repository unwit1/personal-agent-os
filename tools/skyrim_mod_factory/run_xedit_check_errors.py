#!/usr/bin/env python3
"""Run xEdit CheckForErrors for one plugin and parse its log into typed evidence.

The wrapper is Windows/xEdit-facing but remains deterministic:
- command construction uses upstream xEdit tool-mode switches;
- execution is opt-in with --execute;
- a dedicated log path is cleared before launch to prevent stale PASS reuse;
- the resulting log is always parsed by parse_xedit_check_errors.py;
- process success never overrides parser FAIL/needs-review.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
from pathlib import Path
from typing import Any

HERE=Path(__file__).resolve().parent

def load_module(name:str,path:Path):
    spec=importlib.util.spec_from_file_location(name,path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load {path}")
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

PARSER=load_module(
    "parse_xedit_check_errors",
    HERE/"parse_xedit_check_errors.py",
)

SUPPORTED_GAME_MODES={"SSE","TES5","TES5VR","ENDERALSE","ENDERAL"}

def build_command(
    executable:Path,
    plugin:str,
    log_path:Path,
    *,
    game_mode:str="SSE",
    data_path:Path|None=None,
    plugins_file:Path|None=None,
    autoexit:bool=True,
    extra_args:list[str]|None=None,
)->list[str]:
    mode=game_mode.upper()
    if mode not in SUPPORTED_GAME_MODES:
        raise ValueError(
            f"unsupported Skyrim xEdit game mode {game_mode!r}; "
            f"expected one of {sorted(SUPPORTED_GAME_MODES)}"
        )
    if not plugin.lower().endswith((".esm",".esp",".esl")):
        raise ValueError("plugin must end in .esm, .esp, or .esl")
    if any(x in plugin for x in ("\n","\r","\x00")):
        raise ValueError("plugin contains an invalid control character")

    command=[
        str(executable),
        f"-{mode}",
        "-checkforerrors",
        f"-quickedit:{plugin}",
        "-autoload",
        f"-R:{log_path}",
    ]
    if autoexit:
        command.append("-autoexit")
    if data_path is not None:
        command.append(f"-D:{data_path}")
    if plugins_file is not None:
        command.append(f"-P:{plugins_file}")
    command.extend(extra_args or [])
    return command

def run_check(
    executable:Path,
    plugin:str,
    log_path:Path,
    *,
    game_mode:str="SSE",
    data_path:Path|None=None,
    plugins_file:Path|None=None,
    autoexit:bool=True,
    extra_args:list[str]|None=None,
    timeout_seconds:int=900,
    tool_version:str|None=None,
)->dict[str,Any]:
    if not executable.is_file():
        raise ValueError(f"xEdit executable not found: {executable}")
    log_path.parent.mkdir(parents=True,exist_ok=True)
    if log_path.exists():
        log_path.unlink()

    command=build_command(
        executable,
        plugin,
        log_path,
        game_mode=game_mode,
        data_path=data_path,
        plugins_file=plugins_file,
        autoexit=autoexit,
        extra_args=extra_args,
    )
    try:
        proc=subprocess.run(
            command,
            cwd=str(executable.parent),
            text=True,
            capture_output=True,
            timeout=timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise ValueError(
            f"xEdit CheckForErrors timed out after {timeout_seconds} seconds"
        ) from exc

    if not log_path.exists():
        raise ValueError(
            "xEdit process did not create the requested log; "
            f"exit_code={proc.returncode}; stderr={proc.stderr[-2000:]!r}"
        )

    report=PARSER.parse_text(
        log_path.read_text(encoding="utf-8",errors="replace"),
        source_log=str(log_path),
    )
    report["tool"]=executable.name
    report["tool_version"]=tool_version
    report["game_mode"]=game_mode.upper()
    if not report.get("target"):
        report["target"]=plugin
    if proc.returncode!=0:
        report.setdefault("issues",[]).append(
            f"xEdit process exit code was {proc.returncode}"
        )
        if report["status"]=="pass":
            report["status"]="needs-review"

    errors=PARSER.schema_errors(report)
    if errors:
        raise ValueError(
            "xEdit CheckForErrors wrapper produced invalid report: "
            +"; ".join(errors)
        )
    return {
        "command":command,
        "exit_code":proc.returncode,
        "stdout":proc.stdout,
        "stderr":proc.stderr,
        "report":report,
    }

def main()->None:
    ap=argparse.ArgumentParser()
    ap.add_argument("executable",type=Path)
    ap.add_argument("plugin")
    ap.add_argument("--log",type=Path,required=True)
    ap.add_argument("--output",type=Path)
    ap.add_argument("--game-mode",default="SSE")
    ap.add_argument("--data-path",type=Path)
    ap.add_argument("--plugins-file",type=Path)
    ap.add_argument("--tool-version")
    ap.add_argument("--timeout-seconds",type=int,default=900)
    ap.add_argument("--no-autoexit",action="store_true")
    ap.add_argument("--extra-arg",action="append",default=[])
    ap.add_argument("--execute",action="store_true")
    args=ap.parse_args()

    command=build_command(
        args.executable,
        args.plugin,
        args.log,
        game_mode=args.game_mode,
        data_path=args.data_path,
        plugins_file=args.plugins_file,
        autoexit=not args.no_autoexit,
        extra_args=args.extra_arg,
    )
    if not args.execute:
        print(json.dumps({"dry_run":True,"command":command},indent=2))
        return

    try:
        result=run_check(
            args.executable,
            args.plugin,
            args.log,
            game_mode=args.game_mode,
            data_path=args.data_path,
            plugins_file=args.plugins_file,
            autoexit=not args.no_autoexit,
            extra_args=args.extra_arg,
            timeout_seconds=args.timeout_seconds,
            tool_version=args.tool_version,
        )
    except ValueError as exc:
        raise SystemExit(str(exc))

    report=result["report"]
    rendered=json.dumps(report,indent=2)+"\n"
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(rendered,encoding="utf-8")
    else:
        print(rendered,end="")

    if report["status"]=="fail":
        raise SystemExit(2)
    if report["status"]=="needs-review":
        raise SystemExit(3)

if __name__=="__main__":
    main()
