from pathlib import Path

from agent_os.knowledge import upsert_evidence_chunk, upsert_entity
from agent_os.knowledge_context import context, plan


def seed(tmp_path: Path):
    db=tmp_path/"k.sqlite"
    upsert_entity({"id":"tes:numidium","library_id":"elder-scrolls","name":"Numidium","entity_type":"artifact","description":"A brass construct associated with the Dwemer."},db)
    upsert_evidence_chunk({"id":"s:0","library_id":"elder-scrolls","source_id":"s","ordinal":0,"text":"Accounts discuss the Numidium and its Dwemer origins.","text_hash":"h","locator":"chunk:0"},db)
    return db


def test_simple_lookup_uses_only_entity_search():
    assert plan("Numidium")["calls"]==["search_lore"]


def test_source_question_routes_to_evidence():
    assert plan("What sources discuss Numidium?")["mode"]=="evidence"


def test_claim_without_extracted_claims_falls_back_to_evidence(tmp_path: Path):
    db=seed(tmp_path)
    packet=context("Was Numidium created by the Dwemer?",path=db,char_budget=1000)
    assert packet["route"]["mode"]=="claim"
    assert packet["route"]["fallback"]=="search_evidence"
    assert packet["evidence"]


def test_evidence_packet_stays_compact(tmp_path: Path):
    db=seed(tmp_path)
    packet=context("What evidence discusses Numidium?",path=db,char_budget=1000)
    assert packet["evidence"]
    assert packet["approx_chars"] < 1800
