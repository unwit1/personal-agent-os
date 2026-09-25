#!/usr/bin/env python3
"""Compare two Skyrim semantic plugin JSON documents.

The semantic producer decides how fields are normalized. This comparator intentionally
preserves array order: many Skyrim arrays/conditions are order-sensitive.
"""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
from typing import Any

MISSING=object()

def record_key(r:dict)->str:
    return f'{r.get("signature","????")}:{r.get("form_key","?")}'

def diff_values(a:Any,b:Any,path:str,out:list[dict]):
    if type(a) is not type(b):
        out.append({"path":path,"kind":"type-changed","before":a,"after":b})
        return
    if isinstance(a,dict):
        keys=sorted(set(a)|set(b))
        for k in keys:
            av=a.get(k,MISSING); bv=b.get(k,MISSING)
            p=f"{path}.{k}" if path else k
            if av is MISSING:
                out.append({"path":p,"kind":"added","after":bv})
            elif bv is MISSING:
                out.append({"path":p,"kind":"removed","before":av})
            else:
                diff_values(av,bv,p,out)
    elif isinstance(a,list):
        if a!=b:
            out.append({"path":path,"kind":"list-changed","before":a,"after":b})
    elif a!=b:
        out.append({"path":path,"kind":"changed","before":a,"after":b})

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("before",type=Path)
    ap.add_argument("after",type=Path)
    ap.add_argument("--output",type=Path)
    ap.add_argument("--fail-on-diff",action="store_true")
    args=ap.parse_args()

    a=json.loads(args.before.read_text(encoding="utf-8"))
    b=json.loads(args.after.read_text(encoding="utf-8"))
    if a.get("schema_version")!="skyrim-semantic-plugin-v1" or b.get("schema_version")!="skyrim-semantic-plugin-v1":
        raise SystemExit("Both inputs must use skyrim-semantic-plugin-v1")

    ar={record_key(x):x for x in a.get("records",[])}
    br={record_key(x):x for x in b.get("records",[])}
    added=sorted(set(br)-set(ar))
    removed=sorted(set(ar)-set(br))
    changed=[]
    for key in sorted(set(ar)&set(br)):
        diffs=[]
        diff_values(ar[key],br[key],"",diffs)
        if diffs:
            changed.append({"record":key,"changes":diffs})

    plugin_changes=[]
    diff_values(a.get("plugin",{}),b.get("plugin",{}),"plugin",plugin_changes)
    result={
      "schema_version":"skyrim-semantic-plugin-diff-v1",
      "before":str(args.before),
      "after":str(args.after),
      "summary":{
        "records_before":len(ar),
        "records_after":len(br),
        "added":len(added),
        "removed":len(removed),
        "changed":len(changed),
        "plugin_header_changes":len(plugin_changes)
      },
      "plugin_changes":plugin_changes,
      "records_added":added,
      "records_removed":removed,
      "records_changed":changed
    }
    text=json.dumps(result,indent=2)+"\n"
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(text,encoding="utf-8")
    else:
        print(text,end="")
    has_diff=bool(added or removed or changed or plugin_changes)
    if args.fail_on_diff and has_diff:
        sys.exit(2)

if __name__=="__main__":
    main()
