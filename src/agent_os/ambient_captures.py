"""Local, review-first ingestion for AgentOS Ambient Capture exports."""

from __future__ import annotations

import hashlib
import json
import re
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import ValidationError

from .paths import ROOT
from .registry import get_project

LOCAL_DIR = ROOT / ".agent-local" / "ambient-captures"
CAPTURE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


def default_ready_dir() -> Path:
    import os

    local = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    return local / "AgentOSAmbientCapture" / "ingestion" / "ready"


def _schema_paths() -> dict[str, Path]:
    project = get_project("agentos-ambient-capture")
    schemas = Path(project["path"]) / "schemas"
    return {
        "agentos.conversation_capture.v1": schemas / "conversation_capture.schema.json",
        "agentos.call_conversation.v1": schemas / "call_conversation.schema.json",
    }


def _atomic_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".part")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def import_ready(*, ready_dir: Path | None = None, local_dir: Path = LOCAL_DIR) -> dict[str, Any]:
    """Validate and archive ready exports locally, then acknowledge their exact bytes."""
    source = Path(ready_dir or default_ready_dir())
    validators = {
        key: Draft202012Validator(json.loads(path.read_text(encoding="utf-8")),
                                  format_checker=FormatChecker())
        for key, path in _schema_paths().items()
    }
    imported = updated = duplicate = errors = 0
    items = []
    for path in sorted(source.glob("*.json")) if source.exists() else []:
        try:
            item_id = path.stem
            if not CAPTURE_ID.fullmatch(item_id):
                raise ValueError("capture ID contains unsafe filename characters")
            raw = path.read_bytes()
            document = json.loads(raw.decode("utf-8"))
            schema_name = document.get("schema")
            validator = validators.get(schema_name)
            if validator is None:
                items.append({"file": path.name, "status": "unsupported_schema"})
                continue
            validator.validate(document)
            is_call = schema_name == "agentos.call_conversation.v1"
            capture_id = document.get("call_session_id") if is_call else document.get("capture_id")
            expected_stem = f"call-{capture_id}" if is_call else capture_id
            if not isinstance(capture_id, str) or expected_stem != item_id:
                raise ValueError("filename and capture ID disagree")
            if is_call and not document["complete"]:
                items.append({"file": path.name, "status": "waiting_for_complete_call"})
                continue
            digest = hashlib.sha256(raw).hexdigest()
            target = Path(local_dir) / f"{item_id}.json"
            existed = target.exists()
            was_updated = False
            if existed:
                existing = json.loads(target.read_text(encoding="utf-8"))
                if existing.get("source_sha256") != digest:
                    # A capture re-exported after reprocessing (better transcription, voices
                    # matched, corrections) replaces the stored one; earlier versions stay
                    # in "revisions", as for calls.
                    previous = {key: existing[key] for key in
                                ("source_sha256", "imported_at", "review_status", "capture")}
                    existing.setdefault("revisions", []).append(previous)
                    existing.update(source_sha256=digest,
                                    imported_at=datetime.now(UTC).isoformat(),
                                    review_status="unreviewed", capture=document)
                    _atomic_json(target, existing)
                    updated += 1
                    was_updated = True
                else:
                    duplicate += 1
            else:
                _atomic_json(target, {
                    "source": "agentos-ambient-capture",
                    "source_sha256": digest,
                    "imported_at": datetime.now(UTC).isoformat(),
                    "review_status": "unreviewed",
                    "capture": document,
                })
                imported += 1
            ack_dir = source.parent / "acknowledged"
            if is_call:
                ack = {"call_session_id": capture_id, "export_sha256": digest}
            else:
                ack = {"capture_id": capture_id, "export_sha256": digest}
            _atomic_json(ack_dir / f"{item_id}.ack.json", ack)
            items.append({"capture_id": item_id, "status": "updated" if was_updated else
                          "duplicate" if existed else "imported"})
        except ValidationError:
            errors += 1
            items.append({"file": path.name, "status": "error", "error": "schema_validation_error"})
        except (UnicodeError, json.JSONDecodeError):
            errors += 1
            items.append({"file": path.name, "status": "error", "error": "invalid_json"})
        except OSError:
            errors += 1
            items.append({"file": path.name, "status": "error", "error": "local_io_error"})
        except (ValueError, KeyError, TypeError) as exc:
            errors += 1
            items.append({"file": path.name, "status": "error",
                          "error": f"processing_error:{type(exc).__name__}"})
    return {"ready_dir": str(source), "local_archive": str(local_dir), "imported": imported,
            "updated": updated, "duplicates": duplicate, "errors": errors, "items": items}


def list_captures(*, local_dir: Path = LOCAL_DIR) -> list[dict[str, Any]]:
    """Return metadata only; transcript text stays out of status output."""
    results = []
    for path in sorted(Path(local_dir).glob("*.json")) if Path(local_dir).exists() else []:
        record = json.loads(path.read_text(encoding="utf-8"))
        capture = record["capture"]
        is_call = capture.get("schema") == "agentos.call_conversation.v1"
        results.append({"capture_id": path.stem, "started_at": capture["started_at"],
                        "ended_at": capture.get("ended_at"), "review_status": record["review_status"],
                        "segments": len(capture["segments"]), "file": path.name,
                        "kind": "call" if is_call else "capture"})
    return results


def show_capture(capture_id: str, *, local_dir: Path = LOCAL_DIR) -> dict[str, Any]:
    if not CAPTURE_ID.fullmatch(capture_id):
        raise ValueError("invalid capture ID")
    path = Path(local_dir) / f"{capture_id}.json"
    return json.loads(path.read_text(encoding="utf-8"))


def watch(*, ready_dir: Path | None = None, interval_seconds: int = 15) -> None:
    if interval_seconds < 1:
        raise ValueError("interval must be at least one second")
    while True:
        result = import_ready(ready_dir=ready_dir)
        if result["imported"] or result["errors"]:
            print(json.dumps(result, ensure_ascii=False), flush=True)
        time.sleep(interval_seconds)
