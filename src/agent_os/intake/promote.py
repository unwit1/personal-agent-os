"""Distill PII-free company knowledge from work items (``promote`` deliveries).

The RTEC-HR repository holds policies, processes, company facts and current staff
roles only: no PII. This worker reads work mail in small batches, asks the model
(subscription CLI, see ``classify``) for durable organisational facts, and keeps
only statements that pass a deterministic PII screen:

* no email addresses, phone numbers, SSN-like or long ID numbers, street addresses;
* person names only for current staff (HR datastore, Active roster), never anyone else.

Survivors are appended to ``.agent-local/intake/work/knowledge-candidates.jsonl`` with the
source message ids as evidence. They are candidates for review; nothing is written
to RTEC-HR here.
"""

from __future__ import annotations

import json
import re
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from ..mail import config as mail_config
from . import LOCAL, Queue, settings
from .classify import _run_claude, mask, usage_limited

BATCH = 25
CATEGORIES = ("policy", "procedure", "system", "vendor", "benefit", "compliance", "form", "role", "organization", "schedule")
_PII = (re.compile(r"[\w.+'-]+@[\w-]+\.[\w.-]+"), re.compile(r"\b\(?\d{3}\)?[-. ]?\d{3}[-. ]?\d{4}\b"),
        re.compile(r"\b\d{3}-?\d{2}-?\d{4}\b"), re.compile(r"\b\d{6,}\b"),
        re.compile(r"\b\d{2,5} [A-Z][a-z]+ (Street|St|Road|Rd|Avenue|Ave|Lane|Ln|Drive|Dr|Highway|Hwy)\b"))
_NAME = re.compile(r"\b([A-Z][a-z]+) ([A-Z][a-z]+)\b")


def candidates_path() -> Path:
    return LOCAL / "work" / "knowledge-candidates.jsonl"


def staff_names(datastore: Path | None) -> tuple[set[str], set[str]]:
    """(current staff "first last" names, every other known person's names), lower-case."""
    current, everyone = set(), set()
    if not datastore or not Path(datastore).exists():
        return current, everyone
    with closing(sqlite3.connect(f"file:{Path(datastore).as_posix()}?mode=ro", uri=True)) as conn:
        rec: dict[str, dict[str, str]] = {}
        for key, field, value in conn.execute(
                "SELECT person_key, field, value FROM current WHERE field IN ('first_name','last_name','termination_date','employee_status')"):
            rec.setdefault(key, {})[field] = str(value or "")
    for r in rec.values():
        name = f"{r.get('first_name', '').split(' ')[0]} {r.get('last_name', '')}".strip().lower()
        if " " not in name:
            continue
        everyone.add(name)
        if not r.get("termination_date") and r.get("employee_status", "Active").lower().startswith("active"):
            current.add(name)
    return current, everyone - current


def screen(statement: str, current: set[str], others: set[str]) -> str | None:
    """Reason to reject, or None when the statement is PII-free."""
    if any(p.search(statement) for p in _PII):
        return "contact detail or identifying number"
    for first, last in _NAME.findall(statement):
        if f"{first} {last}".lower() in others:
            return "names a person who is not current staff"
    return None


def prompt_for(rows: list[dict[str, Any]]) -> str:
    items = "\n\n".join(f"[{r['id']}] {r['date'][:10]} | {r['subject']}\n{mask(r['body'])[:1500]}" for r in rows)
    return ("These are emails from the HR office of RTEC, a rural public transit agency in Kentucky. Extract durable, "
            "organisation-level knowledge only: policies, procedures and process steps, systems and vendors used, benefit "
            "plans and carriers, compliance obligations, forms, schedules/deadlines, and job titles of staff roles. "
            "NEVER include anything about an individual employee or applicant (health, leave, pay, discipline, hiring "
            "decisions, contact details, addresses, ID numbers). Current staff may be named only together with their role.\n"
            f"Answer ONLY a JSON array of {{\"statement\": str, \"category\": one of {list(CATEGORIES)}, "
            "\"evidence\": [email ids], \"as_of\": \"YYYY-MM-DD\"}. Return [] if nothing qualifies.\n\n" + items)


def promote(limit_batches: int = 1, runner: Callable[[str], str] | None = None) -> dict[str, Any]:
    conf = settings()
    runner = runner or _run_claude
    sc = conf["scopes"]["work"]
    current, others = staff_names(Path(sc["hr_datastore"]) if sc.get("hr_datastore") else None)
    result = {"batches": 0, "kept": 0, "rejected": 0, "errors": []}
    out = candidates_path()
    out.parent.mkdir(parents=True, exist_ok=True)
    with Queue("work") as q:
        window = q.pending("promote", BATCH * limit_batches * 8)
        pending = [r for r in window if r["source"] == "mail" and r["flag"] == "work"]
        skipped = [r["item_id"] for r in window if r["source"] != "mail" or r["flag"] != "work"]
        if skipped:  # reports/automated mail: no free-text knowledge to distill here
            q.finish(skipped, "promote", "skipped", {"reason": "not human work mail"})
        for start in range(0, min(len(pending), BATCH * limit_batches), BATCH):
            batch = pending[start:start + BATCH]
            ids = {r["ref"]: r["item_id"] for r in batch}
            marks = ",".join("?" * len(ids))
            with closing(sqlite3.connect(f"file:{mail_config.db_for('work').as_posix()}?mode=ro", uri=True)) as conn:
                conn.row_factory = sqlite3.Row
                rows = [{"id": m["id"], "date": m["date_utc"] or "", "subject": m["subject"] or "", "body": m["body"] or ""}
                        for m in conn.execute(f"SELECT id, date_utc, subject, body FROM mail_messages WHERE id IN ({marks})", list(ids))]
            try:
                text = runner(prompt_for(rows))
                found = json.loads(text[text.find("["):text.rfind("]") + 1] or "[]")
            except Exception as exc:  # noqa: BLE001
                if usage_limited(exc):  # out of subscription usage: resume next run, items untouched
                    result["paused"] = "usage limit"
                    break
                q.finish(list(ids.values()), "promote", "failed", {"error": str(exc)[:200]})
                result["errors"].append(str(exc)[:200])
                continue
            stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
            with out.open("a", encoding="utf-8") as handle:
                for c in found if isinstance(found, list) else []:
                    statement = str(c.get("statement") or "").strip() if isinstance(c, dict) else ""
                    if not statement:
                        continue
                    reason = screen(statement, current, others)
                    if reason:
                        result["rejected"] += 1
                        continue
                    evidence = [e for e in c.get("evidence") or [] if e in ids]
                    handle.write(json.dumps({"statement": statement, "category": c.get("category"), "as_of": c.get("as_of"),
                                             "evidence": evidence, "at": stamp, "status": "candidate"}, ensure_ascii=False) + "\n")
                    result["kept"] += 1
            q.finish(list(ids.values()), "promote", "done", None)
            result["batches"] += 1
    return result
