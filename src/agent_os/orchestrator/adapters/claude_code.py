"""Claude Code CLI adapter.

Verified against the installed CLI's ``--help`` (2.1.x): non-interactive
``-p/--print`` reading the prompt from stdin, ``--output-format json`` for a
single result object, ``--model``, ``--effort``, ``--permission-mode``,
``--permission-prompts``, ``--allowedTools`` and ``--no-session-persistence``.
Optional flags are only passed when the probed ``--help`` advertises them, so
an older or newer CLI fails clearly instead of silently misbehaving.
"""

from __future__ import annotations

import json
from typing import Any

from .base import (
    AgentLaunchRequest,
    AgentResult,
    InvocationPlan,
    RunningAgent,
    SubprocessAdapter,
    build_env,
    classify_failure,
    extract_structured,
)


# Aliases track the newest model in each tier, so this suggestion stays
# current without a code change. The registry (data) is authoritative.
SUGGESTED_MODELS = {"fast": "haiku", "balanced": "sonnet", "reasoning": "opus", "frontier": "fable"}
SUGGESTED_EFFORT_MAP = {"none": "low", "low": "low", "medium": "medium", "high": "high"}
OPTIONAL_FLAGS = ("--effort", "--permission-mode", "--permission-prompts", "--no-session-persistence", "--allowedTools")


class ClaudeCodeAdapter(SubprocessAdapter):
    adapter_id = "claude_code"
    adapter_version = "claude_code/1"
    default_executable = "claude"
    env_prefixes = ("ANTHROPIC_", "CLAUDE_", "AWS_", "GOOGLE_", "CLOUD_ML_", "VERTEX_")

    def probe_features(self, executable: str) -> dict[str, bool]:
        _, help_text = self._run_quick([executable, "--help"])
        return {flag: flag in help_text for flag in OPTIONAL_FLAGS}

    def resolve_invocation(self, request: AgentLaunchRequest) -> InvocationPlan:
        status = self.probe()
        if not status.available or not status.executable:
            raise RuntimeError(f"{self.provider['id']} is unavailable: {status.reason}")
        features = status.features
        options = self.provider.get("options", {})
        argv = ["-p", "--output-format", "json", "--model", request.model]
        if request.provider_effort and features.get("--effort"):
            argv += ["--effort", request.provider_effort]
        if features.get("--permission-mode"):
            mode = options.get("read_only_permission_mode", "plan") if request.read_only else options.get("permission_mode", "acceptEdits")
            argv += ["--permission-mode", mode]
        if features.get("--permission-prompts"):
            # Nobody is at the keyboard of a headless worker: anything that
            # would prompt is denied rather than hanging the run.
            argv += ["--permission-prompts", "none"]
        if features.get("--no-session-persistence") and options.get("persist_sessions") is not True:
            argv.append("--no-session-persistence")
        tools = request.allowed_tools or options.get("allowed_tools") or []
        if tools and features.get("--allowedTools"):
            argv += ["--allowedTools", ",".join(tools)]
        display = " ".join(["claude", *argv]) + " < prompt.md"
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
        )

    def parse_result(self, handle: RunningAgent, returncode: int | None, stdout: str, stderr: str) -> AgentResult:
        payload = _last_json_object(stdout)
        if payload is None:
            text = (stderr or stdout or "").strip()
            if returncode not in (0, None) or text:
                return self.failed(classify_failure(text, returncode), text or f"exit code {returncode}")
            return self.failed("malformed", "no JSON result on stdout")
        final_text = str(payload.get("result") or "")
        usage = payload.get("usage") if isinstance(payload.get("usage"), dict) else {}
        usage_counts = {
            "input_tokens": int(usage.get("input_tokens") or 0),
            "cached_tokens": int(usage.get("cache_read_input_tokens") or 0),
            "output_tokens": int(usage.get("output_tokens") or 0),
        }
        if payload.get("is_error") or str(payload.get("subtype", "success")) != "success" or returncode not in (0, None):
            text = final_text or str(payload.get("subtype") or stderr)
            return AgentResult(
                outcome="failed",
                failure_kind=classify_failure(text + "\n" + stderr, returncode),
                summary=final_text[:600],
                usage=usage_counts,
                detail=text[:400],
            )
        structured = payload.get("structured_output") if isinstance(payload.get("structured_output"), dict) else None
        structured = structured or extract_structured(final_text)
        return AgentResult(outcome="completed", summary=final_text[-600:], structured=structured, usage=usage_counts)


def _last_json_object(text: str) -> dict[str, Any] | None:
    stripped = (text or "").strip()
    if not stripped:
        return None
    try:
        value = json.loads(stripped)
        return value if isinstance(value, dict) else None
    except json.JSONDecodeError:
        pass
    for line in reversed(stripped.splitlines()):
        line = line.strip()
        if line.startswith("{"):
            try:
                value = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(value, dict):
                return value
    return None


def suggested_provider(executable: str | None = None) -> dict[str, Any]:
    return {
        "id": "claude-code",
        "enabled": True,
        "adapter": ClaudeCodeAdapter.adapter_id,
        "executable": executable or "claude",
        "models": dict(SUGGESTED_MODELS),
        "effort_map": dict(SUGGESTED_EFFORT_MAP),
        "max_concurrency": 2,
        "options": {"permission_mode": "acceptEdits", "read_only_permission_mode": "plan"},
    }
