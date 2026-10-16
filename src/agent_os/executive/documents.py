"""Pure helpers for Executive document tasks (job descriptions and internal postings).

Drafts use the RTEC "Position Description" layout. Nothing here talks to the
window; files are written only by ``write_markdown``/``render_docx`` into a
gitignored output directory.
"""

from __future__ import annotations

import difflib
import hashlib
import re
from pathlib import Path
from typing import Any

from .. import local_paths

DOC_TYPES = ("job_description", "internal_posting")
DOC_LABELS = {"job_description": "Job Description", "internal_posting": "Internal Posting"}
OUTPUT_SUBDIR = Path(".agent-local") / "executive" / "documents"

_QUESTIONS = (
    ("reports_to", "Who does this position report to?", DOC_TYPES),
    ("flsa", "Is the position FLSA exempt or non-exempt?", DOC_TYPES),
    ("pay", "What is the pay grade or pay range?", DOC_TYPES),
    ("schedule", "What are the schedule and hours?", DOC_TYPES),
    ("duties", "Which duties should be added to or removed from the standard description?", DOC_TYPES),
    ("qualifications", "What qualifications are required?", DOC_TYPES),
    ("posting_window", "What are the posting open and close dates?", ("internal_posting",)),
    ("how_to_apply", "How should current employees apply?", ("internal_posting",)),
)

_TBD = "_To be confirmed._"


def _check_type(doc_type: str) -> str:
    if doc_type not in DOC_TYPES:
        raise ValueError(f"doc_type must be one of {', '.join(DOC_TYPES)}")
    return doc_type


def slug(role: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "-", str(role).lower()).strip("-")
    if not value:
        raise ValueError("role is required")
    return value


def default_questions(doc_type: str) -> list[dict[str, Any]]:
    _check_type(doc_type)
    return [
        {"id": qid, "text": text, "answer": None}
        for qid, text, types in _QUESTIONS
        if doc_type in types
    ]


def apply_answers(questions: list[dict[str, Any]], answers: dict[str, Any] | None) -> list[dict[str, Any]]:
    """Return a copy of ``questions`` with ``answers`` ({question_id: text}) filled in."""
    answers = answers or {}
    if not isinstance(answers, dict):
        raise ValueError("answers must be an object of {question_id: text}")
    known = {q["id"] for q in questions}
    unknown = sorted(set(answers) - known)
    if unknown:
        raise ValueError(f"unknown question id: {', '.join(unknown)}")
    out = []
    for question in questions:
        updated = dict(question)
        value = answers.get(question["id"])
        if isinstance(value, str) and value.strip():
            updated["answer"] = value.strip()
        out.append(updated)
    return out


def answer_map(questions: list[dict[str, Any]]) -> dict[str, str]:
    return {q["id"]: q["answer"] for q in questions if q.get("answer")}


def open_questions(questions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{"id": q["id"], "text": q["text"]} for q in questions if not q.get("answer")]


def skeleton(doc_type: str, role: str, answers: dict[str, Any] | None = None,
             changes: list[str] | None = None) -> str:
    """Markdown draft in the RTEC Position Description format."""
    _check_type(doc_type)
    role = str(role).strip()
    if not role:
        raise ValueError("role is required")
    a = {k: v for k, v in (answers or {}).items() if isinstance(v, str) and v.strip()}

    def val(key: str) -> str:
        return a.get(key, _TBD)

    lines = []
    if doc_type == "internal_posting":
        lines += [f"# Internal Job Posting: {role}", ""]
    lines += [
        "# Position Description", "",
        "## Class Title", "", role, "",
        "## Characteristics of the Class", "",
        f"Reports to: {val('reports_to')}", "",
        f"FLSA status: {val('flsa')}", "",
        "## Examples of Duties", "",
        f"- {val('duties')}", "",
        "## Minimum Qualifications", "",
        f"- {val('qualifications')}", "",
        "## Working Conditions", "",
        f"Schedule and hours: {val('schedule')}", "",
    ]
    if doc_type == "internal_posting":
        lines += [
            "## Posting Dates", "", val("posting_window"), "",
            "## Who May Apply", "", "Current employees only.", "",
            "## How to Apply", "", val("how_to_apply"), "",
            "## Pay and Hours", "", f"Pay: {val('pay')}", "", f"Hours: {val('schedule')}", "",
            "## Equal Employment Opportunity", "", "_EEO statement to be inserted._", "",
        ]
    else:
        lines += ["Pay grade or range: " + val("pay"), ""]
    if changes:
        lines += ["## Requested Changes", ""] + [f"- {c}" for c in changes] + [""]
    return "\n".join(lines).rstrip("\n") + "\n"


def unified_diff(old: str, new: str, old_name: str = "saved", new_name: str = "draft") -> str:
    return "".join(difflib.unified_diff(
        (old or "").splitlines(keepends=True), (new or "").splitlines(keepends=True),
        fromfile=old_name, tofile=new_name,
    ))


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def output_dir(role: str, base: Path | str | None = None) -> Path:
    """<repo>/.agent-local/executive/documents/<role-slug>/, refused unless gitignored."""
    root = Path(base) if base is not None else local_paths.ROOT / OUTPUT_SUBDIR
    path = root / slug(role)
    if not local_paths.is_gitignored_local_path(path):
        raise ValueError(f"refusing to write documents outside a gitignored local path: {path}")
    return path


def docx_available() -> bool:
    try:
        import docx  # noqa: F401
    except ImportError:
        return False
    return True


def render_docx(markdown: str, path: Path | str) -> Path | None:
    """Write a simple .docx rendering; returns None when python-docx is not installed."""
    try:
        import docx
    except ImportError:
        return None
    document = docx.Document()
    for line in markdown.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        heading = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        if heading:
            document.add_heading(heading.group(2), level=min(len(heading.group(1)), 4))
        elif stripped.startswith("- "):
            document.add_paragraph(stripped[2:], style="List Bullet")
        else:
            document.add_paragraph(stripped)
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    document.save(str(target))
    return target
