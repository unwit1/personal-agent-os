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
        self.assertIsNone(item["reason"])

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
        expected_keys = {"connector_id", "surface_id", "state", "action", "reason", "credential_reference_configured"}
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


if __name__ == "__main__":
    unittest.main()
