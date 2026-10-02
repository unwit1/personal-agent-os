import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

import unittest
from types import SimpleNamespace

from agent_os.mail.imap_write import ImapMover, MoveRefused


class FakeClient:
    def __init__(self, caps="IMAP4REV1 MOVE", folders=()):
        self.caps = caps
        self.folders = list(folders)
        self.commands = []
        self.untagged_responses = {}

    def capability(self):
        self.commands.append("CAPABILITY")
        return "OK", [self.caps.encode()]

    def list(self):
        self.commands.append("LIST")
        return "OK", [f'(\\HasNoChildren) "/" "{f}"'.encode() for f in self.folders]

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
        return name, ([b"77"] if name == "UIDVALIDITY" else [None])

    def uid(self, command, *args):
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
        self.assertIn('CREATE "Receipts"', client.commands)
        self.assertEqual(mover.select("INBOX"), "77")
        self.assertTrue(mover.capabilities("INBOX")["move"])
        self.assertEqual(mover.move(["5", "6"], "Receipts"), {"5": "105", "6": "106"})
        self.assertIn('UID MOVE 5,6 "Receipts"', client.commands)

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
        mover.move(["5"], "Receipts")  # a plain move degrades to COPY too
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
                 "to": {"mailbox": "Receipts", "uid": "105", "uidvalidity": "88"}}
        mover.undo(entry)
        self.assertIn('SELECT "Receipts" readonly=False', client.commands)
        self.assertEqual(client.commands[-1], 'UID MOVE 105 "INBOX"')


if __name__ == "__main__":
    unittest.main()
