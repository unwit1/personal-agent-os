"""Deterministic keyword lookup over the curated RTEC-HR knowledge tree. No model calls."""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

PROJECT_ID = "rtec-hr-process-model"
ENV_ROOT = "RTEC_HR_ROOT"
BLOCKED_PARTS = ("restricted", "private")
TEXT_KEYS = ("text", "claim", "statement", "summary")
CITATION_KEYS = ("citation", "source", "page", "pages", "handbook_page")
EFFECTIVE_KEYS = ("effective", "effective_date", "effective_from")
SUPERSEDED_KEYS = ("superseded_by", "superseded")
SYNONYMS = {
    "ot": ("overtime",),
    "pto": ("paid", "time", "off"),
    "driver": ("transit", "driver"),
    "drivers": ("transit", "driver"),
}
STOPWORDS = frozenset("a an the our is are what whats s for of to on in and or do does we policy".split())
MAX_FILE_BYTES = 2_000_000

_CACHE: dict[str, Any] = {"root": None, "stamp": None, "records": []}


def _blocked(path: Path, root: Path) -> bool:
    try:
        parts = path.relative_to(root).parts
    except ValueError:
        return True
    return any(token in part.casefold() for part in parts for token in BLOCKED_PARTS)


def find_root() -> Path | None:
    env = os.environ.get(ENV_ROOT)
    if env:
        path = Path(env).expanduser()
        return path if path.is_dir() else None
    try:
        from ..machine import resolve_path
        from ..registry import canonical_projects

        for entry in canonical_projects():
            if entry.get("id") == PROJECT_ID:
                path, _ = resolve_path(entry)
                return path if path.is_dir() else None
    except Exception:
        return None
    return None


def _files(root: Path) -> list[Path]:
    base = root / "knowledge"
    found: list[Path] = []
    if not base.is_dir():
        return found
    for dirpath, dirnames, filenames in os.walk(base):
        dirnames[:] = [d for d in dirnames if not any(t in d.casefold() for t in BLOCKED_PARTS)]
        for name in filenames:
            path = Path(dirpath) / name
            if path.suffix.lower() in (".json", ".md") and not _blocked(path, root):
                found.append(path)
    return sorted(found)


def tokens(text: str) -> list[str]:
    out: list[str] = []
    for word in re.findall(r"[a-z0-9]+", text.casefold()):
        out.extend(SYNONYMS.get(word, (word,)))
    return out


def _first(item: dict[str, Any], keys: tuple[str, ...]) -> Any:
    for key in keys:
        value = item.get(key)
        if value not in (None, "", [], False):
            return value
    return None


def _scalar(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, (str, int, float)):
        return str(value)
    return json.dumps(value, sort_keys=True)


def _walk_json(node: Any, rel: str, inherited: dict[str, Any], out: list[dict[str, Any]]) -> None:
    if isinstance(node, list):
        for child in node:
            _walk_json(child, rel, inherited, out)
        return
    if not isinstance(node, dict):
        return
    if node.get("omitted") or node.get("status") == "omitted":
        return
    context = dict(inherited)
    for key in CITATION_KEYS + EFFECTIVE_KEYS:
        if node.get(key) not in (None, "") and not isinstance(node[key], (dict, list)):
            context[key] = node[key]
    text = _first(node, TEXT_KEYS)
    if isinstance(text, str) and text.strip():
        source, page = node.get("source"), node.get("page")
        if isinstance(source, str) and page not in (None, ""):
            citation: Any = f"{source}, page {page}"
        else:
            citation = _first(node, CITATION_KEYS) or _first(context, CITATION_KEYS)
        out.append({
            "text": text.strip(),
            "source_path": rel,
            "citation": _scalar(citation),
            "effective_date": _scalar(_first(node, EFFECTIVE_KEYS) or _first(context, EFFECTIVE_KEYS)),
            "superseded_by": _scalar(_first(node, SUPERSEDED_KEYS)),
        })
    for child in node.values():
        if isinstance(child, (dict, list)):
            _walk_json(child, rel, context, out)


def _parse_markdown(text: str, rel: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    heading, lines = "", []

    def flush() -> None:
        body = "\n".join(lines).strip()
        if body:
            out.append({
                "text": f"{heading}\n{body}".strip() if heading else body,
                "source_path": rel,
                "citation": f"{rel}#{heading}" if heading else rel,
                "effective_date": None,
                "superseded_by": None,
            })

    for line in text.splitlines():
        match = re.match(r"^#{1,6}\s+(.*\S)\s*$", line)
        if match:
            flush()
            heading, lines = match.group(1), []
        else:
            lines.append(line)
    flush()
    return out


def _parse(path: Path, root: Path) -> list[dict[str, Any]]:
    rel = path.relative_to(root).as_posix()
    try:
        if path.stat().st_size > MAX_FILE_BYTES:
            return []
        raw = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []
    if path.suffix.lower() == ".md":
        return _parse_markdown(raw, rel)
    try:
        data = json.loads(raw)
    except ValueError:
        return []
    out: list[dict[str, Any]] = []
    _walk_json(data, rel, {}, out)
    return out


def load_index(root: Path) -> list[dict[str, Any]]:
    files = _files(root)
    stamp = tuple((str(p), p.stat().st_mtime_ns) for p in files)
    if _CACHE["root"] == str(root) and _CACHE["stamp"] == stamp:
        return _CACHE["records"]
    records: list[dict[str, Any]] = []
    for path in files:
        for record in _parse(path, root):
            record["_tokens"] = tokens(f"{record['text']} {record['source_path']}")
            records.append(record)
    _CACHE.update(root=str(root), stamp=stamp, records=records)
    return records


def search_claims(query: str, limit: int = 5, root: Path | None = None) -> list[dict[str, Any]]:
    root = root or find_root()
    if root is None:
        return []
    terms = {t for t in tokens(query) if t not in STOPWORDS}
    if not terms:
        return []
    scored = []
    for record in load_index(Path(root)):
        hits = terms & set(record["_tokens"])
        if not hits:
            continue
        score = len(hits) / len(terms) + 0.01 * sum(record["_tokens"].count(t) for t in hits) ** 0.5
        if record["superseded_by"]:
            score *= 0.5
        scored.append((score, record))
    scored.sort(key=lambda pair: (-pair[0], pair[1]["source_path"]))
    keys = ("text", "source_path", "citation", "effective_date", "superseded_by")
    return [{k: r[k] for k in keys} for _, r in scored[: max(1, int(limit))]]


ANSWER_GUIDANCE = "Quote the claim and cite source_path/citation. If nothing relevant is found say so; do not substitute general law."


def policy_lookup(query: str, limit: int = 5) -> dict[str, Any]:
    root = find_root()
    results = search_claims(query, limit, root) if root else []
    return {"query": query, "results": results, "knowledge_root_found": root is not None, "answer_guidance": ANSWER_GUIDANCE}
