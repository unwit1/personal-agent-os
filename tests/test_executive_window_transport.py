import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import smtplib

from agent_os.executive.window import transport
from agent_os.executive.window.transport import FakeTransport, SendResult, SmtpImapTransport
from agent_os.mail.accounts import Account


class FakeSMTP:
    def __init__(self, fail=None):
        self.fail, self.sent, self.logins, self.quit_called = fail, [], [], False

    def login(self, user, secret):
        self.logins.append(user)
        if self.fail == "auth":
            raise smtplib.SMTPAuthenticationError(535, b"secret server text")

    def send_message(self, message):
        if self.fail == "refused":
            raise smtplib.SMTPRecipientsRefused({"x@y": (550, b"no")})
        self.sent.append(message)

    def quit(self):
        self.quit_called = True


class FakeIMAP:
    def __init__(self, fail=False):
        self.fail, self.appended, self.out = fail, [], False

    def login(self, user, secret):
        pass

    def list(self):
        return "OK", [b'(\\HasNoChildren \\Sent) "/" "Sent Items"']

    def append(self, folder, flags, date, data):
        if self.fail:
            raise OSError("boom")
        self.appended.append((folder, flags, data))
        return "OK", [b"done"]

    def logout(self):
        self.out = True


def account(**kw):
    values = dict(id="work-earthlink", provider="earthlink", email="me@earthlink.net", enabled=True)
    values.update(kw)
    return Account(**values)


def make(smtp=None, imap=None, accounts=None, secret="pw"):
    smtp = smtp or FakeSMTP()
    imap = imap or FakeIMAP()
    calls = []

    def smtp_factory(*args):
        calls.append(args)
        return smtp

    t = SmtpImapTransport(accounts=accounts if accounts is not None else [account()],
                          secret_lookup=lambda a: secret, smtp_factory=smtp_factory,
                          imap_factory=lambda *a: imap)
    return t, smtp, imap, calls


class FakeTransportTests(unittest.TestCase):
    def test_records_and_ids(self):
        t = FakeTransport()
        r = t.send("a@example.com", "S", "B", from_account="x")
        self.assertTrue(r.sent)
        self.assertEqual(r.message_id, "<fake-1@example.invalid>")
        self.assertEqual(t.calls[0]["from_account"], "x")

    def test_fail_with(self):
        r = FakeTransport(fail_with="boom").send("a@b.c", "S", "B")
        self.assertEqual((r.sent, r.error), (False, "NOT SENT: boom"))

    def test_default_transport_and_factory(self):
        self.assertIsInstance(transport.default_transport(), SmtpImapTransport)
        fake = FakeTransport()
        transport.TRANSPORT_FACTORY = lambda: fake
        try:
            self.assertIs(transport.default_transport(), fake)
        finally:
            transport.TRANSPORT_FACTORY = None


class SmtpImapTests(unittest.TestCase):
    def test_success_with_sent_copy(self):
        t, smtp, imap, calls = make()
        r = t.send("a@example.com", "Hi", "Body", in_reply_to="<x@y>")
        self.assertTrue(r.sent)
        self.assertIsNone(r.error)
        self.assertIsNone(r.warning)
        self.assertEqual(calls[0][:3], ("smtpauth.earthlink.net", 587, "starttls"))
        self.assertEqual(smtp.sent[0]["Message-ID"], r.message_id)
        self.assertEqual(smtp.sent[0]["In-Reply-To"], "<x@y>")
        self.assertEqual(imap.appended[0][0], '"Sent Items"')
        self.assertTrue(smtp.quit_called and imap.out)

    def test_hosted_domain_uses_hosted_smtp(self):
        t, _, _, calls = make(accounts=[account(email="me@example.org")])
        self.assertTrue(t.send("a@b.com", "S", "B").sent)
        self.assertEqual(calls[0][0], "smtpauth.hosting.earthlink.net")

    def test_sent_copy_failure_warns(self):
        t, *_ = make(imap=FakeIMAP(fail=True))
        r = t.send("a@b.com", "S", "B")
        self.assertTrue(r.sent)
        self.assertEqual(r.warning, transport.SENT_WARNING)

    def test_failures(self):
        cases = [
            (dict(smtp=FakeSMTP("auth")), "SMTP authentication failed"),
            (dict(smtp=FakeSMTP("refused")), "recipient refused"),
            (dict(secret=None), "missing credential for account work-earthlink"),
        ]
        for kw, text in cases:
            r = make(**kw)[0].send("a@b.com", "S", "B")
            self.assertFalse(r.sent)
            self.assertEqual(r.error, f"NOT SENT: {text}")
            self.assertNotIn("secret server text", r.error)

    def test_connection_error_and_unexpected_exception(self):
        def boom(*a):
            raise OSError("no route")

        t = SmtpImapTransport(accounts=[account()], secret_lookup=lambda a: "pw", smtp_factory=boom)
        self.assertEqual(t.send("a@b.com", "S", "B").error, "NOT SENT: SMTP connection failed")

        def bad(a):
            raise ValueError("x")

        t = SmtpImapTransport(accounts=[account()], secret_lookup=lambda a: "pw", smtp_factory=bad)
        t._default_account = bad
        self.assertEqual(t.send("a@b.com", "S", "B").error, "NOT SENT: ValueError")

    def test_validation_and_unknown_account(self):
        t, smtp, _, calls = make()
        for args in (("", "S", "B"), ("a@b.com", "", "B"), ("a@b.com", "S", " "), ("a@b.com\nBcc: x", "S", "B")):
            r = t.send(*args)
            self.assertTrue(r.error.startswith("NOT SENT: "))
        self.assertEqual(t.send("a@b.com", "S", "B", from_account="nope").error, "NOT SENT: unknown mail account nope")
        self.assertEqual(calls, [])

    def test_from_accounts_default(self):
        t, *_ = make(accounts=[account(id="home", provider="icloud", email="me@icloud.com"), account()])
        listed = {a["account_id"]: a["default"] for a in t.from_accounts()}
        self.assertEqual(listed, {"home": False, "work-earthlink": True})


if __name__ == "__main__":
    unittest.main()
