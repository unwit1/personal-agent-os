from __future__ import annotations

from typing import Any

from .candidates import candidate_status, curate_candidates
from .index import rebuild
from .registry import projects


EVENTS = {"push", "pull_request", "merge", "candidate_created", "skill_candidate_created", "memory_conflict", "test_failure", "architecture_change", "scheduled"}


def run(event: str = "scheduled", project_id: str | None = None) -> dict[str, Any]:
    if event not in EVENTS:
        raise ValueError(f"unsupported maintenance event: {event}")
    project_ids = [project_id] if project_id else [project["id"] for project in projects()]
    candidate_reports = []
    for item in project_ids:
        status = candidate_status(item)
        candidate_reports.append({"project": item, "counts": status["counts"], "curation": curate_candidates(item, action="review")["results"] if event in {"candidate_created", "scheduled"} else []})
    return {
        "event": event,
        "index": rebuild(),
        "candidate_curation": candidate_reports,
        "google_docs_mirror": {"status": "skipped", "reason": "no Docs connector is configured; Git remains canonical"},
    }
