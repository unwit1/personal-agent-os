"""Deterministic spam/bulk classifier for mail index rows.

Pure functions, no I/O. Contract: docs/integrations/mail-intelligence.md section 1.
"""
from __future__ import annotations

import re
from email.utils import getaddresses, parseaddr

VERDICTS = ("human", "bulk", "spam", "review")
HUMAN_MAX = 2
REVIEW_MIN = 3
BULK_MIN = 6

SPAM_FOLDER_NAMES = ("junk", "junk e-mail", "junk email", "spam", "bulk mail")

_SUFFIX = r"(?:[-_.+\d].*)?"
STRONG_SENDER = re.compile(
    r"^(?:no[-_.]?reply|do[-_.]?not[-_.]?reply|mailer-daemon|postmaster|bounces?|newsletters?|"
    r"marketing|promos?|promotions?|mailer|notifications?|notify|alerts?|autoreply|auto-reply|"
    r"automated)" + _SUFFIX + r"$"
)
WEAK_SENDER = re.compile(
    r"^(?:info|news|hello|team|support|updates?|offers?|deals?|sales|orders?|billing|accounts?|"
    r"service|customercare|customerservice|contact|admin|press|events?|careers)" + _SUFFIX + r"$"
)

BULK_DOMAINS = (
    "sendgrid.net", "amazonses.com", "mailchimp.com", "mcsv.net", "mcdlv.net", "rsgsv.net",
    "constantcontact.com", "ctctcdn.com", "hubspotemail.net", "mailgun.org", "mandrillapp.com",
    "sparkpostmail.com", "sendinblue.com", "brevo.com", "klaviyomail.com", "exacttarget.com",
    "createsend.com", "campaign-archive.com", "mailjet.com", "postmarkapp.com",
    "customeriomail.com",
)
BULK_LABELS = (
    "email", "e", "em", "news", "newsletter", "newsletters", "marketing", "promo", "promos",
    "offers", "mailer", "bounce", "bounces", "mg", "click",
)

PROMO_MARKERS = (
    ("% off", r"\d+\s?%\s*off|%\s*off|\bpercent off\b"),
    ("sale", r"\bsale\b"),
    ("deal", r"\bdeals?\b"),
    ("discount", r"\bdiscount\b"),
    ("coupon", r"\bcoupon\b"),
    ("promo", r"\b(?:promo code|promotion|promo)\b"),
    ("free shipping", r"\bfree shipping\b"),
    ("limited time", r"\blimited[ -]time\b"),
    ("last chance", r"\blast chance\b"),
    ("act now", r"\bact now\b"),
    ("don't miss", r"\bdon['’]?t miss\b"),
    ("exclusive offer", r"\bexclusive (?:offer|deal|access)\b"),
    ("special offer", r"\bspecial offer\b"),
    ("save $", r"\bsave (?:up to )?\$?\d+"),
    ("clearance", r"\bclearance\b"),
    ("bogo", r"\bbogo\b"),
    ("order now", r"\border now\b"),
    ("shop now", r"\bshop now\b"),
    ("new arrivals", r"\bnew arrivals\b"),
    ("webinar", r"\bwebinar\b"),
    ("unsubscribe", r"\bunsubscribe\b"),
    ("newsletter", r"\bnewsletter\b"),
    ("digest", r"\b(?:weekly|daily) digest\b"),
    ("giveaway", r"\bgiveaway\b"),
    ("winner", r"\bwinner\b"),
    ("black friday", r"\bblack friday\b"),
    ("cyber monday", r"\bcyber monday\b"),
)
_PROMO_RES = tuple((label, re.compile(rx, re.IGNORECASE)) for label, rx in PROMO_MARKERS)
_UNSUB_WORD = re.compile(r"\bunsubscribe\b", re.IGNORECASE)

R_OWN = "own sent mail"
R_KNOWN = "known correspondent (you replied before)"
R_FIRST = "first contact (you never replied)"
R_SPAM_PROMO = "unsolicited promotion (no unsubscribe headers)"


def _present(value) -> bool:
    return value is not None and str(value).strip() != ""


def _address(value) -> str:
    if value is None:
        return ""
    addr = parseaddr(str(value))[1].strip().lower()
    return addr if "@" in addr else ""


def _addresses(value) -> list[str]:
    if value is None:
        return []
    items = [str(value)] if isinstance(value, str) else [str(v) for v in value if v is not None]
    out = []
    for _name, addr in getaddresses(items):
        addr = addr.strip().lower()
        if "@" in addr:
            out.append(addr)
    return out


def _spam_folder(mailbox) -> bool:
    if not _present(mailbox):
        return False
    last = re.split(r"[/.\\]", str(mailbox))[-1].strip().lower()
    return last in SPAM_FOLDER_NAMES


def _bulk_domain(domain: str) -> bool:
    if not domain:
        return False
    if any(domain == d or domain.endswith("." + d) for d in BULK_DOMAINS):
        return True
    return domain.split(".")[0] in BULK_LABELS


def known_correspondents(rows, own: set[str]) -> set[str]:
    """Addresses the operator wrote to (To/Cc of rows sent by an own address), minus own."""
    own_l = {str(a).strip().lower() for a in own}
    known: set[str] = set()
    for row in rows:
        if _address(row.get("sender")) not in own_l:
            continue
        known.update(_addresses(row.get("recipients")))
        known.update(_addresses(row.get("cc")))
    return known - own_l


def classify(message: dict, *, own: set[str], known: set[str]) -> dict:
    """-> {'verdict': 'human'|'bulk'|'spam'|'review', 'reasons': [str], 'score': int}"""
    if not isinstance(message, dict):
        raise TypeError("message must be a dict")
    own_l = {str(a).strip().lower() for a in own}
    known_l = {str(a).strip().lower() for a in known}
    addr = _address(message.get("sender"))

    if addr and addr in own_l:
        return {"verdict": "bulk", "reasons": [R_OWN], "score": 0}
    mailbox = message.get("mailbox")
    if _spam_folder(mailbox):
        return {"verdict": "spam", "reasons": [f"in server spam folder ({str(mailbox).strip()})"],
                "score": 100}

    score = 0
    reasons: list[str] = []
    has_list = False
    auto = False

    if _present(message.get("list_unsubscribe")):
        score += 5
        has_list = True
        reasons.append("has List-Unsubscribe header")
    if _present(message.get("list_id")):
        score += 5
        has_list = True
        reasons.append("mailing list (List-Id)")
    prec = message.get("precedence")
    if _present(prec) and str(prec).strip().lower() in ("bulk", "list", "junk"):
        score += 4
        has_list = True
        reasons.append(f"Precedence: {str(prec).strip()}")
    auto_sub = message.get("auto_submitted")
    if _present(auto_sub) and str(auto_sub).strip().lower() != "no":
        score += 8
        auto = True
        reasons.append("auto-generated (Auto-Submitted)")

    local, _, domain = addr.rpartition("@")
    strong = bool(addr) and bool(STRONG_SENDER.match(local))
    sender_pts = 0
    if strong:
        sender_pts += 6
        reasons.append("automated sender address")
    elif addr and WEAK_SENDER.match(local):
        sender_pts += 2
        reasons.append(f"generic sender address ({local}@)")
    if addr and _bulk_domain(domain):
        sender_pts += 3
        reasons.append(f"bulk-mail sending domain ({domain})")
    score += min(sender_pts, 8)

    subject = str(message.get("subject") or "")
    matched = [label for label, rx in _PROMO_RES if rx.search(subject)]
    if matched:
        score += min(2 * len(matched), 4)
        reasons.append(f"promotional subject ({', '.join(matched)})")
    if "unsubscribe" not in matched and _UNSUB_WORD.search(str(message.get("snippet") or "")):
        score += 1
        reasons.append("mentions unsubscribe")

    is_known = bool(addr) and addr in known_l
    if is_known:
        if auto or strong:
            discount = 0
        elif has_list:
            discount = 2
        else:
            discount = 4
        if discount:
            score -= discount
            reasons.append(R_KNOWN)
    elif addr:
        score += 1
        reasons.append(R_FIRST)

    score = max(0, score)
    if score <= HUMAN_MAX:
        verdict = "human"
    elif score < BULK_MIN:
        verdict = "review"
    else:
        verdict = "bulk"
        if not is_known and not has_list and len(matched) >= 2:
            verdict = "spam"
            reasons.append(R_SPAM_PROMO)
    if not reasons:
        reasons = ["no bulk signals"]
    return {"verdict": verdict, "reasons": reasons, "score": score}
