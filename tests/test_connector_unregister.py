from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os import connectors


@unittest.skipUnless(hasattr(connectors, "unregister_connector"), "unregister_connector not implemented yet")
class ConnectorUnregisterTests(unittest.TestCase):
    def test_unregister_requires_confirmation(self) -> None:
        result = connectors.unregister_connector("does-not-exist")
        self.assertFalse(result.get("removed", False))


if __name__ == "__main__":
    unittest.main()
