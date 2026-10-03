from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


class ConnectorUnregisterTests(unittest.TestCase):
    """Placeholder tests for connector unregister functionality."""

    def test_placeholder(self) -> None:
        """Placeholder test to satisfy test discovery."""
        pass


if __name__ == "__main__":
    unittest.main()
