from pathlib import Path

from agent_os.knowledge import search_lore
from agent_os.knowledge_ingest import PilotPage, ingest_pilot_page, normalize_html


HTML = """<html><head><title>Lorkhan - UESPWiki</title><style>.x{}</style></head>
<body><nav>menu noise</nav><h1>Lorkhan</h1><p>Lorkhan is associated with the creation of Mundus.</p>
<script>bad()</script></body></html>"""


def test_normalize_html_removes_script_and_nav():
    title, text = normalize_html(HTML)
    assert title == "Lorkhan"
    assert "creation of Mundus" in text
    assert "bad()" not in text
    assert "menu noise" not in text


def test_pilot_ingest_is_searchable(tmp_path: Path, monkeypatch):
    db = tmp_path / "knowledge.sqlite"
    cache = tmp_path / "cache"
    monkeypatch.setattr("agent_os.knowledge_ingest.CACHE", cache)
    page = PilotPage("lorkhan", "https://en.uesp.net/wiki/Lore:Lorkhan", "deity")
    result = ingest_pilot_page(page, HTML, db)
    assert result["entity_id"] == "tes:lorkhan"
    found = search_lore("Lorkhan Mundus", path=db)
    assert found["results"][0]["id"] == "tes:lorkhan"


def test_non_uesp_host_is_rejected(tmp_path: Path):
    page = PilotPage("bad", "https://example.com/wiki/Lore:Lorkhan", "deity")
    try:
        ingest_pilot_page(page, HTML, tmp_path / "db.sqlite")
    except ValueError:
        pass
    else:
        raise AssertionError("non-UESP host was accepted")
