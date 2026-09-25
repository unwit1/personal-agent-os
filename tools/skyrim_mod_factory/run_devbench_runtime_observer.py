#!/usr/bin/env python3
"""Run a typed Skyrim runtime test through devbench REST and emit fresh observation evidence.

Supported runtime-test drivers:
- kind=tool      -> devbench scenario tool step
- kind=wait-for  -> waitFor event/state transition
- kind=wait-until-> waitUntil live predicate
- kind=wait      -> bounded fixed wait

Assertion probes call any devbench-registered REST tool and evaluate a declared JSON path
with the runtime-test operator. G26 is intentionally not emitted here; the session merger
derives it from assertion outcomes. Performance assertions may emit G20 evidence.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[1]
SCHEMAS=REPO/"schemas"
TEST_SCHEMA="skyrim-runtime-test-v1.schema.json"
SESSION_SCHEMA="skyrim-runtime-session-result-v1.schema.json"
OBS_SCHEMA="skyrim-runtime-observation-v1.schema.json"
MISSING=object()

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

def http_json(
    method:str,
    url:str,
    payload:dict[str,Any]|None=None,
    *,
    timeout_seconds:float=10.0,
)->Any:
    data=None
    headers={"Accept":"application/json"}
    if payload is not None:
        data=json.dumps(payload).encode("utf-8")
        headers["Content-Type"]="application/json"
    request=urllib.request.Request(url,data=data,headers=headers,method=method)
    try:
        with urllib.request.urlopen(request,timeout=timeout_seconds) as response:
            raw=response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        body=exc.read().decode("utf-8",errors="replace")
        raise ValueError(
            f"devbench HTTP {exc.code} for {url}: {body[-2000:]}"
        ) from exc
    except (urllib.error.URLError,TimeoutError,OSError) as exc:
        raise ValueError(f"devbench request failed for {url}: {exc}") from exc
    try:
        value=json.loads(raw or "{}")
    except json.JSONDecodeError as exc:
        raise ValueError(f"devbench returned invalid JSON for {url}: {exc}") from exc
    return value

def health(base_url:str,timeout_seconds:float=5.0)->dict[str,Any]:
    value=http_json(
        "GET",
        base_url.rstrip("/")+"/api/health",
        timeout_seconds=timeout_seconds,
    )
    if not isinstance(value,dict):
        raise ValueError(f"devbench health returned non-object JSON: {value!r}")
    if value.get("ok") is not True:
        raise ValueError(f"devbench health did not report ok=true: {value}")
    return value

def wait_for_health(
    base_url:str,
    *,
    wait_seconds:float,
    request_timeout_seconds:float=2.0,
)->dict[str,Any]:
    deadline=time.monotonic()+wait_seconds
    last_error=None
    while time.monotonic()<deadline:
        try:
            return health(base_url,request_timeout_seconds)
        except ValueError as exc:
            last_error=exc
            time.sleep(0.5)
    raise ValueError(
        f"devbench did not become healthy within {wait_seconds} seconds"
        + (f": {last_error}" if last_error else "")
    )

def post_tool(
    base_url:str,
    name:str,
    arguments:dict[str,Any],
    *,
    timeout_seconds:float=30.0,
)->Any:
    encoded=urllib.parse.quote(name,safe="")
    return http_json(
        "POST",
        base_url.rstrip("/")+"/api/tool/"+encoded,
        arguments,
        timeout_seconds=timeout_seconds,
    )

def compile_driver(step:dict[str,Any])->dict[str,Any]:
    driver=step.get("driver")
    if not isinstance(driver,dict):
        raise ValueError(f"runtime step {step['id']} has no typed driver")
    if driver.get("adapter")!="devbench":
        raise ValueError(
            f"runtime step {step['id']} targets {driver.get('adapter')!r}, not devbench"
        )
    kind=driver["kind"]
    if kind=="tool":
        return {
            "tool":driver["tool"],
            "args":driver.get("arguments") or {},
        }
    if kind=="wait-for":
        row={"waitFor":driver["event"]}
    elif kind=="wait-until":
        row={"waitUntil":driver["condition"]}
    elif kind=="wait":
        return {"wait":driver["milliseconds"]}
    else:
        raise ValueError(f"unsupported devbench driver kind: {kind}")
    timeout=driver.get("timeout_ms")
    if timeout is None and step.get("timeout_seconds") is not None:
        timeout=int(float(step["timeout_seconds"])*1000)
    if timeout is not None:
        row["timeoutMs"]=int(timeout)
    return row

def compile_scenario(test:dict[str,Any])->dict[str,Any]:
    return {"steps":[compile_driver(step) for step in test["steps"]]}

def step_result_status(value:dict[str,Any])->str:
    if value.get("ok") is False or value.get("satisfied") is False:
        return "failed"
    if value.get("ok") is True or value.get("satisfied") is True:
        return "passed"
    kind=value.get("kind")
    if kind=="wait" and value.get("elapsedMs") is not None:
        return "passed"
    return "needs-review"

def scenario_step_observations(
    test:dict[str,Any],
    response:dict[str,Any],
)->list[dict[str,Any]]:
    rows=response.get("results")
    if not isinstance(rows,list):
        return [
            {
                "id":step["id"],
                "status":"needs-review",
                "issues":["devbench scenario response omitted results transcript"],
                "evidence":[],
            }
            for step in test["steps"]
        ]
    by_index={
        row.get("index"):row
        for row in rows
        if isinstance(row,dict) and isinstance(row.get("index"),int)
    }
    out=[]
    for index,step in enumerate(test["steps"]):
        raw=by_index.get(index)
        if raw is None:
            out.append({
                "id":step["id"],
                "status":"needs-review",
                "issues":["devbench scenario transcript omitted this step"],
                "evidence":[],
            })
            continue
        status=step_result_status(raw)
        issues=[] if status=="passed" else [
            "devbench scenario step did not produce a decisive successful result"
        ]
        out.append({
            "id":step["id"],
            "status":status,
            "issues":issues,
            "evidence":[f"devbench://scenario/results/{index}"],
        })
    return out

def get_json_path(value:Any,path:str|None)->Any:
    if not path:
        return value
    current=value
    for part in path.split("."):
        if part=="":
            continue
        if isinstance(current,dict) and part in current:
            current=current[part]
        elif isinstance(current,list) and part.isdigit():
            index=int(part)
            if index>=len(current):
                return MISSING
            current=current[index]
        else:
            return MISSING
    return current

def evaluate_operator(
    observed:Any,
    expected:Any,
    operator:str,
    tolerance:float|None=None,
)->bool|None:
    if operator=="exists":
        return observed is not MISSING
    if operator=="not_exists":
        return observed is MISSING
    if observed is MISSING:
        return False
    if operator=="custom":
        return None
    if operator=="eq":
        if (
            tolerance is not None
            and isinstance(observed,(int,float))
            and isinstance(expected,(int,float))
        ):
            return abs(float(observed)-float(expected))<=tolerance
        return observed==expected
    if operator=="ne":
        return observed!=expected
    try:
        if operator=="gt":
            return observed>expected
        if operator=="gte":
            return observed>=expected
        if operator=="lt":
            return observed<expected
        if operator=="lte":
            return observed<=expected
        if operator=="contains":
            return expected in observed
        if operator=="not_contains":
            return expected not in observed
        if operator=="matches":
            return re.search(str(expected),str(observed)) is not None
    except (TypeError,ValueError,re.error):
        return None
    return None

def capture_trust_issue(
    assertion:dict[str,Any],
    raw:Any,
)->str|None:
    if assertion.get("kind")!="screenshot":
        return None
    probe=assertion.get("probe") or {}
    if probe.get("tool")!="capture" or not isinstance(raw,dict):
        return "screenshot assertion did not return a structured DevBench capture result"
    if raw.get("inconclusive") is True:
        return (
            "DevBench capture is inconclusive: "
            +str(raw.get("inconclusiveReason") or "unspecified reason")
        )
    if raw.get("goldenError"):
        return "DevBench golden comparison failed: "+str(raw["goldenError"])
    if raw.get("provider")=="native":
        return "native fallback screenshots are not trusted for deterministic visual PASS"
    return None

def capture_artifact(
    assertion:dict[str,Any],
    raw:Any,
)->dict[str,Any]|None:
    if assertion.get("kind")!="screenshot":
        return None
    probe=assertion.get("probe") or {}
    if probe.get("tool")!="capture" or not isinstance(raw,dict):
        return None
    raw_path=raw.get("path")
    if not isinstance(raw_path,str) or not raw_path:
        return None
    artifact={
        "kind":"screenshot",
        "path":raw_path,
        "checkpoint_id":raw.get("checkpointId"),
        "provider":raw.get("provider"),
        "inconclusive":bool(raw.get("inconclusive",False)),
        "ssim":raw.get("ssim"),
        "threshold":raw.get("threshold"),
        "passed":raw.get("passed"),
    }
    local=Path(raw_path)
    if local.is_file():
        artifact["sha256"]=sha256_file(local)
    else:
        artifact["sha256"]=None
    return artifact

def assertion_observation(
    assertion:dict[str,Any],
    *,
    base_url:str,
    timeout_seconds:float,
)->tuple[dict[str,Any],dict[str,Any]|None]:
    probe=assertion.get("probe")
    if not isinstance(probe,dict) or probe.get("adapter")!="devbench":
        return {
            "id":assertion["id"],
            "status":"needs-review",
            "observed":None,
            "issues":["assertion has no devbench probe"],
            "evidence":[],
        },None
    try:
        raw=post_tool(
            base_url,
            probe["tool"],
            probe.get("arguments") or {},
            timeout_seconds=timeout_seconds,
        )
    except ValueError as exc:
        return {
            "id":assertion["id"],
            "status":"needs-review",
            "observed":None,
            "issues":[str(exc)],
            "evidence":[],
        },None
    observed=get_json_path(raw,probe.get("json_path"))
    trust_issue=capture_trust_issue(assertion,raw)
    outcome=evaluate_operator(
        observed,
        assertion.get("expected"),
        assertion.get("operator","eq"),
        assertion.get("tolerance"),
    )
    if trust_issue is not None:
        status="needs-review"
        issues=[trust_issue]
    elif outcome is True:
        status="pass"
        issues=[]
    elif outcome is False:
        status="fail"
        issues=[
            f"probe value did not satisfy operator {assertion.get('operator','eq')}"
        ]
    else:
        status="needs-review"
        issues=[
            f"operator {assertion.get('operator','eq')} could not be evaluated deterministically"
        ]
    rendered_observed=None if observed is MISSING else observed
    return {
        "id":assertion["id"],
        "status":status,
        "observed":rendered_observed,
        "issues":issues,
        "evidence":[
            f"devbench://tool/{probe['tool']}#{probe.get('json_path') or '<root>'}"
        ],
    },raw

def identity_tuple(value:dict[str,Any])->tuple[Any,...]:
    return tuple(value.get(k) for k in ("pid","port","exe","vr"))

def sha256_file(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()

def write_artifact(
    evidence_dir:Path|None,
    name:str,
    value:Any,
    kind:str,
)->dict[str,Any]|None:
    if evidence_dir is None:
        return None
    evidence_dir.mkdir(parents=True,exist_ok=True)
    path=evidence_dir/name
    path.write_text(json.dumps(value,indent=2)+"\n",encoding="utf-8")
    return {
        "kind":kind,
        "path":str(path),
        "sha256":sha256_file(path),
    }

def assertion_targets_gate(assertion:dict[str,Any],gate:str)->bool:
    declared=set(assertion.get("gates") or [])
    if gate in declared:
        return True
    if gate=="G20" and assertion.get("kind")=="performance":
        return True
    return False

def scoped_assertion_gate(
    gate:str,
    test:dict[str,Any],
    observations:list[dict[str,Any]],
)->dict[str,Any]|None:
    by_id={row["id"]:row for row in observations}
    selected=[
        assertion for assertion in test["assertions"]
        if assertion_targets_gate(assertion,gate)
    ]
    if not selected:
        return None
    rows=[by_id[x["id"]] for x in selected if x["id"] in by_id]
    if len(rows)!=len(selected) or any(x["status"]=="needs-review" for x in rows):
        status="needs-review"
        issues=[f"one or more {gate} assertions lack decisive evidence"]
    elif any(x["status"]=="fail" for x in rows):
        status="fail"
        issues=[f"one or more {gate} assertions failed"]
    else:
        status="pass"
        issues=[]
    return {
        "gate":gate,
        "status":status,
        "evidence":[f'{row["id"]}: {row["status"]}' for row in rows],
        "issues":issues,
    }


def run_observer(
    test:dict[str,Any],
    session:dict[str,Any],
    *,
    base_url:str="http://127.0.0.1:8920",
    health_wait_seconds:float=60.0,
    request_timeout_seconds:float=30.0,
    evidence_dir:Path|None=None,
    initial_health:dict[str,Any]|None=None,
)->dict[str,Any]:
    validate(test,TEST_SCHEMA,"runtime test")
    validate(session,SESSION_SCHEMA,"runtime session")
    if session["test_id"]!=test["test_id"] or session["project_id"]!=test["project_id"]:
        raise ValueError("runtime test does not match session test/project identity")
    if not session["launch"]["attempted"] or not session.get("started_at"):
        raise ValueError("devbench observer requires an already-launched runtime session")

    before=initial_health or wait_for_health(
        base_url,
        wait_seconds=health_wait_seconds,
        request_timeout_seconds=min(request_timeout_seconds,5.0),
    )
    if before.get("ok") is not True:
        raise ValueError("initial DevBench health must report ok=true")
    artifacts=[]
    artifact=write_artifact(
        evidence_dir,"devbench-health-before.json",before,"devbench-health"
    )
    if artifact:
        artifacts.append(artifact)

    payload=compile_scenario(test)
    scenario=post_tool(
        base_url,
        "scenario",
        payload,
        timeout_seconds=request_timeout_seconds,
    )
    artifact=write_artifact(
        evidence_dir,"devbench-scenario.json",scenario,"devbench-scenario"
    )
    if artifact:
        artifacts.append(artifact)
    steps=scenario_step_observations(test,scenario)

    assertions=[]
    for index,assertion in enumerate(test["assertions"],1):
        row,raw=assertion_observation(
            assertion,
            base_url=base_url,
            timeout_seconds=request_timeout_seconds,
        )
        assertions.append(row)
        if raw is not None:
            artifact=write_artifact(
                evidence_dir,
                f"devbench-probe-{index:03d}-{assertion['id']}.json",
                raw,
                "devbench-probe",
            )
            if artifact:
                artifacts.append(artifact)
            screenshot=capture_artifact(assertion,raw)
            if screenshot:
                artifacts.append(screenshot)

    after=health(base_url,min(request_timeout_seconds,5.0))
    artifact=write_artifact(
        evidence_dir,"devbench-health-after.json",after,"devbench-health"
    )
    if artifact:
        artifacts.append(artifact)

    issues=[]
    if identity_tuple(before)!=identity_tuple(after):
        issues.append(
            "devbench instance identity changed during scenario; evidence is not "
            "accepted as one continuous game process"
        )
        for row in steps:
            if row["status"]=="passed":
                row["status"]="needs-review"
                row["issues"].append("game instance identity changed during scenario")
        for row in assertions:
            if row["status"]=="pass":
                row["status"]="needs-review"
                row["issues"].append("game instance identity changed during scenario")

    gates=[]
    for gate in ("G20","G21"):
        row=scoped_assertion_gate(gate,test,assertions)
        if row is not None:
            gates.append(row)

    observation={
        "schema_version":"skyrim-runtime-observation-v1",
        "run_id":session["run_id"],
        "session_token":session["session_token"],
        "observer_id":"devbench-rest",
        "observer_version":None,
        "transport":"REST",
        "captured_at":now(),
        "steps":steps,
        "assertions":assertions,
        "gates":gates,
        "artifacts":artifacts,
        "issues":issues,
    }
    validate(observation,OBS_SCHEMA,"devbench runtime observation")
    return observation

def main()->None:
    ap=argparse.ArgumentParser()
    ap.add_argument("test",type=Path)
    ap.add_argument("session",type=Path)
    ap.add_argument("--base-url",default="http://127.0.0.1:8920")
    ap.add_argument("--health-wait-seconds",type=float,default=60.0)
    ap.add_argument("--request-timeout-seconds",type=float,default=30.0)
    ap.add_argument("--evidence-dir",type=Path)
    ap.add_argument("--output",type=Path,required=True)
    args=ap.parse_args()
    try:
        observation=run_observer(
            load(args.test),
            load(args.session),
            base_url=args.base_url,
            health_wait_seconds=args.health_wait_seconds,
            request_timeout_seconds=args.request_timeout_seconds,
            evidence_dir=args.evidence_dir,
        )
    except ValueError as exc:
        raise SystemExit(str(exc))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(observation,indent=2)+"\n",encoding="utf-8")
    print(args.output)
    if any(
        row["status"]=="fail"
        for row in observation["assertions"]
    ):
        raise SystemExit(2)
    if any(
        row["status"]=="needs-review"
        for row in observation["steps"]+observation["assertions"]
    ):
        raise SystemExit(3)

if __name__=="__main__":
    main()
