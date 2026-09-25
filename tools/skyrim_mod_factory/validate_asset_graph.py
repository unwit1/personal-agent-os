#!/usr/bin/env python3
"""Validate a Skyrim asset-reference graph against one or more materialized file roots."""
from __future__ import annotations
import argparse, json, os, sys
from pathlib import Path

def norm(s:str)->str:
    return s.replace("\\","/").lstrip("/").lower()

def inventory(roots:list[Path]):
    exact={}; folded={}
    for root in roots:
        if not root.exists(): continue
        for p in root.rglob("*"):
            if not p.is_file(): continue
            rel=p.relative_to(root).as_posix()
            exact.setdefault(rel,[]).append(str(p))
            folded.setdefault(rel.lower(),[]).append({"relative":rel,"full":str(p)})
    return exact,folded

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("graph",type=Path)
    ap.add_argument("--root",type=Path,action="append",default=[])
    ap.add_argument("--file-list",type=Path,
                    help="Optional newline-separated deployed/VFS relative paths")
    ap.add_argument("--output",type=Path)
    args=ap.parse_args()
    g=json.loads(args.graph.read_text(encoding="utf-8"))
    if g.get("schema_version")!="skyrim-asset-graph-v1":
        raise SystemExit("Wrong schema_version")

    exact,folded=inventory(args.root)
    if args.file_list:
        for raw in args.file_list.read_text(encoding="utf-8",errors="replace").splitlines():
            rel=raw.strip().replace("\\","/").lstrip("/")
            if rel:
                exact.setdefault(rel,[]).append("<file-list>")
                folded.setdefault(rel.lower(),[]).append({"relative":rel,"full":"<file-list>"})

    missing=[]; case_mismatch=[]; duplicates=[]; resolved=[]
    allowed=[x.lower().replace("\\","/") for x in g.get("allowed_external",[])]

    for ref in g.get("references",[]):
        rel=ref["path"].replace("\\","/").lstrip("/")
        low=rel.lower()
        matches=folded.get(low,[])
        external=any(low.startswith(p.rstrip("*")) for p in allowed)
        if not matches:
            if ref.get("required",True) and not external:
                missing.append(ref)
            continue
        resolved.append({"reference":ref,"matches":matches})
        if rel not in exact:
            case_mismatch.append({"reference":ref,"matches":matches})
        if len(matches)>1:
            duplicates.append({"reference":ref,"matches":matches})

    result={
      "schema_version":"skyrim-asset-closure-report-v1",
      "project_id":g.get("project_id"),
      "reference_count":len(g.get("references",[])),
      "resolved_count":len(resolved),
      "missing_required":missing,
      "case_mismatches":case_mismatch,
      "duplicate_candidates":duplicates,
      "valid":not missing
    }
    text=json.dumps(result,indent=2)+"\n"
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(text,encoding="utf-8")
    else:
        print(text,end="")
    sys.exit(1 if missing else 0)

if __name__=="__main__":
    main()
