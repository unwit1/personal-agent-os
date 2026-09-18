from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .compiler import compile_context, latest_handoff
from .index import search
from .registry import get_project, identify_project, load_state, projects
from .skills import discover, match, metadata


PROJECT_TERMS = {
    "agent", "architecture", "bug", "code", "debug", "design", "implementation", "memory",
    "mcp", "project", "repository", "schema", "server", "skill", "test", "workflow",
}


def is_project_request(query: str) -> bool:
    tokens = set(re.findall(r"[a-z0-9]+", query.casefold()))
    return bool(tokens & PROJECT_TERMS) or any(item["id"].casefold() in query.casefold() or item["name"].casefold() in query.casefold() for item in projects())


def _from_path_hint(value: str | None) -> dict[str, Any] | None:
    if not value:
        return None
    try:
        return identify_project(Path(value))
    except OSError:
        return None


def resolve_project(query: str, project_hint: str | None = None) -> dict[str, Any]:
    """Rank projects from compact registry and index signals; never compile several contexts."""
    if project_hint:
        try:
            project = get_project(project_hint)
            return {"project": project, "confidence": "explicit", "reason": "explicit project hint", "ambiguous": False}
        except KeyError:
            project = _from_path_hint(project_hint)
            if project:
                return {"project": project, "confidence": "explicit", "reason": "project path hint", "ambiguous": False}
    query_folded = query.casefold()
    scores: dict[str, float] = {}
    reasons: dict[str, list[str]] = {}
    for project in projects():
        score = 0.0
        hits: list[str] = []
        if project["id"].casefold() in query_folded or project["name"].casefold() in query_folded:
            score += 100
            hits.append("project name")
        for token in re.findall(r"[a-z0-9]+", f"{project['id']} {project['name']}".casefold()):
            if len(token) > 3 and token in query_folded:
                score += 5
                hits.append("registry token")
        state = load_state(project)
        for token in re.findall(r"[a-z0-9]+", state.get("summary", "").casefold()):
            if len(token) > 5 and token in query_folded:
                score += 1
        scores[project["id"]] = score
        reasons[project["id"]] = hits
    for position, result in enumerate(search(query, limit=12)):
        if result["scope"] in scores:
            # Search ordering carries useful signal; a top exact/symbol match
            # should not be outweighed by several generic matches elsewhere.
            scores[result["scope"]] += max(1, 6 - position)
            reasons[result["scope"]].append("compact registry search")
    ranked = sorted(projects(), key=lambda project: (-scores[project["id"]], project["id"]))
    if not ranked or scores[ranked[0]["id"]] <= 0:
        return {"project": None, "confidence": "none", "reason": "no compact registry signal", "ambiguous": False}
    top, runner_up = ranked[0], ranked[1] if len(ranked) > 1 else None
    ambiguous = bool(runner_up and scores[top["id"]] == scores[runner_up["id"]])
    return {"project": top, "confidence": "inferred", "reason": ", ".join(sorted(set(reasons[top["id"]]))) or "compact registry state", "ambiguous": ambiguous}


def context(query: str, project_hint: str | None = None, token_budget: int = 2200, include_handoff: bool = True) -> dict[str, Any]:
    if not is_project_request(query) and not project_hint:
        return {"activation": "not_project_related", "project": None, "context": None, "reason": "ordinary chat does not retrieve project context"}
    resolution = resolve_project(query, project_hint)
    project = resolution["project"]
    if not project:
        return {"activation": "project_related", "project": None, "context": None, "resolution": resolution, "reason": "ask for a project only if the ambiguity blocks the work"}
    if resolution["ambiguous"]:
        return {"activation": "project_related", "project": None, "context": None, "resolution": resolution, "reason": "ambiguous project resolution; no full project context loaded"}
    packet = compile_context(project["id"], query, token_budget=token_budget, include_handoff=include_handoff)
    return {"activation": "project_related", "project": project["id"], "resolution": {key: value for key, value in resolution.items() if key != "project"}, "context": packet}


def project_status(project_hint: str | None = None, query: str = "") -> dict[str, Any]:
    resolution = resolve_project(query, project_hint)
    if not resolution["project"]:
        return {"project": None, "resolution": resolution}
    packet = compile_context(resolution["project"]["id"], query or resolution["project"]["name"], token_budget=500, include_handoff=False)
    return {"project": resolution["project"]["id"], "git": packet["git"], "freshness": packet["freshness"], "summary": packet["summary"]}


def skills_match(query: str, project_hint: str | None = None) -> list[dict[str, str]]:
    resolution = resolve_project(query, project_hint)
    if not resolution["project"]:
        return []
    project = resolution["project"]
    state = load_state(project)
    return [metadata(skill) for skill in match(query, discover(Path(project["path"]), state.get("skill_roots", [])))]


def latest_project_handoff(project_hint: str | None = None, query: str = "") -> dict[str, Any] | None:
    resolution = resolve_project(query, project_hint)
    return latest_handoff(resolution["project"]["id"]) if resolution["project"] else None
