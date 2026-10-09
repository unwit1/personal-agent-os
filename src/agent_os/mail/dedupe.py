"""Merge near-duplicate copies that exact matching cannot catch.

Conversion tools (PST -> .eml/zip exports) often drop the Message-ID and
re-render the body, so a copy of a mail already indexed from IMAP or a PST
gets its own logical message. This pass folds such a copy into the original
when all of these hold:

* the copy is known only from file exports (zip_export, mail_file, mbox);
* the original has at least one IMAP or PST source;
* same sender address and normalized subject, dates within two minutes;
* no conflicting Message-IDs (two different IDs are two emails, as in ``Store``);
* the bodies agree (word overlap >= 0.6) or one of them is empty.

The copy's sources move to the original (so provenance is kept) and the copy
row is removed. Every merge is appended to ``<scope>/dedupe-log.jsonl``.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from . import config
from .message import normalize_subject
from .spam import _address
from .store import Store

EXPORT_KINDS = ("zip_export", "mail_file", "mbox")
_WORDS = re.compile(r"\w{3,}")


def _when(value: str | None) -> datetime | None:
    try:
        return datetime.fromisoformat(str(value))
    except (TypeError, ValueError):
        return None


def _overlap(a: str, b: str) -> float:
    x, y = set(_WORDS.findall((a or "")[:3000].lower())), set(_WORDS.findall((b or "")[:3000].lower()))
    if not x or not y:
        return 1.0
    return len(x & y) / min(len(x), len(y))


def merge_near_duplicates(scope: str = "work", db_path: Path | None = None, dry_run: bool = False) -> dict[str, Any]:
    log_path = config.scope_dir(scope) / "dedupe-log.jsonl"
    merged, checked = [], 0
    marks = ",".join("?" * len(EXPORT_KINDS))
    with Store(db_path or config.db_for(scope)) as store:
        conn = store.conn
        copies = conn.execute(
            f"SELECT * FROM mail_messages m WHERE NOT EXISTS (SELECT 1 FROM mail_sources s WHERE s.message_id = m.id "
            f"AND s.source_kind NOT IN ({marks}))", EXPORT_KINDS).fetchall()
        for copy in copies:
            checked += 1
            when = _when(copy["date_utc"])
            if when is None:
                continue
            lo, hi = (when - timedelta(minutes=2)).isoformat(), (when + timedelta(minutes=2)).isoformat()
            subject, sender = normalize_subject(copy["subject"] or ""), _address(copy["sender"])
            for cand in conn.execute(
                    f"SELECT * FROM mail_messages m WHERE m.id <> ? AND m.date_utc BETWEEN ? AND ? AND EXISTS "
                    f"(SELECT 1 FROM mail_sources s WHERE s.message_id = m.id AND s.source_kind NOT IN ({marks}))",
                    (copy["id"], lo, hi, *EXPORT_KINDS)).fetchall():
                if normalize_subject(cand["subject"] or "") != subject or _address(cand["sender"]) != sender:
                    continue
                if copy["rfc_message_id"] and cand["rfc_message_id"] and copy["rfc_message_id"] != cand["rfc_message_id"]:
                    continue
                score = _overlap(copy["body"], cand["body"])
                if score < 0.6:
                    continue
                merged.append({"copy": copy["id"], "into": cand["id"],
                               "date": copy["date_utc"], "overlap": round(score, 2)})
                if not dry_run:
                    conn.execute("UPDATE mail_sources SET message_id=? WHERE message_id=?", (cand["id"], copy["id"]))
                    store._drop_if_orphan(copy["id"])
                break
        if not dry_run:
            conn.commit()
    if merged and not dry_run:
        with log_path.open("a", encoding="utf-8") as handle:
            stamp = datetime.now().isoformat(timespec="seconds")
            for entry in merged:
                handle.write(json.dumps({"at": stamp, **entry}) + "\n")
    return {"scope": scope, "export_only_checked": checked, "merged": len(merged), "dry_run": dry_run}
