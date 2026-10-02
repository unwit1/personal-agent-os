"""Shared prefix detection and stabilization for vLLM prefix caching.

IMP-0018 Phase 0. Ensures that run-level request prefixes are byte-stable for
maximum vLLM prefix-cache hits: when the run has a shared_prefix, every request
sent to vLLM starts with exactly those bytes, before any per-request text.

Feature-detecting: shared_prefix may not be present in all records yet.
"""

from __future__ import annotations

import hashlib
from typing import Any


def run_prefix(record: dict[str, Any]) -> str | None:
    """Extract shared_prefix from record when present and non-empty.

    Supports both direct field (record['shared_prefix']) and nested dict
    (record['context_economy']['shared_prefix']).
    """
    prefix = record.get("shared_prefix")
    if isinstance(prefix, str) and prefix:
        return prefix

    context_economy = record.get("context_economy")
    if isinstance(context_economy, dict):
        prefix = context_economy.get("shared_prefix")
        if isinstance(prefix, str) and prefix:
            return prefix

    return None


def stabilize(messages: list[dict[str, Any]], prefix: str | None) -> list[dict[str, Any]]:
    """Ensure first system message starts with exact prefix bytes when given.

    When prefix is None, returns messages unchanged. Otherwise:
    - Ensures the first system message starts with exactly the prefix bytes
    - Repairs trailing whitespace drift in the prefix
    - Prepends prefix if no system message exists
    - Moves any per-request text after the prefix
    - Never mutates the input

    Returns a new list of message dicts.
    """
    if prefix is None:
        return messages

    messages = [dict(msg) for msg in messages]

    system_idx = None
    for i, msg in enumerate(messages):
        if isinstance(msg, dict) and msg.get("role") == "system":
            system_idx = i
            break

    if system_idx is None:
        messages.insert(0, {"role": "system", "content": prefix})
    else:
        content = messages[system_idx].get("content")

        if isinstance(content, list):
            _stabilize_list_content(messages[system_idx], prefix)
        elif isinstance(content, str):
            _stabilize_string_content(messages[system_idx], prefix)
        else:
            messages[system_idx]["content"] = prefix

    return messages


def _stabilize_string_content(msg: dict[str, Any], prefix: str) -> None:
    """Repair a string-type system message content."""
    current_content = msg.get("content") or ""

    if current_content.startswith(prefix):
        return

    stripped_prefix = prefix.rstrip()
    if stripped_prefix and current_content.startswith(stripped_prefix):
        rest = current_content[len(stripped_prefix):]
        if not rest or rest[0].isspace():
            msg["content"] = prefix + rest.lstrip(" \t\r\n")
        else:
            msg["content"] = prefix + current_content
    else:
        msg["content"] = prefix + current_content


def _stabilize_list_content(msg: dict[str, Any], prefix: str) -> None:
    """Repair a list-type (OpenAI-style) system message content."""
    content = msg.get("content") or []

    if not content:
        msg["content"] = [{"type": "text", "text": prefix}]
        return

    if isinstance(content[0], dict) and content[0].get("type") == "text":
        text = content[0].get("text") or ""
        if text.startswith(prefix):
            return

        stripped_prefix = prefix.rstrip()
        if stripped_prefix and text.startswith(stripped_prefix):
            rest = text[len(stripped_prefix):]
            if not rest or rest[0].isspace():
                content[0]["text"] = prefix + rest.lstrip(" \t\r\n")
            else:
                content[0]["text"] = prefix + text
        else:
            content[0]["text"] = prefix + text
    else:
        content.insert(0, {"type": "text", "text": prefix})


def prefix_fingerprint(prefix: str) -> str:
    """SHA256 hex digest of prefix's UTF-8 bytes for telemetry."""
    return hashlib.sha256(prefix.encode("utf-8")).hexdigest()
