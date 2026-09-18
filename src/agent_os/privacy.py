from __future__ import annotations

import re
from typing import Any


_PATTERNS = {
    "email": re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I),
    "ssn": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    "phone": re.compile(r"(?<!\d)(?:\+?1[\s.-]?)?(?:\(\d{3}\)|\d{3})[\s.-]\d{3}[\s.-]\d{4}(?!\d)"),
    "long_identifier": re.compile(r"\b\d{7,}\b"),
    "secret": re.compile(r"(?i)(?:api[_-]?key|token|secret|password)\s*[:=]\s*['\"]?[A-Za-z0-9_./+\-=]{12,}"),
    "private_key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "windows_path": re.compile(r"(?i)(?:^|\s)[A-Z]:\\(?:Users|Documents and Settings)\\"),
    "unix_home_path": re.compile(r"(?:^|\s)/(?:home|Users)/[^\s/]+/"),
    "street_address": re.compile(r"\b\d{1,6}\s+[A-Za-z0-9.' -]+\s(?:street|st|avenue|ave|road|rd|lane|ln|drive|dr|boulevard|blvd)\b", re.I),
}

_FORBIDDEN_KEYS = {
    "answers",
    "completed_values",
    "field_values",
    "ocr_text",
    "raw_chat",
    "raw_text",
    "signature_image",
    "source_bytes",
    "source_document",
    "source_text",
}


def privacy_findings(value: Any) -> list[str]:
    """Return detector categories only; never echo a rejected value."""
    findings: set[str] = set()

    def visit(item: Any) -> None:
        if isinstance(item, dict):
            for key, nested in item.items():
                if str(key).casefold() in _FORBIDDEN_KEYS:
                    findings.add("raw_source_field")
                visit(nested)
        elif isinstance(item, (list, tuple, set)):
            for nested in item:
                visit(nested)
        elif isinstance(item, str):
            for label, pattern in _PATTERNS.items():
                if pattern.search(item):
                    findings.add(label)

    visit(value)
    return sorted(findings)


def require_private_safe(value: Any, label: str = "record") -> None:
    findings = privacy_findings(value)
    if findings:
        raise ValueError(f"{label} rejected by privacy gate: {', '.join(findings)}")
