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


def connector_with_multiple_surfaces() -> dict:
    return {
        "id": "multi-surface-connector",
        "provider": {"id": "test-provider", "name": "Test Provider"},
        "capabilities": ["test.capability"],
        "scopes": ["test.scope"],
        "health": {"status": "unknown", "checked_at": None},
        "privacy_domain": "test",
        "registrations": [
            {"surface_id": "agent-os-mcp", "state": "desired"},
            {"surface_id": "stale-surface-1", "state": "registered"},
            {"surface_id": "stale-surface-2", "state": "error"},
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


class PruneStalRegistrationsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.registry_path = self.tmp / "registry.json"
        self.events_path = self.tmp / "connector-events.jsonl"
        self.surfaces_list = [{"id": "agent-os-mcp"}, {"id": "existing-surface"}]

        self.registry = {
            "schema": "personal-agent/connector-registry/v1",
            "version": 1,
            "connectors": [
                valid_connector(),
                connector_with_multiple_surfaces(),
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

    def test_preview_identifies_stale_registrations(self) -> None:
        result = connectors.prune_stale_registrations()
        self.assertEqual(result["written"], False)
        self.assertTrue(result["confirmation_required"])
        self.assertEqual(result["connector_id"], None)
        self.assertEqual(len(result["stale"]), 2)

        stale_ids = {(s["connector_id"], s["surface_id"]) for s in result["stale"]}
        self.assertIn(("multi-surface-connector", "stale-surface-1"), stale_ids)
        self.assertIn(("multi-surface-connector", "stale-surface-2"), stale_ids)

    def test_preview_with_connector_id_filter(self) -> None:
        result = connectors.prune_stale_registrations("multi-surface-connector")
        self.assertEqual(result["written"], False)
        self.assertTrue(result["confirmation_required"])
        self.assertEqual(result["connector_id"], "multi-surface-connector")
        self.assertEqual(len(result["stale"]), 2)

        for item in result["stale"]:
            self.assertEqual(item["connector_id"], "multi-surface-connector")

    def test_preview_with_no_stale_registrations(self) -> None:
        # Modify registry to have no stale registrations
        self.registry["connectors"][1]["registrations"] = [
            {"surface_id": "agent-os-mcp", "state": "desired"}
        ]

        result = connectors.prune_stale_registrations()
        self.assertEqual(result["written"], False)
        self.assertEqual(len(result["stale"]), 0)
        self.assertEqual(result["count"], 0)

    def test_preview_never_includes_secret_ref_or_server_name(self) -> None:
        result = connectors.prune_stale_registrations()
        result_json = json.dumps(result)
        self.assertNotIn("secret_ref", result_json)
        self.assertNotIn("server_name", result_json)
        self.assertNotIn("keyring:", result_json)
        self.assertNotIn("scopes", result_json)
        self.assertNotIn("privacy_domain", result_json)

    def test_preview_does_not_write_files(self) -> None:
        connectors.prune_stale_registrations()
        self.assertFalse(self.registry_path.exists())
        self.assertFalse(self.events_path.exists())

    def test_stale_list_is_sorted_by_connector_id_then_surface_id(self) -> None:
        # Add more connectors with multiple stale registrations
        self.registry["connectors"].append({
            "id": "another-connector",
            "provider": {"id": "provider-2", "name": "Provider 2"},
            "capabilities": ["other.capability"],
            "scopes": ["other.scope"],
            "health": {"status": "unknown", "checked_at": None},
            "privacy_domain": "test",
            "registrations": [
                {"surface_id": "stale-b", "state": "desired"},
                {"surface_id": "stale-a", "state": "desired"},
            ],
            "secret_ref": None,
        })

        result = connectors.prune_stale_registrations()
        stale = result["stale"]

        # Verify sorted order
        for i in range(len(stale) - 1):
            current = (stale[i]["connector_id"], stale[i]["surface_id"])
            next_item = (stale[i + 1]["connector_id"], stale[i + 1]["surface_id"])
            self.assertLess(current, next_item)

    def test_confirm_removes_stale_registrations(self) -> None:
        result = connectors.prune_stale_registrations(confirm_write=True)
        self.assertEqual(result["written"], True)
        self.assertEqual(result["count"], 2)
        self.assertEqual(len(result["removed"]), 2)
        self.assertGreater(result["events_recorded"], 0)

        written = json.loads(self.registry_path.read_text(encoding="utf-8"))
        multi_surface = next(
            (c for c in written["connectors"] if c["id"] == "multi-surface-connector"),
            None,
        )
        self.assertIsNotNone(multi_surface)
        self.assertEqual(len(multi_surface["registrations"]), 1)
        self.assertEqual(multi_surface["registrations"][0]["surface_id"], "agent-os-mcp")

    def test_confirm_keeps_connector_even_if_all_registrations_are_removed(self) -> None:
        # Make all registrations stale for multi-surface-connector
        self.registry["connectors"][1]["registrations"] = [
            {"surface_id": "stale-only", "state": "desired"}
        ]

        result = connectors.prune_stale_registrations(confirm_write=True)
        self.assertEqual(result["count"], 1)

        written = json.loads(self.registry_path.read_text(encoding="utf-8"))
        multi_surface = next(
            (c for c in written["connectors"] if c["id"] == "multi-surface-connector"),
            None,
        )
        self.assertIsNotNone(multi_surface)
        self.assertEqual(len(multi_surface["registrations"]), 0)

    def test_confirm_with_connector_id_filter_removes_only_matching_stale(self) -> None:
        result = connectors.prune_stale_registrations(
            "multi-surface-connector", confirm_write=True
        )
        self.assertEqual(result["count"], 2)
        self.assertEqual(result["connector_id"], "multi-surface-connector")

        written = json.loads(self.registry_path.read_text(encoding="utf-8"))
        for connector in written["connectors"]:
            if connector["id"] == "multi-surface-connector":
                self.assertEqual(len(connector["registrations"]), 1)

    def test_confirm_records_connector_updated_events_for_affected_connectors(self) -> None:
        connectors.prune_stale_registrations(confirm_write=True)

        events_content = self.events_path.read_text(encoding="utf-8").strip()
        events = [json.loads(line) for line in events_content.split("\n")]

        updated_events = [e for e in events if e["event"] == "connector.updated"]
        self.assertGreater(len(updated_events), 0)
        self.assertEqual(updated_events[0]["connector_id"], "multi-surface-connector")
        self.assertNotIn("secret_ref", json.dumps(updated_events))
        self.assertNotIn("scopes", json.dumps(updated_events))

    def test_confirm_idempotent_when_no_stale_registrations(self) -> None:
        # First remove all stale registrations
        result1 = connectors.prune_stale_registrations(confirm_write=True)
        self.assertGreater(result1["count"], 0)

        # Reload the registry with updated connectors
        written = json.loads(self.registry_path.read_text(encoding="utf-8"))
        self.registry = written

        # Try again
        result2 = connectors.prune_stale_registrations(confirm_write=True)
        self.assertEqual(result2["written"], False)
        self.assertTrue(result2["idempotent"])
        self.assertEqual(len(result2["removed"]), 0)
        self.assertEqual(result2["count"], 0)

    def test_confirm_does_not_modify_connector_health_or_other_fields(self) -> None:
        # Add a connector with a specific health status
        self.registry["connectors"].append({
            "id": "with-health",
            "provider": {"id": "health-provider", "name": "Health Provider"},
            "capabilities": ["test.capability"],
            "scopes": ["test.scope"],
            "health": {"status": "degraded", "checked_at": "2026-10-03T00:00:00Z"},
            "privacy_domain": "test",
            "registrations": [
                {"surface_id": "stale-surf", "state": "error"},
            ],
            "secret_ref": None,
        })

        connectors.prune_stale_registrations(confirm_write=True)

        written = json.loads(self.registry_path.read_text(encoding="utf-8"))
        with_health = next(
            (c for c in written["connectors"] if c["id"] == "with-health"),
            None,
        )
        self.assertIsNotNone(with_health)
        self.assertEqual(with_health["health"]["status"], "degraded")
        self.assertEqual(with_health["health"]["checked_at"], "2026-10-03T00:00:00Z")

    def test_invalid_connector_id_raises_error(self) -> None:
        with self.assertRaises(ValueError):
            connectors.prune_stale_registrations("bad id with spaces")

    def test_invalid_confirm_write_type_raises_error(self) -> None:
        with self.assertRaises(ValueError):
            connectors.prune_stale_registrations(confirm_write="yes")

    def test_schema_in_all_responses(self) -> None:
        result_preview = connectors.prune_stale_registrations()
        self.assertEqual(
            result_preview["schema"], "personal-agent/connector-prune-stale/v1"
        )

        result_confirm = connectors.prune_stale_registrations(confirm_write=True)
        self.assertEqual(
            result_confirm["schema"], "personal-agent/connector-prune-stale/v1"
        )


if __name__ == "__main__":
    unittest.main()
