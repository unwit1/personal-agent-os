#!/usr/bin/env python3
"""Build deterministic BOOK text fingerprints for the Wheels of Lull continuity.

The builder intentionally stops after the complete BOOK corpus is collected, so it is
independent of later dialogue shards (including currently damaged gzip shards).
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import re
from pathlib import Path

SHARD_RE = re.compile(r"source-records-(\d+)-(\d+)\.jsonl(?:\.gz)?$")
PAGEBREAK_RE = re.compile(r"\[pagebreak\]", re.I)
FONT_RE = re.compile(r"</?font\b[^>]*>", re.I)
P_RE = re.compile(r"</?p\b[^>]*>", re.I)
IMG_RE = re.compile(r"<img\b[^>]*>", re.I)

NORMALIZATION_VERSION = "wol-book-normalize-v1"


def open_text(path: Path):
    if path.suffix == ".gz":
        return gzip.open(path, "rt", encoding="utf-8")
    return path.open("r", encoding="utf-8")


def source_shards(raw_dir: Path):
    found = []
    for path in raw_dir.glob("source-records-*.jsonl*"):
        match = SHARD_RE.search(path.name)
        if match:
            found.append((int(match.group(1)), int(match.group(2)), path))
    return sorted(found)


def normalize_markup(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = PAGEBREAK_RE.sub("\n", text)
    text = FONT_RE.sub("", text)
    text = P_RE.sub("", text)
    text = IMG_RE.sub("", text)
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def comparison_text(text: str) -> str:
    text = normalize_markup(text).lower()
    text = text.replace("“", '"').replace("”", '"')
    text = text.replace("‘", "'").replace("’", "'")
    text = text.replace("–", "-").replace("—", "-")
    return re.sub(r"\s+", " ", text).strip()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def collect_books(raw_dir: Path, expected_books: int) -> list[dict]:
    books = []
    source_sha = None

    for start, _end, path in source_shards(raw_dir):
        with open_text(path) as handle:
            for line_no, line in enumerate(handle):
                if not line.strip():
                    continue
                row = json.loads(line)
                row_sha = row.get("source_sha256")
                if row_sha:
                    if source_sha is None:
                        source_sha = row_sha
                    elif source_sha != row_sha:
                        raise ValueError(
                            f"source SHA mismatch in {path.name}: {row_sha} != {source_sha}"
                        )

                if row.get("record_type") != "BOOK":
                    continue

                raw = row.get("text") or ""
                normalized = normalize_markup(raw)
                compared = comparison_text(raw)
                books.append(
                    {
                        "form_id": row.get("form_id"),
                        "editor_id": row.get("editor_id"),
                        "title": row.get("full_name"),
                        "source_offset": row.get("source_offset"),
                        "raw_text_chars": len(raw),
                        "normalized_text_chars": len(normalized),
                        "raw_text_sha256": sha256_text(raw),
                        "normalized_text_sha256": sha256_text(normalized),
                        "comparison_text_sha256": sha256_text(compared),
                    }
                )

                if len(books) == expected_books:
                    books.sort(key=lambda item: item.get("source_offset") or 0)
                    return books

    raise RuntimeError(
        f"expected {expected_books} BOOK records but found only {len(books)}"
    )


def build(continuity_dir: Path, expected_books: int) -> dict:
    books = collect_books(continuity_dir / "raw", expected_books)
    source_sha = None
    # Every persisted BOOK carries the same source SHA; fetch it from an early shard.
    for _start, _end, path in source_shards(continuity_dir / "raw"):
        with open_text(path) as handle:
            for line in handle:
                if line.strip():
                    source_sha = json.loads(line).get("source_sha256")
                    break
        if source_sha:
            break

    return {
        "continuity_id": "tes.mod.wheels-of-lull",
        "source_sha256": source_sha,
        "stage": "book_text_normalization_and_hashing",
        "status": f"complete_{expected_books}_of_{expected_books}",
        "normalization_version": NORMALIZATION_VERSION,
        "rules": [
            "Normalize CRLF/CR to LF.",
            "Remove [pagebreak], font, p, and img presentation markup only.",
            "Preserve semantic placeholders such as <Alias=Player> and all prose/punctuation.",
            "Trim trailing line whitespace, collapse 3+ blank lines to 2, trim outer whitespace.",
            "comparison_text additionally lowercases, normalizes smart quotes/dashes, and collapses whitespace.",
        ],
        "records": books,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("continuity_dir", type=Path)
    parser.add_argument(
        "--output",
        type=Path,
        help="Output JSON path (default: analysis/book-normalization-index.json)",
    )
    parser.add_argument("--expected-books", type=int, default=33)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if the existing output differs from a freshly generated index.",
    )
    args = parser.parse_args()

    payload = build(args.continuity_dir, args.expected_books)
    output = args.output or args.continuity_dir / "analysis" / "book-normalization-index.json"
    rendered = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"

    if args.check:
        if not output.exists():
            raise SystemExit(f"missing expected index: {output}")
        current = output.read_text(encoding="utf-8")
        if current != rendered:
            raise SystemExit("book normalization index is stale or non-deterministic")
        print(f"OK: {args.expected_books} BOOK fingerprints match {output}")
        return

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(rendered, encoding="utf-8")
    print(f"Wrote {args.expected_books} BOOK fingerprints to {output}")


if __name__ == "__main__":
    main()
