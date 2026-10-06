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


def _gap_id(item: dict[str, Any]) -> str:
    gap_id = (item.get("context") or {}).get("gap_id")
    if not gap_id:
        raise ValueError("missing knowledge-gap gap_id")
    return gap_id


def _answer(item: dict[str, Any], params: dict[str, Any], *, confirm: bool) -> dict[str, Any]:
    gap_id = _gap_id(item)
    store = _store()
    gap = store.get(gap_id)
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


def register(reg: registry.Registry) -> None:
    reg.register_action(
        "knowledge_gap.answer", "Answer", ["knowledge_gap_question"], _answer,
        consequential=True,
        description="Answer a knowledge-gap question and stage it as a candidate memory (never promoted)",
        params_schema={"answer": {"type": "string"}, "project": {"type": "string"}},
    )
