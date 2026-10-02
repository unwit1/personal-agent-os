from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable

REPO_ROOT = Path(__file__).resolve().parents[4]
SERVER_NAME = "agent-os"
ALLOWED_TOOLS = "mcp__agent-os__*"
BUILTIN_TOOLS = (
    "Bash", "Edit", "Write", "MultiEdit", "NotebookEdit", "WebFetch", "WebSearch",
    "Read", "Glob", "Grep", "Task", "TodoWrite",
)
DEFAULT_TIMEOUT_SECONDS = 600


API_KEY_VARS = ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN")


def _child_env() -> dict[str, str]:
    """Parent environment minus API credentials so the CLI uses the subscription."""
    return {k: v for k, v in os.environ.items() if k not in API_KEY_VARS}


def mcp_config(path: Path | str) -> Path:
    """Write a strict MCP config naming only the agent-os server."""
    target = Path(path)
    config = {
        "mcpServers": {
            SERVER_NAME: {
                "command": sys.executable,
                "args": [str(REPO_ROOT / "agent.py"), "mcp"],
            }
        }
    }
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    return target


def build_invocation(
    prompt: str,
    session_id: str | None = None,
    mcp_config_path: Path | str = "",
    claude: str = "claude",
) -> list[str]:
    argv = [
        claude, "-p", prompt,
        "--output-format", "json",
        "--mcp-config", str(mcp_config_path),
        "--strict-mcp-config",
        "--allowedTools", ALLOWED_TOOLS,
        "--disallowedTools", ",".join(BUILTIN_TOOLS),
    ]
    if session_id:
        argv += ["--resume", session_id]
    return argv


def option_prompt(item: dict[str, Any], action: dict[str, Any]) -> str:
    action_id = action.get("action_id") or action.get("id") or ""
    label = action.get("label") or action_id
    context = item.get("context")
    if context is None:
        context = {k: item[k] for k in ("source", "due", "age", "options") if k in item}
    lines = [
        f"The operator selected the option \"{label}\" on an outstanding item.",
        f"Item id: {item.get('id', '')}",
        f"Title: {item.get('title', '')}",
        f"Why: {item.get('why', '')}",
        f"Context: {json.dumps(context, default=str, sort_keys=True)}",
        f"Action id: {action_id}",
        "",
        f"Carry it out by calling the executive_window.run tool with item_id and action_id \"{action_id}\".",
    ]
    if action.get("consequential"):
        lines.append(
            "This action is consequential: it only produces a preview for the operator "
            "to confirm in the window. Do not claim it was executed; tell the operator "
            "to review the preview and click Confirm."
        )
    else:
        lines.append(
            "If a later action turns out to be consequential, it only produces a preview "
            "for the operator to confirm; it never runs on your say-so."
        )
    return "\n".join(lines)


class ChatBridge:
    def __init__(
        self,
        home: Path | str,
        runner: Callable[..., Any] = subprocess.run,
        claude: str = "claude",
        timeout: int = DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        self.home = Path(home)
        self.runner = runner
        self.claude = claude
        self.timeout = timeout

    @property
    def sessions_path(self) -> Path:
        return self.home / "sessions.json"

    def _sessions(self) -> dict[str, str]:
        try:
            data = json.loads(self.sessions_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}
        return data if isinstance(data, dict) else {}

    def _save(self, sessions: dict[str, str]) -> None:
        self.home.mkdir(parents=True, exist_ok=True)
        self.sessions_path.write_text(json.dumps(sessions, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def send(self, conversation_id: str, text: str) -> dict[str, Any]:
        sessions = self._sessions()
        session_id = sessions.get(conversation_id)
        config = mcp_config(self.home / "mcp-config.json")
        argv = build_invocation(text, session_id, config, self.claude)
        try:
            proc = self.runner(
                argv, capture_output=True, text=True, timeout=self.timeout,
                encoding="utf-8", cwd=str(REPO_ROOT), env=_child_env(),
            )
        except (OSError, subprocess.SubprocessError) as exc:
            return {"reply": "", "session_id": session_id, "error": f"{type(exc).__name__}: {exc}"}
        stdout = (getattr(proc, "stdout", "") or "").strip()
        stderr = (getattr(proc, "stderr", "") or "").strip()
        returncode = getattr(proc, "returncode", 0)
        try:
            data = json.loads(stdout)
            if not isinstance(data, dict):
                raise ValueError("not an object")
        except ValueError:
            error = stderr or stdout or "claude produced no JSON output"
            return {"reply": "", "session_id": session_id, "error": error}
        new_sid = data.get("session_id") or session_id
        if new_sid and new_sid != session_id:
            sessions[conversation_id] = new_sid
            self._save(sessions)
        error = None
        if data.get("is_error") or returncode:
            error = str(data.get("result") or stderr or f"claude exited with {returncode}")
        reply = "" if error else str(data.get("result") or "")
        return {"reply": reply, "session_id": new_sid, "error": error}
