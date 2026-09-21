from pathlib import Path
from agent_os.knowledge import search_evidence, upsert_evidence_chunk

def test_evidence_search_returns_relevant_chunk_with_budget(tmp_path: Path):
    db=tmp_path/"k.sqlite"
    upsert_evidence_chunk({"id":"s:0","library_id":"elder-scrolls","source_id":"s","ordinal":0,"text":"The Numidium was a gigantic brass construct associated with the Dwemer.","text_hash":"h0","locator":"chunk:0"},db)
    upsert_evidence_chunk({"id":"s:1","library_id":"elder-scrolls","source_id":"s","ordinal":1,"text":"This unrelated passage discusses crops in Cyrodiil.","text_hash":"h1","locator":"chunk:1"},db)
    result=search_evidence("Numidium Dwemer",path=db,char_budget=500)
    assert result["results"][0]["chunk_id"]=="s:0"
    assert result["approx_chars"]<=500

def test_evidence_search_has_non_fts_fallback(tmp_path: Path):
    db=tmp_path/"k.sqlite"
    upsert_evidence_chunk({"id":"s:0","library_id":"elder-scrolls","source_id":"s","ordinal":0,"text":"Lorkhan and Mundus appear here.","text_hash":"h","locator":"chunk:0"},db)
    result=search_evidence("Lorkhan Mundus",path=db)
    assert result["results"]
