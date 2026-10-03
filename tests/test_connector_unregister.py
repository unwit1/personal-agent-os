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


class UnregisterConnectorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.registry_path = self.tmp / "registry.json"
        self.events_path = self.tmp / "connector-events.jsonl"
        self.registry = {"schema": "personal-agent/connector-registry/v1", "version": 1,
                         "connectors": [valid_connector()]}
        for target, value in (("REGISTRY_PATH", self.registry_path), ("_CONNECTOR_EVENTS_PATH", self.events_path),
                              ("_REGISTRY_LOCK_PATH", self.tmp / "registry.lock")):
            patcher = patch.object(connectors, target, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        loader = patch.object(connectors, "load_connector_registry", side_effect=lambda: json.loads(json.dumps(self.registry)))
        loader.start()
        self.addCleanup(loader.stop)

    def test_preview_writes_nothing_and_hides_the_secret_ref(self) -> None:
        result = connectors.unregister_connector("google-drive-work")
        self.assertEqual(result["written"], False)
        self.assertTrue(result["confirmation_required"])
        self.assertTrue(result["found"])
        self.assertEqual(result["provider_id"], "google-drive")
        self.assertNotIn("secret_ref", json.dumps(result))
        self.assertNotIn("keyring:", json.dumps(result))
        self.assertFalse(self.registry_path.exists())
        self.assertFalse(self.events_path.exists())

    def test_confirm_removes_the_connector_and_records_the_event(self) -> None:
        result = connectors.unregister_connector("google-drive-work", confirm_write=True)
        self.assertTrue(result["written"])
        self.assertEqual(result["count"], 0)
        self.assertTrue(result["event_recorded"])
        written = json.loads(self.registry_path.read_text(encoding="utf-8"))
        self.assertEqual(written["connectors"], [])
        event = json.loads(self.events_path.read_text(encoding="utf-8").strip())
        self.assertEqual(event["event"], "connector.removed")
        self.assertEqual(event["connector_id"], "google-drive-work")
        self.assertNotIn("secret_ref", event)

    def test_unknown_connector(self) -> None:
        preview = connectors.unregister_connector("absent-one")
        self.assertFalse(preview["found"])
        result = connectors.unregister_connector("absent-one", confirm_write=True)
        self.assertEqual(result, {"written": False, "not_found": True, "connector_id": "absent-one"})
        self.assertFalse(self.registry_path.exists())

    def test_invalid_arguments(self) -> None:
        with self.assertRaises(ValueError):
            connectors.unregister_connector("google-drive-work", confirm_write="yes")
        with self.assertRaises(ValueError):
            connectors.unregister_connector("bad id with spaces")


if __name__ == "__main__":
    unittest.main()
