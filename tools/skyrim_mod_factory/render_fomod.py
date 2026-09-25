#!/usr/bin/env python3
"""Render a conservative, schema-validated FOMOD installer from typed intent."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path, PurePosixPath
from typing import Any
import xml.etree.ElementTree as ET

from jsonschema import Draft202012Validator, FormatChecker

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[1]
SCHEMAS=REPO/"schemas"
INTENT_SCHEMA=SCHEMAS/"skyrim-fomod-intent-v1.schema.json"
FOMOD_XSD=REPO/"third_party/fomod-schema/ModuleConfig.xsd"
XSI="http://www.w3.org/2001/XMLSchema-instance"
SCHEMA_URL="http://qconsulting.ca/fo3/ModConfig5.0.xsd"

ET.register_namespace("xsi",XSI)

def load_json(path:Path)->dict[str,Any]:
    return json.loads(path.read_text(encoding="utf-8"))

def intent_errors(value:dict[str,Any])->list[str]:
    schema=load_json(INTENT_SCHEMA)
    out=[]
    validator=Draft202012Validator(schema,format_checker=FormatChecker())
    for err in validator.iter_errors(value):
        loc=".".join(str(x) for x in err.absolute_path) or "<root>"
        out.append(f"{loc}: {err.message}")
    return out

def clean_rel_path(value:str)->str:
    text=value.replace("\\","/").strip()
    if not text or text.startswith("/") or re.match(r"^[A-Za-z]:",text):
        raise ValueError(f"FOMOD path must be relative: {value!r}")
    parts=[p for p in PurePosixPath(text).parts if p not in ("",".")]
    if not parts or ".." in parts:
        raise ValueError(f"FOMOD path may not traverse outside package: {value!r}")
    return "\\".join(parts)

def package_path(root:Path,value:str)->Path:
    return root.joinpath(*clean_rel_path(value).split("\\"))

def bool_text(value:bool)->str:
    return "true" if value else "false"

def render_file_item(parent:ET.Element,item:dict[str,Any])->None:
    attrs={"source":clean_rel_path(item["source"])}
    if "destination" in item:
        attrs["destination"]=(
            "" if item["destination"]=="" else clean_rel_path(item["destination"])
        )
    if item.get("always_install",False):
        attrs["alwaysInstall"]="true"
    if item.get("install_if_usable",False):
        attrs["installIfUsable"]="true"
    if int(item.get("priority",0))!=0:
        attrs["priority"]=str(int(item["priority"]))
    ET.SubElement(parent,item["kind"],attrs)

def dependency_items(value:dict[str,Any])->tuple[str,list[dict[str,Any]]]:
    if value["kind"]=="group":
        return value["operator"],list(value["items"])
    return "And",[value]

def render_dependency_container(parent:ET.Element,value:dict[str,Any],tag:str)->ET.Element:
    operator,items=dependency_items(value)
    node=ET.SubElement(parent,tag,{"operator":operator})
    for dep in items:
        render_dependency(node,dep)
    return node

def render_dependency(parent:ET.Element,dep:dict[str,Any])->None:
    kind=dep["kind"]
    if kind=="file":
        ET.SubElement(parent,"fileDependency",{
            "file":dep["file"],"state":dep["state"],
        })
    elif kind=="flag":
        ET.SubElement(parent,"flagDependency",{
            "flag":dep["flag"],"value":dep["value"],
        })
    elif kind=="game":
        ET.SubElement(parent,"gameDependency",{"version":dep["version"]})
    elif kind=="fomm":
        ET.SubElement(parent,"fommDependency",{"version":dep["version"]})
    elif kind=="group":
        render_dependency_container(parent,dep,"dependencies")
    else:
        raise ValueError(f"unsupported dependency kind: {kind}")

def render_files(parent:ET.Element,items:list[dict[str,Any]],tag:str="files")->ET.Element:
    node=ET.SubElement(parent,tag)
    for item in items:
        render_file_item(node,item)
    return node

def render_info(intent:dict[str,Any])->ET.Element:
    meta=intent["metadata"]
    root=ET.Element("fomod")
    ET.SubElement(root,"Name").text=meta["name"]
    ET.SubElement(root,"Author").text=meta["author"]
    version=ET.SubElement(root,"Version")
    if meta.get("machine_version"):
        version.set("MachineVersion",meta["machine_version"])
    version.text=meta["version"]
    ET.SubElement(root,"Description").text=meta["description"]
    if meta.get("website"):
        ET.SubElement(root,"Website").text=meta["website"]
    if meta.get("id") is not None:
        ET.SubElement(root,"Id").text=str(meta["id"])
    return root

def render_module(intent:dict[str,Any])->ET.Element:
    module=intent["module"]
    root=ET.Element("config",{
        f"{{{XSI}}}noNamespaceSchemaLocation":SCHEMA_URL,
    })

    title=ET.SubElement(root,"moduleName")
    title.text=module["name"]
    if module.get("title_position","Left")!="Left":
        title.set("position",module["title_position"])
    if module.get("title_colour","000000").upper()!="000000":
        title.set("colour",module["title_colour"].upper())

    if module.get("image"):
        attrs={
            "path":clean_rel_path(module["image"]),
            "showImage":bool_text(module.get("image_show",True)),
            "showFade":bool_text(module.get("image_fade",True)),
            "height":str(int(module.get("image_height",-1))),
        }
        ET.SubElement(root,"moduleImage",attrs)

    if module.get("dependencies"):
        render_dependency_container(root,module["dependencies"],"moduleDependencies")

    if module.get("required_files"):
        render_files(root,list(module["required_files"]),"requiredInstallFiles")

    steps=list(module.get("steps") or [])
    if steps:
        steps_node=ET.SubElement(root,"installSteps",{
            "order":module.get("steps_order","Explicit"),
        })
        for step in steps:
            step_node=ET.SubElement(steps_node,"installStep",{"name":step["name"]})
            if step.get("visible"):
                render_dependency_container(step_node,step["visible"],"visible")
            groups_node=ET.SubElement(step_node,"optionalFileGroups",{"order":"Explicit"})
            for group in step["groups"]:
                group_node=ET.SubElement(groups_node,"group",{
                    "name":group["name"],
                    "type":group["type"],
                })
                plugins_node=ET.SubElement(group_node,"plugins",{
                    "order":group.get("order","Explicit"),
                })
                for option in group["options"]:
                    option_node=ET.SubElement(plugins_node,"plugin",{"name":option["name"]})
                    ET.SubElement(option_node,"description").text=option["description"]
                    if option.get("image"):
                        ET.SubElement(option_node,"image",{
                            "path":clean_rel_path(option["image"]),
                        })
                    files=list(option.get("files") or [])
                    flags=list(option.get("flags") or [])
                    if files:
                        render_files(option_node,files)
                    if flags:
                        flags_node=ET.SubElement(option_node,"conditionFlags")
                        for flag in flags:
                            f=ET.SubElement(flags_node,"flag",{"name":flag["name"]})
                            f.text=flag["value"]
                    desc=ET.SubElement(option_node,"typeDescriptor")
                    ET.SubElement(desc,"type",{"name":option["type"]})

    conditional=list(module.get("conditional_installs") or [])
    if conditional:
        cfi=ET.SubElement(root,"conditionalFileInstalls")
        patterns=ET.SubElement(cfi,"patterns")
        for pattern in conditional:
            p=ET.SubElement(patterns,"pattern")
            render_dependency_container(p,pattern["dependencies"],"dependencies")
            render_files(p,list(pattern["files"]))

    return root

def indent_xml(root:ET.Element)->bytes:
    ET.indent(root,space="  ")
    return ET.tostring(root,encoding="utf-8",xml_declaration=True)

def validate_xsd(xml_bytes:bytes,xsd_path:Path=FOMOD_XSD)->list[str]:
    try:
        from lxml import etree
    except ImportError as exc:
        raise ValueError("lxml is required for FOMOD XSD validation") from exc
    try:
        schema_doc=etree.parse(str(xsd_path))
        schema=etree.XMLSchema(schema_doc)
        document=etree.fromstring(xml_bytes)
    except (OSError,etree.XMLSyntaxError,etree.XMLSchemaParseError) as exc:
        raise ValueError(f"could not load FOMOD XSD: {exc}") from exc
    if schema.validate(document):
        return []
    return [
        f"line {x.line}: {x.message}"
        for x in schema.error_log
    ]

def referenced_sources(intent:dict[str,Any])->list[tuple[str,str]]:
    refs=[]
    module=intent["module"]
    if module.get("image"):
        refs.append(("image",module["image"]))
    for item in module.get("required_files") or []:
        refs.append((item["kind"],item["source"]))
    for step in module.get("steps") or []:
        for group in step["groups"]:
            for option in group["options"]:
                if option.get("image"):
                    refs.append(("image",option["image"]))
                for item in option.get("files") or []:
                    refs.append((item["kind"],item["source"]))
    for pattern in module.get("conditional_installs") or []:
        for item in pattern["files"]:
            refs.append((item["kind"],item["source"]))
    return refs

def validate_package_sources(intent:dict[str,Any],package_root:Path)->list[str]:
    issues=[]
    for kind,source in referenced_sources(intent):
        path=package_path(package_root,source)
        exists=path.is_dir() if kind=="folder" else path.is_file()
        if kind=="image":
            exists=path.is_file()
        if not exists:
            issues.append(f"referenced {kind} source does not exist: {source}")
    return issues

def validate_selection_semantics(intent:dict[str,Any])->list[str]:
    issues=[]
    for step in intent["module"].get("steps") or []:
        for group in step["groups"]:
            options=group["options"]
            recommended=sum(x["type"]=="Recommended" for x in options)
            required=sum(x["type"]=="Required" for x in options)
            if group["type"]=="SelectExactlyOne" and recommended>1:
                issues.append(
                    f"{step['name']} / {group['name']}: SelectExactlyOne has "
                    f"{recommended} Recommended defaults"
                )
            if group["type"]=="SelectAtMostOne" and required>1:
                issues.append(
                    f"{step['name']} / {group['name']}: SelectAtMostOne has "
                    f"{required} Required options"
                )
    return issues

def render(intent:dict[str,Any],*,package_root:Path|None=None)->tuple[bytes,bytes]:
    errors=intent_errors(intent)
    if errors:
        raise ValueError("FOMOD intent failed schema validation: "+"; ".join(errors))
    semantic=validate_selection_semantics(intent)
    if semantic:
        raise ValueError("FOMOD selection semantics invalid: "+"; ".join(semantic))
    if package_root is not None:
        source_errors=validate_package_sources(intent,package_root)
        if source_errors:
            raise ValueError("FOMOD package source validation failed: "+"; ".join(source_errors))
    info=indent_xml(render_info(intent))
    module=indent_xml(render_module(intent))
    xsd_errors=validate_xsd(module)
    if xsd_errors:
        raise ValueError("FOMOD ModuleConfig.xml failed XSD validation: "+"; ".join(xsd_errors))
    return info,module

def main()->None:
    ap=argparse.ArgumentParser()
    ap.add_argument("intent",type=Path)
    ap.add_argument("--output-dir",type=Path,required=True)
    ap.add_argument("--package-root",type=Path)
    args=ap.parse_args()

    try:
        info,module=render(
            load_json(args.intent),
            package_root=args.package_root,
        )
    except ValueError as exc:
        raise SystemExit(str(exc))

    fomod=args.output_dir/"fomod"
    fomod.mkdir(parents=True,exist_ok=True)
    (fomod/"info.xml").write_bytes(info)
    (fomod/"ModuleConfig.xml").write_bytes(module)
    print(fomod)

if __name__=="__main__":
    main()
