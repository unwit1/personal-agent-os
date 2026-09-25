#!/usr/bin/env python3
"""Validate deterministic Skyrim FaceGen path/pair/fingerprint invariants."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[1]
MANIFEST_SCHEMA=REPO/"schemas"/"skyrim-facegen-manifest-v1.schema.json"

def validate_manifest(value:dict[str,Any])->None:
    schema=json.loads(MANIFEST_SCHEMA.read_text(encoding="utf-8"))
    errors=sorted(Draft202012Validator(schema).iter_errors(value),key=lambda e:list(e.absolute_path))
    if errors:
        raise ValueError("; ".join(
            f'{".".join(str(x) for x in e.absolute_path) or "<root>"}: {e.message}'
            for e in errors
        ))

def sha256(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda:fh.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()

def split_form_key(value:str)->tuple[str,str]:
    local,plugin=value.split(":",1)
    return local.upper(),plugin

def facegen_filename(local_id:str)->str:
    return local_id.upper().zfill(8)

def resolve_casefold(root:Path,relative:Path)->Path:
    current=root
    for part in relative.parts:
        exact=current/part
        if exact.exists():
            current=exact
            continue
        if not current.is_dir():
            return exact
        matches=[x for x in current.iterdir() if x.name.casefold()==part.casefold()]
        if len(matches)==1:
            current=matches[0]
        else:
            return exact
    return current

def expected_relatives(form_key:str)->tuple[Path,Path]:
    local,plugin=split_form_key(form_key)
    stem=facegen_filename(local)
    return (
        Path("meshes/actors/character/FaceGenData/FaceGeom")/plugin/f"{stem}.nif",
        Path("textures/actors/character/FaceGenData/FaceTint")/plugin/f"{stem}.dds",
    )

def finding(rule_id:str,severity:str,message:str,record:str,**evidence:Any)->dict[str,Any]:
    row={
        "rule_id":rule_id,
        "severity":severity,
        "message":message,
        "record":record,
    }
    if evidence:
        row["evidence"]=evidence
    return row

def analyze(manifest:dict[str,Any])->dict[str,Any]:
    validate_manifest(manifest)
    root=Path(manifest["asset_root"])
    findings=[]
    expected_by_plugin:dict[str,set[str]]={}
    present_pairs=0

    for npc in manifest["npcs"]:
        form_key=npc["form_key"]
        local,plugin=split_form_key(form_key)
        stem=facegen_filename(local)
        expected_by_plugin.setdefault(plugin.casefold(),set()).add(stem.casefold())
        nif_rel,dds_rel=expected_relatives(form_key)
        nif=resolve_casefold(root,nif_rel)
        dds=resolve_casefold(root,dds_rel)
        nif_ok=nif.is_file()
        dds_ok=dds.is_file()

        if not nif_ok or not dds_ok:
            missing=[]
            if not nif_ok: missing.append(nif_rel.as_posix())
            if not dds_ok: missing.append(dds_rel.as_posix())
            findings.append(finding(
                "FACEGEN-PAIR","ERROR",
                "NPC FaceGen requires both FaceGeom NIF and FaceTint DDS",
                form_key,missing=missing,
            ))
            continue
        present_pairs+=1

        for key,path in (("nif_sha256",nif),("dds_sha256",dds)):
            expected=npc.get(key)
            if expected:
                actual=sha256(path)
                if actual!=expected:
                    findings.append(finding(
                        "FACEGEN-FINGERPRINT","ERROR",
                        f"{key} does not match generated/approved FaceGen fingerprint",
                        form_key,path=str(path),expected=expected,actual=actual,
                    ))

    if manifest.get("complete_for_origin_mods"):
        for plugin_key,expected in expected_by_plugin.items():
            for base,ext in (
                (Path("meshes/actors/character/FaceGenData/FaceGeom"),".nif"),
                (Path("textures/actors/character/FaceGenData/FaceTint"),".dds"),
            ):
                base_path=resolve_casefold(root,base)
                if not base_path.is_dir():
                    continue
                dirs=[x for x in base_path.iterdir() if x.is_dir() and x.name.casefold()==plugin_key]
                if len(dirs)!=1:
                    continue
                extras=sorted(
                    x.name for x in dirs[0].iterdir()
                    if x.is_file() and x.suffix.casefold()==ext and x.stem.casefold() not in expected
                )
                if extras:
                    findings.append(finding(
                        "FACEGEN-MANIFEST-COVERAGE","WARNING",
                        "complete FaceGen manifest does not account for files in an origin-plugin folder",
                        dirs[0].name,extension=ext,extras=extras,
                    ))

    status=(
        "fail" if any(x["severity"] in {"BLOCKER","ERROR"} for x in findings)
        else "needs-review" if any(x["severity"]=="WARNING" for x in findings)
        else "pass"
    )
    return {
        "schema_version":"skyrim-static-invariant-report-v1",
        "analyzer":"facegen-coherence-v1",
        "status":status,
        "scope":{
            "asset_root":str(root),
            "declared_npcs":len(manifest["npcs"]),
            "complete_for_origin_mods":bool(manifest.get("complete_for_origin_mods")),
        },
        "findings":findings,
        "coverage":{
            "declared_npcs":len(manifest["npcs"]),
            "present_pairs":present_pairs,
            "path_rule":"FaceGeom/<defining-plugin>/<00+6-digit-local-id>.nif + FaceTint/<defining-plugin>/<00+6-digit-local-id>.dds",
            "fingerprints_checked":sum(
                int(bool(x.get("nif_sha256")))+int(bool(x.get("dds_sha256")))
                for x in manifest["npcs"]
            ),
            "semantic_face_match_checked":False,
        },
        "issues":[
            "NIF/DDS presence and optional fingerprints do not prove that exported face geometry matches winning NPC_ face fields"
        ],
    }

def main()->None:
    ap=argparse.ArgumentParser()
    ap.add_argument("manifest",type=Path)
    ap.add_argument("--output",type=Path)
    args=ap.parse_args()
    value=json.loads(args.manifest.read_text(encoding="utf-8"))
    try:
        result=analyze(value)
    except ValueError as exc:
        raise SystemExit(str(exc))
    text=json.dumps(result,indent=2)+"\n"
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(text,encoding="utf-8")
    else:
        print(text,end="")
    raise SystemExit(0 if result["status"]=="pass" else 2 if result["status"]=="fail" else 3)

if __name__=="__main__":
    main()
