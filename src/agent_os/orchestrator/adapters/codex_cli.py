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
import tomllib
from pathlib import Path
from typing import Any

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
        usage = {"input_tokens": 0, "cached_tokens": 0, "output_tokens": 0}
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
                data = event["usage"]
                usage["input_tokens"] += int(data.get("input_tokens") or 0)
                usage["cached_tokens"] += int(data.get("cached_input_tokens") or 0)
                usage["output_tokens"] += int(data.get("output_tokens") or 0)
            elif kind in {"turn.failed", "error"}:
                error = event.get("error") if isinstance(event.get("error"), dict) else event
                errors.append(str(error.get("message") or error))
            elif kind == "item.completed" and isinstance(event.get("item"), dict):
                item = event["item"]
                if item.get("type") in {"agent_message", "assistant_message"} and item.get("text"):
                    last_agent_text = str(item["text"])
        final_text = _read_tail(handle.result_path) if handle.result_path else ""
        final_text = final_text or last_agent_text
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


def suggested_provider(executable: str | None = None) -> dict[str, Any]:
    model = configured_model()
    models = {key: model for key in ("fast", "balanced", "reasoning", "frontier")} if model else {}
    return {
        "id": "codex",
        "enabled": True,
        "adapter": CodexCliAdapter.adapter_id,
        "executable": executable or "codex",
        "models": models,
        "effort_map": dict(SUGGESTED_EFFORT_MAP),
        "max_concurrency": 2,
        "options": {"sandbox": "workspace-write", "read_only_sandbox": "read-only"},
    }
