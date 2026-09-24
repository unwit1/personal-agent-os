#!/usr/bin/env python3
"""Validate and unpack the Trainwiz ChronoC0da current-snapshot corpus.

The repository stores deterministic gzip segments as base64 text so GitHub's text-only
connector can preserve the complete extracted corpus. Each decoded segment is JSONL;
each row carries a virtual path, its expected SHA-256, and the complete UTF-8 content.
"""
from __future__ import annotations
import argparse, base64, gzip, hashlib, json
from pathlib import Path


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    ap=argparse.ArgumentParser()
    ap.add_argument('continuity_dir', type=Path, help='trainwiz-chronocoda directory')
    ap.add_argument('--output', type=Path, help='directory for reconstructed virtual files')
    ap.add_argument('--check', action='store_true', help='validate only; do not write files')
    args=ap.parse_args()
    root=args.continuity_dir
    manifest=json.loads((root/'corpus'/'manifest.json').read_text(encoding='utf-8'))
    output=args.output or root/'reconstructed-current-snapshot'
    seen: dict[str,str]={}
    count=0
    for seg in manifest['segments']:
        storage=root/'corpus'/seg['storage_file']
        encoded=''.join(storage.read_text(encoding='ascii').split())
        compressed=base64.b64decode(encoded, validate=True)
        got=sha256_bytes(compressed)
        if got != seg['sha256']:
            raise SystemExit(f"segment SHA mismatch: {storage.name}: {got} != {seg['sha256']}")
        raw=gzip.decompress(compressed).decode('utf-8')
        for line_no,line in enumerate(raw.splitlines(),1):
            if not line.strip(): continue
            row=json.loads(line)
            path=row['path']; content=row['content']; expected=row['sha256']
            actual=hashlib.sha256(content.encode('utf-8')).hexdigest()
            if actual != expected:
                raise SystemExit(f"virtual SHA mismatch: {storage.name}:{line_no} {path}")
            if path in seen:
                if seen[path] != actual:
                    raise SystemExit(f"conflicting duplicate virtual path: {path}")
                continue
            seen[path]=actual; count += 1
            if not args.check:
                target=output/path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(content, encoding='utf-8')
    expected=manifest.get('virtual_artifact_count')
    if expected is not None and count != expected:
        raise SystemExit(f"virtual artifact count mismatch: {count} != {expected}")
    print(f"OK: {len(manifest['segments'])} segments, {count} virtual artifacts validated")
    if not args.check: print(f"Reconstructed under {output}")

if __name__=='__main__': main()