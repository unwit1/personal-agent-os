"""Detect a worker stuck repeating itself.

A worker can loop without failing: polling a process it mistook for its own,
re-running one command, waiting on something that never changes. The worker
timeout would catch it only after an hour of spend. Here the tail of the
worker's event stream (Codex ``--json`` or Claude ``stream-json``) is read and
the worker counts as stuck when one command dominates its recent commands.
"""

from __future__ import annotations

import json
import os
from typing import Any

WINDOW = 12  # recent commands inspected
THRESHOLD = 9  # identical commands among them that count as a loop


def _commands(text: str) -> list[str]:
    commands: list[str] = []
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            event = json.loads(line)
        except ValueError:
            continue
        item = event.get("item") or {}
        if event.get("type") == "item.completed" and item.get("type") == "command_execution":
            commands.append(str(item.get("command") or ""))
            continue
        message = event.get("message") or {}
        if event.get("type") == "assistant" and isinstance(message.get("content"), list):
            for block in message["content"]:
                if isinstance(block, dict) and block.get("type") == "tool_use":
                    commands.append(json.dumps(block.get("input") or {}, sort_keys=True))
    return commands


def repeated_command(stdout_path: str | None, *, window: int = WINDOW, threshold: int = THRESHOLD, tail_bytes: int = 400_000) -> dict[str, Any] | None:
    """``{"command", "count", "window"}`` when the worker is looping, else None."""
    if not stdout_path:
        return None
    try:
        with open(stdout_path, "rb") as handle:
            handle.seek(0, os.SEEK_END)
            size = handle.tell()
            handle.seek(max(size - tail_bytes, 0))
            text = handle.read().decode("utf-8", errors="replace")
    except OSError:
        return None
    recent = _commands(text)[-window:]
    if len(recent) < window:
        return None
    counts: dict[str, int] = {}
    for command in recent:
        counts[command] = counts.get(command, 0) + 1
    command, count = max(counts.items(), key=lambda pair: pair[1])
    if count < threshold:
        return None
    return {"command": command[-300:], "count": count, "window": window}
