"""Resumable local-only RTEC work-file inventory and exact-hash reconciliation.

The SQLite database contains sensitive paths and file fingerprints. Its default
location is Agent OS .agent-local (gitignored); never copy it into the corpus.
The crawler never reads applicant Dashboard payloads. It hashes candidates in
bounded batches and writes a durable progress log after each invocation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


REPO = Path(__file__).resolve().parents[4]
DEFAULT_DB = REPO / ".agent-local" / "rtec-hr-reconciliation" / "audit.sqlite3"
DEFAULT_LOG = REPO / ".agent-local" / "rtec-hr-reconciliation" / "audit.log"
SCHEMA_VERSION = 1
DOC_EXTENSIONS = {
    ".txt", ".csv", ".tsv", ".pdf", ".doc", ".docx", ".xls", ".xlsx",
    ".xlsm", ".ppt", ".pptx", ".html", ".htm", ".rtf", ".png", ".jpg",
    ".jpeg", ".tif", ".tiff", ".bmp", ".zip", ".msg", ".eml",
}
SKIP_DIR_NAMES = {
    ".git", ".agent-local", ".agent-os", ".codex", "node_modules", "__pycache__", ".venv", "venv", "site-packages",
    "windows", "$recycle.bin", "system volume information", "appdata", "outputs", "output", "generated", ".build-packages", "worktrees",
    "temp", "tmp", "cache", "cache2", "caches", "cache_storage", "cache_data",
    "code cache", "gpucache", "build", "dist", "target",
}
SKIP_PATH_PARTS = {
    "job-applicant-dashboard", "job applicant dashboard", "applicant dashboard",
    "applicant", "candidate", "pending_new_hires", "pending new hires",
}
HR_TERMS = (
    "hr", "human resource", "personnel", "employee", "benefit", "payroll",
    "leave", "fmla", "workers comp", "workers-comp", "attendance", "handbook",
    "job description", "job opening", "recruit", "hiring", "applicant", "safety",
    "eeo", "aap", "training", "retirement", "unemployment", "new hire",
    "w-4", "i-9", "form", "policy", "procedure", "rtec",
)


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def connect(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA foreign_keys=ON")
    db.executescript("""
    CREATE TABLE IF NOT EXISTS audit_meta(key TEXT PRIMARY KEY, value TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS roots(path TEXT PRIMARY KEY, added_at TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'queued');
    CREATE TABLE IF NOT EXISTS directories(
      path TEXT PRIMARY KEY, root TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'queued',
      error_code TEXT, discovered_at TEXT NOT NULL, completed_at TEXT, last_entry TEXT);
    CREATE INDEX IF NOT EXISTS idx_directories_status ON directories(status, root);
    CREATE TABLE IF NOT EXISTS files(
      path TEXT PRIMARY KEY, root TEXT NOT NULL, filename TEXT NOT NULL, extension TEXT NOT NULL,
      size INTEGER NOT NULL, mtime_ns INTEGER NOT NULL, ctime_ns INTEGER,
      likely_hr INTEGER NOT NULL, sensitivity_route TEXT NOT NULL DEFAULT 'unknown',
      sha256 TEXT, hash_state TEXT NOT NULL DEFAULT 'pending', hash_fingerprint TEXT,
      source_match TEXT, matched_source_id TEXT, matched_knowledge_path TEXT, duplicate_group TEXT,
      classification TEXT NOT NULL DEFAULT 'UNKNOWN_REVIEW', review_required INTEGER NOT NULL DEFAULT 1,
      discovered_at TEXT NOT NULL, updated_at TEXT NOT NULL, error_code TEXT);
    CREATE INDEX IF NOT EXISTS idx_files_hash ON files(sha256);
    CREATE INDEX IF NOT EXISTS idx_files_hash_state ON files(hash_state, likely_hr);
    CREATE INDEX IF NOT EXISTS idx_files_classification ON files(classification, review_required);
    CREATE TABLE IF NOT EXISTS source_hashes(
      sha256 TEXT NOT NULL, source_id TEXT, knowledge_path TEXT NOT NULL,
      hash_kind TEXT NOT NULL, PRIMARY KEY(sha256, knowledge_path, hash_kind));
    CREATE INDEX IF NOT EXISTS idx_source_hashes_hash ON source_hashes(sha256);
    CREATE TABLE IF NOT EXISTS failures(
      path TEXT NOT NULL, phase TEXT NOT NULL, error_code TEXT NOT NULL,
      first_seen TEXT NOT NULL, last_seen TEXT NOT NULL, detail TEXT,
      PRIMARY KEY(path, phase));
    CREATE TABLE IF NOT EXISTS employee_documents(
      document_id TEXT PRIMARY KEY, file_path TEXT NOT NULL UNIQUE REFERENCES files(path),
      employee_key TEXT, employee_display_name TEXT, employee_match_confidence REAL,
      document_type TEXT, document_subtype TEXT, document_date TEXT, effective_date TEXT,
      expiration_date TEXT, issuer TEXT, sensitivity_category TEXT NOT NULL,
      current_historical_status TEXT, version_label TEXT, file_sha256 TEXT,
      duplicate_group TEXT, file_size INTEGER, modified_at TEXT, source_system TEXT,
      provenance_json TEXT NOT NULL DEFAULT '{}', parser TEXT, extraction_status TEXT NOT NULL DEFAULT 'not_started',
      classification_confidence REAL, review_required INTEGER NOT NULL DEFAULT 1,
      gui_known INTEGER NOT NULL DEFAULT 0, created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS knowledge_gaps(
      gap_id TEXT PRIMARY KEY, domain TEXT NOT NULL, question TEXT NOT NULL,
      evidence_summary TEXT NOT NULL, source_refs_json TEXT NOT NULL DEFAULT '[]',
      process_known INTEGER NOT NULL DEFAULT 0, form_known INTEGER NOT NULL DEFAULT 0,
      system_of_record_known INTEGER NOT NULL DEFAULT 0, gui_support_known INTEGER NOT NULL DEFAULT 0,
      automation_support_known INTEGER NOT NULL DEFAULT 0, currentness TEXT NOT NULL DEFAULT 'unknown',
      confidence REAL, status TEXT NOT NULL DEFAULT 'open', created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS checkpoints(
      id INTEGER PRIMARY KEY AUTOINCREMENT, at TEXT NOT NULL, phase TEXT NOT NULL,
      roots INTEGER NOT NULL, directories_done INTEGER NOT NULL, files_discovered INTEGER NOT NULL,
      files_hashed INTEGER NOT NULL, exact_matches INTEGER NOT NULL, duplicates INTEGER NOT NULL,
      failures INTEGER NOT NULL, note TEXT);
    CREATE VIEW IF NOT EXISTS duplicate_groups AS
      SELECT duplicate_group, COUNT(*) AS member_count, MIN(sha256) AS sha256
      FROM files WHERE duplicate_group IS NOT NULL GROUP BY duplicate_group;
    CREATE VIEW IF NOT EXISTS review_queue AS
      SELECT path,filename,extension,sensitivity_route,classification,error_code,updated_at
      FROM files WHERE likely_hr=1 AND (review_required=1 OR classification='UNKNOWN_REVIEW' OR error_code IS NOT NULL);
    """)
    directory_columns = {row[1] for row in db.execute("PRAGMA table_info(directories)")}
    if "last_entry" not in directory_columns:
        db.execute("ALTER TABLE directories ADD COLUMN last_entry TEXT")
    file_columns = {row[1] for row in db.execute("PRAGMA table_info(files)")}
    if "matched_knowledge_path" not in file_columns:
        db.execute("ALTER TABLE files ADD COLUMN matched_knowledge_path TEXT")
    db.execute("INSERT OR IGNORE INTO audit_meta(key,value) VALUES('schema_version',?)", (str(SCHEMA_VERSION),))
    db.commit()
    return db


def default_roots() -> list[Path]:
    home = Path(os.environ.get("USERPROFILE", str(Path.home())))
    roots = [home / name for name in ("Desktop", "Documents", "Downloads", "OneDrive")]
    roots.extend([home / name for name in ("Google Drive", "GoogleDrive", "My Drive")])
    try:
        roots.extend(p for p in home.iterdir() if p.is_dir() and p.name.casefold().startswith("onedrive"))
    except OSError:
        pass
    roots.extend([
        home / "GitHub" / "personal-agent-os",
        home / "Projects" / "HR GUI",
        home / "Projects" / "HR GUI New Hire Intake",
    ])
    # Known local HR working directory is deliberately local and is not the
    # Applicant Dashboard or a scanner model/cache directory.
    roots.append(home / "Documents" / "HR Automation Local" / "HR GUI" / "data")
    return [p for p in roots if p.exists() and p.is_dir()]


def safe_root(path: Path) -> bool:
    if path.drive.casefold() == "r:":
        return False
    normalized = str(path.resolve()).casefold()
    return not any(part in normalized for part in SKIP_PATH_PARTS)


def blocked_directory(path: Path) -> bool:
    if path.drive.casefold() == "r:":
        return True
    if path.name.casefold() in SKIP_DIR_NAMES:
        return True
    if re.fullmatch(r"[^/\\]+\.default(?:-release|-esr)?", path.name.casefold()):
        return True
    low = str(path).casefold()
    if any(part in low for part in SKIP_PATH_PARTS):
        return True
    parts = [part.casefold() for part in path.parts]
    if "personal-agent-os" in parts:
        for index, part in enumerate(parts[:-1]):
            if part == "libraries" and parts[index + 1] in {"elder-scrolls", "skyrim-modding"}:
                return True
            if part == "projects" and parts[index + 1] not in {"rtec-hr-process-model", "hr-gui", "job-applicant-dashboard"}:
                return True
    return False


def is_reparse_point(entry) -> bool:
    try:
        attributes = getattr(entry.stat(follow_symlinks=False), "st_file_attributes", 0)
        return bool(attributes & 0x400)  # Windows FILE_ATTRIBUTE_REPARSE_POINT
    except OSError:
        return False


def add_roots(db: sqlite3.Connection, roots: Iterable[Path]) -> int:
    inserted = 0
    for root in roots:
        root = root.expanduser()
        try:
            resolved = root.resolve(strict=True)
        except (OSError, RuntimeError):
            continue
        if not resolved.is_dir() or not safe_root(resolved):
            continue
        cur = db.execute("INSERT OR IGNORE INTO roots(path,added_at) VALUES(?,?)", (str(resolved), now()))
        inserted += cur.rowcount
        db.execute("INSERT OR IGNORE INTO directories(path,root,discovered_at) VALUES(?,?,?)", (str(resolved), str(resolved), now()))
    db.commit()
    return inserted


def prune_broad_repository_roots(db: sqlite3.Connection) -> None:
    """Replace previously broad GitHub/Projects roots with explicit HR roots."""
    home = Path(os.environ.get("USERPROFILE", str(Path.home())))
    for broad in (home / "GitHub", home / "Projects"):
        key = str(broad.resolve()).casefold()
        rows = db.execute("SELECT path FROM roots").fetchall()
        for row in rows:
            if row["path"].casefold() == key:
                db.execute("DELETE FROM files WHERE root=?", (row["path"],))
                db.execute("DELETE FROM directories WHERE root=?", (row["path"],))
                db.execute("DELETE FROM roots WHERE path=?", (row["path"],))
    db.commit()


def relevance(path: Path, root: Path) -> tuple[bool, str]:
    try:
        relative = path.relative_to(root)
    except ValueError:
        relative = path
    text = " ".join([root.name, *relative.parts]).casefold()
    normalized = re.sub(r"[^a-z0-9]+", " ", text)
    likely = any(
        (term in {"hr", "form"} and re.search(rf"(?<![a-z0-9]){re.escape(term)}s?(?![a-z0-9])", normalized))
        or (term not in {"hr", "form"} and term in normalized)
        for term in HR_TERMS
    ) or "hr automation local" in str(root).casefold()
    if any(term in text for term in ("applicant", "candidate", "pending_new_hires", "pending new hires")):
        route = "restricted_applicant_excluded_from_content"
    elif "hr automation local" in str(root).casefold():
        route = "restricted_employee_metadata_only"
    elif any(term in text for term in ("employee", "personnel", "payroll", "benefit", "medical", "fmla", "discipline", "w-4", "i-9")):
        route = "restricted_employee_metadata_only"
    elif likely:
        route = "organizational_candidate_or_mixed_review"
    else:
        route = "unclassified_work_document"
    return likely, route


def refresh_relevance(db: sqlite3.Connection) -> None:
    excluded_patterns = ("%applicant%", "%candidate%", "%pending_new_hires%", "%pending new hires%")
    excluded_patterns += ("%\\.build-packages\\%", "%\\outputs\\%", "%\\output\\%", "%\\generated\\%",
                          "%\\worktrees\\%", "%\\knowledge\\libraries\\elder-scrolls\\%",
                          "%\\knowledge\\libraries\\skyrim-modding\\%", "%\\cache2\\%",
                          "%\\.default-release\\%", "%\\.default-esr\\%")
    where = " OR ".join("LOWER(path) LIKE ?" for _ in excluded_patterns)
    db.execute(f"DELETE FROM employee_documents WHERE file_path IN (SELECT path FROM files WHERE {where})", excluded_patterns)
    removed_files = db.execute(f"DELETE FROM files WHERE {where}", excluded_patterns).rowcount
    removed_dirs = db.execute(f"DELETE FROM directories WHERE {where}", excluded_patterns).rowcount
    db.execute(f"DELETE FROM failures WHERE {where}", excluded_patterns)
    db.execute("INSERT INTO audit_meta(key,value) VALUES('excluded_applicant_path_rows',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
               (str(removed_files + removed_dirs),))
    rows = db.execute("SELECT path,root,sha256 FROM files").fetchall()
    for row in rows:
        likely, route = relevance(Path(row["path"]), Path(row["root"]))
        if not likely:
            db.execute("""UPDATE files SET likely_hr=0,sensitivity_route=?,sha256=NULL,
              hash_state='not_candidate',hash_fingerprint=NULL,source_match=NULL,
              matched_source_id=NULL,matched_knowledge_path=NULL,duplicate_group=NULL,updated_at=? WHERE path=?""",
              (route, now(), row["path"]))
        else:
            db.execute("UPDATE files SET likely_hr=?,sensitivity_route=?,updated_at=? WHERE path=?",
                       (int(likely), route, now(), row["path"]))
    db.commit()


def record_file(db: sqlite3.Connection, path: Path, root: Path) -> None:
    try:
        stat = path.stat()
        if not path.is_file() or path.suffix.casefold() not in DOC_EXTENSIONS:
            return
        likely, route = relevance(path, root)
        fingerprint = f"{stat.st_size}:{stat.st_mtime_ns}"
        previous = db.execute("SELECT size,mtime_ns,sha256,hash_fingerprint FROM files WHERE path=?", (str(path),)).fetchone()
        sha = previous["sha256"] if previous and previous["hash_fingerprint"] == fingerprint else None
        hash_state = "hashed_cached" if sha else "pending"
        db.execute("""INSERT INTO files(path,root,filename,extension,size,mtime_ns,ctime_ns,likely_hr,
            sensitivity_route,sha256,hash_state,hash_fingerprint,discovered_at,updated_at)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(path) DO UPDATE SET root=excluded.root,filename=excluded.filename,
            extension=excluded.extension,size=excluded.size,mtime_ns=excluded.mtime_ns,ctime_ns=excluded.ctime_ns,
            likely_hr=excluded.likely_hr,sensitivity_route=excluded.sensitivity_route,
            sha256=CASE WHEN files.hash_fingerprint=excluded.hash_fingerprint THEN files.sha256 ELSE NULL END,
            hash_state=CASE WHEN files.hash_fingerprint=excluded.hash_fingerprint THEN files.hash_state ELSE 'pending' END,
            hash_fingerprint=CASE WHEN files.hash_fingerprint=excluded.hash_fingerprint THEN files.hash_fingerprint ELSE NULL END,
            source_match=CASE WHEN files.hash_fingerprint=excluded.hash_fingerprint THEN files.source_match ELSE NULL END,
            matched_source_id=CASE WHEN files.hash_fingerprint=excluded.hash_fingerprint THEN files.matched_source_id ELSE NULL END,
            matched_knowledge_path=CASE WHEN files.hash_fingerprint=excluded.hash_fingerprint THEN files.matched_knowledge_path ELSE NULL END,
            updated_at=excluded.updated_at""",
            (str(path), str(root), path.name, path.suffix.casefold(), stat.st_size, stat.st_mtime_ns,
             getattr(stat, "st_ctime_ns", None), int(likely), route, sha, hash_state,
             fingerprint if sha else None, now(), now()))
    except PermissionError:
        failure(db, str(path), "inventory", "PERMISSION_DENIED", "")
    except OSError as exc:
        failure(db, str(path), "inventory", "STAT_FAILED", type(exc).__name__)


def failure(db: sqlite3.Connection, path: str, phase: str, code: str, detail: str) -> None:
    stamp = now()
    db.execute("""INSERT INTO failures(path,phase,error_code,first_seen,last_seen,detail)
      VALUES(?,?,?,?,?,?) ON CONFLICT(path,phase) DO UPDATE SET
      error_code=excluded.error_code,last_seen=excluded.last_seen,detail=excluded.detail""",
      (path, phase, code, stamp, stamp, detail[:100]))


def discover_batch(db: sqlite3.Connection, max_dirs: int, max_files: int) -> tuple[int, int]:
    done = files = 0
    rows = db.execute("SELECT path,root,last_entry FROM directories WHERE status='queued' ORDER BY discovered_at,path LIMIT ?", (max_dirs,)).fetchall()
    for row in rows:
        folder, root = Path(row["path"]), Path(row["root"])
        db.execute("INSERT INTO audit_meta(key,value) VALUES('current_directory',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (str(folder),))
        if blocked_directory(folder):
            db.execute("UPDATE directories SET status='done',completed_at=?,error_code='EXCLUDED_PRIVACY_BOUNDARY' WHERE path=?", (now(), str(folder)))
            db.commit()
            done += 1
            continue
        db.execute("UPDATE directories SET status='processing' WHERE path=?", (str(folder),))
        paused = False
        last_entry = row["last_entry"]
        try:
            with os.scandir(folder) as iterator:
                entries = sorted(iterator, key=lambda item: item.name.casefold())
                for entry in entries:
                    if last_entry and entry.name.casefold() <= last_entry.casefold():
                        continue
                    if files >= max_files:
                        paused = True
                        break
                    child = Path(entry.path)
                    try:
                        if entry.is_dir(follow_symlinks=False):
                            if not is_reparse_point(entry) and not blocked_directory(child):
                                db.execute("INSERT OR IGNORE INTO directories(path,root,discovered_at) VALUES(?,?,?)", (str(child), str(root), now()))
                        elif files < max_files and entry.is_file(follow_symlinks=False):
                            record_file(db, child, root)
                            files += 1
                        last_entry = entry.name
                    except OSError as exc:
                        failure(db, str(child), "inventory", "PERMISSION_DENIED" if isinstance(exc, PermissionError) else "STAT_FAILED", type(exc).__name__)
                        last_entry = entry.name
            if paused:
                db.execute("UPDATE directories SET status='queued',last_entry=?,discovered_at=? WHERE path=?",
                           (last_entry, now(), str(folder)))
            else:
                db.execute("UPDATE directories SET status='done',completed_at=?,last_entry=NULL WHERE path=?", (now(), str(folder)))
        except PermissionError:
            failure(db, str(folder), "inventory", "PERMISSION_DENIED", "")
            db.execute("UPDATE directories SET status='error',error_code='PERMISSION_DENIED' WHERE path=?", (str(folder),))
        except OSError as exc:
            failure(db, str(folder), "inventory", "DIRECTORY_READ_FAILED", type(exc).__name__)
            db.execute("UPDATE directories SET status='error',error_code='DIRECTORY_READ_FAILED' WHERE path=?", (str(folder),))
        done += 1
        db.commit()
        if files >= max_files:
            break
    return done, files


def hash_batch(db: sqlite3.Connection, limit: int) -> int:
    rows = db.execute("""SELECT path,size,mtime_ns FROM files WHERE hash_state='pending' AND likely_hr=1
      AND sensitivity_route!='restricted_applicant_excluded_from_content' ORDER BY path LIMIT ?""", (limit,)).fetchall()
    hashed = 0
    for row in rows:
        path = Path(row["path"])
        try:
            before = path.stat()
            if before.st_size != row["size"] or before.st_mtime_ns != row["mtime_ns"]:
                db.execute("UPDATE files SET hash_state='changed_during_scan',updated_at=? WHERE path=?", (now(), row["path"]))
                continue
            digest = hashlib.sha256()
            with path.open("rb") as stream:
                for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                    digest.update(chunk)
            after = path.stat()
            if after.st_size != before.st_size or after.st_mtime_ns != before.st_mtime_ns:
                db.execute("UPDATE files SET hash_state='changed_during_hash',updated_at=? WHERE path=?", (now(), row["path"]))
                continue
            value = digest.hexdigest()
            db.execute("UPDATE files SET sha256=?,hash_state='hashed',hash_fingerprint=?,updated_at=? WHERE path=?",
                       (value, f"{after.st_size}:{after.st_mtime_ns}", now(), row["path"]))
            hashed += 1
        except PermissionError:
            failure(db, row["path"], "hash", "PERMISSION_DENIED", "")
            db.execute("UPDATE files SET hash_state='failed',error_code='PERMISSION_DENIED' WHERE path=?", (row["path"],))
        except OSError as exc:
            code = "PASSWORD_PROTECTED" if "password" in str(exc).casefold() else "READ_FAILED"
            failure(db, row["path"], "hash", code, type(exc).__name__)
            db.execute("UPDATE files SET hash_state='failed',error_code=? WHERE path=?", (code, row["path"]))
    db.commit()
    return hashed


def iter_safe_json(root: Path):
    for path in root.rglob("*.json"):
        rel = path.relative_to(root)
        if "restricted-evidence" in {part.casefold() for part in rel.parts}:
            continue
        if any(part.casefold() in {".git", "archive-corpus", "node_modules"} for part in rel.parts):
            continue
        yield path


def collect_hashes(db: sqlite3.Connection, knowledge_root: Path) -> int:
    inserted = 0
    for path in iter_safe_json(knowledge_root):
        try:
            obj = json.loads(path.read_text(encoding="utf-8-sig"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            continue
        for source_id, digest, kind in walk_hash_fields(obj, None):
            cur = db.execute("INSERT OR IGNORE INTO source_hashes(sha256,source_id,knowledge_path,hash_kind) VALUES(?,?,?,?)",
                             (digest, source_id, str(path.relative_to(REPO)), kind))
            inserted += cur.rowcount
    db.commit()
    return inserted


def walk_hash_fields(value, inherited_source):
    if isinstance(value, dict):
        source_id = value.get("source_id") or value.get("id") or inherited_source
        for key, child in value.items():
            key_low = str(key).casefold()
            if isinstance(child, str) and len(child) == 64 and all(c in "0123456789abcdefABCDEF" for c in child):
                if key_low in {"sha256", "content_sha256", "source_sha256", "file_sha256"}:
                    yield str(source_id) if source_id else None, child.casefold(), key_low
            yield from walk_hash_fields(child, source_id)
    elif isinstance(value, list):
        for child in value:
            yield from walk_hash_fields(child, inherited_source)


def reconcile_hashes(db: sqlite3.Connection) -> tuple[int, int]:
    db.execute("UPDATE files SET source_match=NULL,matched_source_id=NULL,matched_knowledge_path=NULL,duplicate_group=NULL")
    db.execute("""UPDATE files SET source_match='ALREADY_INGESTED_EXACT',matched_source_id=(
      SELECT source_id FROM source_hashes WHERE source_hashes.sha256=files.sha256 AND source_id IS NOT NULL ORDER BY knowledge_path LIMIT 1),
      matched_knowledge_path=(SELECT knowledge_path FROM source_hashes WHERE source_hashes.sha256=files.sha256 ORDER BY knowledge_path LIMIT 1)
      WHERE sha256 IN (SELECT sha256 FROM source_hashes)""")
    matched = db.execute("SELECT changes()").fetchone()[0]
    db.execute("""UPDATE files SET source_match='NEW_OR_UNMATCHED',matched_source_id=NULL
      WHERE sha256 IS NOT NULL AND source_match IS NULL""")
    db.execute("""UPDATE files SET duplicate_group='sha256:'||sha256 WHERE sha256 IN
      (SELECT sha256 FROM files GROUP BY sha256 HAVING COUNT(*)>1)""")
    duplicates = db.execute("SELECT COUNT(*) FROM files WHERE duplicate_group IS NOT NULL").fetchone()[0]
    db.commit()
    return matched, duplicates


def checkpoint(db: sqlite3.Connection, phase: str, note: str = "") -> dict:
    def count(query):
        return db.execute(query).fetchone()[0]
    stats = {
        "roots": count("SELECT COUNT(*) FROM roots"),
        "directories_done": count("SELECT COUNT(*) FROM directories WHERE status='done'"),
        "directories_queued": count("SELECT COUNT(*) FROM directories WHERE status='queued'"),
        "files_discovered": count("SELECT COUNT(*) FROM files"),
        "files_hashed": count("SELECT COUNT(*) FROM files WHERE sha256 IS NOT NULL"),
        "files_pending_hash": count("SELECT COUNT(*) FROM files WHERE hash_state='pending' AND likely_hr=1 AND sensitivity_route!='restricted_applicant_excluded_from_content'"),
        "exact_matches": count("SELECT COUNT(*) FROM files WHERE source_match='ALREADY_INGESTED_EXACT'"),
        "duplicates": count("SELECT COUNT(*) FROM files WHERE duplicate_group IS NOT NULL"),
        "duplicate_groups": count("SELECT COUNT(*) FROM duplicate_groups"),
        "duplicate_extra_copies": db.execute("SELECT COALESCE(SUM(member_count-1),0) FROM duplicate_groups").fetchone()[0],
        "source_hash_references": count("SELECT COUNT(*) FROM source_hashes"),
        "distinct_known_source_hashes": count("SELECT COUNT(DISTINCT sha256) FROM source_hashes"),
        "review_queue_items": count("SELECT COUNT(*) FROM review_queue"),
        "employee_registry_entries": count("SELECT COUNT(*) FROM employee_documents"),
        "failures": count("SELECT COUNT(*) FROM failures"),
    }
    current = db.execute("SELECT value FROM audit_meta WHERE key='current_directory'").fetchone()
    stats["current_directory"] = current[0] if current else None
    excluded = db.execute("SELECT value FROM audit_meta WHERE key='excluded_applicant_path_rows'").fetchone()
    stats["excluded_applicant_path_rows"] = int(excluded[0]) if excluded else 0
    db.execute("INSERT INTO checkpoints(at,phase,roots,directories_done,files_discovered,files_hashed,exact_matches,duplicates,failures,note) VALUES(?,?,?,?,?,?,?,?,?,?)",
               (now(), phase, stats["roots"], stats["directories_done"], stats["files_discovered"], stats["files_hashed"], stats["exact_matches"], stats["duplicates"], stats["failures"], note))
    db.commit()
    return stats


def report(stats: dict, log_path: Path, phase: str, note: str) -> None:
    summary = {"at": now(), "phase": phase, **stats, "next_action": note}
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(summary, ensure_ascii=False) + "\n")
    print(json.dumps(summary, indent=2))


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--log", type=Path, default=DEFAULT_LOG)
    parser.add_argument("--root", action="append", default=[], help="Additional explicit work root; may repeat")
    parser.add_argument("--discover", action="store_true", help="Discover root directories in one bounded pass")
    parser.add_argument("--hash", action="store_true", help="Hash a bounded batch of unchanged candidate files")
    parser.add_argument("--reconcile", action="store_true", help="Index safe Knowledge Engine source hashes and reconcile exact file hashes")
    parser.add_argument("--max-dirs", type=int, default=40)
    parser.add_argument("--max-files", type=int, default=500)
    parser.add_argument("--hash-limit", type=int, default=150)
    args = parser.parse_args(argv)
    db = connect(args.db)
    roots = default_roots() + [Path(item) for item in args.root]
    prune_broad_repository_roots(db)
    added = add_roots(db, roots)
    refresh_relevance(db)
    phases = []
    if args.discover:
        directories, files = discover_batch(db, args.max_dirs, args.max_files)
        phases.append(f"discovery: {directories} directories completed, {files} file entries observed")
    if args.hash:
        count = hash_batch(db, args.hash_limit)
        phases.append(f"hashing: {count} files hashed in this batch")
    if args.reconcile:
        inserted = collect_hashes(db, REPO / "knowledge" / "libraries" / "rtec-hr")
        matched, duplicates = reconcile_hashes(db)
        phases.append(f"reconciliation: {inserted} safe source hash references indexed; {matched} exact matches; {duplicates} duplicate members")
    phase = "+".join(x.split(":",1)[0] for x in phases) or "status"
    stats = checkpoint(db, phase, "; ".join(phases))
    note = "resume --discover until directories_queued is 0; then --hash until files_pending_hash is 0; then --reconcile" if stats["directories_queued"] or stats["files_pending_hash"] else "review exact matches, local duplicate groups and UNKNOWN_REVIEW records; do not ingest automatically"
    stats["directories_queued"] = stats.pop("directories_queued")
    stats["files_pending_hash"] = stats.pop("files_pending_hash")
    stats["roots_added_this_run"] = added
    report(stats, args.log, phase, note)
    db.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
