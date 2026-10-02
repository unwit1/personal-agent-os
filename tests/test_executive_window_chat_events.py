import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

import tempfile
import unittest
from unittest import mock

from agent_os import rtec_applicants
from agent_os.executive.gateway import SyntheticDashboardGateway
from agent_os.executive.window import actions_executive, actions_openings, builtin
from agent_os.executive.window.server import Api


class FakeBridge:
    def __init__(self):
        self.calls = []

    def send(self, conversation_id, text):
        self.calls.append(text)
        return {"reply": "model reply"}


class TestChatOpeningEvents(unittest.TestCase):
    def setUp(self):
        self.gateway = SyntheticDashboardGateway(openings={"Alpha": {"open_count": 2}})
        for module, name, value in (
            (actions_executive, "GATEWAY_FACTORY", lambda: self.gateway),
            (actions_openings, "GATEWAY", self.gateway),
        ):
            patcher = mock.patch.object(module, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        audit = mock.patch.object(rtec_applicants, "_audit_access", lambda *a, **k: None)
        audit.start()
        self.addCleanup(audit.stop)
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.bridge = FakeBridge()
        self.api = Api(builtin.default_registry(), self.bridge, Path(tmp.name),
                       transport=object(), gateway_factory=lambda: self.gateway)

    def test_chat_event_makes_pending_preview_without_model(self):
        result = self.api.post("/api/chat", {"text": "We closed the opening in Alpha County."})
        self.assertEqual(result["message"], "Confirm to update openings")
        self.assertEqual(self.bridge.calls, [])
        self.assertEqual(len(result["previews"]), 1)
        preview = result["previews"][0]
        self.assertEqual(preview["action_id"], "openings.event")
        self.assertEqual(preview["item_id"], "county:Alpha")
        self.assertEqual(self.gateway.openings["Alpha"]["open_count"], 2)

    def test_confirm_applies_and_returns_county_group(self):
        result = self.api.post("/api/chat", {"text": "we closed the opening in Alpha"})
        token = result["previews"][0]["confirm_token"]
        done = self.api.post("/api/confirm", {"confirm_token": token})
        self.assertEqual(done["status"], "done")
        self.assertEqual(self.gateway.openings["Alpha"]["open_count"], 0)
        self.assertTrue(done["result"]["applied"]["applied"])
        self.assertIn("county_group", done["result"])
        self.assertEqual(self.api.post("/api/pending", {})["previews"], [])

    def test_unknown_county_reports_error_and_no_pending(self):
        result = self.api.post("/api/chat", {"text": "we closed the opening in Nowhere"})
        self.assertIn("Could not preview", result["message"])
        self.assertEqual(result["previews"], [])

    def test_ordinary_text_goes_to_model(self):
        result = self.api.post("/api/chat", {"text": "what is on my plate?"})
        self.assertEqual(result["message"], "model reply")
        self.assertEqual(self.bridge.calls, ["what is on my plate?"])


if __name__ == "__main__":
    unittest.main()
