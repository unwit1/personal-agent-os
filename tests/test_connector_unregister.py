from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os import connectors  # noqa: E402


class ConnectorEventsReaderGuardTests(unittest.TestCase):
    def test_rejects_invalid_limit(self) -> None:
        for bad in (0, 501, True, "5"):
            with self.assertRaises(ValueError):
                connectors.connector_events(limit=bad)  # type: ignore[arg-type]

    def test_missing_log_returns_no_events(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "connector-events.jsonl"
            with mock.patch.object(connectors, "_CONNECTOR_EVENTS_PATH", missing):
                result = connectors.connector_events()
        self.assertEqual(result["schema"], "personal-agent/connector-events/v1")


if __name__ == "__main__":
    unittest.main()
