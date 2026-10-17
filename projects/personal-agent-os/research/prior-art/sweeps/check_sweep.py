"""Check one prior-art sweep batch: its markdown sections and registry entries.

Usage: python check_sweep.py <batch> [--dir DIR]
Exits non-zero and prints every problem when the batch is incomplete.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / "src"))

from agent_os.orchestrator.prior_art import entry_problems  # noqa: E402

LABELS = ("Repository:", "License:", "What it does:", "Claims vs evidence:", "Fit for Agent OS:", "Test to run:", "Verdict:")
VERDICTS = {"BORROW", "WRAP", "DEFER", "REJECT", "INVESTIGATE"}


def problems(batch: str, directory: Path) -> list[str]:
    found: list[str] = []
    md_path, json_path = directory / f"{batch}.md", directory / f"{batch}.json"
    if not md_path.exists():
        return [f"missing {md_path.name}"]
    sections = re.split(r"^## ", md_path.read_text(encoding="utf-8"), flags=re.M)[1:]
    if not sections:
        found.append(f"{md_path.name}: no '## <Project>' sections")
    names = []
    for section in sections:
        name = section.splitlines()[0].strip()
        names.append(name)
        for label in LABELS:
            if not re.search(rf"^\s*[-*]?\s*\**{re.escape(label[:-1])}\**:", section, re.M):
                found.append(f"{name}: missing '{label}' line")
        verdict = re.search(r"Verdict:\**\s*\**([A-Z]+)", section)
        if verdict and verdict.group(1) not in VERDICTS:
            found.append(f"{name}: verdict {verdict.group(1)} is not one of {sorted(VERDICTS)}")
    if not json_path.exists():
        found.append(f"missing {json_path.name}")
        return found
    try:
        entries = json.loads(json_path.read_text(encoding="utf-8")).get("entries")
    except (ValueError, AttributeError) as exc:
        return found + [f"{json_path.name}: not a JSON object with entries ({exc})"]
    if not isinstance(entries, list) or not entries:
        return found + [f"{json_path.name}: entries must be a non-empty list"]
    for entry in entries:
        found.extend(entry_problems(entry))
        if isinstance(entry, dict) and entry.get("decision") == "ADOPT":
            found.append(f"{entry.get('id')}: ADOPT is not allowed in a sweep")
    if len(entries) != len(sections):
        found.append(f"{len(sections)} markdown sections but {len(entries)} registry entries")
    return found


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("batch")
    parser.add_argument("--dir", default=str(Path(__file__).resolve().parent / "2026-10-17-oss"))
    args = parser.parse_args()
    found = problems(args.batch, Path(args.dir))
    for item in found:
        print(item)
    print("ok" if not found else f"{len(found)} problem(s)")
    return 1 if found else 0


if __name__ == "__main__":
    raise SystemExit(main())
