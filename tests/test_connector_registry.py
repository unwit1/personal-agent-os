"""Contract tests for Git-backed connector registry metadata."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

# The repository may be nested in a larger checkout whose source tree appears
# earlier on PYTHONPATH. Always exercise the package in this worktree.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.connectors import (
    CONNECTOR_REGISTRY_SCHEMA,
    ConnectorRegistryError,
    load_connector_registry,
    validate_connector_registry,
)


def valid_registry() -> dict:
    return {
        "schema": CONNECTOR_REGISTRY_SCHEMA,
        "version": 1,
        "connectors": [
            {
                "id": "google-workspace",
                "provider": {"id": "google", "name": "Google Workspace"},
                "capabilities": ["drive.search", "drive.read"],
                "scopes": ["drive.readonly"],
                "health": "healthy",
                "privacy_domain": "work",
                "registration_state": "registered",
                "secret_ref": {"store": "windows-credential-manager", "key": "agent-os/google-workspace"},
            }
        ],
    }


class ConnectorRegistryTests(unittest.TestCase):
    def test_valid_metadata_is_accepted(self) -> None:
        data = valid_registry()
        self.assertIs(validate_connector_registry(data), data)

    def test_loader_reads_and_validates_registry_json(self) -> None:
        data = valid_registry()
        with patch.object(Path, "read_text", return_value=json.dumps(data)):
            self.assertEqual(load_connector_registry("registry.json"), data)

    def test_credential_field_is_rejected(self) -> None:
        data = valid_registry()
        data["connectors"][0]["access_token"] = "must-not-be-stored"
        with self.assertRaisesRegex(ConnectorRegistryError, "secret-bearing fields"):
            validate_connector_registry(data)

    def test_recognizable_token_value_is_rejected(self) -> None:
        data = valid_registry()
        data["connectors"][0]["secret_ref"]["key"] = "Bearer abc123"
        with self.assertRaisesRegex(ConnectorRegistryError, "credential values"):
            validate_connector_registry(data)


if __name__ == "__main__":
    unittest.main()
