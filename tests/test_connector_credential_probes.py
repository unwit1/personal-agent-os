from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.connectors import (
    _macos_keychain_present,
    _windows_credential_present,
    connector_credential_status,
    REGISTRY_SCHEMA,
)


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


class CredentialProbeTests(unittest.TestCase):
    def test_windows_credential_present_returns_none_on_linux(self) -> None:
        with patch("agent_os.connectors.sys.platform", "linux"):
            result = _windows_credential_present("test-cred")
            self.assertIsNone(result)

    def test_macos_keychain_present_returns_none_on_win32(self) -> None:
        with patch("agent_os.connectors.sys.platform", "win32"):
            result = _macos_keychain_present("test-cred")
            self.assertIsNone(result)

    def test_macos_keychain_present_returns_none_on_darwin_without_security(self) -> None:
        with patch("agent_os.connectors.sys.platform", "darwin"), \
             patch("agent_os.connectors.shutil.which", return_value=None):
            result = _macos_keychain_present("test-cred")
            self.assertIsNone(result)

    def test_macos_keychain_present_returncode_0_returns_true(self) -> None:
        with patch("agent_os.connectors.sys.platform", "darwin"), \
             patch("agent_os.connectors.shutil.which", return_value="/usr/bin/security"), \
             patch("agent_os.connectors.subprocess.run", return_value=SimpleNamespace(returncode=0)) as mock_run:
            result = _macos_keychain_present("test-svc")
            self.assertIs(result, True)
            # Verify exact command args
            cmd = mock_run.call_args.args[0]
            self.assertEqual(cmd, ["security", "find-generic-password", "-s", "test-svc"])

    def test_macos_keychain_present_returncode_44_returns_false(self) -> None:
        with patch("agent_os.connectors.sys.platform", "darwin"), \
             patch("agent_os.connectors.shutil.which", return_value="/usr/bin/security"), \
             patch("agent_os.connectors.subprocess.run", return_value=SimpleNamespace(returncode=44)) as mock_run:
            result = _macos_keychain_present("test-svc")
            self.assertIs(result, False)
            # Verify no -w or -g flags
            cmd = mock_run.call_args.args[0]
            self.assertNotIn("-w", cmd)
            self.assertNotIn("-g", cmd)

    def test_macos_keychain_present_returncode_1_returns_none(self) -> None:
        with patch("agent_os.connectors.sys.platform", "darwin"), \
             patch("agent_os.connectors.shutil.which", return_value="/usr/bin/security"), \
             patch("agent_os.connectors.subprocess.run", return_value=SimpleNamespace(returncode=1)) as mock_run:
            result = _macos_keychain_present("test-svc")
            self.assertIsNone(result)
            # Verify exact command args
            cmd = mock_run.call_args.args[0]
            self.assertEqual(cmd, ["security", "find-generic-password", "-s", "test-svc"])

    def test_macos_keychain_present_timeout_returns_none(self) -> None:
        with patch("agent_os.connectors.sys.platform", "darwin"), \
             patch("agent_os.connectors.shutil.which", return_value="/usr/bin/security"), \
             patch("agent_os.connectors.subprocess.run", side_effect=subprocess.TimeoutExpired("security", 5)):
            result = _macos_keychain_present("test-svc")
            self.assertIsNone(result)

    def test_macos_keychain_present_oserror_returns_none(self) -> None:
        with patch("agent_os.connectors.sys.platform", "darwin"), \
             patch("agent_os.connectors.shutil.which", return_value="/usr/bin/security"), \
             patch("agent_os.connectors.subprocess.run", side_effect=OSError):
            result = _macos_keychain_present("test-svc")
            self.assertIsNone(result)

    def test_windows_credential_status_present(self) -> None:
        connector = valid_connector(secret_ref="windows-credential:AGENT_OS_TEST")
        with patch("agent_os.connectors.load_connector_registry", return_value=valid_registry([connector])), \
             patch("agent_os.connectors._windows_credential_present", return_value=True):
            result = connector_credential_status()

        item = result["items"][0]
        self.assertEqual(item["backend"], "windows-credential")
        self.assertEqual(item["status"], "present")
        self.assertEqual(item["reason"], "credential store entry exists")
        # Verify secret ref not in output
        json_output = json.dumps(result)
        self.assertNotIn("AGENT_OS_TEST", json_output)
        self.assertNotIn("windows-credential:AGENT_OS_TEST", json_output)

    def test_windows_credential_status_missing(self) -> None:
        connector = valid_connector(secret_ref="windows-credential:AGENT_OS_TEST")
        with patch("agent_os.connectors.load_connector_registry", return_value=valid_registry([connector])), \
             patch("agent_os.connectors._windows_credential_present", return_value=False):
            result = connector_credential_status()

        item = result["items"][0]
        self.assertEqual(item["backend"], "windows-credential")
        self.assertEqual(item["status"], "missing")
        self.assertEqual(item["reason"], "credential store entry was not found")
        # Verify secret ref not in output
        json_output = json.dumps(result)
        self.assertNotIn("AGENT_OS_TEST", json_output)

    def test_windows_credential_status_unchecked(self) -> None:
        connector = valid_connector(secret_ref="windows-credential:AGENT_OS_TEST")
        with patch("agent_os.connectors.load_connector_registry", return_value=valid_registry([connector])), \
             patch("agent_os.connectors._windows_credential_present", return_value=None):
            result = connector_credential_status()

        item = result["items"][0]
        self.assertEqual(item["backend"], "windows-credential")
        self.assertEqual(item["status"], "unchecked")
        self.assertEqual(item["reason"], "windows-credential presence check is unavailable on this host")
        # Verify secret ref not in output
        json_output = json.dumps(result)
        self.assertNotIn("AGENT_OS_TEST", json_output)

    def test_macos_keychain_status_present(self) -> None:
        connector = valid_connector(secret_ref="macos-keychain:agent-os/drive")
        with patch("agent_os.connectors.load_connector_registry", return_value=valid_registry([connector])), \
             patch("agent_os.connectors._macos_keychain_present", return_value=True):
            result = connector_credential_status()

        item = result["items"][0]
        self.assertEqual(item["backend"], "macos-keychain")
        self.assertEqual(item["status"], "present")
        self.assertEqual(item["reason"], "credential store entry exists")
        # Verify secret ref not in output
        json_output = json.dumps(result)
        self.assertNotIn("agent-os/drive", json_output)
        self.assertNotIn("macos-keychain:agent-os/drive", json_output)

    def test_macos_keychain_status_missing(self) -> None:
        connector = valid_connector(secret_ref="macos-keychain:agent-os/drive")
        with patch("agent_os.connectors.load_connector_registry", return_value=valid_registry([connector])), \
             patch("agent_os.connectors._macos_keychain_present", return_value=False):
            result = connector_credential_status()

        item = result["items"][0]
        self.assertEqual(item["backend"], "macos-keychain")
        self.assertEqual(item["status"], "missing")
        self.assertEqual(item["reason"], "credential store entry was not found")
        # Verify secret ref not in output
        json_output = json.dumps(result)
        self.assertNotIn("agent-os/drive", json_output)

    def test_macos_keychain_status_unchecked(self) -> None:
        connector = valid_connector(secret_ref="macos-keychain:agent-os/drive")
        with patch("agent_os.connectors.load_connector_registry", return_value=valid_registry([connector])), \
             patch("agent_os.connectors._macos_keychain_present", return_value=None):
            result = connector_credential_status()

        item = result["items"][0]
        self.assertEqual(item["backend"], "macos-keychain")
        self.assertEqual(item["status"], "unchecked")
        self.assertEqual(item["reason"], "macos-keychain presence check is unavailable on this host")
        # Verify secret ref not in output
        json_output = json.dumps(result)
        self.assertNotIn("agent-os/drive", json_output)

    def test_keyring_backend_does_not_call_probe_helpers(self) -> None:
        connector = valid_connector(secret_ref="keyring:agent-os/drive")
        with patch("agent_os.connectors.load_connector_registry", return_value=valid_registry([connector])), \
             patch("agent_os.connectors._windows_credential_present") as mock_windows, \
             patch("agent_os.connectors._macos_keychain_present") as mock_macos:
            result = connector_credential_status()

        item = result["items"][0]
        self.assertEqual(item["backend"], "keyring")
        self.assertEqual(item["status"], "unchecked")
        self.assertIn("presence checks for the keyring backend are not implemented yet", item["reason"])
        # Verify helpers were not called
        mock_windows.assert_not_called()
        mock_macos.assert_not_called()


if __name__ == "__main__":
    unittest.main()
