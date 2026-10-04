from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.surfaces import _connector_subscriber_summary, health


class ConnectorSubscriberSummaryTests(unittest.TestCase):
    def test_available_true_with_empty_subscribers(self) -> None:
        subscriber_status = {
            "schema": "personal-agent/connector-subscriber-status/v1",
            "read_only": True,
            "latest_seq": 0,
            "cursor_store_malformed": 0,
            "count": 0,
            "counts": {
                "caught_up": 0,
                "behind": 0,
                "cursor_ahead": 0,
            },
            "subscribers": [],
        }

        with patch("agent_os.surfaces.connector_subscriber_status", return_value=subscriber_status):
            result = _connector_subscriber_summary()

        self.assertTrue(result["available"])
        self.assertEqual(result["schema"], "personal-agent/connector-subscriber-status/v1")
        self.assertEqual(result["latest_seq"], 0)
        self.assertEqual(result["count"], 0)
        self.assertEqual(result["subscribers"], [])
        self.assertTrue(result["read_only"])

    def test_available_true_with_multiple_subscribers(self) -> None:
        subscriber_status = {
            "schema": "personal-agent/connector-subscriber-status/v1",
            "read_only": True,
            "latest_seq": 100,
            "cursor_store_malformed": 0,
            "count": 3,
            "counts": {
                "caught_up": 2,
                "behind": 1,
                "cursor_ahead": 0,
            },
            "subscribers": [
                {
                    "subscriber_id": "subscriber-1",
                    "after_seq": 100,
                    "lag": 0,
                    "caught_up": True,
                    "cursor_ahead": False,
                },
                {
                    "subscriber_id": "subscriber-2",
                    "after_seq": 95,
                    "lag": 5,
                    "caught_up": False,
                    "cursor_ahead": False,
                },
                {
                    "subscriber_id": "subscriber-3",
                    "after_seq": 100,
                    "lag": 0,
                    "caught_up": True,
                    "cursor_ahead": False,
                },
            ],
        }

        with patch("agent_os.surfaces.connector_subscriber_status", return_value=subscriber_status):
            result = _connector_subscriber_summary()

        self.assertTrue(result["available"])
        self.assertEqual(result["latest_seq"], 100)
        self.assertEqual(result["count"], 3)
        self.assertEqual(result["counts"]["caught_up"], 2)
        self.assertEqual(result["counts"]["behind"], 1)
        self.assertEqual(len(result["subscribers"]), 3)

    def test_available_false_on_oserror(self) -> None:
        with patch("agent_os.surfaces.connector_subscriber_status", side_effect=OSError("cursor store missing")):
            result = _connector_subscriber_summary()

        self.assertFalse(result["available"])
        self.assertEqual(result["schema"], "personal-agent/connector-subscriber-status/v1")
        self.assertIn("reason", result)
        self.assertTrue(result["read_only"])
        dumped = json.dumps(result)
        self.assertNotIn("cursor store missing", dumped)

    def test_available_false_on_valueerror(self) -> None:
        with patch("agent_os.surfaces.connector_subscriber_status", side_effect=ValueError("invalid cursor format")):
            result = _connector_subscriber_summary()

        self.assertFalse(result["available"])
        self.assertEqual(result["schema"], "personal-agent/connector-subscriber-status/v1")
        self.assertIn("reason", result)
        self.assertEqual(result["reason"], "connector subscriber cursors unreadable")
        dumped = json.dumps(result)
        self.assertNotIn("invalid cursor format", dumped)

    def test_summary_has_available_field(self) -> None:
        subscriber_status = {
            "schema": "personal-agent/connector-subscriber-status/v1",
            "read_only": True,
            "latest_seq": 0,
            "cursor_store_malformed": 0,
            "count": 0,
            "counts": {
                "caught_up": 0,
                "behind": 0,
                "cursor_ahead": 0,
            },
            "subscribers": [],
        }

        with patch("agent_os.surfaces.connector_subscriber_status", return_value=subscriber_status):
            result = _connector_subscriber_summary()

        self.assertIn("available", result)
        self.assertTrue(result["available"])

    def test_health_includes_connector_subscribers_summary(self) -> None:
        subscriber_status = {
            "schema": "personal-agent/connector-subscriber-status/v1",
            "read_only": True,
            "latest_seq": 50,
            "cursor_store_malformed": 0,
            "count": 2,
            "counts": {
                "caught_up": 1,
                "behind": 1,
                "cursor_ahead": 0,
            },
            "subscribers": [
                {
                    "subscriber_id": "subscriber-1",
                    "after_seq": 50,
                    "lag": 0,
                    "caught_up": True,
                    "cursor_ahead": False,
                },
                {
                    "subscriber_id": "subscriber-2",
                    "after_seq": 45,
                    "lag": 5,
                    "caught_up": False,
                    "cursor_ahead": False,
                },
            ],
        }

        with patch("agent_os.surfaces.connector_subscriber_status", return_value=subscriber_status):
            result = health()

        self.assertIn("connector_providers", result)
        self.assertIn("subscribers", result["connector_providers"])
        subscribers = result["connector_providers"]["subscribers"]
        self.assertTrue(subscribers["available"])
        self.assertEqual(subscribers["latest_seq"], 50)
        self.assertEqual(subscribers["count"], 2)

    def test_health_reports_unavailable_subscribers(self) -> None:
        with patch("agent_os.surfaces.connector_subscriber_status", side_effect=OSError("file not found")):
            result = health()

        self.assertIn("connector_providers", result)
        self.assertIn("subscribers", result["connector_providers"])
        subscribers = result["connector_providers"]["subscribers"]
        self.assertFalse(subscribers["available"])
        self.assertEqual(subscribers["schema"], "personal-agent/connector-subscriber-status/v1")


if __name__ == "__main__":
    unittest.main()
