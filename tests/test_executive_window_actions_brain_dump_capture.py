from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.executive.window import actions_brain_dump as mod
from agent_os.executive.window.brain_dump_store import BrainDumpStore
from agent_os.executive.window.confirm import PendingStore
from agent_os.executive.window.registry import Registry


class BrainDumpCaptureActionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.store = BrainDumpStore(self.tmp.name)
        mod.STORE_FACTORY = lambda: self.store
        mod.KNOWN_PROJECTS = lambda: []
        self.addCleanup(setattr, mod, "STORE_FACTORY", None)
        self.addCleanup(setattr, mod, "KNOWN_PROJECTS", None)
        self.reg = Registry()
        mod.register(self.reg)
        self.pending = PendingStore(self.tmp.name)

    def test_preview_then_confirm_writes_records_only_on_confirm(self):
        result = self.reg.invoke(
            "brain_dump.capture",
            {"id": "brain-dump-capture", "kind": "brain_dump_capture"},
            {"text": "Call the plumber tomorrow."},
            self.pending,
        )
        self.assertEqual(result["status"], "needs_confirmation")
        self.assertTrue(result["confirm_token"])
        self.assertTrue(result["preview"]["records"])
        self.assertEqual(self.store.records(), [])

        done = self.reg.confirm(result["confirm_token"], self.pending)
        self.assertTrue(done["added"])
        self.assertTrue(self.store.records())

    def test_text_must_be_non_empty(self):
        with self.assertRaisesRegex(ValueError, "text is required"):
            mod._capture({}, {"text": "  "}, confirm=False)

    def test_tab_must_be_supported(self):
        with self.assertRaisesRegex(ValueError, "tab must be work or personal"):
            mod._capture({}, {"text": "Do a thing", "tab": "bogus"}, confirm=False)


if __name__ == "__main__":
    unittest.main()
