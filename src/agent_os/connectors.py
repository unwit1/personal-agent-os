"""Provider-neutral, Git-safe connector registry metadata."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .paths import ROOT

CONNECTOR_REGISTRY_SCHEMA = "personal-agent/connector-registry/v1"
CONNECTOR_REGISTRY_PATH = ROOT / "connectors" / "registry.json"
_SECRET_KEY = re.compile(r"(?:^|[_-])(credential|password|passwd|secret|token|api[_-]?key|private[_-]?key)(?:$|[_-])", re.I)
_BEARER = re.compile(r"\bBearer\s+\S+", re.I)
_SECRET_VALUE = re.compile(
    r"(?:\bAKIA[0-9A-Z]{16}\b|\bgh[pousr]_[A-Za-z0-9]{20,}\b|"
    r"\bgithub_pat_[A-Za-z0-9_]{20,}\b|\bxox[baprs]-[A-Za-z0-9-]{10,}\b|"
    r"\bsk-[A-Za-z0-9_-]{20,}\b|\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b)"
)


class ConnectorRegistryError(ValueError):
    """Invalid or secret-bearing connector registry metadata."""


def _reject_secrets(value: Any, path: str = "registry") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            key_text = str(key)
            # secret_ref is the one permitted secret-related field; it stores
            # only a pointer into an approved local secret store.
            if key_text != "secret_ref" and _SECRET_KEY.search(key_text):
                raise ConnectorRegistryError(f"{path}.{key_text}: secret-bearing fields are forbidden; use secret_ref")
            _reject_secrets(child, f"{path}.{key_text}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _reject_secrets(child, f"{path}[{index}]")
    elif isinstance(value, str) and (_BEARER.search(value) or _SECRET_VALUE.search(value)):
        raise ConnectorRegistryError(f"{path}: credential values are forbidden; use secret_ref")


def _validate_connector(item: Any, index: int) -> None:
    label = f"connectors[{index}]"
    required = {"id", "provider", "capabilities", "scopes", "health", "privacy_domain", "registration_state", "secret_ref"}
    if not isinstance(item, dict) or set(item) != required:
        raise ConnectorRegistryError(f"{label}: expected exactly {', '.join(sorted(required))}")
    if not isinstance(item["id"], str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", item["id"]):
        raise ConnectorRegistryError(f"{label}.id: invalid connector id")
    provider = item["provider"]
    if not isinstance(provider, dict) or set(provider) != {"id", "name"} or not all(isinstance(provider[k], str) and provider[k].strip() for k in ("id", "name")):
        raise ConnectorRegistryError(f"{label}.provider: expected non-empty id and name")
    for field in ("capabilities", "scopes"):
        values = item[field]
        if not isinstance(values, list) or any(not isinstance(v, str) or not v.strip() for v in values) or len(values) != len(set(values)):
            raise ConnectorRegistryError(f"{label}.{field}: expected unique non-empty strings")
    if not isinstance(item["health"], str) or item["health"] not in {"unknown", "healthy", "degraded", "unhealthy"}:
        raise ConnectorRegistryError(f"{label}.health: unsupported health state")
    if not isinstance(item["privacy_domain"], str) or not item["privacy_domain"].strip():
        raise ConnectorRegistryError(f"{label}.privacy_domain: expected a non-empty string")
    if item["registration_state"] not in {"desired", "registered", "disabled", "revoked", "error"}:
        raise ConnectorRegistryError(f"{label}.registration_state: unsupported state")
    ref = item["secret_ref"]
    if not isinstance(ref, dict) or set(ref) != {"store", "key"} or not all(isinstance(ref[k], str) and ref[k].strip() for k in ("store", "key")):
        raise ConnectorRegistryError(f"{label}.secret_ref: expected non-empty store and key references")


def validate_connector_registry(data: Any) -> dict[str, Any]:
    """Validate registry shape and ensure metadata contains no credentials."""
    _reject_secrets(data)
    if not isinstance(data, dict) or set(data) != {"schema", "version", "connectors"}:
        raise ConnectorRegistryError("registry: expected schema, version, and connectors")
    if data["schema"] != CONNECTOR_REGISTRY_SCHEMA or type(data["version"]) is not int or data["version"] != 1:
        raise ConnectorRegistryError("registry: unsupported connector registry schema/version")
    if not isinstance(data["connectors"], list):
        raise ConnectorRegistryError("registry.connectors: expected an array")
    ids: set[str] = set()
    for index, item in enumerate(data["connectors"]):
        _validate_connector(item, index)
        if item["id"] in ids:
            raise ConnectorRegistryError(f"connectors[{index}].id: duplicate connector id")
        ids.add(item["id"])
    return data


def load_connector_registry(path: str | Path = CONNECTOR_REGISTRY_PATH) -> dict[str, Any]:
    """Load and validate a Git-backed connector registry JSON file."""
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ConnectorRegistryError(f"cannot load connector registry: {exc}") from exc
    return validate_connector_registry(data)
