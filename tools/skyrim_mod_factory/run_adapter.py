#!/usr/bin/env python3
"""Execute one Skyrim Mod Factory tool adapter and emit an evidence-rich step record.

Safety model:
- dry-run unless --execute is supplied;
- subprocess list execution only (shell=False);
- all {placeholders} must be supplied explicitly;
- captures stdout/stderr, timestamps, exit code and optional file hashes.

The reusable run_adapter() function is the canonical execution primitive for both
the CLI and higher-level DAG/orchestrator runners.
"""
from __future__ import annotations
import argparse, datetime as dt, hashlib, json, os, re, subprocess, sys
from pathlib import Path
from typing import Any, Iterable

PLACEHOLDER=re.compile(r"\{([A-Za-z_][A-Za-z0-9_]*)\}")

def utcnow()->str:
    return dt.datetime.now(dt.timezone.utc).isoformat()

def sha256(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()

def file_fact(path_text:str)->dict:
    p=Path(path_text)
    fact={"path":str(p)}
    if p.is_file():
        fact.update({"exists":True,"kind":"file","size":p.stat().st_size,"sha256":sha256(p)})
    elif p.is_dir():
        fact.update({"exists":True,"kind":"directory"})
    else:
        fact.update({"exists":False})
    return fact

def subst(value:str, variables:dict[str,str])->str:
    missing=sorted(set(PLACEHOLDER.findall(value))-variables.keys())
    if missing:
        raise ValueError("missing placeholders: "+", ".join(missing))
    return PLACEHOLDER.sub(lambda m:variables[m.group(1)],value)

def load_adapter(registry:Path, adapter_id:str)->dict:
    data=json.loads(registry.read_text(encoding="utf-8"))
    matches=[x for x in data.get("adapters",[]) if x.get("adapter_id")==adapter_id]
    if not matches:
        raise SystemExit(f"Adapter not found: {adapter_id}")
    if len(matches)>1:
        raise SystemExit(f"Duplicate adapter id: {adapter_id}")
    return matches[0]

def build_invocation(adapter:dict[str,Any], variables:dict[str,str])->dict[str,Any]:
    inv=adapter.get("invocation") or {}
    if inv.get("mode") not in {"cli","hybrid"}:
        raise ValueError(
            f"Adapter {adapter.get('adapter_id') or adapter.get('tool') or '?'} "
            f"is not directly CLI-executable (mode={inv.get('mode')})"
        )
    exe=subst(inv.get("executable",""),variables)
    if not exe:
        raise ValueError("adapter invocation has no executable")
    argv=[exe]+[subst(str(x),variables) for x in inv.get("arguments_template",[])]
    cwd=subst(inv["working_directory"],variables) if inv.get("working_directory") else None
    env=os.environ.copy()
    for k,v in (inv.get("environment") or {}).items():
        env[k]=subst(str(v),variables)
    return {
        "argv":argv,
        "cwd":cwd,
        "env":env,
        "timeout":inv.get("timeout_seconds"),
    }

def run_adapter(
    adapter:dict[str,Any],
    *,
    adapter_id:str|None=None,
    variables:dict[str,str]|None=None,
    inputs:Iterable[str]=(),
    outputs:Iterable[str]=(),
    log_dir:Path=Path("tests/reports/tool-runs"),
    execute:bool=False,
    timeout:int|None=None,
    record_id:str|None=None,
)->dict[str,Any]:
    """Run one already-resolved adapter and return a build-report-compatible record."""
    variables=dict(variables or {})
    adapter_id=adapter_id or adapter.get("adapter_id") or adapter.get("tool") or "adapter"
    invocation=build_invocation(adapter,variables)
    argv=invocation["argv"]
    cwd=invocation["cwd"]
    env=invocation["env"]
    effective_timeout=timeout or invocation["timeout"]
    inputs=list(inputs)
    outputs=list(outputs)

    started=utcnow()
    record={
      "id":record_id or f"{adapter_id}:{started}",
      "adapter_id":adapter_id,
      "tool":adapter.get("tool"),
      "tool_version":adapter.get("tool_version"),
      "status":"pending",
      "command":argv,
      "cwd":cwd,
      "started_at":started,
      "dry_run":not execute,
      "inputs":[file_fact(x) for x in inputs],
      "outputs_before":[file_fact(x) for x in outputs],
      "evidence":adapter.get("evidence",{})
    }

    log_dir.mkdir(parents=True,exist_ok=True)
    safe_id=re.sub(r"[^A-Za-z0-9_.-]+","_",adapter_id)
    stamp=dt.datetime.now().strftime("%Y%m%dT%H%M%S")
    stdout_path=log_dir/f"{stamp}-{safe_id}.stdout.log"
    stderr_path=log_dir/f"{stamp}-{safe_id}.stderr.log"

    if not execute:
        record.update({
          "status":"skipped",
          "finished_at":utcnow(),
          "exit_code":None,
          "stdout_path":str(stdout_path),
          "stderr_path":str(stderr_path),
          "outputs_after":[file_fact(x) for x in outputs],
          "issues":["dry-run: command was not executed"]
        })
        return record

    try:
        proc=subprocess.run(
            argv,cwd=cwd,env=env,capture_output=True,text=True,
            encoding="utf-8",errors="replace",timeout=effective_timeout,
            check=False,shell=False
        )
        stdout_path.write_text(proc.stdout,encoding="utf-8")
        stderr_path.write_text(proc.stderr,encoding="utf-8")
        allowed=(adapter.get("success") or {}).get("exit_codes",[0])
        status="passed" if proc.returncode in allowed else "failed"
        record.update({
          "status":status,
          "finished_at":utcnow(),
          "exit_code":proc.returncode,
          "stdout_path":str(stdout_path),
          "stderr_path":str(stderr_path),
          "outputs_after":[file_fact(x) for x in outputs],
          "issues":[]
        })
    except subprocess.TimeoutExpired as ex:
        stdout_path.write_text((ex.stdout or "") if isinstance(ex.stdout,str) else "",encoding="utf-8")
        stderr_path.write_text((ex.stderr or "") if isinstance(ex.stderr,str) else "",encoding="utf-8")
        record.update({
          "status":"failed","finished_at":utcnow(),"exit_code":None,
          "stdout_path":str(stdout_path),"stderr_path":str(stderr_path),
          "outputs_after":[file_fact(x) for x in outputs],
          "issues":[f"timeout after {effective_timeout} seconds"]
        })
    except OSError as ex:
        record.update({
          "status":"failed","finished_at":utcnow(),"exit_code":None,
          "stdout_path":str(stdout_path),"stderr_path":str(stderr_path),
          "outputs_after":[file_fact(x) for x in outputs],
          "issues":[f"process launch failed: {ex}"]
        })
    return record

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--registry",type=Path,required=True)
    ap.add_argument("--adapter",required=True)
    ap.add_argument("--var",action="append",default=[],metavar="KEY=VALUE")
    ap.add_argument("--input",action="append",default=[])
    ap.add_argument("--output",action="append",default=[])
    ap.add_argument("--log-dir",type=Path,default=Path("tests/reports/tool-runs"))
    ap.add_argument("--record",type=Path)
    ap.add_argument("--execute",action="store_true")
    ap.add_argument("--timeout",type=int)
    args=ap.parse_args()

    variables={}
    for item in args.var:
        if "=" not in item:
            raise SystemExit(f"--var expects KEY=VALUE: {item}")
        k,v=item.split("=",1)
        variables[k]=v

    adapter=load_adapter(args.registry,args.adapter)
    try:
        record=run_adapter(
            adapter,
            adapter_id=args.adapter,
            variables=variables,
            inputs=args.input,
            outputs=args.output,
            log_dir=args.log_dir,
            execute=args.execute,
            timeout=args.timeout,
        )
    except ValueError as ex:
        raise SystemExit(str(ex))

    output=json.dumps(record,indent=2)+"\n"
    if args.record:
        args.record.parent.mkdir(parents=True,exist_ok=True)
        args.record.write_text(output,encoding="utf-8")
    print(output,end="")
    sys.exit(1 if record["status"]=="failed" else 0)

if __name__=="__main__":
    main()
