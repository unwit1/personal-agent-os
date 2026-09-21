from pathlib import Path
import json

from agent_os.knowledge import upsert_evidence_chunk, upsert_entity, upsert_source
from agent_os.knowledge_consumer import semantic_mapping_request, suggest_tags


def seed(db):
    upsert_source({"id":"book","library_id":"elder-scrolls","title":"Book","source_class":"primary_text","metadata":{"continuity_id":"tes-base"}},db)
    upsert_entity({"id":"tes:x","library_id":"elder-scrolls","name":"Dwemer","entity_type":"people","description":"Ancient history."},db)
    upsert_evidence_chunk({"id":"book:0","library_id":"elder-scrolls","source_id":"book","ordinal":0,"text":"An account of ancient history.","text_hash":"h"},db)


def test_confirmed_mapping_skips_retrieval(tmp_path: Path):
    mapping=tmp_path/"mappings.json"
    mapping.write_text(json.dumps({"mappings":[{"item_id":"book:1","library_id":"elder-scrolls","continuities":["tes-base"],"tags":["History","NotAllowed"]}]}))
    result=suggest_tags("Book",["History","Magic"],item_id="book:1",mapping_path=mapping,path=tmp_path/"unused.sqlite")
    assert result["cache_hit"] is True
    assert result["confirmed_tags"] == ["History"]
    assert result["lore_packet"] is None
    assert semantic_mapping_request(result) is None


def test_semantic_request_is_closed_and_small(tmp_path: Path):
    db=tmp_path/"kf.sqlite"; seed(db)
    result=suggest_tags("Book",["Magic","Religion"],item_id="book:2",path=db,mapping_path=tmp_path/"none.json",char_budget=1000)
    request=semantic_mapping_request(result)
    assert request is not None
    assert request["allowed_tags"] == ["Magic","Religion"]
    assert "instruction" in request
    assert "lore_packet" not in request
