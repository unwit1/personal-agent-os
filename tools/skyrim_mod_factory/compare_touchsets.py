#!/usr/bin/env python3
"""Find likely compatibility overlap between two Skyrim Mod Factory touch sets.

This is a conservative first-pass overlap detector. It reports shared surfaces; it does
not label overlap as a conflict without semantic evidence.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path

def fields_overlap(a:list[str],b:list[str])->list[str]:
    if not a or not b:
        return ["<whole-or-unspecified-record>"]
    sa=set(a); sb=set(b)
    exact=sorted(sa&sb)
    prefix=[]
    for x in sa:
        for y in sb:
            if x==y: continue
            if x.startswith(y+".") or y.startswith(x+"."):
                prefix.append(f"{x} ~ {y}")
    return exact+sorted(set(prefix))

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("left",type=Path)
    ap.add_argument("right",type=Path)
    ap.add_argument("--output",type=Path)
    args=ap.parse_args()
    a=json.loads(args.left.read_text(encoding="utf-8"))
    b=json.loads(args.right.read_text(encoding="utf-8"))

    overlaps=[]

    for x in a.get("records",[]):
      for y in b.get("records",[]):
        same=False; why=""
        if x.get("form_key") and y.get("form_key") and x["form_key"]==y["form_key"]:
            same=True; why="same FormKey"
        elif x.get("signature")==y.get("signature") and x.get("selector") and x.get("selector")==y.get("selector"):
            same=True; why="same signature/selector"
        if same:
            f=fields_overlap(x.get("field_paths",[]),y.get("field_paths",[]))
            if f:
                overlaps.append({"layer":"record","why":why,"left":x,"right":y,"field_overlap":f})

    amap={x.get("path","").lower():x for x in a.get("assets",[]) if x.get("path")}
    bmap={x.get("path","").lower():x for x in b.get("assets",[]) if x.get("path")}
    for p in sorted(set(amap)&set(bmap)):
        overlaps.append({"layer":"asset","why":"same normalized asset path","path":p,"left":amap[p],"right":bmap[p]})

    for x in a.get("runtime_mutations",[]):
      for y in b.get("runtime_mutations",[]):
        if x.get("domain")==y.get("domain"):
            if (not x.get("selector") or not y.get("selector") or x.get("selector")==y.get("selector")):
                overlaps.append({"layer":"runtime","why":"shared mutation domain/selectors may overlap","left":x,"right":y})

    hooks_a={(x.get("subsystem"),x.get("target")) for x in a.get("native_hooks",[]) if isinstance(x,dict)}
    hooks_b={(x.get("subsystem"),x.get("target")) for x in b.get("native_hooks",[]) if isinstance(x,dict)}
    for h in sorted(hooks_a&hooks_b):
        overlaps.append({"layer":"native","why":"same declared hook surface","surface":h})

    result={
      "schema_version":"skyrim-touchset-comparison-v1",
      "left":a.get("project_id"),"right":b.get("project_id"),
      "overlap_count":len(overlaps),
      "overlaps":overlaps,
      "interpretation":"Overlap is a review signal, not proof of incompatibility."
    }
    text=json.dumps(result,indent=2)+"\n"
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(text,encoding="utf-8")
    else:
        print(text,end="")

if __name__=="__main__":
    main()
