from __future__ import annotations

import json
import os
import re
import secrets
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from ..outbox import DEFAULT_DIR as _OUTBOX_DIR

ENV_HOME = "AGENT_OS_EXECUTIVE_WINDOW_HOME"
DEFAULT_TTL_SECONDS = 900

_TOKEN_RE = re.compile(r"^[A-Za-z0-9_\-]{16,128}$")


def window_home(home: Path | str | None = None) -> Path:
    """Explicit home, else $AGENT_OS_EXECUTIVE_WINDOW_HOME, else beside the outbox."""
    if home is not None:
        return Path(home)
    env = os.environ.get(ENV_HOME)
    if env:
        return Path(env)
    return _OUTBOX_DIR.parent / "executive-window"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _parse_time(value: Any) -> datetime:
    """Parse an ISO time (or accept a datetime); naive values are taken as UTC."""
    if isinstance(value, datetime):
        moment = value
    elif isinstance(value, str):
        moment = datetime.fromisoformat(value.replace("Z", "+00:00"))
    else:
        raise ValueError("expected an ISO datetime")
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    return moment


def _write_json(path: Path, data: Any) -> None:
    """Atomic write: temp file in the same dir, fsync, then replace."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".tmp-", suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(data, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


class PendingStore:
    """On-disk store of previewed consequential actions awaiting operator Confirm.

    Records live in <home>/pending/<token>.json so the server and any other
    process share them. A token is redeemable exactly once via take().
    """

    def __init__(self, home: Path | str | None = None, ttl_seconds: float = DEFAULT_TTL_SECONDS) -> None:
        self.home = window_home(home)
        self.pending_dir = self.home / "pending"
        self.audit_path = self.home / "audit.jsonl"
        self.ttl_seconds = ttl_seconds

    def _path(self, token: str) -> Path:
        if not isinstance(token, str) or not _TOKEN_RE.match(token):
            raise KeyError("unknown token")
        return self.pending_dir / f"{token}.json"

    def _expired(self, record: dict[str, Any], now: datetime | None = None) -> bool:
        try:
            created = _parse_time(record.get("created_at"))
        except ValueError:
            return True
        now = _parse_time(now) if now is not None else _utcnow()
        return now - created > timedelta(seconds=self.ttl_seconds)

    def create(self, action_id: str, item: Any, params: Any, preview: Any) -> str:
        token = secrets.token_urlsafe(24)
        record = {
            "action_id": action_id,
            "item": item,
            "params": params,
            "preview": preview,
            "created_at": _utcnow().isoformat(),
        }
        _write_json(self._path(token), record)
        return token

    def list(self, now: datetime | None = None) -> list[dict[str, Any]]:
        if not self.pending_dir.is_dir():
            return []
        out = []
        for path in sorted(self.pending_dir.glob("*.json")):
            if not _TOKEN_RE.match(path.stem):
                continue
            try:
                record = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            if not isinstance(record, dict) or self._expired(record, now):
                continue
            out.append({**record, "token": path.stem})
        out.sort(key=lambda r: str(r.get("created_at", "")))
        return out

    def take(self, token: str, now: datetime | None = None) -> dict[str, Any]:
        """Atomically claim and delete a record; raises KeyError if unknown, used or expired."""
        path = self._path(token)
        claimed = path.with_name(f".taken-{secrets.token_hex(8)}-{path.name}")
        try:
            # Rename is atomic: only one caller can move the file away.
            os.rename(path, claimed)
        except FileNotFoundError as exc:
            raise KeyError("unknown or already used token") from exc
        try:
            record = json.loads(claimed.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise KeyError("unreadable pending record") from exc
        finally:
            try:
                claimed.unlink()
            except OSError:
                pass
        if not isinstance(record, dict) or self._expired(record, now):
            raise KeyError("expired token")
        return {**record, "token": token}

    def audit(self, event: dict[str, Any]) -> None:
        line = {"ts": _utcnow().isoformat(timespec="seconds"), **event}
        self.home.mkdir(parents=True, exist_ok=True)
        with self.audit_path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(line, sort_keys=True, default=str) + "\n")


class ItemState:
    """Operator dismiss/snooze decisions for outstanding items, kept in state.json."""

    def __init__(self, home: Path | str | None = None) -> None:
        self.home = window_home(home)
        self.path = self.home / "state.json"

    def _load(self) -> dict[str, Any]:
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            data = {}
        if not isinstance(data, dict):
            data = {}
        for key in ("dismissed", "snoozed"):
            if not isinstance(data.get(key), dict):
                data[key] = {}
        return data

    def dismiss(self, item_id: str) -> None:
        data = self._load()
        data["dismissed"][item_id] = _utcnow().isoformat(timespec="seconds")
        data["snoozed"].pop(item_id, None)
        _write_json(self.path, data)

    def snooze(self, item_id: str, until_iso: str) -> None:
        until = _parse_time(until_iso)
        data = self._load()
        data["snoozed"][item_id] = until.isoformat()
        _write_json(self.path, data)

    def is_hidden(self, item_id: str, now: datetime | str | None = None) -> bool:
        data = self._load()
        if item_id in data["dismissed"]:
            return True
        until = data["snoozed"].get(item_id)
        if until is None:
            return False
        try:
            until_at = _parse_time(until)
        except ValueError:
            return False
        moment = _parse_time(now) if now is not None else _utcnow()
        return moment < until_at
