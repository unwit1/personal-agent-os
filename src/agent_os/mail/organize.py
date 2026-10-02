"""Inbox categorizer and organization plan (pure; no moves happen here)."""
from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Callable, Iterable

from . import spam

CATEGORIES = ("action_needed", "waiting_on_others", "receipts_finance", "newsletters_promotions",
              "notifications", "hr_applicants", "personal", "spam", "archive_old")

TARGET_FOLDERS = {
    "action_needed": None,
    "waiting_on_others": None,
    "receipts_finance": "Agent OS/Receipts",
    "newsletters_promotions": "Agent OS/Newsletters",
    "notifications": "Agent OS/Notifications",
    "hr_applicants": "Agent OS/Applicants",
    "personal": "Agent OS/Personal",
    "spam": "Agent OS/Spam",
    "archive_old": "Agent OS/Archive",
}

OWN_SENT = "own_sent"
ARCHIVE_DAYS = 365
SAMPLE_CHARS = 120
ARCHIVABLE = ("notifications", "newsletters_promotions", "personal", "waiting_on_others")

_HR_SUBJECT = re.compile(r"applicant|application|apply|resume|r[ée]sum[ée]|\bcv\b|candidate|interview|hiring|recruit|job posting|offer letter|onboarding", re.I)
_HR_DOMAINS = ("indeed.com", "ziprecruiter.com", "greenhouse.io", "lever.co", "workable.com",
               "applytojob.com", "jobvite.com", "smartrecruiters.com")
_FIN_SUBJECT = re.compile(r"receipt|invoice|order confirmation|your order|payment|statement|billing|refund|transaction|\btax\b|\bpaid\b", re.I)
_FIN_LOCAL = re.compile(r"^(billing|invoices?|receipts?|payments?|orders?)$", re.I)
_FIN_DOMAINS = ("paypal.com", "stripe.com", "squareup.com", "venmo.com")


def _domain_in(domain: str, domains: tuple[str, ...]) -> bool:
    return any(domain == d or domain.endswith("." + d) for d in domains)


def _parse_date(value) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _age_days(message: dict, now: datetime) -> float:
    parsed = _parse_date(message.get("date"))
    return max(0.0, (now - parsed).total_seconds() / 86400) if parsed else 0.0


def _asks(message: dict, own: set[str]) -> bool:
    if "?" in str(message.get("subject") or "") or "?" in str(message.get("snippet") or ""):
        return True
    return bool(set(spam._addresses(message.get("recipients"))) & own)


def _is_inbox(message: dict) -> bool:
    return str(message.get("mailbox") or "").strip().casefold() == "inbox"


def categorize(message: dict, *, own: set[str], known: set[str], now: datetime | None = None,
               thread_last_own: bool = False) -> tuple[str, str]:
    """-> (category, reason). Own sent mail returns ('own_sent', ...) and is never moved."""
    now = now or datetime.now(timezone.utc)
    result = spam.classify(message, own=own, known=known)
    verdict, reasons = result["verdict"], result["reasons"]
    if reasons == [spam.R_OWN]:
        return OWN_SENT, spam.R_OWN
    addr = spam._address(message.get("sender"))
    local, _, domain = addr.rpartition("@")
    subject = str(message.get("subject") or "")
    scope = message.get("scope")
    lead = reasons[0]

    if verdict == "spam":
        return "spam", lead
    if verdict == "bulk":
        if scope == "work":
            hit = _HR_SUBJECT.search(subject)
            if hit or _domain_in(domain, _HR_DOMAINS):
                return "hr_applicants", (f'subject mentions "{hit.group(0)}"' if hit else f"job board sender ({domain})")
        hit = _FIN_SUBJECT.search(subject)
        if hit or _FIN_LOCAL.match(local) or _domain_in(domain, _FIN_DOMAINS):
            return "receipts_finance", (f'subject mentions "{hit.group(0)}"' if hit else f"billing sender ({addr})")
        promo = any(rx.search(subject) for _, rx in spam._PROMO_RES)
        auto = spam._present(message.get("auto_submitted")) and str(message["auto_submitted"]).strip().lower() != "no"
        if (spam.STRONG_SENDER.match(local) or auto) and not promo:
            category = "notifications"
        else:
            category = "newsletters_promotions"
        reason = lead
    elif verdict == "review":
        return "action_needed", "borderline: " + lead
    elif thread_last_own:
        category, reason = "waiting_on_others", "you spoke last in this thread"
    elif _asks(message, own):
        return "action_needed", "asks a question or addresses you directly"
    elif scope == "personal":
        category, reason = "personal", "personal correspondent, no reply needed"
    else:
        return "action_needed", "default: kept in inbox"

    if category in ARCHIVABLE and _age_days(message, now) > ARCHIVE_DAYS:
        return "archive_old", f"older than {ARCHIVE_DAYS} days ({category}: {reason})"
    return category, reason


def _default_iter_rows(scope: str) -> Iterable[dict] | None:
    from . import config
    from .store import Store

    path = config.db_for(scope)
    if not path.exists():
        return None
    with Store(path) as store:
        return list(store.iter_messages())


def _own_addresses() -> set[str]:
    from .accounts import load_accounts

    return {spam._address(a.email) for a in load_accounts() if getattr(a, "email", None)}


def _empty_account(scope: str) -> dict:
    return {"scope": scope, "inbox_total": 0,
            "categories": {c: {"count": 0, "samples": [], "target_folder": TARGET_FOLDERS[c], "messages": []}
                           for c in CATEGORIES}}


def build_plan(*, scopes=("work", "personal"), iter_rows: Callable[[str], Iterable[dict] | None] | None = None,
               own: set[str] | None = None, now: datetime | None = None, sample: int = 5) -> dict:
    now = now or datetime.now(timezone.utc)
    own = {spam._address(a) for a in (own if own is not None else _own_addresses())}
    rows_for = iter_rows or _default_iter_rows
    sample = max(0, min(int(sample), 5))
    plan: dict = {"generated_at": now.isoformat(), "scopes": [], "accounts": {},
                  "spam_filtered": {"total": 0, "spam": 0, "bulk": 0, "own_sent": 0, "review": 0, "by_account": {}},
                  "skipped": {"missing_scopes": [], "non_inbox": 0}}
    for scope in scopes:
        rows = rows_for(scope)
        if rows is None:
            plan["skipped"]["missing_scopes"].append(scope)
            continue
        rows = [{**r, "scope": r.get("scope") or scope} for r in rows]
        plan["scopes"].append(scope)
        known = spam.known_correspondents(rows, own)
        newest: dict[str, tuple[str, bool]] = {}
        for r in rows:
            tid, stamp = r.get("thread_id"), str(r.get("date") or "")
            if tid and (tid not in newest or stamp >= newest[tid][0]):
                newest[tid] = (stamp, spam._address(r.get("sender")) in own)
        for r in sorted(rows, key=lambda r: str(r.get("date") or ""), reverse=True):
            acct = r.get("account_id") or "unknown"
            result = spam.classify(r, own=own, known=known)
            verdict = result["verdict"]
            counts = plan["spam_filtered"]["by_account"].setdefault(
                acct, {"spam": 0, "bulk": 0, "own_sent": 0, "review": 0})
            if result["reasons"] == [spam.R_OWN]:
                counts["own_sent"] += 1
                plan["spam_filtered"]["own_sent"] += 1
            elif verdict in ("spam", "bulk", "review"):
                counts[verdict] += 1
                plan["spam_filtered"][verdict] += 1
                if verdict != "review":
                    plan["spam_filtered"]["total"] += 1
            if not _is_inbox(r):
                plan["skipped"]["non_inbox"] += 1
                continue
            last_own = newest.get(r.get("thread_id"), (None, False))[1]
            category, reason = categorize(r, own=own, known=known, now=now, thread_last_own=last_own)
            if category == OWN_SENT:
                continue
            entry = plan["accounts"].setdefault(acct, _empty_account(scope))
            entry["inbox_total"] += 1
            bucket = entry["categories"][category]
            bucket["count"] += 1
            if len(bucket["samples"]) < sample:
                bucket["samples"].append(str(r.get("subject") or "")[:SAMPLE_CHARS])
            bucket["messages"].append({"id": r.get("id"), "uid": r.get("uid"),
                                       "mailbox": r.get("mailbox"), "reason": reason})
    return plan
