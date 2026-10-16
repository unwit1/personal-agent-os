from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os import mcp_server
from agent_os.executive import computer
from agent_os.executive.window import actions_computer, registry
from agent_os.executive.window.confirm import ENV_HOME, PendingStore

SECRET = "TOP-SECRET-CONTENT-123"


def call(name, /, **arguments):
    request = {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": name, "arguments": arguments}}
    result = mcp_server._handle_mcp(request, mcp_server.methods())["result"]
    return bool(result.get("isError")), json.loads(result["content"][0]["text"])


class ComputerTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        base = Path(tmp.name).resolve()
        self.root = base / "docs"
        self.outside = base / "outside"
        self.drafts = base / "drafts"
        self.trash = base / "trash"
        self.home = base / "window"
        for d in (self.root, self.outside):
            d.mkdir()
        (self.root / "notes.md").write_text(f"hello {SECRET}\n", encoding="utf-8")
        (self.root / "sub").mkdir()
        (self.root / "sub" / "data.csv").write_text("a,b\n1,2\n", encoding="utf-8")
        (self.outside / "private.txt").write_text("nope", encoding="utf-8")
        config = base / "computer.json"
        config.write_text(json.dumps({"allowed_roots": [str(self.root)], "drafts_root": str(self.drafts),
                                      "trash_root": str(self.trash)}), encoding="utf-8")
        env = patch.dict(os.environ, {computer.ENV_CONFIG: str(config), ENV_HOME: str(self.home)})
        env.start()
        self.addCleanup(env.stop)
        self.reg = registry.Registry()
        actions_computer.register(self.reg)
        reg_patch = patch.object(mcp_server, "_window_registry", lambda: self.reg)
        reg_patch.start()
        self.addCleanup(reg_patch.stop)
        self.pending = PendingStore()

    def audit_lines(self):
        return [json.loads(line) for line in computer.audit_path().read_text(encoding="utf-8").splitlines()]

    def only_token(self):
        records = self.pending.list()
        self.assertEqual(len(records), 1)
        return records[0]["token"]

    # ---- guard

    def test_path_escapes_rejected(self):
        for bad in (str(self.root / ".." / "outside" / "private.txt"), str(self.outside / "private.txt"),
                    "../outside/private.txt"):
            with self.assertRaises(computer.ComputerAccessError, msg=bad):
                computer.read_text(bad)
        try:
            os.symlink(self.outside, self.root / "link")
        except (OSError, NotImplementedError):
            self.skipTest("symlinks unavailable")
        with self.assertRaises(computer.ComputerAccessError):
            computer.read_text(str(self.root / "link" / "private.txt"))
        with self.assertRaises(computer.ComputerAccessError):
            computer.list_dir(str(self.root / "link"))
        found = computer.search_files(str(self.root), "*.txt")
        self.assertEqual(found["results"], [])
        err, out = call("computer.read", path=str(self.outside / "private.txt"))
        self.assertTrue(err)
        self.assertIn("outside the allowed roots", out["error"])

    # ---- free tier

    def test_free_ops(self):
        listed = computer.list_dir(str(self.root))
        self.assertEqual({e["name"] for e in listed["entries"]}, {"notes.md", "sub"})
        read = computer.read_text("notes.md")
        self.assertIn(SECRET, read["text"])
        hits = computer.search_files(str(self.root), "*.CSV")
        self.assertEqual([Path(r["path"]).name for r in hits["results"]], ["data.csv"])
        hits = computer.search_files(str(self.root), "*", contains="top-secret")
        self.assertEqual([Path(r["path"]).name for r in hits["results"]], ["notes.md"])
        err, out = call("computer.list", path=str(self.root / "sub"))
        self.assertFalse(err, out)
        self.assertEqual(out["entries"][0]["name"], "data.csv")

    def test_large_and_unsupported_files_are_metadata_only(self):
        big = self.root / "big.txt"
        big.write_bytes(b"x" * (computer.MAX_READ_BYTES + 1))
        self.assertIsNone(computer.read_text(str(big))["text"])
        (self.root / "blob.bin").write_bytes(b"\x00\x01")
        out = computer.read_text(str(self.root / "blob.bin"))
        self.assertIsNone(out["text"])
        self.assertEqual(out["size"], 2)

    # ---- automatic tier

    def test_draft_never_overwrites(self):
        first = computer.write_draft("letter.md", "one")
        err, second = call("computer.write_draft", name="letter.md", content="two")
        self.assertFalse(err, second)
        third = computer.write_draft("letter.md", "three")
        self.assertEqual(Path(first["path"]).name, "letter.md")
        self.assertEqual(Path(second["path"]).name, "letter-v2.md")
        self.assertEqual(Path(third["path"]).name, "letter-v3.md")
        self.assertEqual(Path(first["path"]).read_text(encoding="utf-8"), "one")
        for bad in ("../escape.md", "sub/x.md", str(self.root / "x.md")):
            with self.assertRaises(computer.ComputerAccessError):
                computer.write_draft(bad, "x")

    # ---- confirm tier

    def test_write_waits_for_confirm_and_backs_up(self):
        target = self.root / "notes.md"
        err, out = call("computer.write", path=str(target), content="new text\n")
        self.assertFalse(err, out)
        self.assertEqual(out["status"], "needs_confirmation")
        self.assertEqual(out["message"], "Waiting for you to click Confirm in the command center.")
        self.assertNotIn("confirm_token", out)
        self.assertNotIn(self.only_token(), json.dumps(out))
        self.assertIn("+new text", out["preview"]["diff"])
        self.assertIn(f"-hello {SECRET}", out["preview"]["diff"])
        self.assertIn(SECRET, target.read_text(encoding="utf-8"))  # untouched until Confirm
        result = self.reg.confirm(self.only_token(), self.pending)
        self.assertEqual(target.read_text(encoding="utf-8"), "new text\n")
        self.assertIn(SECRET, Path(result["backup"]).read_text(encoding="utf-8"))

    def test_write_refuses_when_file_changed_after_preview(self):
        target = self.root / "notes.md"
        call("computer.write", path=str(target), content="new\n")
        target.write_text("edited meanwhile\n", encoding="utf-8")
        with self.assertRaises(computer.ComputerAccessError):
            self.reg.confirm(self.only_token(), self.pending)
        self.assertEqual(target.read_text(encoding="utf-8"), "edited meanwhile\n")

    def test_move_waits_for_confirm_and_never_overwrites(self):
        src, dst = self.root / "notes.md", self.root / "sub" / "moved.md"
        err, out = call("computer.move", source=str(src), target=str(dst))
        self.assertFalse(err, out)
        self.assertEqual((out["preview"]["source"], out["preview"]["target"]), (str(src), str(dst)))
        self.assertTrue(src.exists())
        self.reg.confirm(self.only_token(), self.pending)
        self.assertFalse(src.exists())
        self.assertTrue(dst.exists())
        err, out = call("computer.move", source=str(dst), target=str(self.root / "sub" / "data.csv"))
        self.assertTrue(err)
        err, out = call("computer.move", source=str(dst), target=str(self.outside / "x.md"))
        self.assertTrue(err)
        self.assertEqual(self.pending.list(), [])

    def test_delete_goes_to_trash(self):
        target = self.root / "notes.md"
        err, out = call("computer.delete", path=str(target))
        self.assertFalse(err, out)
        self.assertTrue(target.exists())
        result = self.reg.confirm(self.only_token(), self.pending)
        self.assertFalse(target.exists())
        trashed = Path(result["trashed_to"])
        self.assertEqual(trashed.parent, self.trash)
        self.assertIn(SECRET, trashed.read_text(encoding="utf-8"))
        origin = json.loads(trashed.with_name(trashed.name + ".origin.json").read_text(encoding="utf-8"))
        self.assertEqual(origin["original_path"], str(target))

    def test_open_waits_for_confirm(self):
        opened = []
        with patch.object(computer, "OPENER", opened.append):
            err, out = call("computer.open", path=str(self.root / "notes.md"))
            self.assertFalse(err, out)
            self.assertEqual(opened, [])
            self.reg.confirm(self.only_token(), self.pending)
        self.assertEqual(opened, [str(self.root / "notes.md")])

    def test_run_command_gate_and_refusals(self):
        calls = []

        def runner(args, **kwargs):
            calls.append((args, kwargs))
            return type("Done", (), {"returncode": 0, "stdout": "ok", "stderr": ""})()

        with patch.object(computer, "RUNNER", runner):
            for argv in ("ls -la", ["ls", "a;rm -rf /"], ["echo", "$(id)"], ["cat", "a|b"], ["bash", "-c", "ls"],
                         ["cmd.exe", "/c", "dir"], ["run.bat"], []):
                err, out = call("computer.run", argv=argv)
                self.assertTrue(err, argv)
                with self.assertRaises(computer.ComputerAccessError):
                    computer.run_command(argv)
            err, out = call("computer.run", argv=["git", "status"], cwd=str(self.outside))
            self.assertTrue(err)
            self.assertEqual(self.pending.list(), [])
            err, out = call("computer.run", argv=["git", "status"], cwd=str(self.root / "sub"))
            self.assertFalse(err, out)
            self.assertEqual(out["preview"]["argv"], ["git", "status"])
            self.assertEqual(calls, [])
            result = self.reg.confirm(self.only_token(), self.pending)
        self.assertEqual(result["stdout"], "ok")
        args, kwargs = calls[0]
        self.assertEqual(args, ["git", "status"])
        self.assertIs(kwargs["shell"], False)
        self.assertEqual(kwargs["cwd"], str(self.root / "sub"))
        self.assertEqual(kwargs["timeout"], 120)

    def test_window_invoke_only_previews(self):
        item = {"id": "computer-x", "kind": "computer_request"}
        out = self.reg.invoke("computer.delete_file", item, {"path": str(self.root / "notes.md")}, self.pending)
        self.assertEqual(out["status"], "needs_confirmation")
        self.assertTrue((self.root / "notes.md").exists())
        self.assertTrue(all(self.reg._actions[a]["consequential"] for a, *_ in actions_computer.ACTIONS))

    def test_audit_has_no_contents(self):
        computer.read_text("notes.md")
        computer.write_draft("d.md", SECRET)
        call("computer.write", path=str(self.root / "notes.md"), content=SECRET + "-new")
        self.reg.confirm(self.only_token(), self.pending)
        with self.assertRaises(computer.ComputerAccessError):
            computer.read_text(str(self.outside / "private.txt"))
        raw = computer.audit_path().read_text(encoding="utf-8")
        self.assertNotIn(SECRET, raw)
        lines = self.audit_lines()
        self.assertEqual([l["op"] for l in lines],
                         ["read_text", "write_draft", "preview_write", "write_file", "read_text"])
        self.assertTrue(all({"op", "path", "ok", "ts"} <= set(l) for l in lines))
        self.assertFalse(lines[-1]["ok"])

    def test_tools_listed(self):
        listed = mcp_server._handle_mcp({"jsonrpc": "2.0", "id": 1, "method": "tools/list"}, mcp_server.methods())
        names = {t["name"] for t in listed["result"]["tools"]}
        for op in ("list", "read", "search", "write_draft", "write", "move", "delete", "open", "run"):
            self.assertIn(f"computer.{op}", names)
            self.assertIn(f"computer.{op}", mcp_server.methods())


if __name__ == "__main__":
    unittest.main()
