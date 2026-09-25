#!/usr/bin/env python3
"""Inventory an external training-data source tree without copying its raw assets.

The output is a reproducible manifest of paths, hashes, file types and lightweight SVG/image
metadata. It is intended for source trees cloned at a pinned Git commit or unpacked from a
versioned archive.

Outputs:
  asset_manifest.jsonl
  source_inventory_summary.json
"""

from __future__ import annotations
import argparse, hashlib, json, os, re, subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from xml.etree import ElementTree as ET

VERSION="training-source-tree-inventory/v1"
RASTER={".png",".jpg",".jpeg",".webp",".gif",".bmp",".tif",".tiff"}
VECTOR={".svg",".eps",".ai",".pdf"}
MESH={".obj",".fbx",".dae",".gltf",".glb",".stl",".3mf",".blend",".dat"}
TEXT={".txt",".md",".json",".csv",".tsv",".xml",".yaml",".yml",".ini",".cfg"}

def now_iso(): return datetime.now(timezone.utc).isoformat()
def sha256(path:Path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for c in iter(lambda:f.read(1024*1024),b""): h.update(c)
    return h.hexdigest()
def git_head(root:Path):
    try:return subprocess.check_output(["git","-C",str(root),"rev-parse","HEAD"],text=True).strip()
    except Exception:return None
def classify(ext):
    e=ext.lower()
    if e in RASTER:return "raster_image"
    if e in VECTOR:return "vector_or_document"
    if e in MESH:return "geometry"
    if e in TEXT:return "metadata_or_text"
    return "other"
def svg_meta(path):
    try:
        root=ET.parse(path).getroot()
        vb=root.attrib.get("viewBox")
        width=root.attrib.get("width")
        height=root.attrib.get("height")
        counts=Counter()
        for el in root.iter():
            tag=el.tag.rsplit("}",1)[-1]
            counts[tag]+=1
        return {"width":width,"height":height,"viewBox":vb,"element_counts":dict(counts)}
    except Exception as exc:
        return {"parse_error":str(exc)[:500]}
def image_meta(path):
    try:
        from PIL import Image
        with Image.open(path) as im:
            return {"width":im.width,"height":im.height,"mode":im.mode,"format":im.format}
    except Exception as exc:
        return {"parse_error":str(exc)[:500]}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--source-id",required=True)
    ap.add_argument("--root",type=Path,required=True)
    ap.add_argument("--output-dir",type=Path,required=True)
    ap.add_argument("--source-url")
    ap.add_argument("--exclude",action="append",default=[".git"])
    args=ap.parse_args()
    root=args.root.resolve()
    out=args.output_dir.resolve();out.mkdir(parents=True,exist_ok=True)
    if not root.is_dir():raise SystemExit(f"not a directory: {root}")

    manifest=out/"asset_manifest.jsonl"
    exts=Counter();classes=Counter();tops=Counter();total_bytes=0;files=0
    svg_count=0;raster_meta_count=0
    with manifest.open("w",encoding="utf-8") as mf:
        for p in sorted(x for x in root.rglob("*") if x.is_file()):
            rel=p.relative_to(root)
            if any(part in args.exclude for part in rel.parts):continue
            ext=p.suffix.lower();kind=classify(ext)
            rec={
                "asset_id":"asset-"+hashlib.sha256((args.source_id+"|"+rel.as_posix()).encode()).hexdigest()[:24],
                "source_id":args.source_id,
                "relative_path":rel.as_posix(),
                "extension":ext,
                "asset_class":kind,
                "size_bytes":p.stat().st_size,
                "sha256":sha256(p)
            }
            if ext==".svg":
                rec["svg"]=svg_meta(p);svg_count+=1
            elif ext in RASTER:
                rec["image"]=image_meta(p);raster_meta_count+=1
            mf.write(json.dumps(rec,ensure_ascii=False)+"\n")
            files+=1;total_bytes+=p.stat().st_size;exts[ext or "<none>"]+=1;classes[kind]+=1
            tops[rel.parts[0] if rel.parts else "."]+=1
    summary={
        "schema":"training-source-tree-inventory/v1",
        "processor_version":VERSION,
        "created_at":now_iso(),
        "source_id":args.source_id,
        "source_url":args.source_url,
        "root":str(root),
        "git_commit":git_head(root),
        "files":files,
        "total_bytes":total_bytes,
        "asset_classes":dict(classes.most_common()),
        "extensions":dict(exts.most_common()),
        "top_level_counts":dict(tops.most_common()),
        "svg_files_profiled":svg_count,
        "raster_files_profiled":raster_meta_count,
        "manifest":str(manifest)
    }
    (out/"source_inventory_summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
    print(json.dumps(summary,indent=2))
if __name__=="__main__":main()
