from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from .knowledge import upsert_entity, upsert_source
from .paths import INDEX_DIR, ROOT

UESP_HOSTS = {"en.uesp.net", "www.uesp.net"}
LEDGER = ROOT / "knowledge" / "elder-scrolls" / "crawl-ledger.json"
CACHE = INDEX_DIR / "knowledge-cache" / "elder-scrolls"


class _TextParser(HTMLParser):
    SKIP = {"script", "style", "nav"}
    def __init__(self) -> None:
        super().__init__()
        self.depth = 0
        self.parts: list[str] = []
        self.title = ""
        self._in_title = False
    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP: self.depth += 1
        if tag == "title": self._in_title = True
    def handle_endtag(self, tag):
        if tag in self.SKIP and self.depth: self.depth -= 1
        if tag == "title": self._in_title = False
    def handle_data(self, data):
        if self.depth: return
        value = " ".join(data.split())
        if not value: return
        if self._in_title: self.title += (" " if self.title else "") + value
        self.parts.append(value)


@dataclass(frozen=True)
class PilotPage:
    id: str
    url: str
    entity_type: str


def _safe_uesp(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname not in UESP_HOSTS:
        raise ValueError("UESP ingestion only permits HTTPS pages on the configured UESP hosts")


def fetch_uesp(url: str, timeout: int = 20) -> str:
    _safe_uesp(url)
    request = Request(url, headers={"User-Agent": "PersonalAgentOS-LorePilot/0.1"})
    with urlopen(request, timeout=timeout) as response:
        content_type = response.headers.get("Content-Type", "")
        if "text/html" not in content_type:
            raise ValueError(f"expected HTML, got {content_type}")
        return response.read().decode("utf-8", errors="replace")


def normalize_html(html: str) -> tuple[str, str]:
    parser = _TextParser(); parser.feed(html)
    text = re.sub(r"\s+", " ", " ".join(parser.parts)).strip()
    title = re.sub(r"\s+- UESPWiki.*$", "", parser.title).strip()
    return title, text


def ingest_pilot_page(page: PilotPage, html: str | None = None, db_path: Path | None = None) -> dict:
    _safe_uesp(page.url)
    raw = html if html is not None else fetch_uesp(page.url)
    title, text = normalize_html(raw)
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    CACHE.mkdir(parents=True, exist_ok=True)
    (CACHE / f"{page.id}.txt").write_text(text, encoding="utf-8")
    source_id = f"uesp:{page.id}"
    entity_id = f"tes:{page.id}"
    upsert_source({"id": source_id, "library_id": "elder-scrolls", "title": title or page.id, "source_class": "secondary_reference", "uri": page.url, "metadata": {"sha256": digest}}, db_path)
    upsert_entity({"id": entity_id, "library_id": "elder-scrolls", "name": title or page.id, "entity_type": page.entity_type, "aliases": [], "description": text[:1200], "metadata": {"source_id": source_id}}, db_path)
    return {"page_id": page.id, "source_id": source_id, "entity_id": entity_id, "title": title, "sha256": digest, "characters": len(text)}


def pilot_manifest() -> list[PilotPage]:
    return [
        PilotPage("lorkhan", "https://en.uesp.net/wiki/Lore:Lorkhan", "deity"),
        PilotPage("vivec", "https://en.uesp.net/wiki/Lore:Vivec", "person"),
        PilotPage("dwemer", "https://en.uesp.net/wiki/Lore:Dwemer", "people"),
        PilotPage("red-mountain", "https://en.uesp.net/wiki/Lore:Red_Mountain", "place"),
        PilotPage("tribunal", "https://en.uesp.net/wiki/Lore:Tribunal", "faction"),
        PilotPage("numidium", "https://en.uesp.net/wiki/Lore:Numidium", "artifact"),
        PilotPage("battle-of-red-mountain", "https://en.uesp.net/wiki/Lore:Battle_of_Red_Mountain", "event"),
        PilotPage("36-lessons", "https://en.uesp.net/wiki/Lore:36_Lessons_of_Vivec", "text"),
    ]


def update_ledger(results: Iterable[dict]) -> None:
    ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
    by_id = {entry["id"]: entry for entry in ledger.get("entries", [])}
    for result in results:
        by_id[result["page_id"]] = {"id": result["page_id"], "status": "fetched", "sha256": result["sha256"], "characters": result["characters"]}
    ledger["entries"] = sorted(by_id.values(), key=lambda x: x["id"])
    ledger["status"] = "pilot_fetched"
    LEDGER.write_text(json.dumps(ledger, indent=2) + "\n", encoding="utf-8")


def run_pilot(db_path: Path | None = None) -> dict:
    results = [ingest_pilot_page(page, db_path=db_path) for page in pilot_manifest()]
    update_ledger(results)
    return {"pages": len(results), "results": results}
