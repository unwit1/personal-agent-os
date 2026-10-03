from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import patch

from sys import path

path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.connectors import connector_provisioning_readiness, REGISTRY_SCHEMA


def valid_connector(
    connector_id: str = "google-drive-work",
    provider_id: str = "google-drive",
    surface_id: str = "agent-os-mcp",
    secret_ref: str | None = ...,  # type: ignore
    server_name: str | None = None,
    state: str = "desired",
) -> dict:
    if secret_ref is ...:  # type: ignore
        secret_ref = f"env:AGENT_OS_{connector_id.upper()}"

    registration = {"surface_id": surface_id, "state": state}
    if server_name is not None:
        registration["server_name"] = server_name

    return {
        "id": connector_id,
        "provider": {"id": provider_id, "name": f"Provider {provider_id}"},
        "capabilities": ["files.search", "files.read"],
        "scopes": ["drive.readonly"],
        "health": {"status": "unknown", "checked_at": None},
        "privacy_domain": "work",
        "registrations": [registration],
        "secret_ref": secret_ref,
    }


def valid_registry(connectors: list[dict] | None = None) -> dict:
    if connectors is None:
        connectors = [valid_connector()]
    return {"schema": REGISTRY_SCHEMA, "version": 1, "connectors": connectors}


def mock_surfaces() -> list[dict]:
    return [
        {
            "id": "agent-os-mcp",
            "name": "Agent OS MCP",
            "vendor": "Anthropic",
            "mechanism": "MCP",
            "summary": "Direct Agent OS MCP integration",
            "expected_tier": "routed",
            "invocation": {"kind": "none"},
            "instruction": {"kind": "none"},
            "capture": {"kind": "none"},
            "connector_capabilities": {
                "inspect_local_config": {"available": True, "reason": None},
                "mutate_local_config": {"available": True, "reason": None},
                "transfer_credentials": {"available": False, "reason": "not supported"},
                "agent_os_bridge": {"available": True, "reason": None},
            },
        },
    ]


class ConnectorProvisioningReadinessTests(unittest.TestCase):
    def test_returns_correct_schema_and_structure(self) -> None:
        with patch("agent_os.connectors.load_connector_registry", return_value=valid_registry()):
            with patch("agent_os.surfaces.surfaces", return_value=mock_surfaces()):
                result = connector_provisioning_readiness()
                self.assertEqual(result["schema"], "personal-agent/connector-provisioning-readiness/v1")
                self.assertTrue(result["read_only"])
                self.assertEqual(result["surface_filter"], None)
                self.assertIsInstance(result["items"], list)
                self.assertEqual(result["count"], len(result["items"]))

    def test_items_have_required_fields(self) -> None:
        with patch("agent_os.connectors.load_connector_registry", return_value=valid_registry()):
            with patch("agent_os.surfaces.surfaces", return_value=mock_surfaces()):
                result = connector_provisioning_readiness()
                required_fields = {"connector_id", "surface_id", "state", "action", "credential_status", "readiness", "blockers"}
                for item in result["items"]:
                    self.assertEqual(set(item.keys()), required_fields)

    def test_readiness_no_action(self) -> None:
        connector = valid_connector(state="registered")
        with patch("agent_os.connectors.load_connector_registry", return_value=valid_registry([connector])):
            with patch("agent_os.surfaces.surfaces", return_value=mock_surfaces()):
                result = connector_provisioning_readiness()
                self.assertEqual(len(result["items"]), 1)
                item = result["items"][0]
                self.assertEqual(item["action"], "none")
                self.assertEqual(item["readiness"], "no_action")

    def test_readiness_ready_with_present_credential(self) -> None:
        import os
        connector = valid_connector()
        os.environ["AGENT_OS_GOOGLE-DRIVE-WORK"] = "test_token"
        try:
            with patch("agent_os.connectors.load_connector_registry", return_value=valid_registry([connector])):
                with patch("agent_os.surfaces.surfaces", return_value=mock_surfaces()):
                    result = connector_provisioning_readiness()
                    self.assertEqual(len(result["items"]), 1)
                    item = result["items"][0]
                    self.assertEqual(item["credential_status"], "present")
                    self.assertEqual(item["blockers"], [])
                    self.assertEqual(item["readiness"], "ready")
        finally:
            os.environ.pop("AGENT_OS_GOOGLE-DRIVE-WORK", None)

    def test_credential_status_missing(self) -> None:
        import os
        connector = valid_connector()
        os.environ.pop("AGENT_OS_GOOGLE-DRIVE-WORK", None)
        try:
            with patch("agent_os.connectors.load_connector_registry", return_value=valid_registry([connector])):
                with patch("agent_os.surfaces.surfaces", return_value=mock_surfaces()):
                    result = connector_provisioning_readiness()
                    item = result["items"][0]
                    self.assertEqual(item["credential_status"], "missing")
                    self.assertIn("credential_missing", item["blockers"])
                    self.assertEqual(item["readiness"], "blocked")
        finally:
            pass

    def test_credential_status_not_configured(self) -> None:
        connector = valid_connector(secret_ref=None)
        with patch("agent_os.connectors.load_connector_registry", return_value=valid_registry([connector])):
            with patch("agent_os.surfaces.surfaces", return_value=mock_surfaces()):
                result = connector_provisioning_readiness()
                item = result["items"][0]
                self.assertEqual(item["credential_status"], "not_configured")

    def test_unknown_surface_blocker(self) -> None:
        connector = valid_connector(surface_id="unknown-surface")
        with patch("agent_os.connectors.load_connector_registry", return_value=valid_registry([connector])):
            with patch("agent_os.surfaces.surfaces", return_value=mock_surfaces()):
                result = connector_provisioning_readiness()
                item = result["items"][0]
                self.assertEqual(item["action"], "unknown_surface")
                self.assertIn("unknown_surface", item["blockers"])
                self.assertEqual(item["readiness"], "blocked")

    def test_surface_filter(self) -> None:
        connectors = [
            valid_connector(connector_id="c1", surface_id="agent-os-mcp"),
            valid_connector(connector_id="c2", surface_id="other-surface"),
        ]
        with patch("agent_os.connectors.load_connector_registry", return_value=valid_registry(connectors)):
            with patch("agent_os.surfaces.surfaces", return_value=mock_surfaces()):
                result = connector_provisioning_readiness(surface_id="agent-os-mcp")
                self.assertEqual(result["surface_filter"], "agent-os-mcp")
                self.assertEqual(len(result["items"]), 1)
                self.assertEqual(result["items"][0]["connector_id"], "c1")

    def test_investigate_action_blocker(self) -> None:
        connector = valid_connector(state="error")
        with patch("agent_os.connectors.load_connector_registry", return_value=valid_registry([connector])):
            with patch("agent_os.surfaces.surfaces", return_value=mock_surfaces()):
                with patch("agent_os.connectors._windows_credential_present", return_value=True):
                    result = connector_provisioning_readiness()
                    item = result["items"][0]
                    self.assertEqual(item["action"], "investigate")
                    self.assertIn("registration_error", item["blockers"])
                    self.assertEqual(item["readiness"], "blocked")

    def test_shared_credential_conflict_blocker(self) -> None:
        import os
        os.environ["SHARED_CRED"] = "test_value"
        try:
            connectors = [
                valid_connector(connector_id="c1", secret_ref="env:SHARED_CRED"),
                valid_connector(connector_id="c2", secret_ref="env:SHARED_CRED"),
            ]
            with patch("agent_os.connectors.load_connector_registry", return_value=valid_registry(connectors)):
                with patch("agent_os.surfaces.surfaces", return_value=mock_surfaces()):
                    result = connector_provisioning_readiness()
                    self.assertEqual(len(result["items"]), 2)
                    for item in result["items"]:
                        self.assertIn("conflict:shared_credential_reference", item["blockers"])
                        self.assertEqual(item["readiness"], "blocked")
        finally:
            os.environ.pop("SHARED_CRED", None)

    def test_duplicate_provider_surface_conflict(self) -> None:
        import os
        os.environ["AGENT_OS_C1"] = "token1"
        os.environ["AGENT_OS_C2"] = "token2"
        try:
            connectors = [
                valid_connector(connector_id="c1", provider_id="google"),
                valid_connector(connector_id="c2", provider_id="google"),
            ]
            with patch("agent_os.connectors.load_connector_registry", return_value=valid_registry(connectors)):
                with patch("agent_os.surfaces.surfaces", return_value=mock_surfaces()):
                    result = connector_provisioning_readiness()
                    self.assertEqual(len(result["items"]), 2)
                    for item in result["items"]:
                        self.assertIn("conflict:duplicate_provider_surface", item["blockers"])
                        self.assertEqual(item["readiness"], "blocked")
        finally:
            os.environ.pop("AGENT_OS_C1", None)
            os.environ.pop("AGENT_OS_C2", None)

    def test_native_entry_absent_blocker(self) -> None:
        import tempfile
        import json

        connector = valid_connector(server_name="claude-code")
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"
            config_path.write_text(json.dumps({"mcpServers": {"other-server": {"command": "other"}}}))

            surface = {
                "id": "agent-os-mcp",
                "name": "Agent OS MCP",
                "vendor": "Anthropic",
                "mechanism": "MCP",
                "summary": "Direct Agent OS MCP integration",
                "expected_tier": "routed",
                "invocation": {"kind": "json", "registrations": [str(config_path)]},
                "instruction": {"kind": "none"},
                "capture": {"kind": "none"},
                "connector_capabilities": {
                    "inspect_local_config": {"available": True, "reason": None},
                    "mutate_local_config": {"available": True, "reason": None},
                    "transfer_credentials": {"available": False, "reason": "not supported"},
                    "agent_os_bridge": {"available": True, "reason": None},
                },
            }

            with patch("agent_os.connectors.load_connector_registry", return_value=valid_registry([connector])):
                with patch("agent_os.surfaces.surfaces", return_value=[surface]):
                    with patch("agent_os.machine.resolve_user_path", side_effect=lambda p: Path(p)):
                        with patch("agent_os.connectors._windows_credential_present", return_value=True):
                            result = connector_provisioning_readiness()
                            item = result["items"][0]
                            self.assertIn("native_entry_absent", item["blockers"])
                            self.assertEqual(item["readiness"], "blocked")

    def test_multiple_blockers_sorted(self) -> None:
        import os
        import tempfile
        import json

        os.environ.pop("AGENT_OS_C1", None)
        os.environ.pop("AGENT_OS_C2", None)
        os.environ["SHARED_CRED"] = "shared_value"

        try:
            connector = valid_connector(
                connector_id="c1",
                secret_ref="env:SHARED_CRED",
                state="error",
                server_name="missing-server"
            )
            connectors = [
                connector,
                valid_connector(connector_id="c2", secret_ref="env:SHARED_CRED"),
            ]

            with tempfile.TemporaryDirectory() as tmpdir:
                config_path = Path(tmpdir) / "config.json"
                config_path.write_text(json.dumps({"mcpServers": {}}))

                surface = {
                    "id": "agent-os-mcp",
                    "name": "Agent OS MCP",
                    "vendor": "Anthropic",
                    "mechanism": "MCP",
                    "summary": "Direct Agent OS MCP integration",
                    "expected_tier": "routed",
                    "invocation": {"kind": "json", "registrations": [str(config_path)]},
                    "instruction": {"kind": "none"},
                    "capture": {"kind": "none"},
                    "connector_capabilities": {
                        "inspect_local_config": {"available": True, "reason": None},
                        "mutate_local_config": {"available": True, "reason": None},
                        "transfer_credentials": {"available": False, "reason": "not supported"},
                        "agent_os_bridge": {"available": True, "reason": None},
                    },
                }

                with patch("agent_os.connectors.load_connector_registry", return_value=valid_registry(connectors)):
                    with patch("agent_os.surfaces.surfaces", return_value=[surface]):
                        with patch("agent_os.machine.resolve_user_path", side_effect=lambda p: Path(p)):
                            result = connector_provisioning_readiness()
                            c1_item = next(item for item in result["items"] if item["connector_id"] == "c1")
                            expected_blockers = [
                                "registration_error",
                                "native_entry_absent",
                                "conflict:duplicate_provider_surface",
                                "conflict:shared_credential_reference",
                            ]
                            self.assertEqual(c1_item["blockers"], expected_blockers)
                            self.assertEqual(c1_item["readiness"], "blocked")
        finally:
            os.environ.pop("SHARED_CRED", None)


if __name__ == "__main__":
    unittest.main()
