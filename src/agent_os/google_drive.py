"""Thin Google Drive record adapter backed by the provider-neutral ledger.

The connector owns Drive enumeration and content fetching. This module accepts
those provider-shaped records, derives stable identity from the Drive scope and
file ID, and lets a caller process claimed records without retaining payloads
in the ledger.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping

from .ingestion import IngestionLedger, stable_stage_id, stable_work_id


SOURCE = "google-drive"
INGESTION_PROCESSOR_VERSION = "google-drive-v1"
DriveProcessor = Callable[["GoogleDriveFile"], Iterable[str]]


def drive_source_key(drive_scope: str, file_id: str) -> str:
    """Return a deterministic logical key for one Drive file in one scope."""
    scope = _required_text(drive_scope, "drive_scope")
    identifier = _required_text(file_id, "file_id")
    # JSON encoding keeps the pair unambiguous even if a future provider scope
    # or ID contains punctuation used by a human-readable separator.
    import json

    return json.dumps([scope, identifier], ensure_ascii=False, separators=(",", ":"))


@dataclass(frozen=True)
class GoogleDriveFile:
    """Provider-shaped Drive metadata plus the fetched canonical content."""

    drive_scope: str
    file_id: str
    name: str
    parents: tuple[str, ...]
    content: bytes

    @classmethod
    def from_mapping(cls, drive_scope: str, value: Mapping[str, Any]) -> "GoogleDriveFile":
        if not isinstance(value, Mapping):
            raise ValueError("Google Drive record must be an object")
        parents = value.get("parents", ())
        if isinstance(parents, str) or not isinstance(parents, (list, tuple)):
            raise ValueError("Google Drive parents must be a list")
        content = value.get("content")
        if isinstance(content, str):
            content = content.encode("utf-8")
        elif isinstance(content, (bytes, bytearray)):
            content = bytes(content)
        else:
            raise ValueError("Google Drive content must be text or bytes")
        return cls(
            drive_scope=_required_text(drive_scope, "drive_scope"),
            file_id=_required_text(value.get("file_id", value.get("id")), "file_id"),
            name=_required_text(value.get("name", ""), "name"),
            parents=tuple(_required_text(parent, "parent") for parent in parents),
            content=content,
        )

    @property
    def source_key(self) -> str:
        return drive_source_key(self.drive_scope, self.file_id)


def sync_records(
    records: Iterable[GoogleDriveFile | Mapping[str, Any]],
    *,
    drive_scope: str,
    ledger_path: Path,
    processor: DriveProcessor | None = None,
) -> dict[str, Any]:
    """Process fetched Drive records through a restart-safe ingestion ledger.

    The optional processor is the downstream local importer. Its output
    references, not the source payload, are recorded in the ledger. A default
    processor is provided for metadata-only fixture use and records a stable
    source reference.
    """
    scope = _required_text(drive_scope, "drive_scope")
    work_id = stable_work_id(SOURCE, scope)
    stage_id = stable_stage_id(work_id, "sync")
    ledger = IngestionLedger(
        ledger_path,
        source=SOURCE,
        work_id=work_id,
        stage_id=stage_id,
        processor_version=INGESTION_PROCESSOR_VERSION,
    )
    process = processor or _default_processor
    stats = {
        "drive_scope": scope,
        "checked": 0,
        "indexed_new": 0,
        "reprocessed": 0,
        "resumed": 0,
        "skipped": 0,
        "errors": 0,
    }

    for raw_record in records:
        record = raw_record if isinstance(raw_record, GoogleDriveFile) else GoogleDriveFile.from_mapping(scope, raw_record)
        if record.drive_scope != scope:
            raise ValueError("Google Drive record scope does not match the sync scope")
        stats["checked"] += 1
        result = ledger.enqueue(record.source_key, content=record.content)
        action = result["action"]
        if action == "queued":
            stats["indexed_new"] += 1
        elif action == "requeued":
            stats["reprocessed"] += 1
        elif result["status"] == "queued":
            stats["resumed"] += 1
        elif result["status"] == "processed":
            stats["skipped"] += 1
            ledger.checkpoint(record.source_key, checked=stats["checked"], processed=stats["checked"] - stats["skipped"] - stats["errors"])
            continue
        elif result["status"] == "error":
            stats["errors"] += 1
            ledger.checkpoint(record.source_key, checked=stats["checked"], processed=stats["checked"] - stats["skipped"] - stats["errors"])
            continue

        claimed = ledger.claim(1)
        if not claimed or claimed[0]["item_id"] != result["item_id"]:
            raise RuntimeError("Google Drive ledger claim did not match the current source record")
        try:
            output_refs = list(process(record))
            ledger.complete(result["item_id"], output_refs)
            ledger.checkpoint(record.source_key, checked=stats["checked"], processed=stats["checked"] - stats["skipped"] - stats["errors"])
        except KeyboardInterrupt:
            raise
        except Exception as exc:
            ledger.fail(result["item_id"], str(exc) or exc.__class__.__name__, retryable=True)
            stats["errors"] += 1
            ledger.checkpoint(record.source_key, checked=stats["checked"], processed=stats["checked"] - stats["skipped"] - stats["errors"])

    stats["checkpoint"] = ledger.status()["checkpoint"]
    return stats


def _default_processor(record: GoogleDriveFile) -> list[str]:
    return [f"drive:{record.source_key}"]


def _required_text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty string")
    return value

