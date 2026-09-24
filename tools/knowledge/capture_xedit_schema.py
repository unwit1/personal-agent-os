#!/usr/bin/env python3
"""Capture xEdit's own plugin-definition export through xDump/xExport.

The xEdit xDump program determines tool mode and game mode from either executable
name or command-line switches. Current source documents:
  <Game>Export [options] RAW|UESPWIKI
and accepts -Export plus a game-mode switch such as -SSE.

This wrapper preserves stdout plus exact command/provenance instead of trying to
reverse engineer Delphi schema construction.
"""
from __future__ import annotations
import argparse, datetime as dt, hashlib, json, subprocess
from pathlib import Path

def sha256(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("executable",type=Path,
                    help="Built xDump/xExport executable from the exact xEdit source/release")
    ap.add_argument("--game",default="SSE",
                    help="xEdit game mode switch, e.g. SSE, TES5, TES5VR")
    ap.add_argument("--format",choices=["RAW","UESPWIKI"],default="RAW")
    ap.add_argument("--output",type=Path,required=True)
    ap.add_argument("--metadata",type=Path,required=True)
    ap.add_argument("--source",required=True,
                    help="Exact upstream URL/tag/commit used to build the executable")
    args=ap.parse_args()

    exe=args.executable.resolve()
    if not exe.exists():
        raise SystemExit(f"Executable not found: {exe}")

    cmd=[str(exe),"-Export",f"-{args.game}",args.format]
    proc=subprocess.run(cmd,capture_output=True,text=True,encoding="utf-8",
                        errors="replace",check=False)

    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.metadata.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(proc.stdout,encoding="utf-8")
    meta={
        "captured_at_utc":dt.datetime.now(dt.timezone.utc).isoformat(),
        "source":args.source,
        "executable":str(exe),
        "executable_sha256":sha256(exe),
        "game_mode":args.game,
        "format":args.format,
        "command":cmd,
        "return_code":proc.returncode,
        "stderr":proc.stderr,
        "output_bytes":len(proc.stdout.encode("utf-8")),
    }
    args.metadata.write_text(json.dumps(meta,indent=2),encoding="utf-8")
    if proc.returncode:
        raise SystemExit(proc.returncode)
    print(f"Captured {args.format} {args.game} schema to {args.output}")

if __name__=="__main__":
    main()
