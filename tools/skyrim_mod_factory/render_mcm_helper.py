#!/usr/bin/env python3
"""Generate and statically validate MCM Helper config.json + settings.ini."""
from __future__ import annotations

import argparse
import json
import math
import re
from copy import deepcopy
from pathlib import Path
from typing import Any, Iterable

from jsonschema import Draft202012Validator, FormatChecker

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[1]
SCHEMAS=REPO/"schemas"
INTENT_SCHEMA=SCHEMAS/"skyrim-mcm-helper-intent-v1.schema.json"
REPORT_SCHEMA=SCHEMAS/"skyrim-mcm-helper-validation-report-v1.schema.json"
MCM_SCHEMA=REPO/"third_party/mcm-helper/config.schema.agent-os.json"
UPSTREAM_SCHEMA_URL="https://raw.githubusercontent.com/Exit-9B/MCM-Helper/main/docs/config.schema.json"

SETTING_SOURCE_PREFIXES={
    "ModSettingBool":{"b"},
    "ModSettingFloat":{"f"},
    "ModSettingInt":{"i","u","r"},
    "ModSettingString":{"s","S"},
}

def load(path:Path)->dict[str,Any]:
    return json.loads(path.read_text(encoding="utf-8"))

def validate_json(value:dict[str,Any],schema_path:Path)->list[str]:
    schema=load(schema_path)
    Draft202012Validator.check_schema(schema)
    validator=Draft202012Validator(schema,format_checker=FormatChecker())
    out=[]
    for err in validator.iter_errors(value):
        loc=".".join(str(x) for x in err.absolute_path) or "<root>"
        out.append(f"{loc}: {err.message}")
    return out

def issue(code:str,message:str,location:str|None=None,severity:str="ERROR")->dict[str,Any]:
    return {
        "severity":severity,
        "code":code,
        "message":message,
        "location":location,
    }

def setting_value_valid(name:str,value:Any)->bool:
    prefix=name[0] if name else ""
    if prefix=="b":
        return isinstance(value,bool) or (
            isinstance(value,int) and not isinstance(value,bool) and value in (0,1)
        )
    if prefix=="f":
        return isinstance(value,(int,float)) and not isinstance(value,bool) and math.isfinite(float(value))
    if prefix=="i":
        return isinstance(value,int) and not isinstance(value,bool)
    if prefix=="u":
        return isinstance(value,int) and not isinstance(value,bool) and value>=0
    if prefix=="r":
        return isinstance(value,int) and not isinstance(value,bool) and 0<=value<=0xFFFFFFFF
    if prefix in {"s","S"}:
        return isinstance(value,str) and "\n" not in value and "\r" not in value
    return False

def build_settings_index(settings:list[dict[str,Any]])->tuple[dict[str,dict[str,Any]],list[dict[str,Any]],list[dict[str,Any]]]:
    index={}
    rows=[]
    problems=[]
    seen_sections=set()
    for section in settings:
        section_name=section["name"]
        section_key=section_name.casefold()
        if section_key in seen_sections:
            problems.append(issue(
                "MCM-DUPLICATE-SECTION",
                f"duplicate settings.ini section {section_name!r}",
                f"settings.{section_name}",
            ))
        seen_sections.add(section_key)
        seen_names=set()
        for setting in section["values"]:
            name=setting["name"]
            skey=name.casefold()
            if skey in seen_names:
                problems.append(issue(
                    "MCM-DUPLICATE-SETTING",
                    f"duplicate setting {name!r} in section {section_name!r}",
                    f"settings.{section_name}.{name}",
                ))
            seen_names.add(skey)
            if not setting_value_valid(name,setting["value"]):
                problems.append(issue(
                    "MCM-SETTING-TYPE-MISMATCH",
                    f"default value for {name}:{section_name} is incompatible with prefix {name[:1]!r}",
                    f"settings.{section_name}.{name}",
                ))
            identifier=f"{name}:{section_name}"
            index[identifier.casefold()]=setting
            rows.append({
                "id":identifier,
                "prefix":name[0],
                "value":setting["value"],
            })
    return index,rows,problems

def iter_page_contents(config:dict[str,Any])->Iterable[tuple[str,list[dict[str,Any]]]]:
    if isinstance(config.get("content"),list):
        yield "<main>",config["content"]
    for i,page in enumerate(config.get("pages") or []):
        if isinstance(page.get("content"),list):
            yield f"pages[{i}] {page.get('pageDisplayName','<unnamed>')}",page["content"]

def group_condition_refs(value:Any)->list[int]:
    if isinstance(value,int) and not isinstance(value,bool):
        return [value]
    if isinstance(value,list):
        out=[]
        for x in value:
            out.extend(group_condition_refs(x))
        return out
    if isinstance(value,dict):
        out=[]
        for x in value.values():
            out.extend(group_condition_refs(x))
        return out
    return []

def validate_control(
    control:dict[str,Any],
    *,
    location:str,
    settings_index:dict[str,dict[str,Any]],
)->tuple[list[dict[str,Any]],dict[str,Any]|None]:
    problems=[]
    vo=control.get("valueOptions") or {}
    source=vo.get("sourceType")
    row=None
    if source in SETTING_SOURCE_PREFIXES:
        setting_id=control.get("id")
        row={
            "location":location,
            "type":control.get("type"),
            "id":setting_id,
            "source_type":source,
        }
        if not isinstance(setting_id,str) or ":" not in setting_id:
            problems.append(issue(
                "MCM-MODSETTING-ID-MISSING",
                f"{source} control requires an id in key:section form",
                location,
            ))
        else:
            default=settings_index.get(setting_id.casefold())
            if default is None:
                problems.append(issue(
                    "MCM-MODSETTING-DEFAULT-MISSING",
                    f"{source} control id {setting_id!r} has no settings.ini default",
                    location,
                ))
            setting_name=setting_id.split(":",1)[0]
            if not setting_name or setting_name[0] not in SETTING_SOURCE_PREFIXES[source]:
                problems.append(issue(
                    "MCM-MODSETTING-SOURCE-TYPE",
                    f"{source} is incompatible with setting prefix in {setting_id!r}",
                    location,
                ))

    ctype=control.get("type")
    if ctype=="slider":
        minimum=vo.get("min")
        maximum=vo.get("max")
        step=vo.get("step")
        if minimum is not None and maximum is not None and minimum>maximum:
            problems.append(issue(
                "MCM-SLIDER-RANGE",
                f"slider min {minimum} exceeds max {maximum}",
                location,
            ))
        if step is not None and step<=0:
            problems.append(issue(
                "MCM-SLIDER-STEP",
                f"slider step must be positive, got {step}",
                location,
            ))
    if ctype in {"menu","enum","stepper"}:
        options=vo.get("options")
        if options is not None and len(options)==0:
            problems.append(issue(
                "MCM-OPTIONS-EMPTY",
                f"{ctype} control has an empty options array",
                location,
            ))
        short=vo.get("shortNames")
        if short is not None and options is not None and len(short)!=len(options):
            problems.append(issue(
                "MCM-SHORTNAMES-LENGTH",
                f"{ctype} control has {len(options)} options but {len(short)} shortNames",
                location,
            ))
    if "groupControl" in control and ctype not in {"toggle","hiddenToggle"}:
        problems.append(issue(
            "MCM-GROUPCONTROL-TYPE",
            "groupControl may only be declared on toggle/hiddenToggle controls",
            location,
        ))
    return problems,row

def validate_semantics(intent:dict[str,Any])->dict[str,Any]:
    intent_errors=validate_json(intent,INTENT_SCHEMA)
    if intent_errors:
        raise ValueError("MCM Helper intent failed schema validation: "+"; ".join(intent_errors))

    config=deepcopy(intent["config"])
    config.setdefault("$schema",UPSTREAM_SCHEMA_URL)
    config_errors=validate_json(config,MCM_SCHEMA)
    problems=[
        issue("MCM-CONFIG-SCHEMA",x,"config")
        for x in config_errors
    ]

    mod_name=config.get("modName","")
    if (
        not isinstance(mod_name,str)
        or not mod_name
        or "/" in mod_name
        or "\\" in mod_name
        or mod_name.lower().endswith((".esp",".esm",".esl"))
    ):
        problems.append(issue(
            "MCM-MODNAME",
            "modName must be a path-free plugin name without .esp/.esm/.esl extension",
            "config.modName",
        ))

    settings_index,setting_rows,setting_problems=build_settings_index(intent["settings"])
    problems.extend(setting_problems)

    control_rows=[]
    group_condition_count=0
    page_count=0
    control_count=0
    for page_name,controls in iter_page_contents(config):
        page_count+=1
        group_controls={}
        refs=[]
        for i,control in enumerate(controls):
            control_count+=1
            location=f"{page_name}.content[{i}]"
            p,row=validate_control(
                control,location=location,settings_index=settings_index
            )
            problems.extend(p)
            if row is not None:
                control_rows.append(row)
            if "groupControl" in control:
                number=control["groupControl"]
                if number in group_controls:
                    problems.append(issue(
                        "MCM-DUPLICATE-GROUPCONTROL",
                        f"groupControl {number} is defined more than once on the same page",
                        location,
                    ))
                group_controls[number]=location
            if "groupCondition" in control:
                found=group_condition_refs(control["groupCondition"])
                group_condition_count+=len(found)
                refs.extend((number,location) for number in found)
        for number,location in refs:
            if number not in group_controls:
                problems.append(issue(
                    "MCM-GROUPCONDITION-UNRESOLVED",
                    f"groupCondition references undefined groupControl {number}",
                    location,
                ))

    errors=sum(x["severity"]=="ERROR" for x in problems)
    warnings=sum(x["severity"]=="WARNING" for x in problems)
    status="fail" if errors else ("needs-review" if warnings else "pass")
    report={
        "schema_version":"skyrim-mcm-helper-validation-report-v1",
        "status":status,
        "mod_name":str(mod_name),
        "controls":control_rows,
        "settings":setting_rows,
        "issues":problems,
        "coverage":{
            "pages":page_count,
            "controls":control_count,
            "mod_setting_controls":len(control_rows),
            "settings_defaults":len(setting_rows),
            "group_conditions":group_condition_count,
        },
    }
    report_errors=validate_json(report,REPORT_SCHEMA)
    if report_errors:
        raise ValueError(
            "MCM Helper validation report failed schema validation: "
            +"; ".join(report_errors)
        )
    return report

def ini_value(value:Any)->str:
    if isinstance(value,bool):
        return "1" if value else "0"
    if isinstance(value,float):
        return format(value,".15g")
    return str(value)

def render_settings(settings:list[dict[str,Any]])->str:
    lines=[]
    for index,section in enumerate(settings):
        if index:
            lines.append("")
        lines.append(f"[{section['name']}]")
        for setting in section["values"]:
            lines.append(f"{setting['name']}={ini_value(setting['value'])}")
    return "\n".join(lines)+"\n"

def render(intent:dict[str,Any])->tuple[bytes,bytes,dict[str,Any]]:
    report=validate_semantics(intent)
    if report["status"]=="fail":
        details="; ".join(x["message"] for x in report["issues"])
        raise ValueError("MCM Helper semantic validation failed: "+details)
    config=deepcopy(intent["config"])
    config.setdefault("$schema",UPSTREAM_SCHEMA_URL)
    config_bytes=(json.dumps(config,indent=2,ensure_ascii=False)+"\n").encode("utf-8")
    settings_bytes=render_settings(intent["settings"]).encode("utf-8")
    return config_bytes,settings_bytes,report

def main()->None:
    ap=argparse.ArgumentParser()
    ap.add_argument("intent",type=Path)
    ap.add_argument("--data-root",type=Path,required=True)
    ap.add_argument("--report",type=Path)
    args=ap.parse_args()
    try:
        value=load(args.intent)
        config_bytes,settings_bytes,report=render(value)
    except ValueError as exc:
        raise SystemExit(str(exc))

    mod_name=report["mod_name"]
    output=args.data_root/"MCM"/"Config"/mod_name
    output.mkdir(parents=True,exist_ok=True)
    (output/"config.json").write_bytes(config_bytes)
    (output/"settings.ini").write_bytes(settings_bytes)
    if args.report:
        args.report.parent.mkdir(parents=True,exist_ok=True)
        args.report.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(output)

if __name__=="__main__":
    main()
