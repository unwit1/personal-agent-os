"""One phone log stitched from every source Agent OS has (work scope).

Sources, all read-only:

* calls the PBX reported to Ambient Capture (`call_sessions` in its database): time,
  direction, number or extension;
* call transcripts Ambient Capture built (`call-<session>.json` imported under
  .agent-local/ambient-captures): the microphone's (and, when recorded, the phone's) side
  of the conversation, with speakers named by voice;
* 3CX "New missed call from ..." emails in the work mail index: caller-ID names for
  outside numbers, names for internal extensions, ring time and duration;
* voicemails the browser bridge saved (.agent-os/intake/3cx/voicemails);
* the HR datastore's phone numbers (employees).

A missed-call email within 90 s of a logged call from the same number is the same call.
Every call gets the best caller name available (roster > caller ID > extension directory)
and, when the caller is an employee, a link for their personnel record.

Output (work Recordings' sibling folder "Phone Log"):
    Phone Log/<YYYY-MM-DD>.md            the day's calls, newest last, transcripts inline
    Phone Log/Calls/<date time> - <who>.md   one file per call that has a transcript or voicemail
    Phone Log/people.json                employee -> calls (for dossiers / personnel copies)
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
from collections import defaultdict
from contextlib import closing
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from ..paths import INDEX_DIR, ROOT

AMBIENT_DB = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / "AgentOSAmbientCapture" / "ambient.sqlite3"
CALL_DOCS = ROOT / ".agent-local" / "ambient-captures"
MAIL_DB = ROOT / ".agent-local" / "mail" / "work" / "index.sqlite3"
VOICEMAILS = INDEX_DIR / "intake" / "3cx" / "voicemails"
_EXT = re.compile(r"^New missed call from (.+?) Ext\.(\d+)\s*$")
_OUTSIDE = re.compile(r"^New missed call from (.+?):(.+?) (\+?\d{7,})\s*$")
_RINGING = re.compile(r'Ringing:\s*"?(\d+):(\d+)')
SAME_CALL = timedelta(seconds=90)


def digits(number: str | None) -> str:
    d = re.sub(r"\D", "", number or "")
    return d[-10:] if len(d) >= 10 else d


def _at(value: str | None) -> datetime | None:
    try:
        when = datetime.fromisoformat(value) if value else None
    except ValueError:
        return None
    return when.astimezone(timezone.utc) if when else None


def _ro(path: Path):
    return closing(sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True))


def missed_call_emails(mail_db: Path = MAIL_DB) -> list[dict]:
    if not mail_db.exists():
        return []
    out = []
    with _ro(mail_db) as conn:
        for subject, date, body in conn.execute(
                "SELECT subject, date_utc, body FROM mail_messages WHERE subject LIKE 'New missed call from%'"):
            ring = _RINGING.search(body or "")
            entry = {"at": _at(date), "ring_s": int(ring.group(1)) * 60 + int(ring.group(2)) if ring else None}
            if m := _EXT.match(subject or ""):
                entry.update(name=m.group(1).strip(), number=m.group(2), internal=True)
            elif m := _OUTSIDE.match(subject or ""):
                name = m.group(1).strip()
                entry.update(name=None if name.upper() in ("WIRELESS CALLER", "UNKNOWN", "UNAVAILABLE") else name.title(),
                             number=m.group(3), line=m.group(2).strip(), internal=False)
            else:
                continue
            if entry["at"]:
                out.append(entry)
    return out


def phonebook(emails: list[dict], roster: list[dict]) -> dict[str, dict]:
    """number/extension -> {"name", "source", "person_key"?}."""
    book: dict[str, dict] = {}
    for e in emails:
        if e.get("name"):
            book.setdefault(e["number"] if e["internal"] else digits(e["number"]),
                            {"name": e["name"], "source": "extension" if e["internal"] else "caller ID"})
    for person in roster:
        for number in person["phones"]:
            book[digits(number)] = {"name": person["name"], "source": "HR roster", "person_key": person["key"]}
    return book


def roster(datastore: Path | None) -> list[dict]:
    if not datastore or not Path(datastore).exists():
        return []
    rec: dict[str, dict] = defaultdict(dict)
    with _ro(Path(datastore)) as conn:
        for key, field, value in conn.execute(
                "SELECT person_key, field, value FROM current WHERE field IN "
                "('first_name','last_name','home_phone','work_phone')"):
            rec[key][field] = value or ""
    return [{"key": k, "name": f"{r.get('first_name', '').split(' ')[0]} {r.get('last_name', '')}".strip(),
             "phones": [r[f] for f in ("home_phone", "work_phone") if digits(r.get(f))]}
            for k, r in rec.items()]


DASHBOARD = Path.home() / "Documents" / "HR Automation Local" / "Job Applicant Dashboard"
_PHONE_LINE = re.compile(r"Phone[^:\n]*:\s*([()\d .+-]{10,20})")


def _norm_name(name: str) -> str:
    return " ".join(sorted(re.sub(r"[^a-z ]", " ", (name or "").lower()).split()))


def applicants(dashboard: Path = DASHBOARD) -> list[dict]:
    """Applicants from the Applicant Dashboard, with the phone number read from their
    application PDF (cached by file and modification time)."""
    db = dashboard / "dashboard.db"
    if not db.exists():
        return []
    try:
        settings = json.loads((dashboard / "Config" / "paths_settings.json").read_text(encoding="utf-8"))
        apps = Path(settings["applications_dir"])
    except (OSError, ValueError, KeyError):
        return []
    cache_path = ROOT / ".agent-local" / "intake" / "applicant-phones.json"
    cache = json.loads(cache_path.read_text(encoding="utf-8")) if cache_path.exists() else {}
    out = []
    with _ro(db) as conn:
        rows = conn.execute("SELECT applicant_key, name, status, position, pdf_path FROM applicants").fetchall()
    for key, name, status, position, pdf in rows:
        phone = ""
        path = apps / (pdf or "")
        if pdf and path.is_file():
            stamp = f"{path}|{path.stat().st_mtime:.0f}"
            if stamp not in cache:
                try:
                    import pymupdf

                    with pymupdf.open(path) as doc:
                        m = _PHONE_LINE.search(doc[0].get_text())
                    cache[stamp] = m.group(1).strip() if m else ""
                except Exception:  # noqa: BLE001 - unreadable PDF: no number
                    cache[stamp] = ""
            phone = cache[stamp]
        out.append({"key": key, "name": " ".join((name or "").split()), "status": status,
                    "position": position, "phone": phone})
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json.dumps(cache), encoding="utf-8")
    return out


def build(conf: dict[str, Any]) -> dict[str, Any]:
    from ..mail.directory import PeopleMatcher, load_people

    work = conf["scopes"]["work"]
    out_dir = Path(work["correspondence_dir"]).parent / "Phone Log"
    datastore = Path(work["hr_datastore"]) if work.get("hr_datastore") else None
    emails = missed_call_emails()
    book = phonebook(emails, roster(datastore))
    pool = applicants()
    by_name = {}
    for a in pool:
        by_name.setdefault(_norm_name(a["name"]), a)
        if digits(a["phone"]) and digits(a["phone"]) not in book:   # employees take precedence
            book[digits(a["phone"])] = {"name": a["name"], "source": f"applicant ({a['status']})",
                                        "applicant": a}
    matcher = PeopleMatcher(load_people(datastore))

    calls: list[dict] = []
    if AMBIENT_DB.exists():
        with _ro(AMBIENT_DB) as conn:
            conn.row_factory = sqlite3.Row
            for s in conn.execute("SELECT * FROM call_sessions"):
                at = _at(s["ringing_at"] or s["dialing_at"] or s["created_at"])
                if at is None:
                    continue
                calls.append({"id": s["session_id"], "at": at, "direction": s["direction"],
                              "number": s["remote_number"] or "", "name": s["remote_name"],
                              "status": s["status"], "inferred": s["source_system"] == "transcript",
                              "confidence": s["reconciliation_confidence"]})
    used = set()
    for call in calls:
        for i, e in enumerate(emails):
            if i in used or abs(e["at"] - call["at"]) > SAME_CALL:
                continue
            if not call["number"] or digits(call["number"]) == digits(e["number"]) or call["number"] == e["number"]:
                call["missed"], call["ring_s"] = True, e["ring_s"]
                call["name"] = call["name"] or e.get("name")
                call["number"] = call["number"] or e["number"]
                used.add(i)
                break
    for i, e in enumerate(emails):
        if i not in used:
            calls.append({"id": f"missed-{e['at']:%Y%m%dT%H%M%S}-{digits(e['number'])}", "at": e["at"],
                          "direction": "inbound", "number": e["number"], "name": e.get("name"),
                          "status": "missed", "missed": True, "ring_s": e["ring_s"], "inferred": False})
    for call in calls:
        key = call["number"] if len(digits(call["number"])) < 7 else digits(call["number"])
        entry = book.get(key) or {}
        call["who"] = entry.get("name") or call.get("name") or (f"Ext. {call['number']}" if call["number"] and len(key) < 7 else call["number"] or "Unknown caller")
        call["who_source"] = entry.get("source") or ("call log" if call.get("name") else "")
        call["person_key"] = entry.get("person_key")
        applicant = entry.get("applicant") or by_name.get(_norm_name(call["who"]))
        if applicant and not call["person_key"]:
            call["applicant"] = applicant
            call["who"] = applicant["name"]
            call["who_source"] = entry.get("source") or f"applicant ({applicant['status']}, name match)"
        doc = CALL_DOCS / f"call-{call['id']}.json"
        if doc.exists():
            capture = json.loads(doc.read_text(encoding="utf-8")).get("capture") or {}
            call["transcript"] = [(seg.get("at", "")[11:19], seg.get("display") or seg.get("person") or "?", seg.get("text", ""))
                                  for seg in capture.get("segments") or []]
    for vm in sorted(VOICEMAILS.glob("*.json")) if VOICEMAILS.exists() else []:
        meta = json.loads(vm.read_text(encoding="utf-8"))
        at = _at(meta.get("received_at") or meta.get("time") or meta.get("date"))
        if at:
            calls.append({"id": f"voicemail-{vm.stem}", "at": at, "direction": "inbound",
                          "number": meta.get("caller_number") or "", "who": meta.get("caller_name") or meta.get("from") or "Voicemail",
                          "who_source": "voicemail", "status": "voicemail", "inferred": False,
                          "transcript": [("", "Voicemail", meta.get("transcription") or "")],
                          "audio": str(vm.with_suffix(".wav")) if vm.with_suffix(".wav").exists() else None})
    return _write(out_dir, sorted(calls, key=lambda c: c["at"]), matcher)


def _describe(call: dict) -> str:
    if call.get("status") == "voicemail":
        return "voicemail"
    if call.get("missed"):
        return f"missed (rang {call['ring_s']}s)" if call.get("ring_s") is not None else "missed"
    if call.get("transcript"):
        return "inferred from conversation" if call.get("inferred") else "answered (conversation recorded)"
    return "logged; no recording"


def _safe(text: str) -> str:
    return re.sub(r'[<>:"/\\|?*]+', " ", text).strip()[:60] or "caller"


def _write(out_dir: Path, calls: list[dict], matcher) -> dict[str, Any]:
    from .adapters import _write_if_changed

    days: dict[str, list[dict]] = defaultdict(list)
    people: dict[str, list[dict]] = defaultdict(list)
    applicant_calls: dict[str, list[dict]] = defaultdict(list)
    for call in calls:
        local = call["at"].astimezone()
        call["local"] = local
        days[f"{local:%Y-%m-%d}"].append(call)
        if call.get("transcript"):
            rel = f"Calls/{local:%Y-%m-%d %H%M} - {_safe(call['who'])} [{call['id'][:8]}].md"
            lines = [f"# Call {local:%Y-%m-%d %H:%M} - {call['who']}", "",
                     f"- direction: {call['direction']}", f"- number: {call['number'] or 'unknown'}",
                     f"- caller name from: {call['who_source'] or 'unknown'}", f"- status: {_describe(call)}", ""]
            lines += [f"**[{t}] {who}:** {text}" for t, who, text in call["transcript"]]
            if call.get("audio"):
                lines += ["", f"Audio: <{call['audio']}>"]
            call["file"] = rel
            call["hash"] = _write_if_changed(out_dir / rel, "\n".join(lines) + "\n")
            linked = matcher.match({"from": call["who"]}, " ".join(t[2] for t in call["transcript"]))
        else:
            linked = matcher.match({"from": call["who"]}, "")
        if call.get("person_key"):
            linked.setdefault(call["person_key"], {"role": "from", "ambiguous": False})
        if call.get("applicant"):
            applicant_calls[call["applicant"]["key"]].append({
                "at": call["at"].isoformat(), "status": _describe(call), "number": call["number"],
                "file": call.get("file"), "applicant_status": call["applicant"]["status"]})
        for key, link in linked.items():
            if call.get("file"):
                people[key].append({"id": call["id"], "date": call["at"].isoformat(), "subject": f"Phone call {call['who']}",
                                    "title": f"Phone call {call['who']}", "file": call["file"], "role": link["role"],
                                    "ambiguous": link["ambiguous"], "flag": "work", "hash": call.get("hash", "")})
    written = []
    for day, items in sorted(days.items()):
        lines = [f"# Phone log {day}", "", "| Time | Direction | Who | Number | Status |", "|---|---|---|---|---|"]
        for c in items:
            who = f"[{c['who']}](<{c['file']}>)" if c.get("file") else c["who"]
        if c.get("applicant"):
            who += f" (applicant: {c['applicant']['status']}, {c['applicant']['position'] or 'position ?'})"
            lines.append(f"| {c['local']:%H:%M} | {c['direction']} | {who} | {c['number'] or ''} | {_describe(c)} |")
        path = out_dir / f"{day}.md"
        written.append((day, path, _write_if_changed(path, "\n".join(lines) + "\n"), len(items)))
    _write_if_changed(out_dir / "people.json", json.dumps({k: {"items": v} for k, v in people.items()}, ensure_ascii=False))
    _write_if_changed(out_dir / "applicants.json", json.dumps(applicant_calls, ensure_ascii=False))
    return {"calls": len(calls), "days": written, "with_transcript": sum(1 for c in calls if c.get("file")),
            "missed": sum(1 for c in calls if c.get("missed")), "people": len(people),
            "applicant_calls": sum(len(v) for v in applicant_calls.values()), "applicants": len(applicant_calls)}
