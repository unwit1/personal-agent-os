#!/usr/bin/env python3
"""Capture selected decoded records from official Skyrim master plugins using xDump.

Designed for local use on an authorized game installation. Raw Bethesda master dumps
are derived from copyrighted game data and should stay in local/high-volume storage;
only normalized technical facts that pass review should be promoted to Git.
"""
from __future__ import annotations
import argparse, datetime as dt, hashlib, json, subprocess
from pathlib import Path

DEFAULT_SIGNATURES = [
    "GMST","DOBJ","AVIF","MGEF","SPEL","PERK","RACE","CSTY","CLAS",
    "WTHR","CLMT","LGTM","IMGS","ECZN","LCTN","MUSC","SNDR","SOPM",
]

def sha256(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("xdump",type=Path)
    ap.add_argument("master",type=Path)
    ap.add_argument("--game",default="SSE")
    ap.add_argument("--records",default=",".join(DEFAULT_SIGNATURES),
                    help="Comma-separated record signatures passed to xDump -dr:")
    ap.add_argument("--output-dir",type=Path,required=True)
    ap.add_argument("--source-note",default="local authorized Skyrim installation")
    args=ap.parse_args()

    xdump=args.xdump.resolve()
    master=args.master.resolve()
    if not xdump.exists():
        raise SystemExit(f"xDump executable not found: {xdump}")
    if not master.exists():
        raise SystemExit(f"Master plugin not found: {master}")

    args.output_dir.mkdir(parents=True,exist_ok=True)
    stem=master.name.replace(".","_")
    dump_path=args.output_dir/f"{stem}.xdump.txt"
    meta_path=args.output_dir/f"{stem}.metadata.json"

    cmd=[str(xdump),"-Dump",f"-{args.game}",f"-dr:{args.records}",str(master)]
    proc=subprocess.run(cmd,capture_output=True,text=True,encoding="utf-8",
                        errors="replace",check=False)
    dump_path.write_text(proc.stdout,encoding="utf-8")
    meta={
      "captured_at_utc":dt.datetime.now(dt.timezone.utc).isoformat(),
      "source_note":args.source_note,
      "game_mode":args.game,
      "master_path":str(master),
      "master_sha256":sha256(master),
      "xdump_path":str(xdump),
      "xdump_sha256":sha256(xdump),
      "record_filter":args.records.split(","),
      "command":cmd,
      "return_code":proc.returncode,
      "stderr":proc.stderr,
      "raw_output_policy":"local-only; do not commit wholesale Bethesda master dump",
    }
    meta_path.write_text(json.dumps(meta,indent=2),encoding="utf-8")
    if proc.returncode:
        raise SystemExit(proc.returncode)
    print(f"Captured {master.name} -> {dump_path}")

if __name__=="__main__":
    main()
