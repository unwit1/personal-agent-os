"""In-process synthetic coding agent for tests, demos, and dry runs.

It behaves like a real adapter from the scheduler's point of view -- it is
launched, polled for a configurable number of ticks, may edit its worktree,
and returns a structured result or a classified failure -- but it never calls
a model. Behaviour is scripted per provider through ``SCRIPTS``.
"""

from __future__ import annotations

import itertools
import time
from pathlib import Path
from typing import Any, Callable

from ...timestamps import utc_now_iso
from .base import AgentLaunchRequest, AgentProcessStatus, AgentResult, InvocationPlan, ProviderStatus, RunningAgent


Script = Callable[[AgentLaunchRequest, int], dict[str, Any]]
SCRIPTS: dict[str, Script] = {}
_CALLS: dict[str, int] = {}
_LIVE: dict[str, dict[str, Any]] = {}
_TOKENS = itertools.count(1)


def reset() -> None:
    SCRIPTS.clear()
    _CALLS.clear()
    _LIVE.clear()


def default_script(request: AgentLaunchRequest, call: int) -> dict[str, Any]:
    if request.role == "planner":
        return {"structured": {"status": "done", "tasks": [{"id": "implement", "goal": "Implement the goal", "role": "implementer"}]}}
    if request.role == "reviewer":
        return {"structured": {"status": "done", "verdict": "approved", "findings": []}}
    target = f"synthetic/{request.node_id}.txt"
    return {
        "edits": {target: f"synthetic change by {request.node_id} (call {call})\n"},
        "structured": {"status": "done", "summary": f"edited {target}", "outputs": [target]},
    }


class SyntheticAdapter:
    adapter_id = "synthetic"
    adapter_version = "synthetic/1"

    def __init__(self, provider: dict[str, Any]) -> None:
        self.provider = provider

    def probe(self) -> ProviderStatus:
        options = self.provider.get("options", {})
        if options.get("unavailable"):
            return ProviderStatus(self.provider["id"], False, reason="synthetic provider marked unavailable")
        return ProviderStatus(self.provider["id"], True, executable="<in-process>", version=self.adapter_version)

    def resolve_invocation(self, request: AgentLaunchRequest) -> InvocationPlan:
        return InvocationPlan(
            executable="<in-process>",
            argv=["--model", request.model, "--effort", str(request.provider_effort)],
            cwd=request.cwd,
            env={},
            stdin_path=request.prompt_path,
            provider=self.provider["id"],
            model=request.model,
            effort=request.provider_effort,
            adapter_version=self.adapter_version,
            display=f"synthetic --model {request.model} --effort {request.provider_effort}",
        )

    def start(self, request: AgentLaunchRequest) -> RunningAgent:
        plan = self.resolve_invocation(request)
        provider_id = self.provider["id"]
        _CALLS[provider_id] = _CALLS.get(provider_id, 0) + 1
        script = SCRIPTS.get(self.provider.get("options", {}).get("script", provider_id), default_script)
        behaviour = dict(script(request, _CALLS[provider_id]) or {})
        token = f"synthetic-{next(_TOKENS)}"
        _LIVE[token] = {"request": request, "behaviour": behaviour, "ticks": int(behaviour.get("ticks", 0)), "cancelled": False}
        out = Path(request.output_dir)
        out.mkdir(parents=True, exist_ok=True)
        (out / "invocation.txt").write_text(plan.display + "\n", encoding="utf-8")
        return RunningAgent(
            provider_id=provider_id,
            node_id=request.node_id,
            pid=None,
            started_monotonic=time.monotonic(),
            started_at=utc_now_iso(),
            stdout_path=str(out / "stdout.log"),
            stderr_path=str(out / "stderr.log"),
            result_path=None,
            display=plan.display,
            token=token,
        )

    def poll(self, handle: RunningAgent) -> AgentProcessStatus:
        live = _LIVE.get(handle.token or "")
        if live is None:
            # The in-process "process" died with the engine that started it.
            return AgentProcessStatus(running=False, returncode=None)
        if live["cancelled"]:
            return AgentProcessStatus(running=False, returncode=-1)
        if live["ticks"] > 0:
            live["ticks"] -= 1
            return AgentProcessStatus(running=True)
        return AgentProcessStatus(running=False, returncode=0)

    def cancel(self, handle: RunningAgent) -> None:
        live = _LIVE.get(handle.token or "")
        if live is not None:
            live["cancelled"] = True

    def collect(self, handle: RunningAgent) -> AgentResult:
        live = _LIVE.pop(handle.token or "", None)
        if live is None:
            return AgentResult(outcome="failed", failure_kind="interrupted", detail="synthetic worker was lost")
        if live["cancelled"]:
            return AgentResult(outcome="failed", failure_kind="cancelled", detail="cancelled")
        behaviour = live["behaviour"]
        request: AgentLaunchRequest = live["request"]
        if behaviour.get("failure"):
            partial = behaviour.get("partial_edits") or {}
            if partial and not request.read_only:
                _apply(request.cwd, partial)
            return AgentResult(outcome="failed", failure_kind=str(behaviour["failure"]), detail=str(behaviour.get("detail") or behaviour["failure"]))
        if not request.read_only:
            _apply(request.cwd, behaviour.get("edits") or {})
        structured = behaviour.get("structured")
        summary = str(behaviour.get("summary") or (structured or {}).get("summary") or "synthetic worker finished")
        usage = behaviour.get("usage") or {"input_tokens": 100, "output_tokens": 20}
        return AgentResult(outcome="completed", summary=summary, structured=structured, usage=usage, duration_ms=1)


def _apply(cwd: str, edits: dict[str, str | None]) -> None:
    root = Path(cwd)
    for relative, content in edits.items():
        target = root / relative
        if content is None:
            if target.exists():
                target.unlink()
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8", newline="\n")
