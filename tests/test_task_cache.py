"""Tests for orchestrator task cache module."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.orchestrator import task_cache  # noqa: E402


class NormalizeGoalTests(unittest.TestCase):
    """Tests for normalize_goal function."""

    def test_strips_leading_and_trailing_whitespace(self) -> None:
        """Goal text is stripped of leading and trailing whitespace."""
        self.assertEqual(task_cache.normalize_goal("  hello world  "), "hello world")
        self.assertEqual(task_cache.normalize_goal("\t\n  test  \n\t"), "test")

    def test_collapses_internal_whitespace_runs(self) -> None:
        """Multiple internal whitespace characters collapse to single space."""
        self.assertEqual(task_cache.normalize_goal("hello   world"), "hello world")
        self.assertEqual(task_cache.normalize_goal("hello\t\n  world"), "hello world")
        self.assertEqual(task_cache.normalize_goal("one    two    three"), "one two three")

    def test_empty_string_remains_empty(self) -> None:
        """Empty or whitespace-only strings normalize to empty string."""
        self.assertEqual(task_cache.normalize_goal(""), "")
        self.assertEqual(task_cache.normalize_goal("   "), "")
        self.assertEqual(task_cache.normalize_goal("\t\n"), "")


class TaskCacheKeyTests(unittest.TestCase):
    """Tests for task_cache_key function."""

    def test_key_is_stable_sha256_hex(self) -> None:
        """Key is a valid hex sha256 string."""
        key = task_cache.task_cache_key(
            goal="test goal", scope=["a.txt"], base_files={"a.txt": "abc123"}, validators=[], role="implementer"
        )
        self.assertIsInstance(key, str)
        self.assertEqual(len(key), 64)
        self.assertTrue(all(c in "0123456789abcdef" for c in key))

    def test_key_stable_under_scope_reordering(self) -> None:
        """Key is identical regardless of scope order (normalized to sorted)."""
        key1 = task_cache.task_cache_key(
            goal="test",
            scope=["z.txt", "a.txt", "m.txt"],
            base_files={"a.txt": "1", "m.txt": "2", "z.txt": "3"},
            validators=[],
            role="implementer",
        )
        key2 = task_cache.task_cache_key(
            goal="test",
            scope=["a.txt", "z.txt", "m.txt"],
            base_files={"m.txt": "2", "z.txt": "3", "a.txt": "1"},
            validators=[],
            role="implementer",
        )
        self.assertEqual(key1, key2)

    def test_key_stable_under_goal_whitespace_changes(self) -> None:
        """Key is identical when goal differs only in whitespace."""
        key1 = task_cache.task_cache_key(
            goal="  implement   feature  ", scope=["a.txt"], base_files={"a.txt": "x"}, validators=[], role="implementer"
        )
        key2 = task_cache.task_cache_key(
            goal="implement feature", scope=["a.txt"], base_files={"a.txt": "x"}, validators=[], role="implementer"
        )
        self.assertEqual(key1, key2)

    def test_key_changes_when_goal_content_differs(self) -> None:
        """Key differs when goal words differ."""
        key1 = task_cache.task_cache_key(
            goal="fix bug", scope=["a.txt"], base_files={"a.txt": "x"}, validators=[], role="implementer"
        )
        key2 = task_cache.task_cache_key(
            goal="add feature", scope=["a.txt"], base_files={"a.txt": "x"}, validators=[], role="implementer"
        )
        self.assertNotEqual(key1, key2)

    def test_key_changes_when_base_files_differ(self) -> None:
        """Key differs when base file hashes differ."""
        key1 = task_cache.task_cache_key(
            goal="test", scope=["a.txt"], base_files={"a.txt": "hash1"}, validators=[], role="implementer"
        )
        key2 = task_cache.task_cache_key(
            goal="test", scope=["a.txt"], base_files={"a.txt": "hash2"}, validators=[], role="implementer"
        )
        self.assertNotEqual(key1, key2)

    def test_key_changes_when_file_is_added_or_removed(self) -> None:
        """Key differs when scope files are added or removed."""
        key1 = task_cache.task_cache_key(
            goal="test", scope=["a.txt", "b.txt"], base_files={"a.txt": "1", "b.txt": "2"}, validators=[], role="implementer"
        )
        key2 = task_cache.task_cache_key(
            goal="test", scope=["a.txt"], base_files={"a.txt": "1"}, validators=[], role="implementer"
        )
        self.assertNotEqual(key1, key2)

    def test_key_changes_when_validator_changes(self) -> None:
        """Key differs when validators differ."""
        key1 = task_cache.task_cache_key(
            goal="test", scope=["a.txt"], base_files={"a.txt": "x"}, validators=["pytest"], role="implementer"
        )
        key2 = task_cache.task_cache_key(
            goal="test", scope=["a.txt"], base_files={"a.txt": "x"}, validators=["mypy"], role="implementer"
        )
        self.assertNotEqual(key1, key2)

    def test_key_changes_when_validator_order_changes(self) -> None:
        """Key differs when validator order changes."""
        key1 = task_cache.task_cache_key(
            goal="test", scope=["a.txt"], base_files={"a.txt": "x"}, validators=["pytest", "mypy"], role="implementer"
        )
        key2 = task_cache.task_cache_key(
            goal="test", scope=["a.txt"], base_files={"a.txt": "x"}, validators=["mypy", "pytest"], role="implementer"
        )
        self.assertNotEqual(key1, key2)

    def test_key_changes_when_role_changes(self) -> None:
        """Key differs when role changes."""
        key1 = task_cache.task_cache_key(
            goal="test", scope=["a.txt"], base_files={"a.txt": "x"}, validators=[], role="implementer"
        )
        key2 = task_cache.task_cache_key(
            goal="test", scope=["a.txt"], base_files={"a.txt": "x"}, validators=[], role="test_author"
        )
        self.assertNotEqual(key1, key2)

    def test_key_handles_null_base_files(self) -> None:
        """Key handles paths that don't exist (null) in base_files."""
        key = task_cache.task_cache_key(
            goal="test", scope=["a.txt", "b.txt"], base_files={"a.txt": "hash", "b.txt": None}, validators=[], role="implementer"
        )
        self.assertIsInstance(key, str)
        self.assertEqual(len(key), 64)


class EligibleForRecordTests(unittest.TestCase):
    """Tests for eligible_for_record function."""

    def test_rejects_wrong_role(self) -> None:
        """Rejects when role is not implementer or test_author."""
        node = {"role": "reviewer", "execution_path": "model", "scope": ["a.txt"]}
        review = {"verdict": "approved", "findings": []}
        self.assertFalse(task_cache.eligible_for_record(node, review, ["a.txt"]))

        node = {"role": "unknown", "execution_path": "model", "scope": ["a.txt"]}
        self.assertFalse(task_cache.eligible_for_record(node, review, ["a.txt"]))

    def test_rejects_deterministic_path(self) -> None:
        """Rejects when execution_path is not 'model'."""
        node = {"role": "implementer", "execution_path": "deterministic", "scope": ["a.txt"]}
        review = {"verdict": "approved", "findings": []}
        self.assertFalse(task_cache.eligible_for_record(node, review, ["a.txt"]))

        node = {"role": "implementer", "execution_path": "skill", "scope": ["a.txt"]}
        self.assertFalse(task_cache.eligible_for_record(node, review, ["a.txt"]))

    def test_rejects_when_review_is_none(self) -> None:
        """Rejects when review is None."""
        node = {"role": "implementer", "execution_path": "model", "scope": ["a.txt"]}
        self.assertFalse(task_cache.eligible_for_record(node, None, ["a.txt"]))

    def test_rejects_non_approved_verdict(self) -> None:
        """Rejects when review verdict is not 'approved'."""
        node = {"role": "implementer", "execution_path": "model", "scope": ["a.txt"]}
        review = {"verdict": "rejected", "findings": []}
        self.assertFalse(task_cache.eligible_for_record(node, review, ["a.txt"]))

        review = {"verdict": "pending", "findings": []}
        self.assertFalse(task_cache.eligible_for_record(node, review, ["a.txt"]))

    def test_rejects_empty_patch_paths(self) -> None:
        """Rejects when patch_paths is empty."""
        node = {"role": "implementer", "execution_path": "model", "scope": ["a.txt"]}
        review = {"verdict": "approved", "findings": []}
        self.assertFalse(task_cache.eligible_for_record(node, review, []))

    def test_rejects_out_of_scope_patch_path(self) -> None:
        """Rejects when any patch path is not in node scope."""
        node = {"role": "implementer", "execution_path": "model", "scope": ["a.txt", "b.txt"]}
        review = {"verdict": "approved", "findings": []}
        self.assertFalse(task_cache.eligible_for_record(node, review, ["a.txt", "c.txt"]))

        node = {"role": "implementer", "execution_path": "model", "scope": ["a.txt"]}
        self.assertFalse(task_cache.eligible_for_record(node, review, ["b.txt"]))

    def test_rejects_open_material_findings(self) -> None:
        """Rejects when review has an open material finding."""
        node = {"role": "implementer", "execution_path": "model", "scope": ["a.txt"]}
        review = {
            "verdict": "approved",
            "findings": [{"severity": "material", "state": "open"}],
        }
        self.assertFalse(task_cache.eligible_for_record(node, review, ["a.txt"]))

    def test_accepts_resolved_material_findings(self) -> None:
        """Accepts when material findings are all resolved."""
        node = {"role": "implementer", "execution_path": "model", "scope": ["a.txt"]}
        review = {
            "verdict": "approved",
            "findings": [{"severity": "material", "state": "resolved"}],
        }
        self.assertTrue(task_cache.eligible_for_record(node, review, ["a.txt"]))

    def test_accepts_non_material_open_findings(self) -> None:
        """Accepts when open findings are non-material."""
        node = {"role": "implementer", "execution_path": "model", "scope": ["a.txt"]}
        review = {
            "verdict": "approved",
            "findings": [{"severity": "info", "state": "open"}],
        }
        self.assertTrue(task_cache.eligible_for_record(node, review, ["a.txt"]))

    def test_accepts_valid_implementer(self) -> None:
        """Accepts a valid implementer record."""
        node = {"role": "implementer", "execution_path": "model", "scope": ["a.txt", "b.txt"]}
        review = {"verdict": "approved", "findings": []}
        self.assertTrue(task_cache.eligible_for_record(node, review, ["a.txt", "b.txt"]))

    def test_accepts_valid_test_author(self) -> None:
        """Accepts a valid test_author record."""
        node = {"role": "test_author", "execution_path": "model", "scope": ["test_a.py"]}
        review = {"verdict": "approved", "findings": []}
        self.assertTrue(task_cache.eligible_for_record(node, review, ["test_a.py"]))

    def test_accepts_subset_of_scope_paths(self) -> None:
        """Accepts when patch_paths are a subset of node scope."""
        node = {"role": "implementer", "execution_path": "model", "scope": ["a.txt", "b.txt", "c.txt"]}
        review = {"verdict": "approved", "findings": []}
        self.assertTrue(task_cache.eligible_for_record(node, review, ["a.txt", "b.txt"]))


class TaskCacheStoreTests(unittest.TestCase):
    """Tests for TaskCacheStore class."""

    def setUp(self) -> None:
        """Create a temporary directory for each test."""
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.store = task_cache.TaskCacheStore(self.root)
        self.addCleanup(self.tmp.cleanup)

    def test_lookup_returns_none_for_missing_key(self) -> None:
        """lookup returns None when key doesn't exist."""
        result = self.store.lookup("nonexistent_key")
        self.assertIsNone(result)

    def test_lookup_returns_none_for_corrupt_file(self) -> None:
        """lookup returns None when file is corrupt JSON."""
        key = "test_key"
        (self.root / f"{key}.json").write_text("{invalid json}", encoding="utf-8")
        result = self.store.lookup(key)
        self.assertIsNone(result)

    def test_lookup_returns_none_for_non_dict_entry(self) -> None:
        """lookup returns None when JSON is valid but not a dict."""
        key = "test_key"
        (self.root / f"{key}.json").write_text('["this", "is", "a", "list"]', encoding="utf-8")
        result = self.store.lookup(key)
        self.assertIsNone(result)

        key2 = "test_key2"
        (self.root / f"{key2}.json").write_text('"just a string"', encoding="utf-8")
        result = self.store.lookup(key2)
        self.assertIsNone(result)

    def test_lookup_returns_none_for_mismatched_key(self) -> None:
        """lookup returns None when entry key doesn't match the requested key."""
        key = "test_key"
        wrong_key = "wrong_key"
        entry = {
            "schema": "personal-agent/orchestrator-task-cache/v1",
            "policy_version": task_cache.TASK_CACHE_POLICY_VERSION,
            "key": wrong_key,
            "patch": "test patch",
            "validator_evidence": [],
            "metadata": {},
        }
        (self.root / f"{key}.json").write_text(json.dumps(entry), encoding="utf-8")
        result = self.store.lookup(key)
        self.assertIsNone(result)

    def test_lookup_returns_none_for_wrong_policy_version(self) -> None:
        """lookup returns None when policy_version doesn't match."""
        key = "test_key"
        entry = {
            "schema": "personal-agent/orchestrator-task-cache/v1",
            "policy_version": 999,
            "key": key,
            "patch": "test patch",
            "validator_evidence": [],
            "metadata": {},
        }
        (self.root / f"{key}.json").write_text(json.dumps(entry), encoding="utf-8")
        result = self.store.lookup(key)
        self.assertIsNone(result)

    def test_record_creates_file_atomically(self) -> None:
        """record writes file atomically and returns the path."""
        key = "test_key"
        patch = "diff test"
        evidence = [{"command": "pytest", "passed": True}]
        meta = {"run_id": "run123", "node_id": "node1"}

        path = self.store.record(key, patch, evidence, meta)

        self.assertTrue(path.exists())
        self.assertEqual(path, self.root / f"{key}.json")

    def test_store_round_trips(self) -> None:
        """Record and lookup returns the same data."""
        key = "test_key"
        patch = "--- a/file.txt\n+++ b/file.txt"
        evidence = [{"command": "pytest -v", "passed": True}, {"command": "mypy", "passed": False}]
        meta = {"run_id": "run_abc", "node_id": "node_xyz", "created_at": "2026-10-04T12:00:00Z"}

        self.store.record(key, patch, evidence, meta)
        result = self.store.lookup(key)

        self.assertIsNotNone(result)
        self.assertEqual(result["key"], key)
        self.assertEqual(result["patch"], patch)
        self.assertEqual(result["validator_evidence"], evidence)
        self.assertEqual(result["metadata"], meta)
        self.assertEqual(result["policy_version"], task_cache.TASK_CACHE_POLICY_VERSION)

    def test_lookup_returns_entry_after_record(self) -> None:
        """Recorded entry can be looked up."""
        key = "my_key"
        patch = "test patch content"
        evidence = []
        meta = {}

        self.store.record(key, patch, evidence, meta)
        entry = self.store.lookup(key)

        self.assertIsNotNone(entry)
        self.assertEqual(entry["patch"], patch)

    def test_record_does_not_overwrite_existing_entry(self) -> None:
        """Recording twice with same key preserves first entry."""
        key = "shared_key"
        first_patch = "first patch"
        second_patch = "second patch"

        self.store.record(key, first_patch, [], {})
        first_entry = self.store.lookup(key)

        self.store.record(key, second_patch, [], {})
        second_entry = self.store.lookup(key)

        self.assertEqual(first_entry["patch"], first_patch)
        self.assertEqual(second_entry["patch"], first_patch)

    def test_record_overwrites_corrupt_entry(self) -> None:
        """record() replaces corrupt entries instead of skipping."""
        key = "corrupt_key"
        (self.root / f"{key}.json").write_text("{invalid json}", encoding="utf-8")

        patch = "valid patch"
        evidence = []
        meta = {}

        path = self.store.record(key, patch, evidence, meta)
        entry = self.store.lookup(key)

        self.assertIsNotNone(entry)
        self.assertEqual(entry["patch"], patch)

    def test_record_overwrites_wrong_policy_version(self) -> None:
        """record() replaces entries with wrong policy_version."""
        key = "policy_key"
        old_entry = {
            "schema": "personal-agent/orchestrator-task-cache/v1",
            "policy_version": 999,
            "key": key,
            "patch": "old patch",
            "validator_evidence": [],
            "metadata": {},
        }
        (self.root / f"{key}.json").write_text(json.dumps(old_entry), encoding="utf-8")

        new_patch = "new patch"
        path = self.store.record(key, new_patch, [], {})
        entry = self.store.lookup(key)

        self.assertIsNotNone(entry)
        self.assertEqual(entry["patch"], new_patch)
        self.assertEqual(entry["policy_version"], task_cache.TASK_CACHE_POLICY_VERSION)

    def test_multiple_entries_coexist(self) -> None:
        """Multiple different keys can be stored and retrieved independently."""
        key1 = "key1"
        key2 = "key2"
        patch1 = "patch 1"
        patch2 = "patch 2"

        self.store.record(key1, patch1, [], {})
        self.store.record(key2, patch2, [], {})

        entry1 = self.store.lookup(key1)
        entry2 = self.store.lookup(key2)

        self.assertIsNotNone(entry1)
        self.assertIsNotNone(entry2)
        self.assertEqual(entry1["patch"], patch1)
        self.assertEqual(entry2["patch"], patch2)


if __name__ == "__main__":
    unittest.main()
