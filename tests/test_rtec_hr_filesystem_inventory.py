from __future__ import annotations

import importlib.util
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path



MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "projects"
    / "rtec-hr-process-model"
    / "audits"
    / "filesystem-reconciliation"
    / "inventory.py"
)
SPEC = importlib.util.spec_from_file_location("rtec_hr_filesystem_inventory", MODULE_PATH)
assert SPEC and SPEC.loader
inventory = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = inventory
SPEC.loader.exec_module(inventory)
EXTRACTOR_PATH = MODULE_PATH.with_name("extractor.py")
EXTRACTOR_SPEC = importlib.util.spec_from_file_location("rtec_hr_local_extractor", EXTRACTOR_PATH)
assert EXTRACTOR_SPEC and EXTRACTOR_SPEC.loader
extractor = importlib.util.module_from_spec(EXTRACTOR_SPEC)
sys.modules[EXTRACTOR_SPEC.name] = extractor
EXTRACTOR_SPEC.loader.exec_module(extractor)
sys.modules["extractor"] = extractor
OCR_PATH = MODULE_PATH.with_name("ocr.py")
OCR_SPEC = importlib.util.spec_from_file_location("rtec_hr_local_ocr", OCR_PATH)
assert OCR_SPEC and OCR_SPEC.loader
ocr = importlib.util.module_from_spec(OCR_SPEC)
sys.modules[OCR_SPEC.name] = ocr
OCR_SPEC.loader.exec_module(ocr)


class RtecHrFilesystemInventoryTests(unittest.TestCase):
    def test_server_drive_and_applicant_roots_are_excluded(self) -> None:
        self.assertFalse(inventory.safe_root(Path("R:/")))
        self.assertTrue(inventory.blocked_directory(Path("R:/HR/Shared")))
        self.assertTrue(inventory.blocked_directory(Path("C:/Work/Job Applicant Dashboard")))
        self.assertTrue(inventory.blocked_directory(Path("C:/Work/_Pending_New_Hires")))

    def test_profile_name_does_not_make_every_file_hr_relevant(self) -> None:
        root = Path("C:/Users/HR.RTEC/Desktop")
        likely, route = inventory.relevance(root / "personal-notes.pdf", root)
        self.assertFalse(likely)
        self.assertEqual(route, "unclassified_work_document")
        self.assertTrue(inventory.relevance(root / "benefits" / "plan-guide.pdf", root)[0])

    def test_discovery_resumes_after_a_bounded_file_batch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "HR"
            root.mkdir()
            for name in ("a-policy.pdf", "b-policy.pdf", "c-policy.pdf"):
                (root / name).write_bytes(name.encode("ascii"))
            db = inventory.connect(Path(tmp) / "audit.sqlite3")
            inventory.add_roots(db, [root])

            seen = 0
            while db.execute("SELECT COUNT(*) FROM directories WHERE status='queued'").fetchone()[0]:
                inventory.discover_batch(db, max_dirs=1, max_files=1)
                seen = db.execute("SELECT COUNT(*) FROM files").fetchone()[0]

            self.assertEqual(seen, 3)
            self.assertEqual(db.execute("SELECT COUNT(*) FROM directories WHERE status='done'").fetchone()[0], 1)
            db.close()

    def test_xlsx_extracts_all_sheets_without_returning_cell_values(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            try:
                from openpyxl import Workbook
            except ImportError:
                self.skipTest("openpyxl is optional for local workbook parsing")
            path = Path(tmp) / "Employee Roster.xlsx"
            workbook = Workbook()
            visible = workbook.active
            visible.title = "Office"
            visible.append(["Employee ID", "Name", "Email"])
            visible.append(["0001", "Synthetic Person", "person@example.test"])
            hidden = workbook.create_sheet("Hidden Data")
            hidden.sheet_state = "hidden"
            hidden.append(["SSN", "Date of Birth"])
            hidden.append(["123-45-6789", "01/02/1980"])
            workbook.save(path)

            result = extractor.extract(path, "organizational_candidate_or_mixed_review")

            self.assertEqual(result["classification"], "EMPLOYEE_SPECIFIC_RESTRICTED")
            self.assertEqual(result["sheet_count"], 2)
            self.assertEqual(result["sheet_schemas"][1]["sheet_state"], "hidden")
            self.assertIn("ssn_value_pattern", result["signal_codes"])
            self.assertNotIn("text", result)
            self.assertNotIn("Synthetic Person", repr(result))
            self.assertNotIn("123-45-6789", repr(result))

    def test_blank_policy_candidate_is_reviewable_but_not_auto_promoted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "Leave Policy.txt"
            path.write_text("Leave policy and procedure. " + "General process instructions. " * 20, encoding="utf-8")

            result = extractor.extract(path, "organizational_candidate_or_mixed_review")

            self.assertEqual(result["classification"], "SAFE_ORGANIZATIONAL_CANDIDATE")
            self.assertEqual(result["review_required"], 1)
            self.assertNotIn("text", result)

    def test_ocr_routes_signal_codes_without_returning_raw_text(self) -> None:
        class FakeReader:
            def readtext(self, _image, detail=1, paragraph=True):
                self.image_shape = _image.shape
                return [([[(0, 0), (1, 0), (1, 1), (0, 1)]], "Employee ID 123456", 0.99)]

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "Synthetic Scan.png"
            from PIL import Image

            Image.new("RGB", (3000, 3000), "white").save(path)
            fake = FakeReader()
            result = ocr.extract_page(path, 0, fake)

        self.assertIn("employee_record_content_term", result["signal_codes"])
        self.assertLessEqual(max(fake.image_shape[:2]), ocr.MAX_IMAGE_EDGE)
        self.assertNotIn("text", result)
        self.assertNotIn("123456", repr(result))
        self.assertEqual(
            ocr.classify_ocr(result["signal_codes"], "policy", "organizational_candidate_or_mixed_review")[0],
            "EMPLOYEE_SPECIFIC_RESTRICTED",
        )
        self.assertEqual(
            ocr.classify_ocr([], "leave policy", "organizational_candidate_or_mixed_review")[0],
            "SAFE_ORGANIZATIONAL_CANDIDATE",
        )

    def test_ocr_batch_resumes_at_the_next_page_without_storing_text(self) -> None:
        from types import SimpleNamespace

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "Blank Policy.pdf"
            path.write_bytes(b"synthetic-pdf")
            stat = path.stat()
            db = inventory.connect(root / "audit.sqlite3")
            db.execute("""INSERT INTO files(path,root,filename,extension,size,mtime_ns,likely_hr,
              sensitivity_route,sha256,hash_state,discovered_at,updated_at)
              VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
                       (str(path), str(root), path.name, ".pdf", stat.st_size, stat.st_mtime_ns,
                        1, "organizational_candidate_or_mixed_review", "a" * 64, "complete", "now", "now"))
            db.execute("""INSERT INTO file_extractions(path,file_sha256,processor_version,extraction_status,
              classification,classification_confidence,extracted_at)
              VALUES(?,?,?,?,?,?,?)""",
                       (str(path), "a" * 64, extractor.PROCESSOR_VERSION, "OCR_REQUIRED", "UNKNOWN_REVIEW", 0.0, "now"))
            db.commit()
            fake_ocr = SimpleNamespace(
                OCR_PROCESSOR_VERSION="fake-ocr@1",
                get_reader=lambda: object(),
                page_count=lambda _path: 2,
                extract_page=lambda _path, index, _reader: {
                    "page_text_sha256": hashlib.sha256(f"page-{index}".encode()).hexdigest(),
                    "text_char_count": 12,
                    "signal_codes": [],
                },
                classify_ocr=lambda _signals, _hint, _route: ("SAFE_ORGANIZATIONAL_CANDIDATE", 0.7),
                aggregate_hash=lambda values: hashlib.sha256("\n".join(values).encode()).hexdigest(),
            )
            previous = sys.modules.get("ocr")
            sys.modules["ocr"] = fake_ocr
            try:
                self.assertEqual(inventory.ocr_batch(db, 1, 1), 1)
                first = db.execute("SELECT status,pages_processed,page_hashes_json FROM file_ocr").fetchone()
                self.assertEqual((first["status"], first["pages_processed"]), ("partial", 1))
                self.assertEqual(inventory.ocr_batch(db, 1, 1), 1)
                second = db.execute("SELECT status,pages_processed,page_hashes_json FROM file_ocr").fetchone()
                self.assertEqual((second["status"], second["pages_processed"]), ("complete", 2))
                self.assertEqual(len(json.loads(second["page_hashes_json"])), 2)
                self.assertNotIn("synthetic-pdf", second["page_hashes_json"])
            finally:
                if previous is None:
                    sys.modules.pop("ocr", None)
                else:
                    sys.modules["ocr"] = previous
                db.close()

    def test_normalized_duplicate_view_keeps_text_groups_separate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db = inventory.connect(root / "audit.sqlite3")
            for name in ("copy-a.txt", "copy-b.txt"):
                path = root / name
                db.execute("""INSERT INTO files(path,root,filename,extension,size,mtime_ns,likely_hr,
                  sensitivity_route,sha256,hash_state,discovered_at,updated_at)
                  VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
                           (str(path), str(root), name, ".txt", 10, 1, 1,
                            "organizational_candidate_or_mixed_review", "a" * 64, "complete", "now", "now"))
                db.execute("""INSERT INTO file_extractions(path,file_sha256,processor_version,extraction_status,
                  normalized_text_sha256,classification,classification_confidence,extracted_at)
                  VALUES(?,?,?,?,?,?,?,?)""",
                           (str(path), "a" * 64, extractor.PROCESSOR_VERSION, "parsed", "same-normalized-text",
                            "SAFE_ORGANIZATIONAL_CANDIDATE", 0.7, "now"))
            db.commit()
            group = db.execute("SELECT member_count FROM normalized_duplicate_groups").fetchone()
            self.assertEqual(group[0], 2)
            db.close()

    def test_hash_reconciliation_does_not_promote_ambiguous_hash_kinds(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db = inventory.connect(root / "audit.sqlite3")
            for name, digest in (("explicit.pdf", "a" * 64), ("ambiguous.pdf", "b" * 64)):
                db.execute("""INSERT INTO files(path,root,filename,extension,size,mtime_ns,likely_hr,
                  sensitivity_route,sha256,hash_state,discovered_at,updated_at)
                  VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
                           (str(root / name), str(root), name, ".pdf", 10, 1, 1,
                            "organizational_candidate_or_mixed_review", digest, "complete", "now", "now"))
            db.execute("INSERT INTO source_hashes(sha256,source_id,knowledge_path,hash_kind) VALUES(?,?,?,?)",
                       ("a" * 64, "source-1", "knowledge/source.json", "source_sha256"))
            db.execute("INSERT INTO source_hashes(sha256,source_id,knowledge_path,hash_kind) VALUES(?,?,?,?)",
                       ("b" * 64, "source-2", "knowledge/source.json", "content_sha256"))
            db.commit()
            matched, _ = inventory.reconcile_hashes(db)
            self.assertEqual(matched, 1)
            states = {Path(row["path"]).name: row["source_match"] for row in
                      db.execute("SELECT path,source_match FROM files").fetchall()}
            self.assertEqual(states["explicit.pdf"], "ALREADY_INGESTED_EXACT")
            self.assertEqual(states["ambiguous.pdf"], "HASH_MATCH_UNVERIFIED")
            db.close()

    def test_employee_document_type_hint_uses_known_form_label_only(self) -> None:
        rules = [
            {"match": ["FMLA", "FMLA Medical Cert"], "modules": ["fmla"]},
            {"match": ["Warning Notice"], "modules": ["disciplinary"]},
        ]
        hint = inventory.document_type_hint("Synthetic Person FMLA Medical Cert.pdf", rules)
        self.assertEqual(hint, ("fmla", "FMLA Medical Cert", 0.8, ["fmla"]))
        self.assertNotIn("Synthetic Person", repr(hint))
        self.assertIsNone(inventory.document_type_hint("Synthetic Person Notice.pdf", rules))


if __name__ == "__main__":
    unittest.main()
