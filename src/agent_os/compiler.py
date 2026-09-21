from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .changes import compact_changes
from .index import search
from .improvements import compact_improvements
from .paths import ROOT
from .registry import get_project, git_status, load_state
from .skills import discover, match, metadata
from .storage import load_json


def latest_handoff(project_id: str) -> dict[str, Any] | None:
    handoff_dir = ROOT / "projects" / project_id / "handoffs"
    files = sorted(handoff_dir.glob("*.json"), reverse=True) if handoff_dir.exists() else []
    return load_json(files[0]) if files else None


def _compact_state(state: dict[str, Any]) -> dict[str, Any]:
    keys = ("summary", "current_priorities", "constraints", "important_paths", "validation_commands", "updated_at")
    return {key: state[key] for key in keys if key in state}


def _compact_handoff(handoff: dict[str, Any] | None) -> dict[str, Any] | None:
    if not handoff:
        return None
    keys = ("created_at", "completed", "decisions", "remaining", "validation")
    return {key: handoff[key] for key in keys if key in handoff}


def _freshness(project: dict[str, Any], state: dict[str, Any], git: dict[str, Any]) -> dict[str, str]:
    marker = state.get("repository_marker")
    output = git.get("output", "")
    if not git.get("available"):
        return {"status": "unknown", "reason": "repository state is unavailable"}
    if marker and marker not in output:
        return {"status": "stale", "reason": "state repository marker differs from current Git state"}
    if marker:
        return {"status": "current", "reason": "state repository marker matches current Git state"}
    if "\n" in output:
        return {"status": "stale", "reason": "working tree has changes after the recorded project state"}
    return {"status": "unknown", "reason": "project state has no repository marker"}


def _compact_git(git: dict[str, Any]) -> dict[str, Any]:
    lines = git.get("output", "").splitlines()
    return {
        "available": git.get("available", False),
        "branch": lines[0] if lines else None,
        "dirty": len(lines) > 1,
        "error": git.get("error") or None,
    }


STATE_PRUNE_ORDER = ("validation_commands", "important_paths", "constraints", "updated_at", "current_priorities", "summary")


def _prune_state(value: dict[str, Any]) -> None:
    for key in STATE_PRUNE_ORDER:
        if key in value:
            del value[key]
            return
    if value:
        del value[next(iter(value))]


def _prune_development_context(value: dict[str, list[dict[str, Any]]]) -> None:
    """Shed extra entries before the single most relevant one in each stream."""
    for key in ("changes", "improvements"):
        if len(value.get(key) or []) > 1:
            value[key].pop()
            return
    for key in ("changes", "improvements"):
        if value.get(key):
            del value[key]
            return
    value.clear()


def _fit(packet: dict[str, Any], token_budget: int) -> tuple[dict[str, Any], int]:
    """Prune lowest-value context first so task-relevant material survives longest.

    Generic project bulk (the previous handoff, broad state lists) is shed before
    anything selected specifically for this task, and the top-ranked development
    context entry is the last thing to go.
    """
    limit = max(token_budget, 250) * 4
    prunable = (
        ("latest_agent_os_handoff", lambda value: value.clear()),
        ("state", _prune_state),
        ("search_matches", lambda value: value.pop()),
        ("matched_skills", lambda value: value.pop()),
        ("development_context", _prune_development_context),
    )
    for key, reduce in prunable:
        while len(json.dumps(packet, default=str, ensure_ascii=False)) > limit and packet.get(key):
            reduce(packet[key])
    if len(json.dumps(packet, default=str, ensure_ascii=False)) > limit:
        packet["task"] = packet["task"][: max(80, limit // 8)]
    return packet, limit


def compile_context(
    project_id: str,
    task: str,
    token_budget: int = 4000,
    include_handoff: bool = True,
    include_skill_content: bool = False,
) -> dict[str, Any]:
    project = get_project(project_id)
    state = load_state(project)
    project_path = Path(project["path"])
    available = discover(project_path, state.get("skill_roots", []))
    selected = match(task, available)
    selected_skills = []
    for skill in selected:
        item = metadata(skill)
        if include_skill_content:
            item["content"] = skill.path.read_text(encoding="utf-8", errors="replace")
        selected_skills.append(item)
    git = git_status(project)
    handoff = _compact_handoff(latest_handoff(project["id"])) if include_handoff else None

    development_context: dict[str, list[dict[str, Any]]] = {}
    relevant_changes = compact_changes(project["id"], task)
    relevant_improvements = compact_improvements(project["id"], task)
    if relevant_changes:
        development_context["changes"] = relevant_changes
    if relevant_improvements:
        development_context["improvements"] = relevant_improvements

    packet = {
        "project": project["id"],
        "task": task,
        "repository": project.get("repository"),
        "project_path": str(project_path),
        "git": _compact_git(git),
        "summary": state.get("summary", ""),
        "state": _compact_state(state),
        "latest_agent_os_handoff": handoff,
        "matched_skills": selected_skills,
        "search_matches": search(task, scope=project["id"], limit=6),
        "freshness": _freshness(project, state, git),
        "context_policy": {
            "token_budget": token_budget,
            "raw_history_loaded": False,
            "selection": "metadata, lexical search, compact state, matched skill metadata only",
            "full_skill_bodies_loaded": include_skill_content,
        },
    }
    if development_context:
        packet["development_context"] = development_context
    packet, limit = _fit(packet, token_budget)
    packet_chars = len(json.dumps(packet, default=str, ensure_ascii=False))
    naive_chars = sum(
        (project_path / relative).stat().st_size
        for relative in state.get("context_files", [])
        if (project_path / relative).is_file()
    ) + sum(skill.path.stat().st_size for skill in available)
    packet["context_measurement"] = {
        "estimated_packet_tokens": (packet_chars + 3) // 4,
        "token_budget": max(token_budget, 250),
        "within_budget": packet_chars <= limit,
        "naive_all_registered_context_tokens": (naive_chars + 3) // 4,
        "estimated_tokens_avoided": max((naive_chars - packet_chars) // 4, 0),
    }
    packet, limit = _fit(packet, token_budget)
    packet_chars = len(json.dumps(packet, default=str, ensure_ascii=False))
    packet["context_measurement"]["estimated_packet_tokens"] = (packet_chars + 3) // 4
    packet["context_measurement"]["within_budget"] = packet_chars <= limit
    return packet
