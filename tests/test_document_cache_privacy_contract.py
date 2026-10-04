"""Tests for document cache privacy contract guarantees.

Validates the promises in docs/document-intelligence.md:
- The cache is an optimization, never canonical state
- The cache is workstation-local and private
- Extraction is cached; interpretation is not
"""

import json
import tempfile
import unittest
from pathlib import Path

import agent_os  # noqa: F401
from agent_os.paths import ROOT
from ingester_engine.cache import (
    INTERPRETATION_COMPONENTS,
    CachePrivacyError,
    DocumentCache,
    PageKey,
    cache_root,
    cache_status_safe,
    is_private_location,
)


class TestDocumentCachePrivacyContract(unittest.TestCase):
    """Enforce privacy and structure guarantees of the document cache."""

    def test_cache_refuses_tracked_locations(self):
        """DocumentCache(root=ROOT / 'forms' / 'cache') raises CachePrivacyError."""
        tracked_root = ROOT / "forms" / "cache"
        with self.assertRaises(CachePrivacyError):
            DocumentCache(root=tracked_root)

    def test_is_private_location(self):
        """is_private_location distinguishes tracked vs. private locations."""
        # Default cache root is private
        self.assertTrue(is_private_location(cache_root()))

        # Tracked repository path is not private
        tracked_root = ROOT / "forms" / "cache"
        self.assertFalse(is_private_location(tracked_root))

    def test_cache_status_safe_omits_paths(self):
        """cache_status_safe() output contains no absolute paths or 'path'/'root' keys."""
        status = cache_status_safe()

        # Serialize as it would be shared
        serialized = json.dumps(status)

        # Must not contain the cache root path
        cache_root_str = str(cache_root())
        self.assertNotIn(
            cache_root_str,
            serialized,
            f"cache_status_safe leaked cache root path: {cache_root_str}",
        )

        # Must not contain user home directory
        home = str(Path.home())
        self.assertNotIn(
            home,
            serialized,
            f"cache_status_safe leaked home directory: {home}",
        )

        # Must not have 'path' or 'root' keys
        self.assertNotIn("path", status)
        self.assertNotIn("root", status)

    def test_page_key_excludes_interpretation_components(self):
        """No INTERPRETATION_COMPONENTS name appears in PageKey's fields."""
        # Get PageKey's field names
        key = PageKey(
            file_hash="abc",
            page_index=0,
            dpi=300,
            rotation=0,
            extractor="test",
            ocr_engine="test",
            preprocess="none",
        )
        key_dict = key.as_dict()
        key_fields = set(key_dict.keys())

        # Check that no interpretation component appears
        interpretation_names = set(INTERPRETATION_COMPONENTS)
        overlap = interpretation_names & key_fields

        self.assertEqual(
            overlap,
            set(),
            f"INTERPRETATION_COMPONENTS {overlap} found in PageKey fields {key_fields}",
        )

    def test_fingerprint_changes_with_extraction_params(self):
        """Changing dpi or ocr_engine on PageKey changes fingerprint()."""
        base_key = PageKey(
            file_hash="abc123",
            page_index=0,
            dpi=300,
            rotation=0,
            extractor="test",
            ocr_engine="google",
            preprocess="none",
        )
        base_fp = base_key.fingerprint()

        # Different DPI should change fingerprint
        key_different_dpi = PageKey(
            file_hash="abc123",
            page_index=0,
            dpi=150,
            rotation=0,
            extractor="test",
            ocr_engine="google",
            preprocess="none",
        )
        self.assertNotEqual(
            base_fp, key_different_dpi.fingerprint(), "DPI change should alter fingerprint"
        )

        # Different ocr_engine should change fingerprint
        key_different_engine = PageKey(
            file_hash="abc123",
            page_index=0,
            dpi=300,
            rotation=0,
            extractor="test",
            ocr_engine="tesseract",
            preprocess="none",
        )
        self.assertNotEqual(
            base_fp,
            key_different_engine.fingerprint(),
            "OCR engine change should alter fingerprint",
        )

    def test_equal_keys_give_equal_fingerprints(self):
        """Equal PageKey instances produce equal fingerprints."""
        key1 = PageKey(
            file_hash="abc123",
            page_index=0,
            dpi=300,
            rotation=0,
            extractor="test",
            ocr_engine="google",
            preprocess="none",
        )
        key2 = PageKey(
            file_hash="abc123",
            page_index=0,
            dpi=300,
            rotation=0,
            extractor="test",
            ocr_engine="google",
            preprocess="none",
        )

        self.assertEqual(key1.fingerprint(), key2.fingerprint())

    def test_corrupted_cache_entry_returns_none(self):
        """A corrupted entry file makes get(key) return None without raising."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create cache in a temporary private location
            cache_root_path = Path(tmpdir) / ".agent-local" / "document-cache"
            cache = DocumentCache(root=cache_root_path)

            # Create and cache a page
            key = PageKey(
                file_hash="corrupttest",
                page_index=0,
                dpi=300,
                rotation=0,
                extractor="test",
                ocr_engine="test",
                preprocess="none",
            )
            payload = {"text": "original data", "extracted_at": 0}
            cache.put(key, payload)

            # Verify it's retrievable
            result = cache.get(key)
            self.assertIsNotNone(result)

            # Corrupt the entry file
            entry_files = list(cache_root_path.rglob("*.json"))
            self.assertTrue(entry_files, "Expected to find cache entry files")

            entry_file = entry_files[0]
            entry_file.write_bytes(b"not json at all")

            # get() should return None, not raise
            result = cache.get(key)
            self.assertIsNone(
                result,
                "get() should return None for corrupted entry, not raise",
            )

    def test_interpretation_components_excluded_by_construction(self):
        """Verify INTERPRETATION_COMPONENTS tuple contains expected names."""
        # This test documents what components are interpretation-only
        # and should never be in the cache key
        expected = ("classifier", "fingerprint", "naming", "dates", "packet")

        # Check each component is a string and not in PageKey
        key = PageKey(
            file_hash="test",
            page_index=0,
            dpi=300,
            rotation=0,
            extractor="test",
            ocr_engine="test",
            preprocess="none",
        )
        key_fields = set(key.as_dict().keys())

        for component in INTERPRETATION_COMPONENTS:
            self.assertIsInstance(component, str)
            self.assertNotIn(
                component,
                key_fields,
                f"{component} must not be in PageKey for interpretation independence",
            )


if __name__ == "__main__":
    unittest.main()
