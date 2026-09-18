from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path
from typing import Iterable

from .paths import INDEX_DIR, INDEX_PATH, ROOT
from .registry import load_state, projects
from .skills import discover


def _safe_text(path: Path, limit: int = 500_000) -> str:
    if not path.is_file() or path.stat().st_size > limit:
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def canonical_documents() -> Iterable[tuple[str, str, str, str]]:
    local_files = [
        ROOT / "profile" / "preferences.json",
        ROOT / "projects" / "registry.json",
        ROOT / "policy" / "CANONICAL_AGENT_POLICY.md",
    ]
    local_files.extend(sorted((ROOT / "memory").rglob("*.json")) if (ROOT / "memory").exists() else [])
    for path in local_files:
        if path.exists():
            yield (str(path), "agent-os", "canonical", _safe_text(path))

    for project in projects():
        state = load_state(project)
        state_path = ROOT / project["state_file"]
        yield (str(state_path), project["id"], "project-state", _safe_text(state_path))
        project_path = Path(project["path"])
        for relative in state.get("context_files", []):
            path = (project_path / relative).resolve()
            try:
                path.relative_to(project_path.resolve())
            except ValueError:
                continue
            if path.exists():
                yield (str(path), project["id"], "project-context", _safe_text(path))

        for skill in discover(project_path, state.get("skill_roots", [])):
            searchable = json.dumps({"name": skill.name, "description": skill.description})
            yield (str(skill.path), project["id"], "skill-metadata", searchable)


def rebuild() -> dict[str, int | str]:
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    if INDEX_PATH.exists():
        INDEX_PATH.unlink()
    connection = sqlite3.connect(INDEX_PATH)
    try:
        connection.execute(
            "CREATE TABLE documents (id INTEGER PRIMARY KEY, path TEXT, scope TEXT, kind TEXT, content TEXT, UNIQUE(path, scope))"
        )
        fts5 = True
        try:
            connection.execute(
                "CREATE VIRTUAL TABLE documents_fts USING fts5(path, scope, kind, content, content='documents', content_rowid='id')"
            )
        except sqlite3.OperationalError:
            fts5 = False
        count = 0
        for path, scope, kind, content in canonical_documents():
            cursor = connection.execute(
                "INSERT INTO documents(path, scope, kind, content) VALUES (?, ?, ?, ?)",
                (path, scope, kind, content),
            )
            if fts5:
                connection.execute(
                    "INSERT INTO documents_fts(rowid, path, scope, kind, content) VALUES (?, ?, ?, ?, ?)",
                    (cursor.lastrowid, path, scope, kind, content),
                )
            count += 1
        connection.commit()
    finally:
        connection.close()
    return {"documents": count, "index": str(INDEX_PATH), "fts5": int(fts5)}


def search(query: str, scope: str | None = None, limit: int = 8) -> list[dict[str, str]]:
    if not INDEX_PATH.exists():
        rebuild()
    connection = sqlite3.connect(INDEX_PATH)
    connection.row_factory = sqlite3.Row
    try:
        has_fts = connection.execute(
            "SELECT 1 FROM sqlite_master WHERE name = 'documents_fts'"
        ).fetchone()
        params: list[object]
        if has_fts:
            terms = re.findall(r"[A-Za-z0-9]+", query)
            if not terms:
                return []
            cleaned = " OR ".join(f'"{term}"' for term in terms)
            sql = (
                "SELECT d.path, d.scope, d.kind, snippet(documents_fts, 3, '[', ']', ' … ', 18) AS excerpt "
                "FROM documents_fts JOIN documents d ON d.id = documents_fts.rowid "
                "WHERE documents_fts MATCH ?"
            )
            params = [cleaned]
            if scope:
                sql += " AND d.scope = ?"
                params.append(scope)
            sql += " ORDER BY bm25(documents_fts) LIMIT ?"
            params.append(limit)
        else:
            sql = "SELECT path, scope, kind, substr(content, 1, 300) AS excerpt FROM documents WHERE content LIKE ?"
            params = [f"%{query}%"]
            if scope:
                sql += " AND scope = ?"
                params.append(scope)
            sql += " LIMIT ?"
            params.append(limit)
        return [dict(row) for row in connection.execute(sql, params)]
    except sqlite3.OperationalError:
        return []
    finally:
        connection.close()
