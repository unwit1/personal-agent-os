from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os import mcp_server
from agent_os.executive.window import actions_brain_dump, actions_knowledge_gaps
from agent_os.executive.window.brain_dump_store import BrainDumpStore
from agent_os.executive.window.gap_store import GapStore
from agent_os.executive.window.builtin import default_registry
from agent_os.executive.window.confirm import PendingStore


class CaptureMCPWriteTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        home = Path(self.temp.name)
        env = patch.dict(os.environ, {"AGENT_OS_EXECUTIVE_WINDOW_HOME": str(home)})
        env.start()
        self.addCleanup(env.stop)
        old_brain_factory = actions_brain_dump.STORE_FACTORY
        old_projects = actions_brain_dump.KNOWN_PROJECTS
        old_gap_factory = actions_knowledge_gaps.STORE_FACTORY
        actions_brain_dump.STORE_FACTORY = lambda: BrainDumpStore(home)
        actions_brain_dump.KNOWN_PROJECTS = lambda: []
        actions_knowledge_gaps.STORE_FACTORY = lambda: GapStore(home)
        self.addCleanup(setattr, actions_brain_dump, "STORE_FACTORY", old_brain_factory)
        self.addCleanup(setattr, actions_brain_dump, "KNOWN_PROJECTS", old_projects)
        self.addCleanup(setattr, actions_knowledge_gaps, "STORE_FACTORY", old_gap_factory)

    def test_tools_are_registered_and_listed(self):
        names = {"executive_capture.brain_dump_capture", "executive_capture.gaps_enqueue"}
        available = mcp_server.methods()
        response = mcp_server._handle_mcp({"id": 1, "method": "tools/list"}, available)
        listed = {tool["name"] for tool in response["result"]["tools"]}
        self.assertTrue(names.issubset(available))
        self.assertTrue(names.issubset(listed))

    def test_brain_dump_capture_requires_confirm_to_write(self):
        store = BrainDumpStore(self.temp.name)
        result = mcp_server._capture_brain_dump_capture("Call the plumber tomorrow.")
        self.assertEqual(result["status"], "needs_confirmation")
        self.assertEqual(store.records(), [])
        pending = PendingStore(self.temp.name).list()
        self.assertEqual(len(pending), 1)
        self.assertEqual(pending[0]["action_id"], "brain_dump.capture")
        default_registry().confirm(result["confirm_token"], PendingStore(self.temp.name))
        self.assertTrue(store.records())

    def test_gaps_enqueue_requires_confirm_to_write(self):
        store = GapStore(self.temp.name)
        gaps = [{"id": "g1", "question": "Which room?", "topic": "home", "utility": 1, "urgency": 1}]
        result = mcp_server._capture_gaps_enqueue(gaps)
        self.assertEqual(result["status"], "needs_confirmation")
        self.assertEqual(store.gaps(), [])
        pending = PendingStore(self.temp.name).list()
        self.assertEqual(len(pending), 1)
        self.assertEqual(pending[0]["action_id"], "knowledge_gap.enqueue")
        default_registry().confirm(result["confirm_token"], PendingStore(self.temp.name))
        self.assertEqual([gap["id"] for gap in store.gaps()], ["g1"])

    def test_empty_brain_dump_capture_raises(self):
        with self.assertRaises(ValueError):
            mcp_server._capture_brain_dump_capture("")


if __name__ == "__main__":
    unittest.main()
