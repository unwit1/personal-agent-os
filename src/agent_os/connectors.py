"""Provider-neutral, secret-safe connector registry contract (v1)."""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from .paths import ROOT
from .privacy import privacy_findings


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
