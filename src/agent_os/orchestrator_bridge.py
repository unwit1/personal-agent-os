"""Which Orchestrator implementation Agent OS drives.

During the extraction to the standalone ``orchestrator-os`` package
(docs/adr/0001-orchestrator-os-extraction.md) Agent OS keeps a single
switch instead of two engines wired into its surfaces:

- ``AGENT_OS_ORCHESTRATOR_BACKEND=internal`` (default until cutover):
  the in-tree ``agent_os.orchestrator`` package, unchanged.
- ``AGENT_OS_ORCHESTRATOR_BACKEND=external``: the installed
  ``orchestrator_os`` package, with Agent OS supplying project context
  through ``agent_os.orchestrator_host``. Existing runs stay visible because
  the run store keeps its old location unless ``AGENT_OS_ORCHESTRATOR_HOME``
  says otherwise.

CLI, MCP and the Executive window import ``cli``, ``service`` and ``simple``
from here, so the switch changes every surface at once.
"""

from __future__ import annotations

import importlib
import os
from types import ModuleType

from .paths import ROOT

BACKEND_ENV = "AGENT_OS_ORCHESTRATOR_BACKEND"


class OrchestratorUnavailable(ImportError):
    pass


def backend() -> str:
    value = (os.environ.get(BACKEND_ENV) or "internal").strip().lower()
    if value not in {"internal", "external"}:
        raise ValueError(f"{BACKEND_ENV} must be 'internal' or 'external', not {value!r}")
    return value


def _external(name: str) -> ModuleType:
    os.environ.setdefault("AGENT_OS_ORCHESTRATOR_HOME", str(ROOT / ".agent-local" / "orchestrator"))
    try:
        host = importlib.import_module("orchestrator_os.host")
    except ImportError as exc:
        raise OrchestratorUnavailable(
            "AGENT_OS_ORCHESTRATOR_BACKEND=external but the orchestrator-os package is not installed. "
            "Install it with `pip install -e <orchestrator-os checkout>` or unset the variable."
        ) from exc
    from .orchestrator_host import HOST

    if not isinstance(host.get_host(), type(HOST)):
        host.set_host(HOST)
    return importlib.import_module(f"orchestrator_os.{name}")


def module(name: str) -> ModuleType:
    """``cli``, ``service``, ``simple`` ... of the selected backend."""
    if backend() == "external":
        return _external(name)
    return importlib.import_module(f"agent_os.orchestrator.{name}")
