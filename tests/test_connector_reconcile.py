from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.connectors import connector_reconcile_plan, REGISTRY_SCHEMA
from agent_os.surfaces import _connector_capabilities


def valid_connector(connector_id: str = "google-drive-work", surface_id: str = "agent-os-mcp", state: str = "desired") -> dict:
    return {
        "id": connector_id,
        "provider": {"id": "google-drive", "name": "Google Drive"},
        "capabilities": ["files.search", "files.read"],
        "scopes": ["drive.readonly"],
        "health": {"status": "unknown", "checked_at": None},
        "privacy_domain": "work",
        "registrations": [{"surface_id": surface_id, "state": state}],
        "secret_ref": "keyring:agent-os/google-drive-work",
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
        {
            "id": "claude-code",
            "name": "Claude Code",
            "vendor": "Anthropic",
            "mechanism": "Web",
            "summary": "Web-based Claude Code integration",
            "expected_tier": "bridged",
            "invocation": {"kind": "none"},
            "instruction": {"kind": "none"},
            "capture": {"kind": "none"},
            "connector_capabilities": {
                "inspect_local_config": {"available": False, "reason": "web-based"},
                "mutate_local_config": {"available": False, "reason": "web-based"},
                "transfer_credentials": {"available": False, "reason": "web-based"},
                "agent_os_bridge": {"available": None, "reason": "bridge status unknown"},
            },
        },
    ]


class ConnectorReconcilePlanTests(unittest.TestCase):
    def test_returns_correct_schema_and_structure(self) -> None:
        with patch("agent_os.connectors.load_connector_registry", return_value=valid_registry()):
            with patch("agent_os.surfaces.surfaces", return_value=mock_surfaces()):
                result = connector_reconcile_plan()

        self.assertEqual(result["schema"], "personal-agent/connector-reconcile-plan/v1")
        self.assertEqual(result["applied"], False)
        self.assertIsNone(result["surface_filter"])
        self.assertIn("count", result)
        self.assertIn("action_counts", result)
        self.assertIn("items", result)

    def test_empty_registry_returns_empty_items(self) -> None:
        with patch("agent_os.connectors.load_connector_registry", return_value=valid_registry([])):
            with patch("agent_os.surfaces.surfaces", return_value=mock_surfaces()):
                result = connector_reconcile_plan()

        self.assertEqual(result["count"], 0)
        self.assertEqual(result["items"], [])
        self.assertEqual(result["action_counts"], {})

    def test_filters_by_surface_id(self) -> None:
        connectors = [
            valid_connector("conn-a", "agent-os-mcp", "desired"),
            valid_connector("conn-b", "claude-code", "desired"),
        ]
        with patch("agent_os.connectors.load_connector_registry", return_value=valid_registry(connectors)):
            with patch("agent_os.surfaces.surfaces", return_value=mock_surfaces()):
                result = connector_reconcile_plan("agent-os-mcp")

        self.assertEqual(result["surface_filter"], "agent-os-mcp")
        self.assertEqual(result["count"], 1)
        self.assertEqual(result["items"][0]["surface_id"], "agent-os-mcp")

    def test_desired_state_with_mutate_available_true(self) -> None:
        with patch("agent_os.connectors.load_connector_registry", return_value=valid_registry()):
            with patch("agent_os.surfaces.surfaces", return_value=mock_surfaces()):
                result = connector_reconcile_plan()

        item = result["items"][0]
        self.assertEqual(item["state"], "desired")
        self.assertEqual(item["action"], "provision_local_config")
        self.assertIsInstance(item["reason"], str)
        self.assertGreater(len(item["reason"]), 0)
        self.assertEqual(item["reason"], "connector capability has not been declared for this surface")

    def test_desired_state_with_mutate_available_true_explicit_reason(self) -> None:
        surfaces = [
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
                    "mutate_local_config": {"available": True, "reason": "explicit capability reason"},
                    "transfer_credentials": {"available": False, "reason": "not supported"},
                    "agent_os_bridge": {"available": True, "reason": None},
                },
            },
        ]
        with patch("agent_os.connectors.load_connector_registry", return_value=valid_registry()):
            with patch("agent_os.surfaces.surfaces", return_value=surfaces):
                result = connector_reconcile_plan()

        item = result["items"][0]
        self.assertEqual(item["state"], "desired")
        self.assertEqual(item["action"], "provision_local_config")
        self.assertEqual(item["reason"], "explicit capability reason")

    def test_desired_state_with_mutate_available_false(self) -> None:
        connectors = [valid_connector("conn-a", "claude-code", "desired")]
        with patch("agent_os.connectors.load_connector_registry", return_value=valid_registry(connectors)):
            with patch("agent_os.surfaces.surfaces", return_value=mock_surfaces()):
                result = connector_reconcile_plan()

        item = result["items"][0]
        self.assertEqual(item["state"], "desired")
        self.assertEqual(item["action"], "manual_host_setup")
        self.assertEqual(item["reason"], "web-based")

    def test_desired_state_with_mutate_available_none(self) -> None:
        surfaces = [
            {
                "id": "undeclared-surface",
                "name": "Undeclared",
                "vendor": "Test",
                "mechanism": "Test",
                "summary": "Test surface",
                "expected_tier": "unintegrated",
                "invocation": {"kind": "none"},
                "instruction": {"kind": "none"},
                "capture": {"kind": "none"},
            },
        ]
        connectors = [valid_connector("conn-a", "undeclared-surface", "desired")]
        with patch("agent_os.connectors.load_connector_registry", return_value=valid_registry(connectors)):
            with patch("agent_os.surfaces.surfaces", return_value=surfaces):
                result = connector_reconcile_plan()

        item = result["items"][0]
        self.assertEqual(item["state"], "desired")
        self.assertEqual(item["action"], "undetermined")
        self.assertEqual(item["reason"], "connector capability has not been declared for this surface")

    def test_registered_state_no_action(self) -> None:
        connectors = [valid_connector("conn-a", "agent-os-mcp", "registered")]
        with patch("agent_os.connectors.load_connector_registry", return_value=valid_registry(connectors)):
            with patch("agent_os.surfaces.surfaces", return_value=mock_surfaces()):
                result = connector_reconcile_plan()

        item = result["items"][0]
        self.assertEqual(item["state"], "registered")
        self.assertEqual(item["action"], "none")
        self.assertEqual(item["reason"], "registration is already registered")

    def test_disabled_state_no_action(self) -> None:
        connectors = [valid_connector("conn-a", "agent-os-mcp", "disabled")]
        with patch("agent_os.connectors.load_connector_registry", return_value=valid_registry(connectors)):
            with patch("agent_os.surfaces.surfaces", return_value=mock_surfaces()):
                result = connector_reconcile_plan()

        item = result["items"][0]
        self.assertEqual(item["state"], "disabled")
        self.assertEqual(item["action"], "none")
        self.assertEqual(item["reason"], "registration is already disabled")

    def test_unsupported_state_no_action(self) -> None:
        connectors = [valid_connector("conn-a", "agent-os-mcp", "unsupported")]
        with patch("agent_os.connectors.load_connector_registry", return_value=valid_registry(connectors)):
            with patch("agent_os.surfaces.surfaces", return_value=mock_surfaces()):
                result = connector_reconcile_plan()

        item = result["items"][0]
        self.assertEqual(item["state"], "unsupported")
        self.assertEqual(item["action"], "none")
        self.assertEqual(item["reason"], "registration is already unsupported")

    def test_error_state_investigate(self) -> None:
        connectors = [valid_connector("conn-a", "agent-os-mcp", "error")]
        with patch("agent_os.connectors.load_connector_registry", return_value=valid_registry(connectors)):
            with patch("agent_os.surfaces.surfaces", return_value=mock_surfaces()):
                result = connector_reconcile_plan()

        item = result["items"][0]
        self.assertEqual(item["state"], "error")
        self.assertEqual(item["action"], "investigate")
        self.assertEqual(item["reason"], "registration reported an error; an adapter must re-verify it")

    def test_unknown_surface_action(self) -> None:
        connectors = [valid_connector("conn-a", "unknown-surface", "desired")]
        with patch("agent_os.connectors.load_connector_registry", return_value=valid_registry(connectors)):
            with patch("agent_os.surfaces.surfaces", return_value=mock_surfaces()):
                result = connector_reconcile_plan()

        item = result["items"][0]
        self.assertEqual(item["action"], "unknown_surface")
        self.assertEqual(item["reason"], "surface is not declared in the surface registry")

    def test_items_sorted_by_connector_and_surface_id(self) -> None:
        connectors = [
            valid_connector("z-conn", "agent-os-mcp", "desired"),
            valid_connector("a-conn", "claude-code", "desired"),
            valid_connector("a-conn", "agent-os-mcp", "desired"),
        ]
        with patch("agent_os.connectors.load_connector_registry", return_value=valid_registry(connectors)):
            with patch("agent_os.surfaces.surfaces", return_value=mock_surfaces()):
                result = connector_reconcile_plan()

        self.assertEqual(len(result["items"]), 3)
        self.assertEqual(result["items"][0]["connector_id"], "a-conn")
        self.assertEqual(result["items"][0]["surface_id"], "agent-os-mcp")
        self.assertEqual(result["items"][1]["connector_id"], "a-conn")
        self.assertEqual(result["items"][1]["surface_id"], "claude-code")
        self.assertEqual(result["items"][2]["connector_id"], "z-conn")

    def test_action_counts_aggregates_actions(self) -> None:
        connectors = [
            valid_connector("conn-a", "agent-os-mcp", "desired"),
            valid_connector("conn-b", "agent-os-mcp", "registered"),
            valid_connector("conn-c", "claude-code", "desired"),
        ]
        with patch("agent_os.connectors.load_connector_registry", return_value=valid_registry(connectors)):
            with patch("agent_os.surfaces.surfaces", return_value=mock_surfaces()):
                result = connector_reconcile_plan()

        self.assertEqual(result["action_counts"]["provision_local_config"], 1)
        self.assertEqual(result["action_counts"]["none"], 1)
        self.assertEqual(result["action_counts"]["manual_host_setup"], 1)

    def test_credential_reference_configured_boolean(self) -> None:
        with_secret = {**valid_connector(), "secret_ref": "keyring:test"}
        without_secret = {**valid_connector(), "secret_ref": None}

        with patch("agent_os.connectors.load_connector_registry", return_value=valid_registry([with_secret])):
            with patch("agent_os.surfaces.surfaces", return_value=mock_surfaces()):
                result = connector_reconcile_plan()
            self.assertTrue(result["items"][0]["credential_reference_configured"])

        with patch("agent_os.connectors.load_connector_registry", return_value=valid_registry([without_secret])):
            with patch("agent_os.surfaces.surfaces", return_value=mock_surfaces()):
                result = connector_reconcile_plan()
            self.assertFalse(result["items"][0]["credential_reference_configured"])

    def test_item_contains_exact_keys(self) -> None:
        with patch("agent_os.connectors.load_connector_registry", return_value=valid_registry()):
            with patch("agent_os.surfaces.surfaces", return_value=mock_surfaces()):
                result = connector_reconcile_plan()

        item = result["items"][0]
        expected_keys = {"connector_id", "surface_id", "state", "action", "reason", "credential_reference_configured", "native_server_name", "native_entry_requested", "native_entry_status"}
        self.assertEqual(set(item.keys()), expected_keys)

    def test_multiple_registrations_per_connector(self) -> None:
        connector = valid_connector()
        connector["registrations"] = [
            {"surface_id": "agent-os-mcp", "state": "desired"},
            {"surface_id": "claude-code", "state": "registered"},
        ]
        with patch("agent_os.connectors.load_connector_registry", return_value=valid_registry([connector])):
            with patch("agent_os.surfaces.surfaces", return_value=mock_surfaces()):
                result = connector_reconcile_plan()

        self.assertEqual(result["count"], 2)
        self.assertEqual(result["items"][0]["action"], "provision_local_config")
        self.assertEqual(result["items"][1]["action"], "none")

    def test_native_server_name_when_present(self) -> None:
        connector = valid_connector()
        connector["registrations"] = [{"surface_id": "agent-os-mcp", "state": "desired", "server_name": "my-server"}]
        with patch("agent_os.connectors.load_connector_registry", return_value=valid_registry([connector])):
            with patch("agent_os.surfaces.surfaces", return_value=mock_surfaces()):
                result = connector_reconcile_plan()

        item = result["items"][0]
        self.assertEqual(item["native_server_name"], "my-server")
        self.assertTrue(item["native_entry_requested"])

    def test_native_server_name_when_absent(self) -> None:
        connector = valid_connector()
        connector["registrations"] = [{"surface_id": "agent-os-mcp", "state": "desired"}]
        with patch("agent_os.connectors.load_connector_registry", return_value=valid_registry([connector])):
            with patch("agent_os.surfaces.surfaces", return_value=mock_surfaces()):
                result = connector_reconcile_plan()

        item = result["items"][0]
        self.assertIsNone(item["native_server_name"])
        self.assertFalse(item["native_entry_requested"])

    def test_native_entry_status_not_requested(self) -> None:
        connector = valid_connector()
        connector["registrations"] = [{"surface_id": "agent-os-mcp", "state": "desired"}]
        with patch("agent_os.connectors.load_connector_registry", return_value=valid_registry([connector])):
            with patch("agent_os.surfaces.surfaces", return_value=mock_surfaces()):
                result = connector_reconcile_plan()

        item = result["items"][0]
        self.assertEqual(item["native_entry_status"], "not_requested")
        self.assertIn("not_requested", result["native_entry_status_counts"])
        self.assertEqual(result["native_entry_status_counts"]["not_requested"], 1)

    def test_native_entry_status_not_inspectable(self) -> None:
        connector = valid_connector()
        connector["registrations"] = [{"surface_id": "claude-code", "state": "desired", "server_name": "test-server"}]
        with patch("agent_os.connectors.load_connector_registry", return_value=valid_registry([connector])):
            with patch("agent_os.surfaces.surfaces", return_value=mock_surfaces()):
                result = connector_reconcile_plan()

        item = result["items"][0]
        self.assertEqual(item["native_entry_status"], "not_inspectable")
        self.assertIn("not_inspectable", result["native_entry_status_counts"])

    def test_native_entry_status_unknown_surface(self) -> None:
        connector = valid_connector()
        connector["registrations"] = [{"surface_id": "unknown-surface", "state": "desired", "server_name": "test-server"}]
        with patch("agent_os.connectors.load_connector_registry", return_value=valid_registry([connector])):
            with patch("agent_os.surfaces.surfaces", return_value=mock_surfaces()):
                result = connector_reconcile_plan()

        item = result["items"][0]
        self.assertEqual(item["native_entry_status"], "unknown_surface")
        self.assertIn("unknown_surface", result["native_entry_status_counts"])

    def test_native_entry_status_present_in_json_file(self) -> None:
        import tempfile
        import json as json_module

        connector = valid_connector()
        connector["registrations"] = [{"surface_id": "agent-os-mcp", "state": "desired", "server_name": "test-server"}]

        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "config.json"
            config_data = {
                "mcpServers": {
                    "test-server": {"command": "python test.py"},
                    "other-server": {"command": "python other.py"},
                }
            }
            config_file.write_text(json_module.dumps(config_data), encoding="utf-8")

            surfaces_data = [
                {
                    "id": "agent-os-mcp",
                    "name": "Agent OS MCP",
                    "vendor": "Anthropic",
                    "mechanism": "MCP",
                    "summary": "Direct Agent OS MCP integration",
                    "expected_tier": "routed",
                    "invocation": {"kind": "json", "registrations": [str(config_file)]},
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

            with patch("agent_os.connectors.load_connector_registry", return_value=valid_registry([connector])):
                with patch("agent_os.surfaces.surfaces", return_value=surfaces_data):
                    with patch("agent_os.machine.resolve_user_path", side_effect=lambda p: Path(p)):
                        result = connector_reconcile_plan()

            item = result["items"][0]
            self.assertEqual(item["native_entry_status"], "present")
            self.assertEqual(result["native_entry_status_counts"]["present"], 1)

    def test_native_entry_status_absent_in_json_file(self) -> None:
        import tempfile
        import json as json_module

        connector = valid_connector()
        connector["registrations"] = [{"surface_id": "agent-os-mcp", "state": "desired", "server_name": "missing-server"}]

        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "config.json"
            config_data = {
                "mcpServers": {
                    "test-server": {"command": "python test.py"},
                    "other-server": {"command": "python other.py"},
                }
            }
            config_file.write_text(json_module.dumps(config_data), encoding="utf-8")

            surfaces_data = [
                {
                    "id": "agent-os-mcp",
                    "name": "Agent OS MCP",
                    "vendor": "Anthropic",
                    "mechanism": "MCP",
                    "summary": "Direct Agent OS MCP integration",
                    "expected_tier": "routed",
                    "invocation": {"kind": "json", "registrations": [str(config_file)]},
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

            with patch("agent_os.connectors.load_connector_registry", return_value=valid_registry([connector])):
                with patch("agent_os.surfaces.surfaces", return_value=surfaces_data):
                    with patch("agent_os.machine.resolve_user_path", side_effect=lambda p: Path(p)):
                        result = connector_reconcile_plan()

            item = result["items"][0]
            self.assertEqual(item["native_entry_status"], "absent")
            self.assertEqual(result["native_entry_status_counts"]["absent"], 1)

    def test_native_entry_status_unreadable_malformed_file(self) -> None:
        import tempfile

        connector = valid_connector()
        connector["registrations"] = [{"surface_id": "agent-os-mcp", "state": "desired", "server_name": "test-server"}]

        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "config.json"
            config_file.write_text("{ invalid json }", encoding="utf-8")

            surfaces_data = [
                {
                    "id": "agent-os-mcp",
                    "name": "Agent OS MCP",
                    "vendor": "Anthropic",
                    "mechanism": "MCP",
                    "summary": "Direct Agent OS MCP integration",
                    "expected_tier": "routed",
                    "invocation": {"kind": "json", "registrations": [str(config_file)]},
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

            with patch("agent_os.connectors.load_connector_registry", return_value=valid_registry([connector])):
                with patch("agent_os.surfaces.surfaces", return_value=surfaces_data):
                    with patch("agent_os.machine.resolve_user_path", side_effect=lambda p: Path(p)):
                        result = connector_reconcile_plan()

            item = result["items"][0]
            self.assertEqual(item["native_entry_status"], "unreadable")
            self.assertEqual(result["native_entry_status_counts"]["unreadable"], 1)

    def test_native_entry_status_counts_aggregation(self) -> None:
        connectors = [
            valid_connector("conn-a", "agent-os-mcp", "desired"),
            valid_connector("conn-b", "agent-os-mcp", "desired"),
            valid_connector("conn-c", "claude-code", "desired"),
        ]
        connectors[0]["registrations"] = [{"surface_id": "agent-os-mcp", "state": "desired", "server_name": "test"}]
        connectors[1]["registrations"] = [{"surface_id": "agent-os-mcp", "state": "desired"}]
        connectors[2]["registrations"] = [{"surface_id": "claude-code", "state": "desired", "server_name": "test"}]

        with patch("agent_os.connectors.load_connector_registry", return_value=valid_registry(connectors)):
            with patch("agent_os.surfaces.surfaces", return_value=mock_surfaces()):
                result = connector_reconcile_plan()

        self.assertIn("native_entry_status_counts", result)
        self.assertEqual(result["native_entry_status_counts"]["not_inspectable"], 1)
        self.assertEqual(result["native_entry_status_counts"]["not_requested"], 1)

    def test_native_entry_status_present_in_toml_file(self) -> None:
        import tempfile

        connector = valid_connector()
        connector["registrations"] = [{"surface_id": "agent-os-mcp", "state": "desired", "server_name": "test-server"}]

        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "config.toml"
            toml_content = """
[mcp_servers.test-server]
command = "python test.py"

[mcp_servers.other-server]
command = "python other.py"
"""
            config_file.write_text(toml_content, encoding="utf-8")

            surfaces_data = [
                {
                    "id": "agent-os-mcp",
                    "name": "Agent OS MCP",
                    "vendor": "Anthropic",
                    "mechanism": "MCP",
                    "summary": "Direct Agent OS MCP integration",
                    "expected_tier": "routed",
                    "invocation": {"kind": "toml", "registrations": [str(config_file)]},
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

            with patch("agent_os.connectors.load_connector_registry", return_value=valid_registry([connector])):
                with patch("agent_os.surfaces.surfaces", return_value=surfaces_data):
                    with patch("agent_os.machine.resolve_user_path", side_effect=lambda p: Path(p)):
                        result = connector_reconcile_plan()

            item = result["items"][0]
            self.assertEqual(item["native_entry_status"], "present")
            self.assertEqual(result["native_entry_status_counts"]["present"], 1)


if __name__ == "__main__":
    unittest.main()
