#!/usr/bin/env python3
"""Extract candidate Skyrim record signatures from xEdit Pascal definitions.

This is a deliberately conservative lexical extractor. It inventories definitions
for review; it is not a Delphi parser and must not be used to mutate plugins.
"""
from __future__ import annotations
import argparse, json, re
from pathlib import Path

SIG_RE = re.compile(r"wbRecord\s*\(\s*([^,\n]+)", re.I)
LIT_RE = re.compile(r"'([A-Z0-9_]{4})'")
SIGFUNC_RE = re.compile(r"wbSignature\s*\(\s*'([A-Z0-9_]{4})'\s*\)", re.I)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("xedit_source",type=Path)
    ap.add_argument("--json",type=Path,required=True)
    ap.add_argument("--provenance",required=True,
                    help="Exact TES5Edit tag/commit + retrieval date")
    args=ap.parse_args()
    hits={}
    for path in sorted(args.xedit_source.rglob("*.pas")):
        txt=path.read_text(encoding="utf-8",errors="replace")
        lines=txt.splitlines()
        for i,line in enumerate(lines,1):
            if "wbRecord" not in line:
                continue
            window="\n".join(lines[i-1:min(i+8,len(lines))])
            sigs=set(SIGFUNC_RE.findall(window))
            if not sigs:
                sigs.update(LIT_RE.findall(window[:500]))
            for sig in sigs:
                hits.setdefault(sig,[]).append({
                    "file":str(path.relative_to(args.xedit_source)),
                    "line":i,
                    "context":line.strip()[:300],
                })
    payload={
        "provenance":args.provenance,
        "warning":"Candidate lexical inventory; validate against xEdit definitions before canonical promotion.",
        "record_signatures":dict(sorted(hits.items())),
    }
    args.json.parent.mkdir(parents=True,exist_ok=True)
    args.json.write_text(json.dumps(payload,indent=2),encoding="utf-8")
    print(f"Found {len(hits)} candidate record signatures")

if __name__=="__main__":
    main()
