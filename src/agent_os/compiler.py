from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .changes import compact_changes
from .index import search
from .improvements import compact_improvements
from .profile import compact_profile
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


HANDOFF_BULK_PRUNE_ORDER = ("completed", "validation", "created_at")
HANDOFF_ACTIONABLE_PRUNE_ORDER = ("decisions", "remaining")


def _prune_handoff_bulk(value: dict[str, Any]) -> bool:
    """Shed the previous handoff's narrative, never its next action.

    A handoff records what was finished as well as what is still open. The
    finished narrative is the verbose history a fresh task rarely needs, while
    the open decisions and remaining work are the next action itself. Only the
    narrative is generic bulk, so only the narrative is shed at this stage.
    """
    for key in HANDOFF_BULK_PRUNE_ORDER:
        if key in value:
            del value[key]
            return True
    return False


def _prune_handoff_actionable(value: dict[str, Any]) -> bool:
    """Last resort: give up recent decisions before the remaining work."""
    for key in HANDOFF_ACTIONABLE_PRUNE_ORDER:
        if key in value:
            del value[key]
            return True
    if value:
        value.clear()
        return True
    return False


def _reduce_profile(value: dict[str, Any]) -> bool:
    """Shed the least relevant profile fact first; selection order is by score."""
    facts = value.get("facts") or []
    if not facts:
        return False
    facts.pop()
    value.setdefault("diagnostics", {})["selected"] = len(facts)
    return True


def _reduce_list(value: list[Any]) -> bool:
    if not value:
        return False
    value.pop()
    return True


def _reduce_state(value: dict[str, Any]) -> bool:
    if not value:
        return False
    _prune_state(value)
    return True


def _reduce_development_context(value: dict[str, Any]) -> bool:
    if not value:
        return False
    _prune_development_context(value)
    return True


def _fit(packet: dict[str, Any], token_budget: int) -> tuple[dict[str, Any], int]:
    """Prune by usefulness, not by source order, so actionable context survives.

    Verbose history goes first and the task's own next action goes last. The
    previous handoff is graded rather than dropped whole: its finished narrative
    is generic bulk, but its open decisions and remaining work rank alongside the
    development context selected for this task, so they are shed only after
    broad state, lexical matches, and skill metadata have already gone.
    """
    limit = max(token_budget, 250) * 4
    prunable = (
        ("latest_agent_os_handoff", _prune_handoff_bulk),
        ("state", _reduce_state),
        ("search_matches", _reduce_list),
        ("profile_context", _reduce_profile),
        ("matched_skills", _reduce_list),
        ("development_context", _reduce_development_context),
        ("latest_agent_os_handoff", _prune_handoff_actionable),
    )
    for key, reduce in prunable:
        while len(json.dumps(packet, default=str, ensure_ascii=False)) > limit:
            section = packet.get(key)
            if section is None or not reduce(section):
                break
    # A profile slice pruned down to no facts is pure overhead: the diagnostics
    # shell costs bytes and says nothing. Drop the section, not just its facts.
    if isinstance(packet.get("profile_context"), dict) and not packet["profile_context"].get("facts"):
        packet.pop("profile_context", None)
    # Under extreme pressure the remaining core is still not all equal value.
    # A static description of the selection strategy and the project's generic
    # summary rank below the task itself, so they go before the task is cut.
    if len(json.dumps(packet, default=str, ensure_ascii=False)) > limit:
        policy = packet.get("context_policy")
        if isinstance(policy, dict):
            policy.pop("selection", None)
    if len(json.dumps(packet, default=str, ensure_ascii=False)) > limit:
        packet["summary"] = ""
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
    selected = match(task, available, minimum_score=2)
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
    profile_slice = compact_profile(task)
    if profile_slice["facts"]:
        packet["profile_context"] = profile_slice
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
