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
        # Coordinates > 1
        with self.assertRaises(ValueError) as cm:
            FieldRegion(left=0.0, top=0.0, right=1.5, bottom=1.0)
        self.assertIn("between 0 and 1", str(cm.exception))

        # Coordinates < 0
        with self.assertRaises(ValueError) as cm:
            FieldRegion(left=-0.1, top=0.0, right=1.0, bottom=1.0)
        self.assertIn("between 0 and 1", str(cm.exception))

    def test_field_region_rejects_invalid_geometry_zero_width(self) -> None:
        """FieldRegion validation rejects zero or negative width."""
        # left == right (zero width)
        with self.assertRaises(ValueError) as cm:
            FieldRegion(left=0.5, top=0.0, right=0.5, bottom=1.0)
        self.assertIn("positive width", str(cm.exception))

        # left > right (negative width)
        with self.assertRaises(ValueError) as cm:
            FieldRegion(left=0.7, top=0.0, right=0.3, bottom=1.0)
        self.assertIn("positive width", str(cm.exception))

    def test_field_region_rejects_invalid_geometry_zero_height(self) -> None:
        """FieldRegion validation rejects zero or negative height."""
        # top == bottom (zero height)
        with self.assertRaises(ValueError) as cm:
            FieldRegion(left=0.0, top=0.5, right=1.0, bottom=0.5)
        self.assertIn("positive", str(cm.exception))

        # top > bottom (negative height)
        with self.assertRaises(ValueError) as cm:
            FieldRegion(left=0.0, top=0.7, right=1.0, bottom=0.3)
        self.assertIn("positive", str(cm.exception))

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

    def test_telemetry_field_region_pages_incremented(self) -> None:
        """Telemetry field_region_pages counter increments on each call."""
        cache = DocumentCache(root=self.cache_root)
        ocr, _ = self._make_ocr()
        render_page, crop_region = self._make_render_and_crop()

        key = PageKey(file_hash="a" * 64, page_index=0)
        region = FieldRegion(left=0.0, top=0.0, right=1.0, bottom=1.0)

        initial_count = cache.telemetry.field_region_pages
        extract_field_region(
            key,
            region,
            render_page=render_page,
            crop_region=crop_region,
            ocr=ocr,
            cache=cache,
        )
        self.assertEqual(
            cache.telemetry.field_region_pages,
            initial_count + 1,
            "field_region_pages should increment",
        )

    def test_telemetry_field_region_ocr_pages_incremented_on_ocr(self) -> None:
        """Telemetry field_region_ocr_pages increments when OCR runs."""
        cache = DocumentCache(root=self.cache_root)
        ocr, _ = self._make_ocr()
        render_page, crop_region = self._make_render_and_crop()

        key = PageKey(file_hash="a" * 64, page_index=0)
        region = FieldRegion(left=0.0, top=0.0, right=1.0, bottom=1.0)

        initial_count = cache.telemetry.field_region_ocr_pages
        extract_field_region(
            key,
            region,
            render_page=render_page,
            crop_region=crop_region,
            ocr=ocr,
            cache=cache,
        )
        self.assertEqual(
            cache.telemetry.field_region_ocr_pages,
            initial_count + 1,
            "field_region_ocr_pages should increment on OCR",
        )

    def test_telemetry_field_region_cache_hits_incremented_on_hit(self) -> None:
        """Telemetry field_region_cache_hits increments only on cache hits."""
        cache = DocumentCache(root=self.cache_root)
        ocr, _ = self._make_ocr()
        render_page, crop_region = self._make_render_and_crop()

        key = PageKey(file_hash="a" * 64, page_index=0)
        region = FieldRegion(left=0.0, top=0.0, right=1.0, bottom=1.0)

        # First call - not a cache hit
        initial_hits = cache.telemetry.field_region_cache_hits
        extract_field_region(
            key,
            region,
            render_page=render_page,
            crop_region=crop_region,
            ocr=ocr,
            cache=cache,
        )
        self.assertEqual(
            cache.telemetry.field_region_cache_hits,
            initial_hits,
            "No cache hit on first call",
        )

        # Second call - cache hit
        extract_field_region(
            key,
            region,
            render_page=render_page,
            crop_region=crop_region,
            ocr=ocr,
            cache=cache,
        )
        self.assertEqual(
            cache.telemetry.field_region_cache_hits,
            initial_hits + 1,
            "Cache hit should increment counter",
        )

    def test_telemetry_counters_are_integers(self) -> None:
        """Telemetry counters contain only integers."""
        cache = DocumentCache(root=self.cache_root)
        ocr, _ = self._make_ocr()
        render_page, crop_region = self._make_render_and_crop()

        key = PageKey(file_hash="a" * 64, page_index=0)
        region = FieldRegion(left=0.0, top=0.0, right=1.0, bottom=1.0)

        extract_field_region(
            key,
            region,
            render_page=render_page,
            crop_region=crop_region,
            ocr=ocr,
            cache=cache,
        )

        # Verify all telemetry counters are integers
        self.assertIsInstance(cache.telemetry.field_region_pages, int)
        self.assertIsInstance(cache.telemetry.field_region_ocr_pages, int)
        self.assertIsInstance(cache.telemetry.field_region_cache_hits, int)

    def test_extract_field_region_rejects_non_positive_dpi(self) -> None:
        """extract_field_region rejects non-positive DPI values."""
        cache = DocumentCache(root=self.cache_root)
        ocr, _ = self._make_ocr()
        render_page, crop_region = self._make_render_and_crop()

        key = PageKey(file_hash="a" * 64, page_index=0)
        region = FieldRegion(left=0.0, top=0.0, right=1.0, bottom=1.0)

        # DPI = 0
        with self.assertRaises(ValueError) as cm:
            extract_field_region(
                key,
                region,
                render_page=render_page,
                crop_region=crop_region,
                ocr=ocr,
                dpi=0,
                cache=cache,
            )
        self.assertIn("positive", str(cm.exception).lower())

        # Negative DPI
        with self.assertRaises(ValueError) as cm:
            extract_field_region(
                key,
                region,
                render_page=render_page,
                crop_region=crop_region,
                ocr=ocr,
                dpi=-100,
                cache=cache,
            )
        self.assertIn("positive", str(cm.exception).lower())


if __name__ == "__main__":
    unittest.main()
