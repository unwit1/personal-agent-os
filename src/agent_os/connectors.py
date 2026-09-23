"""Provider-neutral, secret-safe connector registry contract (v1)."""

from __future__ import annotations

import hashlib
import json
import os
import re
import tomllib
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Iterator

from .paths import ROOT
from .privacy import privacy_findings
from .storage import write_json


REGISTRY_SCHEMA = "personal-agent/connector-registry/v1"
REGISTRY_VERSION = 1
REGISTRY_PATH = ROOT / "connectors" / "registry.json"
_IDENTIFIER = re.compile(r"^[a-z][a-z0-9._-]{0,63}$")
_SECRET_REF = re.compile(
    r"^(?:keyring|windows-credential|macos-keychain|secret-service|env):"
    r"[A-Za-z0-9][A-Za-z0-9._/-]{0,127}$"
)
_HEALTH_STATES = {"unknown", "healthy", "degraded", "unavailable"}
_REGISTRATION_STATES = {"desired", "registered", "disabled", "unsupported", "error"}
_REGISTRY_KEYS = {"schema", "version", "connectors"}
_REGISTRY_LOCK_PATH = ROOT / ".agent-local" / "connector-registry.lock"
_CONNECTOR_KEYS = {
    "id", "provider", "capabilities", "scopes", "health", "privacy_domain",
    "registrations", "secret_ref",
}


def load_connector_registry(path: Path | None = None) -> dict[str, Any]:
    """Load and validate connector metadata without reading credential stores."""
    source = Path(path) if path is not None else REGISTRY_PATH
    try:
        registry = json.loads(source.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError("connector registry contains invalid JSON") from exc
    except UnicodeError as exc:
        raise ValueError("connector registry must be UTF-8 JSON") from exc
    validate_connector_registry(registry)
    return registry


def validate_connector_registry(registry: Any) -> None:
    """Raise ValueError unless registry data conforms to the v1 contract."""
    if not isinstance(registry, dict) or set(registry) != _REGISTRY_KEYS:
        raise ValueError("connector registry must contain only schema, version, and connectors")
    if registry.get("schema") != REGISTRY_SCHEMA or type(registry.get("version")) is not int or registry["version"] != REGISTRY_VERSION:
        raise ValueError("unsupported connector registry schema or version")
    connectors = registry.get("connectors")
    if not isinstance(connectors, list):
        raise ValueError("connector registry connectors must be an array")
    seen_ids: set[str] = set()
    for connector in connectors:
        _validate_connector(connector)
        if connector["id"] in seen_ids:
            raise ValueError("connector registry contains duplicate connector IDs")
        seen_ids.add(connector["id"])


def connector_status(surface_id: str | None = None) -> dict[str, Any]:
    """Return registry metadata for clients; credential-store references stay local."""
    registry = load_connector_registry()
    connectors = []
    for connector in registry["connectors"]:
        registrations = connector["registrations"]
        if surface_id and not any(item["surface_id"] == surface_id for item in registrations):
            continue
        connectors.append(
            {
                "id": connector["id"],
                "provider": connector["provider"],
                "capabilities": connector["capabilities"],
                "scopes": connector["scopes"],
                "health": connector["health"],
                "privacy_domain": connector["privacy_domain"],
                "registrations": registrations,
                "credential_reference_configured": connector["secret_ref"] is not None,
            }
        )
    return {
        "schema": REGISTRY_SCHEMA,
        "version": REGISTRY_VERSION,
        "count": len(connectors),
        "connectors": connectors,
    }


def register_connector(
    connector: Any,
    *,
    confirm_write: bool = False,
    replace_existing: bool = False,
) -> dict[str, Any]:
    """Preview or explicitly persist desired connector metadata, never credentials."""
    _validate_connector(connector)
    if type(confirm_write) is not bool or type(replace_existing) is not bool:
        raise ValueError("confirm_write and replace_existing must be booleans")
    if connector["health"] != {"status": "unknown", "checked_at": None}:
        raise ValueError("new connector metadata must start with unknown provider health")
    if any(item["state"] != "desired" for item in connector["registrations"]):
        raise ValueError("new connector registrations must start as desired; adapters own verified states")

    connector_id = connector["id"]
    if not confirm_write:
        return {
            "written": False,
            "confirmation_required": True,
            "connector_id": connector_id,
            "replace_existing_requested": replace_existing,
        }

    with _registry_write_lock():
        registry = load_connector_registry()
        existing_index = next(
            (index for index, item in enumerate(registry["connectors"]) if item["id"] == connector_id),
            None,
        )
        if existing_index is not None:
            if registry["connectors"][existing_index] == connector:
                return {"written": False, "idempotent": True, "connector_id": connector_id}
            if not replace_existing:
                raise ValueError("connector ID already exists; set replace_existing and confirm to update it")
            registry["connectors"][existing_index] = connector
        else:
            if replace_existing:
                raise ValueError("replace_existing was set, but the connector ID does not exist")
            registry["connectors"].append(connector)

        registry["connectors"].sort(key=lambda item: item["id"])
        write_json(REGISTRY_PATH, registry)
    return {
        "written": True,
        "replaced": existing_index is not None,
        "connector_id": connector_id,
        "count": len(registry["connectors"]),
    }


@contextmanager
def _registry_write_lock() -> Iterator[None]:
    """Serialize registry read/modify/write across MCP and CLI processes."""
    _REGISTRY_LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _REGISTRY_LOCK_PATH.open("a+b") as lock_file:
        if os.name == "nt":
            import msvcrt

            lock_file.seek(0, os.SEEK_END)
            if lock_file.tell() == 0:
                lock_file.write(b"\0")
                lock_file.flush()
            lock_file.seek(0)
            msvcrt.locking(lock_file.fileno(), msvcrt.LK_LOCK, 1)
            try:
                yield
            finally:
                lock_file.seek(0)
                msvcrt.locking(lock_file.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl

            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


def connector_import_candidates(surface_id: str | None = None) -> dict[str, Any]:
    """Inventory client MCP server labels for explicit, privacy-safe import review.

    Only the configured server name and executable basename leave this function.
    Arguments, environment entries, file paths, and credential values are never
    included in the returned candidate records.
    """
    from .machine import resolve_user_path
    from .surfaces import surfaces

    selected = surfaces()
    if surface_id:
        selected = [item for item in selected if item["id"].casefold() == surface_id.casefold()]
        if not selected:
            raise KeyError(f"Unknown client surface: {surface_id}")

    grouped: dict[tuple[str, str], dict[str, Any]] = {}
    inspected_files = 0
    malformed_files = 0
    privacy_filtered = 0
    parsed_files: dict[str, Any | None] = {}

    for surface in selected:
        invocation = surface["invocation"]
        ignored_names = {str(name).casefold() for name in invocation.get("server_keys", [])}
        for location in invocation.get("registrations", []):
            path = resolve_user_path(location)
            path_key = str(path).casefold()
            if not path.is_file():
                continue
            if path_key not in parsed_files:
                try:
                    raw = path.read_text(encoding="utf-8-sig")
                    if path.suffix.casefold() == ".toml":
                        document = tomllib.loads(raw)
                    else:
                        document = json.loads(raw)
                except (OSError, UnicodeError, json.JSONDecodeError, tomllib.TOMLDecodeError):
                    malformed_files += 1
                    parsed_files[path_key] = None
                    continue
                inspected_files += 1
                parsed_files[path_key] = document
            document = parsed_files[path_key]
            if document is None:
                continue
            for name, command in _walk_mcp_servers(document):
                label = str(name).strip()
                executable = _command_basename(command)
                if not label or label.casefold() in ignored_names or not executable:
                    continue
                record = {"server_name": label[:120], "command": executable[:120]}
                if privacy_findings(record):
                    privacy_filtered += 1
                    continue
                key = (record["server_name"].casefold(), record["command"].casefold())
                candidate_id = hashlib.sha256((key[0] + "\0" + key[1]).encode("utf-8")).hexdigest()[:20]
                candidate = grouped.setdefault(
                    key,
                    {
                        "candidate_id": candidate_id,
                        "server_name": record["server_name"],
                        "command": record["command"],
                        "surfaces": [],
                        "classification": "needs_review",
                        "reason": "provider identity and allowed data scopes need explicit review",
                    },
                )
                if surface["id"] not in candidate["surfaces"]:
                    candidate["surfaces"].append(surface["id"])

    candidates = sorted(grouped.values(), key=lambda item: (item["server_name"].casefold(), item["command"].casefold()))
    return {
        "schema": "personal-agent/connector-import-candidates/v1",
        "scanned_surfaces": [item["id"] for item in selected],
        "inspected_files": inspected_files,
        "malformed_files": malformed_files,
        "privacy_filtered": privacy_filtered,
        "count": len(candidates),
        "candidates": candidates,
    }


def _walk_mcp_servers(document: Any) -> Iterator[tuple[str, Any]]:
    if isinstance(document, dict):
        for key, value in document.items():
            if key in {"mcpServers", "mcp_servers"} and isinstance(value, dict):
                for name, entry in value.items():
                    if isinstance(entry, dict):
                        yield str(name), entry.get("command")
            yield from _walk_mcp_servers(value)
    elif isinstance(document, list):
        for item in document:
            yield from _walk_mcp_servers(item)


def _command_basename(command: Any) -> str | None:
    if not isinstance(command, str) or not command.strip():
        return None
    value = command.strip()
    if value[0] in {'"', "'"}:
        quote = value[0]
        closing = value.find(quote, 1)
        if closing > 0:
            executable = value[1:closing]
        else:
            candidate = value[1:].strip()
            executable = candidate.split(None, 1)[0] if candidate else ""
        if any(char.isspace() for char in executable) and "/" not in executable and "\\" not in executable:
            executable = executable.split(None, 1)[0]
    else:
        executable = value.split(None, 1)[0]
    basename = executable.replace("\\", "/").rsplit("/", 1)[-1]
    if not re.fullmatch(r"[A-Za-z0-9._+-]{1,120}", basename):
        return None
    return basename


def _validate_connector(connector: Any) -> None:
    if not isinstance(connector, dict) or set(connector) != _CONNECTOR_KEYS:
        raise ValueError("connector entry has missing or unsupported fields")
    _identifier(connector["id"], "connector id")
    provider = connector["provider"]
    if not isinstance(provider, dict) or set(provider) != {"id", "name"}:
        raise ValueError("connector provider must contain only id and name")
    _identifier(provider["id"], "provider id")
    _label(provider["name"], "provider name")

    for field in ("capabilities", "scopes"):
        values = connector[field]
        if not isinstance(values, list) or any(not isinstance(item, str) or not item.strip() for item in values):
            raise ValueError(f"connector {field} must be an array of non-empty strings")
        if len(values) > 128 or len(values) != len(set(values)):
            raise ValueError(f"connector {field} must be unique and contain at most 128 items")
        limit = 64 if field == "capabilities" else 160
        if any(len(item) > limit for item in values):
            raise ValueError(f"connector {field} entries are too long")
        if field == "capabilities" and any(not _IDENTIFIER.fullmatch(item) for item in values):
            raise ValueError("connector capabilities must be identifiers")

    health = connector["health"]
    if not isinstance(health, dict) or set(health) != {"status", "checked_at"}:
        raise ValueError("connector health must contain only status and checked_at")
    if health["status"] not in _HEALTH_STATES:
        raise ValueError("connector health status is invalid")
    checked_at = health["checked_at"]
    if checked_at is not None:
        if not isinstance(checked_at, str):
            raise ValueError("connector health checked_at must be a timestamp or null")
        try:
            parsed = datetime.fromisoformat(checked_at.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError("connector health checked_at must be an ISO 8601 timestamp") from exc
        if parsed.tzinfo is None:
            raise ValueError("connector health checked_at must include a timezone")

    _identifier(connector["privacy_domain"], "privacy domain")
    registrations = connector["registrations"]
    if not isinstance(registrations, list) or len(registrations) > 64:
        raise ValueError("connector registrations must be an array of at most 64 entries")
    seen_surfaces: set[str] = set()
    for registration in registrations:
        if not isinstance(registration, dict) or set(registration) != {"surface_id", "state"}:
            raise ValueError("connector registration must contain only surface_id and state")
        _identifier(registration["surface_id"], "surface id")
        if registration["surface_id"] in seen_surfaces:
            raise ValueError("connector registrations contain duplicate surface IDs")
        seen_surfaces.add(registration["surface_id"])
        if registration["state"] not in _REGISTRATION_STATES:
            raise ValueError("connector registration state is invalid")

    secret_ref = connector["secret_ref"]
    if secret_ref is not None and (not isinstance(secret_ref, str) or not _SECRET_REF.fullmatch(secret_ref)):
        raise ValueError("connector secret_ref must name a supported local secret-store entry")

    if privacy_findings(connector):
        raise ValueError("connector metadata rejected by privacy checks")


def _identifier(value: Any, label: str) -> None:
    if not isinstance(value, str) or not _IDENTIFIER.fullmatch(value):
        raise ValueError(f"connector {label} is invalid")


def _label(value: Any, label: str) -> None:
    if not isinstance(value, str) or not value.strip() or len(value) > 100:
        raise ValueError(f"connector {label} is invalid")
