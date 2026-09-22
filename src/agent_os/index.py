from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path
from typing import Any, Callable, Iterable

from .ingestion import IngestionLedger, stable_stage_id, stable_work_id
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
    if (ROOT / "forms" / "registry.json").exists():
        local_files.append(ROOT / "forms" / "registry.json")
    for path in local_files:
        if path.exists():
            yield (str(path), "agent-os", "canonical", _safe_text(path))

    for project in projects():
        state = load_state(project)
        state_path = ROOT / project["state_file"]
        yield (str(state_path), project["id"], "project-state", _safe_text(state_path))
        for relative, kind in (("changes/index.json", "change-index"), ("improvements/index.json", "improvement-index")):
            compact_index = ROOT / "projects" / project["id"] / relative
            if compact_index.exists():
                yield (str(compact_index), project["id"], kind, _safe_text(compact_index))
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


def _ensure_schema(connection: sqlite3.Connection) -> bool:
    connection.execute(
        "CREATE TABLE IF NOT EXISTS documents (id INTEGER PRIMARY KEY, path TEXT, scope TEXT, kind TEXT, content TEXT, UNIQUE(path, scope))"
    )
    try:
        connection.execute(
            "CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts USING fts5(path, scope, kind, content, content='documents', content_rowid='id')"
        )
        return True
    except sqlite3.OperationalError:
        return False


def rebuild_documents(
    documents: Iterable[tuple[str, str, str, str]],
    *,
    index_path: Path | None = None,
    ledger_path: Path | None = None,
    processor_version: str = "canonical-index@1",
    before_write: Callable[[str, str, str, str], None] | None = None,
) -> dict[str, int | str]:
    """Incrementally rebuild a local search index through an ingestion ledger.

    The SQLite index remains derived state. The ledger records only source keys,
    fingerprints, states, and checkpoints, so deleting the index still permits
    a repair rebuild from the source iterable.
    """
    target_index = index_path or INDEX_PATH
    target_ledger = ledger_path or target_index.parent / "ingestion.json"
    target_index.parent.mkdir(parents=True, exist_ok=True)
    work_id = stable_work_id("canonical-index", "repository")
    stage_id = stable_stage_id(work_id, "rebuild")
    ledger = IngestionLedger(
        target_ledger,
        source="canonical-document",
        work_id=work_id,
        stage_id=stage_id,
        processor_version=processor_version,
    )
    connection = sqlite3.connect(target_index)
    fts5 = _ensure_schema(connection)
    logical_keys: set[tuple[str, str]] = set()
    checked = queued = reprocessed = resumed = skipped = repaired = errors = 0

    def exists(path: str, scope: str) -> bool:
        return connection.execute(
            "SELECT 1 FROM documents WHERE path=? AND scope=?", (path, scope)
        ).fetchone() is not None

    try:
        for path, scope, kind, content in documents:
            checked += 1
            logical_keys.add((path, scope))
            # Kind is part of the indexed output, so it must invalidate the
            # same way source-content changes do without changing the stable
            # logical document identity.
            fingerprint_input = json.dumps((kind, content), ensure_ascii=False, separators=(",", ":"))
            item = ledger.enqueue(f"{scope}:{path}", content=fingerprint_input)
            should_write = True
            if item["action"] == "queued":
                queued += 1
            elif item["action"] == "requeued":
                reprocessed += 1
            elif item["status"] == "queued":
                resumed += 1
            elif item["status"] == "processed":
                if exists(path, scope):
                    skipped += 1
                    ledger.checkpoint(f"{scope}:{path}", checked=checked, processed=checked - skipped - errors)
                    should_write = False
                else:
                    # The derived index may have been deleted independently of
                    # its ledger. Repair it without treating the ledger as the
                    # canonical source of truth.
                    repaired += 1
            elif item["status"] == "error":
                errors += 1
                ledger.checkpoint(f"{scope}:{path}", checked=checked, processed=checked - skipped - errors)
                should_write = False

            if not should_write:
                continue
            claimed = ledger.claim(1)
            if not claimed:
                # A processed item being repaired is intentionally not claimed;
                # its missing derived row is the observable retry condition.
                if item["status"] != "processed":
                    continue
                item_id = None
            else:
                item_id = claimed[0]["item_id"]
            try:
                if before_write is not None:
                    before_write(path, scope, kind, content)
                connection.execute(
                    "INSERT OR REPLACE INTO documents(path, scope, kind, content) VALUES (?, ?, ?, ?)",
                    (path, scope, kind, content),
                )
                connection.commit()
                if item_id is not None:
                    ledger.complete(item_id, [f"index:{scope}:{path}"])
                ledger.checkpoint(f"{scope}:{path}", checked=checked, processed=checked - skipped - errors)
            except Exception as exc:
                connection.rollback()
                if item_id is not None:
                    ledger.fail(item_id, str(exc) or exc.__class__.__name__, retryable=True)
                errors += 1
                ledger.checkpoint(f"{scope}:{path}", checked=checked, processed=checked - skipped - errors)

        stale = connection.execute("SELECT id, path, scope FROM documents").fetchall()
        removed = 0
        for row_id, path, scope in stale:
            if (path, scope) not in logical_keys:
                connection.execute("DELETE FROM documents WHERE id=?", (row_id,))
                removed += 1
        if fts5:
            # This is an external-content FTS table. Rebuild the derived FTS
            # structure from the authoritative rows; a direct DELETE against
            # this table is not portable across SQLite builds.
            connection.execute("DROP TABLE IF EXISTS documents_fts")
            connection.execute(
                "CREATE VIRTUAL TABLE documents_fts USING fts5(path, scope, kind, content, content='documents', content_rowid='id')"
            )
            connection.execute(
                "INSERT INTO documents_fts(rowid, path, scope, kind, content) SELECT id, path, scope, kind, content FROM documents"
            )
        connection.commit()
    finally:
        connection.close()
    return {
        "documents": len(logical_keys),
        "index": str(target_index),
        "fts5": int(fts5),
        "checked": checked,
        "queued": queued,
        "reprocessed": reprocessed,
        "resumed": resumed,
        "skipped": skipped,
        "repaired": repaired,
        "errors": errors,
        "removed": removed,
    }


def rebuild() -> dict[str, int | str]:
    """Incrementally rebuild the canonical local search index."""
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    return rebuild_documents(canonical_documents())


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
