import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

import unittest
from types import SimpleNamespace

from agent_os.mail.imap_write import ImapMover, MoveRefused, WriteViolation, connect_write


class FakeClient:
    def __init__(self, caps="IMAP4REV1 MOVE", folders=()):
        self.caps = caps
        self.folders = list(folders)
        self.commands = []
        self.untagged_responses = {}
        self.delim = "/"
        self.validity = b"77"

    def capability(self):
        self.commands.append("CAPABILITY")
        return "OK", [self.caps.encode()]

    def list(self):
        self.commands.append("LIST")
        return "OK", [f'(\\HasNoChildren) "{self.delim}" "{f}"'.encode() for f in self.folders]

    def create(self, name):
        self.commands.append(f"CREATE {name}")
        return "OK", [b"done"]

    def subscribe(self, name):
        self.commands.append(f"SUBSCRIBE {name}")
        return "OK", [b"done"]

    def select(self, name, readonly=False):
        self.commands.append(f"SELECT {name} readonly={readonly}")
        return "OK", [b"3"]

    def response(self, name):
        return name, ([self.validity] if name == "UIDVALIDITY" else [None])

    def _simple_command(self, name, *args):
        self.commands.append(" ".join([name, *map(str, args)]))
        return "OK", [b"[COPYUID 77 5,6 105,106] done"]

    def uid(self, command, *args):
        if command == "MOVE":  # stdlib imaplib rejects UID MOVE
            raise RuntimeError("Unknown IMAP4 UID command: MOVE")
        self.commands.append(" ".join(["UID", command, *map(str, args)]))
        if command in ("MOVE", "COPY"):
            return "OK", [b"[COPYUID 77 5,6 105,106] done"]
        return "OK", [b"done"]

    def logout(self):
        self.commands.append("LOGOUT")
        return "BYE", []


def mover_for(client, allow=True):
    return ImapMover(SimpleNamespace(id="a1", allow_organize=allow), lambda acct: client)


class ImapMoverTests(unittest.TestCase):
    def test_refuses_read_only_account(self):
        with self.assertRaises(MoveRefused):
            mover_for(FakeClient(), allow=False)

    def test_move_path_creates_folder_and_records_dest_uids(self):
        client = FakeClient(folders=["INBOX"])
        mover = mover_for(client)
        self.assertEqual(mover.ensure_folder("Receipts"), "Receipts")
        self.assertIn("CREATE Receipts", client.commands)
        self.assertEqual(mover.select("INBOX"), "77")
        self.assertTrue(mover.capabilities("INBOX")["move"])
        self.assertEqual(mover.move(["5", "6"], "Receipts"), {"5": "105", "6": "106"})
        self.assertIn("UID MOVE 5,6 Receipts", client.commands)

    def test_existing_folder_not_created(self):
        client = FakeClient(folders=["INBOX", "Receipts"])
        mover_for(client).ensure_folder("Receipts")
        self.assertFalse(any(c.startswith("CREATE") for c in client.commands))

    def test_copy_fallback_never_deletes(self):
        client = FakeClient(caps="IMAP4REV1")
        mover = mover_for(client)
        mover.select("INBOX")
        self.assertFalse(mover.capabilities("INBOX")["move"])
        self.assertEqual(mover.copy_flag(["5", "6"], "Receipts"), {"5": "105", "6": "106"})
        with self.assertRaises(MoveRefused):
            mover.move(["5"], "Receipts")
        mover.close()
        joined = "\n".join(client.commands)
        self.assertNotIn("UID MOVE", joined)
        self.assertNotIn("\\Deleted", joined)
        self.assertNotIn("EXPUNGE", joined.upper())
        self.assertNotIn("CLOSE", joined.upper())
        self.assertIn("UID COPY 5,6", joined)

    def test_undo_issues_reverse_move(self):
        client = FakeClient()
        mover = mover_for(client)
        entry = {"method": "move", "from": {"mailbox": "INBOX", "uid": "5", "uidvalidity": "77"},
                 "to": {"mailbox": "Receipts", "uid": "105", "uidvalidity": "77"}}
        self.assertEqual(mover.undo(entry), "105")
        self.assertIn("SELECT Receipts readonly=False", client.commands)
        self.assertEqual(client.commands[-1], "UID MOVE 105 INBOX")

    def test_undo_skips_on_uidvalidity_mismatch(self):
        client = FakeClient()
        mover = mover_for(client)
        entry = {"method": "move", "from": {"mailbox": "INBOX", "uid": "5", "uidvalidity": "77"},
                 "to": {"mailbox": "Receipts", "uid": "105", "uidvalidity": "88"}}
        self.assertIsNone(mover.undo(entry))
        self.assertFalse(any("MOVE" in c for c in client.commands))
        client.validity = b"88"
        self.assertEqual(mover.undo(entry), "105")
        self.assertEqual(client.commands[-1], "UID MOVE 105 INBOX")

    def test_copy_flag_undo_checks_validity(self):
        client = FakeClient()
        mover = mover_for(client)
        entry = {"method": "copy_flag", "from": {"mailbox": "INBOX", "uid": "5", "uidvalidity": "12"},
                 "to": {"mailbox": "Receipts", "uid": "105", "uidvalidity": "88"}}
        self.assertIsNone(mover.undo(entry))
        self.assertFalse(any("STORE" in c for c in client.commands))

    def test_nested_folder_with_dot_delimiter_and_inbox_prefix(self):
        client = FakeClient(folders=["INBOX", "INBOX.Done"])
        client.delim = "."
        real = mover_for(client).ensure_folder("Mail/Receipts")
        self.assertEqual(real, "INBOX.Mail.Receipts")
        creates = [c for c in client.commands if c.startswith("CREATE")]
        self.assertEqual(creates, ["CREATE INBOX.Mail", "CREATE INBOX.Mail.Receipts"])

    def test_already_exists_create_is_tolerated(self):
        client = FakeClient(folders=["INBOX"])
        client.create = lambda name: ("NO", [b"[ALREADYEXISTS] exists"])
        self.assertEqual(mover_for(client).ensure_folder("Receipts"), "Receipts")

    def test_refused_commands_never_reach_client(self):
        client = FakeClient()
        mover = mover_for(client)
        refused = [("EXPUNGE",), ("UID EXPUNGE", "5"), ("CLOSE",), ("DELETE", "X"), ("RENAME", "X", "Y"),
                   ("APPEND", "X"), ("UID STORE", "5", "+FLAGS", "(\\Deleted)"),
                   ("UID STORE", "5", "+FLAGS.SILENT", "(\\Deleted)"), ("UID FETCH", "5", "(BODY[])")]
        for command in refused:
            with self.subTest(command=command), self.assertRaises(WriteViolation):
                mover._send(*command)
        self.assertEqual(client.commands, [])

    def test_connect_write_refuses_disabled_account_and_builds_mover(self):
        with self.assertRaises(MoveRefused):
            connect_write(SimpleNamespace(id="a1", allow_organize=False), factory=lambda a: FakeClient())
        self.assertIsInstance(
            connect_write(SimpleNamespace(id="a1", allow_organize=True), factory=lambda a: FakeClient()), ImapMover)


if __name__ == "__main__":
    unittest.main()
