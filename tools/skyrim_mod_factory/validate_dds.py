#!/usr/bin/env python3
"""Deterministic DDS structural validator for Skyrim asset pipelines.

Trust boundary:
- Microsoft DDS header/layout and DXGI format definitions;
- Skyrim-specific compatibility policy is deliberately narrow and explicit.

This validator does not decode pixels. It proves header integrity, format identity,
known block-compressed payload size, mip-chain policy, and a small set of
game-generation compatibility invariants.
"""
from __future__ import annotations

import argparse
import json
import math
import struct
from pathlib import Path
from typing import Any

MAGIC=b"DDS "
DDPF_FOURCC=0x4
DDSD_DEPTH=0x800000
DDSCAPS2_CUBEMAP=0x200
DX10_CUBE=0x4

DXGI={
    28:"R8G8B8A8_UNORM",29:"R8G8B8A8_UNORM_SRGB",
    70:"BC1_TYPELESS",71:"BC1_UNORM",72:"BC1_UNORM_SRGB",
    73:"BC2_TYPELESS",74:"BC2_UNORM",75:"BC2_UNORM_SRGB",
    76:"BC3_TYPELESS",77:"BC3_UNORM",78:"BC3_UNORM_SRGB",
    79:"BC4_TYPELESS",80:"BC4_UNORM",81:"BC4_SNORM",
    82:"BC5_TYPELESS",83:"BC5_UNORM",84:"BC5_SNORM",
    94:"BC6H_TYPELESS",95:"BC6H_UF16",96:"BC6H_SF16",
    97:"BC7_TYPELESS",98:"BC7_UNORM",99:"BC7_UNORM_SRGB",
}
BLOCK_BYTES={
    "DXT1":8,"BC4U":8,"BC4S":8,"ATI1":8,
    "DXT3":16,"DXT5":16,"ATI2":16,"BC5U":16,"BC5S":16,
    "BC1_TYPELESS":8,"BC1_UNORM":8,"BC1_UNORM_SRGB":8,
    "BC2_TYPELESS":16,"BC2_UNORM":16,"BC2_UNORM_SRGB":16,
    "BC3_TYPELESS":16,"BC3_UNORM":16,"BC3_UNORM_SRGB":16,
    "BC4_TYPELESS":8,"BC4_UNORM":8,"BC4_SNORM":8,
    "BC5_TYPELESS":16,"BC5_UNORM":16,"BC5_SNORM":16,
    "BC6H_TYPELESS":16,"BC6H_UF16":16,"BC6H_SF16":16,
    "BC7_TYPELESS":16,"BC7_UNORM":16,"BC7_UNORM_SRGB":16,
}

def u32(data:bytes,offset:int)->int:
    return struct.unpack_from("<I",data,offset)[0]

def fourcc_text(value:int)->str:
    raw=struct.pack("<I",value)
    try:
        return raw.decode("ascii")
    except UnicodeDecodeError:
        return "0x"+raw.hex().upper()

def full_mip_count(width:int,height:int,depth:int=1)->int:
    return int(math.floor(math.log2(max(width,height,depth))))+1

def block_payload_size(width:int,height:int,mips:int,block_bytes:int,surfaces:int=1)->int:
    total=0
    w,h=max(1,width),max(1,height)
    for _ in range(max(1,mips)):
        total+=max(1,(w+3)//4)*max(1,(h+3)//4)*block_bytes
        w=max(1,w//2); h=max(1,h//2)
    return total*surfaces

def finding(rule_id:str,severity:str,message:str,**evidence:Any)->dict[str,Any]:
    row={"rule_id":rule_id,"severity":severity,"message":message}
    if evidence:
        row["evidence"]=evidence
    return row

def analyze_bytes(
    data:bytes,
    *,
    path:str="<memory>",
    game:str="sse",
    require_full_mips:bool=False,
)->dict[str,Any]:
    findings=[]
    issues=[]
    scope={"path":path,"game":game,"size_bytes":len(data)}

    if len(data)<128:
        findings.append(finding("DDS-HEADER","BLOCKER","DDS is shorter than the 128-byte base header",actual_size=len(data)))
        return report(scope,findings,issues,{"header_parsed":False})

    if data[:4]!=MAGIC:
        findings.append(finding("DDS-MAGIC","BLOCKER","DDS magic is not 'DDS '",actual=data[:4].hex()))
    header_size=u32(data,4)
    pf_size=u32(data,76)
    if header_size!=124:
        findings.append(finding("DDS-HEADER","BLOCKER","DDS_HEADER size must be 124",actual=header_size))
    if pf_size!=32:
        findings.append(finding("DDS-PIXELFORMAT","BLOCKER","DDS_PIXELFORMAT size must be 32",actual=pf_size))

    flags=u32(data,8)
    height=u32(data,12)
    width=u32(data,16)
    depth=u32(data,24) or 1
    mip_raw=u32(data,28)
    mip_count=mip_raw or 1
    pf_flags=u32(data,80)
    fourcc=fourcc_text(u32(data,84))
    caps2=u32(data,112)

    scope.update({
        "width":width,"height":height,"depth":depth,
        "mip_count":mip_count,"fourcc":fourcc,
    })
    if width==0 or height==0:
        findings.append(finding("DDS-DIMENSIONS","BLOCKER","DDS width and height must be non-zero",width=width,height=height))

    data_offset=128
    dx10=None
    format_name=None
    surfaces=6 if (caps2 & DDSCAPS2_CUBEMAP) else 1
    is_cube=bool(caps2 & DDSCAPS2_CUBEMAP)

    if pf_flags & DDPF_FOURCC:
        if fourcc=="DX10":
            if len(data)<148:
                findings.append(finding("DDS-DX10","BLOCKER","DX10 FourCC requires the 20-byte DDS_HEADER_DXT10 extension",actual_size=len(data)))
            else:
                dxgi=u32(data,128)
                dimension=u32(data,132)
                misc_flag=u32(data,136)
                array_size=u32(data,140)
                misc_flags2=u32(data,144)
                data_offset=148
                format_name=DXGI.get(dxgi)
                is_cube=bool(misc_flag & DX10_CUBE)
                surfaces=array_size*(6 if is_cube else 1)
                dx10={
                    "dxgi_format":dxgi,
                    "format_name":format_name,
                    "resource_dimension":dimension,
                    "misc_flag":misc_flag,
                    "array_size":array_size,
                    "misc_flags2":misc_flags2,
                }
                scope["dx10"]=dx10
                if array_size==0:
                    findings.append(finding("DDS-DX10","BLOCKER","DX10 arraySize must be non-zero"))
                if dimension not in {2,3,4}:
                    findings.append(finding("DDS-DX10","BLOCKER","DX10 resourceDimension must be Texture1D/2D/3D",actual=dimension))
                if dimension==4:
                    if not (flags & DDSD_DEPTH):
                        findings.append(finding("DDS-DX10","BLOCKER","Texture3D requires DDSD_DEPTH"))
                    if array_size!=1:
                        findings.append(finding("DDS-DX10","BLOCKER","Texture3D arraySize must be 1",actual=array_size))
                if format_name is None:
                    findings.append(finding("DDS-FORMAT","WARNING","DXGI format is not in the validator's known Skyrim-relevant format table",dxgi_format=dxgi))
        else:
            format_name=fourcc
    else:
        format_name="UNCOMPRESSED"

    scope["format"]=format_name
    scope["is_cube"]=is_cube

    expected_mips=full_mip_count(width,height,depth) if width and height else None
    scope["full_mip_count"]=expected_mips
    if expected_mips and mip_count>expected_mips:
        findings.append(finding("DDS-MIP-CHAIN","ERROR","DDS declares more mip levels than dimensions permit",declared=mip_count,maximum=expected_mips))
    elif require_full_mips and expected_mips and mip_count!=expected_mips:
        findings.append(finding("DDS-MIP-CHAIN","ERROR","full mip chain required by policy",declared=mip_count,expected=expected_mips))

    if game=="le" and format_name and format_name.startswith("BC7"):
        findings.append(finding("DDS-GAME-FORMAT","ERROR","BC7 is not compatible with the Skyrim LE texture policy",format=format_name))

    block_bytes=BLOCK_BYTES.get(format_name or "")
    payload_size=max(0,len(data)-data_offset)
    coverage={
        "header_parsed":True,
        "pixel_decode_performed":False,
        "payload_size_checked":False,
        "data_offset":data_offset,
        "payload_size":payload_size,
        "source_basis":[
            "Microsoft DDS programming guide/header definitions",
            "Microsoft DXGI_FORMAT enumeration",
            "Skyrim LE/SSE BC7 compatibility policy",
        ],
    }
    if block_bytes and width and height and not (dx10 and dx10["resource_dimension"]==4):
        expected=block_payload_size(width,height,mip_count,block_bytes,max(1,surfaces))
        coverage["payload_size_checked"]=True
        coverage["minimum_expected_payload"]=expected
        if payload_size<expected:
            findings.append(finding("DDS-PAYLOAD","BLOCKER","block-compressed DDS payload is truncated",actual=payload_size,minimum_expected=expected))
    elif format_name=="UNCOMPRESSED":
        issues.append("uncompressed payload byte-size validation is not implemented in this baseline")
    elif dx10 and dx10["resource_dimension"]==4:
        issues.append("Texture3D payload byte-size validation is not implemented in this baseline")
    elif not block_bytes:
        issues.append("payload byte-size validation unavailable for this pixel format")

    return report(scope,findings,issues,coverage)

def report(scope:dict[str,Any],findings:list[dict[str,Any]],issues:list[str],coverage:dict[str,Any])->dict[str,Any]:
    if any(x["severity"] in {"BLOCKER","ERROR"} for x in findings):
        status="fail"
    elif any(x["severity"]=="WARNING" for x in findings) or issues:
        status="needs-review"
    else:
        status="pass"
    return {
        "schema_version":"skyrim-static-invariant-report-v1",
        "analyzer":"dds-structural-v1",
        "status":status,
        "scope":scope,
        "findings":findings,
        "coverage":coverage,
        "issues":issues,
    }

def main()->None:
    ap=argparse.ArgumentParser()
    ap.add_argument("dds",type=Path)
    ap.add_argument("--game",choices=["le","sse","vr"],default="sse")
    ap.add_argument("--require-full-mips",action="store_true")
    ap.add_argument("--output",type=Path)
    args=ap.parse_args()
    result=analyze_bytes(
        args.dds.read_bytes(),
        path=str(args.dds),
        game=args.game,
        require_full_mips=args.require_full_mips,
    )
    text=json.dumps(result,indent=2)+"\n"
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(text,encoding="utf-8")
    else:
        print(text,end="")
    raise SystemExit(0 if result["status"]=="pass" else 2 if result["status"]=="fail" else 3)

if __name__=="__main__":
    main()
