#!/usr/bin/env python3
"""Filter a JSONL asset manifest by explicit training-rights state.

This is a project-policy gate, not legal advice. It prevents assets collected for research,
metadata, or retrieval from accidentally entering model-training jobs.

Input asset records may contain:
  training_rights_status
or:
  training_rights: {"status": ...}

By default only the four explicitly allowed states pass.
"""
from __future__ import annotations
import argparse,json
from collections import Counter
from pathlib import Path

DEFAULT_ALLOWED={
 "allowed_open",
 "allowed_user_captured",
 "allowed_with_attribution",
 "allowed_by_specific_permission",
}

def status_of(r):
    rights=r.get("training_rights")
    if isinstance(rights,dict) and rights.get("status"):
        return str(rights["status"])
    return str(r.get("training_rights_status") or "unknown")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--input",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True)
    ap.add_argument("--rejected-output",type=Path)
    ap.add_argument("--allow-status",action="append",default=[])
    args=ap.parse_args()
    allowed=set(args.allow_status) if args.allow_status else set(DEFAULT_ALLOWED)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    reject_path=args.rejected_output or args.output.with_name(args.output.stem+"_rejected.jsonl")
    reject_path.parent.mkdir(parents=True,exist_ok=True)
    counts=Counter()
    with args.input.open("r",encoding="utf-8") as src,args.output.open("w",encoding="utf-8") as ok,reject_path.open("w",encoding="utf-8") as bad:
        for line in src:
            if not line.strip(): continue
            r=json.loads(line); s=status_of(r); counts[s]+=1
            if s in allowed:
                ok.write(json.dumps(r,ensure_ascii=False)+"\n");counts["passed"]+=1
            else:
                rejected=dict(r)
                rejected["training_gate_rejection"]={"status":s,"reason":"status_not_in_allowed_set"}
                bad.write(json.dumps(rejected,ensure_ascii=False)+"\n");counts["rejected"]+=1
    print(json.dumps({"allowed_statuses":sorted(allowed),"counts":dict(counts),"output":str(args.output),"rejected_output":str(reject_path)},indent=2))

if __name__=="__main__":main()
