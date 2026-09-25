"""Local, deterministic structural extraction with no persisted document text.

This module does not upload, print, or return raw source text to the caller. It
returns hashes, structure, privacy signal codes, and a conservative review
classification. The caller stores results only in the ignored local audit DB.
"""

from __future__ import annotations

import csv
import hashlib
import html
import io
import re
import zipfile
from email import policy
from email.parser import BytesParser
from pathlib import Path
from xml.etree import ElementTree


PROCESSOR_VERSION = "rtec-local-extract@1"
MAX_CELLS = 250_000
MAX_TEXT_CHARS = 50_000_000
ORG_HINTS = ("policy", "procedure", "handbook", "manual", "template", "blank", "guide", "instruction", "reference", "checklist")
PERSON_HEADERS = ("employee id", "employeeid", "employeeidentifier", "employee number", "eid", "employee name", "last name", "first name", "subscriber name", "dependent name")
SENSITIVE_HEADERS = ("ssn", "social security", "date of birth", "dob", "address", "phone", "email", "bank", "routing number", "direct deposit", "salary", "rate of pay", "wage", "benefit election", "dependent", "medical", "diagnosis", "leave case", "discipline", "attendance", "driver license", "license number", "mvr", "drug test", "background check")


def _clean(values) -> str:
    return "\n".join(str(v) for v in values if v is not None and str(v).strip())


def _scan_text(text: str) -> dict:
    normalized = re.sub(r"\s+", " ", text).strip().casefold()
    signals = set()
    if re.search(r"\b\d{3}-\d{2}-\d{4}\b", text):
        signals.add("ssn_value_pattern")
    if re.search(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", text, re.I):
        signals.add("email_value_pattern")
    if re.search(r"(?<!\d)(?:\+?1[ .-]?)?\(?\d{3}\)?[ .-]\d{3}[ .-]\d{4}(?!\d)", text):
        signals.add("phone_value_pattern")
    if re.search(r"\b(?:account|routing|bank)\s*(?:number|no\.?|#)\s*[:#-]?\s*\d{4,}\b", text, re.I):
        signals.add("financial_identifier_value_pattern")
    if re.search(r"\b(?:diagnosis|treatment|medical condition|patient|medical record)\b", text, re.I):
        signals.add("health_content_term")
    if re.search(r"\b(?:employee id|employee number|subscriber id|dependent|pay rate|salary|wage|payroll deduction)\b", text, re.I):
        signals.add("employee_record_content_term")
    return {
        "normalized_sha256": hashlib.sha256(normalized.encode("utf-8")).hexdigest() if normalized else None,
        "text_char_count": len(text),
        "signal_codes": sorted(signals),
    }


def _read_text_file(path: Path) -> str:
    raw = path.read_bytes()
    for encoding in ("utf-8-sig", "utf-16", "cp1252", "latin-1"):
        try:
            return raw.decode(encoding)
        except UnicodeError:
            continue
    return ""


def _extract_pdf(path: Path) -> dict:
    from pypdf import PdfReader

    reader = PdfReader(str(path), strict=False)
    if reader.is_encrypted and not reader.decrypt(""):
        return {"status": "PASSWORD_PROTECTED", "method": "pypdf", "detail_code": "encrypted_pdf"}
    chunks = []
    empty_pages = 0
    for page in reader.pages:
        text = page.extract_text() or ""
        if not text.strip():
            empty_pages += 1
        chunks.append(text)
    text = "\n".join(chunks)
    result = _scan_text(text)
    result.update({"status": "parsed" if text.strip() else "OCR_REQUIRED", "method": "pypdf", "page_count": len(reader.pages), "empty_pages": empty_pages, "sheet_count": 0, "sheet_schemas": []})
    return result


def _extract_docx(path: Path) -> dict:
    from docx import Document

    document = Document(str(path))
    chunks = [p.text for p in document.paragraphs]
    for table in document.tables:
        for row in table.rows:
            chunks.append(" | ".join(cell.text for cell in row.cells))
    text = "\n".join(chunks)
    result = _scan_text(text)
    result.update({"status": "parsed" if text.strip() else "empty_text", "method": "python-docx", "page_count": None, "sheet_count": len(document.tables), "sheet_schemas": []})
    return result


def _sheet_classification(headers: list[str], row_count: int) -> tuple[set[str], set[str]]:
    joined = " ".join(headers).casefold()
    labels = set()
    if any(term in joined for term in PERSON_HEADERS):
        labels.add("person_columns")
    if any(term in joined for term in SENSITIVE_HEADERS):
        labels.add("sensitive_columns")
    signals = set()
    if row_count > 0 and "person_columns" in labels:
        signals.add("employee_table_values")
    return labels, signals


def _extract_xlsx(path: Path) -> dict:
    from openpyxl import load_workbook

    workbook = load_workbook(path, read_only=False, data_only=False, keep_links=False)
    text_values = []
    schemas = []
    signal_codes = set()
    cell_count = formula_count = 0
    char_count = 0
    truncated = False
    try:
        for sheet in workbook.worksheets:
            nonempty_rows = []
            for row in sheet.iter_rows(values_only=True):
                populated = [value for value in row if value is not None and str(value).strip()]
                if not populated:
                    continue
                nonempty_rows.append(populated)
                cell_count += len(populated)
                for value in populated:
                    value_text = str(value)
                    text_values.append(value_text)
                    char_count += len(value_text)
                    if value_text.startswith("="):
                        formula_count += 1
                if cell_count >= MAX_CELLS or char_count >= MAX_TEXT_CHARS:
                    truncated = True
                    break
            headers = [str(v).strip()[:256] for v in (nonempty_rows[0] if nonempty_rows else [])]
            data_rows = max(0, len(nonempty_rows) - 1)
            labels, signals = _sheet_classification(headers, data_rows)
            signal_codes.update(signals)
            schemas.append({"sheet_name": sheet.title[:160], "sheet_state": sheet.sheet_state, "headers": headers, "nonempty_rows": len(nonempty_rows), "data_rows": data_rows, "header_labels": sorted(labels), "merged_range_count": len(sheet.merged_cells.ranges)})
            if truncated:
                break
        text = "\n".join(text_values)
        result = _scan_text(text)
        signal_codes.update(result["signal_codes"])
        result.update({"status": "partial" if truncated else ("parsed" if text else "empty_text"), "method": "openpyxl", "page_count": None, "sheet_count": len(schemas), "sheet_schemas": schemas, "nonempty_cell_count": cell_count, "formula_count": formula_count, "defined_name_count": len(workbook.defined_names), "signal_codes": sorted(signal_codes), "detail_code": "cell_limit" if truncated else None})
        return result
    finally:
        workbook.close()


def _extract_xls(path: Path) -> dict:
    import xlrd

    workbook = xlrd.open_workbook(str(path), on_demand=True)
    text_values = []
    schemas = []
    signal_codes = set()
    cell_count = formula_count = 0
    char_count = 0
    truncated = False
    try:
        for sheet in workbook.sheets():
            rows = []
            for row_index in range(sheet.nrows):
                populated = [sheet.cell_value(row_index, col) for col in range(sheet.ncols) if sheet.cell_value(row_index, col) not in ("", None)]
                if not populated:
                    continue
                rows.append(populated)
                cell_count += len(populated)
                text_values.extend(str(value) for value in populated)
                char_count += sum(len(str(value)) for value in populated)
                if cell_count >= MAX_CELLS or char_count >= MAX_TEXT_CHARS:
                    truncated = True
                    break
            headers = [str(v).strip()[:256] for v in (rows[0] if rows else [])]
            data_rows = max(0, len(rows) - 1)
            labels, signals = _sheet_classification(headers, data_rows)
            signal_codes.update(signals)
            schemas.append({"sheet_name": sheet.name[:160], "sheet_state": "visible" if sheet.visibility == 0 else "hidden", "headers": headers, "nonempty_rows": len(rows), "data_rows": data_rows, "header_labels": sorted(labels), "merged_range_count": None})
            if truncated:
                break
        text = "\n".join(text_values)
        result = _scan_text(text)
        signal_codes.update(result["signal_codes"])
        result.update({"status": "partial" if truncated else ("parsed" if text else "empty_text"), "method": "xlrd", "page_count": None, "sheet_count": len(schemas), "sheet_schemas": schemas, "nonempty_cell_count": cell_count, "formula_count": None, "defined_name_count": None, "signal_codes": sorted(signal_codes), "detail_code": "cell_limit" if truncated else None})
        return result
    finally:
        workbook.release_resources()


def _extract_csv(path: Path) -> dict:
    text = _read_text_file(path)
    rows = list(csv.reader(io.StringIO(text)))
    headers = [str(v).strip()[:256] for v in (rows[0] if rows else [])]
    labels, signals = _sheet_classification(headers, max(0, len(rows) - 1))
    result = _scan_text(text)
    result.update({"status": "parsed" if text else "empty_text", "method": "csv", "page_count": None, "sheet_count": 1 if rows else 0, "sheet_schemas": ([{"sheet_name": path.stem[:160], "sheet_state": "visible", "headers": headers, "nonempty_rows": len(rows), "data_rows": max(0, len(rows) - 1), "header_labels": sorted(labels), "merged_range_count": None}] if rows else []), "signal_codes": sorted(set(result["signal_codes"]) | signals)})
    return result


def _extract_pptx(path: Path) -> dict:
    chunks = []
    with zipfile.ZipFile(path) as archive:
        slides = sorted((name for name in archive.namelist() if re.fullmatch(r"ppt/slides/slide\d+\.xml", name)), key=lambda n: int(re.search(r"slide(\d+)", n).group(1)))
        for name in slides:
            root = ElementTree.fromstring(archive.read(name))
            chunks.extend(node.text or "" for node in root.iter() if node.tag.endswith("}t"))
    text = "\n".join(chunks)
    result = _scan_text(text)
    result.update({"status": "parsed" if text.strip() else "empty_text", "method": "pptx-xml", "page_count": len(slides), "sheet_count": 0, "sheet_schemas": []})
    return result


def extract(path: Path, sensitivity_route: str) -> dict:
    """Extract structure and transient text locally; return no source text."""
    path = Path(path)
    ext = path.suffix.casefold()
    try:
        if ext == ".pdf":
            result = _extract_pdf(path)
        elif ext == ".docx":
            result = _extract_docx(path)
        elif ext == ".xlsx" or ext == ".xlsm":
            result = _extract_xlsx(path)
        elif ext == ".xls":
            result = _extract_xls(path)
        elif ext in {".csv", ".tsv"}:
            result = _extract_csv(path)
        elif ext in {".txt", ".html", ".htm", ".rtf"}:
            text = _read_text_file(path)
            if ext in {".html", ".htm"}:
                text = html.unescape(re.sub(r"<[^>]+>", " ", text))
            elif ext == ".rtf":
                text = re.sub(r"\\'[0-9a-fA-F]{2}|\\[a-zA-Z]+-?\d* ?|[{}]", " ", text)
            result = _scan_text(text)
            result.update({"status": "parsed" if text.strip() else "empty_text", "method": "local-text", "page_count": None, "sheet_count": 0, "sheet_schemas": []})
        elif ext == ".pptx":
            result = _extract_pptx(path)
        elif ext in {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"}:
            result = {"status": "OCR_REQUIRED", "method": "none", "detail_code": "image_ocr_not_run", "page_count": None, "sheet_count": 0, "sheet_schemas": [], "text_char_count": 0, "normalized_sha256": None, "signal_codes": []}
        elif ext == ".zip":
            with zipfile.ZipFile(path) as archive:
                members = archive.infolist()
            result = {"status": "ARCHIVE_REVIEW", "method": "zip-directory", "detail_code": "archive_members_not_extracted", "page_count": None, "sheet_count": 0, "sheet_schemas": [], "text_char_count": 0, "normalized_sha256": None, "signal_codes": [], "archive_member_count": len(members), "archive_extensions": sorted({Path(item.filename).suffix.casefold() for item in members if Path(item.filename).suffix})}
        elif ext == ".eml":
            message = BytesParser(policy=policy.default).parsebytes(path.read_bytes())
            body = message.get_body(preferencelist=("plain",))
            text = body.get_content() if body else ""
            result = _scan_text(text)
            result.update({"status": "parsed" if text.strip() else "empty_text", "method": "email-parser", "detail_code": "attachments_not_extracted", "page_count": None, "sheet_count": 0, "sheet_schemas": []})
        else:
            result = {"status": "UNSUPPORTED_FORMAT", "method": "none", "detail_code": ext or "no_extension", "page_count": None, "sheet_count": 0, "sheet_schemas": [], "text_char_count": 0, "normalized_sha256": None, "signal_codes": []}
    except PermissionError:
        result = {"status": "PERMISSION_DENIED", "method": "unknown", "detail_code": "permission_denied"}
    except (zipfile.BadZipFile, OSError, ValueError, RuntimeError) as exc:
        result = {"status": "CORRUPT", "method": "local-parser", "detail_code": type(exc).__name__}
    except Exception as exc:
        name = type(exc).__name__
        code = "PASSWORD_PROTECTED" if "password" in name.casefold() or "decrypt" in name.casefold() else "PARSE_FAILED"
        result = {"status": code, "method": "local-parser", "detail_code": name}

    signals = set(result.get("signal_codes", []))
    headers = " ".join(
        header for sheet in result.get("sheet_schemas", []) for header in sheet.get("headers", [])
    ).casefold()
    has_person_rows = any("employee_table_values" in sheet.get("header_labels", []) or "person_columns" in sheet.get("header_labels", []) and sheet.get("data_rows", 0) > 0 for sheet in result.get("sheet_schemas", []))
    high_risk_signals = signals & {"ssn_value_pattern", "email_value_pattern", "phone_value_pattern", "financial_identifier_value_pattern", "employee_table_values"}
    ambiguous_sensitive_signals = signals & {"health_content_term", "employee_record_content_term"}
    sensitive_labels = any(term in headers for term in SENSITIVE_HEADERS)
    organizational_hint = any(term in path.name.casefold() for term in ORG_HINTS)
    if result.get("status") not in {"parsed", "partial", "empty_text", "OCR_REQUIRED", "ARCHIVE_REVIEW"}:
        classification = "UNPARSEABLE"
        confidence = 0.99
    elif high_risk_signals or has_person_rows or sensitivity_route == "restricted_employee_metadata_only" and sensitive_labels:
        classification = "EMPLOYEE_SPECIFIC_RESTRICTED"
        confidence = 0.93 if high_risk_signals or has_person_rows else 0.70
    elif result.get("status") == "OCR_REQUIRED":
        classification = "UNKNOWN_REVIEW"
        confidence = 0.30
    elif sensitive_labels or ambiguous_sensitive_signals or result.get("status") in {"partial", "ARCHIVE_REVIEW"}:
        classification = "MIXED_OR_UNCERTAIN"
        confidence = 0.55
    elif sensitivity_route == "organizational_candidate_or_mixed_review" and (organizational_hint or result.get("text_char_count", 0) >= 300):
        classification = "SAFE_ORGANIZATIONAL_CANDIDATE"
        confidence = 0.65
    else:
        classification = "UNKNOWN_REVIEW"
        confidence = 0.35
    result["classification"] = classification
    result["classification_confidence"] = confidence
    result["review_required"] = 1
    result["processor_version"] = PROCESSOR_VERSION
    return result
