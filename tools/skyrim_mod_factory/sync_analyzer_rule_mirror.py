#!/usr/bin/env python3
"""Regenerate the legacy analyzer mirror from the canonical Skyrim rule pack."""
from pathlib import Path
import json

ROOT=Path(__file__).resolve().parents[2]
base=ROOT/"knowledge"/"libraries"/"skyrim-modding"/"automation"
source=base/"analyzer-rule-pack-core.json"
target=base/"analyzers"/"core-rules.json"

data=json.loads(source.read_text(encoding="utf-8"))
mirror={
    "schema_version":"skyrim-analyzer-rule-registry-v1",
    "generated_from":"knowledge/libraries/skyrim-modding/automation/analyzer-rule-pack-core.json",
    "note":"Compatibility mirror. The canonical rule pack is analyzer-rule-pack-core.json; regenerate this file rather than editing it directly.",
    "rules":data.get("rules",[]),
}
target.parent.mkdir(parents=True,exist_ok=True)
target.write_text(json.dumps(mirror,indent=2)+"\n",encoding="utf-8")
print(f"Wrote {target} with {len(mirror['rules'])} rules")
