"""Universal intake: every connected data source -> a scoped directory -> an ingestion queue.

Each source adapter (mail, 3CX, ambient recordings, iPhone texts, report folders,
and any folder the operator connects) yields :class:`Item` records that point at
a readable file on disk. Items are recorded in a per-scope queue; work and
personal never share a queue, a directory or a knowledge base.

    .agent-local/intake/settings.json        scopes, directories, engine roots, folder sources
    .agent-local/intake/<scope>/queue.sqlite3   items + one delivery row per consumer

Consumers (a delivery row each, so new consumers can be added without touching sources):

* ``engine``   - the Ingester Engine knowledge base of the scope (drained automatically).
* ``classify`` - items the rules could not classify (flag ``review``); for model review.
* ``promote``  - work items whose derived, PII-free knowledge (policies, processes,
  company facts, current staff roles) may be proposed to the RTEC-HR repository as
  reviewable candidates. Nothing is promoted automatically: RTEC-HR holds no PII.

Spam and bulk items are recorded with an explicit ``skipped`` delivery and reason:
nothing disappears silently. A changed file (new content hash) is queued again.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable

from ..paths import ROOT

LOCAL = ROOT / ".agent-local" / "intake"
SETTINGS_FILE = LOCAL / "settings.json"
SCOPES = ("work", "personal")
HOME = Path.home()

DEFAULT_SETTINGS: dict[str, Any] = {
    "scopes": {
        "work": {
            "correspondence_dir": str(HOME / "Documents" / "HR" / "Correspondence"),
            "engine_root": str(HOME / "Documents" / "HR Automation Local" / "Knowledge" / "rtec-work"),
            "hr_datastore": str(HOME / "Documents" / "HR Automation Local" / "HR GUI" / "data" / "hr_datastore.sqlite"),
            "work_domains": ["4rtec.com", "ridertec.org"],
        },
        "personal": {
            "correspondence_dir": str(HOME / "Documents" / "Personal" / "Correspondence"),
            "engine_root": str(HOME / "Documents" / "Personal" / "Knowledge"),
        },
    },
    # Extra folders to watch: {"name": ..., "path": ..., "scope": "work"|"personal", "kind": "report"}
    "folders": [],
    "ambient_scope": "work",  # the capture microphone is on the HR office PC
    "engine_batch": 200,
    "classify_batch": 200,  # model reviews per scope per run (subscription, Haiku)
    "promote_batches": 1,  # 25-message knowledge-distillation batches per run (subscription)
    "disabled_sources": [],
}
SKIP_ENGINE_FLAGS = {"spam": "flagged spam", "bulk": "flagged bulk/newsletter", "not_work": "not work related"}


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def settings() -> dict[str, Any]:
    data = json.loads(json.dumps(DEFAULT_SETTINGS))
    if SETTINGS_FILE.exists():
        stored = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
        for scope, values in stored.get("scopes", {}).items():
            data["scopes"].setdefault(scope, {}).update(values)
        data.update({k: v for k, v in stored.items() if k != "scopes"})
    return data


def save_settings(data: dict[str, Any]) -> None:
    LOCAL.mkdir(parents=True, exist_ok=True)
    SETTINGS_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def check_scope(scope: str) -> str:
    if scope not in SCOPES:
        raise ValueError(f"scope must be one of {SCOPES}")
    return scope


@dataclass
class Item:
    source: str            # adapter name, e.g. "mail", "3cx", "ambient", "folder:adp-reports"
    kind: str              # email, call, voicemail, recording, transcript, text, report, document
    scope: str
    ref: str               # stable id inside the source
    path: str              # readable file on disk (what the Engine ingests)
    content_hash: str
    title: str = ""
    occurred_at: str = ""
    flag: str = ""         # work, automated, personal, bulk, spam, review ("" = unflagged)
    meta: dict[str, Any] = field(default_factory=dict)

    @property
    def item_id(self) -> str:
        return "itm_" + hashlib.sha256(f"{self.source}\x1f{self.ref}".encode()).hexdigest()[:24]


def consumers_for(item: Item) -> dict[str, tuple[str, str]]:
    """consumer -> (state, reason) for a new or changed item."""
    out: dict[str, tuple[str, str]] = {}
    if item.flag in SKIP_ENGINE_FLAGS:
        out["engine"] = ("skipped", SKIP_ENGINE_FLAGS[item.flag])
    else:
        out["engine"] = ("pending", "")
    if item.flag == "review":
        out["classify"] = ("pending", "rules undecided")
    elif item.meta.get("screen"):
        out["classify"] = ("pending", "personal-address sender: check it is work related")
    if item.scope == "work" and item.flag in ("work", "", "automated"):
        out["promote"] = ("pending", "derive PII-free company knowledge for RTEC-HR review")
    return out


class Queue:
    def __init__(self, scope: str, path: Path | None = None):
        self.scope = check_scope(scope)
        self.path = Path(path or LOCAL / scope / "queue.sqlite3")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.path, timeout=60)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.executescript("""
        CREATE TABLE IF NOT EXISTS items (
          item_id TEXT PRIMARY KEY, source TEXT, kind TEXT, ref TEXT, path TEXT, content_hash TEXT, title TEXT,
          occurred_at TEXT, flag TEXT, meta TEXT, first_seen TEXT, updated_at TEXT, present INTEGER DEFAULT 1);
        CREATE TABLE IF NOT EXISTS deliveries (
          item_id TEXT, consumer TEXT, state TEXT, reason TEXT, attempts INTEGER DEFAULT 0, content_hash TEXT,
          updated_at TEXT, result TEXT, PRIMARY KEY (item_id, consumer));
        CREATE INDEX IF NOT EXISTS deliveries_state ON deliveries(consumer, state);
        CREATE INDEX IF NOT EXISTS items_source ON items(source);
        """)

    def close(self) -> None:
        self.conn.close()

    def __enter__(self) -> "Queue":
        return self

    def __exit__(self, *exc: Any) -> None:
        self.conn.commit()
        self.close()

    def upsert(self, item: Item) -> str:
        """'new', 'changed', 'reflagged' or 'same'."""
        if item.scope != self.scope:
            raise ValueError(f"{item.source}:{item.ref} is {item.scope}, queue is {self.scope}")
        row = self.conn.execute("SELECT content_hash, flag FROM items WHERE item_id=?", (item.item_id,)).fetchone()
        stamp = now()
        values = (item.source, item.kind, item.ref, item.path, item.content_hash, item.title, item.occurred_at, item.flag,
                  json.dumps(item.meta, ensure_ascii=False), stamp)
        if row is None:
            self.conn.execute("INSERT INTO items (source,kind,ref,path,content_hash,title,occurred_at,flag,meta,updated_at,item_id,first_seen) "
                              "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", (*values, item.item_id, stamp))
            status = "new"
        elif row["content_hash"] != item.content_hash or row["flag"] != item.flag:
            self.conn.execute("UPDATE items SET source=?,kind=?,ref=?,path=?,content_hash=?,title=?,occurred_at=?,flag=?,meta=?,updated_at=?,present=1 "
                              "WHERE item_id=?", (*values, item.item_id))
            status = "changed" if row["content_hash"] != item.content_hash else "reflagged"
        else:
            self.conn.execute("UPDATE items SET path=?, meta=?, present=1 WHERE item_id=?",
                              (item.path, json.dumps(item.meta, ensure_ascii=False), item.item_id))
            have = {r["consumer"] for r in self.conn.execute("SELECT consumer FROM deliveries WHERE item_id=?", (item.item_id,))}
            for consumer, (state, reason) in consumers_for(item).items():
                if consumer not in have:  # a consumer added after this item was queued
                    self.conn.execute("INSERT INTO deliveries (item_id,consumer,state,reason,attempts,content_hash,updated_at) "
                                      "VALUES (?,?,?,?,0,?,?)", (item.item_id, consumer, state, reason, item.content_hash, stamp))
            return "same"
        for consumer, (state, reason) in consumers_for(item).items():
            old = self.conn.execute("SELECT state, content_hash FROM deliveries WHERE item_id=? AND consumer=?",
                                    (item.item_id, consumer)).fetchone()
            if old is not None and old["state"] == "done" and old["content_hash"] == item.content_hash:
                continue  # already ingested this exact content; a flag change alone does not redo it
            self.conn.execute("INSERT OR REPLACE INTO deliveries (item_id,consumer,state,reason,attempts,content_hash,updated_at) "
                              "VALUES (?,?,?,?,0,?,?)", (item.item_id, consumer, state, reason, item.content_hash, stamp))
        if status != "new":  # consumers no longer applicable after a reflag (e.g. review -> work)
            wanted = set(consumers_for(item))
            for d in self.conn.execute("SELECT consumer FROM deliveries WHERE item_id=? AND state='pending'", (item.item_id,)).fetchall():
                if d["consumer"] not in wanted:
                    self.conn.execute("UPDATE deliveries SET state='skipped', reason='no longer applies', updated_at=? "
                                      "WHERE item_id=? AND consumer=?", (stamp, item.item_id, d["consumer"]))
        return status

    def mark_missing(self, source: str, present_ids: set[str]) -> int:
        gone = [r["item_id"] for r in self.conn.execute("SELECT item_id FROM items WHERE source=? AND present=1", (source,))
                if r["item_id"] not in present_ids]
        self.conn.executemany("UPDATE items SET present=0 WHERE item_id=?", [(g,) for g in gone])
        return len(gone)

    def pending(self, consumer: str, limit: int = 100) -> list[sqlite3.Row]:
        return self.conn.execute(
            "SELECT i.*, d.attempts FROM deliveries d JOIN items i USING(item_id) WHERE d.consumer=? AND d.state IN ('pending','failed') "
            "AND d.attempts < 3 AND i.present=1 ORDER BY i.occurred_at, i.item_id LIMIT ?", (consumer, limit)).fetchall()

    def finish(self, item_ids: Iterable[str], consumer: str, state: str, result: Any = None) -> None:
        stamp = now()
        for item_id in item_ids:
            self.conn.execute("UPDATE deliveries SET state=?, attempts=attempts+?, updated_at=?, result=? WHERE item_id=? AND consumer=?",
                              (state, 1 if state == "failed" else 0, stamp, json.dumps(result)[:4000] if result is not None else None,
                               item_id, consumer))
        self.conn.commit()

    def stats(self) -> dict[str, Any]:
        out: dict[str, Any] = {"scope": self.scope, "items": {}, "deliveries": {}}
        for r in self.conn.execute("SELECT source, kind, flag, COUNT(*) n FROM items WHERE present=1 GROUP BY 1,2,3"):
            out["items"].setdefault(r["source"], {}).setdefault(r["kind"], {})[r["flag"] or "-"] = r["n"]
        for r in self.conn.execute("SELECT consumer, state, COUNT(*) n FROM deliveries GROUP BY 1,2"):
            out["deliveries"].setdefault(r["consumer"], {})[r["state"]] = r["n"]
        return out


# ---------------------------------------------------------------------------
# Collection
# ---------------------------------------------------------------------------

Adapter = Callable[[dict[str, Any]], Iterable[Item]]
ADAPTERS: dict[str, Adapter] = {}


def adapter(name: str) -> Callable[[Adapter], Adapter]:
    def wrap(fn: Adapter) -> Adapter:
        ADAPTERS[name] = fn
        return fn
    return wrap


def collect(sources: Iterable[str] | None = None) -> dict[str, Any]:
    """Run every enabled adapter and record its items in the right scope's queue."""
    from . import adapters  # noqa: F401  registers the built-in adapters

    conf = settings()
    wanted = set(sources) if sources else set(ADAPTERS) - set(conf.get("disabled_sources", []))
    queues = {scope: Queue(scope) for scope in SCOPES}
    report: dict[str, Any] = {}
    try:
        for name in sorted(wanted):
            counts = {"new": 0, "changed": 0, "reflagged": 0, "same": 0, "missing": 0}
            seen: dict[str, dict[str, set[str]]] = {}
            try:
                for item in ADAPTERS[name](conf):
                    counts[queues[check_scope(item.scope)].upsert(item)] += 1
                    seen.setdefault(item.scope, {}).setdefault(item.source, set()).add(item.item_id)
                for scope, by_source in seen.items():
                    for source, ids in by_source.items():
                        counts["missing"] += queues[scope].mark_missing(source, ids)
                for q in queues.values():
                    q.conn.commit()
            except Exception as exc:  # one broken source never blocks the others
                for q in queues.values():
                    q.conn.rollback()
                counts["error"] = f"{type(exc).__name__}: {exc}"
            report[name] = counts
    finally:
        for q in queues.values():
            q.conn.commit()
            q.close()
    return report


def status() -> dict[str, Any]:
    out = {}
    for scope in SCOPES:
        with Queue(scope) as q:
            out[scope] = q.stats()
    return out


# ---------------------------------------------------------------------------
# Draining into the Ingester Engine
# ---------------------------------------------------------------------------


def drain_engine(scope: str, limit: int | None = None) -> dict[str, Any]:
    """Ingest up to ``limit`` pending items of one scope into that scope's Engine knowledge base."""
    conf = settings()
    root = conf["scopes"][check_scope(scope)].get("engine_root")
    if not root or not (Path(root) / "INGESTER.yaml").exists():
        return {"scope": scope, "skipped": "no engine_root with INGESTER.yaml"}
    from ingester_engine.service import ServiceError  # type: ignore
    from ingester_engine.service.ingest import ingest  # type: ignore

    limit = int(limit or conf.get("engine_batch", 200))
    result: dict[str, Any] = {"scope": scope, "ingested": 0, "failed": 0, "batches": []}
    lock = _acquire(LOCAL / scope / "drain.lock")
    if lock is None:
        return {**result, "skipped": "another drain is running for this scope"}
    try:
        with Queue(scope) as q:
            rows = [r for r in q.pending("engine", limit) if Path(r["path"]).exists()]
            by_kind: dict[str, list[sqlite3.Row]] = {}
            for r in rows:
                by_kind.setdefault(r["kind"], []).append(r)
            for kind, batch in by_kind.items():
                ok, status, error = _ingest_batch(ingest, ServiceError, root, [_stage(scope, r) for r in batch], f"{kind}s")
                q.finish([r["item_id"] for r in batch], "engine", "done" if ok else "failed", {"status": status})
                for r in batch:
                    _stage_path(scope, r).unlink(missing_ok=True)
                result["ingested" if ok else "failed"] += len(batch)
                result["batches"].append({"kind": kind, "items": len(batch), "status": status, **({"error": error} if error else {})})
    finally:
        lock.unlink(missing_ok=True)
    return result


def _ingest_batch(ingest: Callable, ServiceError: type, root: str, paths: list[Path], label: str) -> tuple[bool, str, str]:
    """(ok, status, error) from the Engine service envelope {"ok", "result": {"succeeded", "report"}} or {"ok": False, "error"}."""
    try:
        envelope = ingest(root, paths=[str(p) for p in paths], label=label, workers=1)
    except ServiceError as exc:
        return False, getattr(exc, "code", "error"), str(exc)
    except Exception as exc:  # noqa: BLE001
        return False, "error", f"{type(exc).__name__}: {exc}"
    body = envelope.get("result") if isinstance(envelope.get("result"), dict) else envelope
    report = body.get("report") or body.get("inbox") or {}
    ok = bool(envelope.get("ok", True)) and bool(body.get("succeeded"))
    error = "" if ok else str(envelope.get("error") or report.get("failures") or "")[:500]
    return ok, str(report.get("status") or ("ok" if ok else "error")), error


def _acquire(path: Path) -> Path | None:
    """A lock file holding the owner's pid; a lock left by a dead process is taken over."""
    import os
    import subprocess

    path.parent.mkdir(parents=True, exist_ok=True)
    for _ in range(2):
        try:
            fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, str(os.getpid()).encode())
            os.close(fd)
            return path
        except FileExistsError:
            try:
                pid = int(path.read_text() or 0)
            except (OSError, ValueError):
                pid = 0
            alive = pid and str(pid) in subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/NH"], capture_output=True, text=True,
                                                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)).stdout
            if alive:
                return None
            path.unlink(missing_ok=True)
    return None


def _stage_path(scope: str, row: sqlite3.Row) -> Path:
    return LOCAL / scope / "staging" / f"{row['item_id']}{Path(row['path']).suffix.lower()}"


def _stage(scope: str, row: sqlite3.Row) -> Path:
    """A short-named hard link (or copy) of the item: Engine copies keep the name, and Windows paths stop at 260."""
    import os
    import shutil

    target = _stage_path(scope, row)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.unlink(missing_ok=True)
    try:
        os.link(row["path"], target)
    except OSError:
        shutil.copyfile(row["path"], target)
    return target


# ---------------------------------------------------------------------------
# The automatic pipeline (scheduled task)
# ---------------------------------------------------------------------------


def run(*, sync: bool = True, drain: bool = True, drain_limit: int | None = None, classify_limit: int | None = None) -> dict[str, Any]:
    """Pull new mail, refresh the correspondence directories and dossiers, queue everything, feed the Engine."""
    from ..mail import config as mail_config
    from ..mail import directory, sync as mail_sync

    conf = settings()
    classify_limit = conf.get("classify_batch", 200) if classify_limit is None else classify_limit
    log: dict[str, Any] = {"started_at": now()}
    if sync:
        try:
            log["mail_sync"] = {k: mail_sync().get(k) for k in ("indexed_new", "errors", "complete")}
        except Exception as exc:  # noqa: BLE001
            log["mail_sync"] = {"error": f"{type(exc).__name__}: {exc}"}
    for scope in SCOPES:
        sc = conf["scopes"][scope]
        if not sc.get("correspondence_dir") or not mail_config.db_for(scope).exists():
            continue
        try:
            log[f"directory_{scope}"] = directory.export(
                scope, Path(sc["correspondence_dir"]), datastore=Path(sc["hr_datastore"]) if sc.get("hr_datastore") else None,
                work_domains=sc.get("work_domains"),
                coverage_log=mail_config.scope_dir(scope) / "source-coverage.jsonl")
        except Exception as exc:  # noqa: BLE001
            log[f"directory_{scope}"] = {"error": f"{type(exc).__name__}: {exc}"}
    log["collect"] = collect()  # also writes Recordings/people.json (transcripts -> employees)
    log["dossiers"] = _refresh_dossiers()
    log["personnel"] = _hrgui("hrgui.core.personnel_files", "reorganize") | {
        "sync": _hrgui("hrgui.core.personnel_files", "sync")}
    if classify_limit:
        from .classify import classify

        log["classify"] = {}
        for scope in SCOPES:
            try:
                log["classify"][scope] = classify(scope, classify_limit)
            except Exception as exc:  # noqa: BLE001
                log["classify"][scope] = {"error": f"{type(exc).__name__}: {exc}"}
    if conf.get("promote_batches", 1):
        from .promote import promote

        try:
            log["promote"] = promote(conf.get("promote_batches", 1))
        except Exception as exc:  # noqa: BLE001
            log["promote"] = {"error": f"{type(exc).__name__}: {exc}"}
    if drain:
        log["engine"] = {scope: drain_engine(scope, drain_limit) for scope in SCOPES}
    log["finished_at"] = now()
    LOCAL.mkdir(parents=True, exist_ok=True)
    with (LOCAL / "runs.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(log, default=str) + "\n")
    return log


def _refresh_dossiers() -> dict[str, Any]:
    """Rebuild HR GUI dossiers so their Correspondence sections pick up new mail (HR GUI owns the dossiers)."""
    return _hrgui("hrgui.core.dossiers")


def _hrgui(module: str, *args: str) -> dict[str, Any]:
    """Run an HR GUI module (HR GUI owns dossiers and Personnel Documents): moving employee folders
    between Active/Inactive and refreshing their Correspondence copies."""
    import subprocess
    import sys

    from ..registry import get_project

    try:
        app = Path(get_project("hr-gui")["path"])
    except Exception:  # noqa: BLE001
        return {"skipped": "hr-gui project not found"}
    exe = Path(sys.executable)
    if exe.name.lower() == "pythonw.exe":
        exe = exe.with_name("python.exe")
    done = subprocess.run([str(exe), "-m", module, *args], cwd=app, capture_output=True, text=True, timeout=1800,
                          creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    return {"returncode": done.returncode, "output": (done.stdout or done.stderr)[-400:]}


__all__ = ["Item", "Queue", "adapter", "collect", "drain_engine", "run", "settings", "save_settings", "status", "asdict"]
