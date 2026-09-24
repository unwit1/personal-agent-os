#!/usr/bin/env python3
"""Validate structural integrity of the Skyrim modding knowledge repository."""
from pathlib import Path
import re, sys

ROOT = Path(__file__).resolve().parents[2]
LIB = ROOT / "knowledge" / "libraries" / "skyrim-modding"
TERMS = LIB / "terminology"
INDEX = LIB / "indexes" / "terminology-index.md"

errors = []
modules = sorted(p.name for p in TERMS.glob("*.md"))
if not INDEX.exists():
    errors.append("terminology-index.md is missing")
    index_text = ""
else:
    index_text = INDEX.read_text(encoding="utf-8")

m = re.search(r"Terminology modules:\s*(\d+)", index_text)
if not m:
    errors.append("terminology index has no module-count line")
elif int(m.group(1)) != len(modules):
    errors.append(f"index says {m.group(1)} modules but terminology/ contains {len(modules)}")

linked = set(re.findall(r"\.\./terminology/([^\)\s]+\.md)", index_text))
missing_links = sorted(set(modules) - linked)
stale_links = sorted(linked - set(modules))
if missing_links:
    errors.append("modules missing from index: " + ", ".join(missing_links))
if stale_links:
    errors.append("stale index links: " + ", ".join(stale_links))

required = [
    LIB / "troubleshooting" / "diagnostic-router.md",
    LIB / "troubleshooting" / "tool-error-catalog.md",
    LIB / "troubleshooting" / "compatibility-patterns.md",
    LIB / "sources" / "registry.md",
    LIB / "research" / "frontier.md",
    LIB / "research" / "version-provenance-model.md",
]
for p in required:
    if not p.exists():
        errors.append(f"required retrieval surface missing: {p.relative_to(ROOT)}")

if errors:
    print("Skyrim knowledge validation FAILED:")
    for e in errors:
        print(f"- {e}")
    sys.exit(1)

print(f"Skyrim knowledge validation passed: {len(modules)} terminology modules indexed.")
