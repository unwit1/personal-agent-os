#!/usr/bin/env python3
"""Windows-first MO2 runtime session manager for Skyrim Mod Factory.

This layer owns reproducible session boundaries, not in-game semantics yet:
- validate worker/test contracts;
- copy a template MO2 profile into a disposable profile;
- copy save fixtures into the disposable profile;
- refuse unsafe mutation roots;
- reject known conflicting processes before launch;
- launch a configured executable through MO2's documented CLI;
- capture stdout/stderr and filesystem evidence deltas;
- delete or retain the disposable profile according to policy;
- never claim G19/G20/G21/G26 PASS without typed observer evidence.

Game-driving transports (DevBench/SkyLink/etc.) plug in above this boundary.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import fnmatch
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable

from jsonschema import Draft202012Validator

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[1]
SCHEMAS=REPO/"schemas"
CONFIG_SCHEMA="skyrim-runtime-worker-config-v1.schema.json"
TEST_SCHEMA="skyrim-runtime-test-v1.schema.json"
RESULT_SCHEMA="skyrim-runtime-session-result-v1.schema.json"

def now()->str:
    return dt.datetime.now(dt.timezone.utc).isoformat()

def load(path:Path)->dict[str,Any]:
    return json.loads(path.read_text(encoding="utf-8"))

def schema_errors(value:dict[str,Any],name:str)->list[str]:
    schema=load(SCHEMAS/name)
    out=[]
    for err in Draft202012Validator(schema).iter_errors(value):
        loc=".".join(str(x) for x in err.absolute_path) or "<root>"
        out.append(f"{loc}: {err.message}")
    return out

def validate(value:dict[str,Any],name:str,label:str)->None:
    errors=schema_errors(value,name)
    if errors:
        raise ValueError(f"{label} failed schema validation: "+"; ".join(errors))

def sanitize(value:str)->str:
    clean=re.sub(r"[^A-Za-z0-9._-]+","-",value).strip("-._")
    return clean or "runtime"

def is_within(path:Path,roots:Iterable[Path])->bool:
    resolved=path.resolve()
    for root in roots:
        try:
            resolved.relative_to(root.resolve())
            return True
        except ValueError:
            pass
    return False

def sha256_json(value:Any)->str:
    payload=json.dumps(
        value,
        sort_keys=True,
        separators=(",",":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()

def sha256_file(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk=f.read(1024*1024)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()

def file_fact(path:Path,root:Path|None=None)->dict[str,Any]:
    rel=str(path.relative_to(root)) if root is not None else str(path)
    stat=path.stat()
    return {
        "path":rel.replace("\\","/"),
        "size":stat.st_size,
        "mtime_ns":stat.st_mtime_ns,
        "sha256":sha256_file(path),
    }

def tree_manifest(root:Path)->list[dict[str,Any]]:
    if not root.exists():
        return []
    return [
        file_fact(path,root)
        for path in sorted(p for p in root.rglob("*") if p.is_file())
    ]

def should_ignore(relative:Path,patterns:list[str])->bool:
    text=str(relative).replace("\\","/")
    return any(fnmatch.fnmatch(text,pattern) for pattern in patterns)

def copy_profile(template:Path,destination:Path,ignore_patterns:list[str])->None:
    if not template.is_dir():
        raise ValueError(f"template profile directory does not exist: {template}")
    if destination.exists():
        raise ValueError(f"disposable profile already exists: {destination}")
    destination.parent.mkdir(parents=True,exist_ok=True)
    shutil.copytree(
        template,
        destination,
        ignore=lambda directory,names:[
            name
            for name in names
            if should_ignore(
                (Path(directory)/name).relative_to(template),
                ignore_patterns,
            )
        ],
    )

def verify_required_files(profile:Path,required:list[str])->None:
    missing=[rel for rel in required if not (profile/rel).is_file()]
    if missing:
        raise ValueError(
            "disposable profile is missing required files: "+", ".join(missing)
        )

def build_mo2_command(config:dict[str,Any],profile_name:str)->list[str]:
    mo2=config["mo2"]
    command=[mo2["executable"]]
    if mo2.get("instance"):
        command.extend(["--instance",str(mo2["instance"])])
    command.extend(["--profile",profile_name,"run","--executable",mo2["configured_executable"]])
    if mo2.get("arguments"):
        command.extend(["--arguments",str(mo2["arguments"])])
    if mo2.get("cwd"):
        command.extend(["--cwd",str(mo2["cwd"])])
    return command

def windows_process_names()->set[str]:
    if os.name!="nt":
        raise ValueError("runtime execution requires Windows")
    proc=subprocess.run(
        ["tasklist","/FO","CSV","/NH"],
        text=True,
        capture_output=True,
        check=False,
    )
    if proc.returncode!=0:
        raise ValueError(
            f"tasklist failed with exit code {proc.returncode}: {proc.stderr[-1000:]!r}"
        )
    names=set()
    for row in csv.reader(io.StringIO(proc.stdout)):
        if row:
            names.add(row[0].lower())
    return names

def assert_process_exclusivity(config:dict[str,Any])->None:
    policy=config["process_policy"]
    names=windows_process_names()
    conflicts=[
        name for name in policy["exclusive_process_names"]
        if name.lower() in names
    ]
    if conflicts:
        raise ValueError(
            "runtime launch refused because conflicting process(es) are running: "
            +", ".join(conflicts)
        )

def copy_fixture(
    test:dict[str,Any],
    config:dict[str,Any],
    disposable:Path,
)->dict[str,Any]|None:
    fixture=test.get("fixture") or {}
    if fixture.get("kind")!="save":
        return {
            "kind":fixture.get("kind"),
            "source":None,
            "destination":None,
            "sha256":None,
        }
    raw=fixture.get("save_path")
    if not raw:
        raise ValueError("save fixture requires fixture.save_path")
    source=Path(raw)
    if not source.is_file():
        raise ValueError(f"save fixture does not exist: {source}")
    target_rel=(config.get("fixture_policy") or {}).get(
        "save_target_relative","saves"
    )
    destination=disposable/target_rel/source.name
    destination.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(source,destination)
    if sha256_file(source)!=sha256_file(destination):
        raise ValueError("save fixture copy hash mismatch")
    return {
        "kind":"save",
        "source":str(source),
        "destination":str(destination),
        "sha256":sha256_file(destination),
    }

def path_matches_source(path_text:str,source_text:str)->bool:
    path=Path(path_text)
    source=Path(source_text)
    path_norm=str(path.resolve()).replace("\\","/").lower()
    source_raw=str(source).replace("\\","/")
    if any(ch in source_raw for ch in "*?[]"):
        if Path(source_raw).is_absolute():
            pattern=str(Path(source_raw)).replace("\\","/").lower()
        else:
            pattern=str(Path(source_raw).resolve()).replace("\\","/").lower()
        return fnmatch.fnmatchcase(path_norm,pattern)
    if source.is_dir():
        return is_within(path,[source])
    try:
        return path.resolve()==source.resolve()
    except OSError:
        return False

def source_root_exists(source_text:str)->bool:
    raw=str(source_text)
    if not any(ch in raw for ch in "*?[]"):
        path=Path(raw)
        return path.exists() if path.is_dir() else path.parent.exists()
    wildcard_positions=[raw.find(ch) for ch in "*?[" if ch in raw]
    cut=min(x for x in wildcard_positions if x>=0)
    prefix=raw[:cut]
    root=Path(prefix).parent
    return root.exists()

def validate_g19_source_coverage(config:dict[str,Any])->list[str]:
    cfg=config.get("evidence") or {}
    issues=[]
    for raw in cfg.get("log_paths") or []:
        if not expand_paths([raw]):
            issues.append(f"configured runtime log source has no readable file match: {raw}")
    for raw in cfg.get("crash_paths") or []:
        if not source_root_exists(raw):
            issues.append(f"configured crash evidence root is unavailable: {raw}")
    return issues

def expand_paths(patterns:list[str])->list[Path]:
    found=[]
    for raw in patterns:
        path=Path(raw)
        if any(ch in raw for ch in "*?[]"):
            base=Path(path.anchor or ".")
            pattern=str(path)[len(path.anchor):].lstrip("\\/")
            for candidate in base.glob(pattern):
                if candidate.is_file():
                    found.append(candidate)
        elif path.is_file():
            found.append(path)
        elif path.is_dir():
            found.extend(p for p in path.rglob("*") if p.is_file())
    unique={str(p.resolve()).lower():p for p in found}
    return sorted(unique.values(),key=lambda p:str(p).lower())

def evidence_snapshot(config:dict[str,Any])->dict[str,dict[str,Any]]:
    evidence=config.get("evidence") or {}
    paths=expand_paths(
        list(evidence.get("log_paths") or [])
        +list(evidence.get("crash_paths") or [])
        +list(evidence.get("frame_trace_paths") or [])
    )
    return {str(p.resolve()):file_fact(p) for p in paths}

def evidence_delta(
    before:dict[str,dict[str,Any]],
    after:dict[str,dict[str,Any]],
)->list[dict[str,Any]]:
    rows=[]
    for path in sorted(set(before)|set(after)):
        a=before.get(path)
        b=after.get(path)
        if a==b:
            continue
        rows.append({
            "path":path,
            "change":"added" if a is None else "removed" if b is None else "changed",
            "before":a,
            "after":b,
        })
    return rows

def copy_changed_evidence(delta:list[dict[str,Any]],session_dir:Path)->list[dict[str,Any]]:
    out=[]
    evidence_dir=session_dir/"artifacts"
    for index,row in enumerate(delta,1):
        raw=row["path"]
        source=Path(raw)
        item=dict(row)
        if source.is_file():
            target=evidence_dir/f"{index:04d}-{sanitize(source.name)}"
            target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(source,target)
            item["captured_path"]=str(target)
            item["captured_sha256"]=sha256_file(target)
        out.append(item)
    return out

def evaluate_g19(
    config:dict[str,Any],
    log_delta:list[dict[str,Any]],
    crash_delta:list[dict[str,Any]],
)->dict[str,Any]:
    cfg=config.get("evidence") or {}
    evidence=[]
    issues=[]
    crash_changes=[
        row for row in crash_delta
        if row.get("change") in {"added","changed"}
    ]
    if crash_changes:
        return {
            "gate":"G19",
            "status":"fail",
            "evidence":[
                f'new/changed crash artifact: {row["path"]}'
                for row in crash_changes
            ],
            "issues":["runtime session produced new or changed crash evidence"],
        }

    removed=[
        row for row in (list(log_delta)+list(crash_delta))
        if row.get("change")=="removed"
    ]
    if removed:
        return {
            "gate":"G19",
            "status":"needs-review",
            "evidence":[f'removed evidence source: {row["path"]}' for row in removed],
            "issues":["configured runtime evidence disappeared during the session"],
        }

    raw_patterns=list(cfg.get("forbidden_log_patterns") or [])
    compiled=[]
    for pattern in raw_patterns:
        try:
            compiled.append((pattern,re.compile(pattern,re.I)))
        except re.error as exc:
            issues.append(f"invalid forbidden_log_pattern {pattern!r}: {exc}")
    if issues:
        return {
            "gate":"G19",
            "status":"needs-review",
            "evidence":[],
            "issues":issues,
        }

    hits=[]
    for row in log_delta:
        captured=row.get("captured_path")
        if not captured or not Path(captured).is_file():
            continue
        try:
            text=Path(captured).read_text(encoding="utf-8",errors="replace")
        except OSError as exc:
            issues.append(f"could not read captured log {captured}: {exc}")
            continue
        for pattern,rx in compiled:
            if rx.search(text):
                hits.append((row["path"],pattern))
    if hits:
        return {
            "gate":"G19",
            "status":"fail",
            "evidence":[
                f"forbidden runtime log pattern {pattern!r} matched {path}"
                for path,pattern in hits
            ],
            "issues":["runtime log cleanliness check found forbidden signatures"],
        }
    if issues:
        return {
            "gate":"G19",
            "status":"needs-review",
            "evidence":[],
            "issues":issues,
        }

    configured_sources=bool(
        cfg.get("log_paths") or cfg.get("crash_paths")
    )
    coverage_issues=validate_g19_source_coverage(config)
    if coverage_issues:
        return {
            "gate":"G19",
            "status":"needs-review",
            "evidence":[],
            "issues":coverage_issues,
        }
    if not configured_sources:
        return {
            "gate":"G19",
            "status":"needs-review",
            "evidence":[],
            "issues":["no runtime log/crash sources are configured"],
        }
    if cfg.get("log_paths") and not raw_patterns:
        return {
            "gate":"G19",
            "status":"needs-review",
            "evidence":[],
            "issues":[
                "runtime log sources are configured but no forbidden log patterns "
                "define what should fail"
            ],
        }
    if not cfg.get("complete_for_g19",False):
        return {
            "gate":"G19",
            "status":"needs-review",
            "evidence":[
                "configured sources had no new crash artifact or forbidden log match"
            ],
            "issues":[
                "runtime evidence configuration is not declared complete_for_g19"
            ],
        }
    evidence.append("no configured crash artifact was added or changed")
    if cfg.get("log_paths"):
        evidence.append("no forbidden pattern matched configured runtime log deltas")
    return {
        "gate":"G19",
        "status":"pass",
        "evidence":evidence,
        "issues":[],
    }

def default_gate_rows(test:dict[str,Any])->list[dict[str,Any]]:
    performance_required=bool(
        (test.get("evidence") or {}).get("performance")
        or any(x.get("kind")=="performance" for x in test.get("assertions") or [])
    )
    save_required=(test.get("fixture") or {}).get("kind")=="save"
    return [
        {
            "gate":"G19",
            "status":"needs-review",
            "evidence":[],
            "issues":["crash/log cleanliness has not been proven for this session"],
        },
        {
            "gate":"G20",
            "status":"needs-review" if performance_required else "not-applicable",
            "evidence":[] if performance_required else [
                "runtime test declares no performance assertion or performance evidence"
            ],
            "issues":["performance evidence has not been supplied"] if performance_required else [],
        },
        {
            "gate":"G21",
            "status":"needs-review" if save_required else "not-applicable",
            "evidence":[] if save_required else [
                "runtime fixture is not save-based"
            ],
            "issues":["save/migration evidence has not been supplied"] if save_required else [],
        },
        {
            "gate":"G26",
            "status":"needs-review",
            "evidence":[],
            "issues":["runtime assertions have not been observed by a typed adapter"],
        },
    ]

def prepare_session(
    test:dict[str,Any],
    config:dict[str,Any],
    *,
    run_id:str,
    build_id:str|None=None,
)->tuple[dict[str,Any],Path]:
    validate(test,TEST_SCHEMA,"runtime test")
    validate(config,CONFIG_SCHEMA,"runtime worker config")
    allowed=[Path(x) for x in config["workspace"].get("allowed_mutation_roots") or []]
    disposable_root=Path(config["profiles"]["disposable_root"])
    run_root=Path(config["workspace"]["run_root"])
    evidence_root=Path(config["workspace"]["evidence_root"])
    for path,label in (
        (disposable_root,"disposable profile root"),
        (run_root,"runtime run root"),
        (evidence_root,"runtime evidence root"),
    ):
        if not is_within(path,allowed):
            raise ValueError(f"{label} is outside allowed mutation roots: {path}")

    profile_name=(
        config["profiles"]["profile_name_prefix"]
        +"-"+sanitize(test["test_id"])
        +"-"+sanitize(run_id)
    )
    disposable=disposable_root/profile_name
    if not is_within(disposable,allowed):
        raise ValueError(f"disposable profile is outside allowed mutation roots: {disposable}")

    template=Path(config["profiles"]["template_dir"])
    template_before=tree_manifest(template)
    copy_profile(
        template,
        disposable,
        list(config["profiles"].get("copy_ignores") or []),
    )
    verify_required_files(
        disposable,
        list(config["profiles"].get("required_files") or []),
    )
    fixture=copy_fixture(test,config,disposable)
    before_manifest=tree_manifest(disposable)

    session_dir=evidence_root/sanitize(run_id)
    if not is_within(session_dir,allowed):
        raise ValueError(f"session evidence directory is outside allowed roots: {session_dir}")
    session_dir.mkdir(parents=True,exist_ok=False)

    prepared_at=now()
    session_token=sha256_json({
        "run_id":run_id,
        "test_id":test["test_id"],
        "project_id":test["project_id"],
        "worker_id":config["worker_id"],
        "profile_name":profile_name,
        "profile_manifest":before_manifest,
        "prepared_at":prepared_at,
    })
    result={
        "schema_version":"skyrim-runtime-session-result-v1",
        "run_id":run_id,
        "test_id":test["test_id"],
        "project_id":test["project_id"],
        "worker_id":config["worker_id"],
        "build_id":build_id,
        "session_token":session_token,
        "status":"prepared",
        "prepared_at":prepared_at,
        "started_at":None,
        "finished_at":None,
        "profile":{
            "template_dir":str(template),
            "disposable_dir":str(disposable),
            "profile_name":profile_name,
            "before_manifest":before_manifest,
            "after_manifest":[],
            "restored":False,
            "fresh_copy":True,
            "retained":True,
        },
        "fixture":fixture,
        "launch":{
            "command":build_mo2_command(config,profile_name),
            "attempted":False,
            "exit_code":None,
            "timed_out":False,
            "stdout_path":None,
            "stderr_path":None,
        },
        "steps":[
            {
                "id":step["id"],
                "status":"needs-review",
                "issues":["step transport has not supplied typed execution evidence"],
            }
            for step in test["steps"]
        ],
        "assertions":[
            {
                "id":assertion["id"],
                "status":"needs-review",
                "severity":assertion.get("severity","ERROR"),
                "expected":assertion.get("expected"),
                "observed":None,
                "issues":["runtime assertion has not been observed by a typed adapter"],
            }
            for assertion in test["assertions"]
        ],
        "evidence":{
            "session_dir":str(session_dir),
            "artifacts":[],
            "log_delta":[],
            "crash_delta":[],
            "screenshots":[],
            "frame_traces":[],
        },
        "cleanup":{"attempted":False,"status":"skipped","issues":[]},
        "gates":default_gate_rows(test),
        "issues":[],
    }
    result["_template_before"]=template_before
    return result,session_dir

def finalize_cleanup(
    result:dict[str,Any],
    config:dict[str,Any],
    *,
    success:bool,
)->None:
    disposable=Path(result["profile"]["disposable_dir"])
    template=Path(result["profile"]["template_dir"])
    result["profile"]["after_manifest"]=tree_manifest(disposable)
    result["cleanup"]["attempted"]=True
    policy=config.get("fixture_policy") or {}
    should_delete=(
        success and policy.get("delete_disposable_profile_on_success",True)
    ) or (
        not success and not policy.get("retain_on_failure",True)
    )
    try:
        if should_delete and disposable.exists():
            shutil.rmtree(disposable)
            result["profile"]["retained"]=False
        else:
            result["profile"]["retained"]=disposable.exists()
        template_before=result.pop("_template_before",[])
        template_after=tree_manifest(template)
        if template_before!=template_after:
            result["cleanup"]["status"]="failed"
            result["cleanup"]["issues"].append(
                "template MO2 profile changed during runtime session"
            )
            result["profile"]["restored"]=False
            return
        result["profile"]["restored"]=not disposable.exists() if should_delete else True
        result["cleanup"]["status"]="passed"
    except OSError as exc:
        result["cleanup"]["status"]="failed"
        result["cleanup"]["issues"].append(str(exc))
        result["profile"]["restored"]=False
    result.pop("_template_before",None)

def run_session(
    test:dict[str,Any],
    config:dict[str,Any],
    *,
    run_id:str,
    build_id:str|None=None,
    execute:bool=False,
)->dict[str,Any]:
    result,session_dir=prepare_session(
        test,config,run_id=run_id,build_id=build_id
    )
    if not execute:
        result.pop("_template_before",None)
        validate(result,RESULT_SCHEMA,"runtime session result")
        return result

    if os.name!="nt":
        result["status"]="aborted"
        result["issues"].append("runtime execution requires Windows")
        finalize_cleanup(result,config,success=False)
        validate(result,RESULT_SCHEMA,"runtime session result")
        return result

    try:
        assert_process_exclusivity(config)
    except ValueError as exc:
        result["status"]="aborted"
        result["issues"].append(str(exc))
        finalize_cleanup(result,config,success=False)
        validate(result,RESULT_SCHEMA,"runtime session result")
        return result

    before=evidence_snapshot(config)
    result["started_at"]=now()
    stdout_path=session_dir/"mo2.stdout.log"
    stderr_path=session_dir/"mo2.stderr.log"
    result["launch"]["attempted"]=True
    result["launch"]["stdout_path"]=str(stdout_path)
    result["launch"]["stderr_path"]=str(stderr_path)
    timed_out=False
    exit_code=None
    try:
        proc=subprocess.run(
            result["launch"]["command"],
            text=True,
            capture_output=True,
            timeout=config["timeouts"]["scenario_seconds"],
            check=False,
        )
        exit_code=proc.returncode
        stdout_path.write_text(proc.stdout or "",encoding="utf-8",errors="replace")
        stderr_path.write_text(proc.stderr or "",encoding="utf-8",errors="replace")
    except subprocess.TimeoutExpired as exc:
        timed_out=True
        stdout_path.write_text(exc.stdout or "",encoding="utf-8",errors="replace")
        stderr_path.write_text(exc.stderr or "",encoding="utf-8",errors="replace")

    result["launch"]["exit_code"]=exit_code
    result["launch"]["timed_out"]=timed_out
    after=evidence_snapshot(config)
    delta=evidence_delta(before,after)
    captured=copy_changed_evidence(delta,session_dir)
    result["evidence"]["artifacts"]=captured
    crash_sources=list((config.get("evidence") or {}).get("crash_paths") or [])
    frame_sources=list((config.get("evidence") or {}).get("frame_trace_paths") or [])
    result["evidence"]["crash_delta"]=[
        x for x in captured
        if any(path_matches_source(x["path"],source) for source in crash_sources)
    ]
    result["evidence"]["frame_traces"]=[
        x.get("captured_path") for x in captured
        if x.get("captured_path")
        and any(path_matches_source(x["path"],source) for source in frame_sources)
    ]
    result["evidence"]["log_delta"]=[
        x for x in captured
        if x not in result["evidence"]["crash_delta"]
    ]
    gates={row["gate"]:row for row in result["gates"]}
    gates["G19"]=evaluate_g19(
        config,
        result["evidence"]["log_delta"],
        result["evidence"]["crash_delta"],
    )
    result["gates"]=[gates[g] for g in ("G19","G20","G21","G26")]

    result["finished_at"]=now()
    if timed_out:
        result["status"]="failed"
        result["issues"].append("MO2/runtime process exceeded scenario timeout")
    elif exit_code not in (0,None):
        result["status"]="failed"
        result["issues"].append(f"MO2/runtime process exited with code {exit_code}")
    else:
        result["status"]="needs-review"
        result["issues"].append(
            "session launched and evidence was captured, but no typed in-game observer "
            "has proven the runtime assertions"
        )

    finalize_cleanup(result,config,success=result["status"]=="passed")
    validate(result,RESULT_SCHEMA,"runtime session result")
    return result

def main()->None:
    ap=argparse.ArgumentParser()
    ap.add_argument("test",type=Path)
    ap.add_argument("config",type=Path)
    ap.add_argument("--run-id",required=True)
    ap.add_argument("--build-id")
    ap.add_argument("--output",type=Path,required=True)
    ap.add_argument("--execute",action="store_true")
    args=ap.parse_args()
    try:
        result=run_session(
            load(args.test),
            load(args.config),
            run_id=args.run_id,
            build_id=args.build_id,
            execute=args.execute,
        )
    except ValueError as exc:
        raise SystemExit(str(exc))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(args.output)
    if result["status"]=="failed":
        raise SystemExit(2)
    if result["status"] in {"needs-review","aborted"}:
        raise SystemExit(3)

if __name__=="__main__":
    main()
