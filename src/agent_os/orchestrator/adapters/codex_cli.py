"""Codex CLI adapter.

Verified against the installed CLI's ``codex exec --help`` (0.155.x):
``exec`` runs non-interactively and reads the prompt from stdin when the prompt
argument is ``-``; ``-m`` selects the model; reasoning effort is a config value
(``-c model_reasoning_effort=...``); ``-s`` selects the sandbox; ``-C`` sets
the working root; ``--json`` streams JSONL events; ``-o`` writes the final
message to a file; ``--ephemeral`` avoids persisting session files.
"""

from __future__ import annotations

import json
import re
import tomllib
from pathlib import Path
from typing import Any

from ..usage import from_codex_turns
from .base import (
    AgentLaunchRequest,
    AgentResult,
    InvocationPlan,
    RunningAgent,
    SubprocessAdapter,
    _read_tail,
    build_env,
    classify_failure,
    extract_structured,
)


SUGGESTED_EFFORT_MAP = {"none": "low", "low": "low", "medium": "medium", "high": "high"}
# Relative cost weights per capability class; data the operator may edit.
SUGGESTED_COSTS = {"fast": 1, "balanced": 3, "reasoning": 6, "frontier": 10}
# Codex model families, cheapest first. A catalog slug such as
# ``gpt-6-luna`` is ``gpt-<version>-<family>``.
FAMILY_CLASSES = {"luna": "fast", "terra": "balanced", "sol": "reasoning", "astra": "frontier"}
_SLUG = re.compile(r"^gpt-(?P<version>\d+(?:\.\d+)*)-(?P<family>[a-z]+)$")
# Logged by the Windows restricted-token sandbox when it cannot confine
# commands to the workspace (for example, a workspace nested inside %TEMP%).
SANDBOX_REFUSAL = "cannot enforce split writable root sets"
# `codex exec --json` item types that are tool invocations, counted per worker.
TOOL_ITEM_TYPES = frozenset({"command_execution", "mcp_tool_call", "file_change", "web_search"})
OPTIONAL_FLAGS = ("--json", "--output-last-message", "--ephemeral", "--sandbox", "--cd", "--skip-git-repo-check")


class CodexCliAdapter(SubprocessAdapter):
    adapter_id = "codex_cli"
    adapter_version = "codex_cli/1"
    default_executable = "codex"
    env_prefixes = ("OPENAI_", "CODEX_", "AZURE_OPENAI_")

    def probe_features(self, executable: str) -> dict[str, bool]:
        _, help_text = self._run_quick([executable, "exec", "--help"])
        return {flag: flag in help_text for flag in OPTIONAL_FLAGS}

    def resolve_invocation(self, request: AgentLaunchRequest) -> InvocationPlan:
        status = self.probe()
        if not status.available or not status.executable:
            raise RuntimeError(f"{self.provider['id']} is unavailable: {status.reason}")
        features = status.features
        options = self.provider.get("options", {})
        result_path = str(Path(request.output_dir) / "last-message.md")
        argv = ["exec", "-m", request.model]
        keep = options.get("keep_mcp_servers")
        if keep is not True:
            # A bounded worker gets everything it needs in its prompt; the
            # operator's MCP servers (mail, Agent OS, ...) would only add turns
            # and reach beyond the worktree.
            for name in configured_mcp_servers():
                if not isinstance(keep, list) or name not in keep:
                    argv += ["-c", f"mcp_servers.{name}.enabled=false"]
        if request.provider_effort:
            argv += ["-c", f'model_reasoning_effort="{request.provider_effort}"']
        if features.get("--sandbox"):
            sandbox = options.get("read_only_sandbox", "read-only") if request.read_only else options.get("sandbox", "workspace-write")
            argv += ["-s", sandbox]
        if features.get("--cd"):
            argv += ["-C", request.cwd]
        if features.get("--json"):
            argv.append("--json")
        if features.get("--output-last-message"):
            argv += ["-o", result_path]
        if features.get("--ephemeral") and options.get("persist_sessions") is not True:
            argv.append("--ephemeral")
        argv.append("-")
        display = " ".join(["codex", *argv]) + " < prompt.md"
        return InvocationPlan(
            executable=status.executable,
            argv=argv,
            cwd=request.cwd,
            env=build_env(self.provider.get("env_allowlist", []), request.env_allowlist, self.env_prefixes),
            stdin_path=request.prompt_path,
            provider=self.provider["id"],
            model=request.model,
            effort=request.provider_effort,
            adapter_version=self.adapter_version,
            display=display,
            result_path=result_path if features.get("--output-last-message") else None,
        )

    def parse_result(self, handle: RunningAgent, returncode: int | None, stdout: str, stderr: str) -> AgentResult:
        turns: list[dict] = []
        tool_calls = 0
        errors: list[str] = []
        last_agent_text = ""
        for line in stdout.splitlines():
            line = line.strip()
            if not line.startswith("{"):
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            kind = str(event.get("type", ""))
            if kind == "turn.completed" and isinstance(event.get("usage"), dict):
                turns.append(event["usage"])
            elif kind in {"turn.failed", "error"}:
                error = event.get("error") if isinstance(event.get("error"), dict) else event
                errors.append(str(error.get("message") or error))
            elif kind == "item.completed" and isinstance(event.get("item"), dict):
                item = event["item"]
                if item.get("type") in {"agent_message", "assistant_message"} and item.get("text"):
                    last_agent_text = str(item["text"])
                elif item.get("type") in TOOL_ITEM_TYPES:
                    tool_calls += 1
        usage = from_codex_turns(turns, tool_calls)
        final_text = _read_tail(handle.result_path) if handle.result_path else ""
        final_text = final_text or last_agent_text
        if SANDBOX_REFUSAL in stderr:
            # The model "finishes" politely, but it could not run a single
            # command; that is a provider/environment failure, so the node can
            # fail over instead of opening a pointless decision gate.
            return AgentResult(
                outcome="failed",
                failure_kind="unavailable",
                summary=final_text[-600:],
                usage=usage,
                detail="codex sandbox refused to run in this worktree (on Windows, keep worktrees outside %TEMP%)",
            )
        if errors or returncode not in (0, None):
            text = "\n".join(errors) or stderr or f"exit code {returncode}"
            return AgentResult(
                outcome="failed",
                failure_kind=classify_failure(text + "\n" + stderr, returncode),
                summary=final_text[-600:],
                usage=usage,
                detail=text[:400],
            )
        if not final_text.strip():
            return self.failed("malformed", "codex produced no final message")
        return AgentResult(outcome="completed", summary=final_text[-600:], structured=extract_structured(final_text), usage=usage)


def configured_model(config_path: Path | None = None) -> str | None:
    path = config_path or Path.home() / ".codex" / "config.toml"
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError):
        return None
    model = data.get("model")
    return str(model) if model else None


def configured_mcp_servers(config_path: Path | None = None) -> list[str]:
    path = config_path or Path.home() / ".codex" / "config.toml"
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError):
        return []
    servers = data.get("mcp_servers")
    return sorted(name for name in servers if re.fullmatch(r"[A-Za-z0-9_-]+", name)) if isinstance(servers, dict) else []


def discover_models(cache_path: Path | None = None) -> dict[str, str]:
    """Map capability classes to the newest listed Codex model of each family.

    Reads the model catalog the Codex CLI caches locally (no network, no model
    call). Hidden models are ignored. A class with no matching family is left
    out; the router then falls back to the nearest covered class.
    """
    path = cache_path or Path.home() / ".codex" / "models_cache.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    best: dict[str, tuple[tuple[int, ...], str]] = {}
    for item in data.get("models") or []:
        if not isinstance(item, dict) or item.get("visibility", "list") != "list" or item.get("supported_in_api") is False:
            continue
        match = _SLUG.match(str(item.get("slug") or ""))
        if not match or match["family"] not in FAMILY_CLASSES:
            continue
        capability = FAMILY_CLASSES[match["family"]]
        version = tuple(int(part) for part in match["version"].split("."))
        if capability not in best or version > best[capability][0]:
            best[capability] = (version, match.group(0))
    return {capability: slug for capability, (_, slug) in best.items()}


def suggested_provider(executable: str | None = None) -> dict[str, Any]:
    models = discover_models()
    if not models:
        model = configured_model()
        models = {key: model for key in ("fast", "balanced", "reasoning", "frontier")} if model else {}
    return {
        "id": "codex",
        "enabled": True,
        "adapter": CodexCliAdapter.adapter_id,
        "executable": executable or "codex",
        "discover": True,
        "models": models,
        "costs": dict(SUGGESTED_COSTS),
        "effort_map": dict(SUGGESTED_EFFORT_MAP),
        "max_concurrency": 6,
        "tier_concurrency": {"reasoning": 2, "frontier": 1},
        "options": {"sandbox": "workspace-write", "read_only_sandbox": "read-only"},
    }
