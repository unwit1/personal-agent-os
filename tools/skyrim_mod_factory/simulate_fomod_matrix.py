#!/usr/bin/env python3
"""Enumerate and validate FOMOD option combinations without a mod manager UI."""
from __future__ import annotations

import argparse
import itertools
import json
import re
from copy import deepcopy
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[1]
SCHEMAS=REPO/"schemas"
INTENT_SCHEMA=SCHEMAS/"skyrim-fomod-intent-v1.schema.json"
REPORT_SCHEMA=SCHEMAS/"skyrim-fomod-matrix-report-v1.schema.json"

def load(path:Path)->dict[str,Any]:
    return json.loads(path.read_text(encoding="utf-8"))

def schema_errors(value:dict[str,Any],path:Path)->list[str]:
    schema=load(path)
    validator=Draft202012Validator(schema,format_checker=FormatChecker())
    out=[]
    for err in validator.iter_errors(value):
        loc=".".join(str(x) for x in err.absolute_path) or "<root>"
        out.append(f"{loc}: {err.message}")
    return out

def version_tuple(value:str)->tuple[int,...]:
    parts=[]
    for piece in re.split(r"[._-]",value):
        if piece=="":
            continue
        m=re.match(r"^(\d+)",piece)
        if not m:
            break
        parts.append(int(m.group(1)))
    if not parts:
        raise ValueError(f"version is not comparable numerically: {value!r}")
    return tuple(parts)

def version_at_least(current:str,minimum:str)->bool:
    a=list(version_tuple(current)); b=list(version_tuple(minimum))
    n=max(len(a),len(b))
    return tuple(a+[0]*(n-len(a))) >= tuple(b+[0]*(n-len(b)))

def eval_dependency(dep:dict[str,Any],environment:dict[str,Any],flags:dict[str,str])->bool:
    kind=dep["kind"]
    if kind=="file":
        state=(environment.get("files") or {}).get(dep["file"],"Missing")
        return state==dep["state"]
    if kind=="flag":
        return flags.get(dep["flag"])==dep["value"]
    if kind=="game":
        current=environment.get("game_version")
        return bool(current) and version_at_least(str(current),dep["version"])
    if kind=="fomm":
        current=environment.get("fomm_version")
        return bool(current) and version_at_least(str(current),dep["version"])
    if kind=="group":
        values=[eval_dependency(x,environment,flags) for x in dep["items"]]
        return all(values) if dep["operator"]=="And" else any(values)
    raise ValueError(f"unsupported dependency kind: {kind}")

def option_is_usable(option:dict[str,Any])->bool:
    return option["type"] not in {"NotUsable"}

def group_choices(group:dict[str,Any])->list[tuple[int,...]]:
    options=group["options"]
    usable=[i for i,x in enumerate(options) if option_is_usable(x)]
    required=[i for i,x in enumerate(options) if x["type"]=="Required"]
    required_set=set(required)
    kind=group["type"]

    def valid(choice:tuple[int,...])->bool:
        selected=set(choice)
        if not required_set.issubset(selected):
            return False
        count=len(selected)
        if kind=="SelectExactlyOne":
            return count==1
        if kind=="SelectAtMostOne":
            return count<=1
        if kind=="SelectAtLeastOne":
            return count>=1
        if kind=="SelectAll":
            return selected==set(range(len(options)))
        if kind=="SelectAny":
            return True
        raise ValueError(f"unsupported group type: {kind}")

    if kind=="SelectAll":
        candidates=[tuple(usable)]
    else:
        candidates=[
            combo
            for n in range(len(usable)+1)
            for combo in itertools.combinations(usable,n)
        ]
    return [x for x in candidates if valid(x)]

def validate_unique_names(intent:dict[str,Any])->list[str]:
    issues=[]
    steps=intent["module"].get("steps") or []
    seen_steps=set()
    for step in steps:
        s=step["name"].casefold()
        if s in seen_steps:
            issues.append(f"duplicate install step name: {step['name']}")
        seen_steps.add(s)
        seen_groups=set()
        for group in step["groups"]:
            g=group["name"].casefold()
            if g in seen_groups:
                issues.append(
                    f"{step['name']}: duplicate group name: {group['name']}"
                )
            seen_groups.add(g)
            seen_options=set()
            for option in group["options"]:
                o=option["name"].casefold()
                if o in seen_options:
                    issues.append(
                        f"{step['name']} / {group['name']}: "
                        f"duplicate option name: {option['name']}"
                    )
                seen_options.add(o)
    return issues

def effective_destination(item:dict[str,Any])->str:
    if "destination" in item:
        return item["destination"]
    return item["source"]

def install_row(item:dict[str,Any],reason:str)->dict[str,Any]:
    return {
        "kind":item["kind"],
        "source":item["source"],
        "destination":effective_destination(item),
        "priority":int(item.get("priority",0)),
        "reason":reason,
    }

def add_flag(flags:dict[str,str],name:str,value:str,issues:list[str],reason:str)->None:
    existing=flags.get(name)
    if existing is not None and existing!=value:
        issues.append(
            f"condition flag conflict for {name!r}: "
            f"{existing!r} versus {value!r} ({reason})"
        )
        return
    flags[name]=value

def enumerate_step_states(
    base:dict[str,Any],
    step:dict[str,Any],
    environment:dict[str,Any],
    *,
    max_cases:int,
)->list[dict[str,Any]]:
    if step.get("visible") and not eval_dependency(
        step["visible"],environment,base["flags"]
    ):
        state=deepcopy(base)
        return [state]

    group_choices_list=[]
    for group in step["groups"]:
        choices=group_choices(group)
        if not choices:
            state=deepcopy(base)
            state["issues"].append(
                f"unsatisfiable group {step['name']} / {group['name']}"
            )
            return [state]
        group_choices_list.append((group,choices))

    total=1
    for _,choices in group_choices_list:
        total*=len(choices)
        if total>max_cases:
            raise ValueError(
                f"step {step['name']!r} expands beyond max_cases={max_cases}"
            )

    states=[]
    for product in itertools.product(*(choices for _,choices in group_choices_list)):
        state=deepcopy(base)
        state["visible_steps"].append(step["name"])
        for (group,_),selected_indices in zip(group_choices_list,product):
            selected_set=set(selected_indices)
            selected_names=[]
            for idx,option in enumerate(group["options"]):
                selected=idx in selected_set
                if selected:
                    selected_names.append(option["name"])
                    for flag in option.get("flags") or []:
                        add_flag(
                            state["flags"],flag["name"],flag["value"],
                            state["issues"],
                            f"{step['name']} / {group['name']} / {option['name']}",
                        )
                for item in option.get("files") or []:
                    should_install=(
                        selected
                        or bool(item.get("always_install",False))
                        or (
                            bool(item.get("install_if_usable",False))
                            and option_is_usable(option)
                        )
                    )
                    if should_install:
                        reason=(
                            f"selected option {step['name']} / {group['name']} / {option['name']}"
                            if selected else
                            f"option policy {step['name']} / {group['name']} / {option['name']}"
                        )
                        state["installed_items"].append(install_row(item,reason))
            state["selections"].append({
                "step":step["name"],
                "group":group["name"],
                "options":selected_names,
            })
        states.append(state)
        if len(states)>max_cases:
            raise ValueError(f"matrix exceeds max_cases={max_cases}")
    return states

def destination_issues(items:list[dict[str,Any]])->list[str]:
    by_dest={}
    issues=[]
    for row in items:
        dest=str(row["destination"]).replace("\\","/").casefold()
        by_dest.setdefault(dest,[]).append(row)
    for dest,rows in by_dest.items():
        sources={str(x["source"]).casefold() for x in rows}
        if len(sources)<=1:
            continue
        max_priority=max(int(x["priority"]) for x in rows)
        winners=[x for x in rows if int(x["priority"])==max_priority]
        winner_sources={str(x["source"]).casefold() for x in winners}
        if len(winner_sources)>1:
            issues.append(
                f"ambiguous install collision at {dest!r}: "
                f"multiple distinct sources share winning priority {max_priority}"
            )
    return issues

def simulate(
    intent:dict[str,Any],
    *,
    environment:dict[str,Any]|None=None,
    max_cases:int=4096,
)->dict[str,Any]:
    errors=schema_errors(intent,INTENT_SCHEMA)
    if errors:
        raise ValueError("FOMOD intent failed schema validation: "+"; ".join(errors))
    if max_cases<1:
        raise ValueError("max_cases must be >= 1")
    environment=deepcopy(environment or {})
    environment.setdefault("files",{})

    issues=validate_unique_names(intent)
    module=intent["module"]
    module_ok=(
        eval_dependency(module["dependencies"],environment,{})
        if module.get("dependencies") else True
    )

    initial={
        "visible_steps":[],
        "selections":[],
        "flags":{},
        "installed_items":[
            install_row(x,"required install")
            for x in module.get("required_files") or []
        ],
        "issues":[],
    }
    states=[initial]

    if module_ok:
        for step in module.get("steps") or []:
            next_states=[]
            for state in states:
                remaining=max_cases-len(next_states)
                if remaining<=0:
                    raise ValueError(f"matrix exceeds max_cases={max_cases}")
                next_states.extend(
                    enumerate_step_states(
                        state,step,environment,max_cases=max_cases
                    )
                )
                if len(next_states)>max_cases:
                    raise ValueError(f"matrix exceeds max_cases={max_cases}")
            states=next_states

        for state in states:
            for idx,pattern in enumerate(module.get("conditional_installs") or []):
                if eval_dependency(pattern["dependencies"],environment,state["flags"]):
                    for item in pattern["files"]:
                        state["installed_items"].append(
                            install_row(item,f"conditional pattern {idx+1}")
                        )
            state["installed_items"].sort(
                key=lambda x:(int(x["priority"]),x["destination"],x["source"])
            )
            state["issues"].extend(destination_issues(state["installed_items"]))
    else:
        states=[]

    cases=[]
    for i,state in enumerate(states,1):
        cases.append({
            "case_id":i,
            "visible_steps":state["visible_steps"],
            "selections":state["selections"],
            "flags":state["flags"],
            "installed_items":state["installed_items"],
            "issues":state["issues"],
        })

    case_issues=sum(bool(x["issues"]) for x in cases)
    if issues or case_issues:
        status="fail"
    elif not module_ok:
        status="pass"
    else:
        status="pass"

    report={
        "schema_version":"skyrim-fomod-matrix-report-v1",
        "status":status,
        "module_dependencies_met":module_ok,
        "environment":environment,
        "total_cases":len(cases),
        "cases":cases,
        "issues":issues,
        "coverage":{
            "steps":len(module.get("steps") or []),
            "groups":sum(
                len(step["groups"]) for step in module.get("steps") or []
            ),
            "options":sum(
                len(group["options"])
                for step in module.get("steps") or []
                for group in step["groups"]
            ),
            "conditional_patterns":len(module.get("conditional_installs") or []),
            "enumerated_cases":len(cases),
            "max_cases":max_cases,
        },
    }
    report_errors=schema_errors(report,REPORT_SCHEMA)
    if report_errors:
        raise ValueError(
            "FOMOD matrix report failed schema validation: "
            +"; ".join(report_errors)
        )
    return report

def main()->None:
    ap=argparse.ArgumentParser()
    ap.add_argument("intent",type=Path)
    ap.add_argument("--environment",type=Path)
    ap.add_argument("--max-cases",type=int,default=4096)
    ap.add_argument("--output",type=Path)
    args=ap.parse_args()
    try:
        report=simulate(
            load(args.intent),
            environment=load(args.environment) if args.environment else None,
            max_cases=args.max_cases,
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
