from pathlib import Path

from agent_os.knowledge import upsert_evidence_chunk, upsert_entity, upsert_source
from agent_os.knowledge_consumer import suggest_tags


def test_kf_taxonomy_is_closed(tmp_path: Path):
    db=tmp_path/"kf.sqlite"
    upsert_source({"id":"book","library_id":"elder-scrolls","title":"Dwemer Book","source_class":"primary_text","metadata":{"continuity_id":"tes-base"}},db)
    upsert_entity({"id":"tes:dwemer","library_id":"elder-scrolls","name":"Dwemer","entity_type":"people","description":"Ancient Dwemer history."},db)
    upsert_evidence_chunk({"id":"book:0","library_id":"elder-scrolls","source_id":"book","ordinal":0,"text":"This book discusses Dwemer history and ruins.","text_hash":"h"},db)
    result=suggest_tags("Dwemer book",["History","Magic"],library_id="elder-scrolls",path=db)
    assert result["deterministic_matches"] == ["History"]
    assert set(result["deterministic_matches"]) <= set(result["allowed_tags"])
    assert result["policy"]["invent_tags"] is False


def test_kf_packet_respects_continuity(tmp_path: Path):
    db=tmp_path/"kf.sqlite"
    upsert_source({"id":"vicn","library_id":"elder-scrolls","title":"VICN","source_class":"project_overlay","metadata":{"continuity_id":"vicn"}},db)
    upsert_evidence_chunk({"id":"vicn:0","library_id":"elder-scrolls","source_id":"vicn","ordinal":0,"text":"Alchemy appears only in this VICN test evidence.","text_hash":"h"},db)
    result=suggest_tags("test evidence",["Alchemy"],continuities=["tes-base"],path=db)
    assert "Alchemy" not in result["deterministic_matches"]
