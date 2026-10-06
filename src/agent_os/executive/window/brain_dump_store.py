from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from . import confirm


def _utc_seconds() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class BrainDumpStore:
    """Persistent records captured from Executive window brain dumps."""

    def __init__(self, home=None) -> None:
        self.home = confirm.window_home(home)
        self.path = self.home / "brain-dump.json"

    def _load(self) -> dict[str, Any]:
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            data = {}
        if not isinstance(data, dict) or not isinstance(data.get("records"), dict):
            return {"records": {}}
        return data

    def _save(self, data: dict[str, Any]) -> None:
        confirm._write_json(self.path, data)

    def add(self, result: dict, *, tab: str) -> list[str]:
        data = self._load()
        records = data["records"]
        added: list[str] = []
        stored_tab = tab if tab in ("work", "personal") else "work"
        for record in result.get("records", []):
            if not isinstance(record, dict) or not isinstance(record.get("id"), str):
                continue
            record_id = record["id"]
            if record_id in records:
                continue
            records[record_id] = {
                **record,
                "tab": stored_tab,
                "status": "open",
                "captured_at": _utc_seconds(),
                "clarification": None,
            }
            added.append(record_id)
        for entry in result.get("clarifications", []):
            if isinstance(entry, dict) and entry.get("record_id") in added:
                records[entry["record_id"]]["clarification"] = {
                    "reason": entry["reason"],
                    "candidates": list(entry.get("candidates", [])),
                }
        if added:
            self._save(data)
        return added

    def existing_ids(self) -> set[str]:
        return set(self._load()["records"])

    def records(self, status: str | None = "open") -> list[dict]:
        values = list(self._load()["records"].values())
        if status is not None:
            values = [record for record in values if record.get("status") == status]
        return sorted(values, key=lambda record: (record.get("captured_at", ""), record.get("id", "")))

    def get(self, record_id: str) -> dict:
        record = self._load()["records"].get(record_id)
        if record is None:
            raise KeyError(f"unknown brain-dump record: {record_id}")
        return record

    def set_project(self, record_id: str, project: str) -> dict:
        data = self._load()
        record = data["records"].get(record_id)
        if record is None:
            raise KeyError(f"unknown brain-dump record: {record_id}")
        record.update(project=project, clarification=None, confidence=0.9)
        self._save(data)
        return record

    def mark_staged(self, record_id: str, staging: dict) -> dict:
        data = self._load()
        record = data["records"].get(record_id)
        if record is None:
            raise KeyError(f"unknown brain-dump record: {record_id}")
        record["status"] = "staged"
        record["staged_at"] = _utc_seconds()
        record["candidate_ids"] = [
            item["id"] for key in ("created", "duplicates")
            for item in staging.get(key, [])
        ]
        self._save(data)
        return record
