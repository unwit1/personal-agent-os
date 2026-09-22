import sys
import unittest
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os import changes, improvements, ingestion, telemetry, workflows  # noqa: E402
from agent_os.timestamps import utc_now_iso  # noqa: E402


class TimestampTests(unittest.TestCase):
    def test_shared_formatter_returns_timezone_aware_iso_timestamp(self) -> None:
        value = utc_now_iso()
        parsed = datetime.fromisoformat(value)
        self.assertIsNotNone(parsed.tzinfo)
        self.assertEqual(parsed.utcoffset().total_seconds(), 0)

    def test_existing_state_writers_keep_the_same_timestamp_contract(self) -> None:
        for helper in (
            ingestion._now,
            changes._now,
            improvements._now,
            workflows._now,
            telemetry._utc_now,
        ):
            with self.subTest(helper=helper.__module__):
                value = helper()
                parsed = datetime.fromisoformat(value)
                self.assertIsNotNone(parsed.tzinfo)
                self.assertEqual(parsed.utcoffset().total_seconds(), 0)


if __name__ == "__main__":
    unittest.main()
