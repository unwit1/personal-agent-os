"""Repository chooser: discovery and creation (local temp folders only)."""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.orchestrator import repos  # noqa: E402


def git(cwd: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)


def make_repo(path: Path) -> Path:
    path.mkdir(parents=True)
    git(path, "init", "-b", "main")
    git(path, "config", "user.email", "test@example.test")
    git(path, "config", "user.name", "Test")
    (path / "a.txt").write_text("a", encoding="utf-8")
    git(path, "add", "a.txt")
    git(path, "commit", "-m", "first")
    return path


class RepoChooserTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="agent-os-repos-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def test_lists_main_checkouts_once_and_marks_registered_and_non_git_projects(self) -> None:
        root = self.tmp / "GitHub"
        alpha = make_repo(root / "alpha")
        make_repo(root / "group" / "beta")
        (root / "alpha-extra").mkdir()
        (root / "alpha-extra" / ".git").write_text("gitdir: elsewhere", encoding="utf-8")  # a worktree checkout
        make_repo(root / "alpha" / "node_modules" / "vendored")
        plain = self.tmp / "Projects" / "Scans"
        plain.mkdir(parents=True)
        registered = [{"id": "alpha-app", "path": str(alpha)}, {"id": "alpha-model", "path": str(alpha)}, {"id": "scans", "path": str(plain)}]
        items = repos.list_repositories([root], registered)
        self.assertEqual(sorted(item["name"] for item in items if item["git"]), ["alpha", "beta"])
        by_name = {item["name"]: item for item in items}
        self.assertEqual(by_name["alpha"]["project"], "alpha-app", "the first registered entry names a shared folder")
        self.assertEqual((by_name["alpha"]["branch"], bool(by_name["alpha"]["last_commit"])), ("main", True))
        self.assertEqual((by_name["Scans"]["git"], by_name["Scans"]["project"]), (False, "scans"))

    def test_create_repository_makes_a_committed_repo_and_refuses_bad_or_taken_names(self) -> None:
        with mock.patch.dict("os.environ", {"GIT_AUTHOR_NAME": "T", "GIT_AUTHOR_EMAIL": "t@x.test", "GIT_COMMITTER_NAME": "T", "GIT_COMMITTER_EMAIL": "t@x.test"}):
            created = repos.create_repository("My Tool", self.tmp, description="Does a thing")
        target = self.tmp / "My Tool"
        self.assertEqual((created["path"], created["branch"], created["github"]), (str(target), "main", None))
        self.assertIn("Does a thing", (target / "README.md").read_text(encoding="utf-8"))
        self.assertTrue(created["last_commit"])
        for bad in ("", "../escape", "a/b", "x" * 90):
            with self.assertRaises(ValueError):
                repos.create_repository(bad, self.tmp)
        with self.assertRaises(ValueError):
            repos.create_repository("My Tool", self.tmp)

    def test_github_publish_is_opt_in_and_reports_a_missing_cli(self) -> None:
        with mock.patch.dict("os.environ", {"GIT_AUTHOR_NAME": "T", "GIT_AUTHOR_EMAIL": "t@x.test", "GIT_COMMITTER_NAME": "T", "GIT_COMMITTER_EMAIL": "t@x.test"}), \
             mock.patch.object(repos, "publish_to_github", wraps=repos.publish_to_github) as publish, mock.patch.object(repos.shutil, "which", return_value=None):
            local = repos.create_repository("local-only", self.tmp)
            self.assertEqual(publish.call_count, 0)
            published = repos.create_repository("wants-github", self.tmp, github=True)
        self.assertIsNone(local["github"])
        self.assertEqual(published["github"]["ok"], False)
        self.assertIn("not installed", published["github"]["message"])

    def test_server_routes(self) -> None:
        from agent_os.orchestrator import server

        api = server.Api.__new__(server.Api)
        with mock.patch.object(repos, "list_repositories", return_value=[{"name": "x"}]), mock.patch.object(repos, "default_roots", return_value=[self.tmp]):
            self.assertEqual(api.get("/api/repos", {})["repositories"], [{"name": "x"}])
        with mock.patch.object(repos, "create_repository", return_value={"name": "new"}) as create:
            self.assertEqual(api.post("/api/repos", {"name": "new", "github": True}), {"name": "new"})
        create.assert_called_once_with("new", None, description="", github=True)


if __name__ == "__main__":
    unittest.main()
