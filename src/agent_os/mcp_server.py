from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Callable

from .compiler import compile_context
from .handoffs import create_handoff
from .index import search
from .registry import get_project, git_status, identify_project, load_state, projects
from .skills import discover, match, metadata


def methods() -> dict[str, Callable[..., Any]]:
    return {
        "project.list": lambda: projects(),
        "project.identify": lambda path: identify_project(Path(path)),
        "project.status": lambda project: {"state": load_state(get_project(project)), "git": git_status(get_project(project))},
        "project.context": compile_context,
        "memory.search": search,
        "skill.search": lambda query, project=None: [
            metadata(skill)
            for skill in match(
                query,
                discover(
                    Path(get_project(project)["path"]) if project else None,
                    load_state(get_project(project)).get("skill_roots", []) if project else (),
                ),
            )
        ],
        "agent.start_session": compile_context,
        "agent.finish_session": create_handoff,
    }


def serve() -> int:
    available = methods()
    for line in sys.stdin:
        try:
            request = json.loads(line)
            method = request.get("method")
            if method == "rpc.discover":
                result = sorted(available)
            elif method not in available:
                raise KeyError(f"Unknown method: {method}")
            else:
                params = request.get("params", {})
                result = available[method](**params) if isinstance(params, dict) else available[method](*params)
            response = {"jsonrpc": "2.0", "id": request.get("id"), "result": result}
        except Exception as exc:
            response = {"jsonrpc": "2.0", "id": None, "error": {"code": -32000, "message": str(exc)}}
        print(json.dumps(response, default=str), flush=True)
    return 0
