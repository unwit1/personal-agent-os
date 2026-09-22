"""Provider adapters. The only place provider-specific CLI syntax may live.

A provider entry in the machine-local registry names its adapter by ID; the
core looks adapters up here and never imports a vendor module directly. A new
coding CLI is added by writing one adapter module and registering it below --
the scheduler does not change.
"""

from __future__ import annotations

from typing import Any, Callable

from .base import (
    AgentLaunchRequest,
    AgentProcessStatus,
    AgentResult,
    CodingAgentAdapter,
    InvocationPlan,
    ProviderStatus,
    RunningAgent,
)
from .claude_code import ClaudeCodeAdapter
from .claude_code import suggested_provider as _claude_code_suggestion
from .codex_cli import CodexCliAdapter
from .codex_cli import suggested_provider as _codex_cli_suggestion
from .synthetic import SyntheticAdapter


ADAPTERS: dict[str, Callable[[dict[str, Any]], CodingAgentAdapter]] = {
    ClaudeCodeAdapter.adapter_id: ClaudeCodeAdapter,
    CodexCliAdapter.adapter_id: CodexCliAdapter,
    SyntheticAdapter.adapter_id: SyntheticAdapter,
}

SUGGESTIONS: dict[str, Callable[[str | None], dict[str, Any]]] = {
    ClaudeCodeAdapter.adapter_id: _claude_code_suggestion,
    CodexCliAdapter.adapter_id: _codex_cli_suggestion,
}


class UnknownAdapter(KeyError):
    pass


def get_adapter(provider: dict[str, Any]) -> CodingAgentAdapter:
    adapter_id = provider.get("adapter")
    factory = ADAPTERS.get(str(adapter_id))
    if factory is None:
        raise UnknownAdapter(f"provider {provider.get('id')} names unknown adapter {adapter_id!r}")
    return factory(provider)


def suggested_registry() -> dict[str, Any]:
    """Probe installed CLIs and suggest a registry entry for each one found.

    Suggestions are data for the operator to review; nothing here is written
    unless the caller chooses to write it.
    """
    providers = []
    for adapter_id, suggest in SUGGESTIONS.items():
        entry = suggest(None)
        status = ADAPTERS[adapter_id](entry).probe()
        entry["enabled"] = bool(status.available)
        entry["_probe"] = status.as_dict()
        providers.append(entry)
    return {"providers": providers}


__all__ = [
    "ADAPTERS",
    "AgentLaunchRequest",
    "AgentProcessStatus",
    "AgentResult",
    "CodingAgentAdapter",
    "InvocationPlan",
    "ProviderStatus",
    "RunningAgent",
    "UnknownAdapter",
    "get_adapter",
    "suggested_registry",
]
