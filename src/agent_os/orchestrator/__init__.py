"""Multi-agent coding orchestrator (P1.2A).

The orchestrator coordinates local coding-agent CLIs as independent workers on
one larger task. The core -- run model, scheduler, router, worktree manager,
validators, review coordinator, integration and the auto-continue controller --
is provider-neutral: it asks for a capability class and an effort, and a
provider adapter translates that into a concrete command line. Vendor names and
CLI syntax live only in ``agent_os.orchestrator.adapters``.

Every surface (CLI, MCP, local HTTP API, GUI) drives the same engine in
``engine.Orchestrator``; the GUI holds no orchestration policy.
"""

from .engine import Orchestrator

__all__ = ["Orchestrator"]
