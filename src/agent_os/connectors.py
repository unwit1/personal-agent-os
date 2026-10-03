"""Provider-neutral, secret-safe connector registry contract (v1)."""

from __future__ import annotations

import ctypes
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tomllib
from collections import Counter, defaultdict
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from .paths import ROOT
from .privacy import privacy_findings
from .storage import write_json


REGISTRY_SCHEMA = "personal-agent/connector-registry/v1"
REGISTRY_VERSION = 1
REGISTRY_PATH = ROOT / "connectors" / "registry.json"
_CONNECTOR_EVENTS_PATH = ROOT / ".agent-local" / "connector-events.jsonl"
EVENT_SCHEMA = "personal-agent/connector-event/v1"
_IDENTIFIER = re.compile(r"^[a-z][a-z0-9._-]{0,63}$")
_CANDIDATE_ID = re.compile(r"^[a-f0-9]{20}$")
_SECRET_REF = re.compile(
    r"^(?:keyring|windows-credential|macos-keychain|secret-service|env):"
    r"[A-Za-z0-9][A-Za-z0-9._/-]{0,127}$"
)
_SERVER_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}")
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


def _surface_server_names(surface: dict) -> set[str] | None:
    """Collect MCP server names from a surface's registration files.

    Returns the set of server names (casefolded) found in parsed files,
    None if no files exist or none could be parsed successfully.
    """
    from .machine import resolve_user_path

    server_names: set[str] = set()
    found_any_file = False
    parsed_any = False

    for location in surface.get("invocation", {}).get("registrations", []):
        path = resolve_user_path(location)
        if not path.is_file():
            continue

        found_any_file = True
        try:
            raw = path.read_text(encoding="utf-8-sig")
            if path.suffix.casefold() == ".toml":
                document = tomllib.loads(raw)
            else:
                document = json.loads(raw)
        except (OSError, UnicodeError, json.JSONDecodeError, tomllib.TOMLDecodeError):
            continue

        parsed_any = True
        for name, _ in _walk_mcp_servers(document):
            server_names.add(str(name).casefold())

    return server_names if found_any_file and parsed_any else None


def connector_reconcile_plan(surface_id: str | None = None) -> dict[str, Any]:
    """Analyze desired connector registrations and plan provisioning steps.

    Strictly read-only: loads registry and surfaces, compares desired state to
    known surfaces and capabilities, and returns action recommendations.
    Never writes, reads credentials, or contacts providers.
    """
    from .surfaces import surfaces, _connector_capabilities

    registry = load_connector_registry()
    known = {s["id"]: s for s in surfaces()}

    items = []
    surface_names_cache: dict[str, set[str] | None] = {}

    for connector in registry["connectors"]:
        connector_id = connector["id"]
        for registration in connector["registrations"]:
            reg_surface_id = registration["surface_id"]
            if surface_id and reg_surface_id != surface_id:
                continue

            state = registration["state"]
            action: str
            reason: str

            if reg_surface_id not in known:
                action = "unknown_surface"
                reason = "surface is not declared in the surface registry"
            elif state in {"registered", "disabled", "unsupported"}:
                action = "none"
                reason = f"registration is already {state}"
            elif state == "error":
                action = "investigate"
                reason = "registration reported an error; an adapter must re-verify it"
            else:
                cap = _connector_capabilities(known[reg_surface_id]).get("mutate_local_config", {})
                available = cap.get("available")
                reason = cap.get("reason") or "connector capability has not been declared for this surface"
                if available is True:
                    action = "provision_local_config"
                elif available is False:
                    action = "manual_host_setup"
                else:
                    action = "undetermined"

            native_entry_status = "unknown_surface"
            server_name = registration.get("server_name")
            if server_name is None:
                native_entry_status = "not_requested"
            elif reg_surface_id in known:
                inspect_cap = _connector_capabilities(known[reg_surface_id]).get("inspect_local_config", {})
                if inspect_cap.get("available") is not True:
                    native_entry_status = "not_inspectable"
                else:
                    if reg_surface_id not in surface_names_cache:
                        surface_names_cache[reg_surface_id] = _surface_server_names(known[reg_surface_id])
                    cached_names = surface_names_cache[reg_surface_id]
                    if cached_names is None:
                        native_entry_status = "unreadable"
                    elif server_name.casefold() in cached_names:
                        native_entry_status = "present"
                    else:
                        native_entry_status = "absent"

            items.append({
                "connector_id": connector_id,
                "surface_id": reg_surface_id,
                "state": state,
                "action": action,
                "reason": reason,
                "credential_reference_configured": connector["secret_ref"] is not None,
                "native_server_name": registration.get("server_name"),
                "native_entry_requested": registration.get("server_name") is not None,
                "native_entry_status": native_entry_status,
            })

    items.sort(key=lambda item: (item["connector_id"], item["surface_id"]))

    action_counts: dict[str, int] = {}
    native_entry_status_counts: dict[str, int] = {}
    for item in items:
        action = item["action"]
        action_counts[action] = action_counts.get(action, 0) + 1
        status = item["native_entry_status"]
        native_entry_status_counts[status] = native_entry_status_counts.get(status, 0) + 1

    return {
        "schema": "personal-agent/connector-reconcile-plan/v1",
        "applied": False,
        "surface_filter": surface_id,
        "count": len(items),
        "action_counts": action_counts,
        "native_entry_status_counts": native_entry_status_counts,
        "items": items,
    }


def _windows_credential_present(name: str) -> bool | None:
    """Check Windows Credential Manager for a generic credential without reading its secret."""
    if sys.platform != "win32":
        return None
    try:
        from ctypes import wintypes

        advapi32 = ctypes.WinDLL("advapi32", use_last_error=True)
        cred_read = advapi32.CredReadW
        cred_read.argtypes = [
            wintypes.LPCWSTR,
            wintypes.DWORD,
            wintypes.DWORD,
            ctypes.POINTER(ctypes.c_void_p),
        ]
        cred_read.restype = wintypes.BOOL
        cred_free = advapi32.CredFree
        cred_free.argtypes = [ctypes.c_void_p]
        cred_free.restype = None

        ptr = ctypes.c_void_p()
        if cred_read(name, 1, 0, ctypes.byref(ptr)):
            cred_free(ptr)
            return True
        if ctypes.get_last_error() == 1168:
            return False
        return None
    except (OSError, AttributeError):
        return None


def _macos_keychain_present(name: str) -> bool | None:
    """Check the macOS keychain for a generic password item without requesting its value."""
    if sys.platform != "darwin" or not shutil.which("security"):
        return None
    try:
        result = subprocess.run(
            ["security", "find-generic-password", "-s", name],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode == 0:
        return True
    if result.returncode == 44:
        return False
    return None


def connector_credential_status(surface_id: str | None = None) -> dict[str, Any]:
    """Report credential presence status for registered connectors without exposing secrets.

    Read-only credential presence checks only. Never transfers, reads, or stores credentials.
    """
    registry = load_connector_registry()
    items = []

    for connector in registry["connectors"]:
        connector_id = connector["id"]
        registrations = connector["registrations"]

        if surface_id and not any(item["surface_id"] == surface_id for item in registrations):
            continue

        secret_ref = connector["secret_ref"]

        if secret_ref is None:
            item = {
                "connector_id": connector_id,
                "backend": None,
                "status": "not_configured",
                "reason": "no credential reference is declared",
            }
        else:
            backend, name = secret_ref.split(":", 1)

            if backend == "env":
                value = os.environ.get(name, "").strip()
                if value:
                    status = "present"
                    reason = "environment variable is set"
                else:
                    status = "missing"
                    reason = "environment variable is not set or empty"
            elif backend in ("windows-credential", "macos-keychain"):
                if backend == "windows-credential":
                    present = _windows_credential_present(name)
                else:
                    present = _macos_keychain_present(name)
                if present is True:
                    status = "present"
                    reason = "credential store entry exists"
                elif present is False:
                    status = "missing"
                    reason = "credential store entry was not found"
                else:
                    status = "unchecked"
                    reason = f"{backend} presence check is unavailable on this host"
            else:
                status = "unchecked"
                reason = f"presence checks for the {backend} backend are not implemented yet"

            item = {
                "connector_id": connector_id,
                "backend": backend,
                "status": status,
                "reason": reason,
            }

        items.append(item)

    items.sort(key=lambda item: item["connector_id"])

    status_counts: dict[str, int] = {}
    for item in items:
        status = item["status"]
        status_counts[status] = status_counts.get(status, 0) + 1

    return {
        "schema": "personal-agent/connector-credential-status/v1",
        "values_returned": False,
        "surface_filter": surface_id,
        "count": len(items),
        "status_counts": status_counts,
        "items": items,
    }


def connector_conflicts(surface_id: str | None = None) -> dict[str, Any]:
    """Detect conflicts in connector registry: duplicate providers, server name collisions, shared credentials.

    Read-only analysis only. Never writes, reads credentials, or contacts providers.
    """
    registry = load_connector_registry()
    conflicts: list[dict[str, Any]] = []

    # Build indexes for conflict detection using defaultdict
    provider_surface_map: dict[tuple[str, str], list[tuple[str, str]]] = defaultdict(list)
    server_name_map: dict[tuple[str, str], list[str]] = defaultdict(list)
    secret_ref_map: dict[str, list[str]] = defaultdict(list)

    for connector in registry["connectors"]:
        connector_id = connector["id"]
        provider_id = connector["provider"]["id"]
        secret_ref = connector["secret_ref"]

        # Only consider connectors with registrations matching the filter
        relevant_registrations = connector["registrations"]
        if surface_id:
            relevant_registrations = [r for r in relevant_registrations if r["surface_id"] == surface_id]

        # Track shared credential references (only for connectors with relevant registrations when surface_id is set)
        if secret_ref is not None and (not surface_id or relevant_registrations):
            secret_ref_map[secret_ref].append(connector_id)

        # Process registrations for provider/surface and server_name conflicts
        for registration in relevant_registrations:
            reg_surface_id = registration["surface_id"]
            state = registration["state"]

            # (a) duplicate_provider_surface: only track desired/registered/error states
            if state in {"desired", "registered", "error"}:
                provider_surface_map[(provider_id, reg_surface_id)].append((connector_id, state))

            # (b) native_server_name_collision: track all server_name registrations
            server_name = registration.get("server_name")
            if server_name is not None:
                server_name_map[(reg_surface_id, server_name)].append(connector_id)

    # Detect (a) duplicate_provider_surface conflicts
    for (provider_id, reg_surface_id), items in provider_surface_map.items():
        connector_ids = sorted(set(cid for cid, _ in items))
        if len(connector_ids) > 1:
            conflicts.append({
                "kind": "duplicate_provider_surface",
                "provider_id": provider_id,
                "surface_id": reg_surface_id,
                "connector_ids": connector_ids,
            })

    # Detect (b) native_server_name_collision conflicts
    for (reg_surface_id, server_name), connector_ids in server_name_map.items():
        unique_ids = sorted(set(connector_ids))
        if len(unique_ids) > 1:
            conflicts.append({
                "kind": "native_server_name_collision",
                "surface_id": reg_surface_id,
                "server_name": server_name,
                "connector_ids": unique_ids,
            })

    # Detect (c) shared_credential_reference conflicts
    for secret_ref, connector_ids in secret_ref_map.items():
        if len(connector_ids) > 1:
            backend = secret_ref.split(":", 1)[0]
            unique_ids = sorted(set(connector_ids))
            conflicts.append({
                "kind": "shared_credential_reference",
                "backend": backend,
                "connector_ids": unique_ids,
            })

    # Sort conflicts by (kind, surface_id or '', connector_ids)
    conflicts.sort(key=lambda c: (c["kind"], c.get("surface_id", ""), tuple(c["connector_ids"])))

    # Build kind_counts
    kind_counts = dict(Counter(c["kind"] for c in conflicts))

    return {
        "schema": "personal-agent/connector-conflicts/v1",
        "surface_filter": surface_id,
        "read_only": True,
        "count": len(conflicts),
        "kind_counts": kind_counts,
        "conflicts": conflicts,
    }


_EVENT_FIELDS = ("schema", "event", "connector_id", "provider_id", "capabilities", "surfaces", "at")


def connector_events(limit: int = 50, connector_id: str | None = None) -> dict[str, Any]:
    """Read the connector change event log with optional filtering and limit.

    Returns empty results if the events file is missing.
    Skips malformed or non-matching records and counts them.
    """
    if type(limit) is bool or not isinstance(limit, int):
        raise ValueError("limit must be an integer")
    if limit < 1 or limit > 500:
        raise ValueError("limit must be between 1 and 500")

    if connector_id is not None:
        _identifier(connector_id, "connector id")

    if not _CONNECTOR_EVENTS_PATH.is_file():
        return {
            "schema": "personal-agent/connector-events/v1",
            "connector_filter": connector_id,
            "limit": limit,
            "count": 0,
            "malformed": 0,
            "items": [],
        }

    items = []
    malformed = 0

    try:
        lines = _CONNECTOR_EVENTS_PATH.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError):
        lines = []

    for line in lines:
        if not line.strip():
            malformed += 1
            continue

        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            malformed += 1
            continue

        if not isinstance(record, dict) or record.get("schema") != EVENT_SCHEMA:
            malformed += 1
            continue

        if connector_id is not None and record.get("connector_id") != connector_id:
            continue

        items.append({key: record[key] for key in _EVENT_FIELDS if key in record})

    # Keep only the last limit items in chronological order
    items = items[-limit:]

    return {
        "schema": "personal-agent/connector-events/v1",
        "connector_filter": connector_id,
        "limit": limit,
        "count": len(items),
        "malformed": malformed,
        "items": items,
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
        event_recorded = _append_connector_event("connector.updated" if existing_index is not None else "connector.added", connector)
    return {
        "written": True,
        "replaced": existing_index is not None,
        "connector_id": connector_id,
        "count": len(registry["connectors"]),
        "event_recorded": event_recorded,
    }


def unregister_connector(
    connector_id: str,
    *,
    confirm_write: bool = False,
) -> dict[str, Any]:
    """Preview or remove a connector's registry metadata without revoking credentials."""
    _identifier(connector_id, "connector id")
    if type(confirm_write) is not bool:
        raise ValueError("confirm_write must be a boolean")

    if not confirm_write:
        registry = load_connector_registry()
        connector = next(
            (item for item in registry["connectors"] if item["id"] == connector_id),
            None,
        )
        # The preview names what would be removed without echoing the record:
        # it carries the secret_ref, which connector outputs never return.
        return {
            "written": False,
            "confirmation_required": True,
            "connector_id": connector_id,
            "found": connector is not None,
            "provider_id": connector["provider"]["id"] if connector else None,
        }

    with _registry_write_lock():
        registry = load_connector_registry()
        existing_index = next(
            (index for index, item in enumerate(registry["connectors"]) if item["id"] == connector_id),
            None,
        )
        if existing_index is None:
            return {"written": False, "not_found": True, "connector_id": connector_id}

        connector = registry["connectors"][existing_index]
        registry["connectors"].pop(existing_index)
        write_json(REGISTRY_PATH, registry)
        event_recorded = _append_connector_event("connector.removed", connector)

    return {
        "written": True,
        "connector_id": connector_id,
        "count": len(registry["connectors"]),
        "event_recorded": event_recorded,
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


def _append_connector_event(event: str, connector: dict) -> bool:
    """Append a connector change event to the append-only log.

    Returns True on success, False on OSError (includes mkdir failures).
    Never includes secret_ref, scopes, server_name, or privacy_domain.
    """
    try:
        record = {
            "schema": EVENT_SCHEMA,
            "event": event,
            "connector_id": connector["id"],
            "provider_id": connector["provider"]["id"],
            "capabilities": sorted(connector["capabilities"]),
            "surfaces": sorted(r["surface_id"] for r in connector["registrations"]),
            "at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        }
        _CONNECTOR_EVENTS_PATH.parent.mkdir(parents=True, exist_ok=True)
        with _CONNECTOR_EVENTS_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, sort_keys=True) + "\n")
        return True
    except OSError:
        return False


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


def import_connector_candidate(
    candidate_id: str,
    connector: Any,
    *,
    reviewed: bool = False,
    confirm_write: bool = False,
    replace_existing: bool = False,
) -> dict[str, Any]:
    """Attach explicitly reviewed metadata to a discovered client registration.

    Candidate discovery exposes only a server label and executable basename;
    it cannot establish provider identity, allowed scopes, or credential
    portability. Those details must be supplied and reviewed by the caller.
    This operation never reads a credential store or copies client config.
    """
    if not isinstance(candidate_id, str) or not _CANDIDATE_ID.fullmatch(candidate_id):
        raise ValueError("candidate_id must be a 20-character lowercase hexadecimal ID")
    if type(reviewed) is not bool:
        raise ValueError("reviewed must be a boolean")
    if type(confirm_write) is not bool or type(replace_existing) is not bool:
        raise ValueError("confirm_write and replace_existing must be booleans")
    _validate_connector(connector)

    result = connector_import_candidates()
    candidate = next(
        (item for item in result["candidates"] if item["candidate_id"] == candidate_id),
        None,
    )
    if candidate is None:
        raise KeyError(f"unknown connector import candidate: {candidate_id}")

    candidate_surfaces = sorted(candidate["surfaces"])
    connector_surfaces = {item["surface_id"] for item in connector["registrations"]}
    if not connector_surfaces.intersection(candidate_surfaces):
        raise ValueError("connector must declare a desired registration on at least one candidate surface")

    if not reviewed:
        return {
            "written": False,
            "review_required": True,
            "candidate": candidate,
            "candidate_surfaces": candidate_surfaces,
            "credential_values_transferred": False,
        }

    outcome = register_connector(
        connector,
        confirm_write=confirm_write,
        replace_existing=replace_existing,
    )
    return {
        **outcome,
        "candidate_id": candidate_id,
        "candidate_surfaces": candidate_surfaces,
        "credential_values_transferred": False,
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
        if not isinstance(registration, dict) or set(registration) not in ({"surface_id", "state"}, {"surface_id", "state", "server_name"}):
            raise ValueError("connector registration must contain only surface_id, state, and optional server_name")
        _identifier(registration["surface_id"], "surface id")
        if registration["surface_id"] in seen_surfaces:
            raise ValueError("connector registrations contain duplicate surface IDs")
        seen_surfaces.add(registration["surface_id"])
        if registration["state"] not in _REGISTRATION_STATES:
            raise ValueError("connector registration state is invalid")
        if "server_name" in registration:
            server_name = registration["server_name"]
            if not isinstance(server_name, str) or not _SERVER_NAME.fullmatch(server_name):
                raise ValueError("connector registration server_name is invalid")

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
