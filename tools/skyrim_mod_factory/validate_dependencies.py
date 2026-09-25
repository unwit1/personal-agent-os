#!/usr/bin/env python3
"""Validate a Skyrim Mod Factory dependency lock and flag release-blocking unknowns."""
from __future__ import annotations
import argparse, json, re, sys
from pathlib import Path

SHIPPED={"bundled","generated-derivative","permission-required"}
LINKED={"static","source-copy","asset-derivative"}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("lock",type=Path)
    args=ap.parse_args()
    d=json.loads(args.lock.read_text(encoding="utf-8"))
    errors=[]; warnings=[]

    if d.get("schema_version")!="skyrim-dependency-lock-v1":
        errors.append("schema_version must be skyrim-dependency-lock-v1")

    seen=set()
    for i,x in enumerate(d.get("dependencies",[])):
        p=f"dependencies[{i}]"
        ident=x.get("id")
        if not ident or not re.fullmatch(r"[a-z0-9][a-z0-9._-]*",ident):
            errors.append(f"{p}: invalid id")
        elif ident in seen:
            errors.append(f"{p}: duplicate id {ident}")
        seen.add(ident)

        if not x.get("source"):
            errors.append(f"{p}: source is required")
        if not x.get("version") and not x.get("commit") and x.get("role")!="official-game-data":
            warnings.append(f"{p} {ident}: no version or commit pin")

        red=x.get("redistribution","unknown")
        lic=x.get("license_status","unknown")
        link=x.get("linkage","unknown")

        if red in SHIPPED and lic=="unknown":
            errors.append(f"{p} {ident}: shipped/derived dependency has unknown license status")
        if link in LINKED and lic=="unknown":
            errors.append(f"{p} {ident}: linked/copied dependency has unknown license status")
        if red in {"permission-required","generated-derivative"} and not x.get("permission_evidence"):
            warnings.append(f"{p} {ident}: redistribution/derivative permission evidence is empty")
        if red=="bundled" and not x.get("sha256") and x.get("role") not in {"asset-source","official-game-data"}:
            warnings.append(f"{p} {ident}: bundled binary/package has no checksum")
        if x.get("update_policy")=="follow-latest-candidate":
            warnings.append(f"{p} {ident}: latest updates must remain candidate-only until regression gates pass")

    result={"valid":not errors,"dependencies":len(d.get("dependencies",[])),"errors":errors,"warnings":warnings}
    print(json.dumps(result,indent=2))
    sys.exit(1 if errors else 0)

if __name__=="__main__":
    main()
