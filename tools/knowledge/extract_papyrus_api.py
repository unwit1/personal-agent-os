#!/usr/bin/env python3
"""Extract a reviewable Papyrus API catalog from PSC source trees.

This intentionally produces candidate facts. It does not claim that parsing source
alone proves runtime availability: native functions still require their supplying
DLL/runtime, and multiple source trees may declare the same class differently.
"""
from __future__ import annotations
import argparse, json, re
from pathlib import Path

SCRIPT_RE = re.compile(r"^\s*ScriptName\s+(\S+)(?:\s+extends\s+(\S+))?", re.I)
DECL_RE = re.compile(
    r"^\s*(?:(?P<ret>[A-Za-z_][\w\[\]]*)\s+)?"
    r"(?P<kind>Function|Event)\s+(?P<name>[A-Za-z_]\w*)\s*"
    r"\((?P<args>[^)]*)\)\s*(?P<mods>.*)$", re.I
)

def scan_file(path: Path, root: Path) -> dict:
    lines = path.read_text(encoding="utf-8-sig", errors="replace").splitlines()
    script = path.stem
    parent = None
    declarations = []
    for number, raw in enumerate(lines, 1):
        line = raw.split(";", 1)[0].strip()
        if not line:
            continue
        sm = SCRIPT_RE.match(line)
        if sm:
            script, parent = sm.group(1), sm.group(2)
            continue
        m = DECL_RE.match(line)
        if not m:
            continue
        mods = m.group("mods").strip()
        declarations.append({
            "kind": m.group("kind").lower(),
            "name": m.group("name"),
            "return_type": m.group("ret") if m.group("kind").lower() == "function" else None,
            "arguments": m.group("args").strip(),
            "modifiers": mods,
            "native": bool(re.search(r"\bNative\b", mods, re.I)),
            "global": bool(re.search(r"\bGlobal\b", mods, re.I)),
            "line": number,
        })
    return {
        "script": script,
        "extends": parent,
        "source": str(path.relative_to(root)),
        "declarations": declarations,
    }

def markdown(data: list[dict], provenance: str) -> str:
    out = [
        "# Generated Papyrus API Candidate Index", "",
        f"Provenance: {provenance}", "",
        "> Generated candidate data. Validate framework/runtime availability before promotion.",
        ""
    ]
    for s in sorted(data, key=lambda x: x["script"].lower()):
        ext = f" extends {s['extends']}" if s["extends"] else ""
        out += [f"## {s['script']}{ext}", "", f"Source: `{s['source']}`", ""]
        for d in s["declarations"]:
            ret = (d["return_type"] + " ") if d["return_type"] else ""
            mods = (" " + d["modifiers"]) if d["modifiers"] else ""
            out.append(f"- `{ret}{d['kind'].title()} {d['name']}({d['arguments']}){mods}` — line {d['line']}")
        out.append("")
    return "\n".join(out)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("psc_root", type=Path)
    ap.add_argument("--json", type=Path, required=True)
    ap.add_argument("--markdown", type=Path, required=True)
    ap.add_argument("--provenance", required=True,
                    help="Example: SKSE64 tag v2.x / commit abc123, retrieved YYYY-MM-DD")
    args = ap.parse_args()
    root = args.psc_root.resolve()
    data = [scan_file(p, root) for p in sorted(root.rglob("*.psc"))]
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.markdown.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps({
        "provenance": args.provenance,
        "scripts": data
    }, indent=2), encoding="utf-8")
    args.markdown.write_text(markdown(data, args.provenance), encoding="utf-8")
    print(f"Indexed {len(data)} PSC files")

if __name__ == "__main__":
    main()
