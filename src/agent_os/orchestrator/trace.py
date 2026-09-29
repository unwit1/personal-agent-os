"""OpenTelemetry-compatible trace projection: ``agent-os orchestrate trace``.

Converts one orchestrated run's append-only telemetry
(``<orchestrator home>/runs/<run-id>/telemetry.jsonl``) into OTLP/JSON spans
that any OpenTelemetry backend can load (MIE-0017). No dependency: the
GenAI semantic conventions (prior art PA-otel-genai) are borrowed as attribute
names only.

Span tree:

* ``invoke_workflow <run-id>`` -- the run (workflow/agent conventions are
  still provisional upstream; marked ``agent_os.semconv_status=provisional``);
* ``node <id>`` -- each planned node (implementer, reviewer, repairer, ...);
* ``invoke_agent <role>`` -- each model worker call, with
  ``gen_ai.operation.name``, ``gen_ai.provider.name``, ``gen_ai.request.model``,
  ``gen_ai.response.model`` (the concrete model), ``gen_ai.usage.*`` and
  ``error.type`` on failure;
* ``execute_tool validators`` -- each validation step.

Everything else (routing decisions, checkpoints, commits, reviews) becomes a
span event. **Privacy boundary:** only allowlisted structural fields are
exported; goals, prompts, summaries, details and file contents never are.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from .ledger import read_events
from .store import orchestrator_home

SCOPE = {"name": "agent-os.orchestrator.trace", "version": "1"}
# Only these event-data keys may appear in exported attributes or events.
ALLOWED_KEYS = {
    "role", "provider", "model", "capability_class", "effort", "attempt", "escalations", "tier", "failure_kind", "duration_ms",
    "passed", "duration_s", "tests_run", "tests_passed", "tests_failed", "validators", "selection", "selected", "of", "reused",
    "verdict", "findings", "material_findings", "independent_provider", "round", "subject", "commit", "new_commit", "label", "branch",
    "integrated", "nodes", "planning", "auto_continue", "mode", "guard", "category", "model_calls_avoided", "from_provider", "reason_kind",
}
USAGE_KEYS = {"input_tokens": "gen_ai.usage.input_tokens", "output_tokens": "gen_ai.usage.output_tokens",
              "cache_read_tokens": "gen_ai.usage.cache_read_input_tokens", "reasoning_tokens": "agent_os.usage.reasoning_tokens"}


def telemetry_path(run_id: str, home: Path | None = None) -> Path:
    return Path(home or orchestrator_home()) / "runs" / run_id / "telemetry.jsonl"


def _nanos(stamp: str | None) -> str:
    if not stamp:
        return "0"
    return str(int(datetime.fromisoformat(stamp).timestamp() * 1_000_000_000))


def _id(run_id: str, key: str, length: int) -> str:
    return hashlib.sha256(f"{run_id}|{key}".encode()).hexdigest()[:length]


def _value(value: Any) -> dict[str, Any]:
    if isinstance(value, bool):
        return {"boolValue": value}
    if isinstance(value, int):
        return {"intValue": str(value)}
    if isinstance(value, float):
        return {"doubleValue": value}
    return {"stringValue": str(value)[:200]}


def _attributes(pairs: dict[str, Any]) -> list[dict[str, Any]]:
    return [{"key": key, "value": _value(value)} for key, value in sorted(pairs.items()) if value is not None]


def _clean(data: dict[str, Any], prefix: str = "agent_os.") -> dict[str, Any]:
    return {prefix + key: value for key, value in (data or {}).items() if key in ALLOWED_KEYS and isinstance(value, (str, int, float, bool))}


class _Span:
    def __init__(self, run_id: str, key: str, name: str, parent: str | None, start: str | None) -> None:
        self.span_id = _id(run_id, key, 16)
        self.name = name
        self.parent = parent
        self.start = start
        self.end = start
        self.attributes: dict[str, Any] = {}
        self.events: list[dict[str, Any]] = []
        self.error: str | None = None

    def touch(self, stamp: str | None) -> None:
        if stamp and (self.end is None or stamp > self.end):
            self.end = stamp

    def as_otlp(self, trace_id: str) -> dict[str, Any]:
        span = {"traceId": trace_id, "spanId": self.span_id, "name": self.name, "kind": 1,
                "startTimeUnixNano": _nanos(self.start), "endTimeUnixNano": _nanos(self.end or self.start),
                "attributes": _attributes(self.attributes), "events": self.events,
                "status": {"code": 2, "message": self.error[:120]} if self.error else {"code": 1}}
        if self.parent:
            span["parentSpanId"] = self.parent
        return span


def project(events: list[dict[str, Any]], run_id: str) -> dict[str, Any]:
    trace_id = _id(run_id, "trace", 32)
    events = sorted(events, key=lambda event: (event.get("at") or "", event.get("seq") or 0))
    root = _Span(run_id, "root", f"invoke_workflow {run_id}", None, events[0]["at"] if events else None)
    root.attributes.update({"gen_ai.operation.name": "invoke_workflow", "gen_ai.agent.name": "agent-os-orchestrator",
                            "agent_os.run_id": run_id, "agent_os.semconv_status": "provisional"})
    nodes: dict[str, _Span] = {}
    open_model: dict[str, _Span] = {}
    open_tests: dict[str, _Span] = {}
    spans: list[_Span] = [root]
    counters: dict[str, int] = {}

    def node_span(node_id: str, stamp: str) -> _Span:
        if node_id not in nodes:
            span = _Span(run_id, f"node|{node_id}", f"node {node_id}", root.span_id, stamp)
            span.attributes["agent_os.node_id"] = node_id
            nodes[node_id] = span
            spans.append(span)
        return nodes[node_id]

    for event in events:
        kind, stamp, node_id, data = event["type"], event.get("at"), event.get("node"), event.get("data") or {}
        root.touch(stamp)
        if kind in {"run_completed", "run_failed"}:
            root.attributes.update(_clean(data))
            if kind == "run_failed":
                root.error = "run_failed"
            continue
        if kind == "run_started":
            root.attributes.update(_clean(data))
            continue
        if not node_id:
            root.events.append({"timeUnixNano": _nanos(stamp), "name": kind, "attributes": _attributes(_clean(data))})
            continue
        parent = node_span(node_id, stamp)
        parent.touch(stamp)
        if data.get("role"):
            parent.attributes["agent_os.role"] = data["role"]
        if kind in {"model_started", "review_started"}:
            counters[node_id] = counters.get(node_id, 0) + 1
            span = _Span(run_id, f"model|{node_id}|{counters[node_id]}", f"invoke_agent {data.get('role') or 'worker'}", parent.span_id, stamp)
            span.attributes.update({"gen_ai.operation.name": "invoke_agent", "gen_ai.agent.name": data.get("role"),
                                    "gen_ai.provider.name": data.get("provider"), "gen_ai.request.model": data.get("model")})
            open_model[node_id] = span
            spans.append(span)
        elif kind in {"model_completed", "model_failed"}:
            span = open_model.pop(node_id, None)
            if span is None:  # completion without a start (resumed run): synthesize
                counters[node_id] = counters.get(node_id, 0) + 1
                span = _Span(run_id, f"model|{node_id}|{counters[node_id]}", f"invoke_agent {data.get('role') or 'worker'}", parent.span_id, stamp)
                span.attributes.update({"gen_ai.operation.name": "invoke_agent", "gen_ai.provider.name": data.get("provider"), "gen_ai.request.model": data.get("model")})
                spans.append(span)
            span.touch(stamp)
            usage = data.get("usage") or {}
            span.attributes["gen_ai.response.model"] = usage.get("model_resolved") or data.get("model")
            for key, name in USAGE_KEYS.items():
                if isinstance(usage.get(key), int):
                    span.attributes[name] = usage[key]
            if usage.get("accuracy"):
                span.attributes["agent_os.usage.accuracy"] = usage["accuracy"]
            span.attributes.update(_clean({key: data.get(key) for key in ("capability_class", "effort", "attempt", "duration_ms")}))
            if data.get("failure_kind") or kind == "model_failed":
                span.error = str(data.get("failure_kind") or "failed")
                span.attributes["error.type"] = span.error
        elif kind == "tests_started":
            span = _Span(run_id, f"tests|{node_id}|{event.get('seq')}", "execute_tool validators", parent.span_id, stamp)
            span.attributes.update({"gen_ai.operation.name": "execute_tool", "gen_ai.tool.name": "validators"})
            open_tests[node_id] = span
            spans.append(span)
        elif kind == "tests_completed":
            span = open_tests.pop(node_id, None) or _Span(run_id, f"tests|{node_id}|{event.get('seq')}", "execute_tool validators", parent.span_id, stamp)
            if span not in spans:
                span.attributes.update({"gen_ai.operation.name": "execute_tool", "gen_ai.tool.name": "validators"})
                spans.append(span)
            span.touch(stamp)
            span.attributes.update(_clean(data))
            if data.get("passed") is False:
                span.error = "validation_failed"
                span.attributes["error.type"] = "validation_failed"
        else:
            parent.events.append({"timeUnixNano": _nanos(stamp), "name": kind, "attributes": _attributes(_clean(data))})
    for span in spans:
        if span is not root:
            nodes_parent = next((node for node in nodes.values() if node.span_id == span.parent), None)
            if nodes_parent:
                nodes_parent.touch(span.end)
        root.touch(span.end)
    return {"resourceSpans": [{"resource": {"attributes": _attributes({"service.name": "agent-os-orchestrator", "agent_os.trace_projection": "otlp-json/1"})},
                               "scopeSpans": [{"scope": SCOPE, "spans": [span.as_otlp(trace_id) for span in spans]}]}]}


def export(run_id: str, *, home: Path | None = None, out: Path | None = None) -> dict[str, Any]:
    events, malformed = read_events(telemetry_path(run_id, home))
    if not events:
        raise FileNotFoundError(f"no telemetry for run {run_id}")
    document = project(events, run_id)
    spans = document["resourceSpans"][0]["scopeSpans"][0]["spans"]
    if out:
        Path(out).write_text(json.dumps(document, indent=1), encoding="utf-8")
    return {"run_id": run_id, "spans": len(spans), "malformed_events": malformed, "written": str(out) if out else None,
            "document": None if out else document}
