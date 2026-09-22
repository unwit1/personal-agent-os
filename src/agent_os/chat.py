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


def _normalize(value: str) -> str:
    """Fold punctuation so `JSON RPC`, `json-rpc` and `JSON_RPC` compare equal."""
    return f" {re.sub(r'[^a-z0-9]+', ' ', value.casefold()).strip()} "


def routing_terms(project: dict[str, Any]) -> list[str]:
    return [str(term) for term in project.get("routing_terms", []) if str(term).strip()]


def _term_hits(normalized_query: str, terms: list[str]) -> list[str]:
    return sorted({term for term in terms if _normalize(term).strip() and _normalize(term) in normalized_query})


def is_project_request(query: str) -> bool:
    tokens = set(re.findall(r"[a-z0-9]+", query.casefold()))
    if tokens & PROJECT_TERMS:
        return True
    normalized = _normalize(query)
    for item in projects():
        if _normalize(item["id"]) in normalized or _normalize(item["name"]) in normalized:
            return True
        if _term_hits(normalized, routing_terms(item)):
            return True
    return False


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
    normalized_query = _normalize(query)
    scores: dict[str, float] = {}
    reasons: dict[str, list[str]] = {}
    domain_hits: dict[str, int] = {}
    routable = [project for project in projects() if not project.get("redirect_to")]
    for project in routable:
        score = 0.0
        hits: list[str] = []
        if project["id"].casefold() in query_folded or project["name"].casefold() in query_folded:
            score += 100
            hits.append("project name")
        for alias in project.get("aliases", []):
            if alias.casefold() in query_folded:
                score += 80
                hits.append("project alias")
        matched_terms = _term_hits(normalized_query, routing_terms(project))
        domain_hits[project["id"]] = len(matched_terms)
        if matched_terms:
            score += 20 * len(matched_terms)
            hits.append("domain term")
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
    ranked = sorted(routable, key=lambda project: (-scores[project["id"]], project["id"]))
    if not ranked or scores[ranked[0]["id"]] <= 0:
        return {"project": None, "confidence": "none", "reason": "no compact registry signal", "ambiguous": False}
    top, runner_up = ranked[0], ranked[1] if len(ranked) > 1 else None
    query_terms = re.findall(r"[a-z0-9]+", query_folded)
    strong_reasons = {"project name", "project alias"}
    top_reasons = set(reasons[top["id"]])
    if len(query_terms) <= 1 and not strong_reasons.intersection(top_reasons):
        return {"project": None, "confidence": "none", "reason": "single weak routing signal", "ambiguous": False}
    # Lexical index overlap alone routes generic coding questions into whichever
    # project happens to mention the same common words, so a distinctive signal
    # is required: an explicit name/alias, or registered domain vocabulary.
    hits = domain_hits.get(top["id"], 0)
    distinctive = bool(strong_reasons.intersection(top_reasons)) or hits >= 2 or (hits == 1 and len(top_reasons) > 1)
    if not distinctive:
        return {"project": None, "confidence": "none", "reason": "no distinctive project signal", "ambiguous": False}
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
    result = {"activation": "project_related", "project": project["id"], "resolution": {key: value for key, value in resolution.items() if key != "project"}, "context": packet}

    # Who else is working here, surfaced without being asked.
    #
    # On 2026-09-22 two agents worked one repository within the same hour. The
    # second landed eight commits while the first was measuring a corpus, and
    # the first nearly attributed the resulting regression to its own change.
    # Neither had any way to see the other. A preflight that reports project
    # context but not the colleague editing it is describing an empty room.
    from .coordination import active_claims

    try:
        others = active_claims(project["id"])
    except Exception:  # noqa: BLE001 - coordination must never block retrieval
        others = []
    if others:
        result["active_work"] = {
            "warning": "another agent has announced work on this project",
            "claims": [
                {
                    "claim_id": item["claim_id"],
                    "agent": item["agent"],
                    "task": item["task"],
                    "scope": item["scope"],
                    "since": item["created_at"],
                }
                for item in others
            ],
            "advice": "check scope overlap before editing; message them rather than racing",
        }
    return result


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
