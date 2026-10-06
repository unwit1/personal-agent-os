"""Actions for answering and staging Executive knowledge-gap records."""

from __future__ import annotations

from typing import Any, Callable

from ... import candidates, registry as project_registry
from .. import knowledge_gaps
from . import gap_store
from . import registry

STORE_FACTORY: Callable[[], Any] | None = None
PROJECT_EXISTS: Callable[[str], bool] | None = None
STAGE: Callable[..., dict[str, Any]] | None = None


def _store() -> Any:
    return STORE_FACTORY() if STORE_FACTORY is not None else gap_store.GapStore()


def _project_exists(project: str) -> bool:
    if PROJECT_EXISTS is not None:
        return PROJECT_EXISTS(project)
    return any(p.get("id") == project for p in project_registry.canonical_projects())


def _stage(project: str, source: str, items: list[dict[str, Any]]) -> dict[str, Any]:
    if STAGE is not None:
        return STAGE(project, source, items)
    return candidates.stage_candidates(project, source, items)


def _enqueue(item: dict[str, Any], params: dict[str, Any], *, confirm: bool) -> dict[str, Any]:
    gaps = params.get("gaps")
    if not isinstance(gaps, list) or not gaps or any(not isinstance(gap, dict) for gap in gaps):
        raise ValueError("gaps must be a non-empty JSON list of objects")
    tab = params.get("tab") or "personal"
    if tab not in ("work", "personal"):
        raise ValueError("tab must be work or personal")
    budget = int(params.get("budget", 1))
    min_score = float(params.get("min_score", 0.2))
    store = _store()
    selection = knowledge_gaps.select_questions(
        gaps, budget=budget, min_score=min_score, asked_ids=sorted(store.answered_ids())
    )
    if not confirm:
        return {
            "gaps": gaps,
            "tab": tab,
            "selection": selection,
            "note": "Adds these questions to the Executive window on Confirm; nothing is staged or promoted.",
        }
    return {"enqueued": store.add(gaps, tab=tab), "tab": tab, "selection": selection}


def _gap_id(item: dict[str, Any]) -> str:
    gap_id = (item.get("context") or {}).get("gap_id")
    if not gap_id:
        raise ValueError("missing knowledge-gap gap_id")
    return gap_id


def _answer(item: dict[str, Any], params: dict[str, Any], *, confirm: bool) -> dict[str, Any]:
    gap_id = _gap_id(item)
    store = _store()
    gap = store.get(gap_id)
    if gap.get("status", "open") != "open":
        raise ValueError(f"knowledge gap already answered: {gap_id}")
    answer = params.get("answer")
    project = params.get("project") or gap.get("project")
    if not project:
        raise ValueError("pass project to stage the answer")
    if not isinstance(project, str) or not _project_exists(project):
        raise ValueError(f"unknown project: {project}")
    candidate = knowledge_gaps.answer_to_candidate(
        gap, answer, source="executive:knowledge-gap"
    )
    if not confirm:
        return {
            "gap_id": gap_id,
            "project": project,
            "candidate": candidate,
            "note": "Stages a candidate for review; nothing is promoted.",
        }
    staged = _stage(project, "Executive knowledge gap", [candidate])
    store.mark_answered(gap_id, answer, staged)
    return {"gap_id": gap_id, "project": project, "staging": staged}


def answer_gap(
    gap_id: str, answer: Any, *, project: str | None = None, confirm: bool = False
) -> dict[str, Any]:
    item = {"context": {"gap_id": gap_id}}
    params = {"answer": answer}
    if project:
        params["project"] = project
    try:
        return _answer(item, params, confirm=confirm)
    except KeyError as exc:
        raise ValueError(f"unknown knowledge gap: {gap_id}") from exc


def register(reg: registry.Registry) -> None:
    reg.register_action(
        "knowledge_gap.enqueue", "Enqueue knowledge gaps", ["knowledge_gap_enqueue"], _enqueue,
        consequential=True,
        description="Add knowledge-gap questions to the Executive window (preview first; writes only on Confirm)",
        params_schema={"gaps": {"type": "array"}, "tab": {"type": "string", "enum": ["work", "personal"]}, "budget": {"type": "integer"}, "min_score": {"type": "number"}},
    )
    reg.register_action(
        "knowledge_gap.answer", "Answer", ["knowledge_gap_question"], _answer,
        consequential=True,
        description="Answer a knowledge-gap question and stage it as a candidate memory (never promoted)",
        params_schema={"answer": {"type": "string"}, "project": {"type": "string"}},
    )
