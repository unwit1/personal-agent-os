#!/usr/bin/env python3
"""Parse xEdit/SSEEdit "Check for Errors" log sessions into typed evidence.

The parser is deliberately fail-closed:
- only the most recent Check for Errors session is considered;
- the xEdit completion summary is authoritative for processed/error counts;
- a missing start/completion boundary can never produce PASS;
- explicit error findings fail even if the summary is missing or contradictory;
- warnings, parser coverage gaps, or count mismatches require review.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[1]
SCHEMAS=REPO/"schemas"
SCHEMA_NAME="skyrim-xedit-error-report-v1.schema.json"
PARSER_VERSION="1.0"

TIMESTAMP_RE=re.compile(r"^\s*\[[0-9:]+\]\s*")
START_RE=re.compile(r"\bStart:\s*Checking for Errors\b",re.I)
TARGET_RE=re.compile(r"\bChecking for Errors in\s+(?:\[[^\]]+\]\s*)?(?P<target>.+?)\s*$",re.I)
DONE_RE=re.compile(
    r"\bDone:\s*Checking for Errors\s*,?\s*"
    r"Processed Records:\s*(?P<processed>\d+)\s*,?\s*"
    r"Errors found:\s*(?P<errors>\d+)\s*,?\s*"
    r"Elapsed Time:\s*(?P<elapsed>[^,\r\n]+)",
    re.I,
)
RECORD_RE=re.compile(
    r"(?P<context>.*?)\[(?P<signature>[A-Z0-9_]{4}):(?P<form>[0-9A-Fa-f]{8})\]\s*$"
)
PLUGIN_RE=re.compile(r"(?P<plugin>[^\\/:*?\"<>|\r\n]+\.(?:esm|esp|esl))\b",re.I)
SUSPICIOUS_RE=re.compile(
    r"\b(error|warning|invalid|missing|unresolved|could not be resolved|"
    r"found a|null reference|not persistent|marked as deleted)\b",
    re.I,
)

def load_json(path:Path)->dict[str,Any]:
    return json.loads(path.read_text(encoding="utf-8"))

def schema_errors(value:dict[str,Any])->list[str]:
    schema=load_json(SCHEMAS/SCHEMA_NAME)
    out=[]
    for err in Draft202012Validator(schema).iter_errors(value):
        loc=".".join(str(x) for x in err.absolute_path) or "<root>"
        out.append(f"{loc}: {err.message}")
    return out

def strip_prefix(line:str)->str:
    return TIMESTAMP_RE.sub("",line,1).strip()

def classify_message(message:str)->tuple[str,str]:
    low=message.lower()
    if "could not be resolved" in low or "unresolved" in low:
        return "error","unresolved-reference"
    if "found a null reference" in low:
        return "error","null-reference"
    if "found a " in low and " reference" in low and "expected:" in low:
        return "error","reference-type-mismatch"
    if "objectid" in low and "invalid for a light module" in low:
        return "error","invalid-light-objectid"
    if "record marked as deleted but contains" in low:
        return "error","deleted-record-content"
    if "missing" in low:
        return "error","missing-data"
    if "<warning:" in low or low.startswith("warning:") or low.startswith("<warning:"):
        return "warning","xedit-warning"
    if "< error:" in low or "<error:" in low or low.startswith("error:"):
        return "error","xedit-error"
    return "error","unclassified"

def select_session(lines:list[str])->tuple[int,int,bool,bool]:
    starts=[i for i,line in enumerate(lines) if START_RE.search(strip_prefix(line))]
    dones=[i for i,line in enumerate(lines) if DONE_RE.search(strip_prefix(line))]
    if starts:
        start=starts[-1]
        following=[i for i in dones if i>=start]
        end=following[0] if following else len(lines)-1
        return start,end,True,bool(following)
    if dones:
        end=dones[-1]
        return 0,end,False,True
    return 0,max(0,len(lines)-1),False,False

def parse_text(text:str,source_log:str="<memory>")->dict[str,Any]:
    lines=text.splitlines()
    if not lines:
        lines=[]
    start,end,start_found,completion_detected=select_session(lines)
    session=lines[start:end+1] if lines else []

    target=None
    plugin=None
    processed=None
    declared_errors=None
    elapsed=None
    findings=[]
    suspicious_unparsed=0
    current_record=None
    current_signature=None
    current_form=None
    issues=[]

    for offset,raw in enumerate(session):
        line_number=start+offset+1
        body=strip_prefix(raw)
        if not body:
            continue
        if START_RE.search(body):
            continue
        match=TARGET_RE.search(body)
        if match:
            target=match.group("target").strip()
            pm=PLUGIN_RE.search(target)
            if pm:
                plugin=pm.group("plugin")
            continue
        done=DONE_RE.search(body)
        if done:
            processed=int(done.group("processed"))
            declared_errors=int(done.group("errors"))
            elapsed=done.group("elapsed").strip()
            continue

        record=RECORD_RE.search(body)
        if record and "->" not in body:
            current_record=body
            current_signature=record.group("signature")
            current_form=record.group("form").upper()
            continue

        if "->" in body:
            field_path,message=(part.strip() for part in body.split("->",1))
            severity,category=classify_message(message)
            findings.append({
                "line_number":line_number,
                "severity":severity,
                "category":category,
                "message":message,
                "raw":raw,
                "record_context":current_record,
                "field_path":field_path or None,
                "plugin":plugin,
                "form_id":current_form,
                "signature":current_signature,
            })
            continue

        if SUSPICIOUS_RE.search(body):
            severity,category=classify_message(body)
            if category!="unclassified":
                findings.append({
                    "line_number":line_number,
                    "severity":severity,
                    "category":category,
                    "message":body,
                    "raw":raw,
                    "record_context":current_record,
                    "field_path":None,
                    "plugin":plugin,
                    "form_id":current_form,
                    "signature":current_signature,
                })
            else:
                suspicious_unparsed+=1

    parsed_errors=sum(x["severity"]=="error" for x in findings)
    parsed_warnings=sum(x["severity"]=="warning" for x in findings)

    if not start_found:
        issues.append("Check for Errors start marker was not found")
    if not completion_detected:
        issues.append("Check for Errors completion summary was not found")
    if completion_detected and declared_errors is not None and declared_errors!=parsed_errors:
        issues.append(
            f"xEdit declared {declared_errors} errors but parser extracted {parsed_errors}; "
            "retain raw log and review parser coverage"
        )
    if suspicious_unparsed:
        issues.append(
            f"{suspicious_unparsed} suspicious session lines were not classified"
        )

    if parsed_errors>0 or (declared_errors is not None and declared_errors>0):
        status="fail"
    elif (
        not start_found
        or not completion_detected
        or declared_errors is None
        or parsed_warnings>0
        or suspicious_unparsed>0
    ):
        status="needs-review"
    else:
        status="pass"

    report={
        "schema_version":"skyrim-xedit-error-report-v1",
        "source_log":source_log,
        "parser_version":PARSER_VERSION,
        "tool":None,
        "tool_version":None,
        "game_mode":None,
        "target":target,
        "status":status,
        "completion_detected":completion_detected,
        "processed_records":processed,
        "declared_errors":declared_errors,
        "elapsed_time":elapsed,
        "findings":findings,
        "coverage":{
            "total_lines":len(lines),
            "session_lines":len(session),
            "finding_lines":len(findings),
            "suspicious_unparsed_lines":suspicious_unparsed,
        },
        "issues":issues,
    }
    errors=schema_errors(report)
    if errors:
        raise ValueError("xEdit error report failed schema validation: "+"; ".join(errors))
    return report

def main()->None:
    ap=argparse.ArgumentParser()
    ap.add_argument("log",type=Path)
    ap.add_argument("--output",type=Path)
    args=ap.parse_args()

    report=parse_text(
        args.log.read_text(encoding="utf-8",errors="replace"),
        source_log=str(args.log),
    )
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
