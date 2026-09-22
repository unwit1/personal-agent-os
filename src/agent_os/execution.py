"""Provider-neutral execution adapters for approved local execution paths.

The workflow layer only needs to know whether an approved local cache contains
the requested result. The document cache owns its private storage and payload;
this adapter exposes only a hit, a stable cache key, and a reason.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .documents import DocumentCache, PageKey


CACHE_LOOKUP_KIND = "document_page"
PAGE_KEY_FIELDS = frozenset(
    {"file_hash", "page_index", "dpi", "rotation", "extractor", "ocr_engine", "preprocess"}
)


@dataclass(frozen=True)
class CacheLookup:
    """Sanitized result of a local cache lookup; never carries cached content."""

    hit: bool
    cache_key: str
    reason: str


def cache_lookup_problems(config: Any) -> list[str]:
    """Validate the manifest-side contract for a document cache lookup."""
    if not isinstance(config, dict):
        return ["cache_lookup must be an object"]
    if config.get("kind") != CACHE_LOOKUP_KIND:
        return ["cache_lookup.kind must be document_page"]
    key = config.get("key")
    if not isinstance(key, dict):
        return ["cache_lookup.key must be an object"]
    unknown = sorted(set(key) - PAGE_KEY_FIELDS)
    problems = [f"cache_lookup.key has unsupported field {field}" for field in unknown]
    file_hash = key.get("file_hash")
    if not isinstance(file_hash, str) or len(file_hash) != 64 or any(
        char not in "0123456789abcdef" for char in file_hash.lower()
    ):
        problems.append("cache_lookup.key.file_hash must be a SHA-256 hexadecimal digest")
    if not isinstance(key.get("page_index"), int) or key["page_index"] < 0:
        problems.append("cache_lookup.key.page_index must be a non-negative integer")
    return problems


def lookup_document_page(config: dict[str, Any], root: Path) -> CacheLookup:
    """Look up one existing local document-cache entry without exposing content."""
    problems = cache_lookup_problems(config)
    if problems:
        raise ValueError("; ".join(problems))
    key = PageKey(**config["key"])
    cache = DocumentCache(root=Path(root) / ".agent-local" / "document-cache")
    hit = cache.get(key) is not None
    return CacheLookup(
        hit=hit,
        cache_key=key.fingerprint(),
        reason="local document cache hit" if hit else "local document cache miss",
    )
