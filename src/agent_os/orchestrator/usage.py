"""Provider token usage, normalized and honestly labelled.

Providers report usage differently:

* Claude Code (``--output-format json``) reports ``input_tokens`` *excluding*
  cache traffic, plus ``cache_read_input_tokens`` and
  ``cache_creation_input_tokens`` separately.
* Codex (``exec --json``) reports ``input_tokens`` *including* the cached part
  and ``cached_input_tokens`` as a subset (OpenAI usage semantics).

Adding those raw fields together would compare different things, so every
adapter converts to one shape here. ``input_tokens`` always means every input
token the model processed (uncached + cache read + cache write).

Every usage record carries an ``accuracy``:

* ``exact`` -- the provider reported the numbers;
* ``estimated`` -- derived by Agent OS (for example characters / 4);
* ``unavailable`` -- the provider reported nothing. Counts are ``None``, never 0.
"""

from __future__ import annotations

import math
from typing import Any


ACCURACIES = ("exact", "estimated", "unavailable")
COUNT_KEYS = (
    "input_tokens",
    "uncached_input_tokens",
    "cache_read_tokens",
    "cache_write_tokens",
    "output_tokens",
    "reasoning_tokens",
)
# Characters per token used for every Agent OS estimate. A rough, widely used
# ratio for English/code; estimates are always labelled as estimates.
CHARS_PER_TOKEN = 4
ESTIMATE_METHOD = f"characters/{CHARS_PER_TOKEN}"


def estimate_tokens(text_or_length: str | bytes | int | None) -> int:
    if text_or_length is None:
        return 0
    length = text_or_length if isinstance(text_or_length, int) else len(text_or_length)
    return int(math.ceil(max(length, 0) / CHARS_PER_TOKEN))


def _int(value: Any) -> int | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return max(int(value), 0)
    except (TypeError, ValueError):
        return None


def unavailable(source: str = "none") -> dict[str, Any]:
    return {**{key: None for key in COUNT_KEYS}, "cached_tokens": None, "cost_usd": None, "turns": None, "tool_calls": None, "accuracy": "unavailable", "source": source}


def normalized(
    *,
    uncached_input: Any = None,
    cache_read: Any = None,
    cache_write: Any = None,
    total_input: Any = None,
    output: Any = None,
    reasoning: Any = None,
    cost_usd: Any = None,
    turns: Any = None,
    tool_calls: Any = None,
    source: str,
    accuracy: str = "exact",
) -> dict[str, Any]:
    """Build the canonical record. Give either ``total_input`` (Codex style)
    or ``uncached_input`` (Claude style); the other is derived."""
    read = _int(cache_read)
    write = _int(cache_write)
    uncached = _int(uncached_input)
    total = _int(total_input)
    if total is None and uncached is not None:
        total = uncached + (read or 0) + (write or 0)
    if uncached is None and total is not None:
        uncached = max(total - (read or 0) - (write or 0), 0)
    out = _int(output)
    if total is None and out is None:
        return unavailable(source)
    try:
        cost = round(float(cost_usd), 6) if cost_usd is not None else None
    except (TypeError, ValueError):
        cost = None
    return {
        "input_tokens": total,
        "uncached_input_tokens": uncached,
        "cache_read_tokens": read,
        "cache_write_tokens": write,
        "cached_tokens": read,  # pre-normalization field name, kept for older readers
        "output_tokens": out,
        "reasoning_tokens": _int(reasoning),
        "cost_usd": cost,
        "turns": _int(turns),
        "tool_calls": _int(tool_calls),
        "accuracy": accuracy if accuracy in ACCURACIES else "estimated",
        "source": source,
    }


def from_claude(payload: dict[str, Any] | None) -> dict[str, Any]:
    """Claude Code ``--output-format json`` result object."""
    if not isinstance(payload, dict):
        return unavailable("claude-code")
    usage = payload.get("usage")
    if not isinstance(usage, dict):
        return unavailable("claude-code")
    details = usage.get("output_tokens_details") if isinstance(usage.get("output_tokens_details"), dict) else {}
    return normalized(
        uncached_input=usage.get("input_tokens"),
        cache_read=usage.get("cache_read_input_tokens"),
        cache_write=usage.get("cache_creation_input_tokens"),
        output=usage.get("output_tokens"),
        reasoning=details.get("thinking_tokens"),
        cost_usd=payload.get("total_cost_usd"),
        turns=payload.get("num_turns"),
        source="claude-code",
    )


def from_codex_turns(turns: list[dict[str, Any]], tool_calls: int | None = None) -> dict[str, Any]:
    """Sum of Codex ``turn.completed`` usage objects."""
    if not turns:
        return unavailable("codex")
    total = sum(_int(item.get("input_tokens")) or 0 for item in turns)
    cached = sum(_int(item.get("cached_input_tokens")) or 0 for item in turns)
    output = sum(_int(item.get("output_tokens")) or 0 for item in turns)
    reasoning_values = [_int(item.get("reasoning_output_tokens")) for item in turns]
    reasoning = sum(value for value in reasoning_values if value is not None) if any(value is not None for value in reasoning_values) else None
    return normalized(total_input=total, cache_read=cached, output=output, reasoning=reasoning, turns=len(turns), tool_calls=tool_calls, source="codex")


def coerce(value: dict[str, Any] | None, source: str = "unknown") -> dict[str, Any]:
    """Accept an already normalized record, a legacy ``{input_tokens,
    cached_tokens, output_tokens}`` dict, or nothing."""
    if not value:
        return unavailable(source)
    if value.get("accuracy") in ACCURACIES and "uncached_input_tokens" in value:
        return {**unavailable(source), **value}
    return normalized(
        total_input=value.get("input_tokens"),
        cache_read=value.get("cached_tokens"),
        output=value.get("output_tokens"),
        reasoning=value.get("reasoning_tokens"),
        cost_usd=value.get("cost_usd"),
        turns=value.get("turns"),
        source=str(value.get("source") or source),
        accuracy=str(value.get("accuracy") or "exact"),
    )


def empty_totals() -> dict[str, Any]:
    return {
        "input_tokens": 0,
        "cached_tokens": 0,
        "output_tokens": 0,
        "workers": 0,
        "cache_write_tokens": 0,
        "reasoning_tokens": 0,
        "cost_usd": 0.0,
        "calls_exact": 0,
        "calls_estimated": 0,
        "calls_unavailable": 0,
    }


def add(totals: dict[str, Any], usage: dict[str, Any]) -> dict[str, Any]:
    """Add one normalized record to run totals. Only exact numbers are summed
    into the token totals; the per-accuracy call counts say how complete the
    totals are."""
    for key, value in empty_totals().items():
        totals.setdefault(key, value)
    accuracy = usage.get("accuracy", "unavailable")
    totals[f"calls_{accuracy}"] = totals.get(f"calls_{accuracy}", 0) + 1
    if accuracy != "exact":
        return totals
    totals["input_tokens"] += usage.get("input_tokens") or 0
    totals["cached_tokens"] += usage.get("cache_read_tokens") or 0
    totals["cache_write_tokens"] += usage.get("cache_write_tokens") or 0
    totals["output_tokens"] += usage.get("output_tokens") or 0
    totals["reasoning_tokens"] += usage.get("reasoning_tokens") or 0
    if usage.get("cost_usd") is not None:
        totals["cost_usd"] = round(float(totals["cost_usd"]) + float(usage["cost_usd"]), 6)
    return totals
