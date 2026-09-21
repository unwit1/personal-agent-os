"""Dependency-free, shared runtime and JSON Schema lifecycle contracts."""
from __future__ import annotations

import math
from typing import Any


def text(limit=2000):
    return {"type": "string", "maxLength": limit}


def array(items=None, limit=20):
    return {"type": "array", "items": items or text(), "maxItems": limit}


def obj(properties, required=()):
    return {"type": "object", "properties": properties, "required": list(required), "additionalProperties": False}


DECISION = obj({"decision": text(), "rationale_summary": text(), "evidence": array(),
                "alternatives": array(), "uncertainties": array(), "risks": array()},
               ("decision", "rationale_summary"))
VALIDATION = obj({"status": {"enum": ["passed", "failed", "not_run"]}, "checks": array()}, ("status", "checks"))
CANDIDATE = obj({"kind": {"enum": ["decision_candidate", "lesson_candidate", "skill_candidate", "skill_patch_candidate",
                                     "preference_candidate", "project_state_candidate", "prompt_optimization_candidate",
                                     "test_candidate", "deterministic_rule_candidate", "documentation_candidate"]},
                 "statement": text(), "evidence": array(), "confidence": {"type": "number", "minimum": 0, "maximum": 1}},
                ("kind", "statement", "evidence"))
CHANGE = obj({"title": text(180), "request_summary": text(), "change_type": {"enum": ["bug", "feature", "refactor", "workflow", "performance", "security", "test", "documentation", "architecture", "other"]},
              "components": array(), "repository_files": array(), "diagnosis_summary": text(), "fix_summary": text()},
             ("title", "request_summary", "change_type"))
IMPROVEMENT = obj({"title": text(160), "category": {"enum": ["bug", "performance", "architecture", "missing_test", "documentation", "skill_candidate", "workflow", "security", "privacy", "other"]},
                   "observation": text(), "suggested_direction": text(), "acceptance": array(), "evidence": array(),
                   "subsystem": text(), "priority": {"enum": ["critical", "high", "medium", "low"]}, "risks": array()},
                  ("title", "category", "observation", "suggested_direction", "acceptance", "evidence"))
POSTFLIGHT = obj({
    "summary": {**text(), "minLength": 1}, "sanitized": {"type": "boolean"},
    "decisions": array(DECISION), "evidence": array(), "assumptions": array(), "uncertainties": array(),
    "risks": array(), "files_changed": array(text(500), 200), "actions": array(),
    "validation": VALIDATION, "remaining": array(), "lessons": array(CANDIDATE),
    "proposed_memories": array(CANDIDATE), "proposed_skills": array(CANDIDATE),
    "proposed_changes": array(CHANGE, 5), "proposed_improvements": array(IMPROVEMENT, 5),
    "architecture_change": {"type": "boolean"}, "destructive_change": {"type": "boolean"},
    "cross_project": {"type": "boolean"},
}, ("summary", "sanitized", "decisions", "evidence", "files_changed", "validation", "remaining"))
PROVIDER_RESULT = obj({"response": text(100000), "postflight": POSTFLIGHT}, ("response", "postflight"))
REVIEW_RESULT = obj({"status": {"enum": ["pass", "pass_with_notes", "changes_requested"]}, "findings": array()}, ("status", "findings"))
BEGIN_INPUT = obj({"query": {**text(200000), "minLength": 1}, "source_client": text(64),
                   "source_session": {"type": ["string", "null"]}, "project_hint": {"type": ["string", "null"]},
                   "token_budget": {"type": "integer", "minimum": 800, "maximum": 32000},
                   "execution_metadata": {"type": "object"}}, ("query", "source_client"))
CONTINUE_INPUT = obj({"task_id": text(), "query": text(200000),
                      "token_budget": {"type": "integer", "minimum": 800, "maximum": 32000},
                      "reset_context": {"type": "boolean"}, "resume": {"type": "boolean"}}, ("task_id", "query"))
FINISH_INPUT = obj({"task_id": text(), "postflight": POSTFLIGHT}, ("task_id", "postflight"))
ABORT_INPUT = obj({"task_id": text(), "stage": {"enum": ["preflight", "execution", "postflight"]},
                   "error_class": {"enum": ["preflight_failed", "execution_failed", "interrupted", "timeout", "postflight_failed", "invalid_result", "client_unavailable"]},
                   "partial_changes": {"type": "boolean"},
                   "validation_status": {"enum": ["unknown", "passed", "failed", "not_run"]}}, ("task_id",))
ENVELOPE = obj({"schema_version": {"const": 1}, "task_id": text(40), "source": {"type": "object"},
                "routing": {"type": "object"}, "request": {"type": "object"}, "privacy": {"type": "object"},
                "requirements": {"type": "object"}, "preflight_completed": {"const": True},
                "context_mode": {"enum": ["full", "delta"]}, "context": {"type": "object"},
                "measurement": {"type": "object"}},
               ("schema_version", "task_id", "source", "routing", "request", "privacy", "requirements", "preflight_completed", "context_mode", "context", "measurement"))
TRACE = obj({"schema_version": {"const": 1}, "task_id": text(40), "project": text(), "prompt_hash": text(64),
             "source": {"type": "object"}, "postflight": POSTFLIGHT, "review": {"type": "object"},
             "artifacts": {"type": "object"}, "outcome": {"enum": ["completed", "validation_failed", "review_required"]},
             "status": {"const": "unverified"}, "created_at": text()},
            ("schema_version", "task_id", "project", "prompt_hash", "source", "postflight", "review", "artifacts", "outcome", "status", "created_at"))


def validate_contract(value: Any, schema: dict, label="payload") -> None:
    """Validate our intentionally small JSON Schema subset without echoing input."""
    if "enum" in schema and value not in schema["enum"]:
        raise ValueError(f"{label}: unsupported value")
    if "const" in schema and value != schema["const"]:
        raise ValueError(f"{label}: unsupported version")
    kind = schema.get("type")
    types = {"object": dict, "array": list, "string": str, "boolean": bool, "integer": int, "number": (int, float), "null": type(None)}
    if kind:
        kinds = kind if isinstance(kind, list) else [kind]
        if not any(isinstance(value, types[k]) and not (k in {"integer", "number"} and isinstance(value, bool)) for k in kinds):
            raise ValueError(f"{label}: invalid type")
    if isinstance(value, dict):
        if set(schema.get("required", [])) - value.keys():
            raise ValueError(f"{label}: missing required fields")
        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False and set(value) - properties.keys():
            raise ValueError(f"{label}: unexpected fields")
        for key, item in value.items():
            if key in properties:
                validate_contract(item, properties[key], f"{label}.{key}")
    if isinstance(value, list):
        if len(value) > schema.get("maxItems", 10000):
            raise ValueError(f"{label}: too many items")
        for item in value:
            validate_contract(item, schema.get("items", {}), label)
    if isinstance(value, str) and not schema.get("minLength", 0) <= len(value) <= schema.get("maxLength", 1000000):
        raise ValueError(f"{label}: invalid length")
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if not math.isfinite(value) or not schema.get("minimum", -math.inf) <= value <= schema.get("maximum", math.inf):
            raise ValueError(f"{label}: invalid number")
