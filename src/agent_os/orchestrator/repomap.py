"""A compact, goal-focused map of a repository for planner prompts.

A planner with no map explores: every turn re-sends the whole conversation,
so tokens grow with turns x context (a live planner used 32 turns and 1.7M
input tokens). This map is built locally with no model call:

* the tracked-file layout, summarized per directory;
* the files most relevant to the goal, ranked by explicit mentions, path
  terms and content term hits, with line counts, top-level definitions and
  their test file when one exists.

It is a starting point, not a boundary: the planner may still open files.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from pathlib import Path

from .worktrees import git

MAX_FILE_BYTES = 200_000
BULK_FOLDER_FILES = 1000
SECTION_MARKER = "Roadmap section:"  # see roadmap.build_goal
TEXT_SUFFIXES = {".py", ".md", ".json", ".js", ".ts", ".toml", ".txt", ".html", ".css", ".yml", ".yaml", ".ps1", ".sh"}
STOP = frozenset(
    "that this with from into only when what then than have been will should must each also your their them they "
    "which where while there these those about after before above under over does done make made using used the and "
    "for not are but all any can may its our out use new one two per via stage task tasks goal work roadmap next "
    "current status complete bounded slice section file files remain remaining".split()
)
_WORD = re.compile(r"[A-Za-z][A-Za-z0-9_]{3,}")
_PATHLIKE = re.compile(r"`?([A-Za-z0-9_./-]+\.(?:py|md|json|js|ts|toml|html|css))`?")
_DEF = re.compile(r"^(?:def|class|async def) ([A-Za-z_][A-Za-z0-9_]*)", re.MULTILINE)


def terms(goal: str, limit: int = 24) -> list[str]:
    counts = Counter(word.casefold() for word in _WORD.findall(goal) if word.casefold() not in STOP)
    return [word for word, _ in counts.most_common(limit)]


def build(repo: Path | str, goal: str, *, max_files: int = 12, max_chars: int = 6000) -> dict:
    """Return ``{"text": ..., "stats": ...}`` for the planner prompt."""
    repo = Path(repo)
    # A Continue Roadmap goal is fixed instructions plus the quoted stage:
    # only the stage says what the work is about.
    if SECTION_MARKER in goal:
        goal = goal.split(SECTION_MARKER, 1)[1]
    tracked = [line for line in git(["ls-files"], repo).stdout.splitlines() if line.strip()]
    tracked_set = set(tracked)
    mentioned = {match.strip("`./") for match in _PATHLIKE.findall(goal)}
    words = terms(goal)
    layout = Counter(name.split("/")[0] if "/" in name else "(root)" for name in tracked)
    # Folders with thousands of tracked files are data (imported libraries,
    # corpora): match their paths, but do not read their contents.
    bulk = {folder for folder, count in layout.items() if count > BULK_FOLDER_FILES}
    texts: dict[str, str] = {}
    for name in tracked:
        path = repo / name
        if path.suffix.lower() not in TEXT_SUFFIXES or name.split("/")[0] in bulk:
            continue
        try:
            if path.stat().st_size <= MAX_FILE_BYTES:
                texts[name] = path.read_text(encoding="utf-8", errors="ignore").casefold()
        except OSError:
            continue
    # Rare terms say more about relevance than words every file contains.
    total = max(len(texts), 1)
    idf = {word: math.log(1 + total / (1 + sum(1 for text in texts.values() if word in text))) for word in words}
    scored: list[tuple[float, str, int, list[str]]] = []
    for name in tracked:
        lower = name.casefold()
        score = 0.0
        if name in mentioned or any(lower.endswith("/" + item.casefold()) or lower == item.casefold() for item in mentioned):
            score += 50
        score += sum(4 * idf[word] for word in words if word in lower)
        text = texts.get(name)
        if text is not None:
            score += sum(min(text.count(word), 5) * idf[word] * 0.5 for word in words)
        if score <= 0:
            continue
        # Canonical roadmaps and handoffs are quoted in the goal already.
        if "/roadmap/" in lower or "/handoffs/" in lower or "/candidates/" in lower:
            score *= 0.2
        elif lower.endswith(".json"):
            score *= 0.5  # data and state files rarely hold the code to change
        raw = (repo / name).read_text(encoding="utf-8", errors="ignore") if text is not None else ""
        defs = _DEF.findall(raw)[:10] if name.endswith(".py") else []
        scored.append((score, name, raw.count("\n") + 1 if raw else 0, defs))
    scored.sort(key=lambda item: (-item[0], item[1]))
    chosen = scored[:max_files]
    lines = ["Repository layout (tracked files per top-level folder): " + ", ".join(f"{folder} {count}" for folder, count in sorted(layout.items(), key=lambda item: -item[1])[:14])]
    lines.append("Files most relevant to this goal (ranked locally by mentions and term matches; lines, top-level names):")
    for _, name, line_count, defs in chosen:
        test = _test_for(name, tracked_set)
        detail = f"- {name}" + (f" ({line_count} lines)" if line_count else "")
        if defs:
            detail += ": " + ", ".join(defs)
        if test:
            detail += f" [tests: {test}]"
        lines.append(detail)
    related = companions([name for _, name, _, _ in chosen], tracked, bulk)
    if related:
        lines.append("Related by name (schemas, fixtures and docs that often change with them): " + ", ".join(related))
    text = "\n".join(lines)
    if len(text) > max_chars:
        text = text[: max_chars].rsplit("\n", 1)[0]
    return {"text": text, "stats": {"tracked_files": len(tracked), "candidates_scored": len(scored), "listed": len(chosen), "related": len(related), "terms": words[:12], "chars": len(text)}}


def companions(chosen: list[str], tracked: list[str], bulk: set[str], limit: int = 8) -> list[str]:
    """Files elsewhere whose names share the stem of the top-ranked source
    files: ``workflows.py`` -> ``schemas/workflow-manifest-v1.schema.json``."""
    stems = []
    for name in chosen[:4]:
        if name.endswith((".py", ".js", ".ts")) and not Path(name).name.startswith("test_"):
            stem = Path(name).stem.casefold().rstrip("s")
            if len(stem) >= 5:
                stems.append(stem)
    found = []
    for name in tracked:
        lower = name.casefold()
        if name in chosen or name.split("/")[0] in bulk or "/roadmap/" in lower or lower.startswith(("tests/", "src/")):
            continue
        if any(stem in Path(lower).name for stem in stems):
            found.append(name)
    return found[:limit]


def _test_for(name: str, tracked: set[str]) -> str | None:
    stem = Path(name).stem
    for candidate in (f"tests/test_{stem}.py", f"tests/test_{stem.split('_')[0]}.py"):
        if candidate in tracked and candidate != name:
            return candidate
    return None
