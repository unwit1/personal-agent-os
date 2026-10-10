"""Model review of mail the rules could not decide (``classify`` deliveries).

Runs the Claude Code CLI headless on the operator's subscription (API keys are
removed from the child environment, as in the Executive window). Each batch
sends only sender, recipients, subject and a short snippet, with SSN-, phone-
and date-of-birth-like numbers masked. The model answers one flag per message:

    work | automated | bulk | spam | not_work   (personal scope: personal instead of work/not_work)

Decisions go to ``.agent-local/mail/<scope>/flag-overrides.json``; the correspondence
export applies them on its next run, which re-flags the queue items.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import sqlite3
import subprocess
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from ..mail import config as mail_config
from . import Queue, check_scope

MODEL = os.environ.get("AGENT_OS_INTAKE_CLASSIFY_MODEL", "haiku")
BATCH = 40
WORK_FLAGS = {"work", "automated", "bulk", "spam", "not_work"}
PERSONAL_FLAGS = {"personal", "automated", "bulk", "spam"}
_MASKS = (
    (re.compile(r"\b\d{3}[- ]?\d{2}[- ]?\d{4}\b"), "[number]"),           # SSN-like
    (re.compile(r"\b\(?\d{3}\)?[-. ]?\d{3}[-. ]?\d{4}\b"), "[phone]"),
    (re.compile(r"\b\d{1,2}/\d{1,2}/(19|20)\d{2}\b"), "[date]"),           # DOB-like dates
    (re.compile(r"\b\d{7,}\b"), "[number]"),
)


def usage_limited(exc: Exception) -> bool:
    """The CLI answered "usage limit reached" (HTTP 429): nothing is wrong with the items."""
    text = str(exc).lower()
    return "429" in text or "hit your" in text or "usage limit" in text or "rate limit" in text


def overrides_path(scope: str) -> Path:
    return mail_config.scope_dir(scope) / "flag-overrides.json"


def load_overrides(scope: str) -> dict[str, dict[str, str]]:
    path = overrides_path(scope)
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def mask(text: str) -> str:
    for pattern, label in _MASKS:
        text = pattern.sub(label, text)
    return text


def prompt_for(scope: str, rows: list[dict[str, Any]]) -> str:
    if scope == "work":
        flags = ("work: real work correspondence of an HR office at a rural public transit agency (RTEC), including applicants, "
                 "employees, vendors, insurers, government agencies; automated: work-relevant system or vendor notifications "
                 "(benefits, payroll, HR systems, job boards, receipts); bulk: newsletters, webinars, marketing from known "
                 "organisations; spam: unsolicited junk, scams, phishing; not_work: personal, non-work mail that landed in a work mailbox. "
                 "A person emailing photos or documents to HR is work even with no subject or text (applicants and employees "
                 "send paperwork from their phones); an employee's doctor's excuse, sick or COVID notice, appointment, jury duty or "
                 "funeral notice is work (attendance and leave)")
    else:
        flags = ("personal: real personal correspondence; automated: receipts, accounts, deliveries, notifications; "
                 "bulk: newsletters and marketing; spam: unsolicited junk, scams, phishing")
    items = "\n".join(json.dumps({"id": r["id"], "from": r["from"][:120], "to": r["to"][:160], "subject": r["subject"][:200],
                                  "snippet": mask(r["snippet"])[:400], "attachments": r.get("attachments", [])},
                                 ensure_ascii=False) for r in rows)
    return ("Classify each email by one flag. Flags: " + flags + ".\n"
            "Answer ONLY a JSON array of objects {\"id\": ..., \"flag\": ..., \"reason\": \"<= 8 words\"}, one per email, same ids.\n\n"
            + items)


def _run_claude(prompt: str) -> str:
    env = {k: v for k, v in os.environ.items() if k not in ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN")}
    exe = shutil.which("claude.exe") or shutil.which("claude") or "claude"
    argv = [exe, "-p", "--output-format", "json", "--model", MODEL, "--tools", "", "--strict-mcp-config", "--mcp-config",
            '{"mcpServers":{}}', "--disable-slash-commands", "--no-session-persistence",
            "--system-prompt", "You classify emails. Reply with the requested JSON only."]
    done = subprocess.run(argv,
                          input=prompt, capture_output=True, text=True, encoding="utf-8", timeout=600, env=env, cwd=str(Path.home()),
                          shell=exe.lower().endswith(".cmd"), creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    if done.returncode != 0:
        raise RuntimeError((done.stderr or done.stdout)[-300:])
    return json.loads(done.stdout).get("result", "")


def _parse(text: str, allowed: set[str], ids: set[str]) -> dict[str, dict[str, str]]:
    start, end = text.find("["), text.rfind("]")
    if start < 0 or end < start:
        return {}
    out = {}
    for entry in json.loads(text[start:end + 1]):
        if isinstance(entry, dict) and entry.get("id") in ids and entry.get("flag") in allowed:
            out[entry["id"]] = {"flag": entry["flag"], "reason": str(entry.get("reason") or "")[:80]}
    return out


def _rows(scope: str, message_ids: list[str]) -> list[dict[str, Any]]:
    marks = ",".join("?" * len(message_ids))
    with closing(sqlite3.connect(f"file:{mail_config.db_for(scope).as_posix()}?mode=ro", uri=True)) as conn:
        conn.row_factory = sqlite3.Row
        kinds: dict[str, list[str]] = {}
        has_attachments = conn.execute("SELECT 1 FROM sqlite_master WHERE name = 'mail_attachments'").fetchone()
        for a in conn.execute(f"SELECT message_id, filename, mime_type FROM mail_attachments WHERE message_id IN ({marks})",
                              message_ids) if has_attachments else []:
            # Only the file type: attachment names can carry personal details.
            name = str(a["filename"] or "")
            kinds.setdefault(a["message_id"], []).append(name.rsplit(".", 1)[-1].lower()[:8] if "." in name else str(a["mime_type"] or "?"))
        return [{"id": r["id"], "from": r["sender"] or "", "to": r["recipients"] or "", "subject": r["subject"] or "",
                 "snippet": " ".join((r["body"] or "").split())[:600], "attachments": kinds.get(r["id"], [])[:10]}
                for r in conn.execute(f"SELECT id, sender, recipients, subject, body FROM mail_messages WHERE id IN ({marks})", message_ids)]


def classify(scope: str, limit: int = 200, runner: Callable[[str], str] | None = None) -> dict[str, Any]:
    """Decide up to ``limit`` pending ``classify`` items of one scope (mail only)."""
    check_scope(scope)
    runner = runner or _run_claude
    allowed = WORK_FLAGS if scope == "work" else PERSONAL_FLAGS
    overrides = load_overrides(scope)
    result = {"scope": scope, "decided": 0, "batches": 0, "errors": []}
    with Queue(scope) as q:
        pending = [r for r in q.pending("classify", limit) if r["source"] == "mail"]
        for start in range(0, len(pending), BATCH):
            batch = pending[start:start + BATCH]
            by_message = {r["ref"]: r["item_id"] for r in batch}
            rows = _rows(scope, list(by_message))
            try:
                decided = _parse(runner(prompt_for(scope, rows)), allowed, set(by_message))
            except Exception as exc:  # noqa: BLE001 -- retried on the next run (attempts cap at 3)
                if usage_limited(exc):  # the subscription is out of usage: try again next run
                    result["paused"] = "usage limit"
                    break
                q.finish(list(by_message.values()), "classify", "failed", {"error": str(exc)[:200]})
                result["errors"].append(str(exc)[:200])
                continue
            stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
            for message_id, decision in decided.items():
                overrides[message_id] = {**decision, "by": f"model:{MODEL}", "at": stamp}
            q.finish([by_message[m] for m in decided], "classify", "done", None)
            result["decided"] += len(decided)
            result["batches"] += 1
    path = overrides_path(scope)
    path.write_text(json.dumps(overrides, indent=1), encoding="utf-8")
    return result
