import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.mail import accounts as accounts_lib  # noqa: E402


class AllowMovesTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "accounts.json"

    def test_default_false(self):
        account = accounts_lib.Account(id="work-a", provider="icloud", email="a@example.test")
        self.assertFalse(account.allow_moves)
        with mock.patch.object(accounts_lib, "credential_status", return_value=(False, "none")):
            public = account.public()
        self.assertIs(public["allow_moves"], False)
        self.assertTrue(public["read_only"])
        self.assertTrue(account.read_only)

    def test_true_survives_save_load(self):
        account = accounts_lib.Account(id="work-a", provider="icloud", email="a@example.test", allow_moves=True)
        accounts_lib.save_accounts([account], self.path)
        loaded = accounts_lib.load_accounts(self.path)
        self.assertTrue(loaded[0].allow_moves)
        self.assertTrue(loaded[0].read_only)

    def test_legacy_file_without_key_is_false(self):
        legacy = {"schema_version": 1, "accounts": [{"id": "work-a", "provider": "icloud", "email": "a@example.test"}]}
        self.path.write_text(json.dumps(legacy), encoding="utf-8")
        self.assertFalse(accounts_lib.load_accounts(self.path)[0].allow_moves)


if __name__ == "__main__":
    unittest.main()
