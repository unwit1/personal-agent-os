from pathlib import Path

from agent_os.knowledge import find_contradictions, get_entity, search_lore, upsert_claim, upsert_entity, upsert_source, verify_claim


def test_provenance_and_budgeted_retrieval(tmp_path: Path):
    db = tmp_path / "knowledge.sqlite"
    upsert_source({"id":"uesp:lorkhan","library_id":"elder-scrolls","title":"Lorkhan","source_class":"secondary_reference"}, db)
    upsert_entity({"id":"tes:lorkhan","library_id":"elder-scrolls","name":"Lorkhan","entity_type":"deity","aliases":["Shor","Shezarr"],"description":"A major figure in Elder Scrolls creation traditions."}, db)
    upsert_claim({"id":"claim:lorkhan:creation","library_id":"elder-scrolls","subject_id":"tes:lorkhan","predicate":"associated_with","object":"creation of Mundus","citations":[{"source_id":"uesp:lorkhan","locator":"lead"}]}, db)

    found = search_lore("Lorkhan creation", path=db, char_budget=500)
    assert found["results"][0]["id"] == "tes:lorkhan"
    assert found["approx_chars"] <= 500

    entity = get_entity("tes:lorkhan", path=db)
    assert entity["claims"][0]["citations"][0]["source_id"] == "uesp:lorkhan"

    checked = verify_claim("Lorkhan creation Mundus", path=db)
    assert checked["verified"] is True


def test_claim_without_citation_is_rejected(tmp_path: Path):
    db = tmp_path / "knowledge.sqlite"
    try:
        upsert_claim({"id":"bad","library_id":"elder-scrolls","subject_id":"x","predicate":"is","object":"y","citations":[]}, db)
    except ValueError:
        pass
    else:
        raise AssertionError("citation-free claim was accepted")


def test_contradictions_can_coexist(tmp_path: Path):
    import json, sqlite3
    db = tmp_path / "knowledge.sqlite"
    upsert_entity({"id":"tes:x","library_id":"elder-scrolls","name":"X","entity_type":"concept"}, db)
    upsert_source({"id":"s1","library_id":"elder-scrolls","title":"A","source_class":"primary_text"}, db)
    upsert_claim({"id":"c1","library_id":"elder-scrolls","subject_id":"tes:x","predicate":"state","object":"A","citations":[{"source_id":"s1"}]}, db)
    from agent_os.knowledge import connect
    with connect(db) as conn:
        conn.execute("INSERT INTO contradictions VALUES (?,?,?,?,?,?)", ("k1","elder-scrolls",json.dumps(["c1","c2"]),"direct","sources disagree",None))
    assert find_contradictions("tes:x", path=db)["contradictions"][0]["id"] == "k1"
