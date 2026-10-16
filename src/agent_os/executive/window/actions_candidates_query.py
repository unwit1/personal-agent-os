"""Recognize chat questions like "good applicants for the Dispatcher opening"."""
from __future__ import annotations

import re
from typing import Any

_FILLER = {"the", "a", "an", "open", "opening", "openings", "job", "jobs", "position", "positions",
           "role", "roles", "our", "current"}
_NOUN = r"(?:applicants?|candidates?)"
_QUALITY = r"(?:good|best|top|strong|great|qualified|promising|suitable)"
_PREP = r"(?:for|on|in|at|to fill)"
_APPLICANTS = re.compile(
    rf"\b{_QUALITY}\b[\w\s,]{{0,30}}?{_NOUN}\s+{_PREP}\s+(?P<rest>.+)$",
    re.IGNORECASE,
)
_WHO = re.compile(
    r"\bwho\s+(?:should|do|can|could|would)\s+(?:i|we)\s+"
    r"(?:interview|hire|call|consider|contact|pick|choose|look at|talk to)\b"
    rf"(?:\s+first)?\s+{_PREP}\s+(?P<rest>.+)$",
    re.IGNORECASE,
)
_WHO_ARE = re.compile(
    rf"\bwho\s+(?:are|is)\s+(?:the\s+)?{_NOUN}\s+{_PREP}\s+(?P<rest>.+)$",
    re.IGNORECASE,
)
_NUMBER = re.compile(r"\b(?:top|best|first)\s+(\d{1,3})\b", re.IGNORECASE)


def _clean(rest: str) -> str:
    rest = re.split(r"[?!.;]|\s+(?:please|thanks|thank you)\b", rest, maxsplit=1, flags=re.IGNORECASE)[0]
    words = [w for w in rest.split() if w.lower().strip(",") not in _FILLER]
    return " ".join(words).strip(" ,")


def parse_candidate_query(text: str) -> dict[str, Any] | None:
    """Return {'opening': str[, 'limit': int]} for a who-are-good-applicants question, else None."""
    text = " ".join(str(text or "").split())
    if not text:
        return None
    match = _APPLICANTS.search(text) or _WHO.search(text) or _WHO_ARE.search(text)
    if not match:
        return None
    opening = _clean(match.group("rest"))
    if not opening:
        return None
    result: dict[str, Any] = {"opening": opening}
    number = _NUMBER.search(text)
    if number and int(number.group(1)) > 0:
        result["limit"] = int(number.group(1))
    return result
