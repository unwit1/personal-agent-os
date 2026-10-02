from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from email.utils import getaddresses
from pathlib import Path
from typing import Any, Callable

AUTOMATED = re.compile(r"no[-_.]?reply|do[-_.]?not[-_.]?reply|donotreply|mailer-daemon|notifications?@|newsletter|bounce|listserv|\blist\b", re.I)


def _addresses(value: str | None) -> set[str]:
    return {addr.strip().lower() for _, addr in getaddresses([value or ""]) if addr.strip()}


def _own_default() -> set[str]:
    try:
        from ...mail import accounts as accounts_lib
        return {a.email.strip().lower() for a in accounts_lib.load_accounts() if a.email}
    except Exception:
        return set()


def _parse(value: Any) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _score(latest: dict[str, Any], own: set[str]) -> int:
    score = 0
    if "?" in f"{latest.get('subject') or ''} {latest.get('snippet') or ''}":
        score += 1
    if own & _addresses(latest.get("recipients")):
        score += 1
    if not AUTOMATED.search(latest.get("sender") or ""):
        score += 1
    return score


def mail_items(db_path: Path | None = None, own_addresses: list[str] | None = None, days: int = 14, limit: int = 50,
               search: Callable[..., list[dict[str, Any]]] | None = None, now: datetime | None = None) -> list[dict[str, Any]]:
    """Items for threads whose latest message awaits a reply. Reads the local index only.

    Mail lives in one index per scope; work-scope threads go to the Work tab
    and personal-scope threads to the Personal tab. An explicit db_path (tests,
    a legacy combined index) is read once and treated as personal."""
    if search is None:
        from ... import mail
        search = mail.search
    own = {a.strip().lower() for a in own_addresses} if own_addresses is not None else _own_default()
    now = now or datetime.now(timezone.utc)
    cutoff = now - timedelta(days=days)
    rows: list[dict[str, Any]] = []
    sources = [("personal", {"db_path": db_path})] if db_path is not None else [("personal", {"scope": "personal"}), ("work", {"scope": "work"})]
    for tab, where in sources:
        try:
            found = search("", limit=max(limit * 10, 200), after=cutoff.date().isoformat(), **where)
        except (ValueError, OSError):
            continue  # that scope has no index yet
        rows.extend({**row, "_tab": tab} for row in found)
    threads: dict[str, dict[str, Any]] = {}
    for row in rows:
        when = _parse(row.get("date"))
        if when is None:
            continue
        key = row.get("thread_id") or row.get("id") or row.get("message_id")
        if key and (key not in threads or when > threads[key]["_when"]):
            threads[key] = {**row, "_when": when}
    from ...mail import spam
    known = spam.known_correspondents(rows, own)
    items = []
    review: list[dict[str, Any]] = []
    filtered: dict[str, list[dict[str, Any]]] = {}
    for key, latest in threads.items():
        sender = latest.get("sender") or ""
        if own & _addresses(sender) or latest["_when"] < cutoff:
            continue
        result = spam.classify(latest, own=own, known=known)
        verdict, reasons = result["verdict"], result["reasons"]
        tab = latest.get("_tab", "personal")
        subject = latest.get("subject") or "(no subject)"
        if verdict in ("bulk", "spam"):
            filtered.setdefault(tab, []).append({"subject": subject, "sender": sender, "verdict": verdict,
                                                 "reasons": list(reasons), "_when": latest["_when"]})
            continue
        if verdict == "review":
            age = max(0, (now - latest["_when"]).days)
            review.append({
                "id": f"mail:review:{key}", "tab": tab, "kind": "mail_review", "title": subject,
                "why": f"borderline, needs operator review: {'; '.join(reasons)}",
                "source": "mail", "age_days": age, "score": 1,
                "context": {"thread_id": key, "message_id": latest.get("message_id"), "sender": sender,
                            "subject": subject, "verdict": verdict, "reasons": list(reasons)},
                "_when": latest["_when"],
            })
            continue
        score = _score(latest, own)
        if score < 2:
            continue
        age = max(0, (now - latest["_when"]).days)
        subject = latest.get("subject") or "(no subject)"
        items.append({
            "id": f"mail:{key}", "tab": latest.get("_tab", "personal"), "kind": "mail_thread", "title": subject,
            "why": f"{sender} has been waiting {age} day{'s' if age != 1 else ''} for a reply",
            "source": "mail", "age_days": age, "score": score,
            "context": {"thread_id": key, "message_id": latest.get("message_id"), "sender": sender, "subject": subject},
            "_when": latest["_when"],
        })
    items.extend(review)
    items.sort(key=lambda i: (-i["score"], -i["_when"].timestamp()))
    items = items[:limit]
    for item in items:
        del item["_when"]
    for tab, entries in filtered.items():
        entries.sort(key=lambda e: -e["_when"].timestamp())
        counts: dict[str, int] = {}
        for entry in entries:
            reason = entry["reasons"][0]
            counts[reason] = counts.get(reason, 0) + 1
        n = len(entries)
        items.append({
            "id": f"mail:filtered:{tab}", "tab": tab, "kind": "mail_filtered",
            "title": f"{n} mail thread{'s' if n != 1 else ''} filtered (bulk/spam)",
            "why": "Likely bulk, automated or spam mail kept out of your commitments",
            "source": "mail", "age_days": 0, "score": 0,
            "context": {"counts": counts,
                        "filtered": [{k: e[k] for k in ("subject", "sender", "verdict", "reasons")} for e in entries[:25]]},
        })
    return items
