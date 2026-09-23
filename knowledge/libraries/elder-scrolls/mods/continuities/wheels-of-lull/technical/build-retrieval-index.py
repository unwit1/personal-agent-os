#!/usr/bin/env python3
"""Deterministic retrieval materializer for the Wheels of Lull continuity.

Uses only the persisted raw source-record shards plus derived speaker-resolution data.
A full rebuild requires every raw shard to be readable. If a shard is corrupt, the
builder fails closed and points to the continuity repair plan rather than silently
building a partial retrieval corpus.
"""
from __future__ import annotations
import argparse, gzip, json, math, re, zlib
from collections import Counter
from pathlib import Path

SHARD_RE = re.compile(r"source-records-(\d+)-(\d+)\.jsonl(?:\.gz)?$")
TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9'_-]{1,}")
SKIP_TEXT_KEYS = {
    "source_file","source_sha256","continuity_id","provenance_status","record_type",
    "form_id","editor_id","source_offset","raw","raw_hex","target_raw_hex","_raw_shard","_source_record_index",
}

def open_text(path: Path):
    return gzip.open(path, "rt", encoding="utf-8") if path.suffix == ".gz" else path.open("r", encoding="utf-8")

def source_shards(raw_dir: Path):
    found=[]
    for p in raw_dir.glob("source-records-*.jsonl*"):
        m=SHARD_RE.search(p.name)
        if m: found.append((int(m.group(1)), int(m.group(2)), p))
    return sorted(found)

def load_records(raw_dir: Path):
    rows=[]
    for start,end,path in source_shards(raw_dir):
        try:
            with open_text(path) as f:
                for line_no,line in enumerate(f, 0):
                    if not line.strip(): continue
                    row=json.loads(line)
                    row["_source_record_index"] = start + line_no
                    row["_raw_shard"] = path.name
                    rows.append(row)
        except (OSError, EOFError, UnicodeDecodeError, json.JSONDecodeError, zlib.error) as exc:
            raise RuntimeError(
                f"Cannot materialize retrieval corpus: unreadable raw shard {path.name}. "
                "Do not build a partial index. Regenerate the shard from the verified "
                "source ESP using analysis/repair-plan.md, then rerun this builder. "
                f"Underlying error: {exc}"
            ) from exc
    rows.sort(key=lambda r:r["_source_record_index"])
    return rows

def load_speakers(path: Path):
    if not path.exists(): return {}
    out={}
    with gzip.open(path,"rt",encoding="utf-8") as f:
        for line in f:
            if line.strip():
                r=json.loads(line); out[r["i"]]=r
    return out

def collect_strings(obj, key=None):
    vals=[]
    if isinstance(obj,str):
        if key not in SKIP_TEXT_KEYS and obj.strip(): vals.append(obj.strip())
    elif isinstance(obj,list):
        for x in obj: vals.extend(collect_strings(x,key))
    elif isinstance(obj,dict):
        for k,v in obj.items(): vals.extend(collect_strings(v,k))
    return vals

def normalize(row, speakers):
    fid=row.get("form_id")
    typ=row.get("record_type")
    strings=collect_strings(row)
    seen=set(); text=[]
    for s in strings:
        if s not in seen:
            seen.add(s); text.append(s)
    doc={
        "source_record_index":row["_source_record_index"],
        "raw_shard":row["_raw_shard"],
        "record_type":typ,
        "form_id":fid,
        "editor_id":row.get("editor_id"),
        "title":row.get("full_name") or row.get("title") or row.get("name"),
        "source_offset":row.get("source_offset"),
        "text":"\n".join(text),
    }
    sp=speakers.get(fid)
    if sp:
        doc["speaker_resolution_status"]=sp.get("s")
        doc["speakers"]=[x.get("name") for x in sp.get("p",[]) if x.get("name")]
    for key in ("quest_form_id","parent_topic_form_id","parent_location_form_id","location_form_id"):
        if row.get(key): doc[key]=row[key]
    return doc

def tokenize(text): return TOKEN_RE.findall((text or "").lower())

def build(continuity_dir: Path, output_dir: Path):
    raw=continuity_dir/"raw"
    speakers=load_speakers(continuity_dir/"dialogue"/"speaker-resolution-compact.jsonl.gz")
    rows=load_records(raw)
    docs=[normalize(r,speakers) for r in rows]
    output_dir.mkdir(parents=True,exist_ok=True)
    out_docs=output_dir/"retrieval-documents.jsonl.gz"
    with gzip.open(out_docs,"wt",encoding="utf-8",compresslevel=9) as f:
        for d in docs: f.write(json.dumps(d,ensure_ascii=False,separators=(",",":"))+"\n")
    routing={d["form_id"]:{"source_record_index":d["source_record_index"],"raw_shard":d["raw_shard"],"record_type":d["record_type"],"title":d.get("title"),"editor_id":d.get("editor_id")} for d in docs if d.get("form_id")}
    with gzip.open(output_dir/"form-routing.json.gz","wt",encoding="utf-8",compresslevel=9) as f:
        json.dump(routing,f,ensure_ascii=False,separators=(",",":"))
    df=Counter()
    for d in docs: df.update(set(tokenize(d["text"])))
    lex={"document_count":len(docs),"df":dict(sorted((k,v) for k,v in df.items() if v>=2))}
    with gzip.open(output_dir/"lexical-df.json.gz","wt",encoding="utf-8",compresslevel=9) as f:
        json.dump(lex,f,ensure_ascii=False,separators=(",",":"))
    manifest={"documents":len(docs),"first_index":docs[0]["source_record_index"] if docs else None,"last_index":docs[-1]["source_record_index"] if docs else None,"outputs":[out_docs.name,"form-routing.json.gz","lexical-df.json.gz"]}
    (output_dir/"build-result.json").write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
    return docs

def bm25(docs, query, top_k=10, k1=1.5, b=.75):
    q=tokenize(query); N=len(docs)
    toks=[tokenize(d["text"]) for d in docs]
    avg=sum(map(len,toks))/N if N else 0
    dfs=Counter()
    for ts in toks: dfs.update(set(ts))
    scored=[]
    for d,ts in zip(docs,toks):
        tf=Counter(ts); dl=len(ts); score=0.0
        for term in q:
            n=dfs.get(term,0)
            if not n: continue
            idf=math.log(1+(N-n+.5)/(n+.5))
            f=tf.get(term,0)
            if f: score += idf*(f*(k1+1))/(f+k1*(1-b+b*(dl/avg if avg else 0)))
        if score>0: scored.append((score,d))
    scored.sort(key=lambda x:(-x[0],x[1]["source_record_index"]))
    return scored[:top_k]

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("continuity_dir", type=Path)
    ap.add_argument("--output-dir", type=Path)
    ap.add_argument("--search")
    ap.add_argument("--top-k",type=int,default=10)
    args=ap.parse_args()
    out=args.output_dir or args.continuity_dir/".generated-retrieval"
    docs=build(args.continuity_dir,out)
    if args.search:
        for score,d in bm25(docs,args.search,args.top_k):
            print(json.dumps({"score":round(score,6),"source_record_index":d["source_record_index"],"record_type":d["record_type"],"form_id":d["form_id"],"title":d.get("title"),"speakers":d.get("speakers",[]),"snippet":d["text"][:300]},ensure_ascii=False))

if __name__=="__main__": main()
