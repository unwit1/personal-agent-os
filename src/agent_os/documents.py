"""Shared document intelligence: content-addressed extraction with a local cache.

Several projects need the same expensive primitives from a page -- hash it,
decide whether it is blank, pull out embedded text, and only then pay for OCR.
Repeating that work per project, and repeating it again on every development
run, is the single largest avoidable cost in document handling.

This layer owns those primitives and a persistent cache for them. It owns no
business rules: form types, employee association, naming and date semantics
stay in the project that understands them.

Three constraints shape the design.

**The cache is an optimization, never canonical state.** Every entry point
works with the cache absent, unwritable, or corrupt. A cache miss costs time;
it never changes an answer.

**The cache is workstation-local and private.** It holds derived text from real
work documents, so it lives in a gitignored local-runtime directory, is never
committed or synced, and is never projected into Git. Only counts and sanitized
structure may cross that boundary.

**Extraction is cached; interpretation is not.** The cache key covers only what
actually determines the extracted bytes -- file content, page, render settings,
engine and preprocessing. Classifier, fingerprint, naming and date logic are
deliberately excluded, so changing how a page is *interpreted* reuses the OCR
instead of paying for it again. That is the difference between a development
loop measured in seconds and one measured in minutes.

No OCR engine is bundled. Callers pass their own extraction and OCR callables,
so this stays provider-neutral and testable without any engine installed.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterable

from .ingestion import IngestionLedger, stable_item_id, stable_stage_id, stable_work_id
from .local_paths import is_gitignored_local_path
from .paths import ROOT
from .privacy import privacy_findings


# The cache may contain derived text from real work documents, so it lives in
# the gitignored local-runtime tree and never anywhere else.
LOCAL_RUNTIME_DIR = ROOT / ".agent-local"
CACHE_DIR = LOCAL_RUNTIME_DIR / "document-cache"
CACHE_ENV = "AGENT_OS_DOCUMENT_CACHE"

CACHE_SCHEMA_VERSION = 1

# Only versions that change the extracted bytes belong here. Adding a
# classifier or fingerprint version to this map would force OCR to rerun on
# every interpretation change, which is exactly what the cache exists to avoid.
EXTRACTION_COMPONENTS = ("extractor", "ocr_engine", "preprocess")

# Interpretation layers. Named so the exclusion is explicit and testable rather
# than merely absent.
INTERPRETATION_COMPONENTS = ("classifier", "fingerprint", "naming", "dates", "packet")

DEFAULT_MAX_BYTES = 512 * 1024 * 1024
DEFAULT_MAX_AGE_DAYS = 90

_WORD = re.compile(r"[^\W\d_]{2,}", re.UNICODE)


class CachePrivacyError(RuntimeError):
    """Raised when a cache location would place private text inside Git."""


def cache_root(override: Path | None = None) -> Path:
    if override is not None:
        return Path(override)
    configured = os.environ.get(CACHE_ENV)
    return Path(configured).expanduser() if configured else CACHE_DIR


def assert_private_location(path: Path) -> None:
    """Refuse a cache location that Git would track.

    The check is structural rather than advisory: a cache placed in the
    repository would put derived work-document text into canonical history, and
    no amount of care elsewhere would undo that.
    """
    if not is_gitignored_local_path(
        path,
        allowed_roots=(".agent-local", ".agent-os", ".tmp"),
    ):
        relative = Path(path).expanduser().resolve().relative_to(ROOT.resolve())
        raise CachePrivacyError(
            f"refusing a document cache inside the repository at {relative}; "
            "the cache holds derived work-document text and must stay in a "
            "gitignored local-runtime directory"
        )


# --------------------------------------------------------------------------
# Content addressing
# --------------------------------------------------------------------------


def hash_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def hash_file(path: Path, chunk: int = 1 << 20) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(chunk), b""):
            digest.update(block)
    return digest.hexdigest()


def preprocess_signature(settings: dict[str, Any] | None) -> str:
    """Stable signature for preprocessing settings, order-independent."""
    if not settings:
        return "none"
    canonical = json.dumps(settings, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]


@dataclass(frozen=True)
class PageKey:
    """Everything that determines a page's extracted bytes, and nothing else."""

    file_hash: str
    page_index: int
    dpi: int = 300
    rotation: int = 0
    extractor: str = "none"
    ocr_engine: str = "none"
    preprocess: str = "none"

    def fingerprint(self) -> str:
        parts = [
            str(CACHE_SCHEMA_VERSION),
            self.file_hash,
            str(self.page_index),
            str(self.dpi),
            str(self.rotation),
            self.extractor,
            self.ocr_engine,
            self.preprocess,
        ]
        return hashlib.sha256("\0".join(parts).encode("utf-8")).hexdigest()

    def as_dict(self) -> dict[str, Any]:
        return {
            "file_hash": self.file_hash,
            "page_index": self.page_index,
            "dpi": self.dpi,
            "rotation": self.rotation,
            "extractor": self.extractor,
            "ocr_engine": self.ocr_engine,
            "preprocess": self.preprocess,
        }


# --------------------------------------------------------------------------
# Cheap signals
# --------------------------------------------------------------------------


def is_blank_text(text: str | None, minimum_words: int = 3) -> bool:
    """Cheap blank detection: too few real words to be a page worth reading."""
    if not text:
        return True
    return len(_WORD.findall(text)) < minimum_words


def embedded_text_is_sufficient(text: str | None, minimum_words: int = 12) -> bool:
    """Decide whether embedded text removes the need to OCR this page.

    Deliberately conservative. A page carrying a handful of words is usually a
    scanned image with a stray text layer, and treating that as sufficient
    would silently degrade accuracy to save a second.
    """
    if not text:
        return False
    return len(_WORD.findall(text)) >= minimum_words


# Structural vocabulary: the words a *form* uses, never the words a *person*
# supplies. Membership is an allowlist, so a value someone filled in cannot
# reach a signature no matter how often it repeats on the page.
FORM_VOCABULARY: frozenset[str] = frozenset(
    {
        "acknowledgement", "action", "address", "agreement", "amount", "applicant",
        "application", "approval", "approved", "authorization", "benefits", "box",
        "certification", "check", "city", "class", "code", "comments", "company",
        "complete", "completed", "confidential", "contact", "continued", "copy",
        "date", "department", "description", "detail", "details", "division",
        "document", "effective", "employee", "employer", "employment", "ending",
        "evaluation", "event", "exempt", "expiration", "federal", "form", "full",
        "general", "group", "hire", "hours", "identification", "information",
        "initial", "instructions", "job", "level", "list", "location", "manager",
        "name", "notice", "number", "office", "official", "other", "page", "part",
        "pay", "payroll", "performance", "period", "personnel", "phone", "plan",
        "please", "policy", "position", "print", "printed", "program", "purpose",
        "quarter", "rate", "reason", "record", "reference", "region", "report",
        "request", "required", "review", "reviewer", "revision", "role", "salary",
        "schedule", "section", "shift", "signature", "signed", "staff", "start",
        "state", "statement", "status", "supervisor", "termination", "title",
        "total", "training", "type", "unit", "verification", "week", "witness",
        "year", "zip",
    }
)


def structural_fingerprint(
    text: str | None,
    limit: int = 24,
    vocabulary: frozenset[str] | None = None,
) -> dict[str, Any]:
    """A privacy-safe structural signature of a page.

    Anchors come from an allowlisted form vocabulary, not from repetition.
    Repetition within a single page is not evidence of boilerplate: a person's
    name recurs naturally on a form -- in the name field, on the signature
    line, inside an email address -- and treating that as structure would put
    their identity into a shared signature.

    Building the signature from vocabulary alone also makes it a genuine
    *template* signature: two copies of the same form filled in by different
    people produce the same value, which is what template reuse needs and what
    keeps employee-specific values out of it.
    """
    allowed = FORM_VOCABULARY if vocabulary is None else vocabulary
    words = _WORD.findall((text or "").casefold())
    counts: dict[str, int] = {}
    for word in words:
        counts[word] = counts.get(word, 0) + 1
    anchors = sorted(word for word in counts if word in allowed)[:limit]
    signature = hashlib.sha256("\n".join(anchors).encode("utf-8")).hexdigest()
    return {
        "word_count": len(words),
        "distinct_words": len(counts),
        "anchor_terms": anchors,
        "signature": signature,
    }


# --------------------------------------------------------------------------
# Telemetry
# --------------------------------------------------------------------------


@dataclass
class Telemetry:
    """Compact counts only. Never page content, never a filename."""

    pages: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    blank_skips: int = 0
    embedded_text_pages: int = 0
    ocr_pages: int = 0
    cache_writes: int = 0
    cache_errors: int = 0
    seconds_saved: float = 0.0
    invalidations: dict[str, int] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "pages": self.pages,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "blank_skips": self.blank_skips,
            "embedded_text_pages": self.embedded_text_pages,
            "ocr_pages": self.ocr_pages,
            "cache_writes": self.cache_writes,
            "cache_errors": self.cache_errors,
            "seconds_saved": round(self.seconds_saved, 3),
            "invalidations": dict(sorted(self.invalidations.items())),
            "cache_hit_rate": round(self.cache_hits / self.pages, 3) if self.pages else 0.0,
        }


# --------------------------------------------------------------------------
# Cache
# --------------------------------------------------------------------------


class DocumentCache:
    """Persistent, content-addressed page-extraction cache.

    Every method degrades to a miss rather than raising. A cache that cannot be
    read, written, or parsed must slow the caller down, never break it.
    """

    def __init__(self, root: Path | None = None, enabled: bool = True) -> None:
        self.root = cache_root(root)
        assert_private_location(self.root)
        self.enabled = enabled
        self.telemetry = Telemetry()

    # -- storage -------------------------------------------------------
    def _path(self, key: PageKey) -> Path:
        digest = key.fingerprint()
        return self.root / digest[:2] / f"{digest}.json"

    def get(self, key: PageKey) -> dict[str, Any] | None:
        if not self.enabled:
            return None
        path = self._path(key)
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        if record.get("schema_version") != CACHE_SCHEMA_VERSION:
            return None
        if record.get("key") != key.as_dict():
            # A digest collision or a hand-edited file: treat as a miss.
            return None
        return record

    def put(self, key: PageKey, payload: dict[str, Any]) -> bool:
        if not self.enabled:
            return False
        record = {
            "schema_version": CACHE_SCHEMA_VERSION,
            "key": key.as_dict(),
            "stored_at": time.time(),
            **payload,
        }
        path = self._path(key)
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            temporary = path.with_suffix(".tmp")
            temporary.write_text(json.dumps(record, ensure_ascii=False), encoding="utf-8")
            os.replace(temporary, path)
        except OSError:
            self.telemetry.cache_errors += 1
            return False
        self.telemetry.cache_writes += 1
        return True

    # -- maintenance ---------------------------------------------------
    def entries(self) -> Iterable[Path]:
        if not self.root.exists():
            return []
        return sorted(self.root.rglob("*.json"))

    def stats(self) -> dict[str, Any]:
        total = 0
        count = 0
        oldest: float | None = None
        for path in self.entries():
            try:
                stat = path.stat()
            except OSError:
                continue
            count += 1
            total += stat.st_size
            oldest = stat.st_mtime if oldest is None else min(oldest, stat.st_mtime)
        return {
            "location": str(self.root),
            "private_local_only": True,
            "exists": self.root.exists(),
            "entries": count,
            "bytes": total,
            "oldest_entry_age_days": round((time.time() - oldest) / 86400, 2) if oldest else None,
        }

    def clear(self) -> dict[str, Any]:
        removed = sum(1 for _ in self.entries())
        shutil.rmtree(self.root, ignore_errors=True)
        return {"cleared": True, "removed_entries": removed, "location": str(self.root)}

    def prune(self, max_bytes: int = DEFAULT_MAX_BYTES, max_age_days: int = DEFAULT_MAX_AGE_DAYS) -> dict[str, Any]:
        """Enforce retention: drop the oldest entries past age or size limits."""
        now = time.time()
        records: list[tuple[float, int, Path]] = []
        for path in self.entries():
            try:
                stat = path.stat()
            except OSError:
                continue
            records.append((stat.st_mtime, stat.st_size, path))
        removed = 0
        freed = 0
        keep: list[tuple[float, int, Path]] = []
        for mtime, size, path in records:
            if (now - mtime) / 86400 > max_age_days:
                try:
                    path.unlink()
                    removed += 1
                    freed += size
                except OSError:
                    pass
            else:
                keep.append((mtime, size, path))
        keep.sort()  # oldest first
        total = sum(size for _, size, _ in keep)
        while total > max_bytes and keep:
            mtime, size, path = keep.pop(0)
            try:
                path.unlink()
                removed += 1
                freed += size
                total -= size
            except OSError:
                break
        return {"removed_entries": removed, "freed_bytes": freed, "remaining_bytes": total}

    def invalidate_file(self, file_hash: str) -> int:
        """Drop every cached page of one document."""
        removed = 0
        for path in self.entries():
            try:
                record = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if record.get("key", {}).get("file_hash") == file_hash:
                try:
                    path.unlink()
                    removed += 1
                except OSError:
                    pass
        return removed


# --------------------------------------------------------------------------
# Extraction routing
# --------------------------------------------------------------------------


def extract_page(
    key: PageKey,
    embedded_text: Callable[[], str | None] | None = None,
    ocr: Callable[[], str | None] | None = None,
    cache: DocumentCache | None = None,
    minimum_embedded_words: int = 12,
) -> dict[str, Any]:
    """Resolve one page's text by the cheapest route that can be trusted.

    Order: cache, then embedded text, then OCR. Each step is skipped when the
    previous one already answered, and the route taken is reported so callers
    can measure where the cost actually went.

    The callables are supplied by the caller, so no OCR engine is bundled and
    the routing is testable without one installed.
    """
    store = cache if cache is not None else DocumentCache()
    store.telemetry.pages += 1

    cached = store.get(key)
    if cached is not None:
        store.telemetry.cache_hits += 1
        store.telemetry.seconds_saved += float(cached.get("elapsed_seconds") or 0.0)
        return {**cached, "route": "cache", "cached": True}
    store.telemetry.cache_misses += 1

    started = time.monotonic()
    text: str | None = None
    route = "none"

    if embedded_text is not None:
        try:
            text = embedded_text()
        except Exception:  # noqa: BLE001 - a failed extractor must not break the page
            text = None
        if embedded_text_is_sufficient(text, minimum_embedded_words):
            route = "embedded_text"
            store.telemetry.embedded_text_pages += 1

    if route == "none":
        if is_blank_text(text) and embedded_text is not None and ocr is None:
            route = "blank"
            store.telemetry.blank_skips += 1
        elif ocr is not None:
            try:
                ocr_text = ocr()
            except Exception:  # noqa: BLE001 - OCR failure degrades, never crashes
                ocr_text = None
            if ocr_text is not None:
                text = ocr_text
            route = "ocr"
            store.telemetry.ocr_pages += 1
            if is_blank_text(text):
                store.telemetry.blank_skips += 1
        else:
            route = "blank" if is_blank_text(text) else "embedded_text"
            if route == "blank":
                store.telemetry.blank_skips += 1
            else:
                store.telemetry.embedded_text_pages += 1

    elapsed = time.monotonic() - started
    payload = {
        "text": text or "",
        "route": route,
        "blank": is_blank_text(text),
        "structure": structural_fingerprint(text),
        "elapsed_seconds": round(elapsed, 4),
    }
    store.put(key, payload)
    return {**payload, "cached": False}


@dataclass(frozen=True)
class PageInput:
    """One local document page handed to the resumable batch seam."""

    source_key: str
    content: bytes
    key: PageKey
    embedded_text: Callable[[], str | None] | None = None
    ocr: Callable[[], str | None] | None = None


def extract_batch(
    pages: Iterable[PageInput],
    *,
    batch_id: str,
    cache: DocumentCache | None = None,
    ledger_path: Path | None = None,
    processor_version: str = "document-extract@1",
) -> dict[str, Any]:
    """Extract a local page batch through a restart-safe ingestion ledger.

    The ledger records that extraction for a page fingerprint finished, while
    ``extract_page`` remains responsible for embedded-text/OCR routing and its
    content-addressed cache. Reopening the same local ledger resumes work.
    """
    if not str(batch_id).strip():
        raise ValueError("batch_id must not be empty")
    store = cache if cache is not None else DocumentCache()
    work_id = stable_work_id("documents", batch_id)
    stage_id = stable_stage_id(work_id, "extract")
    target_ledger = ledger_path or (store.root.parent / "document-batches" / f"{batch_id}.json")
    assert_private_location(target_ledger)
    ledger = IngestionLedger(
        target_ledger,
        source="document-page",
        work_id=work_id,
        stage_id=stage_id,
        processor_version=processor_version,
    )
    results: dict[str, dict[str, Any]] = {}
    checked = newly_queued = reprocessed = resumed = skipped = errors = 0
    for page in pages:
        if not isinstance(page, PageInput):
            raise ValueError("document batch pages must be PageInput instances")
        checked += 1
        item = ledger.enqueue(page.source_key, content=page.content)
        if item["action"] == "queued":
            newly_queued += 1
        elif item["action"] == "requeued":
            reprocessed += 1
        elif item["status"] == "queued":
            resumed += 1
        elif item["status"] == "processed":
            skipped += 1
            results[page.source_key] = extract_page(page.key, page.embedded_text, page.ocr, store)
            ledger.checkpoint(page.source_key, checked=checked, processed=checked - skipped - errors)
            continue
        elif item["status"] == "error":
            errors += 1
            ledger.checkpoint(page.source_key, checked=checked, processed=checked - skipped - errors)
            continue

        claimed = ledger.claim(1)
        if not claimed:
            continue
        item_id = claimed[0]["item_id"]
        try:
            result = extract_page(page.key, page.embedded_text, page.ocr, store)
            results[page.source_key] = result
            ledger.complete(item_id, [f"page:{stable_item_id('document-page', page.source_key)}"])
            ledger.checkpoint(page.source_key, checked=checked, processed=checked - skipped - errors, route=result["route"])
        except Exception as exc:
            ledger.fail(item_id, str(exc) or exc.__class__.__name__, retryable=True)
            errors += 1
            ledger.checkpoint(page.source_key, checked=checked, processed=checked - skipped - errors)
    return {
        "batch_id": batch_id,
        "checked": checked,
        "queued": newly_queued,
        "reprocessed": reprocessed,
        "resumed": resumed,
        "skipped": skipped,
        "errors": errors,
        "results": results,
    }


def cache_status_safe(cache: DocumentCache | None = None) -> dict[str, Any]:
    """Cache status without the absolute path.

    The location is useful locally and is exactly the kind of machine-specific
    detail that must not travel to a client or a report.
    """
    store = cache if cache is not None else DocumentCache()
    stats = store.stats()
    return {
        "exists": stats["exists"],
        "entries": stats["entries"],
        "bytes": stats["bytes"],
        "oldest_entry_age_days": stats["oldest_entry_age_days"],
        "private_local_only": True,
        "committed_to_git": False,
    }


def sanitized_report(telemetry: Telemetry, cache: DocumentCache | None = None) -> dict[str, Any]:
    """The only shape of this data allowed to leave the private boundary.

    Counts and rates, never text, never a path, never a document identity.
    """
    report: dict[str, Any] = {
        "schema": "personal-agent/document-telemetry/v1",
        "counts": telemetry.as_dict(),
        "contains_document_content": False,
    }
    if cache is not None:
        stats = cache.stats()
        report["cache"] = {"entries": stats["entries"], "bytes": stats["bytes"]}
    findings = privacy_findings(report)
    if findings:  # pragma: no cover - defensive; counts cannot trip the gate
        raise ValueError(f"document telemetry rejected by privacy gate: {', '.join(findings)}")
    return report
