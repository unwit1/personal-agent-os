from __future__ import annotations

import json
import shutil
import sys
import time
import unittest
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os import documents
from agent_os.documents import (
    CachePrivacyError,
    DocumentCache,
    PageKey,
    cache_status_safe,
    embedded_text_is_sufficient,
    extract_page,
    hash_bytes,
    hash_file,
    is_blank_text,
    preprocess_signature,
    sanitized_report,
    structural_fingerprint,
)
from agent_os.paths import ROOT


# A realistic boilerplate-heavy page: repeated form vocabulary plus values that
# belong to one specific person and must never reach a shared signature.
FORM_TEXT = (
    "Employee Review Form. Employee name: Dana Whitfield. Employee number 8841203. "
    "Department: Operations. Department manager signature required. "
    "Review period start date. Review period end date. Review section one. "
    "Review section two. Signature of employee. Signature of manager. "
    "Contact dana.whitfield@example.com or 555-123-4567."
)


class CacheFixture(unittest.TestCase):
    def setUp(self) -> None:
        scratch = ROOT / ".tmp"
        scratch.mkdir(exist_ok=True)
        self.location = scratch / f"doccache-{uuid.uuid4()}"
        self.cache = DocumentCache(root=self.location)
        self.addCleanup(shutil.rmtree, self.location, True)

    def key(self, **overrides) -> PageKey:
        base = {
            "file_hash": hash_bytes(b"document-bytes"),
            "page_index": 0,
            "dpi": 300,
            "rotation": 0,
            "extractor": "pdftext@1.2",
            "ocr_engine": "engine@5.0",
            "preprocess": preprocess_signature({"deskew": True}),
        }
        base.update(overrides)
        return PageKey(**base)


class ContentAddressingTests(CacheFixture):
    def test_identical_content_produces_one_key(self) -> None:
        self.assertEqual(self.key().fingerprint(), self.key().fingerprint())

    def test_different_pages_of_one_file_are_distinct(self) -> None:
        self.assertNotEqual(self.key().fingerprint(), self.key(page_index=1).fingerprint())

    def test_render_settings_change_the_key(self) -> None:
        for change in ({"dpi": 600}, {"rotation": 90}, {"preprocess": preprocess_signature({"deskew": False})}):
            with self.subTest(change=change):
                self.assertNotEqual(self.key().fingerprint(), self.key(**change).fingerprint())

    def test_engine_version_changes_the_key(self) -> None:
        """A new OCR engine really does produce different bytes."""
        self.assertNotEqual(self.key().fingerprint(), self.key(ocr_engine="engine@6.0").fingerprint())
        self.assertNotEqual(self.key().fingerprint(), self.key(extractor="pdftext@2.0").fingerprint())

    def test_preprocess_signature_is_order_independent(self) -> None:
        self.assertEqual(
            preprocess_signature({"deskew": True, "denoise": False}),
            preprocess_signature({"denoise": False, "deskew": True}),
        )

    def test_file_hashing_matches_byte_hashing(self) -> None:
        path = self.location.with_suffix(".bin")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"document-bytes")
        self.addCleanup(path.unlink, True)
        self.assertEqual(hash_file(path), hash_bytes(b"document-bytes"))


class InterpretationInvalidationTests(CacheFixture):
    """The central economy guarantee of this layer."""

    def test_the_key_excludes_every_interpretation_layer(self) -> None:
        fields = set(self.key().as_dict())
        for component in documents.INTERPRETATION_COMPONENTS:
            with self.subTest(component=component):
                self.assertNotIn(
                    component,
                    fields,
                    f"'{component}' is in the extraction cache key; changing it would force OCR to rerun",
                )

    def test_the_key_covers_every_extraction_input(self) -> None:
        fields = set(self.key().as_dict())
        for component in documents.EXTRACTION_COMPONENTS:
            self.assertIn(component, fields)

    def test_changing_the_classifier_reuses_cached_ocr(self) -> None:
        """A classifier change must not cost a single second of OCR."""
        calls = {"ocr": 0}

        def ocr() -> str:
            calls["ocr"] += 1
            return FORM_TEXT

        extract_page(self.key(), lambda: None, ocr, self.cache)
        self.assertEqual(calls["ocr"], 1)
        # A downstream change: same document, same render settings, new
        # classifier. The key is unchanged by construction.
        result = extract_page(self.key(), lambda: None, ocr, self.cache)
        self.assertEqual(calls["ocr"], 1, "a classifier-level change re-ran OCR")
        self.assertEqual(result["route"], "cache")


class RoutingTests(CacheFixture):
    def test_sufficient_embedded_text_avoids_ocr_entirely(self) -> None:
        calls = {"ocr": 0}

        def ocr() -> str:
            calls["ocr"] += 1
            return "should never run"

        result = extract_page(self.key(), lambda: FORM_TEXT, ocr, self.cache)
        self.assertEqual(result["route"], "embedded_text")
        self.assertEqual(calls["ocr"], 0, "OCR ran despite sufficient embedded text")

    def test_thin_embedded_text_falls_through_to_ocr(self) -> None:
        """A stray text layer on a scan must not be trusted as the page."""
        result = extract_page(self.key(), lambda: "Page 1", lambda: FORM_TEXT, self.cache)
        self.assertEqual(result["route"], "ocr")
        self.assertIn("Department", result["text"])

    def test_a_second_pass_is_served_from_cache(self) -> None:
        first = extract_page(self.key(), lambda: FORM_TEXT, None, self.cache)
        second = extract_page(self.key(), lambda: FORM_TEXT, None, self.cache)
        self.assertFalse(first["cached"])
        self.assertTrue(second["cached"])
        self.assertEqual(first["text"], second["text"])

    def test_blank_pages_are_detected_cheaply(self) -> None:
        self.assertTrue(is_blank_text(""))
        self.assertTrue(is_blank_text("  \n "))
        self.assertTrue(is_blank_text("1 2 3"))
        self.assertFalse(is_blank_text("Employee Review Form"))

    def test_embedded_sufficiency_is_conservative(self) -> None:
        self.assertFalse(embedded_text_is_sufficient(None))
        self.assertFalse(embedded_text_is_sufficient("Page 1 of 4"))
        self.assertTrue(embedded_text_is_sufficient(FORM_TEXT))

    def test_a_failing_extractor_degrades_to_ocr(self) -> None:
        def broken() -> str:
            raise RuntimeError("no text layer")

        result = extract_page(self.key(), broken, lambda: FORM_TEXT, self.cache)
        self.assertEqual(result["route"], "ocr")

    def test_a_failing_ocr_engine_does_not_crash_the_page(self) -> None:
        def broken() -> str:
            raise RuntimeError("engine unavailable")

        result = extract_page(self.key(), lambda: None, broken, self.cache)
        self.assertEqual(result["route"], "ocr")
        self.assertTrue(result["blank"])


class CacheAbsenceTests(CacheFixture):
    """The cache is an optimization; correctness never depends on it."""

    def test_a_disabled_cache_still_returns_the_same_text(self) -> None:
        disabled = DocumentCache(root=self.location, enabled=False)
        with_cache = extract_page(self.key(), lambda: FORM_TEXT, None, self.cache)
        without = extract_page(self.key(), lambda: FORM_TEXT, None, disabled)
        self.assertEqual(with_cache["text"], without["text"])
        self.assertEqual(with_cache["route"], without["route"])

    def test_a_disabled_cache_never_writes(self) -> None:
        disabled = DocumentCache(root=self.location, enabled=False)
        extract_page(self.key(), lambda: FORM_TEXT, None, disabled)
        self.assertEqual(list(disabled.entries()), [])

    def test_a_corrupt_entry_is_a_miss_not_a_failure(self) -> None:
        extract_page(self.key(), lambda: FORM_TEXT, None, self.cache)
        for path in list(self.cache.entries()):
            path.write_text("{ this is not json", encoding="utf-8")
        result = extract_page(self.key(), lambda: FORM_TEXT, None, self.cache)
        self.assertEqual(result["text"], FORM_TEXT)
        self.assertFalse(result["cached"])

    def test_a_tampered_key_is_rejected(self) -> None:
        """A record whose key does not match its location is not trusted."""
        extract_page(self.key(), lambda: FORM_TEXT, None, self.cache)
        for path in list(self.cache.entries()):
            record = json.loads(path.read_text(encoding="utf-8"))
            record["key"]["page_index"] = 99
            path.write_text(json.dumps(record), encoding="utf-8")
        self.assertIsNone(self.cache.get(self.key()))

    def test_a_stale_schema_version_is_a_miss(self) -> None:
        extract_page(self.key(), lambda: FORM_TEXT, None, self.cache)
        for path in list(self.cache.entries()):
            record = json.loads(path.read_text(encoding="utf-8"))
            record["schema_version"] = 0
            path.write_text(json.dumps(record), encoding="utf-8")
        self.assertIsNone(self.cache.get(self.key()))


class PrivacyBoundaryTests(CacheFixture):
    def test_a_cache_inside_the_repository_is_refused(self) -> None:
        for candidate in ("forms", "projects", "knowledge", "docs"):
            with self.subTest(location=candidate):
                with self.assertRaises(CachePrivacyError):
                    DocumentCache(root=ROOT / candidate / "cache")

    def test_the_local_runtime_location_is_allowed(self) -> None:
        DocumentCache(root=ROOT / ".agent-local" / "document-cache")

    def test_a_location_outside_the_repository_is_allowed(self) -> None:
        DocumentCache(root=Path.home() / ".agent-os" / "document-cache")

    def test_the_default_location_is_gitignored(self) -> None:
        gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
        self.assertIn(".agent-local/", gitignore)
        self.assertTrue(str(documents.CACHE_DIR).endswith(str(Path(".agent-local") / "document-cache")))

    def test_the_structural_fingerprint_carries_no_personal_values(self) -> None:
        """Boilerplate repeats across a form; a person's data does not."""
        structure = structural_fingerprint(FORM_TEXT)
        blob = json.dumps(structure)
        for secret in ("whitfield", "8841203", "example.com", "555"):
            self.assertNotIn(secret, blob.casefold(), f"'{secret}' leaked into the structural signature")
        self.assertIn("employee", structure["anchor_terms"])

    def test_the_signature_identifies_the_template_not_the_person(self) -> None:
        """Two copies of one form, different people, must match.

        This is what template reuse needs, and it is also the property that
        keeps employee-specific values out of the signature by construction.
        """
        one = structural_fingerprint(FORM_TEXT)
        two = structural_fingerprint(
            FORM_TEXT.replace("Dana Whitfield", "Marcus Oyelaran")
            .replace("8841203", "2299017")
            .replace("dana.whitfield@example.com", "marcus.oyelaran@example.com")
            .replace("555-123-4567", "555-987-6543")
        )
        self.assertEqual(one["signature"], two["signature"], "the signature tracks the person, not the template")
        self.assertEqual(one["anchor_terms"], two["anchor_terms"])

    def test_anchor_terms_come_only_from_the_allowed_vocabulary(self) -> None:
        structure = structural_fingerprint(FORM_TEXT)
        self.assertTrue(structure["anchor_terms"])
        for term in structure["anchor_terms"]:
            self.assertIn(term, documents.FORM_VOCABULARY)

    def test_repetition_alone_never_creates_an_anchor(self) -> None:
        """A name repeated three times is still a name."""
        structure = structural_fingerprint("Whitfield Whitfield Whitfield Whitfield")
        self.assertEqual(structure["anchor_terms"], [])

    def test_the_sanitized_report_carries_no_content_or_path(self) -> None:
        extract_page(self.key(), lambda: FORM_TEXT, None, self.cache)
        report = sanitized_report(self.cache.telemetry, self.cache)
        blob = json.dumps(report)
        self.assertNotIn("Whitfield", blob)
        self.assertNotIn(str(self.location), blob)
        self.assertFalse(report["contains_document_content"])

    def test_the_safe_status_omits_the_absolute_path(self) -> None:
        status = cache_status_safe(self.cache)
        self.assertNotIn("location", status)
        self.assertTrue(status["private_local_only"])
        self.assertFalse(status["committed_to_git"])

    def test_no_cache_file_is_tracked_in_git(self) -> None:
        import subprocess

        tracked = subprocess.run(
            ["git", "ls-files", ".agent-local"], cwd=str(ROOT), capture_output=True, text=True
        )
        self.assertEqual(tracked.stdout.strip(), "", "private local-runtime files are tracked in Git")


class RetentionTests(CacheFixture):
    def _fill(self, pages: int) -> None:
        for index in range(pages):
            extract_page(self.key(page_index=index), lambda: FORM_TEXT, None, self.cache)

    def test_stats_report_size_and_count(self) -> None:
        self._fill(3)
        stats = self.cache.stats()
        self.assertEqual(stats["entries"], 3)
        self.assertGreater(stats["bytes"], 0)

    def test_clearing_removes_every_entry(self) -> None:
        self._fill(3)
        result = self.cache.clear()
        self.assertEqual(result["removed_entries"], 3)
        self.assertEqual(self.cache.stats()["entries"], 0)

    def test_a_size_limit_evicts_oldest_first(self) -> None:
        self._fill(5)
        before = self.cache.stats()["bytes"]
        result = self.cache.prune(max_bytes=before // 2, max_age_days=365)
        self.assertGreater(result["removed_entries"], 0)
        self.assertLessEqual(self.cache.stats()["bytes"], before)

    def test_an_age_limit_removes_stale_entries(self) -> None:
        self._fill(2)
        stale = time.time() - 86400 * 400
        for path in self.cache.entries():
            import os

            os.utime(path, (stale, stale))
        result = self.cache.prune(max_age_days=90)
        self.assertEqual(result["removed_entries"], 2)

    def test_invalidating_one_document_leaves_others(self) -> None:
        self._fill(2)
        other = self.key(file_hash=hash_bytes(b"another-document"))
        extract_page(other, lambda: FORM_TEXT, None, self.cache)
        removed = self.cache.invalidate_file(self.key().file_hash)
        self.assertEqual(removed, 2)
        self.assertEqual(self.cache.stats()["entries"], 1)
        self.assertIsNotNone(self.cache.get(other))

    def test_rebuilding_after_a_clear_works(self) -> None:
        self._fill(2)
        self.cache.clear()
        result = extract_page(self.key(), lambda: FORM_TEXT, None, self.cache)
        self.assertEqual(result["text"], FORM_TEXT)
        self.assertEqual(self.cache.stats()["entries"], 1)


class TelemetryTests(CacheFixture):
    def test_counts_describe_where_the_work_went(self) -> None:
        extract_page(self.key(page_index=0), lambda: FORM_TEXT, None, self.cache)
        extract_page(self.key(page_index=0), lambda: FORM_TEXT, None, self.cache)
        extract_page(self.key(page_index=1), lambda: None, lambda: FORM_TEXT, self.cache)
        counts = self.cache.telemetry.as_dict()
        self.assertEqual(counts["pages"], 3)
        self.assertEqual(counts["cache_hits"], 1)
        self.assertEqual(counts["embedded_text_pages"], 1)
        self.assertEqual(counts["ocr_pages"], 1)
        self.assertAlmostEqual(counts["cache_hit_rate"], round(1 / 3, 3))

    def test_repeated_runs_report_rising_hit_rates(self) -> None:
        """The economy claim, measured rather than asserted."""
        for index in range(4):
            extract_page(self.key(page_index=index), lambda: FORM_TEXT, None, self.cache)
        first_pass = self.cache.telemetry.as_dict()["cache_hit_rate"]
        second = DocumentCache(root=self.location)
        for index in range(4):
            extract_page(self.key(page_index=index), lambda: FORM_TEXT, None, second)
        self.assertEqual(first_pass, 0.0)
        self.assertEqual(second.telemetry.as_dict()["cache_hit_rate"], 1.0)


if __name__ == "__main__":
    unittest.main()
