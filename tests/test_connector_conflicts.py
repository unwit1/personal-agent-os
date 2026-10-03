from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import patch

from sys import path

path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.connectors import connector_conflicts, REGISTRY_SCHEMA


def valid_connector(
    connector_id: str = "google-drive-work",
    provider_id: str = "google-drive",
    surface_id: str = "agent-os-mcp",
    secret_ref: str | None = ...,  # type: ignore
    server_name: str | None = None,
    state: str = "desired",
) -> dict:
    # Default secret_ref is unique per connector_id to avoid accidental sharing in tests
    if secret_ref is ...:  # type: ignore
        secret_ref = f"keyring:agent-os/{connector_id}"

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


class ConnectorConflictsTests(unittest.TestCase):
    def test_returns_correct_schema_and_structure(self) -> None:
        with patch("agent_os.connectors.load_connector_registry", return_value=valid_registry()):
            result = connector_conflicts()

        self.assertEqual(result["schema"], "personal-agent/connector-conflicts/v1")
        self.assertTrue(result["read_only"])
        self.assertIsNone(result["surface_filter"])
        self.assertIn("count", result)
        self.assertIn("kind_counts", result)
        self.assertIn("conflicts", result)

    def test_empty_registry_returns_empty_conflicts(self) -> None:
        with patch("agent_os.connectors.load_connector_registry", return_value=valid_registry([])):
            result = connector_conflicts()

        self.assertEqual(result["count"], 0)
        self.assertEqual(result["conflicts"], [])
        self.assertEqual(result["kind_counts"], {})

    def test_duplicate_provider_surface_conflict(self) -> None:
        connectors = [
            valid_connector("conn-a", "google-drive", "agent-os-mcp", state="desired"),
            valid_connector("conn-b", "google-drive", "agent-os-mcp", state="desired"),
        ]
        with patch("agent_os.connectors.load_connector_registry", return_value=valid_registry(connectors)):
            result = connector_conflicts()

        self.assertEqual(result["count"], 1)
        conflict = result["conflicts"][0]
        self.assertEqual(conflict["kind"], "duplicate_provider_surface")
        self.assertEqual(conflict["provider_id"], "google-drive")
        self.assertEqual(conflict["surface_id"], "agent-os-mcp")
        self.assertEqual(sorted(conflict["connector_ids"]), ["conn-a", "conn-b"])
        self.assertEqual(result["kind_counts"]["duplicate_provider_surface"], 1)

    def test_duplicate_provider_surface_ignores_disabled_state(self) -> None:
        connectors = [
            valid_connector("conn-a", "google-drive", "agent-os-mcp", state="desired"),
            valid_connector("conn-b", "google-drive", "agent-os-mcp", state="disabled"),
        ]
        with patch("agent_os.connectors.load_connector_registry", return_value=valid_registry(connectors)):
            result = connector_conflicts()

        self.assertEqual(result["count"], 0)
        self.assertEqual(result["conflicts"], [])

    def test_duplicate_provider_surface_ignores_unsupported_state(self) -> None:
        connectors = [
            valid_connector("conn-a", "google-drive", "agent-os-mcp", state="desired"),
            valid_connector("conn-b", "google-drive", "agent-os-mcp", state="unsupported"),
        ]
        with patch("agent_os.connectors.load_connector_registry", return_value=valid_registry(connectors)):
            result = connector_conflicts()

        self.assertEqual(result["count"], 0)

    def test_duplicate_provider_surface_detects_registered_and_error(self) -> None:
        connectors = [
            valid_connector("conn-a", "google-drive", "agent-os-mcp", state="registered"),
            valid_connector("conn-b", "google-drive", "agent-os-mcp", state="error"),
        ]
        with patch("agent_os.connectors.load_connector_registry", return_value=valid_registry(connectors)):
            result = connector_conflicts()

        self.assertEqual(result["count"], 1)
        conflict = result["conflicts"][0]
        self.assertEqual(conflict["kind"], "duplicate_provider_surface")

    def test_native_server_name_collision(self) -> None:
        connectors = [
            valid_connector("conn-a", "google-drive", "agent-os-mcp", server_name="my-server"),
            valid_connector("conn-b", "dropbox", "agent-os-mcp", server_name="my-server"),
        ]
        with patch("agent_os.connectors.load_connector_registry", return_value=valid_registry(connectors)):
            result = connector_conflicts()

        self.assertEqual(result["count"], 1)
        conflict = result["conflicts"][0]
        self.assertEqual(conflict["kind"], "native_server_name_collision")
        self.assertEqual(conflict["surface_id"], "agent-os-mcp")
        self.assertEqual(conflict["server_name"], "my-server")
        self.assertEqual(sorted(conflict["connector_ids"]), ["conn-a", "conn-b"])

    def test_native_server_name_collision_ignores_missing_server_name(self) -> None:
        connectors = [
            valid_connector("conn-a", "google-drive", "agent-os-mcp", server_name="my-server"),
            valid_connector("conn-b", "dropbox", "agent-os-mcp", server_name=None),
        ]
        with patch("agent_os.connectors.load_connector_registry", return_value=valid_registry(connectors)):
            result = connector_conflicts()

        self.assertEqual(result["count"], 0)

    def test_native_server_name_collision_different_surfaces(self) -> None:
        connectors = [
            valid_connector("conn-a", "google-drive", "agent-os-mcp", server_name="my-server"),
            valid_connector("conn-b", "dropbox", "claude-code", server_name="my-server"),
        ]
        with patch("agent_os.connectors.load_connector_registry", return_value=valid_registry(connectors)):
            result = connector_conflicts()

        self.assertEqual(result["count"], 0)

    def test_shared_credential_reference_conflict(self) -> None:
        secret_ref = "env:SHARED_SECRET"
        connectors = [
            valid_connector("conn-a", "google-drive", "agent-os-mcp", secret_ref=secret_ref),
            valid_connector("conn-b", "dropbox", "agent-os-mcp", secret_ref=secret_ref),
        ]
        with patch("agent_os.connectors.load_connector_registry", return_value=valid_registry(connectors)):
            result = connector_conflicts()

        self.assertEqual(result["count"], 1)
        conflict = result["conflicts"][0]
        self.assertEqual(conflict["kind"], "shared_credential_reference")
        self.assertEqual(conflict["backend"], "env")
        self.assertEqual(sorted(conflict["connector_ids"]), ["conn-a", "conn-b"])
        self.assertNotIn("secret_ref", conflict)

    def test_shared_credential_reference_ignores_none(self) -> None:
        connectors = [
            valid_connector("conn-a", "google-drive", "agent-os-mcp", secret_ref=None),
            valid_connector("conn-b", "dropbox", "agent-os-mcp", secret_ref=None),
        ]
        with patch("agent_os.connectors.load_connector_registry", return_value=valid_registry(connectors)):
            result = connector_conflicts()

        self.assertEqual(result["count"], 0)

    def test_shared_credential_reference_different_backends(self) -> None:
        connectors = [
            valid_connector("conn-a", "google-drive", "agent-os-mcp", secret_ref="env:SECRET"),
            valid_connector("conn-b", "dropbox", "agent-os-mcp", secret_ref="keyring:secret"),
        ]
        with patch("agent_os.connectors.load_connector_registry", return_value=valid_registry(connectors)):
            result = connector_conflicts()

        self.assertEqual(result["count"], 0)

    def test_surface_filter_excludes_other_surfaces(self) -> None:
        connectors = [
            valid_connector("conn-a", "google-drive", "agent-os-mcp", state="desired"),
            valid_connector("conn-b", "google-drive", "agent-os-mcp", state="desired"),
            valid_connector("conn-c", "google-drive", "claude-code", state="desired"),
        ]
        with patch("agent_os.connectors.load_connector_registry", return_value=valid_registry(connectors)):
            result = connector_conflicts("agent-os-mcp")

        self.assertEqual(result["surface_filter"], "agent-os-mcp")
        self.assertEqual(result["count"], 1)
        conflict = result["conflicts"][0]
        self.assertEqual(conflict["kind"], "duplicate_provider_surface")
        self.assertEqual(conflict["surface_id"], "agent-os-mcp")

    def test_surface_filter_excludes_connectors_without_registration_on_surface(self) -> None:
        # When surface_id is given, shared credential references only count connectors registered on that surface
        secret_ref = "env:SHARED"
        connectors = [
            valid_connector("conn-a", "google-drive", "agent-os-mcp", secret_ref=secret_ref),
            valid_connector("conn-b", "dropbox", "claude-code", secret_ref=secret_ref),
        ]
        with patch("agent_os.connectors.load_connector_registry", return_value=valid_registry(connectors)):
            result = connector_conflicts("agent-os-mcp")

        self.assertEqual(result["count"], 0)
        self.assertEqual(result["conflicts"], [])

    def test_surface_filter_includes_shared_credential_reference_on_same_surface(self) -> None:
        # When surface_id is given and both connectors are on that surface, shared_credential_reference conflict is reported
        secret_ref = "env:SHARED"
        connectors = [
            valid_connector("conn-a", "google-drive", "agent-os-mcp", secret_ref=secret_ref),
            valid_connector("conn-b", "dropbox", "agent-os-mcp", secret_ref=secret_ref),
        ]
        with patch("agent_os.connectors.load_connector_registry", return_value=valid_registry(connectors)):
            result = connector_conflicts("agent-os-mcp")

        self.assertEqual(result["count"], 1)
        conflict = result["conflicts"][0]
        self.assertEqual(conflict["kind"], "shared_credential_reference")
        self.assertEqual(sorted(conflict["connector_ids"]), ["conn-a", "conn-b"])

    def test_multiple_conflicts_different_kinds(self) -> None:
        connectors = [
            valid_connector("conn-a", "google-drive", "agent-os-mcp", "env:shared", server_name="srv1", state="desired"),
            valid_connector("conn-b", "google-drive", "agent-os-mcp", "env:shared", server_name="srv2", state="desired"),
            valid_connector("conn-c", "dropbox", "agent-os-mcp", None, server_name="srv1"),
        ]
        with patch("agent_os.connectors.load_connector_registry", return_value=valid_registry(connectors)):
            result = connector_conflicts()

        # Should have: duplicate_provider_surface (conn-a, conn-b), shared_credential_reference (conn-a, conn-b), server_name_collision (conn-a, conn-c)
        self.assertEqual(result["count"], 3)
        self.assertEqual(result["kind_counts"]["duplicate_provider_surface"], 1)
        self.assertEqual(result["kind_counts"]["native_server_name_collision"], 1)
        self.assertEqual(result["kind_counts"]["shared_credential_reference"], 1)

    def test_conflicts_sorted_by_kind_surface_id_connector_ids(self) -> None:
        connectors = [
            valid_connector("z-conn", "google-drive", "surf-b", "env:shared1", state="desired"),
            valid_connector("a-conn", "google-drive", "surf-a", "env:shared1", state="desired"),
            valid_connector("b-conn", "google-drive", "surf-a", "env:shared2", state="desired"),
            valid_connector("c-conn", "dropbox", "surf-a", "env:shared2", state="desired"),
        ]
        with patch("agent_os.connectors.load_connector_registry", return_value=valid_registry(connectors)):
            result = connector_conflicts()

        # Expect 3 conflicts: 1 duplicate_provider_surface, 2 shared_credential_reference
        self.assertEqual(result["count"], 3)
        conflicts = result["conflicts"]
        # First should be duplicate_provider_surface on surf-a
        self.assertEqual(conflicts[0]["kind"], "duplicate_provider_surface")
        self.assertEqual(conflicts[0]["surface_id"], "surf-a")
        # Next two should be shared_credential_reference sorted by connector_ids
        self.assertEqual(conflicts[1]["kind"], "shared_credential_reference")
        self.assertEqual(conflicts[2]["kind"], "shared_credential_reference")

    def test_connector_ids_are_sorted_and_unique(self) -> None:
        connectors = [
            valid_connector("z-conn", "google-drive", "agent-os-mcp", state="desired"),
            valid_connector("a-conn", "google-drive", "agent-os-mcp", state="desired"),
            valid_connector("m-conn", "google-drive", "agent-os-mcp", state="desired"),
        ]
        with patch("agent_os.connectors.load_connector_registry", return_value=valid_registry(connectors)):
            result = connector_conflicts()

        self.assertEqual(result["count"], 1)
        conflict = result["conflicts"][0]
        self.assertEqual(conflict["connector_ids"], ["a-conn", "m-conn", "z-conn"])

    def test_no_conflicts_with_single_connector_per_provider_per_surface(self) -> None:
        connectors = [
            valid_connector("conn-a", "google-drive", "agent-os-mcp"),
            valid_connector("conn-b", "dropbox", "agent-os-mcp"),
            valid_connector("conn-c", "google-drive", "claude-code"),
        ]
        with patch("agent_os.connectors.load_connector_registry", return_value=valid_registry(connectors)):
            result = connector_conflicts()

        self.assertEqual(result["count"], 0)
        self.assertEqual(result["conflicts"], [])
        self.assertEqual(result["kind_counts"], {})

    def test_connector_with_multiple_registrations_on_different_surfaces(self) -> None:
        connector = {
            "id": "multi-surf-conn",
            "provider": {"id": "google-drive", "name": "Google Drive"},
            "capabilities": ["files.search"],
            "scopes": ["drive.readonly"],
            "health": {"status": "unknown", "checked_at": None},
            "privacy_domain": "work",
            "registrations": [
                {"surface_id": "agent-os-mcp", "state": "desired"},
                {"surface_id": "claude-code", "state": "desired"},
            ],
            "secret_ref": "env:SHARED",
        }
        connectors = [
            connector,
            valid_connector("conn-b", "dropbox", "agent-os-mcp", "env:SHARED"),
        ]
        with patch("agent_os.connectors.load_connector_registry", return_value=valid_registry(connectors)):
            result = connector_conflicts()

        self.assertEqual(result["count"], 1)
        conflict = result["conflicts"][0]
        self.assertEqual(conflict["kind"], "shared_credential_reference")

    def test_surface_filter_with_multiple_registrations(self) -> None:
        connector = {
            "id": "multi-surf-conn",
            "provider": {"id": "google-drive", "name": "Google Drive"},
            "capabilities": ["files.search"],
            "scopes": ["drive.readonly"],
            "health": {"status": "unknown", "checked_at": None},
            "privacy_domain": "work",
            "registrations": [
                {"surface_id": "agent-os-mcp", "state": "desired"},
                {"surface_id": "claude-code", "state": "desired"},
            ],
            "secret_ref": None,
        }
        connectors = [
            connector,
            valid_connector("conn-a", "google-drive", "agent-os-mcp", state="desired"),
            valid_connector("conn-b", "google-drive", "claude-code", state="desired"),
        ]
        with patch("agent_os.connectors.load_connector_registry", return_value=valid_registry(connectors)):
            result = connector_conflicts("agent-os-mcp")

        self.assertEqual(result["count"], 1)
        conflict = result["conflicts"][0]
        self.assertEqual(conflict["kind"], "duplicate_provider_surface")
        self.assertEqual(conflict["surface_id"], "agent-os-mcp")
        self.assertEqual(sorted(conflict["connector_ids"]), ["conn-a", "multi-surf-conn"])

    def test_server_name_collision_with_all_states(self) -> None:
        connectors = [
            valid_connector("conn-a", "google-drive", "agent-os-mcp", server_name="srv", state="desired"),
            valid_connector("conn-b", "dropbox", "agent-os-mcp", server_name="srv", state="registered"),
            valid_connector("conn-c", "slack", "agent-os-mcp", server_name="srv", state="disabled"),
        ]
        with patch("agent_os.connectors.load_connector_registry", return_value=valid_registry(connectors)):
            result = connector_conflicts()

        self.assertEqual(result["count"], 1)
        conflict = result["conflicts"][0]
        self.assertEqual(conflict["kind"], "native_server_name_collision")
        self.assertEqual(len(conflict["connector_ids"]), 3)

    def test_shared_credential_with_windows_credential_backend(self) -> None:
        secret_ref = "windows-credential:cred-name"
        connectors = [
            valid_connector("conn-a", "google-drive", "agent-os-mcp", secret_ref=secret_ref),
            valid_connector("conn-b", "dropbox", "agent-os-mcp", secret_ref=secret_ref),
        ]
        with patch("agent_os.connectors.load_connector_registry", return_value=valid_registry(connectors)):
            result = connector_conflicts()

        conflict = result["conflicts"][0]
        self.assertEqual(conflict["backend"], "windows-credential")
        self.assertNotIn("secret_ref", conflict)

    def test_shared_credential_with_keyring_backend(self) -> None:
        secret_ref = "keyring:my/secret"
        connectors = [
            valid_connector("conn-a", "google-drive", "agent-os-mcp", secret_ref=secret_ref),
            valid_connector("conn-b", "dropbox", "agent-os-mcp", secret_ref=secret_ref),
        ]
        with patch("agent_os.connectors.load_connector_registry", return_value=valid_registry(connectors)):
            result = connector_conflicts()

        conflict = result["conflicts"][0]
        self.assertEqual(conflict["backend"], "keyring")

    def test_three_connectors_duplicate_provider_surface(self) -> None:
        connectors = [
            valid_connector("conn-a", "google-drive", "agent-os-mcp", state="desired"),
            valid_connector("conn-b", "google-drive", "agent-os-mcp", state="registered"),
            valid_connector("conn-c", "google-drive", "agent-os-mcp", state="error"),
        ]
        with patch("agent_os.connectors.load_connector_registry", return_value=valid_registry(connectors)):
            result = connector_conflicts()

        self.assertEqual(result["count"], 1)
        conflict = result["conflicts"][0]
        self.assertEqual(len(conflict["connector_ids"]), 3)

    def test_single_connector_with_multiple_same_surface_registrations_no_conflict(self) -> None:
        # A single connector with multiple registrations on the same surface should not be a conflict
        connector = {
            "id": "multi-reg-conn",
            "provider": {"id": "google-drive", "name": "Google Drive"},
            "capabilities": ["files.search"],
            "scopes": ["drive.readonly"],
            "health": {"status": "unknown", "checked_at": None},
            "privacy_domain": "work",
            "registrations": [
                {"surface_id": "agent-os-mcp", "state": "desired"},
                {"surface_id": "agent-os-mcp", "state": "desired"},
            ],
            "secret_ref": None,
        }
        with patch("agent_os.connectors.load_connector_registry", return_value=valid_registry([connector])):
            result = connector_conflicts()

        self.assertEqual(result["count"], 0)
        self.assertEqual(result["conflicts"], [])

    def test_single_connector_with_multiple_same_surface_same_server_name_no_conflict(self) -> None:
        # A single connector with multiple registrations on the same surface with the same server_name should not be a conflict
        connector = {
            "id": "multi-reg-conn",
            "provider": {"id": "google-drive", "name": "Google Drive"},
            "capabilities": ["files.search"],
            "scopes": ["drive.readonly"],
            "health": {"status": "unknown", "checked_at": None},
            "privacy_domain": "work",
            "registrations": [
                {"surface_id": "agent-os-mcp", "state": "desired", "server_name": "my-server"},
                {"surface_id": "agent-os-mcp", "state": "desired", "server_name": "my-server"},
            ],
            "secret_ref": None,
        }
        with patch("agent_os.connectors.load_connector_registry", return_value=valid_registry([connector])):
            result = connector_conflicts()

        self.assertEqual(result["count"], 0)
        self.assertEqual(result["conflicts"], [])


if __name__ == "__main__":
    unittest.main()
