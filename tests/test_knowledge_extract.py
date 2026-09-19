from pathlib import Path

from agent_os.knowledge import upsert_evidence_chunk, upsert_entity, upsert_source
from agent_os.knowledge_extract import accept_claim, claim_candidate


def seeded(tmp_path: Path):
    db = tmp_path / "knowledge.sqlite"
    upsert_source({"id":"s1","library_id":"elder-scrolls","title":"Source","source_class":"primary_text"}, db)
    upsert_entity({"id":"tes:x","library_id":"elder-scrolls","name":"X","entity_type":"concept"}, db)
    upsert_evidence_chunk({"id":"s1:chunk:0","library_id":"elder-scrolls","source_id":"s1","ordinal":0,"text":"X is described as Y.","text_hash":"abc","locator":"chunk:0"}, db)
    return db


def test_candidate_is_bound_to_exact_evidence(tmp_path: Path):
    db = seeded(tmp_path)
    candidate = claim_candidate("tes:x","described_as","Y","s1:chunk:0",path=db)
    assert candidate["citations"][0]["evidence_chunk_id"] == "s1:chunk:0"
    assert candidate["citations"][0]["evidence_hash"] == "abc"
    assert accept_claim(candidate, db)["id"].startswith("claim:")


def test_missing_evidence_cannot_be_promoted(tmp_path: Path):
    db = seeded(tmp_path)
    try:
        claim_candidate("tes:x","described_as","Y","missing",path=db)
    except KeyError:
        pass
    else:
        raise AssertionError("candidate without stored evidence was accepted")
