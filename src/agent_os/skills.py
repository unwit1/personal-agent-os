from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .paths import ROOT


WORD_RE = re.compile(r"[a-z0-9]+", re.IGNORECASE)


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


def discover(project_path: Path | None = None, skill_roots: Iterable[str] = ()) -> list[Skill]:
    roots: list[tuple[Path, str]] = [(ROOT / "skills", "agent-os")]
    if project_path:
        roots.extend((project_path / item, "project") for item in skill_roots)
    found: list[Skill] = []
    seen: set[Path] = set()
    for root, source in roots:
        if not root.exists():
            continue
        for path in sorted(root.glob("*/SKILL.md")):
            resolved = path.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            name, description = _frontmatter(path)
            found.append(Skill(name, description, path, source))
    return found


def match(task: str, available: list[Skill], limit: int = 3) -> list[Skill]:
    task_tokens = set(WORD_RE.findall(task.casefold()))
    scored: list[tuple[float, Skill]] = []
    for skill in available:
        haystack = f"{skill.name} {skill.description}".casefold()
        tokens = set(WORD_RE.findall(haystack))
        overlap = len(task_tokens & tokens)
        phrase_bonus = 2 if skill.name.replace("-", " ") in task.casefold() else 0
        score = overlap + phrase_bonus
        if score:
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
