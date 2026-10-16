"""Actions for drafting, proposing and saving Executive document tasks.

Saving follows the Confirm rule: the preview pins the exact text in the
pending params, and Confirm writes those params unchanged (never regenerated).
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Callable

from .. import documents
from . import doc_store
from . import registry

STORE_FACTORY: Callable[[], Any] | None = None
OUTPUT_BASE: Path | str | None = None


def _store() -> Any:
    return STORE_FACTORY() if STORE_FACTORY is not None else doc_store.DocumentTaskStore()


def _doc_id(item: dict[str, Any]) -> str:
    doc_id = (item.get("context") or {}).get("doc_id")
    if not doc_id:
        raise ValueError("missing document doc_id")
    return doc_id


def _open_task(store: Any, item: dict[str, Any]) -> dict[str, Any]:
    task = store.get(_doc_id(item))
    if task.get("status") == "discarded":
        raise ValueError(f"document task was discarded: {task['id']}")
    return task


def _title(task: dict[str, Any]) -> str:
    return f"{documents.DOC_LABELS.get(task['doc_type'], task['doc_type'])}: {task['role']}"


def _last_saved_text(task: dict[str, Any]) -> str:
    revisions = task.get("revisions") or []
    if not revisions:
        return ""
    try:
        return Path(revisions[-1]["path"]).read_text(encoding="utf-8")
    except (OSError, KeyError):
        return ""


def _redact_text(params: dict[str, Any]) -> Any:
    """Take the pinned text out of the pending params before Confirm audits them.

    registry.confirm audits the same params dict after the handler runs, so the
    audit log records only the text's sha256, never the HR document itself."""
    text = params.pop("text", None)
    if isinstance(text, str):
        params["text_sha256"] = documents.sha256(text)
    return text


def _start(item: dict[str, Any], params: dict[str, Any], *, confirm: bool) -> dict[str, Any]:
    doc_type = params.get("doc_type")
    if doc_type not in documents.DOC_TYPES:
        raise ValueError(f"doc_type must be one of {', '.join(documents.DOC_TYPES)}")
    role = params.get("role")
    if not isinstance(role, str) or not role.strip():
        raise ValueError("role is required")
    role = role.strip()
    documents.slug(role)
    questions = documents.default_questions(doc_type)
    task = _store().create(doc_type, role, questions, documents.skeleton(doc_type, role))
    return {
        "doc_id": task["id"],
        "doc_type": doc_type,
        "role": role,
        "status": task["status"],
        "draft": task["draft"],
        "questions": documents.open_questions(task["questions"]),
        "note": "Draft only; answer the questions with document.answer. Nothing is saved until document.save is confirmed.",
    }


def _answer(item: dict[str, Any], params: dict[str, Any], *, confirm: bool) -> dict[str, Any]:
    store = _store()
    task = _open_task(store, item)
    raw_answers = params.get("answers") or {}
    if not isinstance(raw_answers, dict):
        raise ValueError("answers must be an object of {question_id: text}")
    answers = dict(raw_answers)
    question_id = (item.get("context") or {}).get("question_id")
    if question_id and isinstance(params.get("answer"), str):
        answers[question_id] = params["answer"]
    changes = params.get("changes")
    if changes is not None and not isinstance(changes, str):
        raise ValueError("changes must be text")
    text = params.get("text")
    if text is not None and (not isinstance(text, str) or not text.strip()):
        raise ValueError("text must be the complete draft")
    if not answers and not (changes and changes.strip()) and text is None:
        raise ValueError("pass answers, changes or text")
    questions = documents.apply_answers(task["questions"], answers)
    all_changes = list(task.get("changes") or [])
    if changes and changes.strip():
        all_changes.append(changes.strip())
    source = task.get("draft_source", "template")
    if text is not None:
        draft, source = text, "text"
    elif source == "text":
        draft = task["draft"]  # keep the written draft; answers and changes are recorded for the next revision
    else:
        draft = documents.skeleton(task["doc_type"], task["role"], documents.answer_map(questions), all_changes)
    unanswered = documents.open_questions(questions)
    task = store.update(
        task["id"], questions=questions, changes=all_changes, draft=draft, draft_source=source,
        status="awaiting_answers" if unanswered else "drafting",
    )
    return {
        "doc_id": task["id"],
        "status": task["status"],
        "draft": draft,
        "open_questions": unanswered,
        "note": (
            "Recorded the answers, but left your hand-written draft unchanged; pass text to revise it."
            if source == "text" and text is None else
            "Updated the draft only; nothing is saved until document.save is confirmed."
        ),
    }


def _propose(item: dict[str, Any], params: dict[str, Any], *, confirm: bool) -> dict[str, Any]:
    pinned = _redact_text(params) if confirm else None
    store = _store()
    task = _open_task(store, item)
    if not confirm:
        if "text" in params:
            text = params["text"]  # explicitly supplied; pinned for Confirm
        else:
            text = task["draft"]
            params["draft_sha256"] = documents.sha256(text)  # Confirm refuses if the draft moved on
        if not isinstance(text, str) or not text.strip():
            raise ValueError("text must be the complete draft")
        return {
            "doc_id": task["id"],
            "title": f"Proposed {_title(task)}",
            "content": documents.unified_diff(_last_saved_text(task), text),
            "open_questions": documents.open_questions(task["questions"]),
            "sha256": documents.sha256(text),
            "note": "Marks this draft as proposed on Confirm; nothing is written to disk.",
        }
    text = pinned
    if text is None:
        if documents.sha256(task["draft"]) != params.get("draft_sha256"):
            raise ValueError("draft changed since preview; propose again")
        text = task["draft"]
    if not isinstance(text, str):
        raise ValueError("missing previewed text")
    source = "text" if text != task["draft"] else task.get("draft_source", "template")
    store.update(task["id"], draft=text, draft_source=source, status="proposed")
    return {"doc_id": task["id"], "status": "proposed", "sha256": documents.sha256(text)}


def _next_version(task: dict[str, Any]) -> int:
    """One past the highest {doc_type}-vN.md already in the role's shared folder."""
    directory = documents.output_dir(task["role"], base=OUTPUT_BASE)
    pattern = re.compile(re.escape(task["doc_type"]) + r"-v(\d+)\.md")
    found = [int(m.group(1)) for p in directory.glob(task["doc_type"] + "-v*.md")
             if (m := pattern.fullmatch(p.name))]
    return max(found, default=0) + 1


def _targets(task: dict[str, Any], version: int) -> tuple[Path, Path | None]:
    directory = documents.output_dir(task["role"], base=OUTPUT_BASE)
    stem = f"{task['doc_type']}-v{version}"
    docx_path = directory / f"{stem}.docx" if documents.docx_available() else None
    return directory / f"{stem}.md", docx_path


def _save(item: dict[str, Any], params: dict[str, Any], *, confirm: bool) -> dict[str, Any]:
    pinned = _redact_text(params) if confirm else None
    store = _store()
    task = _open_task(store, item)
    if not confirm:
        text = params.get("text", task["draft"])
        if not isinstance(text, str) or not text.strip():
            raise ValueError("text must be the complete document")
        version = _next_version(task)
        md_path, docx_path = _targets(task, version)
        digest = documents.sha256(text)
        # Pin exactly what is previewed; Confirm writes these params unchanged.
        params.update(text=text, version=version, sha256=digest)
        return {
            "doc_id": task["id"],
            "title": f"Save {_title(task)} (v{version})",
            "content": text,
            "paths": [str(md_path)] + ([str(docx_path)] if docx_path else []),
            "sha256": digest,
            "open_questions": documents.open_questions(task["questions"]),
            "note": "Writes exactly this text on Confirm."
                    + ("" if docx_path else " python-docx is not installed, so no .docx will be written."),
        }
    text, version, digest = pinned, params.get("version"), params.get("sha256")
    if not isinstance(text, str) or not isinstance(version, int) or documents.sha256(text) != digest:
        raise ValueError("pending save does not match its preview")
    md_path, docx_path = _targets(task, version)
    if md_path.exists():
        raise ValueError(f"refusing to overwrite {md_path}")
    md_path.parent.mkdir(parents=True, exist_ok=True)
    with md_path.open("w", encoding="utf-8", newline="") as handle:
        handle.write(text)
    if docx_path is not None:
        documents.render_docx(text, docx_path)
    store.add_revision(task["id"], {"n": version, "sha256": digest, "path": str(md_path)})
    return {"doc_id": task["id"], "path": str(md_path), "sha256": digest}


def _discard(item: dict[str, Any], params: dict[str, Any], *, confirm: bool) -> dict[str, Any]:
    store = _store()
    task = store.update(_doc_id(item), status="discarded")
    return {"doc_id": task["id"], "status": task["status"]}


def register(reg: registry.Registry) -> None:
    reg.register_action(
        "document.start", "Start document", ["document_start"], _start,
        consequential=False,
        description="Start a job description or internal posting draft and list the questions to ask first",
        params_schema={"doc_type": {"type": "string", "enum": list(documents.DOC_TYPES)}, "role": {"type": "string"}},
    )
    reg.register_action(
        "document.answer", "Answer", ["document_task", "document_question"], _answer,
        consequential=False,
        description="Record answers or requested changes; updates the draft only, never a saved file",
        params_schema={"answers": {"type": "object"}, "answer": {"type": "string"},
                       "changes": {"type": "string"}, "text": {"type": "string"}},
    )
    reg.register_action(
        "document.propose", "Propose", ["document_task"], _propose,
        consequential=True,
        description="Preview the draft as a diff against the last saved version (marks proposed on Confirm)",
        params_schema={"text": {"type": "string"}},
    )
    reg.register_action(
        "document.save", "Save", ["document_task"], _save,
        consequential=True,
        description="Preview the exact final text and paths; writes that text on Confirm",
        params_schema={"text": {"type": "string"}},
    )
    reg.register_action(
        "document.discard", "Discard", ["document_task"], _discard,
        consequential=False,
        description="Discard a document task without saving",
        params_schema={},
    )
