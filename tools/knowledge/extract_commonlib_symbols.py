#!/usr/bin/env python3
"""Extract a reviewable CommonLibSSE-NG symbol graph from Doxygen XML.

Run Doxygen against the exact CommonLib checkout first. Doxygen XML is used instead
of regexing C++ headers so classes/methods/namespaces/locations retain structure.
"""
from __future__ import annotations
import argparse, json
import xml.etree.ElementTree as ET
from pathlib import Path

def text_of(node, tag):
    child = node.find(tag)
    return "".join(child.itertext()).strip() if child is not None else None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("xml_root", type=Path)
    ap.add_argument("--json", type=Path, required=True)
    ap.add_argument("--provenance", required=True,
                    help="Exact CommonLib repo/tag/commit + retrieval date")
    args = ap.parse_args()
    compounds = []
    for path in sorted(args.xml_root.glob("*.xml")):
        try:
            root = ET.parse(path).getroot()
        except ET.ParseError:
            continue
        for comp in root.findall(".//compounddef"):
            kind = comp.get("kind")
            if kind not in {"class","struct","namespace","file"}:
                continue
            name = text_of(comp, "compoundname")
            members = []
            for member in comp.findall(".//memberdef"):
                mkind = member.get("kind")
                if mkind not in {"function","variable","enum","typedef"}:
                    continue
                loc = member.find("location")
                members.append({
                    "kind": mkind,
                    "name": text_of(member, "name"),
                    "definition": text_of(member, "definition"),
                    "argsstring": text_of(member, "argsstring"),
                    "protection": member.get("prot"),
                    "static": member.get("static") == "yes",
                    "file": loc.get("file") if loc is not None else None,
                    "line": int(loc.get("line")) if loc is not None and loc.get("line","").isdigit() else None,
                })
            compounds.append({"kind":kind,"name":name,"members":members})
    payload={"provenance":args.provenance,"compounds":compounds}
    args.json.parent.mkdir(parents=True,exist_ok=True)
    args.json.write_text(json.dumps(payload,indent=2),encoding="utf-8")
    print(f"Indexed {len(compounds)} compounds / {sum(len(x['members']) for x in compounds)} members")

if __name__=="__main__":
    main()
