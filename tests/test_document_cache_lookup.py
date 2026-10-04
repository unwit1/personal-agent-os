from __future__ import annotations

import secrets
import tempfile
import unittest
from pathlib import Path

import agent_os  # noqa: F401

from ingester_engine.cache import DocumentCache, PageKey
from agent_os.execution import cache_lookup_problems, lookup_document_page


class TestCacheLookupProblems(unittest.TestCase):
    """Tests for cache_lookup_problems validation function."""

    def test_invalid_file_hash_too_short(self) -> None:
        """Returns a problem for file_hash that is too short."""
        config = {
            "kind": "document_page",
            "key": {"file_hash": "abc", "page_index": 0},
        }
        problems = cache_lookup_problems(config)
        self.assertTrue(
            any("file_hash" in p for p in problems),
            f"Expected a problem mentioning 'file_hash', got {problems}",
        )

    def test_invalid_file_hash_not_hex(self) -> None:
        """Returns a problem for file_hash with non-hex characters."""
        config = {
            "kind": "document_page",
            "key": {"file_hash": "z" * 64, "page_index": 0},
        }
        problems = cache_lookup_problems(config)
        self.assertTrue(
            any("file_hash" in p for p in problems),
            f"Expected a problem mentioning 'file_hash', got {problems}",
        )

    def test_invalid_page_index_negative(self) -> None:
        """Returns a problem for negative page_index."""
        config = {
            "kind": "document_page",
            "key": {"file_hash": "a" * 64, "page_index": -1},
        }
        problems = cache_lookup_problems(config)
        self.assertTrue(
            any("page_index" in p for p in problems),
            f"Expected a problem mentioning 'page_index', got {problems}",
        )

    def test_invalid_page_index_not_int(self) -> None:
        """Returns a problem for non-integer page_index."""
        config = {
            "kind": "document_page",
            "key": {"file_hash": "a" * 64, "page_index": "0"},
        }
        problems = cache_lookup_problems(config)
        self.assertTrue(
            any("page_index" in p for p in problems),
            f"Expected a problem mentioning 'page_index', got {problems}",
        )

    def test_unsupported_field(self) -> None:
        """Returns a problem for unknown field in key."""
        config = {
            "kind": "document_page",
            "key": {
                "file_hash": "a" * 64,
                "page_index": 0,
                "unknown_field": "value",
            },
        }
        problems = cache_lookup_problems(config)
        self.assertTrue(
            any("unsupported field" in p for p in problems),
            f"Expected a problem mentioning 'unsupported field', got {problems}",
        )

    def test_valid_minimal_key(self) -> None:
        """Returns [] for a valid minimal key."""
        config = {
            "kind": "document_page",
            "key": {"file_hash": "a" * 64, "page_index": 0},
        }
        problems = cache_lookup_problems(config)
        self.assertEqual(problems, [])

    def test_valid_key_with_optional_fields(self) -> None:
        """Returns [] for a valid key with optional fields."""
        config = {
            "kind": "document_page",
            "key": {
                "file_hash": "f" * 64,
                "page_index": 5,
                "dpi": 300,
                "rotation": 90,
                "extractor": "pdf",
                "ocr_engine": "tesseract",
                "preprocess": "binarize",
            },
        }
        problems = cache_lookup_problems(config)
        self.assertEqual(problems, [])


class TestLookupDocumentPage(unittest.TestCase):
    """Tests for lookup_document_page function."""

    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.temp_root = Path(self.tempdir.name)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_raises_value_error_for_invalid_config(self) -> None:
        """Raises ValueError when config has validation problems."""
        config = {
            "kind": "document_page",
            "key": {"file_hash": "invalid", "page_index": -1},
        }
        with self.assertRaises(ValueError):
            lookup_document_page(config, self.temp_root)

    def test_returns_miss_for_nonexistent_entry(self) -> None:
        """Returns hit=False and 'miss' reason for a non-existent entry."""
        file_hash = secrets.token_hex(32)
        config = {
            "kind": "document_page",
            "key": {"file_hash": file_hash, "page_index": 0},
        }
        result = lookup_document_page(config, self.temp_root)

        self.assertFalse(result.hit)
        self.assertEqual(result.reason, "local document cache miss")
        # Verify cache_key matches the PageKey fingerprint
        expected_key = PageKey(file_hash=file_hash, page_index=0)
        self.assertEqual(result.cache_key, expected_key.fingerprint())

    def test_returns_hit_after_writing_to_cache(self) -> None:
        """Returns hit=True after an entry is written to DocumentCache."""
        file_hash = secrets.token_hex(32)
        page_index = 0
        key = PageKey(file_hash=file_hash, page_index=page_index)

        # Write an entry to the cache
        cache_root = self.temp_root / ".agent-local" / "document-cache"
        cache = DocumentCache(root=cache_root)
        payload = {"text": "Test content", "metadata": "Some metadata"}
        cache.put(key, payload)

        # Now look it up
        config = {
            "kind": "document_page",
            "key": {"file_hash": file_hash, "page_index": page_index},
        }
        result = lookup_document_page(config, self.temp_root)

        self.assertTrue(result.hit)
        self.assertEqual(result.reason, "local document cache hit")
        self.assertEqual(result.cache_key, key.fingerprint())

    def test_cache_lookup_result_does_not_expose_content(self) -> None:
        """CacheLookup result does not contain the stored text or temp path."""
        file_hash = secrets.token_hex(32)
        key = PageKey(file_hash=file_hash, page_index=0)

        # Write an entry with sensitive content
        cache_root = self.temp_root / ".agent-local" / "document-cache"
        cache = DocumentCache(root=cache_root)
        sensitive_text = "SENSITIVE_DOCUMENT_CONTENT_12345"
        payload = {"text": sensitive_text, "metadata": "secret"}
        cache.put(key, payload)

        # Look it up
        config = {
            "kind": "document_page",
            "key": {"file_hash": file_hash, "page_index": 0},
        }
        result = lookup_document_page(config, self.temp_root)

        # Verify the result does not contain the sensitive content
        result_str = str(result)
        self.assertNotIn(sensitive_text, result_str)
        self.assertNotIn(str(self.temp_root), result_str)
        self.assertNotIn(str(cache_root), result_str)


if __name__ == "__main__":
    unittest.main()
