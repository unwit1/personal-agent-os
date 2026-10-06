"""Parse informal brain dumps into classified executive records.

Pure helpers for splitting, classifying, and resolving captured text.
"""

from __future__ import annotations

import hashlib
import re
from typing import Iterable

RECORD_TYPES = ("task", "idea", "reminder", "appointment", "decision", "project_update", "research_request", "follow_up")


def split_segments(text: str) -> list[str]:
    """Split free-form notes into clean sentence-sized segments."""
    if not isinstance(text, str):
        return []
    segments: list[str] = []
    for line in text.splitlines():
        line = re.sub(r"^\s*(?:(?:[-*•])\s+|(?:\d+[.)])\s+)", "", line)
        for segment in re.split(r"[.;!?] ", line):
            segment = segment.strip().rstrip(".").strip()
            if segment:
                segments.append(segment)
    return segments


def classify(segment: str) -> str:
    """Classify a segment using ordered, deterministic phrase rules."""
    value = segment.lower()
    if value.startswith(("remind me", "don't forget", "dont forget", "remember to")):
        return "reminder"
    if (re.search(r"\b(meeting|appointment|dentist|doctor)\b", value) or "call with" in value
            or re.search(r"\bat \d{1,2}(:\d{2})?\s?(am|pm)\b", value)):
        return "appointment"
    if any(phrase in value for phrase in ("follow up", "follow-up", "reply to", "get back to")) or value.startswith(("email ", "text ", "call ")):
        return "follow_up"
    if any(phrase in value for phrase in ("research", "look up", "find out", "compare ")):
        return "research_request"
    if any(phrase in value for phrase in ("decided", "decision:", "going with", "we chose", "i chose")):
        return "decision"
    if any(phrase in value for phrase in ("finished", "shipped", "completed", "done with", "update:")):
        return "project_update"
    if any(phrase in value for phrase in ("idea", "what if", "maybe we could")):
        return "idea"
    return "task"


def _project_matches(segment: str, known_projects: Iterable[dict]) -> list[str]:
    matches: list[str] = []
    for project in known_projects:
        if not isinstance(project, dict) or not project.get("id"):
            continue
        project_id = str(project["id"])
        names = [project_id, *(project.get("aliases", []) if isinstance(project.get("aliases", []), (list, tuple)) else [])]
        if any(re.search(r"\b" + re.escape(str(name)) + r"\b", segment, re.IGNORECASE) for name in names if str(name)):
            if project_id not in matches:
                matches.append(project_id)
    return matches


def resolve_project(segment: str, known_projects: Iterable[dict]) -> tuple[str | None, str | None]:
    """Resolve a project by whole-word id or alias, reporting ambiguity."""
    matches = _project_matches(segment, known_projects)
    if len(matches) == 1:
        return matches[0], None
    if len(matches) > 1:
        return None, "ambiguous_project"
    if re.search(r"(?:^|\s)[@#][\w-]+", segment):
        return None, "unknown_reference"
    return None, None


def record_id(type_: str, text: str) -> str:
    """Return a stable id for a normalized record."""
    normalized = " ".join(text.lower().split())
    digest = hashlib.sha256(f"{type_}\0{normalized}".encode("utf-8")).hexdigest()[:12]
    return "bd-" + digest


def process(text: str, *, known_projects=(), existing_ids=()) -> dict:
    """Turn a dump into records, duplicate notices, and project clarifications."""
    records, duplicates, clarifications = [], [], []
    seen: set[str] = set()
    existing = set(existing_ids)
    for segment in split_segments(text):
        type_ = classify(segment)
        identifier = record_id(type_, segment)
        project, reason = resolve_project(segment, known_projects)
        if identifier in seen:
            duplicates.append({"id": identifier, "text": segment, "reason": "repeated_in_dump"})
            continue
        seen.add(identifier)
        if identifier in existing:
            duplicates.append({"id": identifier, "text": segment, "reason": "already_captured"})
            continue
        records.append({"id": identifier, "type": type_, "text": segment, "project": project,
                        "confidence": 0.9 if project is not None else 0.5})
        if reason is not None:
            clarifications.append({"record_id": identifier, "text": segment, "reason": reason,
                                   "candidates": _project_matches(segment, known_projects)})
    return {"records": records, "duplicates": duplicates, "clarifications": clarifications}
