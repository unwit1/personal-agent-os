"""Natural-language county opening events for the Executive window."""
from __future__ import annotations

import re
from typing import Any

from .registry import REGISTRY

GATEWAY: Any = None

_NUMBERS = {"a": 1, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5}
_COUNTY = r"(?P<county>[A-Za-z][A-Za-z.'-]*(?:\s+[A-Za-z][A-Za-z.'-]*){0,2}?)(?:\s+county)?"
_END = r"\s*[.!]?\s*$"
_NUM = r"(?:(?P<num>a|one|two|three|four|five)\s+)?"

_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("close", re.compile(rf"^(?:we\s+)?(?:closed|filled)\s+the\s+(?:opening|position)\s+in\s+(?:the\s+)?{_COUNTY}{_END}", re.I)),
    ("close", re.compile(rf"^the\s+{_COUNTY}\s+(?:opening|position)\s+is\s+(?:filled|closed){_END}", re.I)),
    ("close", re.compile(rf"^(?:we(?:'re|\s+are)\s+)?no\s+longer\s+hiring\s+in\s+(?:the\s+)?{_COUNTY}{_END}", re.I)),
    ("quit", re.compile(rf"^{_NUM}drivers?\s+quit\s+in\s+(?:the\s+)?{_COUNTY}{_END}", re.I)),
    ("quit", re.compile(rf"^we\s+lost\s+{_NUM}drivers?\s+in\s+(?:the\s+)?{_COUNTY}{_END}", re.I)),
    ("new", re.compile(rf"^we\s+(?:have|got)\s+a\s+new\s+(?:driver\s+)?(?:opening|position)\s+in\s+(?:the\s+)?{_COUNTY}{_END}", re.I)),
    ("new", re.compile(rf"^new\s+(?:driver\s+)?(?:opening|position)\s+in\s+(?:the\s+)?{_COUNTY}{_END}", re.I)),
    ("new", re.compile(rf"^we(?:'re|\s+are)\s+hiring\s+in\s+(?:the\s+)?{_COUNTY}{_END}", re.I)),
]


def parse_opening_event(text: str) -> dict[str, Any] | None:
    """Parse "we closed the opening in X" style text into {county, change}."""
    text = " ".join(str(text or "").split())
    if not text or text.endswith("?"):
        return None
    for change, pattern in _PATTERNS:
        match = pattern.match(text)
        if match:
            county = match.group("county").strip()
            if county.casefold() in {"county", "the"}:
                return None
            event: dict[str, Any] = {"county": county, "change": change}
            num = (match.groupdict().get("num") or "").casefold()
            if _NUMBERS.get(num, 1) > 1:
                event["count"] = _NUMBERS[num]
            return event
    return None


def _gateway() -> Any:
    if GATEWAY is not None:
        return GATEWAY
    from ..gateway import LocalDashboardGateway

    return LocalDashboardGateway()


def openings_event(item: dict[str, Any], params: dict[str, Any], *, confirm: bool) -> dict[str, Any]:
    county = params.get("county")
    change = params.get("change")
    count = params.get("count", 1)
    if params.get("text"):
        event = parse_opening_event(params["text"])
        if event is None:
            raise ValueError("Could not understand the opening event")
        county, change, count = event["county"], event["change"], event.get("count", 1)
    if not county or not change:
        raise ValueError("county and change are required")
    gateway = _gateway()
    if not confirm:
        return gateway.preview_opening_change(county, change, count=count)
    from .. import applicants

    applied = gateway.apply_opening_change(county, change, count=count)
    group = applicants.county_candidates(applied.get("county", county), gateway=gateway)
    return {"applied": applied, "county_group": group}


def register(registry: Any) -> None:
    registry.register_action(
        id="county.opening_change",
        label="Update county openings",
        applies_to="*",
        handler=openings_event,
        consequential=True,
        description="Record an opening event (close, quit, new) for a county; previews, then applies on Confirm.",
        params_schema={
            "type": "object",
            "properties": {
                "county": {"type": "string"},
                "change": {"type": "string", "enum": ["close", "quit", "new"]},
                "text": {"type": "string", "description": "Natural language, e.g. 'we closed the opening in X'"},
            },
        },
    )


register(REGISTRY)
