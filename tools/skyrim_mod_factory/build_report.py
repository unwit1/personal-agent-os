#!/usr/bin/env python3
"""Create or update a Skyrim Mod Factory build report from step records."""
from __future__ import annotations
import argparse, datetime as dt, hashlib, json, uuid
from pathlib import Path

def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()

def sha256(path:Path):
    h=hashlib.sha256(path.read_bytes())
    return h.hexdigest()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("manifest",type=Path)
    ap.add_argument("--output",type=Path,required=True)
    ap.add_argument("--step",type=Path,action="append",default=[])
    ap.add_argument("--status",choices=["running","passed","failed","needs-review","cancelled"],default="running")
    ap.add_argument("--git-commit")
    args=ap.parse_args()

    manifest=json.loads(args.manifest.read_text(encoding="utf-8"))
    existing={}
    if args.output.exists():
        existing=json.loads(args.output.read_text(encoding="utf-8"))

    steps=existing.get("steps",[])
    known={s.get("id") for s in steps}
    for p in args.step:
        s=json.loads(p.read_text(encoding="utf-8"))
        if s.get("id") in known:
            steps=[s if x.get("id")==s.get("id") else x for x in steps]
        else:
            steps.append(s); known.add(s.get("id"))

    report={
      "schema_version":"skyrim-mod-build-report-v1",
      "project_id":manifest.get("project_id"),
      "build_id":existing.get("build_id") or str(uuid.uuid4()),
      "git_commit":args.git_commit or existing.get("git_commit"),
      "manifest_sha256":sha256(args.manifest),
      "started_at":existing.get("started_at") or now(),
      "finished_at":now() if args.status!="running" else existing.get("finished_at"),
      "status":args.status,
      "runtime_context":existing.get("runtime_context",{}),
      "steps":steps,
      "gates":existing.get("gates",[]),
      "artifacts":existing.get("artifacts",[]),
      "known_issues":existing.get("known_issues",[]),
      "human_checks_remaining":existing.get("human_checks_remaining",(manifest.get("validation") or {}).get("human_checks",[]))
    }
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(args.output)

if __name__=="__main__":
    main()
