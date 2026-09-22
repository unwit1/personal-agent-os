from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .paths import ROOT


WORD_RE = re.compile(r"[a-z0-9]+", re.IGNORECASE)
DEFAULT_MINIMUM_SCORE = 2


@dataclass(frozen=True)
class Skill:
    name: str
    description: str
    path: Path
    source: str


def _frontmatter(path: Path) -> tuple[str, str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    name = path.parent.name
    description = ""
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            for line in text[3:end].splitlines():
                key, separator, value = line.partition(":")
                if not separator:
                    continue
                if key.strip() == "name":
                    name = value.strip().strip('"\'')
                elif key.strip() == "description":
                    description = value.strip().strip('"\'')
    if not description:
        for line in text.splitlines():
            candidate = line.strip().lstrip("#").strip()
            if candidate and candidate != "---" and not candidate.casefold().startswith("skill:"):
                description = candidate
                break
    return name, description


CANONICAL_ROOT = ROOT / "skills"


def _within(path: Path, ancestor: Path) -> bool:
    try:
        path.relative_to(ancestor)
    except ValueError:
        return False
    return True


def _project_roots(project_path: Path | None, skill_roots: Iterable[str], canonical: Path) -> list[Path]:
    """Project roots that are not the canonical Agent OS skill tree.

    Personal Agent OS is itself a registered project, so its state may list the
    canonical directory as a project skill root. Discovering the same tree twice
    would emit duplicate skills, so containment is checked in both directions
    rather than relying on exact path identity.
    """
    if not project_path:
        return []
    roots: list[Path] = []
    for item in skill_roots:
        try:
            candidate = (project_path / item).resolve()
        except OSError:
            continue
        if _within(candidate, canonical) or _within(canonical, candidate):
            continue
        if any(candidate == existing for existing in roots):
            continue
        roots.append(candidate)
    return roots


def discover(project_path: Path | None = None, skill_roots: Iterable[str] = ()) -> list[Skill]:
    """Return one Skill per skill name. Project-local skills override canonical ones."""
    try:
        canonical = CANONICAL_ROOT.resolve()
    except OSError:
        canonical = CANONICAL_ROOT
    roots: list[tuple[Path, str]] = [(canonical, "agent-os")]
    roots.extend((item, "project") for item in _project_roots(project_path, skill_roots, canonical))
    by_name: dict[str, Skill] = {}
    seen_paths: set[Path] = set()
    for root, source in roots:
        if not root.exists():
            continue
        for path in sorted(root.glob("*/SKILL.md")):
            try:
                resolved = path.resolve()
            except OSError:
                resolved = path
            if resolved in seen_paths:
                continue
            seen_paths.add(resolved)
            name, description = _frontmatter(path)
            if name in by_name and source != "project":
                continue
            by_name[name] = Skill(name, description, path, source)
    return sorted(by_name.values(), key=lambda skill: skill.name)


def match(
    task: str,
    available: list[Skill],
    limit: int = 3,
    minimum_score: int = DEFAULT_MINIMUM_SCORE,
) -> list[Skill]:
    """Return only skills with enough lexical evidence to be useful."""
    if not isinstance(minimum_score, int) or minimum_score < 1:
        raise ValueError("minimum_score must be a positive integer")
    task_tokens = set(WORD_RE.findall(task.casefold()))
    scored: list[tuple[float, Skill]] = []
    for skill in available:
        haystack = f"{skill.name} {skill.description}".casefold()
        tokens = set(WORD_RE.findall(haystack))
        overlap = len(task_tokens & tokens)
        phrase_bonus = 2 if skill.name.replace("-", " ") in task.casefold() else 0
        score = overlap + phrase_bonus
        if score >= minimum_score:
            scored.append((score, skill))
    scored.sort(key=lambda item: (-item[0], item[1].name))
    return [skill for _, skill in scored[:limit]]


def metadata(skill: Skill) -> dict[str, str]:
    return {
        "name": skill.name,
        "description": skill.description,
        "path": str(skill.path),
        "source": skill.source,
    }
