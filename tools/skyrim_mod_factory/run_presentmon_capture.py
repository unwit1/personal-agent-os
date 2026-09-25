#!/usr/bin/env python3
"""Run and summarize a process-scoped PresentMon capture.

CLI grammar is pinned to GameTechDev/PresentMon's current console application:
--process_id, --output_file, --no_console_stats, --v2_metrics,
--terminate_on_proc_exit, and optional --timed/--terminate_after_timed.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
import subprocess
from pathlib import Path
from typing import Any

METRIC_CANDIDATES=(
    "FrameTime",
    "CPUBusy",
    "CPUWait",
    "GPULatency",
    "GPUTime",
    "GPUBusy",
    "GPUWait",
    "msBetweenPresents",
    "msInPresentAPI",
    "msGPUActive",
)
FRAME_TIME_CANDIDATES=("FrameTime","msBetweenPresents")

def build_command(
    executable:Path,
    *,
    process_id:int,
    output_csv:Path,
    timed_seconds:float|None=None,
)->list[str]:
    if process_id<=0:
        raise ValueError("process_id must be positive")
    cmd=[
        str(executable),
        "--process_id",str(process_id),
        "--output_file",str(output_csv),
        "--no_console_stats",
        "--v2_metrics",
        "--terminate_on_proc_exit",
    ]
    if timed_seconds is not None:
        if timed_seconds<=0:
            raise ValueError("timed_seconds must be positive")
        cmd.extend([
            "--timed",str(timed_seconds),
            "--terminate_after_timed",
        ])
    return cmd

def percentile(values:list[float],p:float)->float:
    if not values:
        raise ValueError("percentile requires values")
    ordered=sorted(values)
    rank=max(1,math.ceil(p*len(ordered)))
    return ordered[rank-1]

def metric_summary(values:list[float])->dict[str,Any]:
    return {
        "count":len(values),
        "mean":statistics.fmean(values),
        "p50":percentile(values,0.50),
        "p95":percentile(values,0.95),
        "p99":percentile(values,0.99),
        "max":max(values),
    }

def finite_number(raw:str|None)->float|None:
    if raw is None or raw.strip() in {"","NA","N/A"}:
        return None
    try:
        value=float(raw)
    except ValueError:
        return None
    return value if math.isfinite(value) else None

def summarize_csv(path:Path,process_id:int)->dict[str,Any]:
    issues=[]
    if not path.is_file():
        return {
            "schema_version":"skyrim-frame-trace-summary-v1",
            "provider":"presentmon",
            "source_csv":str(path),
            "process_id":process_id,
            "status":"fail",
            "frame_count":0,
            "columns":[],
            "metrics":{},
            "issues":["PresentMon CSV does not exist"],
        }

    with path.open("r",encoding="utf-8-sig",newline="") as fh:
        reader=csv.DictReader(fh)
        columns=list(reader.fieldnames or [])
        rows=list(reader)

    if "ProcessID" not in columns:
        return {
            "schema_version":"skyrim-frame-trace-summary-v1",
            "provider":"presentmon",
            "source_csv":str(path),
            "process_id":process_id,
            "status":"fail",
            "frame_count":0,
            "columns":columns,
            "metrics":{},
            "issues":["PresentMon CSV is missing ProcessID"],
        }

    selected=[]
    for row in rows:
        try:
            pid=int(str(row.get("ProcessID","")).strip())
        except ValueError:
            continue
        if pid==process_id:
            selected.append(row)

    metrics={}
    for name in METRIC_CANDIDATES:
        if name not in columns:
            continue
        values=[
            value
            for row in selected
            if (value:=finite_number(row.get(name))) is not None
        ]
        if values:
            metrics[name]=metric_summary(values)
        else:
            issues.append(f"metric column {name} had no finite values for target process")

    frame_metric=next((x for x in FRAME_TIME_CANDIDATES if x in metrics),None)
    if not selected:
        status="fail"
        issues.append("PresentMon captured no frames for target process")
    elif frame_metric is None:
        status="needs-review"
        issues.append("PresentMon trace has no usable frame-time metric")
    else:
        status="pass"

    return {
        "schema_version":"skyrim-frame-trace-summary-v1",
        "provider":"presentmon",
        "source_csv":str(path),
        "process_id":process_id,
        "status":status,
        "frame_count":len(selected),
        "columns":columns,
        "metrics":metrics,
        "issues":issues,
    }

def main()->None:
    ap=argparse.ArgumentParser()
    ap.add_argument("--presentmon",type=Path,required=True)
    ap.add_argument("--process-id",type=int,required=True)
    ap.add_argument("--output-csv",type=Path,required=True)
    ap.add_argument("--summary",type=Path,required=True)
    ap.add_argument("--timed-seconds",type=float)
    ap.add_argument("--execute",action="store_true")
    args=ap.parse_args()

    cmd=build_command(
        args.presentmon,
        process_id=args.process_id,
        output_csv=args.output_csv,
        timed_seconds=args.timed_seconds,
    )
    if not args.execute:
        print(json.dumps({"command":cmd},indent=2))
        return

    args.output_csv.parent.mkdir(parents=True,exist_ok=True)
    args.summary.parent.mkdir(parents=True,exist_ok=True)
    args.output_csv.unlink(missing_ok=True)
    proc=subprocess.run(cmd,text=True,capture_output=True,check=False)
    result=summarize_csv(args.output_csv,args.process_id)
    if proc.returncode!=0:
        result["status"]="fail"
        result["issues"].append(f"PresentMon exited with code {proc.returncode}")
        if proc.stderr.strip():
            result["issues"].append("PresentMon stderr: "+proc.stderr.strip()[:1000])
    args.summary.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(args.summary)
    raise SystemExit(0 if result["status"]=="pass" else 2 if result["status"]=="fail" else 3)

if __name__=="__main__":
    main()
