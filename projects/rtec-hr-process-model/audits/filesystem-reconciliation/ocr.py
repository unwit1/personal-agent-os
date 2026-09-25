"""Offline OCR helpers for the local-only RTEC HR reconciliation audit.

OCR results are summarized in memory as hashes, counts, and privacy signal
codes. Raw OCR text is never returned to the inventory writer or persisted.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np
from PIL import Image, ImageSequence

from extractor import _scan_text

OCR_PROCESSOR_VERSION = "rtec-easyocr-offline@1"
MODEL_DIR = Path.home() / ".EasyOCR" / "model"
REQUIRED_MODELS = ("craft_mlt_25k.pth", "english_g2.pth")
_reader = None


def get_reader():
    """Load only the already-cached English model; network downloads are off."""
    global _reader
    if _reader is None:
        missing = [name for name in REQUIRED_MODELS if not (MODEL_DIR / name).is_file()]
        if missing:
            raise RuntimeError("cached_easyocr_model_missing")
        import easyocr

        _reader = easyocr.Reader(
            ["en"], gpu=False, model_storage_directory=str(MODEL_DIR),
            user_network_directory=str(MODEL_DIR), download_enabled=False,
            verbose=False,
        )
    return _reader


def _page_text(reader, image: Image.Image) -> str:
    results = reader.readtext(np.asarray(image.convert("RGB")), detail=1, paragraph=True)
    return "\n".join(str(item[1]) for item in results if len(item) > 1 and item[1])


def _render_page(path: Path, index: int) -> Image.Image:
    import pymupdf

    with pymupdf.open(path) as document:
        page = document.load_page(index)
        pixmap = page.get_pixmap(matrix=pymupdf.Matrix(1.5, 1.5), alpha=False)
        return Image.frombytes("RGB", [pixmap.width, pixmap.height], pixmap.samples)


def page_count(path: Path) -> int:
    suffix = path.suffix.casefold()
    if suffix == ".pdf":
        import pymupdf

        with pymupdf.open(path) as document:
            return document.page_count
    with Image.open(path) as image:
        return int(getattr(image, "n_frames", 1))


def extract_page(path: Path, index: int, reader=None) -> dict:
    reader = reader or get_reader()
    if path.suffix.casefold() == ".pdf":
        image = _render_page(path, index)
    else:
        with Image.open(path) as source:
            source.seek(index)
            image = source.convert("RGB")
    text = _page_text(reader, image)
    summary = _scan_text(text)
    return {
        "page_text_sha256": summary["normalized_sha256"],
        "text_char_count": summary["text_char_count"],
        "signal_codes": summary["signal_codes"],
    }


def classify_ocr(signals: list[str], text_hint: str, route: str) -> tuple[str, float]:
    sensitive = {
        "ssn_value_pattern", "email_value_pattern", "phone_value_pattern",
        "financial_identifier_value_pattern", "health_content_term",
        "employee_record_content_term", "employee_table_values",
    }
    if route == "restricted_employee_metadata_only" or sensitive.intersection(signals):
        return "EMPLOYEE_SPECIFIC_RESTRICTED", 0.9
    if route == "organizational_candidate_or_mixed_review":
        if any(word in text_hint.casefold() for word in ("policy", "procedure", "handbook", "template", "instruction", "checklist")):
            return "SAFE_ORGANIZATIONAL_CANDIDATE", 0.7
        return "UNKNOWN_REVIEW", 0.4
    return "UNKNOWN_REVIEW", 0.4


def aggregate_hash(page_hashes: list[str]) -> str | None:
    if not page_hashes:
        return None
    material = "\n".join(page_hashes).encode("ascii")
    return hashlib.sha256(material).hexdigest()
