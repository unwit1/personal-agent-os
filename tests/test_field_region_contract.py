from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import agent_os  # noqa: F401

from ingester_engine.cache import DocumentCache, FieldRegion, PageKey, extract_field_region


class TestFieldRegionContract(unittest.TestCase):
    """Tests for the field-region OCR seam consumed from Ingester Engine."""

    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.cache_root = Path(self.tempdir.name) / ".agent-local" / "document-cache"
        self.ocr_call_count = 0

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def _make_ocr(self) -> tuple[callable, callable]:
        """Create an OCR callable that counts calls and a callable to get the count."""
        def ocr(image) -> str | None:
            self.ocr_call_count += 1
            return "SYNTHETIC FIELD"

        def get_count() -> int:
            return self.ocr_call_count

        return ocr, get_count

    def _make_render_and_crop(self):
        """Create render_page and crop_region callables for synthetic testing."""
        def render_page(dpi: int, rotation: int):
            return {"dpi": dpi, "rotation": rotation, "type": "synthetic_page"}

        def crop_region(page_image, region: FieldRegion):
            return {"region": region.as_dict(), "type": "synthetic_crop"}

        return render_page, crop_region

    def test_field_region_rejects_invalid_coordinates_out_of_range(self) -> None:
        """FieldRegion validation rejects coordinates outside [0, 1]."""
        invalid_cases = [
            {"left": 0.0, "top": 0.0, "right": 1.5, "bottom": 1.0},
            {"left": -0.1, "top": 0.0, "right": 1.0, "bottom": 1.0},
        ]
        for kwargs in invalid_cases:
            with self.subTest(kwargs=kwargs):
                with self.assertRaises(ValueError):
                    FieldRegion(**kwargs)

    def test_field_region_rejects_invalid_geometry_zero_width(self) -> None:
        """FieldRegion validation rejects zero or negative width."""
        invalid_cases = [
            {"left": 0.5, "top": 0.0, "right": 0.5, "bottom": 1.0},
            {"left": 0.7, "top": 0.0, "right": 0.3, "bottom": 1.0},
        ]
        for kwargs in invalid_cases:
            with self.subTest(kwargs=kwargs):
                with self.assertRaises(ValueError):
                    FieldRegion(**kwargs)

    def test_field_region_rejects_invalid_geometry_zero_height(self) -> None:
        """FieldRegion validation rejects zero or negative height."""
        invalid_cases = [
            {"left": 0.0, "top": 0.5, "right": 1.0, "bottom": 0.5},
            {"left": 0.0, "top": 0.7, "right": 1.0, "bottom": 0.3},
        ]
        for kwargs in invalid_cases:
            with self.subTest(kwargs=kwargs):
                with self.assertRaises(ValueError):
                    FieldRegion(**kwargs)

    def test_valid_field_region_creation(self) -> None:
        """FieldRegion accepts valid coordinates."""
        region = FieldRegion(left=0.1, top=0.2, right=0.9, bottom=0.8)
        self.assertEqual(region.left, 0.1)
        self.assertEqual(region.top, 0.2)
        self.assertEqual(region.right, 0.9)
        self.assertEqual(region.bottom, 0.8)

    def test_extract_field_region_first_call_runs_ocr(self) -> None:
        """First call to extract_field_region runs OCR and returns synthetic text."""
        cache = DocumentCache(root=self.cache_root)
        ocr, get_count = self._make_ocr()
        render_page, crop_region = self._make_render_and_crop()

        key = PageKey(file_hash="a" * 64, page_index=0)
        region = FieldRegion(left=0.1, top=0.1, right=0.9, bottom=0.9)

        result = extract_field_region(
            key,
            region,
            render_page=render_page,
            crop_region=crop_region,
            ocr=ocr,
            cache=cache,
        )

        self.assertEqual(get_count(), 1, "OCR should be called once on first extraction")
        self.assertEqual(result["text"], "SYNTHETIC FIELD")
        self.assertEqual(result["extraction_kind"], "field_region")
        self.assertIn("route", result)

    def test_extract_field_region_cache_hit_skips_ocr(self) -> None:
        """Repeat call with same page and region uses cache and skips OCR."""
        cache = DocumentCache(root=self.cache_root)
        ocr, get_count = self._make_ocr()
        render_page, crop_region = self._make_render_and_crop()

        key = PageKey(file_hash="a" * 64, page_index=0)
        region = FieldRegion(left=0.1, top=0.1, right=0.9, bottom=0.9)

        # First call
        result1 = extract_field_region(
            key,
            region,
            render_page=render_page,
            crop_region=crop_region,
            ocr=ocr,
            cache=cache,
        )
        self.assertEqual(get_count(), 1, "First call should run OCR")

        # Second call with same key and region
        result2 = extract_field_region(
            key,
            region,
            render_page=render_page,
            crop_region=crop_region,
            ocr=ocr,
            cache=cache,
        )
        self.assertEqual(get_count(), 1, "Second call should use cache, OCR count unchanged")
        self.assertEqual(result2["text"], "SYNTHETIC FIELD")
        self.assertTrue(result2.get("cached"), "Result should indicate it was cached")

    def test_extract_field_region_different_region_runs_ocr_again(self) -> None:
        """Different region on same page runs OCR again."""
        cache = DocumentCache(root=self.cache_root)
        ocr, get_count = self._make_ocr()
        render_page, crop_region = self._make_render_and_crop()

        key = PageKey(file_hash="a" * 64, page_index=0)
        region1 = FieldRegion(left=0.1, top=0.1, right=0.5, bottom=0.5)
        region2 = FieldRegion(left=0.5, top=0.5, right=0.9, bottom=0.9)

        # First region
        extract_field_region(
            key,
            region1,
            render_page=render_page,
            crop_region=crop_region,
            ocr=ocr,
            cache=cache,
        )
        self.assertEqual(get_count(), 1)

        # Different region on same page
        extract_field_region(
            key,
            region2,
            render_page=render_page,
            crop_region=crop_region,
            ocr=ocr,
            cache=cache,
        )
        self.assertEqual(get_count(), 2, "Different region should trigger OCR again")

    def test_telemetry_counters_match_call_sequence(self) -> None:
        """Telemetry counters match the call sequence: two same region, one different."""
        cache = DocumentCache(root=self.cache_root)
        ocr, _ = self._make_ocr()
        render_page, crop_region = self._make_render_and_crop()

        key = PageKey(file_hash="a" * 64, page_index=0)
        region1 = FieldRegion(left=0.0, top=0.0, right=1.0, bottom=1.0)
        region2 = FieldRegion(left=0.1, top=0.1, right=0.9, bottom=0.9)

        # First call with region1 - OCR runs
        extract_field_region(
            key,
            region1,
            render_page=render_page,
            crop_region=crop_region,
            ocr=ocr,
            cache=cache,
        )

        # Second call with region1 - cache hit, no OCR
        extract_field_region(
            key,
            region1,
            render_page=render_page,
            crop_region=crop_region,
            ocr=ocr,
            cache=cache,
        )

        # Third call with region2 - different region, OCR runs
        extract_field_region(
            key,
            region2,
            render_page=render_page,
            crop_region=crop_region,
            ocr=ocr,
            cache=cache,
        )

        # Assert counters match the sequence
        self.assertEqual(
            cache.telemetry.field_region_pages,
            3,
            "field_region_pages should be 3 (3 calls)",
        )
        self.assertEqual(
            cache.telemetry.field_region_ocr_pages,
            2,
            "field_region_ocr_pages should be 2 (first and third calls)",
        )
        self.assertEqual(
            cache.telemetry.field_region_cache_hits,
            1,
            "field_region_cache_hits should be 1 (second call)",
        )

        # Verify all telemetry counters are integers
        self.assertIsInstance(cache.telemetry.field_region_pages, int)
        self.assertIsInstance(cache.telemetry.field_region_ocr_pages, int)
        self.assertIsInstance(cache.telemetry.field_region_cache_hits, int)

        # Verify telemetry contains no OCR text
        telemetry_str = str(cache.telemetry)
        self.assertNotIn("SYNTHETIC FIELD", telemetry_str)

    def test_extract_field_region_rejects_non_positive_dpi(self) -> None:
        """extract_field_region rejects non-positive DPI values."""
        cache = DocumentCache(root=self.cache_root)
        ocr, _ = self._make_ocr()
        render_page, crop_region = self._make_render_and_crop()

        key = PageKey(file_hash="a" * 64, page_index=0)
        region = FieldRegion(left=0.0, top=0.0, right=1.0, bottom=1.0)

        invalid_dpis = [0, -100]
        for dpi in invalid_dpis:
            with self.subTest(dpi=dpi):
                with self.assertRaises(ValueError):
                    extract_field_region(
                        key,
                        region,
                        render_page=render_page,
                        crop_region=crop_region,
                        ocr=ocr,
                        dpi=dpi,
                        cache=cache,
                    )

    def test_field_region_cache_persists_across_cache_instances(self) -> None:
        """Cache persists across different DocumentCache instances with same root."""
        ocr, get_count = self._make_ocr()
        render_page, crop_region = self._make_render_and_crop()

        key = PageKey(file_hash="a" * 64, page_index=0)
        region = FieldRegion(left=0.1, top=0.1, right=0.9, bottom=0.9)

        # First cache instance
        cache1 = DocumentCache(root=self.cache_root)
        result1 = extract_field_region(
            key,
            region,
            render_page=render_page,
            crop_region=crop_region,
            ocr=ocr,
            cache=cache1,
        )
        self.assertEqual(get_count(), 1, "First call should run OCR")
        self.assertEqual(result1["text"], "SYNTHETIC FIELD")

        # Second cache instance with same root
        cache2 = DocumentCache(root=self.cache_root)
        result2 = extract_field_region(
            key,
            region,
            render_page=render_page,
            crop_region=crop_region,
            ocr=ocr,
            cache=cache2,
        )
        self.assertEqual(get_count(), 1, "OCR call count should stay 1 (cached from disk)")
        self.assertEqual(result2["text"], "SYNTHETIC FIELD")
        self.assertTrue(result2.get("cached"), "Result should indicate it was cached")
        self.assertEqual(
            cache2.telemetry.field_region_cache_hits,
            1,
            "Second cache should report 1 cache hit",
        )

    def test_same_region_different_page_index_runs_ocr(self) -> None:
        """Same region on different page indices runs OCR for each."""
        cache = DocumentCache(root=self.cache_root)
        ocr, get_count = self._make_ocr()
        render_page, crop_region = self._make_render_and_crop()

        region = FieldRegion(left=0.1, top=0.1, right=0.9, bottom=0.9)

        # First page
        key1 = PageKey(file_hash="a" * 64, page_index=0)
        extract_field_region(
            key1,
            region,
            render_page=render_page,
            crop_region=crop_region,
            ocr=ocr,
            cache=cache,
        )
        self.assertEqual(get_count(), 1)

        # Different page index, same file hash
        key2 = PageKey(file_hash="a" * 64, page_index=1)
        extract_field_region(
            key2,
            region,
            render_page=render_page,
            crop_region=crop_region,
            ocr=ocr,
            cache=cache,
        )
        self.assertEqual(get_count(), 2, "Different page index should trigger OCR again")

    def test_same_region_different_file_hash_runs_ocr(self) -> None:
        """Same region on different file hashes runs OCR for each."""
        cache = DocumentCache(root=self.cache_root)
        ocr, get_count = self._make_ocr()
        render_page, crop_region = self._make_render_and_crop()

        region = FieldRegion(left=0.1, top=0.1, right=0.9, bottom=0.9)

        # First file hash
        key1 = PageKey(file_hash="a" * 64, page_index=0)
        extract_field_region(
            key1,
            region,
            render_page=render_page,
            crop_region=crop_region,
            ocr=ocr,
            cache=cache,
        )
        self.assertEqual(get_count(), 1)

        # Different file hash, same page index
        key2 = PageKey(file_hash="b" * 64, page_index=0)
        extract_field_region(
            key2,
            region,
            render_page=render_page,
            crop_region=crop_region,
            ocr=ocr,
            cache=cache,
        )
        self.assertEqual(get_count(), 2, "Different file hash should trigger OCR again")

    def test_extract_field_region_different_dpi_runs_ocr_again(self) -> None:
        """Different DPI on same region and page runs OCR again."""
        cache = DocumentCache(root=self.cache_root)
        ocr, get_count = self._make_ocr()
        render_page, crop_region = self._make_render_and_crop()

        key = PageKey(file_hash="a" * 64, page_index=0)
        region = FieldRegion(left=0.1, top=0.1, right=0.9, bottom=0.9)

        # First call with default DPI (72)
        extract_field_region(
            key,
            region,
            render_page=render_page,
            crop_region=crop_region,
            ocr=ocr,
            dpi=72,
            cache=cache,
        )
        self.assertEqual(get_count(), 1, "First call with DPI 72 should run OCR")

        # Second call with different DPI
        extract_field_region(
            key,
            region,
            render_page=render_page,
            crop_region=crop_region,
            ocr=ocr,
            dpi=96,
            cache=cache,
        )
        self.assertEqual(get_count(), 2, "Different DPI should trigger OCR again")

    def test_cached_result_contains_no_absolute_cache_path(self) -> None:
        """Cached result should not contain absolute cache path."""
        cache = DocumentCache(root=self.cache_root)
        ocr, _ = self._make_ocr()
        render_page, crop_region = self._make_render_and_crop()

        key = PageKey(file_hash="a" * 64, page_index=0)
        region = FieldRegion(left=0.1, top=0.1, right=0.9, bottom=0.9)

        # First call to populate cache
        extract_field_region(
            key,
            region,
            render_page=render_page,
            crop_region=crop_region,
            ocr=ocr,
            cache=cache,
        )

        # Second call to get cached result
        result = extract_field_region(
            key,
            region,
            render_page=render_page,
            crop_region=crop_region,
            ocr=ocr,
            cache=cache,
        )

        self.assertTrue(result.get("cached"), "Result should be marked as cached")
        result_str = str(result)
        # Check all path forms to ensure cache path doesn't leak (accounts for Windows backslashes)
        for path_form in (
            str(self.cache_root),
            repr(str(self.cache_root))[1:-1],
            self.cache_root.as_posix(),
        ):
            self.assertNotIn(
                path_form,
                result_str,
                f"Cached result should not contain absolute cache path: {path_form}",
            )


if __name__ == "__main__":
    unittest.main()
