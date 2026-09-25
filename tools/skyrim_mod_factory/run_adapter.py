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

def regex_matches(pattern:str,text:str)->bool:
    try:
        return re.search(pattern,text,re.MULTILINE|re.IGNORECASE) is not None
    except re.error:
        return pattern.lower() in text.lower()

def evaluate_process_result(
    adapter:dict[str,Any],
    *,
    returncode:int,
    stdout:str,
    stderr:str,
    outputs_after:list[dict[str,Any]],
)->dict[str,Any]:
    success=adapter.get("success") or {}
    allowed=success.get("exit_codes",[0])
    issues=[]
    issue_codes=[]
    analyzer_rule_ids=[]
    diagnostic_matches=[]
    fail=False

    if returncode not in allowed:
        fail=True
        issue_codes.append("TOOL_EXIT_CODE")
        issues.append(f"unexpected exit code {returncode}; allowed={allowed}")

    combined=stdout+"\n"+stderr
    for pattern in success.get("forbidden_log_patterns") or []:
        if regex_matches(str(pattern),combined):
            fail=True
            if "FORBIDDEN_LOG_PATTERN" not in issue_codes:
                issue_codes.append("FORBIDDEN_LOG_PATTERN")
            issues.append(f"forbidden log pattern matched: {pattern}")

    streams={"stdout":stdout,"stderr":stderr,"combined":combined}
    for diag in adapter.get("diagnostics") or []:
        stream=diag.get("stream","combined")
        text=streams.get(stream,combined)
        pattern=str(diag.get("pattern",""))
        if not pattern or not regex_matches(pattern,text):
            continue
        code=str(diag["issue_code"])
        severity=diag.get("severity","ERROR")
        rule_id=diag.get("analyzer_rule_id")
        if code not in issue_codes:
            issue_codes.append(code)
        if rule_id and rule_id not in analyzer_rule_ids:
            analyzer_rule_ids.append(rule_id)
        diagnostic_matches.append({
            "issue_code":code,
            "severity":severity,
            "pattern":pattern,
            "stream":stream,
            **({"analyzer_rule_id":rule_id} if rule_id else {}),
        })
        issues.append(f"{severity} diagnostic {code} matched {stream}: {pattern}")
        if severity in {"BLOCKER","ERROR"}:
            fail=True

    missing=[x.get("path") for x in outputs_after if not x.get("exists")]
    if missing:
        fail=True
        issue_codes.append("DECLARED_OUTPUT_MISSING")
        issues.append("declared outputs missing: "+", ".join(str(x) for x in missing))

    return {
        "status":"failed" if fail else "passed",
        "issues":issues,
        "issue_codes":list(dict.fromkeys(issue_codes)),
        "analyzer_rule_ids":list(dict.fromkeys(analyzer_rule_ids)),
        "diagnostic_matches":diagnostic_matches,
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
      "evidence":dict(adapter.get("evidence",{})),
      "issue_codes":[],
      "analyzer_rule_ids":[]
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
          "issues":["dry-run: command was not executed"],
          "issue_codes":[],
          "analyzer_rule_ids":[]
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
        outputs_after=[file_fact(x) for x in outputs]
        verdict=evaluate_process_result(
            adapter,
            returncode=proc.returncode,
            stdout=proc.stdout,
            stderr=proc.stderr,
            outputs_after=outputs_after,
        )
        record["evidence"]["diagnostic_matches"]=verdict["diagnostic_matches"]
        record.update({
          "status":verdict["status"],
          "finished_at":utcnow(),
          "exit_code":proc.returncode,
          "stdout_path":str(stdout_path),
          "stderr_path":str(stderr_path),
          "outputs_after":outputs_after,
          "issues":verdict["issues"],
          "issue_codes":verdict["issue_codes"],
          "analyzer_rule_ids":verdict["analyzer_rule_ids"]
        })
    except subprocess.TimeoutExpired as ex:
        stdout_path.write_text((ex.stdout or "") if isinstance(ex.stdout,str) else "",encoding="utf-8")
        stderr_path.write_text((ex.stderr or "") if isinstance(ex.stderr,str) else "",encoding="utf-8")
        record.update({
          "status":"failed","finished_at":utcnow(),"exit_code":None,
          "stdout_path":str(stdout_path),"stderr_path":str(stderr_path),
          "outputs_after":[file_fact(x) for x in outputs],
          "issues":[f"timeout after {effective_timeout} seconds"],
          "issue_codes":["TOOL_TIMEOUT"],
          "analyzer_rule_ids":[]
        })
    except OSError as ex:
        record.update({
          "status":"failed","finished_at":utcnow(),"exit_code":None,
          "stdout_path":str(stdout_path),"stderr_path":str(stderr_path),
          "outputs_after":[file_fact(x) for x in outputs],
          "issues":[f"process launch failed: {ex}"],
          "issue_codes":["TOOL_LAUNCH_FAILED"],
          "analyzer_rule_ids":[]
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
