#!/usr/bin/env python3
"""Build a provenance-aware LEGO minifigure reference manifest from Rebrickable bulk CSVs.

This tool indexes metadata and source image URLs. It does NOT mirror the image corpus into
Git. Raw reference images should be materialized into a local research directory by a
separate fetcher that respects source terms and records hashes/provenance.

Required Rebrickable bulk files:
  minifigs.csv(.gz)
  inventories.csv(.gz)
  inventory_minifigs.csv(.gz)
  sets.csv(.gz)
  themes.csv(.gz)

Optional:
  inventory_parts.csv(.gz)
  parts.csv(.gz)
  colors.csv(.gz)

Outputs:
  physical_samples.jsonl
  reference_manifest.jsonl
  corpus.sqlite3
  import_report.json
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import sqlite3
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Iterator

PROCESSOR_VERSION = "lego-reference-manifest/v1"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def open_text(path: Path):
    if path.suffix == ".gz":
        return gzip.open(path, "rt", encoding="utf-8-sig", newline="")
    return path.open("r", encoding="utf-8-sig", newline="")


def resolve_table(root: Path, name: str) -> Path:
    for candidate in (root / f"{name}.csv.gz", root / f"{name}.csv"):
        if candidate.exists():
            return candidate
    raise FileNotFoundError(f"missing Rebrickable table: {name}.csv(.gz) in {root}")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def rows(path: Path) -> Iterator[dict[str, str]]:
    with open_text(path) as f:
        yield from csv.DictReader(f)


def theme_ancestry(theme_id: str, themes: dict[str, dict[str, str]]) -> list[dict[str, str]]:
    result: list[dict[str, str]] = []
    seen: set[str] = set()
    current = theme_id
    while current and current not in seen and current in themes:
        seen.add(current)
        item = themes[current]
        result.append({"id": current, "name": item.get("name", "")})
        current = item.get("parent_id", "") or ""
    return result


def stable_id(kind: str, *parts: str) -> str:
    payload = json.dumps([kind, *parts], separators=(",", ":"), ensure_ascii=False)
    return f"{kind}-{hashlib.sha256(payload.encode()).hexdigest()[:24]}"


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        PRAGMA journal_mode=WAL;
        CREATE TABLE IF NOT EXISTS sample (
            sample_id TEXT PRIMARY KEY,
            fig_num TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            num_parts INTEGER,
            image_url TEXT,
            medium TEXT NOT NULL,
            authority TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS set_occurrence (
            sample_id TEXT NOT NULL,
            set_num TEXT NOT NULL,
            set_name TEXT,
            year INTEGER,
            theme_id TEXT,
            theme_path_json TEXT,
            quantity INTEGER,
            PRIMARY KEY(sample_id, set_num)
        );
        CREATE TABLE IF NOT EXISTS reference_asset (
            reference_asset_id TEXT PRIMARY KEY,
            sample_id TEXT NOT NULL,
            medium TEXT NOT NULL,
            authority TEXT NOT NULL,
            source_url TEXT NOT NULL,
            source_role TEXT NOT NULL,
            sha256 TEXT,
            retrieved_at TEXT
        );
        CREATE TABLE IF NOT EXISTS source_file (
            table_name TEXT PRIMARY KEY,
            path TEXT NOT NULL,
            sha256 TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_occurrence_set ON set_occurrence(set_num);
        CREATE INDEX IF NOT EXISTS idx_occurrence_theme ON set_occurrence(theme_id);
        """
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rebrickable-dir", type=Path, required=True)
    ap.add_argument("--output-dir", type=Path, required=True)
    args = ap.parse_args()

    root = args.rebrickable_dir.resolve()
    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)

    required = ["minifigs", "inventories", "inventory_minifigs", "sets", "themes"]
    files = {name: resolve_table(root, name) for name in required}

    source_hashes = {name: sha256_file(path) for name, path in files.items()}

    themes = {r["id"]: r for r in rows(files["themes"])}
    sets = {r["set_num"]: r for r in rows(files["sets"])}

    inventory_to_set: dict[str, str] = {}
    for r in rows(files["inventories"]):
        inventory_to_set[r["id"]] = r["set_num"]

    fig_occurrences: dict[str, list[dict[str, object]]] = defaultdict(list)
    for r in rows(files["inventory_minifigs"]):
        fig_num = r["fig_num"]
        set_num = inventory_to_set.get(r["inventory_id"])
        if not set_num:
            continue
        set_row = sets.get(set_num, {})
        theme_id = set_row.get("theme_id", "")
        try:
            qty = int(r.get("quantity") or 0)
        except ValueError:
            qty = 0
        try:
            year = int(set_row.get("year") or 0)
        except ValueError:
            year = 0
        fig_occurrences[fig_num].append(
            {
                "set_num": set_num,
                "set_name": set_row.get("name", ""),
                "year": year or None,
                "theme_id": theme_id or None,
                "theme_path": theme_ancestry(theme_id, themes) if theme_id else [],
                "quantity": qty,
            }
        )

    db_path = out / "corpus.sqlite3"
    conn = sqlite3.connect(db_path)
    init_db(conn)
    for name, path in files.items():
        conn.execute(
            "INSERT OR REPLACE INTO source_file(table_name,path,sha256) VALUES(?,?,?)",
            (name, str(path), source_hashes[name]),
        )

    samples_path = out / "physical_samples.jsonl"
    refs_path = out / "reference_manifest.jsonl"

    sample_count = 0
    ref_count = 0
    set_links = 0
    figures_without_image = 0
    figures_without_set = 0

    with samples_path.open("w", encoding="utf-8") as sf, refs_path.open("w", encoding="utf-8") as rf:
        for r in rows(files["minifigs"]):
            fig_num = r["fig_num"]
            sample_id = stable_id("sample", "rebrickable", fig_num)
            image_url = (r.get("img_url") or "").strip()
            try:
                num_parts = int(r.get("num_parts") or 0)
            except ValueError:
                num_parts = 0

            occurrences = sorted(
                fig_occurrences.get(fig_num, []),
                key=lambda x: ((x.get("year") or 0), str(x.get("set_num") or "")),
            )
            if not occurrences:
                figures_without_set += 1
            if not image_url:
                figures_without_image += 1

            sample = {
                "sample_id": sample_id,
                "medium": "physical",
                "authority": "structured_catalog",
                "source_catalog": "rebrickable",
                "fig_num": fig_num,
                "name": r.get("name", ""),
                "num_parts": num_parts,
                "catalog_image_url": image_url or None,
                "set_occurrences": occurrences,
                "bricklink_catalog_url": f"https://www.bricklink.com/v2/catalog/catalogitem.page?M={fig_num}",
                "processor_version": PROCESSOR_VERSION,
            }
            sf.write(json.dumps(sample, ensure_ascii=False) + "\n")

            conn.execute(
                "INSERT OR REPLACE INTO sample(sample_id,fig_num,name,num_parts,image_url,medium,authority) VALUES(?,?,?,?,?,?,?)",
                (sample_id, fig_num, sample["name"], num_parts, image_url or None, "physical", "structured_catalog"),
            )

            for occ in occurrences:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO set_occurrence
                    (sample_id,set_num,set_name,year,theme_id,theme_path_json,quantity)
                    VALUES(?,?,?,?,?,?,?)
                    """,
                    (
                        sample_id,
                        occ["set_num"],
                        occ["set_name"],
                        occ["year"],
                        occ["theme_id"],
                        json.dumps(occ["theme_path"], ensure_ascii=False),
                        occ["quantity"],
                    ),
                )
                set_links += 1

            if image_url:
                ref_id = stable_id("ref", "rebrickable", fig_num, image_url)
                ref = {
                    "reference_asset_id": ref_id,
                    "sample_id": sample_id,
                    "medium": "physical_render_or_catalog_photo",
                    "authority": "structured_catalog",
                    "source_catalog": "rebrickable",
                    "source_url": image_url,
                    "source_role": "catalog_primary_image",
                    "materialized_locally": False,
                    "sha256": None,
                    "perceptual_hash": None,
                    "retrieved_at": None,
                }
                rf.write(json.dumps(ref, ensure_ascii=False) + "\n")
                conn.execute(
                    """
                    INSERT OR REPLACE INTO reference_asset
                    (reference_asset_id,sample_id,medium,authority,source_url,source_role,sha256,retrieved_at)
                    VALUES(?,?,?,?,?,?,?,?)
                    """,
                    (ref_id, sample_id, ref["medium"], ref["authority"], image_url, ref["source_role"], None, None),
                )
                ref_count += 1
            sample_count += 1

    conn.commit()
    conn.close()

    report = {
        "schema": "lego-minifigure-reference-import/v1",
        "processor_version": PROCESSOR_VERSION,
        "created_at": now_iso(),
        "source_root": str(root),
        "source_files": {
            name: {"path": str(path), "sha256": source_hashes[name]}
            for name, path in files.items()
        },
        "outputs": {
            "samples": str(samples_path),
            "references": str(refs_path),
            "sqlite": str(db_path),
        },
        "counts": {
            "physical_samples": sample_count,
            "reference_assets": ref_count,
            "set_occurrence_links": set_links,
            "figures_without_catalog_image": figures_without_image,
            "figures_without_set_occurrence": figures_without_set,
        },
        "raw_image_policy": "not mirrored by this tool; materialize locally with source-specific fetch policy",
    }
    (out / "import_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report["counts"], indent=2))


if __name__ == "__main__":
    main()
