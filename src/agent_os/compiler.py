from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .index import search
from .paths import ROOT
from .registry import get_project, git_status, load_state
from .skills import discover, match, metadata
from .storage import load_json


def _latest_handoff(project_id: str) -> dict[str, Any] | None:
    handoff_dir = ROOT / "projects" / project_id / "handoffs"
    files = sorted(handoff_dir.glob("*.json"), reverse=True) if handoff_dir.exists() else []
    return load_json(files[0]) if files else None


def compile_context(project_id: str, task: str, token_budget: int = 4000) -> dict[str, Any]:
    project = get_project(project_id)
    state = load_state(project)
    project_path = Path(project["path"])
    available = discover(project_path, state.get("skill_roots", []))
    selected = match(task, available)
    remaining_chars = max(token_budget, 500) * 4
    selected_skills = []
    for skill in selected:
        body = skill.path.read_text(encoding="utf-8", errors="replace")
        body = body[:remaining_chars]
        remaining_chars -= len(body)
        item = metadata(skill)
        item["content"] = body
        selected_skills.append(item)
        if remaining_chars <= 0:
            break

    packet = {
        "project": project["id"],
        "task": task,
        "repository": project.get("repository"),
        "project_path": str(project_path),
        "git": git_status(project),
        "state": state,
        "latest_agent_os_handoff": _latest_handoff(project["id"]),
        "matched_skills": selected_skills,
        "search_matches": search(task, scope=project["id"], limit=6),
        "context_policy": {
            "token_budget": token_budget,
            "raw_history_loaded": False,
            "selection": "metadata, lexical search, structured state, matched skills only",
        },
    }
    packet_chars = len(json.dumps(packet, default=str))
    naive_chars = sum(
        (project_path / relative).stat().st_size
        for relative in state.get("context_files", [])
        if (project_path / relative).is_file()
    ) + sum(skill.path.stat().st_size for skill in available)
    packet["context_measurement"] = {
        "estimated_packet_tokens": (packet_chars + 3) // 4,
        "naive_all_registered_context_tokens": (naive_chars + 3) // 4,
        "estimated_tokens_avoided": max((naive_chars - packet_chars) // 4, 0),
    }
    return packet
