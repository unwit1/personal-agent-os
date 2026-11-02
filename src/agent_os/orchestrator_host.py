"""Agent OS as a host for the standalone Orchestrator OS package.

Orchestrator OS (``orchestrator_os``) asks its host for project context
through ``orchestrator_os.host``. This object answers from Agent OS's project
registry, context compiler, handoffs, improvement backlog and work claims.

Select it with ``ORCHESTRATOR_HOST=agent_os.orchestrator_host:HOST`` or
``orchestrator_os.host.set_host(HOST)``. This module is the only place Agent
OS business logic meets the orchestrator; the orchestrator never imports
Agent OS itself.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


class AgentOSHost:
    name = "agent_os"

    def projects(self) -> list[dict[str, Any]]:
        from .registry import projects

        return projects()

    def get_project(self, project_id: str) -> dict[str, Any]:
        from .registry import get_project

        return get_project(project_id)

    def identify_project(self, path: Path) -> dict[str, Any] | None:
        from .registry import identify_project

        return identify_project(Path(path))

    def resolve_path(self, project: dict[str, Any], roots: Any = None) -> tuple[Path, str]:
        from .machine import resolve_path

        return resolve_path(project, roots)

    def load_state(self, project: dict[str, Any]) -> dict[str, Any]:
        from .registry import load_state

        return load_state(project)

    def compile_context(self, project_id: str, task: str, **kwargs: Any) -> dict[str, Any]:
        from .compiler import compile_context

        return compile_context(project_id, task, **kwargs)

    def latest_handoff(self, project_id: str) -> dict[str, Any] | None:
        from .compiler import latest_handoff

        return latest_handoff(project_id)

    def capture_improvement(self, project: str, **fields: Any) -> dict[str, Any]:
        from .improvements import capture_improvement

        return capture_improvement(project, **fields)

    def claim(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        from .coordination import claim

        return claim(*args, **kwargs)

    def release(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        from .coordination import release

        return release(*args, **kwargs)

    def economy(self) -> Any:
        from . import economy

        return economy


HOST = AgentOSHost()
