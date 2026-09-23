"""Multi-account, read-only mail: iCloud + EarthLink + archives.

Synthetic messages and a fake IMAP server only; no real mailbox, network or
credential is used.
"""

from __future__ import annotations

import contextlib
import imaplib
import io
import json
import os
import re
import shutil
import sqlite3
import sys
import tempfile
import unittest
from email.message import EmailMessage
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os import mail  # noqa: E402
from agent_os.mail import accounts as accounts_lib  # noqa: E402
from agent_os.mail import config, imap, store as store_lib  # noqa: E402
from agent_os.mail import engine as sync_lib  # noqa: E402

LEAK_PROBE = "THIS_IS_A_TEST_SECRET_DO_NOT_LEAK_12345"


def rfc822(subject: str, body: str, *, sender: str = "Pat <pat@example.test>", to: str = "you@example.test", message_id: str | None = None,
           date: str = "Tue, 01 Sep 2026 10:00:00 +0000", in_reply_to: str | None = None, references: str | None = None,
           attachment: tuple[str, str, bytes] | None = None) -> bytes:
    msg = EmailMessage()
    msg["From"], msg["To"], msg["Subject"], msg["Date"] = sender, to, subject, date
    if message_id:
        msg["Message-ID"] = message_id
    if in_reply_to:
        msg["In-Reply-To"] = in_reply_to
    if references:
        msg["References"] = references
    msg.set_content(body)
    if attachment:
        name, mime, data = attachment
        main, sub = mime.split("/")
        msg.add_attachment(data, maintype=main, subtype=sub, filename=name)
    return bytes(msg)


class FakeKeyring:
    def __init__(self) -> None:
        self.data: dict[tuple[str, str], str] = {}

    def get_password(self, service, key):
        return self.data.get((service, key))

    def set_password(self, service, key, value):
        self.data[(service, key)] = value

    def delete_password(self, service, key):
        self.data.pop((service, key))


class FakeIMAPServer:
    """Enough of imaplib.IMAP4_SSL for the adapter, with call recording."""

    def __init__(self, password: str = LEAK_PROBE, capabilities: tuple[str, ...] = ("IMAP4rev1",)) -> None:
        self.password = password
        self.capabilities = capabilities
        self.boxes: dict[str, dict] = {}
        self.calls: list[tuple] = []
        self.connections: list[tuple] = []
        self.fail_fetch_after: int | None = None
        self._fetches = 0
        self.selected = None

    def add(self, mailbox: str, uid: int, raw: bytes, flags: str = "", uidvalidity: str = "100", modseq: int = 1) -> None:
        box = self.boxes.setdefault(mailbox, {"uidvalidity": uidvalidity, "messages": {}, "modseq": 0})
        box["messages"][uid] = {"raw": raw, "flags": flags, "modseq": modseq, "date": f"01-Sep-2026 10:{uid % 60:02d}:00 +0000"}
        box["modseq"] = max(box["modseq"], modseq)

    def factory(self, host, port, ssl_context=None, timeout=None):
        self.connections.append((host, port))
        return FakeClient(self)


class FakeClient:
    def __init__(self, server: FakeIMAPServer) -> None:
        self.server = server
        self._responses: dict[str, list] = {}

    def login(self, user, password):
        self.server.calls.append(("login", user))
        if password != self.server.password:
            raise imaplib.IMAP4.error(f"[AUTHENTICATIONFAILED] Invalid credentials for {user} with {password}")
        return "OK", [b"logged in"]

    def capability(self):
        return "OK", [" ".join(self.server.capabilities).encode()]

    def list(self):
        return "OK", [f'(\\HasNoChildren) "/" "{name}"'.encode() for name in self.server.boxes]

    def select(self, mailbox, readonly=False):
        self.server.calls.append(("select", mailbox, readonly))
        name = mailbox.strip('"')
        box = self.server.boxes.get(name)
        if box is None:
            return "NO", [b"no such mailbox"]
        self.server.selected = name
        uids = sorted(box["messages"])
        self._responses = {"UIDVALIDITY": [box["uidvalidity"].encode()], "UIDNEXT": [str((uids[-1] if uids else 0) + 1).encode()]}
        if "CONDSTORE" in self.server.capabilities:
            self._responses["HIGHESTMODSEQ"] = [str(box["modseq"]).encode()]
        return "OK", [str(len(uids)).encode()]

    def response(self, name):
        return name, self._responses.get(name, [None])

    def uid(self, command, *args):
        self.server.calls.append(("uid", command.lower(), *[str(arg) for arg in args]))
        box = self.server.boxes[self.server.selected]
        if command.lower() == "search":
            return "OK", [" ".join(str(uid) for uid in sorted(box["messages"])).encode()]
        if command.lower() == "fetch":
            self.server._fetches += 1
            if self.server.fail_fetch_after is not None and "PEEK" in args[1] and self.server._fetches > self.server.fail_fetch_after:
                raise ConnectionResetError("connection lost")
            wanted = _expand(args[0], box["messages"])
            since = re.search(r"CHANGEDSINCE (\d+)", args[1])
            data = []
            for uid in wanted:
                message = box["messages"][uid]
                if since and message["modseq"] <= int(since.group(1)):
                    continue
                meta = f'{uid} (UID {uid} RFC822.SIZE {len(message["raw"])} INTERNALDATE "{message["date"]}" FLAGS ({message["flags"]})'
                if "BODY.PEEK[]" in args[1]:
                    data.append((f"{meta} BODY[] {{{len(message['raw'])}}}".encode(), message["raw"]))
                    data.append(b")")
                else:
                    data.append((meta + ")").encode())
            return "OK", data
        raise AssertionError(f"unexpected UID {command}")

    def logout(self):
        return "BYE", []


def _expand(uid_set: str, messages: dict) -> list[int]:
    wanted = []
    for part in uid_set.split(","):
        if ":" in part:
            start, end = part.split(":")
            wanted += [uid for uid in messages if int(start) <= uid <= (max(messages) if end == "*" else int(end))]
        elif int(part) in messages:
            wanted.append(int(part))
    return sorted(set(wanted))


class MailFixture(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="agent-os-mail-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        local = self.tmp / "mail"
        for name, value in {"LOCAL_DIR": local, "LEGACY_CONFIG": local / "icloud.json", "ACCOUNTS_FILE": local / "accounts.json",
                            "DB": local / "index.sqlite3", "LEDGER_DIR": local / "ledgers", "LOG_FILE": local / "sync-log.jsonl"}.items():
            patcher = mock.patch.object(config, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        patcher = mock.patch.object(mail, "DB", local / "index.sqlite3")
        patcher.start()
        self.addCleanup(patcher.stop)
        self.keyring = FakeKeyring()
        patcher = mock.patch.object(accounts_lib, "_keyring", lambda: self.keyring)
        patcher.start()
        self.addCleanup(patcher.stop)
        env = mock.patch.dict(os.environ, {}, clear=False)
        env.start()
        self.addCleanup(env.stop)
        for key in [key for key in os.environ if key.startswith("AGENT_OS_MAIL_SECRET_") or key == "ICLOUD_APP_PASSWORD"]:
            del os.environ[key]
        self.db = local / "index.sqlite3"

    def account(self, provider: str, account_id: str, email: str, folders: list[str] | None = None) -> accounts_lib.Account:
        account = accounts_lib.add_account(provider, account_id, email, folders=folders)
        accounts_lib.set_secret(account_id, LEAK_PROBE)
        return account

    def sync(self, account, server: FakeIMAPServer, **kwargs):
        return sync_lib.sync_account(account, store_path=self.db, ledger_dir=config.LEDGER_DIR, connect_factory=server.factory, **kwargs)

    def sources(self) -> list[sqlite3.Row]:
        with store_lib.Store(self.db) as store:
            return store.conn.execute("SELECT * FROM mail_sources ORDER BY account_id, uid").fetchall()


# ---------------------------------------------------------------------------
# Providers, accounts, secrets
# ---------------------------------------------------------------------------


class AccountTests(MailFixture):
    def test_provider_defaults_and_login_names(self) -> None:
        icloud = self.account("icloud", "personal-icloud", "me@icloud.com")
        earthlink = self.account("earthlink", "work-earthlink", "me@earthlink.net")
        self.assertEqual((icloud.host, icloud.port), ("imap.mail.me.com", 993))
        self.assertEqual((earthlink.host, earthlink.port), ("imap.earthlink.net", 993))
        self.assertEqual(earthlink.login_name, "me@earthlink.net", "EarthLink logs in with the full address")
        server = FakeIMAPServer()
        for account, host in ((icloud, "imap.mail.me.com"), (earthlink, "imap.earthlink.net")):
            result = sync_lib.health(account, connect_factory=server.factory)
            self.assertTrue(result["ok"])
            self.assertEqual(server.connections[-1], (host, 993))
        self.assertEqual([call[1] for call in server.calls if call[0] == "login"], ["me@icloud.com", "me@earthlink.net"])

    def test_auth_failure_is_sanitized(self) -> None:
        account = self.account("earthlink", "work-earthlink", "me@earthlink.net")
        server = FakeIMAPServer(password="something-else")
        result = sync_lib.health(account, connect_factory=server.factory)
        self.assertEqual(result, {"account_id": "work-earthlink", "provider": "earthlink", "ok": False, "error": "auth_failed"})
        self.assertNotIn(LEAK_PROBE, json.dumps(result))
        self.assertEqual(self.sync(account, server)["error"], "auth_failed")

    def test_account_specific_secret_lookup(self) -> None:
        one = accounts_lib.add_account("icloud", "one", "a@icloud.com")
        two = accounts_lib.add_account("earthlink", "two", "b@earthlink.net")
        os.environ[accounts_lib.env_name("one")] = "env-secret"
        self.keyring.set_password(accounts_lib.SECRET_SERVICE, "two", "keyring-secret")
        self.assertEqual(accounts_lib.env_name("work-earthlink"), "AGENT_OS_MAIL_SECRET_WORK_EARTHLINK")
        self.assertEqual(accounts_lib.get_secret(one), "env-secret")
        self.assertEqual(accounts_lib.get_secret(two), "keyring-secret")
        self.assertEqual(accounts_lib.credential_status(two), (True, "keyring"))
        three = accounts_lib.add_account("icloud", "three", "c@icloud.com")
        self.assertEqual(accounts_lib.credential_status(three), (False, None))
        with self.assertRaises(accounts_lib.AccountError):
            accounts_lib.get_secret(three)

    def test_accounts_validation(self) -> None:
        with self.assertRaises(accounts_lib.AccountError):
            accounts_lib.add_account("gmail", "x1", "x@gmail.com")
        with self.assertRaises(accounts_lib.AccountError):
            accounts_lib.add_account("icloud", "Bad Id!", "x@icloud.com")
        accounts_lib.add_account("icloud", "dup", "x@icloud.com")
        with self.assertRaises(accounts_lib.AccountError):
            accounts_lib.add_account("earthlink", "dup", "y@earthlink.net")
        with self.assertRaises(accounts_lib.AccountError):
            accounts_lib.update_account("dup", read_only=False)
        self.assertTrue(accounts_lib.get_account("dup").read_only)

    def test_legacy_icloud_config_becomes_an_account(self) -> None:
        config.LEGACY_CONFIG.parent.mkdir(parents=True, exist_ok=True)
        config.LEGACY_CONFIG.write_text(json.dumps({"email": "old@icloud.com"}), encoding="utf-8")
        self.keyring.set_password(accounts_lib.LEGACY_SECRET_SERVICE, "old@icloud.com", "legacy-secret")
        [account] = accounts_lib.load_accounts()
        self.assertEqual((account.id, account.provider, account.email, account.legacy), ("icloud", "icloud", "old@icloud.com", True))
        self.assertEqual(accounts_lib.credential_status(account), (True, "legacy-keyring"))
        self.assertTrue(config.LEGACY_CONFIG.exists(), "the old file is kept (reversible)")
        os.environ["ICLOUD_APP_PASSWORD"] = "legacy-env"
        self.assertEqual(accounts_lib.get_secret(account), "legacy-env")

    def test_secret_never_leaks(self) -> None:
        account = self.account("earthlink", "work-earthlink", "me@earthlink.net")
        os.environ[accounts_lib.env_name("other")] = LEAK_PROBE
        server = FakeIMAPServer()
        server.add("INBOX", 1, rfc822("Hello", "body", message_id="<a@x>"))
        sync_result = self.sync(account, server)
        bad = FakeIMAPServer(password="nope")
        failed = sync_lib.health(account, connect_factory=bad.factory)
        from agent_os.mcp_server import methods

        tools = methods()
        with mock.patch.object(mail, "DB", self.db):
            outputs = [mail.list_accounts(), mail.status(), mail.account_status("work-earthlink"), sync_result, failed, tools["mail.accounts"](), tools["mail.sync_status"]()]
        for path in (config.ACCOUNTS_FILE, config.LOG_FILE, config.LOCAL_DIR / "account-state.json"):
            outputs.append(path.read_text(encoding="utf-8"))
        for output in outputs:
            self.assertNotIn(LEAK_PROBE, json.dumps(output, default=str))
        with self.assertRaises(imap.MailError) as caught:
            client = imap.ReadOnlyIMAP(bad.factory("h", 1))
            client.login("me@earthlink.net", LEAK_PROBE)
        self.assertNotIn(LEAK_PROBE, str(caught.exception))


# ---------------------------------------------------------------------------
# Read-only enforcement
# ---------------------------------------------------------------------------


class ReadOnlyTests(MailFixture):
    def test_mailboxes_are_examined_and_nothing_can_write(self) -> None:
        account = self.account("icloud", "personal-icloud", "me@icloud.com")
        server = FakeIMAPServer()
        server.add("INBOX", 1, rfc822("Hi", "there", message_id="<b@x>"))
        self.sync(account, server)
        selects = [call for call in server.calls if call[0] == "select"]
        self.assertTrue(selects and all(call[2] is True for call in selects), selects)
        fetches = [call for call in server.calls if call[:2] == ("uid", "fetch")]
        self.assertTrue(any("BODY.PEEK[]" in call[3] for call in fetches))
        self.assertFalse(any("BODY[]" in call[3] and "PEEK" not in call[3] for call in fetches))
        self.assertEqual({call[1] for call in server.calls if call[0] == "uid"}, {"search", "fetch"})
        client = imap.ReadOnlyIMAP(server.factory("h", 1))
        for attempt in (lambda: client.store("1", "+FLAGS", "\\Seen"), lambda: client.copy("1", "Trash"), lambda: client.expunge(),
                        lambda: client.append("INBOX", None, None, b""), lambda: client.delete("INBOX"), lambda: client.uid("STORE", "1", "+FLAGS", "(\\Deleted)"),
                        lambda: client.uid("MOVE", "1", "Trash"), lambda: client.uid("fetch", "1", "(RFC822)"), lambda: client.select("INBOX")):
            with self.assertRaises(imap.ReadOnlyViolation):
                attempt()
        self.assertFalse(hasattr(mail, "send"))


# ---------------------------------------------------------------------------
# Identity, sync, resume
# ---------------------------------------------------------------------------


class IdentityAndSyncTests(MailFixture):
    def test_same_mailbox_and_uid_in_two_accounts_do_not_collide(self) -> None:
        work = self.account("earthlink", "work-earthlink", "me@earthlink.net")
        home = self.account("icloud", "personal-icloud", "me@icloud.com")
        work_server, home_server = FakeIMAPServer(), FakeIMAPServer()
        work_server.add("INBOX", 1, rfc822("Payroll schedule", "work mail", message_id="<w1@x>"))
        home_server.add("INBOX", 1, rfc822("Dinner", "home mail", message_id="<h1@x>"))
        self.sync(work, work_server)
        self.sync(home, home_server)
        rows = self.sources()
        self.assertEqual(len(rows), 2)
        self.assertEqual({(row["account_id"], row["provider"], row["uid"]) for row in rows}, {("work-earthlink", "earthlink", "1"), ("personal-icloud", "icloud", "1")})
        self.assertEqual(len({row["message_id"] for row in rows}), 2)

    def test_same_account_name_different_provider_is_distinct(self) -> None:
        self.assertNotEqual(store_lib.live_source_id("icloud", "a", "INBOX", "1", "1"), store_lib.live_source_id("earthlink", "a", "INBOX", "1", "1"))
        self.assertNotEqual(store_lib.live_source_id("icloud", "a", "INBOX", "1", "1"), store_lib.live_source_id("icloud", "a", "INBOX", "2", "1"))
        self.assertEqual(store_lib.live_source_id("icloud", "a", "INBOX", "1", "1"), store_lib.live_source_id("icloud", "a", "INBOX", "1", "1"))

    def test_resync_is_idempotent_and_fetches_no_bodies(self) -> None:
        account = self.account("earthlink", "work-earthlink", "me@earthlink.net")
        server = FakeIMAPServer()
        for uid in range(1, 6):
            server.add("INBOX", uid, rfc822(f"Message {uid}", f"body {uid}", message_id=f"<m{uid}@x>"))
        first = self.sync(account, server)
        self.assertEqual((first["indexed_new"], first["fetched"], first["status"]), (5, 5, "ok"))
        second = self.sync(account, server)
        self.assertEqual((second["indexed_new"], second["fetched"], second["status"]), (0, 0, "ok"))
        server.add("INBOX", 6, rfc822("Message 6", "new", message_id="<m6@x>"))
        third = self.sync(account, server)
        self.assertEqual((third["indexed_new"], third["fetched"]), (1, 1))
        self.assertEqual(len(self.sources()), 6)

    def test_limit_takes_newest_first_then_backfills(self) -> None:
        account = self.account("icloud", "personal-icloud", "me@icloud.com")
        server = FakeIMAPServer()
        for uid in range(1, 11):
            server.add("INBOX", uid, rfc822(f"M{uid}", f"b{uid}", message_id=f"<n{uid}@x>"))
        first = self.sync(account, server, limit=3)
        self.assertEqual(sorted(int(row["uid"]) for row in self.sources()), [8, 9, 10])
        self.assertEqual(first["mailboxes"][0]["older_not_indexed"], 7)
        self.sync(account, server, limit=3, backfill=4)
        self.assertEqual(sorted(int(row["uid"]) for row in self.sources()), [4, 5, 6, 7, 8, 9, 10])
        final = self.sync(account, server, limit=3, backfill=10)
        self.assertEqual(len(self.sources()), 10)
        self.assertEqual(final["mailboxes"][0]["older_not_indexed"], 0)

    def test_uidvalidity_change_retires_old_namespace_and_rescans(self) -> None:
        account = self.account("earthlink", "work-earthlink", "me@earthlink.net")
        server = FakeIMAPServer()
        raw = rfc822("Stable", "same content", message_id="<s1@x>")
        server.add("INBOX", 1, raw, uidvalidity="100")
        self.sync(account, server)
        server.boxes["INBOX"] = {"uidvalidity": "200", "messages": {}, "modseq": 0}
        server.add("INBOX", 7, raw, uidvalidity="200")
        result = self.sync(account, server)
        box = result["mailboxes"][0]
        self.assertEqual(box["uidvalidity_changed"]["from"], "100")
        rows = self.sources()
        self.assertEqual({(row["uidvalidity"], row["uid"], row["state"]) for row in rows}, {("100", "1", "stale_uidvalidity"), ("200", "7", "present")})
        self.assertEqual(len({row["message_id"] for row in rows}), 1, "same email: one logical message, both observations kept")

    def test_changed_content_under_same_identity_is_reprocessed(self) -> None:
        account = self.account("earthlink", "work-earthlink", "me@earthlink.net")
        server = FakeIMAPServer()
        server.add("INBOX", 1, rfc822("Original", "before", message_id="<c1@x>"))
        self.sync(account, server)
        server.add("INBOX", 1, rfc822("Original", "after, with more text", message_id="<c1@x>"))  # a non-compliant server
        result = self.sync(account, server)
        self.assertEqual(result["reprocessed"], 1)
        with mock.patch.object(mail, "DB", self.db):
            self.assertEqual(len(mail.search("after")), 1)
            self.assertEqual(mail.search("before"), [])
        self.assertEqual(len(self.sources()), 1)

    def test_interrupted_sync_resumes_without_loss_or_duplicates(self) -> None:
        account = self.account("icloud", "personal-icloud", "me@icloud.com")
        server = FakeIMAPServer()
        for uid in range(1, 8):
            server.add("INBOX", uid, rfc822(f"R{uid}", f"r{uid}", message_id=f"<r{uid}@x>"))
        server.fail_fetch_after = 2  # two body batches succeed, then the connection drops
        first = self.sync(account, server, batch=2)
        self.assertEqual(first["status"], "partial")
        self.assertEqual(first["mailboxes"][0]["error"], "connection_failed")
        self.assertEqual(len(self.sources()), 4, "finished batches are durable")
        with store_lib.Store(self.db) as store:
            self.assertIsNone(store.mailbox_state("personal-icloud", "INBOX")["last_completed"], "never reported complete after an error")
        server.fail_fetch_after = None
        second = self.sync(account, server, batch=2)
        self.assertEqual(second["status"], "ok")
        rows = self.sources()
        self.assertEqual(sorted(int(row["uid"]) for row in rows), list(range(1, 8)))
        self.assertEqual(second["indexed_new"], 3)

    def test_ledger_replay_after_commit_is_idempotent(self) -> None:
        account = self.account("icloud", "personal-icloud", "me@icloud.com")
        server = FakeIMAPServer()
        server.add("INBOX", 1, rfc822("One", "one", message_id="<l1@x>"))
        self.sync(account, server)
        for ledger in config.LEDGER_DIR.rglob("*.json"):
            ledger.unlink()  # as if the process died after the DB commit, before the ledger save
        with store_lib.Store(self.db) as store:
            store.conn.execute("UPDATE mail_mailboxes SET high_water_uid=NULL, backfill_low_uid=NULL")
            store.conn.execute("DELETE FROM mail_sources")  # force a refetch through the pipeline
            store.conn.commit()
        result = self.sync(account, server)
        self.assertEqual(result["errors"], 0)
        self.assertEqual(len(self.sources()), 1)

    def test_condstore_flags_and_missing_messages(self) -> None:
        account = self.account("earthlink", "work-earthlink", "me@earthlink.net")
        server = FakeIMAPServer(capabilities=("IMAP4rev1", "CONDSTORE"))
        server.add("INBOX", 1, rfc822("F1", "f1", message_id="<f1@x>"), modseq=5)
        server.add("INBOX", 2, rfc822("F2", "f2", message_id="<f2@x>"), modseq=6)
        self.sync(account, server)
        server.boxes["INBOX"]["messages"][1].update(flags="\\Seen", modseq=9)
        server.boxes["INBOX"]["modseq"] = 9
        del server.boxes["INBOX"]["messages"][2]
        result = self.sync(account, server)
        box = result["mailboxes"][0]
        self.assertEqual(box["capability_mode"], "condstore")
        self.assertEqual(box["flags_updated"], 1)
        self.assertEqual(box["missing"], 1)
        states = {row["uid"]: (row["state"], row["flags"]) for row in self.sources()}
        self.assertEqual(states, {"1": ("present", "\\Seen"), "2": ("missing", "")})
        self.assertTrue(any("CHANGEDSINCE 6" in " ".join(call) for call in server.calls if call[:2] == ("uid", "fetch")))

    def test_all_folders_with_exclusions(self) -> None:
        account = self.account("icloud", "personal-icloud", "me@icloud.com", folders=["*"])
        accounts_lib.update_account("personal-icloud", exclude_folders=["Junk"])
        server = FakeIMAPServer()
        for box, uid in (("INBOX", 1), ("Sent", 1), ("Junk", 1)):
            server.add(box, uid, rfc822(box, box, message_id=f"<{box}@x>"))
        result = self.sync(accounts_lib.get_account("personal-icloud"), server)
        self.assertEqual(sorted(item["mailbox"] for item in result["mailboxes"]), ["INBOX", "Sent"])


# ---------------------------------------------------------------------------
# Search, threads, provenance
# ---------------------------------------------------------------------------


class SearchThreadProvenanceTests(MailFixture):
    def populate(self) -> None:
        work = self.account("earthlink", "work-earthlink", "me@earthlink.net")
        home = self.account("icloud", "personal-icloud", "me@icloud.com")
        work_server, home_server = FakeIMAPServer(), FakeIMAPServer()
        work_server.add("INBOX", 1, rfc822("Open enrollment reminder", "Benefits open enrollment ends Friday.", sender="HR <hr@corp.test>", message_id="<oe@x>", date="Mon, 14 Sep 2026 09:00:00 +0000"))
        work_server.add("Sent", 1, rfc822("Re: Open enrollment reminder", "Thanks, done.", sender="Me <me@earthlink.net>", to="hr@corp.test", message_id="<oe-reply@x>", in_reply_to="<oe@x>", references="<oe@x>", date="Tue, 15 Sep 2026 09:00:00 +0000"))
        home_server.add("INBOX", 1, rfc822("Garden club", "Bring enrollment forms for the garden club.", sender="Club <club@garden.test>", message_id="<gc@x>", date="Wed, 02 Sep 2026 09:00:00 +0000",
                                           attachment=("roster.csv", "text/csv", b"name,plot\nAda,7\n")))
        self.sync(accounts_lib.get_account("work-earthlink"), work_server, mailboxes=["INBOX", "Sent"])
        self.sync(home, home_server)

    def test_filters(self) -> None:
        self.populate()
        with mock.patch.object(mail, "DB", self.db):
            self.assertEqual(len(mail.search("enrollment")), 3)
            self.assertEqual([item["account_id"] for item in mail.search("enrollment", accounts=["personal-icloud"])], ["personal-icloud"])
            self.assertEqual(len(mail.search("enrollment", providers=["earthlink"])), 2)
            self.assertEqual(len(mail.search("enrollment", mailboxes=["Sent"])), 1)
            self.assertEqual(len(mail.search("", sender="hr@corp.test")), 1)
            self.assertEqual(len(mail.search("", recipient="hr@corp.test")), 1)
            self.assertEqual(len(mail.search("enrollment", after="2026-09-10")), 2)
            self.assertEqual(len(mail.search("enrollment", before="2026-09-10")), 1)
            self.assertEqual(len(mail.search("plot roster")), 1, "attachment text is searchable")
            result = mail.search("garden")[0]
            self.assertTrue(result["id"].startswith("msg_") and result["thread_id"].startswith("thr_"))
            self.assertEqual(result["sources"], ["personal-icloud:INBOX"])
            self.assertLessEqual(len(result["snippet"]), store_lib.SNIPPET_CHARS)
            message = mail.get_message(id=result["id"])
            self.assertEqual(message["attachment_list"][0]["filename"], "roster.csv")
            self.assertNotIn("body", message)
            self.assertIn("garden club", mail.get_message(id=result["id"], include_body=True)["body"])
            self.assertEqual(mail.get_message("1", "INBOX", account_id="personal-icloud")["id"], result["id"], "v1 uid/mailbox lookup still works")
            self.assertEqual(mail.search('enrollment" OR "x'), mail.search("enrollment OR x"), "user text never becomes FTS syntax")

    def test_fallback_search_without_fts(self) -> None:
        self.populate()
        with mock.patch.object(store_lib, "FTS", "CREATE VIRTUAL TABLE mail_fts USING no_such_module(x)"):
            with store_lib.Store(self.db) as store:
                self.assertFalse(store.fts)
                self.assertEqual(len(store.search("enrollment")), 3)
                self.assertEqual(len(store.search("enrollment", accounts=["work-earthlink"])), 2)

    def test_threads(self) -> None:
        self.populate()
        with mock.patch.object(mail, "DB", self.db):
            root = mail.search("Benefits")[0]
            thread = mail.get_thread(message_id=root["id"])
            self.assertEqual([item["subject"] for item in thread["messages"]], ["Open enrollment reminder", "Re: Open enrollment reminder"])
            self.assertEqual(mail.get_thread(thread_id=thread["thread_id"])["count"], 2)

    def test_reply_before_parent_and_same_subject_are_handled(self) -> None:
        with store_lib.Store(self.db) as store:
            from agent_os.mail.message import parse

            def add(uid: str, raw: bytes) -> str:
                return store.record(parse(raw), {"id": store_lib.live_source_id("icloud", "a", "INBOX", "1", uid), "source_kind": "live_imap", "provider": "icloud", "account_id": "a", "mailbox": "INBOX", "uidvalidity": "1", "uid": uid})["message_id"]

            child = add("2", rfc822("Re: Plan", "reply", message_id="<child@x>", in_reply_to="<parent@x>"))
            parent = add("1", rfc822("Plan", "original", message_id="<parent@x>"))
            stranger = add("3", rfc822("Plan", "unrelated email with the same subject", sender="Other <o@x.test>", message_id="<other@x>"))
            no_id = add("4", rfc822("Plan", "no message id at all", sender="Third <t@x.test>"))
            store.conn.commit()
            ids = {name: store.conn.execute("SELECT thread_id FROM mail_messages WHERE id=?", (value,)).fetchone()[0] for name, value in (("child", child), ("parent", parent), ("stranger", stranger), ("no_id", no_id))}
        self.assertEqual(ids["child"], ids["parent"], "a reply indexed before its parent joins the parent's thread")
        self.assertEqual(len({ids["parent"], ids["stranger"], ids["no_id"]}), 3, "equal subjects alone never merge threads")

    def test_live_and_archive_copies_keep_both_observations(self) -> None:
        self.populate()
        raw = rfc822("Open enrollment reminder", "Benefits open enrollment ends Friday.", sender="HR <hr@corp.test>", message_id="<oe@x>", date="Mon, 14 Sep 2026 09:00:00 +0000")
        conflicting = rfc822("Totally different", "Another email that reused the ID.", sender="Spam <s@x.test>", message_id="<oe@x>")
        no_id = rfc822("Old note", "an archive-only email without a Message-ID")
        with mock.patch.object(mail, "DB", self.db):
            result = mail.sync_archive_records([
                {"folder": "Inbox", "record_key": "0001", "raw": raw},
                {"folder": "Inbox", "record_key": "0002", "raw": conflicting},
                {"folder": "Notes", "record_key": "0003", "raw": no_id},
                {"folder": "Notes-copy", "record_key": "0004", "raw": no_id},
            ], archive_id="pst-2019", ledger_dir=config.LEDGER_DIR)
            self.assertEqual((result["indexed_new"], result["deduplicated"]), (4, 2))
            hit = mail.search("Benefits")[0]
            self.assertEqual(hit["source_count"], 2)
            self.assertEqual(sorted(hit["sources"]), ["pst_archive:pst-2019/Inbox", "work-earthlink:INBOX"])
            self.assertEqual(len(mail.search("reused")), 1, "same Message-ID, incompatible content: kept separate")
            self.assertEqual(mail.search("archive-only")[0]["source_count"], 2, "exact content without Message-ID: one message, two observations")
            self.assertEqual(len(mail.search("Benefits", source_kinds=["pst_archive"])), 1)
            twin = rfc822("Weekly note", "identical text", message_id="<twin-1@x>")
            twin2 = rfc822("Weekly note", "identical text", message_id="<twin-2@x>")
            mail.sync_archive_records([{"folder": "Inbox", "record_key": "t1", "raw": twin}, {"folder": "Inbox", "record_key": "t2", "raw": twin2}], archive_id="pst-2019", ledger_dir=config.LEDGER_DIR)
            self.assertEqual(len(mail.search("identical text")), 2, "same text, different Message-IDs: two emails")
            again = mail.sync_archive_records([{"folder": "Inbox", "record_key": "0001", "raw": raw}], archive_id="pst-2019", ledger_dir=config.LEDGER_DIR)
            self.assertEqual(again["skipped"], 1)


# ---------------------------------------------------------------------------
# Migration from schema v1
# ---------------------------------------------------------------------------


class MigrationTests(MailFixture):
    def make_v1(self) -> None:
        self.db.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.db)
        conn.execute("CREATE TABLE messages (uid TEXT NOT NULL, mailbox TEXT NOT NULL, subject TEXT, sender TEXT, recipients TEXT, date TEXT, message_id TEXT, body TEXT, PRIMARY KEY(mailbox, uid))")
        conn.executemany("INSERT INTO messages VALUES (?,?,?,?,?,?,?,?)", [
            ("1", "INBOX", "Old one", "a@x.test", "me@icloud.com", "Mon, 01 Jun 2026 10:00:00 +0000", "<old1@x>", "first old body"),
            ("2", "INBOX", "Old two", "b@x.test", "me@icloud.com", "Tue, 02 Jun 2026 10:00:00 +0000", "", "second old body"),
        ])
        conn.commit()
        conn.close()

    def test_v1_index_is_migrated_with_backup(self) -> None:
        self.make_v1()
        with store_lib.Store(self.db) as store:
            self.assertEqual(store.migration["migrated_rows"], 2)
            self.assertTrue(Path(store.migration["backup"]).exists())
            rows = store.conn.execute("SELECT account_id, provider, uidvalidity, uid, legacy FROM mail_sources ORDER BY uid").fetchall()
            self.assertEqual([tuple(row) for row in rows], [("icloud", "icloud", None, "1", 1), ("icloud", "icloud", None, "2", 1)], "UIDVALIDITY is never invented")
            self.assertEqual(store.conn.execute("SELECT COUNT(*) FROM legacy_messages_v1").fetchone()[0], 2, "original rows kept")
            self.assertEqual([item["subject"] for item in store.search("old body")], ["Old two", "Old one"])
        with store_lib.Store(self.db) as store:
            self.assertIsNone(store.migration, "migration runs once")

    def test_failed_migration_leaves_the_original_intact(self) -> None:
        self.make_v1()
        with mock.patch.object(store_lib, "_parsed_from_row", side_effect=RuntimeError("boom")):
            with self.assertRaises(RuntimeError):
                store_lib.Store(self.db)
        conn = sqlite3.connect(self.db)
        self.assertEqual(conn.execute("SELECT COUNT(*) FROM messages").fetchone()[0], 2)
        self.assertEqual(conn.execute("PRAGMA user_version").fetchone()[0], 0)
        conn.close()

    def test_live_resync_supersedes_legacy_rows(self) -> None:
        self.make_v1()
        config.LEGACY_CONFIG.parent.mkdir(parents=True, exist_ok=True)
        config.LEGACY_CONFIG.write_text(json.dumps({"email": "me@icloud.com"}), encoding="utf-8")
        account = accounts_lib.get_account("icloud")
        accounts_lib.set_secret("icloud", LEAK_PROBE)
        server = FakeIMAPServer()
        server.add("INBOX", 1, rfc822("Old one", "first old body", sender="a@x.test", to="me@icloud.com", message_id="<old1@x>", date="Mon, 01 Jun 2026 10:00:00 +0000"))
        self.sync(account, server)
        states = {(row["uid"], row["uidvalidity"]): row["state"] for row in self.sources()}
        self.assertEqual(states[("1", None)], "superseded")
        self.assertEqual(states[("1", "100")], "present")
        with mock.patch.object(mail, "DB", self.db):
            self.assertEqual(mail.search("first old body")[0]["sources"], ["icloud:INBOX"])


# ---------------------------------------------------------------------------
# Surfaces
# ---------------------------------------------------------------------------


class SurfaceTests(MailFixture):
    def test_mcp_tools_and_cli(self) -> None:
        from agent_os.cli import main
        from agent_os.mcp_server import TOOL_SCHEMAS, methods

        for name in ("mail.accounts", "mail.account_status", "mail.sync", "mail.sync_status", "mail.search", "mail.get_message", "mail.get_thread"):
            self.assertIn(name, TOOL_SCHEMAS)
            self.assertIn(name, methods())
        forbidden = [name for name in TOOL_SCHEMAS if name.startswith("mail.") and any(word in name for word in ("send", "delete", "move", "flag", "mark"))]
        self.assertEqual(forbidden, [])
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            code = main(["mail", "account", "add", "--provider", "earthlink", "--id", "work-earthlink", "--email", "me@earthlink.net"])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(buffer.getvalue())["added"]["imap"], {"host": "imap.earthlink.net", "port": 993, "security": "ssl"})
        with mock.patch("getpass.getpass", return_value=LEAK_PROBE), contextlib.redirect_stdout(io.StringIO()) as out, contextlib.redirect_stderr(io.StringIO()):
            main(["mail", "account", "credential", "work-earthlink"])
        self.assertNotIn(LEAK_PROBE, out.getvalue())
        self.assertEqual(self.keyring.get_password(accounts_lib.SECRET_SERVICE, "work-earthlink"), LEAK_PROBE)
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            main(["mail", "accounts"])
        listed = json.loads(buffer.getvalue())["accounts"][0]
        self.assertEqual((listed["account_id"], listed["credential_available"], listed["read_only"]), ("work-earthlink", True, True))


class SetupWindowTests(MailFixture):
    """The window's logic (no display needed)."""

    def test_save_account_stores_secret_tests_login_and_reuses_account(self) -> None:
        from agent_os.mail.setup_window import save_account

        seen = []
        outcome = save_account("earthlink", " me@earthlink.net ", LEAK_PROBE, test=lambda account: seen.append(account.id) or {"ok": True})
        self.assertEqual((outcome["ok"], outcome["account_id"], outcome["created"]), (True, "earthlink", True))
        self.assertNotIn(LEAK_PROBE, json.dumps(outcome))
        self.assertEqual(self.keyring.get_password(accounts_lib.SECRET_SERVICE, "earthlink"), LEAK_PROBE)
        self.assertNotIn(LEAK_PROBE, config.ACCOUNTS_FILE.read_text(encoding="utf-8"))
        retry = save_account("earthlink", "ME@earthlink.net", "new-value", test=lambda account: {"ok": False, "error": "auth_failed"})
        self.assertEqual((retry["ok"], retry["account_id"], retry["created"]), (False, "earthlink", False))
        self.assertIn("not accepted", retry["message"])
        second = save_account("earthlink", "other@earthlink.net", "x", test=lambda account: {"ok": True})
        self.assertEqual(second["account_id"], "earthlink-2")
        self.assertEqual(len(accounts_lib.load_accounts()), 2)

    def test_earthlink_hosted_domain_gets_hosting_server_and_existing_account_is_updated(self) -> None:
        from agent_os.mail.setup_window import save_account

        self.assertEqual(accounts_lib.default_server("earthlink", "hr@4rtec.com"), ("securemail.hosting.earthlink.net", 993, "ssl"))
        self.assertEqual(accounts_lib.default_server("earthlink", "me@earthlink.net")[0], "imap.earthlink.net")
        self.assertEqual(accounts_lib.default_server("icloud", "me@example.com")[0], "imap.mail.me.com")
        accounts_lib.add_account("earthlink", "earthlink", "hr@4rtec.com")  # saved earlier with the wrong server
        outcome = save_account("earthlink", "hr@4rtec.com", "x", test=lambda account: {"ok": True})
        self.assertEqual((outcome["created"], outcome["server"]), (False, "securemail.hosting.earthlink.net:993 (ssl)"))
        custom = save_account("earthlink", "hr@4rtec.com", "x", host="mail.4rtec.com", port=143, security="starttls", test=lambda account: {"ok": True})
        self.assertEqual(custom["server"], "mail.4rtec.com:143 (starttls)")
        self.assertEqual(accounts_lib.get_account("earthlink").public()["imap"], {"host": "mail.4rtec.com", "port": 143, "security": "starttls"})
        self.assertFalse(save_account("earthlink", "hr@4rtec.com", "x", security="none", test=lambda account: {"ok": True})["ok"])

    def test_starttls_upgrades_before_login_and_certificate_errors_are_named(self) -> None:
        import ssl

        calls = []

        class Plain:
            def __init__(self, host, port, timeout=None):
                calls.append(("connect", host, port))

            def starttls(self, ssl_context=None):
                calls.append(("starttls", ssl_context.check_hostname, ssl_context.verify_mode == ssl.CERT_REQUIRED))

        with mock.patch.object(imaplib, "IMAP4", Plain):
            imap.connect("mail.example.test", 143, security="starttls")
        self.assertEqual(calls, [("connect", "mail.example.test", 143), ("starttls", True, True)])
        self.assertEqual(imap.categorize(ssl.SSLCertVerificationError("hostname mismatch")), "tls_certificate")

    def test_pasted_password_line_break_is_trimmed(self) -> None:
        from agent_os.mail.setup_window import save_account

        save_account("icloud", "me@icloud.com", f"  {LEAK_PROBE}\r\n", test=lambda account: {"ok": True})
        self.assertEqual(self.keyring.get_password(accounts_lib.SECRET_SERVICE, "icloud"), LEAK_PROBE)
        with self.assertRaises(accounts_lib.AccountError):
            accounts_lib.set_secret("icloud", "two\nlines")
        self.assertFalse(save_account("icloud", "me@icloud.com", " \n", test=lambda account: {"ok": True})["ok"])

    def test_save_account_validates_before_touching_anything(self) -> None:
        from agent_os.mail.setup_window import save_account

        for provider, email, secret in (("gmail", "a@b.c", "x"), ("icloud", "not-an-email", "x"), ("icloud", "a@icloud.com", "")):
            self.assertFalse(save_account(provider, email, secret, test=lambda account: {"ok": True})["ok"])
        self.assertEqual(accounts_lib.load_accounts(), [])
        self.assertEqual(self.keyring.data, {})


class BenchmarkTests(unittest.TestCase):
    def test_benchmark_runs_on_synthetic_mail(self) -> None:
        from agent_os.mail.benchmark import run

        out = Path(tempfile.mkdtemp(prefix="agent-os-mail-bench-"))
        self.addCleanup(shutil.rmtree, out, True)
        result = run(20, out_dir=out)
        self.assertEqual(result["logical_messages"], 60, "2 accounts x (20 + a 10-message delta)")
        self.assertTrue(Path(result["file"]).exists())
        self.assertLess(result["no_change_resync_seconds"], result["first_import_seconds"] + 1)


if __name__ == "__main__":
    unittest.main()
