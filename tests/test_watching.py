from agent_os.watching import add_target, list_targets
import agent_os.watching as watching


def test_watch_target_deduplicates_and_merges(tmp_path, monkeypatch):
    monkeypatch.setattr(watching, "WATCH_DIR", tmp_path)
    monkeypatch.setattr(watching, "WATCH_INDEX", tmp_path / "index.json")
    first = add_target({"source_id": "youtube:creator:abc", "title": "Creator", "target_type": "creator", "search_queries": ["Creator new video"]})
    second = add_target({"source_id": "youtube:creator:abc", "title": "Creator", "target_type": "creator", "related_topics": ["skyrim"]})
    assert first["watch_id"] == second["watch_id"]
    targets = list_targets()
    assert len(targets) == 1
    assert targets[0]["search_queries"] == ["Creator new video"]
    assert targets[0]["related_topics"] == ["skyrim"]
