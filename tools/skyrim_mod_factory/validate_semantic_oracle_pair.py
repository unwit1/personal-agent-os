#!/usr/bin/env python3
"""Compare two semantic-plugin oracle documents with a fail-closed verdict."""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[1]
SCHEMAS=REPO/"schemas"

def load_module(name:str,path:Path):
    spec=importlib.util.spec_from_file_location(name,path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load {path}")
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

CMP=load_module("compare_semantic_plugins",HERE/"compare_semantic_plugins.py")

def load(path:Path)->dict[str,Any]:
    return json.loads(path.read_text(encoding="utf-8"))

def schema_errors(value:dict[str,Any],name:str)->list[str]:
    schema=load(SCHEMAS/name)
    out=[]
    for err in Draft202012Validator(schema).iter_errors(value):
        loc=".".join(str(x) for x in err.absolute_path) or "<root>"
        out.append(f"{loc}: {err.message}")
    return out

def validate_pair(
    left:dict[str,Any],
    right:dict[str,Any],
    *,
    left_name:str="<left>",
    right_name:str="<right>",
    require_producers:set[str]|None=None,
)->dict[str,Any]:
    diff=CMP.compare(
        left,right,before_name=left_name,after_name=right_name
    )
    left_producer=(left.get("provenance") or {}).get("producer")
    right_producer=(right.get("provenance") or {}).get("producer")
    issues=[]
    compared=list((diff.get("coverage") or {}).get("compared_fields") or [])

    if require_producers:
        actual={x for x in (left_producer,right_producer) if x}
        missing=sorted(require_producers-actual)
        if missing:
            issues.append(
                "required semantic producers not present: "+", ".join(missing)
            )

    if not diff.get("comparable"):
        status="needs-review"
        issues.extend(diff.get("comparability_reasons") or [])
    elif not compared and (diff.get("coverage") or {}).get("mode")=="declared-intersection":
        status="needs-review"
        issues.append("semantic producers declare no shared comparable fields")
    elif diff.get("verdict")=="different":
        status="fail"
        issues.append("semantic oracles disagree on shared comparable semantics")
    else:
        status="pass"

    report={
        "schema_version":"skyrim-semantic-oracle-report-v1",
        "status":status,
        "left_producer":left_producer,
        "right_producer":right_producer,
        "compared_fields":compared,
        "diff":diff,
        "issues":issues,
    }
    errors=schema_errors(report,"skyrim-semantic-oracle-report-v1.schema.json")
    if errors:
        raise ValueError(
            "semantic oracle report failed schema validation: "
            +"; ".join(errors)
        )
    return report

def main()->None:
    ap=argparse.ArgumentParser()
    ap.add_argument("left",type=Path)
    ap.add_argument("right",type=Path)
    ap.add_argument("--output",type=Path)
    ap.add_argument("--require-mutagen-xdump",action="store_true")
    args=ap.parse_args()

    required=(
        {"mutagen-semantic-export","xedit-xdump-text-normalizer"}
        if args.require_mutagen_xdump else None
    )
    try:
        report=validate_pair(
            load(args.left),
            load(args.right),
            left_name=str(args.left),
            right_name=str(args.right),
            require_producers=required,
        )
    except ValueError as exc:
        raise SystemExit(str(exc))

    rendered=json.dumps(report,indent=2)+"\n"
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(rendered,encoding="utf-8")
    else:
        print(rendered,end="")

    if report["status"]=="fail":
        raise SystemExit(2)
    if report["status"]=="needs-review":
        raise SystemExit(3)

if __name__=="__main__":
    main()
