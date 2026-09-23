from __future__ import annotations

import json
import sys
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.connectors import REGISTRY_SCHEMA, connector_status, load_connector_registry, validate_connector_registry
from agent_os.mcp_server import _handle_mcp, methods
from agent_os.paths import ROOT


def valid_connector() -> dict:
    return {
        "id": "google-drive-work",
        "provider": {"id": "google-drive", "name": "Google Drive"},
        "capabilities": ["files.search", "files.read"],
        "scopes": ["drive.readonly"],
        "health": {"status": "unknown", "checked_at": None},
        "privacy_domain": "work",
        "registrations": [{"surface_id": "agent-os-mcp", "state": "desired"}],
        "secret_ref": "keyring:agent-os/google-drive-work",
    }


def valid_registry() -> dict:
    return {"schema": REGISTRY_SCHEMA, "version": 1, "connectors": [valid_connector()]}


class ConnectorRegistryTests(unittest.TestCase):
    def test_loads_empty_canonical_registry(self) -> None:
        registry = load_connector_registry(ROOT / "connectors" / "registry.json")
        self.assertEqual(registry, {"schema": REGISTRY_SCHEMA, "version": 1, "connectors": []})

    def test_accepts_provider_scopes_health_registrations_and_secret_reference(self) -> None:
        validate_connector_registry(valid_registry())

    def test_rejects_unknown_fields_that_could_carry_credentials(self) -> None:
        registry = valid_registry()
        registry["connectors"][0]["access_token"] = "should-never-be-stored"
        with self.assertRaisesRegex(ValueError, "unsupported fields"):
            validate_connector_registry(registry)

    def test_rejects_credential_values_and_file_paths_as_secret_references(self) -> None:
        for reference in (
            "keyring:api_key=abcdefghijklmnop",
            "C:\\Users\\user\\credentials.json",
            "file:/home/user/.config/token",
        ):
            with self.subTest(reference=reference):
                registry = valid_registry()
                registry["connectors"][0]["secret_ref"] = reference
                with self.assertRaisesRegex(ValueError, "secret_ref"):
                    validate_connector_registry(registry)

    def test_rejects_duplicate_connector_and_surface_ids(self) -> None:
        registry = valid_registry()
        registry["connectors"].append(deepcopy(registry["connectors"][0]))
        with self.assertRaisesRegex(ValueError, "duplicate connector IDs"):
            validate_connector_registry(registry)

        registry = valid_registry()
        registration = deepcopy(registry["connectors"][0]["registrations"][0])
        registry["connectors"][0]["registrations"].append(registration)
        with self.assertRaisesRegex(ValueError, "duplicate surface IDs"):
            validate_connector_registry(registry)

    def test_rejects_invalid_states_and_timezone_free_health_timestamps(self) -> None:
        registry = valid_registry()
        registry["connectors"][0]["health"] = {"status": "connected", "checked_at": None}
        with self.assertRaisesRegex(ValueError, "health status"):
            validate_connector_registry(registry)

        registry = valid_registry()
        registry["connectors"][0]["health"]["checked_at"] = "2026-09-23T12:00:00"
        with self.assertRaisesRegex(ValueError, "include a timezone"):
            validate_connector_registry(registry)

    def test_load_wraps_invalid_json_without_echoing_file_content(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "registry.json"
            path.write_text('{"api_key":"private-placeholder"', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "invalid JSON") as caught:
                load_connector_registry(path)
            self.assertNotIn("private-placeholder", str(caught.exception))

    def test_version_and_top_level_shape_are_enforced(self) -> None:
        registry = valid_registry()
        registry["version"] = 2
        with self.assertRaisesRegex(ValueError, "unsupported"):
            validate_connector_registry(registry)
        registry = valid_registry()
        registry["comment"] = "unexpected"
        with self.assertRaisesRegex(ValueError, "only schema"):
            validate_connector_registry(registry)

    def test_status_redacts_secret_store_reference_and_filters_by_surface(self) -> None:
        with patch("agent_os.connectors.load_connector_registry", return_value=valid_registry()):
            status = connector_status()
            filtered = connector_status("agent-os-mcp")
            empty = connector_status("claude-code")
        self.assertEqual(status["count"], 1)
        self.assertEqual(filtered["count"], 1)
        self.assertEqual(empty["connectors"], [])
        connector = status["connectors"][0]
        self.assertTrue(connector["credential_reference_configured"])
        self.assertNotIn("secret_ref", connector)
        self.assertNotIn("keyring:agent-os/google-drive-work", json.dumps(status))

    def test_mcp_connector_list_is_discoverable_and_redacted(self) -> None:
        available = methods()
        listing = _handle_mcp({"jsonrpc": "2.0", "id": 1, "method": "tools/list"}, available)
        names = {item["name"] for item in listing["result"]["tools"]}
        self.assertIn("connector.list", names)

        with patch("agent_os.connectors.load_connector_registry", return_value=valid_registry()):
            response = _handle_mcp(
                {
                    "jsonrpc": "2.0", "id": 2, "method": "tools/call",
                    "params": {"name": "connector.list", "arguments": {}},
                },
                available,
            )
        payload = json.loads(response["result"]["content"][0]["text"])
        self.assertEqual(payload["count"], 1)
        self.assertNotIn("secret_ref", payload["connectors"][0])


if __name__ == "__main__":
    unittest.main()
