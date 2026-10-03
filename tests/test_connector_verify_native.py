from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from agent_os import connectors
from test_connector_events import valid_connector


def connector_with_server_name(
    connector_id: str = "test-connector",
    surface_id: str = "agent-os-mcp",
    state: str = "desired",
    server_name: str = "test-server",
) -> dict:
    return {
        "id": connector_id,
        "provider": {"id": "test-provider", "name": "Test Provider"},
        "capabilities": ["test.capability"],
        "scopes": ["test.scope"],
        "health": {"status": "unknown", "checked_at": None},
        "privacy_domain": "test",
        "registrations": [
            {"surface_id": surface_id, "state": state, "server_name": server_name}
        ],
        "secret_ref": None,
    }


def mock_surface_inspectable() -> dict:
    return {
        "id": "agent-os-mcp",
        "name": "Agent OS MCP",
        "vendor": "Anthropic",
        "mechanism": "MCP",
        "summary": "Direct Agent OS MCP integration",
        "expected_tier": "routed",
        "invocation": {"kind": "json", "registrations": ["~/.config/test.json"]},
        "instruction": {"kind": "none"},
        "capture": {"kind": "none"},
        "connector_capabilities": {
            "inspect_local_config": {"available": True, "reason": None},
            "mutate_local_config": {"available": True, "reason": None},
            "transfer_credentials": {"available": False, "reason": "not supported"},
            "agent_os_bridge": {"available": True, "reason": None},
        },
    }


def mock_surface_not_inspectable() -> dict:
    return {
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
    }


class VerifyNativeRegistrationsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.registry_path = self.tmp / "registry.json"
        self.events_path = self.tmp / "connector-events.jsonl"

        self.registry = {
            "schema": "personal-agent/connector-registry/v1",
            "version": 1,
            "connectors": [],
        }

        for target, value in (
            ("REGISTRY_PATH", self.registry_path),
            ("_CONNECTOR_EVENTS_PATH", self.events_path),
            ("_REGISTRY_LOCK_PATH", self.tmp / "registry.lock"),
        ):
            patcher = patch.object(connectors, target, value)
            patcher.start()
            self.addCleanup(patcher.stop)

        loader = patch.object(
            connectors,
            "load_connector_registry",
            side_effect=lambda: json.loads(json.dumps(self.registry)),
        )
        loader.start()
        self.addCleanup(loader.stop)

    def test_preview_with_no_registrations(self) -> None:
        self.registry["connectors"] = []

        surfaces_patcher = patch(
            "agent_os.surfaces.surfaces",
            return_value=[mock_surface_inspectable()],
        )
        surfaces_patcher.start()
        self.addCleanup(surfaces_patcher.stop)

        result = connectors.verify_native_registrations()
        self.assertEqual(result["written"], False)
        self.assertTrue(result["confirmation_required"])
        self.assertEqual(result["count"], 0)
        self.assertEqual(result["changes"], [])

    def test_preview_not_requested_state(self) -> None:
        connector = valid_connector()
        connector["registrations"] = [{"surface_id": "agent-os-mcp", "state": "desired"}]
        self.registry["connectors"] = [connector]

        surfaces_patcher = patch(
            "agent_os.surfaces.surfaces",
            return_value=[mock_surface_inspectable()],
        )
        surfaces_patcher.start()
        self.addCleanup(surfaces_patcher.stop)

        result = connectors.verify_native_registrations()
        self.assertEqual(result["written"], False)
        self.assertEqual(result["changes"], [])
        self.assertIn("not_requested", result["unchanged_counts"])

    def test_preview_transition_desired_to_registered(self) -> None:
        connector = connector_with_server_name(state="desired", server_name="test-server")
        self.registry["connectors"] = [connector]

        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "config.json"
            config_data = {
                "mcpServers": {
                    "test-server": {"command": "python test.py"},
                }
            }
            config_file.write_text(json.dumps(config_data), encoding="utf-8")

            surfaces_patcher = patch(
                "agent_os.surfaces.surfaces",
                return_value=[
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
                    }
                ],
            )
            surfaces_patcher.start()
            self.addCleanup(surfaces_patcher.stop)

            machine_patcher = patch(
                "agent_os.machine.resolve_user_path",
                side_effect=lambda p: Path(p),
            )
            machine_patcher.start()
            self.addCleanup(machine_patcher.stop)

            result = connectors.verify_native_registrations()
            self.assertEqual(result["written"], False)
            self.assertTrue(result["confirmation_required"])
            self.assertEqual(len(result["changes"]), 1)

            change = result["changes"][0]
            self.assertEqual(change["connector_id"], "test-connector")
            self.assertEqual(change["from_state"], "desired")
            self.assertEqual(change["to_state"], "registered")
            self.assertEqual(change["native_entry_status"], "present")

    def test_preview_transition_registered_to_desired(self) -> None:
        connector = connector_with_server_name(state="registered", server_name="missing-server")
        self.registry["connectors"] = [connector]

        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "config.json"
            config_data = {
                "mcpServers": {
                    "test-server": {"command": "python test.py"},
                }
            }
            config_file.write_text(json.dumps(config_data), encoding="utf-8")

            surfaces_patcher = patch(
                "agent_os.surfaces.surfaces",
                return_value=[
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
                    }
                ],
            )
            surfaces_patcher.start()
            self.addCleanup(surfaces_patcher.stop)

            machine_patcher = patch(
                "agent_os.machine.resolve_user_path",
                side_effect=lambda p: Path(p),
            )
            machine_patcher.start()
            self.addCleanup(machine_patcher.stop)

            result = connectors.verify_native_registrations()
            self.assertEqual(result["written"], False)
            self.assertEqual(len(result["changes"]), 1)

            change = result["changes"][0]
            self.assertEqual(change["connector_id"], "test-connector")
            self.assertEqual(change["from_state"], "registered")
            self.assertEqual(change["to_state"], "desired")
            self.assertEqual(change["native_entry_status"], "absent")

    def test_preview_no_transition_when_disabled(self) -> None:
        connector = connector_with_server_name(state="disabled", server_name="test-server")
        self.registry["connectors"] = [connector]

        surfaces_patcher = patch(
            "agent_os.surfaces.surfaces",
            return_value=[mock_surface_inspectable()],
        )
        surfaces_patcher.start()
        self.addCleanup(surfaces_patcher.stop)

        result = connectors.verify_native_registrations()
        self.assertEqual(result["written"], False)
        self.assertEqual(result["changes"], [])

    def test_preview_no_transition_when_error_state(self) -> None:
        connector = connector_with_server_name(state="error", server_name="test-server")
        self.registry["connectors"] = [connector]

        surfaces_patcher = patch(
            "agent_os.surfaces.surfaces",
            return_value=[mock_surface_inspectable()],
        )
        surfaces_patcher.start()
        self.addCleanup(surfaces_patcher.stop)

        result = connectors.verify_native_registrations()
        self.assertEqual(result["written"], False)
        self.assertEqual(result["changes"], [])

    def test_preview_no_transition_when_unsupported(self) -> None:
        connector = connector_with_server_name(state="unsupported", server_name="test-server")
        self.registry["connectors"] = [connector]

        surfaces_patcher = patch(
            "agent_os.surfaces.surfaces",
            return_value=[mock_surface_inspectable()],
        )
        surfaces_patcher.start()
        self.addCleanup(surfaces_patcher.stop)

        result = connectors.verify_native_registrations()
        self.assertEqual(result["written"], False)
        self.assertEqual(result["changes"], [])

    def test_preview_not_inspectable_surface(self) -> None:
        connector = connector_with_server_name(surface_id="claude-code")
        self.registry["connectors"] = [connector]

        surfaces_patcher = patch(
            "agent_os.surfaces.surfaces",
            return_value=[mock_surface_not_inspectable()],
        )
        surfaces_patcher.start()
        self.addCleanup(surfaces_patcher.stop)

        result = connectors.verify_native_registrations()
        self.assertEqual(result["written"], False)
        self.assertEqual(result["changes"], [])
        self.assertIn("not_inspectable", result["unchanged_counts"])

    def test_preview_unknown_surface(self) -> None:
        connector = connector_with_server_name(surface_id="unknown-surface")
        self.registry["connectors"] = [connector]

        surfaces_patcher = patch(
            "agent_os.surfaces.surfaces",
            return_value=[mock_surface_inspectable()],
        )
        surfaces_patcher.start()
        self.addCleanup(surfaces_patcher.stop)

        result = connectors.verify_native_registrations()
        self.assertEqual(result["written"], False)
        self.assertEqual(result["changes"], [])
        self.assertIn("unknown_surface", result["unchanged_counts"])

    def test_preview_with_connector_id_filter(self) -> None:
        conn1 = connector_with_server_name(
            connector_id="connector-1",
            state="desired",
            server_name="server-1",
        )
        conn2 = connector_with_server_name(
            connector_id="connector-2",
            state="desired",
            server_name="server-2",
        )
        self.registry["connectors"] = [conn1, conn2]

        surfaces_patcher = patch(
            "agent_os.surfaces.surfaces",
            return_value=[mock_surface_inspectable()],
        )
        surfaces_patcher.start()
        self.addCleanup(surfaces_patcher.stop)

        result = connectors.verify_native_registrations("connector-1")
        self.assertEqual(result["connector_id"], "connector-1")
        self.assertEqual(result["written"], False)

    def test_confirm_applies_changes_to_desired_registered(self) -> None:
        connector = connector_with_server_name(state="desired", server_name="test-server")
        self.registry["connectors"] = [connector]

        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "config.json"
            config_data = {
                "mcpServers": {
                    "test-server": {"command": "python test.py"},
                }
            }
            config_file.write_text(json.dumps(config_data), encoding="utf-8")

            surfaces_patcher = patch(
                "agent_os.surfaces.surfaces",
                return_value=[
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
                    }
                ],
            )
            surfaces_patcher.start()
            self.addCleanup(surfaces_patcher.stop)

            machine_patcher = patch(
                "agent_os.machine.resolve_user_path",
                side_effect=lambda p: Path(p),
            )
            machine_patcher.start()
            self.addCleanup(machine_patcher.stop)

            result = connectors.verify_native_registrations(confirm_write=True)
            self.assertEqual(result["written"], True)
            self.assertEqual(result["count"], 1)
            self.assertGreater(result["events_recorded"], 0)

            written = json.loads(self.registry_path.read_text(encoding="utf-8"))
            connector = written["connectors"][0]
            self.assertEqual(connector["registrations"][0]["state"], "registered")

    def test_confirm_idempotent_when_no_changes(self) -> None:
        connector = valid_connector()
        self.registry["connectors"] = [connector]

        surfaces_patcher = patch(
            "agent_os.surfaces.surfaces",
            return_value=[mock_surface_inspectable()],
        )
        surfaces_patcher.start()
        self.addCleanup(surfaces_patcher.stop)

        result = connectors.verify_native_registrations(confirm_write=True)
        self.assertEqual(result["written"], False)
        self.assertTrue(result["idempotent"])
        self.assertEqual(result["count"], 0)

    def test_changes_sorted_by_connector_and_surface_id(self) -> None:
        connectors_list = [
            connector_with_server_name(
                connector_id="z-connector",
                surface_id="agent-os-mcp",
                state="desired",
                server_name="server-z",
            ),
            connector_with_server_name(
                connector_id="a-connector",
                surface_id="agent-os-mcp",
                state="desired",
                server_name="server-a",
            ),
        ]
        self.registry["connectors"] = connectors_list

        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "config.json"
            config_data = {
                "mcpServers": {
                    "server-z": {"command": "python test.py"},
                    "server-a": {"command": "python test.py"},
                }
            }
            config_file.write_text(json.dumps(config_data), encoding="utf-8")

            surfaces_patcher = patch(
                "agent_os.surfaces.surfaces",
                return_value=[
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
                    }
                ],
            )
            surfaces_patcher.start()
            self.addCleanup(surfaces_patcher.stop)

            machine_patcher = patch(
                "agent_os.machine.resolve_user_path",
                side_effect=lambda p: Path(p),
            )
            machine_patcher.start()
            self.addCleanup(machine_patcher.stop)

            result = connectors.verify_native_registrations()
            if result["changes"]:
                for i in range(len(result["changes"]) - 1):
                    current = (
                        result["changes"][i]["connector_id"],
                        result["changes"][i]["surface_id"],
                    )
                    next_item = (
                        result["changes"][i + 1]["connector_id"],
                        result["changes"][i + 1]["surface_id"],
                    )
                    self.assertLess(current, next_item)

    def test_invalid_connector_id_raises_error(self) -> None:
        with self.assertRaises(ValueError):
            connectors.verify_native_registrations("bad id with spaces")

    def test_invalid_confirm_write_type_raises_error(self) -> None:
        with self.assertRaises(ValueError):
            connectors.verify_native_registrations(confirm_write="yes")

    def test_schema_in_all_responses(self) -> None:
        surfaces_patcher = patch(
            "agent_os.surfaces.surfaces",
            return_value=[mock_surface_inspectable()],
        )
        surfaces_patcher.start()
        self.addCleanup(surfaces_patcher.stop)

        result_preview = connectors.verify_native_registrations()
        self.assertEqual(
            result_preview["schema"], "personal-agent/connector-verify-native/v1"
        )

        result_confirm = connectors.verify_native_registrations(confirm_write=True)
        self.assertEqual(
            result_confirm["schema"], "personal-agent/connector-verify-native/v1"
        )


if __name__ == "__main__":
    unittest.main()
