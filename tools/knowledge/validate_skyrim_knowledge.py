#!/usr/bin/env python3
"""Validate structural and schema integrity of the Skyrim modding knowledge repository."""
from pathlib import Path
import json
import re
import sys

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]
LIB = ROOT / "knowledge" / "libraries" / "skyrim-modding"
TERMS = LIB / "terminology"
INDEX = LIB / "indexes" / "terminology-index.md"
SCHEMAS = ROOT / "schemas"

errors: list[str] = []

def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(f"invalid JSON {path.relative_to(ROOT)}: {exc}")
        return None

def schema(name: str):
    path = SCHEMAS / name
    data = load_json(path)
    if data is not None:
        try:
            Draft202012Validator.check_schema(data)
        except Exception as exc:
            errors.append(f"invalid JSON Schema {path.relative_to(ROOT)}: {exc}")
    return data

def validate(instance, schema_data, label: str):
    if instance is None or schema_data is None:
        return
    validator = Draft202012Validator(schema_data)
    for err in sorted(validator.iter_errors(instance), key=lambda e: list(e.absolute_path)):
        loc = ".".join(str(x) for x in err.absolute_path) or "<root>"
        errors.append(f"{label} at {loc}: {err.message}")

# Markdown/index integrity.
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
    LIB / "automation" / "tool-capability-registry.json",
    LIB / "automation" / "implementation-patterns-core.json",
    LIB / "automation" / "analyzer-rule-pack-core.json",
]
for path in required:
    if not path.exists():
        errors.append(f"required retrieval surface missing: {path.relative_to(ROOT)}")

# Validate every schema definition itself.
for path in sorted(SCHEMAS.glob("skyrim-*.schema.json")):
    data = load_json(path)
    if data is None:
        continue
    try:
        Draft202012Validator.check_schema(data)
    except Exception as exc:
        errors.append(f"invalid JSON Schema {path.relative_to(ROOT)}: {exc}")

adapter_schema = schema("skyrim-tool-adapter-v1.schema.json")
execution_registry_schema = schema("skyrim-tool-adapter-registry-v1.schema.json")
registry_schema = schema("skyrim-tool-capability-registry-v1.schema.json")
rule_schema = schema("skyrim-analyzer-rule-v1.schema.json")
pattern_schema = schema("skyrim-implementation-pattern-v1.schema.json")
runtime_test_schema = schema("skyrim-runtime-test-v1.schema.json")
project_schema = schema("skyrim-mod-project-v1.schema.json")
build_report_schema = schema("skyrim-mod-build-report-v1.schema.json")\nvalidation_gate_registry_schema = schema("skyrim-validation-gate-registry-v1.schema.json")
repair_handler_registry_schema = schema("skyrim-repair-handler-registry-v1.schema.json")

# Adapter manifests.
adapter_dir = LIB / "automation" / "adapters"
adapter_ids: set[str] = set()
aggregate_adapter_registries = 0
if adapter_dir.exists():
    for path in sorted(adapter_dir.glob("*.json")):
        data = load_json(path)
        if isinstance(data, dict) and isinstance(data.get("adapters"), list):
            aggregate_adapter_registries += 1
            validate(data, execution_registry_schema, str(path.relative_to(ROOT)))
            aggregate_ids=[x.get("adapter_id") for x in data.get("adapters",[]) if isinstance(x,dict)]
            if len(aggregate_ids) != len(set(aggregate_ids)):
                errors.append(f"aggregate adapter registry contains duplicate adapter_id values: {path.relative_to(ROOT)}")
            continue
        validate(data, adapter_schema, str(path.relative_to(ROOT)))
        if isinstance(data, dict) and data.get("adapter_id"):
            adapter_id = data["adapter_id"]
            if adapter_id in adapter_ids:
                errors.append(f"duplicate adapter_id: {adapter_id}")
            adapter_ids.add(adapter_id)

# Capability registry.
registry_path = LIB / "automation" / "tool-capability-registry.json"
registry = load_json(registry_path) if registry_path.exists() else None
validate(registry, registry_schema, str(registry_path.relative_to(ROOT)))
if isinstance(registry, dict):
    reg_ids = [x.get("adapter_id") for x in registry.get("adapters", []) if isinstance(x, dict)]
    if len(reg_ids) != len(set(reg_ids)):
        errors.append("tool capability registry contains duplicate adapter_id values")
    for entry in registry.get("adapters", []):
        if not isinstance(entry, dict):
            continue
        manifest = entry.get("adapter_manifest")
        if manifest:
            manifest_path = ROOT / manifest
            if not manifest_path.exists():
                errors.append(f"registry adapter manifest missing: {manifest}")
            else:
                mdata = load_json(manifest_path)
                if isinstance(mdata, dict) and mdata.get("adapter_id") != entry.get("adapter_id"):
                    errors.append(
                        f"registry/manifest adapter_id mismatch: {entry.get('adapter_id')} -> {manifest}"
                    )

# Validation gate registry.
gate_registry_path = LIB / "automation" / "validation-gate-registry.json"
gate_registry = load_json(gate_registry_path) if gate_registry_path.exists() else None
validate(gate_registry, validation_gate_registry_schema, str(gate_registry_path.relative_to(ROOT)))
if isinstance(gate_registry, dict):
    gate_ids = [x.get("gate") for x in gate_registry.get("gates", []) if isinstance(x, dict)]
    if len(gate_ids) != len(set(gate_ids)):
        errors.append("validation gate registry contains duplicate gate ids")
    expected = {f"G{i:02d}" for i in range(30)}
    missing = sorted(expected - set(gate_ids))
    extra = sorted(set(gate_ids) - expected)
    if missing:
        errors.append("validation gate registry missing: " + ", ".join(missing))
    if extra:
        errors.append("validation gate registry has unexpected gates: " + ", ".join(extra))

# Repair handler registry.
repair_handler_path = LIB / "automation" / "repair-handler-registry.json"
repair_handlers = load_json(repair_handler_path) if repair_handler_path.exists() else None
validate(repair_handlers, repair_handler_registry_schema, str(repair_handler_path.relative_to(ROOT)))
if isinstance(repair_handlers, dict):
    handler_ids = [x.get("handler_id") for x in repair_handlers.get("handlers", []) if isinstance(x, dict)]
    handler_rule_ids = [x.get("rule_id") for x in repair_handlers.get("handlers", []) if isinstance(x, dict)]
    if len(handler_ids) != len(set(handler_ids)):
        errors.append("repair handler registry contains duplicate handler_id values")
    if len(handler_rule_ids) != len(set(handler_rule_ids)):
        errors.append("repair handler registry contains multiple automatic handlers for one analyzer rule")

# Analyzer rule pack: validate wrapper fields directly, then every embedded rule.
rule_pack_path = LIB / "automation" / "analyzer-rule-pack-core.json"
rule_pack = load_json(rule_pack_path) if rule_pack_path.exists() else None
if isinstance(rule_pack, dict):
    if rule_pack.get("schema_version") != "skyrim-analyzer-rule-pack-v1":
        errors.append("analyzer rule pack has wrong schema_version")
    rule_ids: set[str] = set()
    for idx, rule in enumerate(rule_pack.get("rules", [])):
        validate(rule, rule_schema, f"{rule_pack_path.relative_to(ROOT)} rules[{idx}]")
        if isinstance(rule, dict) and rule.get("rule_id"):
            rid = rule["rule_id"]
            if rid in rule_ids:
                errors.append(f"duplicate analyzer rule_id: {rid}")
            rule_ids.add(rid)
else:
    errors.append("analyzer rule pack is missing or invalid")

# Repair handlers may only authorize rules present in the canonical analyzer pack.
if isinstance(repair_handlers, dict) and isinstance(rule_pack, dict):
    canonical_rule_ids = {
        x.get("rule_id") for x in rule_pack.get("rules", [])
        if isinstance(x, dict) and x.get("rule_id")
    }
    for handler in repair_handlers.get("handlers", []):
        if not isinstance(handler, dict):
            continue
        if handler.get("rule_id") not in canonical_rule_ids:
            errors.append(
                f"repair handler {handler.get('handler_id')} references unregistered analyzer rule "
                f"{handler.get('rule_id')}"
            )

# Legacy analyzer mirror must exactly follow the canonical pack.
legacy_rule_path = LIB / "automation" / "analyzers" / "core-rules.json"
if legacy_rule_path.exists() and isinstance(rule_pack, dict):
    legacy_rules = load_json(legacy_rule_path)
    if not isinstance(legacy_rules, dict):
        errors.append("legacy analyzer mirror is invalid")
    else:
        if legacy_rules.get("generated_from") != "knowledge/libraries/skyrim-modding/automation/analyzer-rule-pack-core.json":
            errors.append("legacy analyzer mirror does not identify canonical generated_from path")
        canonical_ids = [x.get("rule_id") for x in rule_pack.get("rules", []) if isinstance(x, dict)]
        legacy_ids = [x.get("rule_id") for x in legacy_rules.get("rules", []) if isinstance(x, dict)]
        if canonical_ids != legacy_ids:
            errors.append("legacy analyzer mirror diverges from canonical analyzer-rule-pack-core.json")

# Implementation pattern pack.
pattern_pack_path = LIB / "automation" / "implementation-patterns-core.json"
pattern_pack = load_json(pattern_pack_path) if pattern_pack_path.exists() else None
if isinstance(pattern_pack, dict):
    if pattern_pack.get("schema_version") != "skyrim-implementation-pattern-pack-v1":
        errors.append("implementation pattern pack has wrong schema_version")
    pattern_ids: set[str] = set()
    for idx, pattern in enumerate(pattern_pack.get("patterns", [])):
        validate(pattern, pattern_schema, f"{pattern_pack_path.relative_to(ROOT)} patterns[{idx}]")
        if isinstance(pattern, dict) and pattern.get("pattern_id"):
            pid = pattern["pattern_id"]
            if pid in pattern_ids:
                errors.append(f"duplicate implementation pattern_id: {pid}")
            pattern_ids.add(pid)
else:
    errors.append("implementation pattern pack is missing or invalid")

# The schemas below may not yet have checked-in instances, but checking/loading them
# here makes CI fail immediately if future edits make them invalid.
for name, value in [
    ("runtime test", runtime_test_schema),
    ("project manifest", project_schema),
    ("build report", build_report_schema),
]:
    if value is None:
        errors.append(f"{name} schema could not be loaded")

if errors:
    print("Skyrim knowledge validation FAILED:")
    for error in errors:
        print(f"- {error}")
    sys.exit(1)

print(
    "Skyrim knowledge validation passed: "
    f"{len(modules)} terminology modules, {len(adapter_ids)} adapter manifests, "
    f"{aggregate_adapter_registries} aggregate adapter registries, "
    f"{len(gate_registry.get('gates', [])) if isinstance(gate_registry, dict) else 0} validation gates, "\n    f"{len(rule_pack.get('rules', [])) if isinstance(rule_pack, dict) else 0} analyzer rules, "
    f"{len(pattern_pack.get('patterns', [])) if isinstance(pattern_pack, dict) else 0} implementation patterns."
)
