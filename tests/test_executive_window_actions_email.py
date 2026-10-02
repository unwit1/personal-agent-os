import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

import tempfile
import unittest
from unittest import mock

from agent_os.executive.window import actions_email
from agent_os.executive.window.confirm import window_home


def mail_thread_item(messages=None):
    """Create a mail_thread item with context."""
    if messages is None:
        messages = [
            {
                "id": "msg_123",
                "thread_id": "thr_456",
                "subject": "Test email",
                "sender": "alice@example.com",
                "recipients": "bob@example.com",
                "date": "2026-10-02T12:00:00+00:00",
                "message_id": "msg-id-1@example.com",
                "snippet": "This is a test",
                "attachments": 0,
            }
        ]
    return {
        "id": "mail_thread_1",
        "tab": "personal",
        "kind": "mail_thread",
        "title": "Thread from Alice",
        "why": "Needs reply",
        "source": "mail",
        "context": {"thread": {"thread_id": "thr_456", "count": 1, "subject": "Test email", "messages": messages}},
    }


class EmailReplyDraftTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def test_draft_built_from_thread_context(self):
        """Draft is built from the thread context."""
        item = mail_thread_item()
        with mock.patch.dict("os.environ", {"AGENT_OS_EXECUTIVE_WINDOW_HOME": self.tmp.name}):
            result = actions_email.email_reply_draft(item, {"body": "Thanks!"}, confirm=False)

        self.assertEqual(result["to"], "alice@example.com")
        self.assertEqual(result["subject"], "Re: Test email")
        self.assertEqual(result["in_reply_to"], "msg-id-1@example.com")
        self.assertEqual(result["body"], "Thanks!")

    def test_draft_saved_as_eml(self):
        """Draft is saved as an .eml file."""
        item = mail_thread_item()
        with mock.patch.dict("os.environ", {"AGENT_OS_EXECUTIVE_WINDOW_HOME": self.tmp.name}):
            actions_email.email_reply_draft(item, {"body": "Thanks!"}, confirm=False)
            drafts_dir = Path(self.tmp.name) / "drafts"
            self.assertTrue(drafts_dir.is_dir())
            eml_files = list(drafts_dir.glob("*.eml"))
            self.assertEqual(len(eml_files), 1)
            eml_content = eml_files[0].read_text(encoding="utf-8")
            self.assertIn("To: alice@example.com", eml_content)
            self.assertIn("Subject: Re: Test email", eml_content)

    def test_draft_subject_already_has_re(self):
        """Draft subject doesn't double-add Re: prefix."""
        messages = [
            {
                "id": "msg_123",
                "subject": "Re: Test email",
                "sender": "alice@example.com",
                "message_id": "msg-id-1@example.com",
            }
        ]
        item = mail_thread_item(messages)
        with mock.patch.dict("os.environ", {"AGENT_OS_EXECUTIVE_WINDOW_HOME": self.tmp.name}):
            result = actions_email.email_reply_draft(item, {"body": ""}, confirm=False)

        self.assertEqual(result["subject"], "Re: Test email")

    def test_draft_no_body_is_optional(self):
        """Draft works with no body parameter."""
        item = mail_thread_item()
        with mock.patch.dict("os.environ", {"AGENT_OS_EXECUTIVE_WINDOW_HOME": self.tmp.name}):
            result = actions_email.email_reply_draft(item, {}, confirm=False)

        self.assertEqual(result["body"], "")

    def test_draft_uses_latest_message_in_thread(self):
        """Draft uses the latest message in a multi-message thread."""
        messages = [
            {
                "id": "msg_123",
                "subject": "Original subject",
                "sender": "alice@example.com",
                "message_id": "msg-id-1@example.com",
            },
            {
                "id": "msg_456",
                "subject": "Another message",
                "sender": "bob@example.com",
                "message_id": "msg-id-2@example.com",
            },
        ]
        item = mail_thread_item(messages)
        with mock.patch.dict("os.environ", {"AGENT_OS_EXECUTIVE_WINDOW_HOME": self.tmp.name}):
            result = actions_email.email_reply_draft(item, {"body": "My reply"}, confirm=False)

        self.assertEqual(result["to"], "bob@example.com")
        self.assertEqual(result["subject"], "Re: Another message")
        self.assertEqual(result["in_reply_to"], "msg-id-2@example.com")


class EmailSendTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.transport_calls = []

        def fake_transport(to, subject, body, in_reply_to):
            self.transport_calls.append({"to": to, "subject": subject, "body": body, "in_reply_to": in_reply_to})

        self.fake_transport = fake_transport

    def test_send_preview_never_calls_transport(self):
        """Send preview (confirm=False) never calls the transport."""
        item = {"id": "item_1", "context": {}}
        params = {"to": "alice@example.com", "subject": "Test", "body": "Hello"}

        with mock.patch.object(actions_email, "TRANSPORT", self.fake_transport):
            result = actions_email.email_send(item, params, confirm=False)

        self.assertEqual(result, {"to": "alice@example.com", "subject": "Test", "body": "Hello"})
        self.assertEqual(self.transport_calls, [])

    def test_send_with_transport_calls_it_once(self):
        """Send with confirm=True calls the transport once."""
        item = {"id": "item_1", "context": {}}
        params = {
            "to": "alice@example.com",
            "subject": "Test",
            "body": "Hello",
            "in_reply_to": "msg-123@example.com",
        }

        with mock.patch.object(actions_email, "TRANSPORT", self.fake_transport):
            result = actions_email.email_send(item, params, confirm=True)

        self.assertEqual(result, {"sent": True})
        self.assertEqual(len(self.transport_calls), 1)
        call = self.transport_calls[0]
        self.assertEqual(call["to"], "alice@example.com")
        self.assertEqual(call["subject"], "Test")
        self.assertEqual(call["body"], "Hello")
        self.assertEqual(call["in_reply_to"], "msg-123@example.com")

    def test_send_no_transport_saves_draft(self):
        """Send with no transport saves a draft and returns draft_path."""
        item = {"id": "item_1", "context": {}}
        params = {"to": "alice@example.com", "subject": "Test", "body": "Hello"}

        with mock.patch.dict("os.environ", {"AGENT_OS_EXECUTIVE_WINDOW_HOME": self.tmp.name}):
            with mock.patch.object(actions_email, "TRANSPORT", None):
                result = actions_email.email_send(item, params, confirm=True)

        self.assertFalse(result["sent"])
        self.assertIn("no outbound mail transport configured", result["reason"])
        draft_path = Path(result["draft_path"])
        self.assertTrue(draft_path.exists())
        eml_content = draft_path.read_text(encoding="utf-8")
        self.assertIn("To: alice@example.com", eml_content)
        self.assertIn("Subject: Test", eml_content)

    def test_send_no_transport_nothing_sent(self):
        """Send with no transport doesn't call any transport."""
        item = {"id": "item_1", "context": {}}
        params = {"to": "alice@example.com", "subject": "Test", "body": "Hello"}

        with mock.patch.dict("os.environ", {"AGENT_OS_EXECUTIVE_WINDOW_HOME": self.tmp.name}):
            with mock.patch.object(actions_email, "TRANSPORT", None):
                actions_email.email_send(item, params, confirm=True)

        self.assertEqual(self.transport_calls, [])

    def test_send_multiple_drafts_have_unique_names(self):
        """Multiple drafts get unique filenames."""
        item = {"id": "item_1", "context": {}}

        with mock.patch.dict("os.environ", {"AGENT_OS_EXECUTIVE_WINDOW_HOME": self.tmp.name}):
            with mock.patch.object(actions_email, "TRANSPORT", None):
                result1 = actions_email.email_send(item, {"to": "a@x.com", "subject": "1", "body": "1"}, confirm=True)
                result2 = actions_email.email_send(item, {"to": "b@x.com", "subject": "2", "body": "2"}, confirm=True)

        path1 = Path(result1["draft_path"])
        path2 = Path(result2["draft_path"])
        self.assertNotEqual(path1, path2)
        self.assertTrue(path1.exists())
        self.assertTrue(path2.exists())

    def test_send_invalid_empty_to_raises(self):
        """Send with empty 'to' raises ValueError and never calls transport."""
        item = {"id": "item_1", "context": {}}
        params = {"to": "", "subject": "Test", "body": "Hello"}

        with mock.patch.object(actions_email, "TRANSPORT", self.fake_transport):
            with self.assertRaises(ValueError) as cm:
                actions_email.email_send(item, params, confirm=True)

        self.assertIn("'to' address is required", str(cm.exception))
        self.assertEqual(self.transport_calls, [])

    def test_send_invalid_to_with_newline_raises(self):
        """Send with newline in 'to' raises ValueError."""
        item = {"id": "item_1", "context": {}}
        params = {"to": "alice@example.com\nBcc: attacker@example.com", "subject": "Test", "body": "Hello"}

        with mock.patch.object(actions_email, "TRANSPORT", self.fake_transport):
            with self.assertRaises(ValueError) as cm:
                actions_email.email_send(item, params, confirm=True)

        self.assertIn("cannot contain newlines", str(cm.exception))
        self.assertEqual(self.transport_calls, [])

    def test_send_invalid_subject_with_newline_raises(self):
        """Send with newline in 'subject' raises ValueError."""
        item = {"id": "item_1", "context": {}}
        params = {"to": "alice@example.com", "subject": "Test\nBcc: attacker@example.com", "body": "Hello"}

        with mock.patch.object(actions_email, "TRANSPORT", self.fake_transport):
            with self.assertRaises(ValueError) as cm:
                actions_email.email_send(item, params, confirm=True)

        self.assertIn("cannot contain newlines", str(cm.exception))
        self.assertEqual(self.transport_calls, [])


class RegisterTests(unittest.TestCase):
    def test_actions_registered(self):
        """Both email actions are registered."""
        from agent_os.executive.window.registry import Registry

        registry = Registry()
        actions_email.register(registry)

        action_ids = [a["id"] for a in registry.actions()]
        self.assertIn("email.reply_draft", action_ids)
        self.assertIn("email.send", action_ids)

    def test_reply_draft_not_consequential(self):
        """email.reply_draft is not consequential."""
        from agent_os.executive.window.registry import Registry

        registry = Registry()
        actions_email.register(registry)

        action = next(a for a in registry.actions() if a["id"] == "email.reply_draft")
        self.assertFalse(action["consequential"])

    def test_send_consequential(self):
        """email.send is consequential."""
        from agent_os.executive.window.registry import Registry

        registry = Registry()
        actions_email.register(registry)

        action = next(a for a in registry.actions() if a["id"] == "email.send")
        self.assertTrue(action["consequential"])

    def test_reply_draft_applies_to_mail_thread(self):
        """email.reply_draft applies to mail_thread items."""
        from agent_os.executive.window.registry import Registry

        registry = Registry()
        actions_email.register(registry)

        action = next(a for a in registry.actions() if a["id"] == "email.reply_draft")
        self.assertEqual(action["applies_to"], ["mail_thread"])

    def test_send_applies_to_all(self):
        """email.send applies to all item kinds."""
        from agent_os.executive.window.registry import Registry

        registry = Registry()
        actions_email.register(registry)

        action = next(a for a in registry.actions() if a["id"] == "email.send")
        self.assertEqual(action["applies_to"], "*")


if __name__ == "__main__":
    unittest.main()
