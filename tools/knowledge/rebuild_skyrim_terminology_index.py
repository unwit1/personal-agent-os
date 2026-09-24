#!/usr/bin/env python3
"""Rebuild the Skyrim modding terminology index from the repository itself."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LIB = ROOT / "knowledge" / "libraries" / "skyrim-modding"
TERMS = LIB / "terminology"
OUT = LIB / "indexes" / "terminology-index.md"

rows = []
for path in sorted(TERMS.glob("*.md")):
    text = path.read_text(encoding="utf-8")
    headings = sum(1 for line in text.splitlines() if line.startswith("### "))
    rows.append((path.name, headings))

total = sum(count for _, count in rows)
lines = [
    "# Skyrim Modding Terminology Index",
    "",
    "Status: generated from repository contents",
    f"Terminology modules: {len(rows)}",
    f"Indexed terminology headings: {total}",
    "",
    "Counts include intentional cross-module repetition. The heading total is not a unique-concept count.",
    "",
    "## Retrieval strategy",
    "",
    "Start with `../troubleshooting/diagnostic-router.md` for symptom-driven work and retrieve only the relevant specialist modules.",
    "",
    "## Modules",
    "",
    "| Module | Indexed headings |",
    "|---|---:|",
]
for name, count in rows:
    lines.append(f"| [{name}](../terminology/{name}) | {count} |")

lines += [
    "",
    "## Maintenance",
    "",
    "This file is generated. Run `python tools/knowledge/rebuild_skyrim_terminology_index.py` after adding, removing, or reorganizing terminology modules.",
]
OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"Wrote {OUT} with {len(rows)} modules / {total} headings")
