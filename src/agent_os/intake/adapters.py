"""Built-in intake sources. Add a source with ``@adapter("name")`` yielding :class:`Item`.

Every adapter points items at a readable file: either the file the source already
keeps (a voicemail, a report) or a small Markdown rendering this module writes
into the scope's directory (one day of texts, one recording's transcript).
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Any, Iterator

from ..paths import ROOT
from . import Item, adapter

TEXT_SUFFIXES = {".md", ".txt", ".csv", ".json", ".jsonl", ".html", ".htm", ".xml", ".pdf", ".docx", ".doc", ".xlsx", ".xls",
                 ".pptx", ".rtf", ".odt", ".eml", ".msg", ".png", ".jpg", ".jpeg", ".tif", ".tiff", ".wav", ".mp3", ".m4a"}


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def _write_if_changed(path: Path, text: str) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists() or path.read_text(encoding="utf-8", errors="replace") != text:
        path.write_text(text, encoding="utf-8")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@adapter("mail")
def mail_items(conf: dict[str, Any]) -> Iterator[Item]:
    """One item per distinct message, from each scope's correspondence manifest."""
    for scope, sc in conf["scopes"].items():
        folder = Path(sc.get("correspondence_dir") or "")
        manifest = folder / "manifest.jsonl"
        if not manifest.exists():
            continue
        with manifest.open(encoding="utf-8") as handle:
            for line in handle:
                e = json.loads(line)
                yield Item(source="mail", kind="email", scope=scope, ref=e["id"], path=str(folder / e["file"]),
                           content_hash=e["export_hash"], title=e["subject"], occurred_at=e["date"], flag=e["flag"],
                           meta={"from": e["from"], "people": e.get("people", []), "thread": e.get("thread"), "screen": e.get("screen", False)})


@adapter("3cx")
def phone_items(conf: dict[str, Any]) -> Iterator[Item]:
    """The stitched phone log (intake/phone_log.py): one item per day and per call with a
    transcript or voicemail: work scope."""
    from .phone_log import build

    result = build(conf)
    folder = Path(conf["scopes"]["work"]["correspondence_dir"]).parent / "Phone Log"
    for day, path, digest, count in result["days"]:
        yield Item(source="3cx", kind="call_log", scope="work", ref=f"day:{day}", path=str(path),
                   content_hash=digest, title=f"Phone log {day} ({count} calls)", occurred_at=day, flag="work")
    for path in sorted((folder / "Calls").glob("*.md")) if (folder / "Calls").exists() else []:
        yield Item(source="3cx", kind="call", scope="work", ref=f"call:{path.stem}", path=str(path),
                   content_hash=file_hash(path), title=path.stem, occurred_at=path.stem[:10], flag="work")


@adapter("ambient")
def ambient_items(conf: dict[str, Any]) -> Iterator[Item]:
    """Ambient Capture recordings: one transcript file per capture (scope from settings; per-capture override).
    Work-scope transcripts are also linked to employees (Recordings/people.json): speakers identified by
    voice are direct links, names spoken in the conversation are mentions."""
    from ..mail.directory import PeopleMatcher, load_people

    folder_by_scope = {s: Path(sc["correspondence_dir"]).parent / "Recordings" for s, sc in conf["scopes"].items()}
    work = conf["scopes"].get("work", {})
    matcher = PeopleMatcher(load_people(Path(work["hr_datastore"]) if work.get("hr_datastore") else None))
    linked: dict[str, list[dict[str, Any]]] = {}
    source_dir = ROOT / ".agent-local" / "ambient-captures"
    for path in sorted(source_dir.glob("*.json")) if source_dir.exists() else []:
        record = json.loads(path.read_text(encoding="utf-8"))
        capture = record.get("capture") or {}
        scope = capture.get("scope") or record.get("scope") or conf.get("ambient_scope", "work")
        started = str(capture.get("started_at") or "")
        names = {p.get("speaker") or p.get("id"): p.get("person") or p.get("name") or p.get("label")
                 for p in capture.get("participants") or [] if isinstance(p, dict)}
        speakers = sorted({n for n in names.values() if n})
        lines = [f"# Recording {started}", "", f"- capture: {capture.get('capture_id')}", f"- ended: {capture.get('ended_at')}",
                 f"- speakers: {', '.join(speakers) or 'unidentified'}", ""]
        text = []
        for seg in capture.get("segments") or []:
            speaker = seg.get("speaker") or seg.get("speaker_id") or ""
            said = (seg.get("text") or "").strip()
            text.append(said)
            ms = int(seg.get("start_ms") or 0)
            who = seg.get("person") or names.get(speaker) or speaker or "?"
            lines.append(f"**{who}** [{ms // 60000}:{ms // 1000 % 60:02d}]: {said}")
        rel = f"{started[:10] or 'undated'} {started[11:16].replace(':', '')} {path.stem[:8]}.md"
        out = folder_by_scope[scope] / rel
        digest = _write_if_changed(out, "\n".join(lines) + "\n")
        if scope == "work":
            for key, link in matcher.match({"from": "; ".join(speakers)}, " ".join(text)).items():
                linked.setdefault(key, []).append({
                    "id": path.stem, "date": started, "title": f"Recording {started[:16]}", "subject": f"Recording {started[:16]}",
                    "file": rel, "role": "speaker" if link["role"] != "mention" else "mention",
                    "ambiguous": link["ambiguous"], "flag": "work", "hash": digest})
        yield Item(source="ambient", kind="transcript", scope=scope, ref=path.stem, path=str(out),
                   content_hash=digest, title=f"Recording {started}", occurred_at=started,
                   flag="personal" if scope == "personal" else "work",
                   meta={"review_status": record.get("review_status"), "speakers": speakers})
    if "work" in folder_by_scope:
        folder_by_scope["work"].mkdir(parents=True, exist_ok=True)
        _write_if_changed(folder_by_scope["work"] / "people.json", json.dumps(
            {k: {"items": v} for k, v in linked.items()}, ensure_ascii=False))


@adapter("iphone")
def text_items(conf: dict[str, Any]) -> Iterator[Item]:
    """iPhone Message Archive: one file per conversation per day (personal scope)."""
    from ..registry import get_project

    try:
        db = Path(get_project("iphone-message-archive")["path"]) / "data" / "archive" / "messages.sqlite3"
    except Exception:  # noqa: BLE001
        return
    if not db.exists():
        return
    folder = Path(conf["scopes"]["personal"]["correspondence_dir"]).parent / "Messages"
    with closing(sqlite3.connect(f"file:{db.as_posix()}?mode=ro", uri=True)) as conn:
        conn.row_factory = sqlite3.Row
        cols = {r[1] for r in conn.execute("PRAGMA table_info(messages)")}
        if not {"conversation_id", "body"} <= cols:
            return
        when = "timestamp" if "timestamp" in cols else ("sent_at" if "sent_at" in cols else None)
        if when is None:
            return
        rows = conn.execute(f"SELECT m.conversation_id, m.{when} AS ts, m.body, p.display_name, p.canonical_address, c.title "
                            "FROM messages m LEFT JOIN participants p ON p.participant_id = m.sender_id "
                            f"LEFT JOIN conversations c ON c.conversation_id = m.conversation_id ORDER BY m.conversation_id, m.{when}")
        days: dict[tuple[str, str], list[sqlite3.Row]] = {}
        for r in rows:
            days.setdefault((r["conversation_id"], str(r["ts"] or "")[:10]), []).append(r)
    for (conversation, day), msgs in days.items():
        title = msgs[0]["title"] or conversation
        lines = [f"# {title} - {day}", ""] + [f"**{m['display_name'] or m['canonical_address'] or 'me'}** "
                                               f"[{str(m['ts'])[11:16]}]: {m['body'] or ''}" for m in msgs]
        safe = "".join(ch if ch.isalnum() or ch in " -_" else "_" for ch in str(title))[:60]
        path = folder / day[:4] / f"{day} {safe} {conversation[:8]}.md"
        yield Item(source="iphone", kind="text", scope="personal", ref=f"{conversation}:{day}", path=str(path),
                   content_hash=_write_if_changed(path, "\n".join(lines) + "\n"), title=f"{title} {day}", occurred_at=day,
                   flag="personal")


@adapter("folders")
def folder_items(conf: dict[str, Any]) -> Iterator[Item]:
    """Any connected folder: every readable file in it is an item of the folder's scope and kind."""
    for spec in conf.get("folders", []):
        root = Path(spec["path"])
        if not root.exists():
            continue
        for path in sorted(p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in TEXT_SUFFIXES
                           and not p.name.startswith(("~$", "."))):
            stat = path.stat()
            yield Item(source=f"folder:{spec['name']}", kind=spec.get("kind", "document"), scope=spec["scope"],
                       ref=str(path.relative_to(root)), path=str(path), content_hash=f"{stat.st_size}:{int(stat.st_mtime)}",
                       title=path.stem, occurred_at="", flag=spec.get("flag", "work" if spec["scope"] == "work" else "personal"))
