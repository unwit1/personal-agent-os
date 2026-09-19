from pathlib import Path

from agent_os.knowledge import upsert_claim, upsert_entity, upsert_evidence_chunk, upsert_source
from agent_os.knowledge_continuity import active_continuities, search_evidence_in_continuity, verify_claim_in_continuity


def seed(tmp_path: Path):
    db = tmp_path / "continuity.sqlite"
    upsert_entity({"id":"tes:x","library_id":"elder-scrolls","name":"X","entity_type":"concept"}, db)
    for source_id, continuity, text in [
        ("base","tes-base","X is discussed in base canon."),
        ("bs","beyond-skyrim","X receives a Beyond Skyrim expansion."),
        ("vicn","vicn","X receives a VICN interpretation."),
    ]:
        upsert_source({"id":source_id,"library_id":"elder-scrolls","title":source_id,"source_class":"primary_text","metadata":{"continuity_id":continuity}}, db)
        upsert_evidence_chunk({"id":source_id+":0","library_id":"elder-scrolls","source_id":source_id,"ordinal":0,"text":text,"text_hash":source_id,"locator":"chunk:0"}, db)
    return db


def test_overlays_are_not_implicitly_composed():
    assert active_continuities(["tes-base","beyond-skyrim"]) == ["tes-base","beyond-skyrim"]


def test_evidence_excludes_unselected_overlay(tmp_path: Path):
    db = seed(tmp_path)
    result = search_evidence_in_continuity("X expansion interpretation", continuities=["tes-base","beyond-skyrim"], path=db)
    assert {x["continuity_id"] for x in result["results"]} <= {"tes-base","beyond-skyrim"}
    assert "vicn" not in {x["continuity_id"] for x in result["results"]}


def test_claim_filter_uses_qualifier_until_schema_migration(tmp_path: Path):
    db = seed(tmp_path)
    upsert_claim({"id":"c:bs","library_id":"elder-scrolls","subject_id":"tes:x","predicate":"expanded_by","object":"Beyond Skyrim","qualifiers":{"continuity_id":"beyond-skyrim"},"citations":[{"source_id":"bs","evidence_chunk_id":"bs:0"}]}, db)
    result = verify_claim_in_continuity("X expanded Beyond Skyrim", continuities=["tes-base"], path=db)
    assert not result["evidence_found"]
