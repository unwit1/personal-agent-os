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


def connector_with_multiple_registrations() -> dict:
    return {
        "id": "multi-reg-connector",
        "provider": {"id": "test-provider", "name": "Test Provider"},
        "capabilities": ["test.capability"],
        "scopes": ["test.scope"],
        "health": {"status": "unknown", "checked_at": None},
        "privacy_domain": "test",
        "registrations": [
            {"surface_id": "agent-os-mcp", "state": "desired"},
            {"surface_id": "other-surface", "state": "registered"},
            {"surface_id": "disabled-surface", "state": "disabled"},
        ],
        "secret_ref": None,
    }


def connector_with_server_name() -> dict:
    c = valid_connector()
    c["id"] = "with-server-name"
    c["registrations"] = [
        {"surface_id": "agent-os-mcp", "state": "desired", "server_name": "test-server"}
    ]
    return c


class SetRegistrationStateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.registry_path = self.tmp / "registry.json"
        self.events_path = self.tmp / "connector-events.jsonl"
        self.surfaces_list = [{"id": "agent-os-mcp"}, {"id": "other-surface"}, {"id": "disabled-surface"}]

        self.registry = {
            "schema": "personal-agent/connector-registry/v1",
            "version": 1,
            "connectors": [
                valid_connector(),
                connector_with_multiple_registrations(),
                connector_with_server_name(),
            ],
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

        surfaces_patcher = patch(
            "agent_os.surfaces.surfaces",
            return_value=self.surfaces_list,
        )
        surfaces_patcher.start()
        self.addCleanup(surfaces_patcher.stop)

    def test_preview_desired_state_from_desired(self) -> None:
        result = connectors.set_registration_state(
            "google-drive-work", "agent-os-mcp", "desired"
        )
        self.assertEqual(result["written"], False)
        self.assertTrue(result["confirmation_required"])
        self.assertEqual(result["connector_id"], "google-drive-work")
        self.assertEqual(result["surface_id"], "agent-os-mcp")
        self.assertTrue(result["found"])
        self.assertEqual(result["current_state"], "desired")
        self.assertEqual(result["requested_state"], "desired")
        self.assertFalse(result["would_change"])

    def test_preview_disabled_state_from_desired(self) -> None:
        result = connectors.set_registration_state(
            "google-drive-work", "agent-os-mcp", "disabled"
        )
        self.assertEqual(result["written"], False)
        self.assertTrue(result["confirmation_required"])
        self.assertEqual(result["connector_id"], "google-drive-work")
        self.assertEqual(result["surface_id"], "agent-os-mcp")
        self.assertTrue(result["found"])
        self.assertEqual(result["current_state"], "desired")
        self.assertEqual(result["requested_state"], "disabled")
        self.assertTrue(result["would_change"])

    def test_preview_desired_state_from_disabled(self) -> None:
        result = connectors.set_registration_state(
            "multi-reg-connector", "disabled-surface", "desired"
        )
        self.assertEqual(result["written"], False)
        self.assertTrue(result["confirmation_required"])
        self.assertTrue(result["found"])
        self.assertEqual(result["current_state"], "disabled")
        self.assertEqual(result["requested_state"], "desired")
        self.assertTrue(result["would_change"])

    def test_preview_desired_state_from_registered_raises_error(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            connectors.set_registration_state(
                "multi-reg-connector", "other-surface", "desired"
            )
        self.assertIn("re-enabled", str(ctx.exception).lower())

    def test_preview_disabled_state_from_registered(self) -> None:
        result = connectors.set_registration_state(
            "multi-reg-connector", "other-surface", "disabled"
        )
        self.assertEqual(result["written"], False)
        self.assertTrue(result["found"])
        self.assertEqual(result["current_state"], "registered")
        self.assertEqual(result["requested_state"], "disabled")
        self.assertTrue(result["would_change"])

    def test_preview_not_found(self) -> None:
        result = connectors.set_registration_state(
            "nonexistent-connector", "agent-os-mcp", "desired"
        )
        self.assertEqual(result["written"], False)
        self.assertFalse(result["found"])
        self.assertIsNone(result["current_state"])
        self.assertEqual(result["requested_state"], "desired")
        self.assertFalse(result["would_change"])

    def test_preview_registration_not_found(self) -> None:
        result = connectors.set_registration_state(
            "google-drive-work", "nonexistent-surface", "desired"
        )
        self.assertEqual(result["written"], False)
        self.assertFalse(result["found"])
        self.assertIsNone(result["current_state"])

    def test_preview_never_includes_secret_ref(self) -> None:
        result = connectors.set_registration_state(
            "google-drive-work", "agent-os-mcp", "disabled"
        )
        result_json = json.dumps(result)
        self.assertNotIn("secret_ref", result_json)
        self.assertNotIn("keyring:", result_json)

    def test_preview_does_not_write_files(self) -> None:
        connectors.set_registration_state(
            "google-drive-work", "agent-os-mcp", "disabled"
        )
        self.assertFalse(self.registry_path.exists())
        self.assertFalse(self.events_path.exists())

    def test_confirm_disable_from_desired(self) -> None:
        result = connectors.set_registration_state(
            "google-drive-work", "agent-os-mcp", "disabled", confirm_write=True
        )
        self.assertEqual(result["written"], True)
        self.assertEqual(result["connector_id"], "google-drive-work")
        self.assertEqual(result["surface_id"], "agent-os-mcp")
        self.assertEqual(result["previous_state"], "desired")
        self.assertEqual(result["state"], "disabled")
        self.assertTrue(result["event_recorded"])

        written = json.loads(self.registry_path.read_text(encoding="utf-8"))
        connector = next(
            (c for c in written["connectors"] if c["id"] == "google-drive-work"),
            None,
        )
        self.assertIsNotNone(connector)
        registration = next(
            (r for r in connector["registrations"] if r["surface_id"] == "agent-os-mcp"),
            None,
        )
        self.assertIsNotNone(registration)
        self.assertEqual(registration["state"], "disabled")

    def test_confirm_enable_from_disabled(self) -> None:
        result = connectors.set_registration_state(
            "multi-reg-connector", "disabled-surface", "desired", confirm_write=True
        )
        self.assertEqual(result["written"], True)
        self.assertEqual(result["previous_state"], "disabled")
        self.assertEqual(result["state"], "desired")

        written = json.loads(self.registry_path.read_text(encoding="utf-8"))
        connector = next(
            (c for c in written["connectors"] if c["id"] == "multi-reg-connector"),
            None,
        )
        registration = next(
            (r for r in connector["registrations"] if r["surface_id"] == "disabled-surface"),
            None,
        )
        self.assertEqual(registration["state"], "desired")

    def test_confirm_idempotent_when_state_unchanged(self) -> None:
        result = connectors.set_registration_state(
            "google-drive-work", "agent-os-mcp", "desired", confirm_write=True
        )
        self.assertEqual(result["written"], False)
        self.assertTrue(result["idempotent"])
        self.assertEqual(result["connector_id"], "google-drive-work")
        self.assertEqual(result["surface_id"], "agent-os-mcp")
        self.assertEqual(result["state"], "desired")

    def test_confirm_not_found(self) -> None:
        result = connectors.set_registration_state(
            "nonexistent-connector", "agent-os-mcp", "desired", confirm_write=True
        )
        self.assertEqual(result["written"], False)
        self.assertTrue(result["not_found"])
        self.assertEqual(result["connector_id"], "nonexistent-connector")
        self.assertEqual(result["surface_id"], "agent-os-mcp")

    def test_confirm_registration_not_found(self) -> None:
        result = connectors.set_registration_state(
            "google-drive-work", "nonexistent-surface", "desired", confirm_write=True
        )
        self.assertEqual(result["written"], False)
        self.assertTrue(result["not_found"])

    def test_confirm_enable_from_registered_raises_error(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            connectors.set_registration_state(
                "multi-reg-connector", "other-surface", "desired", confirm_write=True
            )
        self.assertIn("re-enabled", str(ctx.exception).lower())

    def test_confirm_preserves_server_name(self) -> None:
        result = connectors.set_registration_state(
            "with-server-name", "agent-os-mcp", "disabled", confirm_write=True
        )
        self.assertEqual(result["written"], True)

        written = json.loads(self.registry_path.read_text(encoding="utf-8"))
        connector = next(
            (c for c in written["connectors"] if c["id"] == "with-server-name"),
            None,
        )
        registration = next(
            (r for r in connector["registrations"] if r["surface_id"] == "agent-os-mcp"),
            None,
        )
        self.assertEqual(registration["state"], "disabled")
        self.assertEqual(registration["server_name"], "test-server")

    def test_confirm_records_connector_updated_event(self) -> None:
        connectors.set_registration_state(
            "google-drive-work", "agent-os-mcp", "disabled", confirm_write=True
        )

        events_content = self.events_path.read_text(encoding="utf-8").strip()
        events = [json.loads(line) for line in events_content.split("\n")]

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["event"], "connector.updated")
        self.assertEqual(events[0]["connector_id"], "google-drive-work")

    def test_invalid_connector_id_raises_error(self) -> None:
        with self.assertRaises(ValueError):
            connectors.set_registration_state(
                "bad id with spaces", "agent-os-mcp", "desired"
            )

    def test_invalid_surface_id_raises_error(self) -> None:
        with self.assertRaises(ValueError):
            connectors.set_registration_state(
                "google-drive-work", "bad surface id", "desired"
            )

    def test_invalid_state_raises_error(self) -> None:
        with self.assertRaises(ValueError):
            connectors.set_registration_state(
                "google-drive-work", "agent-os-mcp", "registered"
            )

        with self.assertRaises(ValueError):
            connectors.set_registration_state(
                "google-drive-work", "agent-os-mcp", "error"
            )

        with self.assertRaises(ValueError):
            connectors.set_registration_state(
                "google-drive-work", "agent-os-mcp", "unsupported"
            )

    def test_invalid_confirm_write_type_raises_error(self) -> None:
        with self.assertRaises(ValueError):
            connectors.set_registration_state(
                "google-drive-work", "agent-os-mcp", "desired", confirm_write="yes"
            )

    def test_schema_in_all_responses(self) -> None:
        result_preview = connectors.set_registration_state(
            "google-drive-work", "agent-os-mcp", "desired"
        )
        self.assertEqual(
            result_preview["schema"], "personal-agent/connector-registration-state/v1"
        )

        result_confirm = connectors.set_registration_state(
            "google-drive-work", "agent-os-mcp", "disabled", confirm_write=True
        )
        self.assertEqual(
            result_confirm["schema"], "personal-agent/connector-registration-state/v1"
        )

    def test_confirm_does_not_modify_connector_health_or_other_fields(self) -> None:
        # Add a connector with specific health status
        self.registry["connectors"].append({
            "id": "with-health",
            "provider": {"id": "health-provider", "name": "Health Provider"},
            "capabilities": ["test.capability"],
            "scopes": ["test.scope"],
            "health": {"status": "degraded", "checked_at": "2026-10-03T00:00:00Z"},
            "privacy_domain": "test",
            "registrations": [
                {"surface_id": "agent-os-mcp", "state": "desired"},
            ],
            "secret_ref": None,
        })

        connectors.set_registration_state(
            "with-health", "agent-os-mcp", "disabled", confirm_write=True
        )

        written = json.loads(self.registry_path.read_text(encoding="utf-8"))
        with_health = next(
            (c for c in written["connectors"] if c["id"] == "with-health"),
            None,
        )
        self.assertIsNotNone(with_health)
        self.assertEqual(with_health["health"]["status"], "degraded")
        self.assertEqual(with_health["health"]["checked_at"], "2026-10-03T00:00:00Z")
        self.assertEqual(with_health["registrations"][0]["state"], "disabled")


if __name__ == "__main__":
    unittest.main()
