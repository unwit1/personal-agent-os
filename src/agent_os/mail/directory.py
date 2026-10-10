"""Readable correspondence directories built from the mail indexes.

One directory per mail scope (work -> ``Documents/HR/Correspondence``, personal
-> ``Documents/Personal/Correspondence``; see ``intake`` settings). The index is
the source of truth and is already deduplicated: a message held in IMAP, three
PSTs and a zip export is one logical message with four sources, and gets one
file here listing all four. The directory is rebuilt incrementally: a file is
rewritten only when its content changes (new source, new classification).

    Correspondence/
      README.md, INDEX.md       what this is; counts by year, flag and source
      search.html (+ search-data.js)   offline search page (open in a browser)
      index.csv                 one row per message (Excel-friendly)
      Flagged.md                spam, bulk and review messages with the reason
      COVERAGE.md, coverage.json   every source on this PC: copies, merges, unreadable items
      People/                   per-employee message lists (work scope, HR datastore)
      people.json               the same for HR GUI dossiers
      manifest.jsonl            one line per message: id, file, content hash, flag (ingestion queue)
      Messages/<year>/<year-month>/<date time> - <sender> - <subject> [<id>].md
      Spam/<year>/...           messages flagged spam (same file format)

Flags never hide or delete anything: ``work`` (human correspondence), ``automated``
(work-relevant notifications: applicants, billing, systems), ``bulk``
(newsletters/promotions), ``spam``, ``personal`` (personal scope), ``review``
(the deterministic classifier could not decide; queued for model review).
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import sqlite3
from collections import Counter, defaultdict
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from . import config, organize, spam

FLAGS = ("work", "automated", "personal", "not_work", "bulk", "spam", "review")
FLAG_HELP = {
    "work": "human work correspondence",
    "automated": "work-relevant automated mail (applicants, billing, HR/benefit systems, notifications)",
    "personal": "personal correspondence (personal scope)",
    "not_work": "not work related (personal mail in a work mailbox; model decision)",
    "bulk": "newsletters and promotions",
    "spam": "spam (server spam folder or unsolicited promotion)",
    "review": "undecided by the rules; queued for model review",
}
MAX_PATH = 245
ROSTER_LIMIT = 12  # a message naming more people than this is a list/roster: names are not linked as mentions
_UNSAFE = re.compile(r'[<>:"/\\|?*\x00-\x1f]+')
_WORD = re.compile(r"[a-z][a-z'\-]+")
_ADDR = re.compile(r"[\w.+'-]+@[\w-]+(?:\.[\w-]+)+")


def _safe(text: str, limit: int) -> str:
    text = _UNSAFE.sub(" ", str(text or "")).strip(" .")
    return re.sub(r"\s+", " ", text)[:limit].strip(" .") or "untitled"


def _display(sender: str) -> str:
    sender = str(sender or "")
    name = sender.split("<", 1)[0].strip().strip('"').strip("'")
    return name or spam._address(sender) or "unknown"


# Attachments people send HR from a phone or home PC: photos of IDs, transcripts, signed forms.
PAPERWORK = {"jpg", "jpeg", "png", "heic", "heif", "gif", "bmp", "tif", "tiff", "pdf", "doc", "docx", "rtf", "txt",
             "odt", "xls", "xlsx", "csv", "pages"}


def sent_paperwork(attachments: Iterable[Any]) -> bool:
    """True when a message carries document or photo attachments (not just a signature logo)."""
    for a in attachments:
        name = str(a["filename"] or "").lower()
        ext = name.rsplit(".", 1)[-1] if "." in name else str(a["mime_type"] or "").rsplit("/", 1)[-1].lower()
        if ext in PAPERWORK and int(a["size"] or 0) >= 20_000:
            return True
    return False


def keep_paperwork(flag: str, reason: str, m: Any, attachments: list[Any]) -> tuple[str, str]:
    """The model may not bury paperwork: a person's message with documents or photos that it called
    spam (or not work only because it was blank) stays work. Applicants and employees often email
    HR a photo with no subject or text (HR, 2026-10-10)."""
    if not reason.startswith("model") or flag not in ("spam", "not_work") or not sent_paperwork(attachments):
        return flag, reason
    blank = not re.sub(r"[\W_]+", "", m["subject"] or "") or not (m["body"] or "").strip()
    if flag == "spam" or blank:
        return "work", "documents sent to HR (model said " + flag + ")"
    return flag, reason


FREEMAIL = {"gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "aol.com", "icloud.com", "me.com", "live.com", "msn.com",
            "comcast.net", "att.net", "windstream.net", "bellsouth.net", "ymail.com", "protonmail.com", "mail.com"}
JUNK_TLDS = {"blog", "shop", "xyz", "top", "click", "online", "site", "store", "icu", "buzz", "rest", "bond", "cfd", "sbs",
             "monster", "quest", "lol", "mom", "beauty", "hair", "skin", "autos", "boats", "homes", "yachts", "makeup",
             "boutique", "fun", "space", "website", "pw", "tk", "ml", "ga", "cf", "gq", "cyou", "today", "life", "world"}
_JUNK_NAME = re.compile(r"\b(promotion|promo|deal|offer|savings|discount|winner|reward|survey)s?\b", re.IGNORECASE)


def _domain(address: str) -> str:
    return address.rpartition("@")[2].lower()


class Flagger:
    """Message -> (flag, reason). Spam/bulk rules from ``spam``/``organize`` plus organisation context."""

    def __init__(self, scope: str, rows: list[dict], own: set[str], work_domains: set[str], employee_emails: set[str]):
        self.scope, self.own = scope, own
        self.known = spam.known_correspondents(rows, own)
        self.work_domains = {d.lower() for d in work_domains} | {_domain(a) for a in own if "@" in a}
        self.known_domains = {_domain(a) for a in self.known} - FREEMAIL
        self.employees = {e.lower() for e in employee_emails}
        self.epoch = datetime(1970, 1, 1, tzinfo=timezone.utc)  # disables the age-based archive_old category

    def junk(self, sender: str, subject: str) -> str | None:
        address = spam._address(sender)
        domain = _domain(address)
        if domain.rpartition(".")[2] in JUNK_TLDS:
            return f"throwaway domain (.{domain.rpartition('.')[2]})"
        name = str(sender or "").split("<", 1)[0]
        if re.search(r"\S {3,}\S", name) or len(re.findall(r"\S {2,}\S", str(subject or ""))) >= 3:
            return "padded display name or subject (spam obfuscation)"
        if _JUNK_NAME.search(name):
            return f'promotional sender name ("{_JUNK_NAME.search(name).group(0)}")'
        return None

    def __call__(self, row: dict) -> tuple[str, str]:
        default = "personal" if self.scope == "personal" else "work"
        address = spam._address(row.get("sender"))
        domain = _domain(address)
        result = spam.classify(row, own=self.own, known=self.known)
        if result["reasons"] == [spam.R_OWN]:
            return default, "sent by an own address"
        category, reason = organize.categorize({**row, "mailbox": "INBOX"}, own=self.own, known=self.known, now=self.epoch)
        internal = domain in self.work_domains
        if address in self.employees:
            return default, "employee address"
        if internal:
            if category in ("hr_applicants", "receipts_finance", "notifications") or result["verdict"] in ("bulk", "review"):
                return "automated", f"internal system or shared address ({domain})"
            return default, "internal correspondent"
        if result["verdict"] == "spam" or category == "spam":
            return "spam", reason
        if address not in self.known and domain not in self.known_domains:
            junk = self.junk(row.get("sender"), row.get("subject"))
            if junk:
                return "spam", junk
        if category in ("hr_applicants", "receipts_finance", "notifications"):
            return "automated", reason
        if category == "newsletters_promotions":
            return "bulk", reason
        if result["verdict"] == "review":
            if domain in self.known_domains:
                return "automated", f"known organisation ({domain}); {reason.removeprefix('borderline: ')}"
            return "review", reason
        return default, reason


# ---------------------------------------------------------------------------
# People (work scope): HR datastore -> address and name keys
# ---------------------------------------------------------------------------


def load_people(datastore: Path | None) -> list[dict[str, Any]]:
    """People from the HR GUI datastore (read-only): key, name, eid, emails, name pairs."""
    if not datastore or not Path(datastore).exists():
        return []
    rec: dict[str, dict[str, str]] = defaultdict(dict)
    with closing(sqlite3.connect(f"file:{Path(datastore).as_posix()}?mode=ro", uri=True)) as conn:
        for key, field, value in conn.execute(
                "SELECT person_key, field, value FROM current WHERE field IN "
                "('first_name','last_name','preferred_first_name','work_email','personal_email','position_id','full_name')"):
            if value:
                rec[key][field] = str(value).strip()
    people = []
    for key, r in rec.items():
        last = r.get("last_name", "").lower()
        firsts = {r.get("first_name", "").split(" ")[0].lower(), r.get("preferred_first_name", "").split(" ")[0].lower()} - {""}
        first = r.get("first_name", "").split(" ")[0]
        name = f"{r.get('last_name', '')}, {r.get('preferred_first_name') or first}".strip(", ") or r.get("full_name") or key
        people.append({"key": key, "name": name, "eid": r.get("position_id") or ("" if key.startswith("NAME:") else key),
                       "emails": sorted({r[f].lower() for f in ("work_email", "personal_email") if "@" in r.get(f, "")}),
                       "pairs": sorted({(f, last) for f in firsts if len(f) > 1 and len(last) > 1})})
    return people


class PeopleMatcher:
    def __init__(self, people: list[dict[str, Any]]):
        self.people = {p["key"]: p for p in people}
        self.by_email: dict[str, set[str]] = defaultdict(set)
        self.by_pair: dict[tuple[str, str], set[str]] = defaultdict(set)
        for p in people:
            for e in p["emails"]:
                self.by_email[e].add(p["key"])
            for first, last in p["pairs"]:
                self.by_pair[(first, last)].add(p["key"])
                self.by_pair[(last, first)].add(p["key"])  # "Last, First"

    def match(self, header_fields: dict[str, str], text: str) -> dict[str, dict[str, Any]]:
        """{person_key: {"role": from|to|cc|mention, "ambiguous": bool}}."""
        found: dict[str, dict[str, Any]] = {}
        for role in ("from", "to", "cc"):
            value = header_fields.get(role) or ""
            for addr in _ADDR.findall(value.lower()):
                for key in self.by_email.get(addr, ()):
                    found.setdefault(key, {"role": role, "ambiguous": False})
            words = _WORD.findall(value.lower())
            for pair in zip(words, words[1:]):
                keys = self.by_pair.get(pair, ())
                for key in keys:
                    found.setdefault(key, {"role": role, "ambiguous": len(keys) > 1})
        words = _WORD.findall(text.lower())
        mentions: dict[str, bool] = {}
        for pair in zip(words, words[1:]):
            keys = self.by_pair.get(pair)
            if keys:
                for key in keys:
                    mentions[key] = len(keys) > 1
        if len(mentions) <= ROSTER_LIMIT:
            for key, ambiguous in mentions.items():
                found.setdefault(key, {"role": "mention", "ambiguous": ambiguous})
        return found


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------


def _rows(conn: sqlite3.Connection) -> Iterable[sqlite3.Row]:
    return conn.execute("SELECT * FROM mail_messages ORDER BY date_utc, rowid")


def _source_label(s: sqlite3.Row) -> str:
    if s["source_kind"] == "live_imap":
        return f"{s['account_id']}:{s['mailbox']}"
    return f"{s['source_kind']}:{s['archive_id']}/{s['mailbox']}"


def render(m: sqlite3.Row, sources: list[sqlite3.Row], attachments: list[sqlite3.Row], flag: str, reason: str,
           people: dict[str, dict[str, Any]], names: dict[str, str]) -> str:
    def esc(value: Any) -> str:
        return json.dumps(str(value or ""), ensure_ascii=False)

    lines = ["---", f"id: {m['id']}", f"thread: {m['thread_id']}", f"date: {esc(m['date_utc'] or m['date_header'])}",
             f"from: {esc(m['sender'])}", f"to: {esc(m['recipients'])}", f"cc: {esc(m['cc'])}", f"subject: {esc(m['subject'])}",
             f"message_id: {esc(m['rfc_message_id'])}", f"flag: {flag}", f"flag_reason: {esc(reason)}",
             f"content_hash: {m['content_hash']}", "sources:"]
    lines += [f"  - {esc(_source_label(s))}" for s in sources]
    if people:
        lines.append("people:")
        lines += [f"  - {{key: {esc(k)}, name: {esc(names.get(k, k))}, role: {v['role']}{', ambiguous: true' if v['ambiguous'] else ''}}}"
                  for k, v in sorted(people.items())]
    lines += ["---", "", f"# {m['subject'] or '(no subject)'}", "",
              f"**From:** {m['sender'] or ''}  ", f"**To:** {m['recipients'] or ''}  "]
    if m["cc"]:
        lines.append(f"**Cc:** {m['cc']}  ")
    lines += [f"**Date:** {m['date_utc'] or m['date_header'] or 'unknown'}  ", f"**Flag:** {flag} ({reason})", "",
              (m["body"] or "_(no text body)_").rstrip(), ""]
    if attachments:
        lines += ["## Attachments", ""]
        for a in attachments:
            lines.append(f"- {a['filename'] or 'unnamed'} ({a['mime_type'] or '?'}, {a['size'] or 0} bytes, sha256 {str(a['content_hash'] or '')[:16]})")
        for a in attachments:
            text = (a["text"] or "").strip()
            if text:
                lines += ["", f"### Attachment text: {a['filename'] or 'unnamed'}", "", text]
        lines.append("")
    return "\n".join(lines)


def export(scope: str, out_dir: Path, *, datastore: Path | None = None, db_path: Path | None = None,
           coverage_log: Path | None = None, own: set[str] | None = None,
           work_domains: Iterable[str] | None = None) -> dict[str, Any]:
    """(Re)build one scope's directory. Returns counts; safe to run repeatedly."""
    config.check_scope(scope)
    out_dir = Path(out_dir)
    db = Path(db_path or config.db_for(scope))
    state_path = config.scope_dir(scope) / "directory-state.json"
    state = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else {}
    files_state: dict[str, dict[str, str]] = state.get("files", {})
    own = {spam._address(a) for a in (own if own is not None else organize._own_addresses())}
    matcher = PeopleMatcher(load_people(datastore)) if scope == "work" else None
    names = {k: p["name"] for k, p in (matcher.people.items() if matcher else [])}

    with closing(sqlite3.connect(f"file:{db.as_posix()}?mode=ro", uri=True)) as conn:
        conn.row_factory = sqlite3.Row
        sources: dict[str, list[sqlite3.Row]] = defaultdict(list)
        for s in conn.execute("SELECT * FROM mail_sources WHERE state != 'superseded' ORDER BY first_seen"):
            sources[s["message_id"]].append(s)
        attachments: dict[str, list[sqlite3.Row]] = defaultdict(list)
        for a in conn.execute("SELECT * FROM mail_attachments ORDER BY rowid"):
            attachments[a["message_id"]].append(a)
        messages = list(_rows(conn))

    def as_row(m: sqlite3.Row) -> dict[str, Any]:
        first = next((s for s in sources[m["id"]] if s["source_kind"] == "live_imap"), (sources[m["id"]] or [None])[0])
        return {"id": m["id"], "thread_id": m["thread_id"], "subject": m["subject"], "sender": m["sender"],
                "recipients": m["recipients"], "date": m["date_utc"] or m["date_header"], "mailbox": first["mailbox"] if first else "",
                "account_id": first["account_id"] if first else None, "list_unsubscribe": m["list_unsubscribe"],
                "list_id": m["list_id"], "precedence": m["precedence"], "auto_submitted": m["auto_submitted"], "scope": scope,
                "snippet": (m["body"] or "")[:400]}

    rows = [as_row(m) for m in messages]
    employee_emails = {e for p in (matcher.people.values() if matcher else []) for e in p["emails"]}
    flagger = Flagger(scope, rows, own, set(work_domains or ()), employee_emails)
    now = datetime.now(timezone.utc)
    seen_files: set[str] = set()
    manifest, csv_rows, flagged = [], [], defaultdict(list)
    per_person: dict[str, list[dict[str, Any]]] = defaultdict(list)
    counts = Counter()
    by_year = Counter()
    written = 0
    from ..intake.classify import load_overrides

    overrides = load_overrides(scope)
    for m, row in zip(messages, rows):
        flag, reason = flagger(row)
        decided = overrides.get(m["id"])
        if decided:
            flag, reason = decided["flag"], f"model: {decided.get('reason') or decided['flag']}"
            flag, reason = keep_paperwork(flag, reason, m, attachments[m["id"]])
        sender = spam._address(m["sender"])
        screen = (scope == "work" and flag == "work" and not decided and _domain(sender) in FREEMAIL
                  and sender not in employee_emails and sender not in own)
        date = str(m["date_utc"] or "")
        year, month = (date[:4], date[:7]) if re.match(r"\d{4}-\d{2}", date) else ("Undated", "Undated")
        stamp = f"{date[:10]} {date[11:13]}{date[14:16]}" if year != "Undated" else "undated"
        folder = f"Spam/{year}" if flag == "spam" else f"Messages/{year}/{month}"  # spam kept apart (HR, 2026-10-09)
        head = f"{folder}/{_safe(stamp, 16)} - {_safe(_display(m['sender']), 30)} - "
        room = max(20, min(80, MAX_PATH - len(str(out_dir)) - len(head) - 16))  # Windows path limit
        rel = f"{head}{_safe(m['subject'] or 'no subject', room)} [{m['id'][4:12]}].md"
        people = {}
        if matcher is not None:
            people = matcher.match({"from": m["sender"] or "", "to": m["recipients"] or "", "cc": m["cc"] or ""},
                                   f"{m['subject'] or ''}\n{m['body'] or ''}")
        text = render(m, sources[m["id"]], attachments[m["id"]], flag, reason, people, names)
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        previous = files_state.get(m["id"])
        target = out_dir / rel
        if previous and previous.get("file") != rel:
            old = out_dir / previous["file"]
            if old.exists():
                old.unlink()
        if not previous or previous.get("hash") != digest or previous.get("file") != rel or not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text, encoding="utf-8")
            written += 1
        files_state[m["id"]] = {"file": rel, "hash": digest}
        seen_files.add(m["id"])
        counts[flag] += 1
        if flag != "spam":
            by_year[year] += 1
        entry = {"id": m["id"], "file": rel, "date": date, "from": m["sender"] or "", "to": m["recipients"] or "",
                 "subject": m["subject"] or "", "flag": flag, "reason": reason, "thread": m["thread_id"],
                 "sources": len(sources[m["id"]]), "attachments": len(attachments[m["id"]]),
                 "content_hash": m["content_hash"], "export_hash": digest, "people": sorted(people), "screen": screen}
        manifest.append(entry)
        csv_rows.append(entry)
        if flag in ("spam", "bulk", "review", "not_work"):
            flagged[flag].append(entry)
        for key, link in people.items():
            per_person[key].append({"id": m["id"], "date": date, "subject": m["subject"] or "", "file": rel,
                                    "from": m["sender"] or "",
                                    "role": link["role"], "ambiguous": link["ambiguous"], "flag": flag})
    for gone in set(files_state) - seen_files:  # merged away or removed from the index
        old = out_dir / files_state.pop(gone)["file"]
        if old.exists():
            old.unlink()

    for tree in ("Messages", "Spam"):  # folders emptied when messages moved (e.g. into Spam/)
        base = out_dir / tree
        if base.exists():
            for folder in sorted((p for p in base.rglob("*") if p.is_dir()), key=lambda p: len(p.parts), reverse=True):
                if not any(folder.iterdir()):
                    folder.rmdir()
    out_dir.mkdir(parents=True, exist_ok=True)
    _write(out_dir / "manifest.jsonl", "".join(json.dumps(e, ensure_ascii=False) + "\n" for e in manifest))
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["date", "from", "to", "subject", "flag", "reason", "sources", "attachments", "people", "file", "id"])
    for e in csv_rows:
        writer.writerow([e["date"], e["from"], e["to"], e["subject"], e["flag"], e["reason"], e["sources"], e["attachments"],
                         "; ".join(names.get(k, k) for k in e["people"]), e["file"], e["id"]])
    _write(out_dir / "index.csv", "﻿" + buffer.getvalue())
    _write(out_dir / "Flagged.md", _flagged_md(flagged))
    _write(out_dir / "search-data.js", "window.MAIL=" + json.dumps(
        [[e["date"][:16], e["from"][:80], e["to"][:120], e["subject"][:160], e["flag"], e["file"],
          "; ".join(names.get(k, k) for k in e["people"])[:160]] for e in reversed(manifest)], ensure_ascii=False) + ";\n")
    _write(out_dir / "search.html", SEARCH_HTML)
    if matcher is not None:
        _people_files(out_dir, per_person, matcher)
    coverage = _coverage(db, coverage_log)
    _write(out_dir / "coverage.json", json.dumps(coverage, indent=2))
    _write(out_dir / "COVERAGE.md", _coverage_md(coverage))
    summary = {"scope": scope, "folder": str(out_dir), "messages": len(manifest), "written": written,
               "flags": dict(counts), "people_linked": len(per_person), "generated_at": now.isoformat(timespec="seconds")}
    _write(out_dir / "INDEX.md", _index_md(summary, by_year, coverage))
    _write(out_dir / "README.md", README.format(scope=scope))
    state_path.write_text(json.dumps({"files": files_state, "last": summary}), encoding="utf-8")
    return summary


def _write(path: Path, text: str) -> None:
    if not path.exists() or path.read_text(encoding="utf-8", errors="replace") != text:
        path.write_text(text, encoding="utf-8")


def _flagged_md(flagged: dict[str, list[dict[str, Any]]]) -> str:
    lines = ["# Flagged messages", "", "Nothing here is deleted: spam is filed under Spam/<year>/, everything else under Messages/. "
             "Flags come from the deterministic classifier; `review` items are queued for model review.", ""]
    for flag in ("review", "not_work", "spam", "bulk"):
        items = flagged.get(flag, [])
        lines += [f"## {flag} ({len(items)}): {FLAG_HELP[flag]}", ""]
        lines += [f"- {e['date'][:10]} [{e['subject'] or '(no subject)'}](<{e['file']}>) from {e['from']} _({e['reason']})_"
                  for e in sorted(items, key=lambda e: e["date"], reverse=True)]
        lines.append("")
    return "\n".join(lines)


def _people_files(out_dir: Path, per_person: dict[str, list[dict[str, Any]]], matcher: PeopleMatcher) -> None:
    folder = out_dir / "People"
    folder.mkdir(parents=True, exist_ok=True)
    data, keep = {}, set()
    for key, items in per_person.items():
        p = matcher.people[key]
        fname = _safe(f"{p['name']} ({p['eid']})" if p["eid"] else p["name"], 120) + ".md"
        keep.add(fname)
        items = sorted(items, key=lambda i: i["date"], reverse=True)
        direct = [i for i in items if i["role"] != "mention"]
        lines = [f"# {p['name']}" + (f" ({p['eid']})" if p["eid"] else ""), "",
                 f"{len(items)} messages: {len(direct)} sent to/from/cc, {len(items) - len(direct)} mentioning the name. "
                 "Name matches marked _ambiguous_ fit more than one person; check before relying on them.", "",
                 "| Date | Role | Subject | Flag |", "|---|---|---|---|"]
        lines += [f"| {i['date'][:10]} | {i['role']}{' (ambiguous)' if i['ambiguous'] else ''} | "
                  f"[{(i['subject'] or '(no subject)').replace('|', '/')}](<../{i['file']}>) | {i['flag']} |" for i in items]
        _write(folder / fname, "\n".join(lines) + "\n")
        data[key] = {"name": p["name"], "eid": p["eid"], "file": f"People/{fname}", "messages": items}
    for stale in folder.glob("*.md"):
        if stale.name not in keep:
            stale.unlink()
    _write(out_dir / "people.json", json.dumps(data, ensure_ascii=False))


def _coverage(db: Path, log: Path | None) -> dict[str, Any]:
    holders: dict[str, set[tuple[str, str]]] = defaultdict(set)
    copies, messages = Counter(), defaultdict(set)
    with closing(sqlite3.connect(f"file:{db.as_posix()}?mode=ro", uri=True)) as conn:
        for kind, source, message_id in conn.execute("SELECT source_kind, COALESCE(account_id, archive_id), message_id FROM mail_sources"):
            holders[message_id].add((kind, source))
            copies[(kind, source)] += 1
            messages[(kind, source)].add(message_id)
        totals = {"messages": conn.execute("SELECT COUNT(*) FROM mail_messages").fetchone()[0],
                  "observations": conn.execute("SELECT COUNT(*) FROM mail_sources").fetchone()[0]}
    unique = Counter(next(iter(h)) for h in holders.values() if len(h) == 1)
    by_source = [{"source_kind": k[0], "source": k[1], "observations": copies[k], "messages": len(messages[k]), "unique_to_source": unique[k]}
                 for k in sorted(copies)]
    files = []
    if log and Path(log).exists():
        for line in Path(log).read_text(encoding="utf-8").splitlines():
            try:
                files.append(json.loads(line))
            except ValueError:
                pass
    return {"totals": totals, "duplicate_copies_merged": totals["observations"] - totals["messages"], "by_source": by_source,
            "imports": files}


def _coverage_md(c: dict[str, Any]) -> str:
    t = c["totals"]
    lines = ["# Coverage: where every message came from", "",
             f"**{t['messages']:,} distinct messages** from **{t['observations']:,} copies** found in mailboxes, Outlook files and exports "
             f"({c['duplicate_copies_merged']:,} duplicate copies merged, never stored twice).", "",
             "`unique` = messages found only in that source (losing that source would lose them).", "",
             "| Kind | Source | Copies | Messages | Unique |", "|---|---|---|---|---|"]
    lines += [f"| {r['source_kind']} | {r['source']} | {r['observations']:,} | {r['messages']:,} | {r['unique_to_source']:,} |" for r in c["by_source"]]
    retried = {r.get("root") or r.get("path") for r in c["imports"] if r.get("kind") in ("pst", "files") and not r.get("error")}
    imports = [r for r in c["imports"] if r.get("kind") in ("pst", "files")
               and not (r.get("error") and (r.get("root") or r.get("path")) in retried)]  # a later clean rerun replaces a failed run
    if imports:
        lines += ["", "## Files imported from this PC", "",
                  "Every Outlook PST/OST, .eml, .msg, zip export and Thunderbird store found on C: and R:. "
                  "`New` = messages found nowhere else; `Merged` = copies of messages already held.", "",
                  "| File / folder | Seen | New | Merged | Already had | Unreadable |", "|---|---|---|---|---|---|"]
        for r in imports:
            seen = r.get("messages_seen", r.get("checked", 0)) or 0
            merged = r.get("deduplicated", 0) or 0
            already = r.get("already_imported", r.get("skipped", 0)) or 0
            new = r.get("indexed_new", 0) or 0
            if r.get("kind") == "files":
                new = max(0, new - merged)  # an archive import counts every queued record, merges included
            lines.append(f"| {r.get('path') or r.get('root')} | {seen:,} | {new:,} | {merged:,} | {already:,} | "
                         f"{r.get('unreadable', r.get('errors', 0)) or 0}{' ERROR ' + r['error'] if r.get('error') else ''} |")
    copies = [r for r in c["imports"] if r.get("kind") == "identical_copy"]
    if copies:
        lines += ["", "## Byte-identical copies (not read twice)", ""] + [f"- {r['path']} = {r['same_bytes_as']}" for r in copies]
    for r in c["imports"]:
        if r.get("kind") == "not_mail":
            lines += ["", f"_Excluded {r['count']} files that only look like mail: {r['note']}._"]
        elif r.get("kind") == "scan":
            lines += ["", "## Search scope", ""]
            lines += [f"- {d}: {v['dirs']:,} folders, {v['files']:,} files searched ({v['denied_dirs']} folders unreadable)"
                      for d, v in r["drives"].items()]
            lines.append(f"- {r['zip_archives_checked']} zip archives opened and checked for mail")
    return "\n".join(lines) + "\n"


def _index_md(summary: dict[str, Any], by_year: Counter, coverage: dict[str, Any]) -> str:
    lines = [f"# Correspondence ({summary['scope']})", "",
             f"_Updated {summary['generated_at']}. {summary['messages']:,} distinct messages. "
             "Search: open **search.html** in a browser, or **index.csv** in Excel._", "",
             "## By flag", "", "| Flag | Messages | Meaning |", "|---|---|---|"]
    lines += [f"| {f} | {summary['flags'].get(f, 0):,} | {FLAG_HELP[f]} |" for f in FLAGS if summary["flags"].get(f)]
    lines += ["", "See [Flagged.md](Flagged.md) for spam, bulk and review items with reasons.", "", "## By year", ""]
    lines += [f"- [{y}](<Messages/{y}>): {n:,}" for y, n in sorted(by_year.items(), reverse=True)]
    if summary["flags"].get("spam"):
        lines += ["", f"Spam ({summary['flags']['spam']:,}) is filed separately by year under [Spam](<Spam>)."]
    if summary.get("people_linked"):
        lines += ["", "## People", "", f"{summary['people_linked']:,} employees/former employees linked: see [People](<People>)."]
    lines += ["", "## Sources", "", f"{coverage['totals']['observations']:,} copies from {len(coverage['by_source'])} mailboxes/archives; "
              "see [COVERAGE.md](COVERAGE.md)."]
    return "\n".join(lines) + "\n"


README = """# Correspondence ({scope})

Generated by Agent OS from its local mail index (live mailboxes plus every Outlook PST/OST, .eml, .msg,
zip export and Thunderbird store found on this PC). Rebuilt automatically after each mail sync.

* Do not edit files under Messages/ or Spam/: they are regenerated. Put notes in the employee dossiers instead.
* Each message appears once, even if it was in several mailboxes or backups; its file lists every source.
* Flags (work, automated, bulk, spam, personal, review) never hide or delete anything.
* manifest.jsonl feeds the Agent OS ingestion queue (Ingester Engine knowledge building and HR dossiers).
* This folder contains employee and applicant information. Keep it local; never commit or cloud-sync it.
"""

SEARCH_HTML = """<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Correspondence search</title><style>
:root{--bg:#fff;--fg:#1d1d1f;--muted:#666;--line:#e3e3e3;--accent:#2457c5}
@media (prefers-color-scheme:dark){:root{--bg:#1b1b1d;--fg:#eee;--muted:#9a9a9a;--line:#333;--accent:#7aa2ff}}
body{margin:0;font:14px/1.4 system-ui,sans-serif;background:var(--bg);color:var(--fg)}
header{position:sticky;top:0;background:var(--bg);padding:12px 16px;border-bottom:1px solid var(--line);display:flex;gap:8px;flex-wrap:wrap}
input,select{font:inherit;padding:6px 8px;border:1px solid var(--line);border-radius:6px;background:var(--bg);color:var(--fg)}
#q{flex:1;min-width:220px}main{padding:0 16px}table{width:100%;border-collapse:collapse}
td{padding:6px 4px;border-bottom:1px solid var(--line);vertical-align:top}td.d{white-space:nowrap;color:var(--muted)}
a{color:var(--accent);text-decoration:none}.f{font-size:12px;color:var(--muted)}#n{color:var(--muted);align-self:center}
</style></head><body><header><input id="q" placeholder="Search sender, recipient, subject, person... (all words must match)" autofocus>
<select id="flag"><option value="">All flags</option><option>work</option><option>automated</option><option>personal</option><option>review</option><option>bulk</option><option>spam</option></select>
<input id="from" type="date" title="from date"><input id="to" type="date" title="to date"><span id="n"></span></header>
<main><table><tbody id="r"></tbody></table></main><script src="search-data.js"></script><script>
const $=id=>document.getElementById(id),esc=s=>String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const rows=(window.MAIL||[]).map(r=>({r,t:(r[1]+' '+r[2]+' '+r[3]+' '+r[6]).toLowerCase()}));
function run(){const words=$('q').value.toLowerCase().split(/\\s+/).filter(Boolean),f=$('flag').value,a=$('from').value,b=$('to').value;
const hit=rows.filter(x=>(!f||x.r[4]===f)&&(!a||x.r[0]>=a)&&(!b||x.r[0].slice(0,10)<=b)&&words.every(w=>x.t.includes(w)));
$('n').textContent=hit.length.toLocaleString()+' of '+rows.length.toLocaleString();
$('r').innerHTML=hit.slice(0,500).map(({r})=>`<tr><td class="d">${esc(r[0].replace('T',' '))}</td><td>${esc(r[1])}</td><td><a href="${encodeURI(r[5])}">${esc(r[3]||'(no subject)')}</a><div class="f">${esc(r[4])}${r[6]?' · '+esc(r[6]):''}</div></td></tr>`).join('');}
['q','flag','from','to'].forEach(id=>$(id).addEventListener('input',run));run();
</script></body></html>
"""
