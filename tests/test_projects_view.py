from __future__ import annotations

import json
import re
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from agent_os.executive import projects_view as view


class ProjectsViewTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name)
        self.repo = self.home / "HR GUI"
        self.repo.mkdir()
        (self.repo / ".git").mkdir()
        self.entry = {"id": "work", "name": "Work", "path": str(self.repo)}
        self.runner = Mock(side_effect=lambda argv, **kwargs: SimpleNamespace(returncode=0,
                           stdout={"rev-parse": "feature\n", "rev-list": "2\t3\n", "status": " M tracked\n?? new\n"}[argv[1]]))
        self.handoff = Mock(return_value={"created_at": "now", "completed": ["done"], "remaining": ["next"], "raw": "must not return"})

    def projects(self, **kwargs):
        return view.projects(home=self.home, state_home=self.home, entries=kwargs.pop("entries", [self.entry]),
                             runner=self.runner, resolver=kwargs.pop("resolver", lambda entry, _: (entry.get("path"), "test")),
                             handoff_reader=self.handoff, **kwargs)

    def test_inventory_git_handoff_and_sensitive(self):
        result = self.projects()[0]
        self.assertEqual(result["path"], str(self.repo.resolve()))
        self.assertTrue(result["sensitive"])
        self.assertEqual(result["git"], {"branch": "feature", "ahead": 2, "behind": 3, "dirty": 2})
        self.assertEqual(result["handoff"]["completed"], ["done"])
        self.assertNotIn("raw", result["handoff"])
        self.handoff.assert_called_once_with("work")

    def test_missing_and_non_git_checkout_skip_git(self):
        other = self.home / "ordinary"
        other.mkdir()
        rows = self.projects(entries=[{"id": "missing", "path": str(self.home / "missing")},
                                      {"id": "ordinary", "path": str(other)}])
        self.assertIsNone(rows[0]["path"])
        self.assertIsNone(rows[0]["git"])
        self.assertIsNone(rows[1]["git"])
        self.runner.assert_not_called()

    def test_canonical_registry_is_resolved_without_mutation(self):
        resolver = Mock(return_value=(self.repo, "override"))
        with patch.object(view.registry, "canonical_projects", return_value=[self.entry]):
            rows = view.projects(home=self.home, state_home=self.home, resolver=resolver,
                                 runner=self.runner, handoff_reader=self.handoff)
        self.assertEqual(rows[0]["id"], "work")
        resolver.assert_called_once_with(self.entry, [])
        self.assertNotIn("git", self.entry)

    def test_session_inventory_uses_identity_and_first_line_only(self):
        slug = re.sub(r"[^a-zA-Z0-9]", "-", str(self.repo.resolve()))
        claude = self.home / ".claude" / "projects" / slug
        claude.mkdir(parents=True)
        (claude / "claude-id.jsonl").write_text("PRIVATE TRANSCRIPT NOT JSON", encoding="utf-8")
        codex = self.home / ".codex" / "sessions" / "2026" / "10"
        codex.mkdir(parents=True)
        meta = {"type": "session_meta", "payload": {"id": "codex-id", "cwd": str(self.repo), "text": "private"}}
        (codex / "one.jsonl").write_text(json.dumps(meta) + "\nNOT JSON: PRIVATE MESSAGE", encoding="utf-8")
        (codex / "wrong.jsonl").write_text(json.dumps({"type": "session_meta", "payload": {"id": "wrong", "cwd": str(self.home)}}), encoding="utf-8")
        (codex / "bad.jsonl").write_text("bad first line\n" + json.dumps(meta), encoding="utf-8")
        with patch.object(view.cloud_lane, "sessions", return_value=[
                {"session_id": "cloud-id", "repo": str(self.repo), "task": "private", "url": "https://claude.ai/code/cloud-id", "at": "now"},
                {"session_id": "other", "repo": str(self.home)}]):
            row = self.projects()[0]
        self.assertEqual([s["id"] for s in row["claude_sessions"]], ["claude-id"])
        self.assertEqual([s["id"] for s in row["codex_sessions"]], ["codex-id"])
        self.assertEqual([s["session_id"] for s in row["cloud_sessions"]], ["cloud-id"])
        self.assertNotIn("private", json.dumps(row).lower())
        self.assertTrue(row["codex_sessions"][0]["modified_at"])

    def test_git_without_upstream_and_failed_git(self):
        self.runner.side_effect = lambda argv, **kw: SimpleNamespace(returncode=1 if argv[1] == "rev-list" else 0,
                                                                  stdout="main" if argv[1] == "rev-parse" else "")
        git = self.projects()[0]["git"]
        self.assertIsNone(git["ahead"])
        self.assertEqual(git["dirty"], 0)
        self.runner.side_effect = OSError("unavailable")
        self.assertIsNone(self.projects()[0]["git"])

    def test_project_path_requires_registered_existing_checkout(self):
        with patch.object(view.registry, "get_project", return_value=self.entry):
            self.assertEqual(view.project_path("work"), self.repo.resolve())
        with patch.object(view.registry, "get_project", return_value={"path": None}), self.assertRaises(ValueError):
            view.project_path("missing")

    def test_resume_commands_use_new_console_no_shell(self):
        for kind, prefix in [("claude", ["claude", "--resume"]), ("codex", ["codex", "resume"]), ("cloud", ["claude", "--teleport"])]:
            with self.subTest(kind=kind):
                popen = Mock()
                # The executable is resolved to its full path (npm .CMD shims).
                with patch.object(view.shutil, "which", side_effect=lambda name: f"C:/npm/{name}.CMD"):
                    out = view.resume_command(kind, "session-1", self.repo, popen=popen)
                self.assertTrue(out["opened"])
                self.assertEqual(popen.call_args.args[0], [f"C:/npm/{prefix[0]}.CMD", *prefix[1:], "session-1"])
                self.assertEqual(popen.call_args.kwargs["cwd"], str(self.repo.resolve()))
                self.assertIn("creationflags", popen.call_args.kwargs)
                self.assertNotIn("shell", popen.call_args.kwargs)

    def test_resume_rejects_option_injection_and_missing_path(self):
        popen = Mock()
        for kind, id, path in [("bad", "id", self.repo), ("claude", "--help", self.repo),
                               ("codex", "id & command", self.repo), ("cloud", "id", self.home / "missing")]:
            with self.subTest(kind=kind, id=id), self.assertRaises(ValueError):
                view.resume_command(kind, id, path, popen=popen)
        popen.assert_not_called()


if __name__ == "__main__":
    unittest.main()
