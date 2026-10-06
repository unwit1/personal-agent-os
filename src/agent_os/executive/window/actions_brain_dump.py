"""Actions for resolving and staging Executive brain-dump records."""

from __future__ import annotations

from typing import Any, Callable

from ... import candidates, registry as project_registry
from . import brain_dump_store
from . import registry

STORE_FACTORY: Callable[[], Any] | None = None
PROJECT_EXISTS: Callable[[str], bool] | None = None
STAGE: Callable[..., dict[str, Any]] | None = None


def _store() -> Any:
    return STORE_FACTORY() if STORE_FACTORY is not None else brain_dump_store.BrainDumpStore()


def _project_exists(project: str) -> bool:
    if PROJECT_EXISTS is not None:
        return PROJECT_EXISTS(project)
    return any(p.get("id") == project for p in project_registry.canonical_projects())


def _stage(project: str, source: str, items: list[dict[str, Any]]) -> dict[str, Any]:
    if STAGE is not None:
        return STAGE(project, source, items)
    return candidates.stage_candidates(project, source, items)


def _record_id(item: dict[str, Any]) -> str:
    record_id = (item.get("context") or {}).get("record_id")
    if not record_id:
        raise ValueError("missing brain-dump record_id")
    return record_id


def _clarify(item: dict[str, Any], params: dict[str, Any], *, confirm: bool) -> dict[str, Any]:
    record_id = _record_id(item)
    project = params.get("project")
    if not isinstance(project, str) or not project or not _project_exists(project):
        raise ValueError(f"unknown project: {project}")
    _store().set_project(record_id, project)
    return {"record_id": record_id, "project": project}


def _stage_candidate(item: dict[str, Any], params: dict[str, Any], *, confirm: bool) -> dict[str, Any]:
    record_id = _record_id(item)
    store = _store()
    record = store.get(record_id)
    project = params.get("project") or record.get("project")
    if not project:
        raise ValueError("resolve the project first with brain_dump.clarify or pass project")
    if not isinstance(project, str) or not _project_exists(project):
        raise ValueError(f"unknown project: {project}")
    candidate = {
        "kind": "preference_candidate",
        "statement": record["text"],
        "evidence": ["executive:brain-dump", f"brain-dump:{record_id}"],
        "confidence": record.get("confidence"),
    }
    if not confirm:
        return {
            "record_id": record_id,
            "project": project,
            "candidate": candidate,
            "note": "Stages a candidate for review; nothing is promoted.",
        }
    staged = _stage(project, "Executive brain dump", [candidate])
    store.mark_staged(record_id, staged)
    return {"record_id": record_id, "project": project, "staging": staged}


def register(reg: registry.Registry) -> None:
    reg.register_action(
        "brain_dump.clarify", "Set project", ["brain_dump_clarification"], _clarify,
        consequential=False,
        description="Resolve which project a brain-dump record belongs to",
        params_schema={"project": {"type": "string"}},
    )
    reg.register_action(
        "brain_dump.stage_candidate", "Stage as candidate",
        ["brain_dump_record", "brain_dump_clarification"], _stage_candidate,
        consequential=True,
        description="Stage a brain-dump record as a candidate memory (never promoted)",
        params_schema={"project": {"type": "string"}},
    )
