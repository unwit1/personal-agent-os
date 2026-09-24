from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.recovery import (
    FORBIDDEN_KEYS,
    IncrementalLedger,
    checkpoint_path,
    create_checkpoint,
    get_checkpoint,
    inspect_recovery,
    list_checkpoints,
    repository_identity,
    resume_recovery,
    stable_project_id,
    working_tree_fingerprint,
)


class RepoFixture(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.repo = Path(self.temp.name) / "repo"
        self.repo.mkdir()
        self.git("init", "-q")
        self.git("config", "user.email", "tests@example.invalid")
        self.git("config", "user.name", "Tests")
        (self.repo / ".gitignore").write_text(".agent-local/\n", encoding="utf-8")
        (self.repo / "tracked.txt").write_text("original\n", encoding="utf-8")
        self.git("add", ".")
        self.git("commit", "-qm", "initial")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def git(self, *args: str) -> str:
        result = subprocess.run(["git", *args], cwd=self.repo, capture_output=True, text=True, check=True)
        return result.stdout.strip()

    def checkpoint(self, **overrides):
        data = {
            "project_id": "fixture-project", "workflow_id": "fixture-workflow", "run_id": "run-1",
            "stage_id": "stage-2", "completed_stages": ["stage-1"],
            "unresolved_work": ["finish stage 2"], "validation_state": {"passed": True},
            "tests_run": [{"command": "unit", "passed": True}], "next_action": "finish stage 2",
            "recommended_capability_class": "balanced", "origin": {"agent": "first-agent"}, "repo": self.repo,
        }
        data.update(overrides)
        return create_checkpoint(**data)


class FingerprintTests(RepoFixture):
    def test_clean_repository_has_empty_inventory(self) -> None:
        fingerprint = working_tree_fingerprint(self.repo)
        self.assertFalse(any(fingerprint["inventory"].values()))

    def test_modified_staged_untracked_deleted_and_renamed_are_detected(self) -> None:
        (self.repo / "tracked.txt").write_text("modified\n", encoding="utf-8")
        (self.repo / "staged.txt").write_text("staged\n", encoding="utf-8")
        self.git("add", "staged.txt")
        (self.repo / "new.txt").write_text("new\n", encoding="utf-8")
        self.git("mv", "tracked.txt", "renamed.txt")
        fingerprint = working_tree_fingerprint(self.repo)
        inventory = fingerprint["inventory"]
        self.assertIn("staged.txt", inventory["staged"])
        self.assertIn("new.txt", inventory["untracked"])
        self.assertTrue(inventory["renamed"])
        self.git("reset", "--", "staged.txt")
        (self.repo / "renamed.txt").unlink()
        fingerprint = working_tree_fingerprint(self.repo)
        self.assertIn("renamed.txt", fingerprint["inventory"]["deleted"])

    def test_content_changes_change_the_fingerprint_without_persisting_content(self) -> None:
        before = working_tree_fingerprint(self.repo)["value"]
        (self.repo / "tracked.txt").write_text("private replacement\n", encoding="utf-8")
        after = working_tree_fingerprint(self.repo)
        self.assertNotEqual(before, after["value"])
        self.assertNotIn("private replacement", json.dumps(after))


class RecoveryTests(RepoFixture):
    def test_clean_and_missing_checkpoint_statuses(self) -> None:
        self.assertEqual(inspect_recovery("fixture-project", repo=self.repo)["status"], "clean_new_task")
        (self.repo / "tracked.txt").write_text("work\n", encoding="utf-8")
        result = inspect_recovery("fixture-project", repo=self.repo)
        self.assertEqual(result["status"], "ambiguous_local_work")
        self.assertFalse(result["safe_to_continue"])

    def test_unchanged_interrupted_work_returns_exact_continuation(self) -> None:
        (self.repo / "tracked.txt").write_text("interrupted\n", encoding="utf-8")
        record = self.checkpoint()
        resumed = resume_recovery("fixture-project", "run-1", self.repo)
        self.assertTrue(resumed["resumed"])
        self.assertEqual(resumed["status"], "interrupted_resumable_task")
        self.assertEqual(resumed["continuation"]["completed_stages"], ["stage-1"])
        self.assertEqual(resumed["continuation"]["current_stage"], "stage-2")
        self.assertEqual(resumed["continuation"]["next_action"], "finish stage 2")
        self.assertEqual(record["newly_created_untracked_files"], [])

    def test_safe_additional_edits_and_conflicting_edits_are_distinguished(self) -> None:
        (self.repo / "tracked.txt").write_text("interrupted\n", encoding="utf-8")
        self.checkpoint()
        (self.repo / "separate.txt").write_text("later\n", encoding="utf-8")
        safe = inspect_recovery("fixture-project", "run-1", self.repo)
        self.assertEqual(safe["status"], "interrupted_task_with_additional_safe_edits")
        self.assertTrue(safe["safe_to_continue"])
        (self.repo / "tracked.txt").write_text("original\n", encoding="utf-8")
        conflict = inspect_recovery("fixture-project", "run-1", self.repo)
        self.assertEqual(conflict["status"], "conflicting_changes_requiring_review")
        self.assertFalse(conflict["safe_to_continue"])

    def test_branch_movement_and_head_advancement_are_external_changes(self) -> None:
        self.checkpoint()
        self.git("checkout", "-qb", "other")
        changed_branch = inspect_recovery("fixture-project", "run-1", self.repo)
        self.assertEqual(changed_branch["status"], "interrupted_task_with_external_changes")
        self.git("checkout", "-q", "master")
        (self.repo / "advance.txt").write_text("advance\n", encoding="utf-8")
        self.git("add", "advance.txt")
        self.git("commit", "-qm", "advance")
        changed_head = inspect_recovery("fixture-project", "run-1", self.repo)
        self.assertEqual(changed_head["status"], "interrupted_task_with_external_changes")

    def test_corrupted_checkpoint_is_reported_not_overwritten(self) -> None:
        self.checkpoint()
        path = checkpoint_path("fixture-project", "run-1", self.repo)
        path.write_text("not json", encoding="utf-8")
        result = inspect_recovery("fixture-project", "run-1", self.repo)
        self.assertEqual(result["status"], "corrupted_checkpoint")
        self.assertEqual(path.read_text(encoding="utf-8"), "not json")

    def test_checkpoint_is_compact_private_and_idempotent(self) -> None:
        first = self.checkpoint()
        second = self.checkpoint(next_action="same stage, new boundary")
        self.assertEqual(first["checkpoint_id"], second["checkpoint_id"])
        payload = json.dumps(second)
        self.assertLess(len(payload.encode("utf-8")), 64 * 1024)
        self.assertFalse(FORBIDDEN_KEYS.intersection(second))
        with self.assertRaises(ValueError):
            self.checkpoint(decisions=["x"], origin={"transcript": "never save"})
        self.assertEqual(len(list_checkpoints("fixture-project", self.repo)), 1)
        self.assertEqual(get_checkpoint("fixture-project", "run-1", self.repo)["next_action"], "same stage, new boundary")


class StableIdentityTests(RepoFixture):
    def test_same_remote_has_the_same_project_identity_in_different_paths(self) -> None:
        bare = Path(self.temp.name) / "origin.git"
        subprocess.run(["git", "init", "--bare", "-q", str(bare)], check=True)
        self.git("remote", "add", "origin", str(bare))
        self.git("push", "-qu", "origin", "master")
        clone = Path(self.temp.name) / "clone"
        subprocess.run(["git", "clone", "-q", str(bare), str(clone)], check=True)
        self.assertEqual(repository_identity(self.repo)["repository_id"], repository_identity(clone)["repository_id"])
        self.assertEqual(stable_project_id(self.repo), stable_project_id(clone))


class IncrementalLedgerTests(RepoFixture):
    def test_duplicate_items_are_skipped_but_changed_versions_reprocess(self) -> None:
        ledger = IncrementalLedger("drive:archive", kind="import", repo=self.repo)
        first = ledger.claim("file-123", "content-a", "extract@1")
        self.assertEqual(first["action"], "process")
        ledger.complete(first["item_id"], cursor="page-1")
        self.assertEqual(ledger.claim("file-123", "content-a", "extract@1")["action"], "skip")
        self.assertEqual(ledger.claim("file-123", "content-b", "extract@1")["action"], "process")
        self.assertEqual(ledger.claim("file-123", "content-b", "extract@2")["action"], "process")

    def test_interrupted_batch_preserves_cursor_and_retries_only_failed_item(self) -> None:
        ledger = IncrementalLedger("mail:inbox", kind="import", repo=self.repo)
        good = ledger.claim("message-1", "a", "parser@1")
        ledger.complete(good["item_id"], cursor="1")
        bad = ledger.claim("message-2", "b", "parser@1")
        ledger.fail(bad["item_id"], "temporary failure")
        self.assertEqual(ledger.claim("message-1", "a", "parser@1")["action"], "skip")
        self.assertEqual(ledger.claim("message-2", "b", "parser@1")["action"], "process")
        status = ledger.status()
        self.assertEqual(status["cursor"], "1")
        self.assertEqual(status["counts"].get("processing"), 1)


class CrossAgentRecoveryTests(RepoFixture):
    def test_agent_identity_does_not_change_recovery_correctness_in_either_direction(self) -> None:
        for source, destination in (("agent-a", "agent-b"), ("agent-b", "agent-a")):
            with self.subTest(source=source, destination=destination):
                (self.repo / "tracked.txt").write_text(f"{source} interrupted work\n", encoding="utf-8")
                (self.repo / "new-artifact.txt").write_text("untracked artifact\n", encoding="utf-8")
                record = self.checkpoint(run_id=f"{source}-run", origin={"agent": source})
                # A fresh process only reads disk; it neither knows nor trusts
                # origin identity when deciding whether state is resumable.
                recovered = resume_recovery("fixture-project", f"{source}-run", self.repo)
                self.assertTrue(recovered["safe_to_continue"], destination)
                self.assertEqual(recovered["continuation"]["completed_stages"], ["stage-1"])
                self.assertEqual(recovered["checkpoint"]["newly_created_untracked_files"], ["new-artifact.txt"])
                self.assertEqual(record["base_commit"], self.git("rev-parse", "HEAD"))
                (self.repo / "new-artifact.txt").unlink()
                (self.repo / "tracked.txt").write_text("original\n", encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
