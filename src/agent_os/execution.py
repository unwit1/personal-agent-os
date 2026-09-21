"""Deterministic, cache, and approved-skill-first execution planning.

This module selects a route; it never invokes a model or silently executes a
skill.  That keeps provider policy out of the core and makes the decision
auditable from a compact workflow record.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .paths import ROOT
from .skills import discover


ROUTE_ORDER = ("deterministic", "cache", "skill", "model")
COMPLEXITY_PATHS = ("SIMPLE", "PLANNED", "STAGED")


def classify_complexity(
    *,
    action_count: int = 1,
    expected_context_tokens: int = 0,
    needs_resume: bool = False,
    tool_or_provider_count: int = 0,
    validation_complexity: str = "low",
) -> dict[str, str]:
    """Choose the smallest orchestration shape from observable task facts.

    This deliberately accepts structured facts rather than inferring intent
    with a model. Callers retain the evidence alongside the result and route
    only ``STAGED`` work through the persistent workflow orchestrator.
    """
    if needs_resume or action_count >= 4 or tool_or_provider_count >= 2 or expected_context_tokens > 4_000 or validation_complexity == "high":
        return {"path": "STAGED", "reason": "resume, scale, coordination, context, or validation complexity requires checkpoints"}
    if action_count >= 2 or expected_context_tokens > 1_200 or validation_complexity == "medium":
        return {"path": "PLANNED", "reason": "dependent work benefits from a compact plan without persistent orchestration"}
    return {"path": "SIMPLE", "reason": "one bounded low-risk action needs no planning or checkpoint overhead"}


def _safe_artifact(path_value: Any, root: Path) -> Path | None:
    if not isinstance(path_value, str) or not path_value.strip():
        return None
    candidate = (root / path_value).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError:
        return None
    return candidate


def cache_artifact(stage: dict[str, Any], root: Path = ROOT) -> Path | None:
    """Return a declared cache artifact only when it is a safe existing file."""
    cache = stage.get("cache")
    if not isinstance(cache, dict):
        return None
    artifact = _safe_artifact(cache.get("path"), root)
    return artifact if artifact and artifact.is_file() else None


def approved_skill(stage: dict[str, Any], root: Path = ROOT) -> dict[str, str] | None:
    """Resolve an explicitly declared approved skill; never infer approval."""
    name = stage.get("approved_skill")
    if not isinstance(name, str) or not name.strip():
        return None
    for skill in discover():
        if skill.name == name:
            return {"name": skill.name, "path": str(skill.path), "source": skill.source}
    return None


def select_route(stage: dict[str, Any], root: Path = ROOT) -> dict[str, Any]:
    """Choose the least costly declared route with observable evidence.

    A stage's preferred path is its declared deterministic capability. Cache
    and skill routes are considered before any model handoff whenever declared
    and valid. A missing/stale cache is merely unavailable, never an error.
    """
    preferred = stage.get("preferred_execution_path", "model")
    if preferred == "deterministic":
        return {"route": "deterministic", "reason": "stage declares a deterministic execution path"}
    artifact = cache_artifact(stage, root)
    if artifact is not None:
        return {"route": "cache", "reason": "declared cache artifact exists", "artifact": str(artifact.relative_to(root.resolve()))}
    skill = approved_skill(stage, root)
    if skill is not None:
        return {"route": "skill", "reason": "declared approved skill is available", "skill": skill}
    return {
        "route": "model",
        "reason": "no declared deterministic utility, valid cache artifact, or approved skill is available",
    }
