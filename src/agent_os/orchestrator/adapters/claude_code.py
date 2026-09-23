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

from ..usage import from_claude
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
# Relative cost weights per capability class; data the operator may edit.
SUGGESTED_COSTS = {"fast": 2, "balanced": 3, "reasoning": 6, "frontier": 10}
OPTIONAL_FLAGS = (
    "--effort", "--permission-mode", "--permission-prompts", "--no-session-persistence", "--allowedTools",
    "--strict-mcp-config", "--tools", "--disable-slash-commands", "--exclude-dynamic-system-prompt-sections",
    "--setting-sources",
)
# Built-in tools a bounded worker needs. Everything else in the default set
# (sub-agents, web, notebooks, task lists, skills...) is tool-definition text
# sent with every request. Measured with `agent-os orchestrate overhead`.
LEAN_TOOLS = {"edit": ("Bash", "Read", "Edit", "Write", "Glob", "Grep"), "read_only": ("Bash", "Read", "Glob", "Grep")}


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
        if features.get("--strict-mcp-config") and options.get("keep_mcp_servers") is not True:
            # A bounded worker gets everything it needs in its prompt. The
            # operator's MCP servers (mail, Agent OS, ...) would only add
            # turns and reach beyond the worktree.
            argv.append("--strict-mcp-config")
        tools = request.allowed_tools or options.get("allowed_tools") or []
        if tools and features.get("--allowedTools"):
            argv += ["--allowedTools", ",".join(tools)]
        argv += lean_flags(options, features, request.read_only)
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
        usage_counts = from_claude(payload)
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


def lean_flags(options: dict[str, Any], features: dict[str, bool], read_only: bool) -> list[str]:
    """Flags that shrink the fixed per-call context of a headless worker.

    Each is optional in the registry (``options``) and passed only when the
    installed CLI advertises it. ``--bare`` is deliberately not used: it
    ignores OAuth/keychain logins and requires an API key.
    """
    argv: list[str] = []
    lean = options.get("lean_tools", LEAN_DEFAULTS["lean_tools"])
    if lean and features.get("--tools"):
        tools = lean if isinstance(lean, list) else LEAN_TOOLS["read_only" if read_only else "edit"]
        argv += ["--tools", ",".join(tools)]
    if options.get("disable_skills", LEAN_DEFAULTS["disable_skills"]) and features.get("--disable-slash-commands"):
        argv.append("--disable-slash-commands")
    if options.get("shared_prompt_cache", LEAN_DEFAULTS["shared_prompt_cache"]) and features.get("--exclude-dynamic-system-prompt-sections"):
        # Per-worktree details (cwd, git status) move out of the system
        # prompt, so every worker's system prompt is identical and cacheable.
        argv.append("--exclude-dynamic-system-prompt-sections")
    sources = options.get("setting_sources", LEAN_DEFAULTS["setting_sources"])
    if sources is not None and features.get("--setting-sources"):
        argv += ["--setting-sources", str(sources)]
    return argv


# Defaults chosen from measurements (docs/simple-mode.md, "Per-call overhead"),
# Claude Code 2.1.280 / haiku, trivial prompt: 25,177 input tokens per call by
# default; 14,331 with the lean tool set (-43%); skills listing ~2.6k more.
# --exclude-dynamic-system-prompt-sections measured no cache benefit across
# worktrees, and --setting-sources saves ~2% but drops user permission rules
# workers may rely on, so both stay off unless a registry entry turns them on.
LEAN_DEFAULTS: dict[str, Any] = {"lean_tools": True, "disable_skills": True, "shared_prompt_cache": False, "setting_sources": None}


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


def discover_models() -> dict[str, str]:
    """Claude Code resolves tier aliases to the newest model itself."""
    return dict(SUGGESTED_MODELS)


def suggested_provider(executable: str | None = None) -> dict[str, Any]:
    return {
        "id": "claude-code",
        "enabled": True,
        "adapter": ClaudeCodeAdapter.adapter_id,
        "executable": executable or "claude",
        "discover": True,
        "models": dict(SUGGESTED_MODELS),
        "costs": dict(SUGGESTED_COSTS),
        "effort_map": dict(SUGGESTED_EFFORT_MAP),
        "max_concurrency": 3,
        "tier_concurrency": {"reasoning": 2, "frontier": 1},
        "options": {"permission_mode": "acceptEdits", "read_only_permission_mode": "plan"},
    }
