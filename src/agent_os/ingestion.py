"""Small, provider-neutral primitives for restart-safe ingestion.

The ledger stores metadata about work, never the source payload.  Callers keep
their source records and derived artifacts elsewhere and record only stable
identifiers, hashes, state, and output references here.  One worker should own
a ledger at a time; opening it again recovers claims left in ``processing`` by
an interrupted worker.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from .storage import load_json, write_json


SCHEMA = "personal-agent/ingestion-ledger/v1"
VERSION = 1
ITEM_STATUSES = ("queued", "processing", "processed", "error")
_MISSING = object()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _digest(kind: str, *parts: object) -> str:
    """Hash typed parts so concatenation ambiguity cannot create collisions."""
    payload = json.dumps([kind, *parts], ensure_ascii=False, separators=(",", ":"), sort_keys=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def stable_work_id(source: str, scope: str) -> str:
    return f"work-{_digest('work', source, scope)[:24]}"


def stable_run_id(work_id: str, stage_id: str, run_key: str = "default") -> str:
    return f"run-{_digest('run', work_id, stage_id, run_key)[:24]}"


def stable_stage_id(work_id: str, stage: str) -> str:
    return f"stage-{_digest('stage', work_id, stage)[:24]}"


def stable_item_id(source: str, source_key: str) -> str:
    return f"item-{_digest('item', source, source_key)[:24]}"


def content_fingerprint(content: str | bytes) -> str:
    """Return a content hash without retaining the content."""
    data = content.encode("utf-8") if isinstance(content, str) else bytes(content)
    return hashlib.sha256(data).hexdigest()


def processing_fingerprint(content_hash: str, processor_version: str) -> str:
    return _digest("processing", content_hash, processor_version)


def _primitive(value: Any) -> bool:
    return value is None or isinstance(value, (bool, int, float, str))


class IngestionLedger:
    """Atomic JSON ledger for one logical ingestion work item.

    ``source_key`` identifies the logical source record.  A changed content
    hash or processor version requeues that same item ID, while an unchanged
    fingerprint is a deterministic no-op.  The file is intentionally compact
    and suitable for a gitignored local directory such as ``.agent-local``.
    """

    def __init__(
        self,
        path: Path,
        *,
        source: str,
        work_id: str,
        stage_id: str,
        processor_version: str,
    ) -> None:
        self.path = Path(path)
        self.source = source
        self.work_id = work_id
        self.stage_id = stage_id
        self.processor_version = processor_version
        if self.path.exists():
            self._state = self._load()
            self._check_identity()
            if self._state.get("processor_version") != self.processor_version:
                # The default processor may legitimately advance. Existing
                # items retain their recorded version until they are seen
                # again and reconciled by enqueue().
                self._state["processor_version"] = self.processor_version
                self._save()
            self._recover_interrupted()
        else:
            now = _now()
            self._state = {
                "schema": SCHEMA,
                "version": VERSION,
                "source": source,
                "work_id": work_id,
                "stage_id": stage_id,
                "processor_version": processor_version,
                "created_at": now,
                "updated_at": now,
                "checkpoint": {"cursor": None, "sequence": 0},
                "items": {},
            }
            self._save()

    def _load(self) -> dict[str, Any]:
        state = load_json(self.path)
        if not isinstance(state, dict) or state.get("schema") != SCHEMA or state.get("version") != VERSION:
            raise ValueError(f"invalid ingestion ledger: {self.path}")
        if not isinstance(state.get("items"), dict) or not isinstance(state.get("checkpoint"), dict):
            raise ValueError(f"invalid ingestion ledger collections: {self.path}")
        return state

    def _check_identity(self) -> None:
        for key, expected in {
            "source": self.source,
            "work_id": self.work_id,
            "stage_id": self.stage_id,
        }.items():
            if self._state.get(key) != expected:
                raise ValueError(f"ledger identity mismatch for {key}: {self.path}")

    def _save(self) -> None:
        self._state["updated_at"] = _now()
        write_json(self.path, self._state)

    def _recover_interrupted(self) -> None:
        recovered = 0
        for item in self._state["items"].values():
            if item.get("status") == "processing":
                item["status"] = "queued"
                item["recovered_at"] = _now()
                recovered += 1
        if recovered:
            self._save()

    def enqueue(
        self,
        source_key: str,
        *,
        content: str | bytes | None = None,
        content_hash: str | None = None,
        processor_version: str | None = None,
    ) -> dict[str, Any]:
        """Add or reconcile one source record without storing its payload."""
        if not str(source_key).strip():
            raise ValueError("source_key must not be empty")
        if (content is None) == (content_hash is None):
            raise ValueError("provide exactly one of content or content_hash")
        version = processor_version or self.processor_version
        if not str(version).strip():
            raise ValueError("processor_version must not be empty")
        if content_hash is None:
            content_hash = content_fingerprint(content)  # type: ignore[arg-type]
        if len(content_hash) != 64 or any(char not in "0123456789abcdef" for char in content_hash.lower()):
            raise ValueError("content_hash must be a SHA-256 hexadecimal digest")
        item_id = stable_item_id(self.source, source_key)
        fingerprint = processing_fingerprint(content_hash, version)
        existing = self._state["items"].get(item_id)
        if existing and existing.get("fingerprint") == fingerprint:
            return {"item_id": item_id, "action": "duplicate", "status": existing.get("status")}

        now = _now()
        revision = int(existing.get("revision", 0)) + 1 if existing else 1
        self._state["items"][item_id] = {
            "item_id": item_id,
            "source_key": source_key,
            "content_hash": content_hash,
            "processor_version": version,
            "fingerprint": fingerprint,
            "revision": revision,
            "status": "queued",
            "attempts": 0,
            "output_refs": [],
            "error": None,
            "queued_at": now,
            "updated_at": now,
        }
        self._save()
        return {"item_id": item_id, "action": "queued" if existing is None else "requeued", "status": "queued"}

    def enqueue_many(self, items: Iterable[dict[str, Any]]) -> dict[str, int]:
        counts = Counter()
        for item in items:
            if not isinstance(item, dict):
                raise ValueError("each ingestion item must be an object")
            result = self.enqueue(
                str(item.get("source_key", "")),
                content=item.get("content"),
                content_hash=item.get("content_hash"),
                processor_version=item.get("processor_version"),
            )
            counts[result["action"]] += 1
        return dict(counts)

    def claim(self, limit: int = 1) -> list[dict[str, Any]]:
        if limit < 1:
            raise ValueError("limit must be at least 1")
        selected = []
        for item in sorted(self._state["items"].values(), key=lambda value: (value["queued_at"], value["item_id"])):
            if item["status"] != "queued":
                continue
            item["status"] = "processing"
            item["attempts"] = int(item.get("attempts", 0)) + 1
            item["claimed_at"] = _now()
            item["updated_at"] = item["claimed_at"]
            selected.append(dict(item))
            if len(selected) == limit:
                break
        if selected:
            self._save()
        return selected

    def complete(self, item_id: str, output_refs: Iterable[str] = ()) -> dict[str, Any]:
        item = self._item(item_id)
        if item["status"] == "processed":
            return dict(item)
        if item["status"] != "processing":
            raise ValueError(f"item {item_id} is not processing")
        refs = list(dict.fromkeys(str(ref) for ref in output_refs))
        item["status"] = "processed"
        item["output_refs"] = refs
        item["error"] = None
        item["processed_at"] = _now()
        item["updated_at"] = item["processed_at"]
        self._save()
        return dict(item)

    def fail(self, item_id: str, error: str, *, retryable: bool = True) -> dict[str, Any]:
        if not str(error).strip():
            raise ValueError("error must not be empty")
        item = self._item(item_id)
        if item["status"] == "processed":
            return dict(item)
        if item["status"] != "processing":
            raise ValueError(f"item {item_id} is not processing")
        item["status"] = "error"
        item["error"] = str(error)[:2000]
        item["retryable"] = bool(retryable)
        item["updated_at"] = _now()
        self._save()
        return dict(item)

    def retry_errors(self, *, item_ids: Iterable[str] | None = None) -> int:
        allowed = set(item_ids) if item_ids is not None else None
        count = 0
        for item in self._state["items"].values():
            if item["status"] != "error" or (allowed is not None and item["item_id"] not in allowed):
                continue
            if not item.get("retryable", True):
                continue
            item["status"] = "queued"
            item["error"] = None
            item["updated_at"] = _now()
            count += 1
        if count:
            self._save()
        return count

    def checkpoint(self, cursor: str | int | None, **metrics: int | float | str | bool | None) -> dict[str, Any]:
        if not _primitive(cursor) or not all(_primitive(value) for value in metrics.values()):
            raise ValueError("checkpoint cursor and metrics must be scalar values")
        sequence = int(self._state["checkpoint"].get("sequence", 0)) + 1
        self._state["checkpoint"] = {"cursor": cursor, "sequence": sequence, "metrics": dict(metrics)}
        self._save()
        return dict(self._state["checkpoint"])

    def status(self) -> dict[str, Any]:
        counts = Counter(item.get("status") for item in self._state["items"].values())
        return {
            "schema": SCHEMA,
            "source": self.source,
            "work_id": self.work_id,
            "stage_id": self.stage_id,
            "processor_version": self.processor_version,
            "checkpoint": dict(self._state["checkpoint"]),
            "items": len(self._state["items"]),
            "counts": {status: counts.get(status, 0) for status in ITEM_STATUSES},
        }

    def get(self, item_id: str) -> dict[str, Any]:
        return dict(self._item(item_id))

    def _item(self, item_id: str) -> dict[str, Any]:
        try:
            return self._state["items"][item_id]
        except KeyError as exc:
            raise KeyError(f"unknown ingestion item: {item_id}") from exc
