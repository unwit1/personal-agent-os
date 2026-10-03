from __future__ import annotations

import json
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.connectors import connector_credential_status, REGISTRY_SCHEMA


def valid_connector(
    connector_id: str = "google-drive-work",
    surface_id: str = "agent-os-mcp",
    secret_ref: str | None = "keyring:agent-os/google-drive-work",
) -> dict:
    return {
        "id": connector_id,
        "provider": {"id": "google-drive", "name": "Google Drive"},
        "capabilities": ["files.search", "files.read"],
        "scopes": ["drive.readonly"],
        "health": {"status": "unknown", "checked_at": None},
        "privacy_domain": "work",
        "registrations": [{"surface_id": surface_id, "state": "desired"}],
        "secret_ref": secret_ref,
    }


def valid_registry(connectors: list[dict] | None = None) -> dict:
    if connectors is None:
        connectors = [valid_connector()]
    return {"schema": REGISTRY_SCHEMA, "version": 1, "connectors": connectors}


class ConnectorCredentialStatusTests(unittest.TestCase):
    def test_returns_correct_schema_and_structure(self) -> None:
        with patch("agent_os.connectors.load_connector_registry", return_value=valid_registry()):
            result = connector_credential_status()

        self.assertEqual(result["schema"], "personal-agent/connector-credential-status/v1")
        self.assertEqual(result["values_returned"], False)
        self.assertIsNone(result["surface_filter"])
        self.assertIn("count", result)
        self.assertIn("status_counts", result)
        self.assertIn("items", result)

    def test_empty_registry_returns_empty_items(self) -> None:
        with patch("agent_os.connectors.load_connector_registry", return_value=valid_registry([])):
            result = connector_credential_status()

        self.assertEqual(result["count"], 0)
        self.assertEqual(result["items"], [])
        self.assertEqual(result["status_counts"], {})

    def test_filters_by_surface_id(self) -> None:
        connectors = [
            valid_connector("conn-a", "agent-os-mcp", "env:TEST_VAR"),
            valid_connector("conn-b", "claude-code", "env:TEST_VAR"),
        ]
        with patch("agent_os.connectors.load_connector_registry", return_value=valid_registry(connectors)):
            result = connector_credential_status("agent-os-mcp")

        self.assertEqual(result["surface_filter"], "agent-os-mcp")
        self.assertEqual(result["count"], 1)
        self.assertEqual(result["items"][0]["connector_id"], "conn-a")

    def test_null_secret_ref_returns_not_configured(self) -> None:
        connector = valid_connector(secret_ref=None)
        with patch("agent_os.connectors.load_connector_registry", return_value=valid_registry([connector])):
            result = connector_credential_status()

        self.assertEqual(result["count"], 1)
        item = result["items"][0]
        self.assertEqual(item["connector_id"], "google-drive-work")
        self.assertIsNone(item["backend"])
        self.assertEqual(item["status"], "not_configured")
        self.assertEqual(item["reason"], "no credential reference is declared")

    def test_env_ref_present_returns_present(self) -> None:
        connector = valid_connector(secret_ref="env:AGENT_OS_TEST_TOKEN")
        with patch("agent_os.connectors.load_connector_registry", return_value=valid_registry([connector])):
            with patch.dict(os.environ, {"AGENT_OS_TEST_TOKEN": "s3cr3t-value"}):
                result = connector_credential_status()

        self.assertEqual(result["count"], 1)
        item = result["items"][0]
        self.assertEqual(item["connector_id"], "google-drive-work")
        self.assertEqual(item["backend"], "env")
        self.assertEqual(item["status"], "present")
        self.assertEqual(item["reason"], "environment variable is set")

    def test_env_ref_absent_returns_missing(self) -> None:
        connector = valid_connector(secret_ref="env:MISSING_VAR")
        with patch("agent_os.connectors.load_connector_registry", return_value=valid_registry([connector])):
            result = connector_credential_status()

        self.assertEqual(result["count"], 1)
        item = result["items"][0]
        self.assertEqual(item["connector_id"], "google-drive-work")
        self.assertEqual(item["backend"], "env")
        self.assertEqual(item["status"], "missing")
        self.assertEqual(item["reason"], "environment variable is not set or empty")

    def test_env_ref_whitespace_only_returns_missing(self) -> None:
        connector = valid_connector(secret_ref="env:WHITESPACE_VAR")
        with patch("agent_os.connectors.load_connector_registry", return_value=valid_registry([connector])):
            with patch.dict(os.environ, {"WHITESPACE_VAR": "   "}):
                result = connector_credential_status()

        self.assertEqual(result["count"], 1)
        item = result["items"][0]
        self.assertEqual(item["status"], "missing")
        self.assertEqual(item["reason"], "environment variable is not set or empty")

    def test_secret_value_not_in_output(self) -> None:
        connector = valid_connector(secret_ref="env:AGENT_OS_TEST_TOKEN")
        with patch("agent_os.connectors.load_connector_registry", return_value=valid_registry([connector])):
            with patch.dict(os.environ, {"AGENT_OS_TEST_TOKEN": "s3cr3t-value"}):
                result = connector_credential_status()

        json_output = json.dumps(result)
        self.assertNotIn("s3cr3t-value", json_output)

    def test_variable_name_not_in_output(self) -> None:
        connector = valid_connector(secret_ref="env:AGENT_OS_TEST_TOKEN")
        with patch("agent_os.connectors.load_connector_registry", return_value=valid_registry([connector])):
            with patch.dict(os.environ, {"AGENT_OS_TEST_TOKEN": "s3cr3t-value"}):
                result = connector_credential_status()

        json_output = json.dumps(result)
        self.assertNotIn("AGENT_OS_TEST_TOKEN", json_output)

    def test_secret_ref_string_not_in_output(self) -> None:
        connector = valid_connector(secret_ref="env:TEST_TOKEN")
        with patch("agent_os.connectors.load_connector_registry", return_value=valid_registry([connector])):
            with patch.dict(os.environ, {"TEST_TOKEN": "secret"}):
                result = connector_credential_status()

        json_output = json.dumps(result)
        self.assertNotIn("env:TEST_TOKEN", json_output)

    def test_keyring_backend_returns_unchecked(self) -> None:
        connector = valid_connector(secret_ref="keyring:agent-os/google-drive-work")
        with patch("agent_os.connectors.load_connector_registry", return_value=valid_registry([connector])):
            result = connector_credential_status()

        self.assertEqual(result["count"], 1)
        item = result["items"][0]
        self.assertEqual(item["backend"], "keyring")
        self.assertEqual(item["status"], "unchecked")
        self.assertIn("presence checks for the keyring backend are not implemented yet", item["reason"])

    def _status_with(self, secret_ref: str, helper: str, value) -> dict:
        connector = valid_connector(secret_ref=secret_ref)
        with patch("agent_os.connectors.load_connector_registry", return_value=valid_registry([connector])):
            with patch(f"agent_os.connectors.{helper}", return_value=value):
                return connector_credential_status()["items"][0]

    def test_windows_credential_backend_states(self) -> None:
        ref = "windows-credential:agent-os/drive"
        for value, status, reason in [
            (True, "present", "credential store entry exists"),
            (False, "missing", "credential store entry was not found"),
            (None, "unchecked", "windows-credential presence check is unavailable on this host"),
        ]:
            item = self._status_with(ref, "_windows_credential_present", value)
            self.assertEqual(item["backend"], "windows-credential")
            self.assertEqual(item["status"], status)
            self.assertEqual(item["reason"], reason)
            self.assertEqual(set(item), {"connector_id", "backend", "status", "reason"})

    def test_macos_keychain_backend_states(self) -> None:
        ref = "macos-keychain:agent-os/drive"
        for value, status, reason in [
            (True, "present", "credential store entry exists"),
            (False, "missing", "credential store entry was not found"),
            (None, "unchecked", "macos-keychain presence check is unavailable on this host"),
        ]:
            item = self._status_with(ref, "_macos_keychain_present", value)
            self.assertEqual(item["backend"], "macos-keychain")
            self.assertEqual(item["status"], status)
            self.assertEqual(item["reason"], reason)

    def test_windows_helper_returns_none_off_windows(self) -> None:
        from agent_os.connectors import _windows_credential_present

        with patch("agent_os.connectors.sys.platform", "linux"):
            self.assertIsNone(_windows_credential_present("x"))

    def test_macos_helper_return_codes(self) -> None:
        from types import SimpleNamespace

        from agent_os.connectors import _macos_keychain_present

        with patch("agent_os.connectors.sys.platform", "linux"):
            self.assertIsNone(_macos_keychain_present("x"))
        with patch("agent_os.connectors.sys.platform", "darwin"),                 patch("agent_os.connectors.shutil.which", return_value="/usr/bin/security"):
            for code, expected in [(0, True), (44, False), (1, None)]:
                with patch("agent_os.connectors.subprocess.run", return_value=SimpleNamespace(returncode=code)) as run:
                    self.assertIs(_macos_keychain_present("svc"), expected)
                    cmd = run.call_args.args[0]
                    self.assertNotIn("-w", cmd)
                    self.assertNotIn("-g", cmd)
            with patch("agent_os.connectors.subprocess.run", side_effect=OSError):
                self.assertIsNone(_macos_keychain_present("svc"))

    def test_secret_service_backend_returns_unchecked(self) -> None:
        connector = valid_connector(secret_ref="secret-service:agent-os/drive")
        with patch("agent_os.connectors.load_connector_registry", return_value=valid_registry([connector])):
            result = connector_credential_status()

        item = result["items"][0]
        self.assertEqual(item["backend"], "secret-service")
        self.assertEqual(item["status"], "unchecked")

    def test_items_sorted_by_connector_id(self) -> None:
        connectors = [
            valid_connector("z-connector", "agent-os-mcp", "env:Z_VAR"),
            valid_connector("a-connector", "agent-os-mcp", "env:A_VAR"),
            valid_connector("m-connector", "agent-os-mcp", None),
        ]
        with patch("agent_os.connectors.load_connector_registry", return_value=valid_registry(connectors)):
            result = connector_credential_status()

        self.assertEqual(len(result["items"]), 3)
        self.assertEqual(result["items"][0]["connector_id"], "a-connector")
        self.assertEqual(result["items"][1]["connector_id"], "m-connector")
        self.assertEqual(result["items"][2]["connector_id"], "z-connector")

    def test_status_counts_aggregates_statuses(self) -> None:
        connectors = [
            valid_connector("conn-a", "agent-os-mcp", "env:PRESENT_VAR"),
            valid_connector("conn-b", "agent-os-mcp", "env:MISSING_VAR"),
            valid_connector("conn-c", "agent-os-mcp", None),
            valid_connector("conn-d", "agent-os-mcp", "keyring:test"),
        ]
        with patch("agent_os.connectors.load_connector_registry", return_value=valid_registry(connectors)):
            with patch.dict(os.environ, {"PRESENT_VAR": "value"}):
                result = connector_credential_status()

        self.assertEqual(result["status_counts"]["present"], 1)
        self.assertEqual(result["status_counts"]["missing"], 1)
        self.assertEqual(result["status_counts"]["not_configured"], 1)
        self.assertEqual(result["status_counts"]["unchecked"], 1)

    def test_item_contains_exact_keys_no_secret_ref(self) -> None:
        connector = valid_connector(secret_ref=None)
        with patch("agent_os.connectors.load_connector_registry", return_value=valid_registry([connector])):
            result = connector_credential_status()

        item = result["items"][0]
        expected_keys = {"connector_id", "backend", "status", "reason"}
        self.assertEqual(set(item.keys()), expected_keys)

    def test_item_contains_exact_keys_with_secret_ref(self) -> None:
        connector = valid_connector(secret_ref="env:TEST")
        with patch("agent_os.connectors.load_connector_registry", return_value=valid_registry([connector])):
            with patch.dict(os.environ, {"TEST": "value"}):
                result = connector_credential_status()

        item = result["items"][0]
        expected_keys = {"connector_id", "backend", "status", "reason"}
        self.assertEqual(set(item.keys()), expected_keys)

    def test_multiple_connectors_different_surfaces(self) -> None:
        connectors = [
            valid_connector("conn-a", "agent-os-mcp", "env:VAR_A"),
            valid_connector("conn-a", "claude-code", "env:VAR_B"),
        ]
        with patch("agent_os.connectors.load_connector_registry", return_value=valid_registry(connectors)):
            with patch.dict(os.environ, {"VAR_A": "val-a", "VAR_B": "val-b"}):
                result = connector_credential_status()

        self.assertEqual(result["count"], 2)
        self.assertEqual(result["items"][0]["connector_id"], "conn-a")
        self.assertEqual(result["items"][1]["connector_id"], "conn-a")

    def test_multiple_connectors_surface_filter(self) -> None:
        connectors = [
            valid_connector("conn-a", "agent-os-mcp", "env:VAR_A"),
            valid_connector("conn-a", "claude-code", "env:VAR_B"),
        ]
        with patch("agent_os.connectors.load_connector_registry", return_value=valid_registry(connectors)):
            with patch.dict(os.environ, {"VAR_A": "val-a"}):
                result = connector_credential_status("agent-os-mcp")

        self.assertEqual(result["surface_filter"], "agent-os-mcp")
        self.assertEqual(result["count"], 1)
        self.assertEqual(result["items"][0]["connector_id"], "conn-a")

    def test_env_empty_string_returns_missing(self) -> None:
        connector = valid_connector(secret_ref="env:EMPTY_VAR")
        with patch("agent_os.connectors.load_connector_registry", return_value=valid_registry([connector])):
            with patch.dict(os.environ, {"EMPTY_VAR": ""}):
                result = connector_credential_status()

        item = result["items"][0]
        self.assertEqual(item["status"], "missing")
        self.assertEqual(item["reason"], "environment variable is not set or empty")

    def test_complex_secret_ref_names(self) -> None:
        connector = valid_connector(secret_ref="env:AGENT_OS_DB_PASSWORD_STAGING_V2")
        with patch("agent_os.connectors.load_connector_registry", return_value=valid_registry([connector])):
            with patch.dict(os.environ, {"AGENT_OS_DB_PASSWORD_STAGING_V2": "complex-secret"}):
                result = connector_credential_status()

        item = result["items"][0]
        self.assertEqual(item["status"], "present")
        json_output = json.dumps(result)
        self.assertNotIn("AGENT_OS_DB_PASSWORD_STAGING_V2", json_output)
        self.assertNotIn("complex-secret", json_output)


if __name__ == "__main__":
    unittest.main()
