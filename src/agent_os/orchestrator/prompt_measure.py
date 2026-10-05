"""Offline token measurements for orchestrator worker prompts."""

from __future__ import annotations

from typing import Any

from . import prompts
from .usage import estimate_tokens


def measure(
    run: dict, nodes: list[dict], *, repo_map: str | None = None, diff: str | None = None, scope_maps: dict[str, str] | None = None
) -> dict:
    """Measure prompt sizes by role without retaining prompt contents."""
    roles: dict[str, dict[str, int]] = {}
    family_counts: dict[str, int] = {}

    for node in nodes:
        role = node["role"]
        scope_map = None
        if role in ("implementer", "test_author", "repairer", "reviewer"):
            scope_map = (scope_maps or {}).get(node["id"])
        text, _ = prompts.build_measured(
            run,
            node,
            diff=diff if role == "reviewer" else None,
            repo_map=repo_map if role == "planner" else None,
            scope_map=scope_map,
        )
        total = estimate_tokens(text)
        family = prompts.FAMILIES.get(role)
        if (run.get("policy") or {}).get("shared_prefix") and family is not None:
            prefix_tokens = estimate_tokens(prompts.shared_prefix(run, family))
            suffix_tokens = total - prefix_tokens
            family_counts[family] = family_counts.get(family, 0) + 1
        else:
            prefix_tokens = 0
            suffix_tokens = total

        scope_map_tokens = estimate_tokens(scope_map) if scope_map else 0
        stats = roles.setdefault(role, {
            "count": 0,
            "total_tokens": 0,
            "max_tokens": 0,
            "prefix_tokens": 0,
            "suffix_tokens": 0,
            "scope_map_tokens": 0,
        })
        stats["count"] += 1
        stats["total_tokens"] += total
        stats["max_tokens"] = max(stats["max_tokens"], total)
        stats["prefix_tokens"] += prefix_tokens
        stats["suffix_tokens"] += suffix_tokens
        stats["scope_map_tokens"] += scope_map_tokens

    cacheable = sum(
        prefix_tokens * (count - 1)
        for family, count in family_counts.items()
        for prefix_tokens in (estimate_tokens(prompts.shared_prefix(run, family)),)
    )
    return {
        "schema": "personal-agent/orchestrator-prompt-measure/v1",
        "model_calls": 0,
        "roles": roles,
        "totals": {
            "prompts": len(nodes),
            "total_tokens": sum(item["total_tokens"] for item in roles.values()),
            "cacheable_prefix_tokens": cacheable,
            "scope_map_tokens": sum(item["scope_map_tokens"] for item in roles.values()),
        },
    }
