"""The single seam between Orchestrator OS and whatever hosts it.

Everything the engine used to import from Agent OS goes through this module:
where durable state lives, where machine-local config lives, and the optional
project-context services (project registry, context packets, handoffs,
improvement capture, cross-agent work claims).

Orchestrator OS runs on its own with the built-in ``StandaloneHost``. A host
such as Agent OS can supply richer project context by registering an object
with the same methods, either programmatically (``set_host``) or by naming it
in ``ORCHESTRATOR_HOST`` as ``module:attribute``. Orchestrator never imports a
host on its own initiative.

State roots
-----------
``ROOT`` is the *state root*: a directory (normally a Git checkout) holding the
versioned policy, evidence records and eval suites, with gitignored runtime
data under ``ROOT/.agent-local``. Resolution order:

1. ``ORCHESTRATOR_STATE_ROOT``
2. the source checkout this package was installed from (editable installs)
3. ``~/.orchestrator-os``

When ``ROOT`` is an Agent OS checkout (it has
``projects/personal-agent-os/orchestrator-os``) the legacy layout is used, so
the extracted package can read existing history in place before the data is
migrated.
"""

from __future__ import annotations

import importlib
import os
from pathlib import Path
from typing import Any

PACKAGE_DIR = Path(__file__).resolve().parent
GUI_DIR = PACKAGE_DIR / "gui"
DEFAULT_POLICY_PATH = PACKAGE_DIR / "defaults" / "orchestrator-os.policy.json"

STATE_ROOT_ENV = "ORCHESTRATOR_STATE_ROOT"
CONFIG_DIR_ENV = "ORCHESTRATOR_CONFIG_DIR"
HOST_ENV = "ORCHESTRATOR_HOST"
PROJECTS_ENV = "ORCHESTRATOR_PROJECTS"

_LEGACY_SUBDIR = Path("projects") / "personal-agent-os"


def _checkout_root() -> Path | None:
    candidate = PACKAGE_DIR.parents[1]
    pyproject = candidate / "pyproject.toml"
    try:
        if 'name = "orchestrator-os"' in pyproject.read_text(encoding="utf-8"):
            return candidate
    except OSError:
        pass
    return None


def _state_root() -> Path:
    configured = os.environ.get(STATE_ROOT_ENV)
    if configured:
        return Path(configured).expanduser().resolve()
    return _checkout_root() or (Path.home() / ".orchestrator-os")


ROOT = _state_root()
LEGACY_LAYOUT = (ROOT / _LEGACY_SUBDIR / "orchestrator-os").is_dir()

if LEGACY_LAYOUT:
    OS_DIR = ROOT / _LEGACY_SUBDIR / "orchestrator-os"
    RESEARCH_DIR = ROOT / _LEGACY_SUBDIR / "research"
    IMPROVEMENTS_DIR = ROOT / _LEGACY_SUBDIR / "improvements"
else:
    OS_DIR = ROOT / "state" / "orchestrator"
    RESEARCH_DIR = ROOT / "state" / "research"
    IMPROVEMENTS_DIR = ROOT / "state" / "improvements"

PROVIDER_POLICY_DIR = OS_DIR / "provider-policy"
if not PROVIDER_POLICY_DIR.is_dir():
    PROVIDER_POLICY_DIR = PACKAGE_DIR / "defaults" / "provider-policy"

POLICY_PATH = ROOT / "policy" / "orchestrator-os.policy.json"
if not POLICY_PATH.exists():
    POLICY_PATH = DEFAULT_POLICY_PATH

# Machine-local configuration (provider registry, budgets, foreman settings).
# The default stays ~/.agent-os so existing workstation config keeps working;
# set ORCHESTRATOR_CONFIG_DIR to separate it.
CONFIG_DIR = Path(os.environ.get(CONFIG_DIR_ENV) or (Path.home() / ".agent-os")).expanduser()


class HostCapabilityUnavailable(RuntimeError):
    """The active host does not provide an optional project-context service."""


class StandaloneHost:
    """Project context without Agent OS.

    Projects are optional. A run can always name a repository path directly.
    A small JSON registry (``ORCHESTRATOR_PROJECTS`` or
    ``<CONFIG_DIR>/orchestrator-projects.json``) can add ids, summaries,
    constraints and validation commands::

        {"projects": [{"id": "web", "path": "~/src/web",
                       "summary": "...", "constraints": ["..."],
                       "validation_commands": ["npm test"]}]}
    """

    name = "standalone"

    def _registry_path(self) -> Path:
        configured = os.environ.get(PROJECTS_ENV)
        return Path(configured).expanduser() if configured else CONFIG_DIR / "orchestrator-projects.json"

    def projects(self) -> list[dict[str, Any]]:
        import json

        path = self._registry_path()
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return []
        entries = []
        for item in data.get("projects", []):
            if not isinstance(item, dict) or not item.get("id") or not item.get("path"):
                continue
            entries.append({"name": item["id"], **item, "path": str(Path(item["path"]).expanduser()), "path_source": "orchestrator_projects"})
        return entries

    def get_project(self, project_id: str) -> dict[str, Any]:
        wanted = project_id.casefold()
        for project in self.projects():
            names = {str(project["id"]).casefold(), str(project.get("name", "")).casefold(),
                     *(str(alias).casefold() for alias in project.get("aliases", []))}
            if wanted in names:
                return project
        raise KeyError(f"Unknown project: {project_id}")

    def identify_project(self, path: Path) -> dict[str, Any] | None:
        resolved = Path(path).resolve()
        best: tuple[int, dict[str, Any] | None] = (0, None)
        for project in self.projects():
            root = Path(project["path"]).resolve()
            if resolved == root or root in resolved.parents:
                best = max(best, (len(root.parts), project), key=lambda item: item[0])
        return best[1]

    def resolve_path(self, project: dict[str, Any], roots: Any = None) -> tuple[Path, str]:
        return Path(project["path"]).expanduser(), project.get("path_source", "orchestrator_projects")

    def load_state(self, project: dict[str, Any]) -> dict[str, Any]:
        return {key: project.get(key) or [] for key in ("constraints", "validation_commands")}

    def compile_context(self, project_id: str, task: str, token_budget: int = 4000, include_handoff: bool = True, **_: Any) -> dict[str, Any]:
        project = self.get_project(project_id)
        return {"project": project["id"], "summary": project.get("summary", ""), "state": self.load_state(project),
                "context_measurement": {}}

    def latest_handoff(self, project_id: str) -> dict[str, Any] | None:
        return None

    def capture_improvement(self, project: str, **fields: Any) -> dict[str, Any]:
        # No improvement backlog without a host; the failure stays in run state.
        return {"captured": False, "reason": "standalone host has no improvement backlog"}

    def claim(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        raise HostCapabilityUnavailable("work claims need a coordinating host")

    def release(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        raise HostCapabilityUnavailable("work claims need a coordinating host")

    def economy(self) -> Any:
        raise HostCapabilityUnavailable("context-economy benchmarks need the Agent OS host")


_host: Any = None


def _load(spec: str) -> Any:
    module_name, _, attribute = spec.partition(":")
    target = importlib.import_module(module_name)
    return getattr(target, attribute) if attribute else target


def get_host() -> Any:
    global _host
    if _host is None:
        spec = os.environ.get(HOST_ENV)
        _host = _load(spec) if spec else StandaloneHost()
    return _host


def set_host(host: Any) -> Any:
    """Install a host object; returns the previous one. ``None`` resets."""
    global _host
    previous, _host = _host, host
    return previous


# Module-level forwarders: call sites read like the Agent OS functions they replaced.
def projects() -> list[dict[str, Any]]:
    return get_host().projects()


def get_project(project_id: str) -> dict[str, Any]:
    return get_host().get_project(project_id)


def identify_project(path: Path) -> dict[str, Any] | None:
    return get_host().identify_project(path)


def resolve_path(project: dict[str, Any], roots: Any = None) -> tuple[Path, str]:
    return get_host().resolve_path(project, roots)


def load_state(project: dict[str, Any]) -> dict[str, Any]:
    return get_host().load_state(project)


def compile_context(project_id: str, task: str, **kwargs: Any) -> dict[str, Any]:
    return get_host().compile_context(project_id, task, **kwargs)


def latest_handoff(project_id: str) -> dict[str, Any] | None:
    return get_host().latest_handoff(project_id)


def capture_improvement(project: str, **fields: Any) -> dict[str, Any]:
    return get_host().capture_improvement(project, **fields)


def claim(*args: Any, **kwargs: Any) -> dict[str, Any]:
    return get_host().claim(*args, **kwargs)


def release(*args: Any, **kwargs: Any) -> dict[str, Any]:
    return get_host().release(*args, **kwargs)


def economy() -> Any:
    return get_host().economy()
