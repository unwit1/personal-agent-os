import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import argparse  # noqa: E402
import unittest  # noqa: E402
from types import SimpleNamespace  # noqa: E402
from unittest import mock  # noqa: E402

from agent_os.mail import accounts as accounts_lib  # noqa: E402
from agent_os.mail import cli, imap_write, organize, organize_apply  # noqa: E402


def run(argv):
    parser = argparse.ArgumentParser()
    cli.register(parser.add_subparsers(dest="command", required=True))
    out = []
    code = cli.dispatch(parser.parse_args(["mail", *argv]), out.append)
    return code, out


class OrganizeCliTests(unittest.TestCase):
    def test_plan_passes_scope(self):
        with mock.patch.object(organize, "build_plan", return_value={"accounts": {}}) as build:
            code, out = run(["organize-plan", "--scope", "work"])
        self.assertEqual(code, 0)
        self.assertEqual(out, [{"accounts": {}}])
        self.assertEqual(build.call_args.kwargs["scopes"], ("work",))

    def test_plan_defaults_to_all_scopes(self):
        with mock.patch.object(organize, "build_plan", return_value={}) as build:
            run(["organize-plan"])
        self.assertEqual(tuple(build.call_args.kwargs["scopes"]), ("work", "personal"))

    def _apply(self, extra):
        account = SimpleNamespace(mail_scope="personal")
        with mock.patch.object(accounts_lib, "get_account", return_value=account), \
                mock.patch.object(organize, "build_plan", return_value={"plan_id": "p"}) as build, \
                mock.patch.object(organize_apply, "default_journal_path", return_value=Path("j.jsonl")), \
                mock.patch.object(imap_write, "connect_write") as connector, \
                mock.patch.object(organize_apply, "apply_plan", return_value={"ok": True}) as apply:
            code, out = run(["organize-apply", "--account", "a1", "--category", "receipts_finance", *extra])
        return code, out, build, apply, connector

    def test_apply_dry_run_by_default(self):
        code, out, build, apply, connector = self._apply([])
        self.assertEqual(code, 0)
        self.assertEqual(out, [{"ok": True}])
        self.assertEqual(build.call_args.kwargs["scopes"], ("personal",))
        self.assertIs(apply.call_args.kwargs["dry_run"], True)
        self.assertEqual(apply.call_args.args, ({"plan_id": "p"}, "receipts_finance"))
        self.assertEqual(apply.call_args.kwargs["only_accounts"], ["a1"])
        self.assertIs(apply.call_args.kwargs["connect"], connector)
        self.assertEqual(apply.call_args.kwargs["journal_path"], Path("j.jsonl"))

    def test_apply_confirm_is_live(self):
        _, _, _, apply, _ = self._apply(["--confirm"])
        self.assertIs(apply.call_args.kwargs["dry_run"], False)

    def test_apply_error_reported(self):
        account = SimpleNamespace(mail_scope="work")
        with mock.patch.object(accounts_lib, "get_account", return_value=account), \
                mock.patch.object(organize, "build_plan", return_value={}), \
                mock.patch.object(organize_apply, "default_journal_path", return_value=Path("j.jsonl")), \
                mock.patch.object(organize_apply, "apply_plan", side_effect=organize_apply.OrganizeError("stale")):
            code, out = run(["organize-apply", "--account", "a1", "--category", "x"])
        self.assertEqual(code, 1)
        self.assertEqual(out, [{"error": "stale"}])

    def test_undo_dispatch(self):
        with mock.patch.object(organize_apply, "undo", return_value={"undone": 1}) as undo:
            code, out = run(["organize-undo", "jrn_1", "--seq", "3"])
            self.assertEqual((code, out), (0, [{"undone": 1}]))
            self.assertEqual(undo.call_args.args, ("jrn_1",))
            self.assertEqual(undo.call_args.kwargs["seq"], 3)
            self.assertIs(undo.call_args.kwargs["dry_run"], True)
            run(["organize-undo", "jrn_1", "--confirm"])
            self.assertIs(undo.call_args.kwargs["dry_run"], False)

    def test_spam_eval_prints_precision_recall(self):
        code, out = run(["spam-eval"])
        self.assertEqual(code, 0)
        self.assertIn("precision", out[0])
        self.assertIn("recall", out[0])


if __name__ == "__main__":
    unittest.main()
