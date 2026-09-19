from __future__ import annotations
import json, re, sqlite3
from pathlib import Path
from typing import Any
from .paths import INDEX_DIR
DB_PATH=INDEX_DIR/"knowledge.sqlite"

def connect(path: Path|None=None)->sqlite3.Connection:
    target=path or DB_PATH; target.parent.mkdir(parents=True,exist_ok=True)
    db=sqlite3.connect(target); db.row_factory=sqlite3.Row
    db.executescript("""
CREATE TABLE IF NOT EXISTS sources(id TEXT PRIMARY KEY,library_id TEXT NOT NULL,title TEXT NOT NULL,source_class TEXT NOT NULL,uri TEXT,metadata TEXT NOT NULL DEFAULT '{}');
CREATE TABLE IF NOT EXISTS entities(id TEXT PRIMARY KEY,library_id TEXT NOT NULL,name TEXT NOT NULL,entity_type TEXT NOT NULL,aliases TEXT NOT NULL DEFAULT '[]',description TEXT,metadata TEXT NOT NULL DEFAULT '{}');
CREATE TABLE IF NOT EXISTS evidence_chunks(id TEXT PRIMARY KEY,library_id TEXT NOT NULL,source_id TEXT NOT NULL,ordinal INTEGER NOT NULL,text TEXT NOT NULL,text_hash TEXT NOT NULL,locator TEXT,UNIQUE(source_id,ordinal));
CREATE TABLE IF NOT EXISTS claims(id TEXT PRIMARY KEY,library_id TEXT NOT NULL,subject_id TEXT NOT NULL,predicate TEXT NOT NULL,object_json TEXT NOT NULL,qualifiers TEXT NOT NULL DEFAULT '{}',citations TEXT NOT NULL,status TEXT NOT NULL DEFAULT 'asserted');
CREATE TABLE IF NOT EXISTS contradictions(id TEXT PRIMARY KEY,library_id TEXT NOT NULL,claim_ids TEXT NOT NULL,kind TEXT NOT NULL,notes TEXT,resolution TEXT);
CREATE INDEX IF NOT EXISTS idx_entities_library_name ON entities(library_id,name);
CREATE INDEX IF NOT EXISTS idx_claims_library_subject ON claims(library_id,subject_id);
CREATE INDEX IF NOT EXISTS idx_chunks_library_source ON evidence_chunks(library_id,source_id);""")
    try: db.execute("CREATE VIRTUAL TABLE IF NOT EXISTS evidence_fts USING fts5(chunk_id UNINDEXED,library_id UNINDEXED,source_id UNINDEXED,text)")
    except sqlite3.OperationalError: pass
    return db

def upsert_source(x:dict[str,Any],path:Path|None=None)->None:
    with connect(path) as db: db.execute("INSERT OR REPLACE INTO sources VALUES(?,?,?,?,?,?)",(x["id"],x["library_id"],x["title"],x["source_class"],x.get("uri"),json.dumps(x.get("metadata",{}),ensure_ascii=False)))
def upsert_entity(x:dict[str,Any],path:Path|None=None)->None:
    with connect(path) as db: db.execute("INSERT OR REPLACE INTO entities VALUES(?,?,?,?,?,?,?)",(x["id"],x["library_id"],x["name"],x["entity_type"],json.dumps(x.get("aliases",[]),ensure_ascii=False),x.get("description"),json.dumps(x.get("metadata",{}),ensure_ascii=False)))
def upsert_evidence_chunk(x:dict[str,Any],path:Path|None=None)->None:
    with connect(path) as db:
        db.execute("INSERT OR REPLACE INTO evidence_chunks VALUES(?,?,?,?,?,?,?)",(x["id"],x["library_id"],x["source_id"],x["ordinal"],x["text"],x["text_hash"],x.get("locator")))
        try:
            db.execute("DELETE FROM evidence_fts WHERE chunk_id=?",(x["id"],)); db.execute("INSERT INTO evidence_fts VALUES(?,?,?,?)",(x["id"],x["library_id"],x["source_id"],x["text"]))
        except sqlite3.OperationalError: pass
def evidence_chunk(chunk_id:str,path:Path|None=None)->dict[str,Any]:
    with connect(path) as db:
        row=db.execute("SELECT * FROM evidence_chunks WHERE id=?",(chunk_id,)).fetchone()
        if not row: raise KeyError(f"Unknown evidence chunk: {chunk_id}")
        return dict(row)
def upsert_claim(x:dict[str,Any],path:Path|None=None)->None:
    if not x.get("citations"): raise ValueError("claims require at least one citation")
    for citation in x["citations"]:
        if not citation.get("evidence_chunk_id"): raise ValueError("claim citations require evidence_chunk_id")
        evidence_chunk(citation["evidence_chunk_id"],path)
    with connect(path) as db: db.execute("INSERT OR REPLACE INTO claims VALUES(?,?,?,?,?,?,?,?)",(x["id"],x["library_id"],x["subject_id"],x["predicate"],json.dumps(x.get("object"),ensure_ascii=False),json.dumps(x.get("qualifiers",{}),ensure_ascii=False),json.dumps(x["citations"],ensure_ascii=False),x.get("status","asserted")))

def _terms(q:str)->list[str]: return [t.lower() for t in re.findall(r"[\w'-]+",q) if len(t)>1]
def _clip(v:str|None,n:int)->str|None: return v if v is None or len(v)<=n else v[:n-1].rstrip()+"…"

def search_evidence(query:str,library_id:str="elder-scrolls",limit:int=8,char_budget:int=6000,path:Path|None=None)->dict[str,Any]:
    terms=_terms(query); ranked=[]
    with connect(path) as db:
        q=" OR ".join('"' + t.replace('"','""') + '"' for t in terms)
        if q:
            try:
                rows=db.execute("SELECT e.*,bm25(evidence_fts) rank FROM evidence_fts JOIN evidence_chunks e ON e.id=evidence_fts.chunk_id WHERE evidence_fts MATCH ? AND evidence_fts.library_id=? ORDER BY rank LIMIT ?",(q,library_id,max(limit*3,limit))).fetchall()
                ranked=[(float(r["rank"]),r) for r in rows]
            except sqlite3.OperationalError: ranked=[]
        if not ranked:
            for r in db.execute("SELECT * FROM evidence_chunks WHERE library_id=?",(library_id,)):
                overlap=sum(t in r["text"].lower() for t in terms)
                if overlap: ranked.append((-float(overlap),r))
            ranked.sort(key=lambda x:x[0])
        results=[]; used=0
        for rank,r in ranked:
            item={"chunk_id":r["id"],"source_id":r["source_id"],"locator":r["locator"],"rank":rank,"text":_clip(r["text"],1000),"evidence_hash":r["text_hash"]}
            size=len(json.dumps(item,ensure_ascii=False))
            if results and used+size>char_budget: break
            results.append(item); used+=size
            if len(results)>=limit: break
    return {"library_id":library_id,"query":query,"results":results,"approx_chars":used}

def search_lore(query:str,library_id:str="elder-scrolls",limit:int=8,char_budget:int=6000,path:Path|None=None)->dict[str,Any]:
    terms=_terms(query)
    with connect(path) as db:
        scored=[]
        for r in db.execute("SELECT * FROM entities WHERE library_id=?",(library_id,)):
            hay=" ".join([r["name"],r["description"] or "",r["aliases"]]).lower(); score=sum(3 if t in r["name"].lower() else 1 for t in terms if t in hay)
            if score: scored.append((score,r))
        scored.sort(key=lambda x:(-x[0],x[1]["name"].lower())); results=[]; used=0
        for score,r in scored[:limit]:
            item={"id":r["id"],"name":r["name"],"entity_type":r["entity_type"],"score":score,"description":_clip(r["description"],600)}; size=len(json.dumps(item,ensure_ascii=False))
            if results and used+size>char_budget: break
            results.append(item); used+=size
    return {"library_id":library_id,"query":query,"results":results,"approx_chars":used}

def get_entity(entity_id:str,library_id:str="elder-scrolls",char_budget:int=8000,path:Path|None=None)->dict[str,Any]:
    with connect(path) as db:
        e=db.execute("SELECT * FROM entities WHERE id=? AND library_id=?",(entity_id,library_id)).fetchone()
        if not e: raise KeyError(f"Unknown entity: {entity_id}")
        out={"id":e["id"],"name":e["name"],"entity_type":e["entity_type"],"description":e["description"],"claims":[]}; used=len(json.dumps(out,ensure_ascii=False))
        for c in db.execute("SELECT * FROM claims WHERE subject_id=? AND library_id=? ORDER BY id",(entity_id,library_id)):
            item={"id":c["id"],"predicate":c["predicate"],"object":json.loads(c["object_json"]),"status":c["status"],"citations":json.loads(c["citations"])}; size=len(json.dumps(item,ensure_ascii=False))
            if out["claims"] and used+size>char_budget: break
            out["claims"].append(item); used+=size
        out["approx_chars"]=used; return out

def verify_claim(claim_text:str,library_id:str="elder-scrolls",limit:int=8,path:Path|None=None)->dict[str,Any]:
    terms=set(_terms(claim_text)); matches=[]
    with connect(path) as db:
        for r in db.execute("SELECT c.*,e.name FROM claims c JOIN entities e ON e.id=c.subject_id WHERE c.library_id=?",(library_id,)):
            overlap=sum(t in f"{r['name']} {r['predicate']} {r['object_json']}".lower() for t in terms)
            if overlap: matches.append((overlap,r))
    matches.sort(key=lambda x:-x[0]); evidence=[{"claim_id":r["id"],"subject":r["name"],"predicate":r["predicate"],"object":json.loads(r["object_json"]),"citations":json.loads(r["citations"]),"overlap":s} for s,r in matches[:limit]]
    return {"query":claim_text,"evidence":evidence,"verified":bool(evidence),"note":"verified means matching stored evidence exists; it is not an independent truth judgment"}

def find_contradictions(entity_or_claim:str,library_id:str="elder-scrolls",path:Path|None=None)->dict[str,Any]:
    matches=[]
    with connect(path) as db:
        for r in db.execute("SELECT * FROM contradictions WHERE library_id=?",(library_id,)):
            ids=json.loads(r["claim_ids"]); hit=entity_or_claim==r["id"] or entity_or_claim in ids
            if not hit and ids:
                marks=",".join("?" for _ in ids); hit=bool(db.execute(f"SELECT 1 FROM claims WHERE id IN ({marks}) AND subject_id=? LIMIT 1",(*ids,entity_or_claim)).fetchone())
            if hit: matches.append({"id":r["id"],"claim_ids":ids,"kind":r["kind"],"notes":r["notes"],"resolution":r["resolution"]})
    return {"query":entity_or_claim,"contradictions":matches}
