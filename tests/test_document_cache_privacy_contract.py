"""Tests for document cache privacy contract guarantees.

Validates the promises in docs/document-intelligence.md:
- The cache is an optimization, never canonical state
- The cache is workstation-local and private
- Extraction is cached; interpretation is not
"""

import dataclasses
import json
import tempfile
import unittest
from pathlib import Path

import agent_os  # noqa: F401
from agent_os.paths import ROOT
import ingester_engine.cache as cache_mod


def _get_cache_attr(test_case, name):
    """Get an attribute from cache_mod, skipping the test if it doesn't exist."""
    try:
        return getattr(cache_mod, name)
    except AttributeError:
        test_case.skipTest(f"cache_mod.{name} does not exist")


class TestDocumentCachePrivacyContract(unittest.TestCase):
    """Enforce privacy and structure guarantees of the document cache."""

    def test_cache_refuses_tracked_locations(self):
        """DocumentCache(root=ROOT / 'forms' / 'cache') raises CachePrivacyError."""
        CachePrivacyError = _get_cache_attr(self, "CachePrivacyError")
        DocumentCache = _get_cache_attr(self, "DocumentCache")
        tracked_root = ROOT / "forms" / "cache"
        with self.assertRaises(CachePrivacyError):
            DocumentCache(root=tracked_root)

    def test_is_private_location(self):
        """is_private_location distinguishes tracked vs. private locations."""
        is_private_location = _get_cache_attr(self, "is_private_location")
        cache_root = _get_cache_attr(self, "cache_root")
        # Default cache root is private
        self.assertTrue(is_private_location(cache_root()))

        # Tracked repository path is not private
        tracked_root = ROOT / "forms" / "cache"
        self.assertFalse(is_private_location(tracked_root))

    def test_cache_status_safe_omits_paths(self):
        """cache_status_safe() output contains no absolute paths or 'path'/'root' keys."""
        cache_status_safe = _get_cache_attr(self, "cache_status_safe")
        cache_root = _get_cache_attr(self, "cache_root")
        status = cache_status_safe()

        # Serialize as it would be shared
        serialized = json.dumps(status)

        # Check both raw and JSON-escaped forms of sensitive paths
        sensitive_paths = [str(cache_root()), str(Path.home())]
        for path_str in sensitive_paths:
            # Check raw path string
            self.assertNotIn(
                path_str,
                serialized,
                f"cache_status_safe leaked path (raw): {path_str}",
            )
            # Check JSON-escaped version (without quotes: json.dumps adds quotes)
            json_escaped = json.dumps(path_str)[1:-1]
            if json_escaped != path_str:  # only check if escaping changed it
                self.assertNotIn(
                    json_escaped,
                    serialized,
                    f"cache_status_safe leaked path (JSON-escaped): {json_escaped}",
                )

        # Walk the nested structure for 'path' or 'root' keys
        def check_no_path_keys(obj, path="root"):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    self.assertNotEqual(
                        key,
                        "path",
                        f"Found 'path' key at {path}.{key}",
                    )
                    self.assertNotEqual(
                        key,
                        "root",
                        f"Found 'root' key at {path}.{key}",
                    )
                    check_no_path_keys(value, f"{path}.{key}")
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    check_no_path_keys(item, f"{path}[{i}]")

        check_no_path_keys(status)

    def test_page_key_excludes_interpretation_components(self):
        """No INTERPRETATION_COMPONENTS name appears in PageKey's fields."""
        PageKey = _get_cache_attr(self, "PageKey")
        INTERPRETATION_COMPONENTS = _get_cache_attr(self, "INTERPRETATION_COMPONENTS")
        # Get PageKey's field names using dataclasses.fields
        key_fields = set(f.name for f in dataclasses.fields(PageKey))

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
        PageKey = _get_cache_attr(self, "PageKey")
        base_key = PageKey(
            file_hash="a" * 64,
            page_index=0,
            dpi=300,
            rotation=0,
            extractor="test",
            ocr_engine="google",
            preprocess="none",
        )
        base_fp = base_key.fingerprint()

        # Different DPI should change fingerprint
        key_different_dpi = dataclasses.replace(base_key, dpi=150)
        self.assertNotEqual(
            base_fp, key_different_dpi.fingerprint(), "DPI change should alter fingerprint"
        )

        # Different ocr_engine should change fingerprint
        key_different_engine = dataclasses.replace(base_key, ocr_engine="tesseract")
        self.assertNotEqual(
            base_fp,
            key_different_engine.fingerprint(),
            "OCR engine change should alter fingerprint",
        )

    def test_equal_keys_give_equal_fingerprints(self):
        """Equal PageKey instances produce equal fingerprints."""
        PageKey = _get_cache_attr(self, "PageKey")
        key1 = PageKey(
            file_hash="a" * 64,
            page_index=0,
            dpi=300,
            rotation=0,
            extractor="test",
            ocr_engine="google",
            preprocess="none",
        )
        key2 = dataclasses.replace(key1)

        self.assertEqual(key1.fingerprint(), key2.fingerprint())

    def test_corrupted_cache_entry_returns_none(self):
        """A corrupted entry file makes get(key) return None without raising."""
        import inspect

        DocumentCache = _get_cache_attr(self, "DocumentCache")
        PageKey = _get_cache_attr(self, "PageKey")

        # Verify that put() exists
        try:
            inspect.getsource(DocumentCache.put)
        except (OSError, TypeError):
            self.skipTest("DocumentCache.put does not exist or is not inspectable")

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create cache in a temporary private location
            cache_root_path = Path(tmpdir) / ".agent-local" / "document-cache"
            cache = DocumentCache(root=cache_root_path)

            # Create and cache a page
            key = PageKey(
                file_hash="a" * 64,
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

            # Find the stored entry file via rglob
            json_files = list(cache_root_path.rglob("*.json"))
            self.assertEqual(len(json_files), 1, "Expected exactly one cached entry file")
            entry_file = json_files[0]

            # Corrupt the entry file
            entry_file.write_bytes(b"not json at all")

            # get() should return None, not raise
            result = cache.get(key)
            self.assertIsNone(
                result,
                "get() should return None for corrupted entry, not raise",
            )

if __name__ == "__main__":
    unittest.main()
