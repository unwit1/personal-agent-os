"""Ingester Engine ``router_command``: answer an analysis/generation request through a subscription CLI.

The engine's router backend (``ingester_engine.analysis_router``) writes one JSON envelope
(``{"kind": "ingester.analysis", "model", "request", "prompt"}``) to this command's stdin and
reads ``{"drafts": [...], "provider", "model", "usage"}`` from its stdout. Configure it in a
downstream repository's ``ingester/config.toml``::

    [analysis]
    backend = "router"
    router_command = "python -m agent_os.ingester_router"

Subscription only: the prompt goes to the local ``claude`` (default) or ``codex`` CLI, and the
API-key variables are removed from the child environment so neither CLI can fall back to paid
API billing. Choose the provider with ``AGENT_OS_INGESTER_ROUTER_PROVIDER`` (claude-code | codex).

Optional envelope fields (engine spec/analysis.md, "Router request optional fields"):
``provider_policy.allowed_providers`` limits dispatch to the listed providers (the configured one
if allowed, else the first allowed one; an error if none is available), and
``allowance.max_cost_units`` is honoured trivially: subscription calls cost 0 units, always reported.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable

PROVIDERS = ("claude-code", "codex")
DEFAULT_MODELS = {"claude-code": "opus", "codex": "gpt-6-sol"}
PAID_KEY_VARS = ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "OPENAI_API_KEY", "CODEX_API_KEY")
_FENCE = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL | re.IGNORECASE)

Runner = Callable[[list[str], str, dict[str, str], float], str]


class RouterError(RuntimeError):
    pass


def subscription_env(base: dict[str, str] | None = None) -> dict[str, str]:
    """The child environment without any variable that would switch a CLI to paid API billing."""
    env = dict(os.environ if base is None else base)
    for name in PAID_KEY_VARS:
        env.pop(name, None)
    return env


def _run(argv: list[str], prompt: str, env: dict[str, str], timeout: float) -> str:
    done = subprocess.run(argv, input=prompt, capture_output=True, text=True, encoding="utf-8",
                          env=env, timeout=timeout, check=False)
    if done.returncode != 0:
        raise RouterError(f"{argv[0]} exited {done.returncode}: {(done.stderr or done.stdout).strip()[:400]}")
    return done.stdout


def _model_for(provider: str, requested: str | None) -> str:
    requested = (requested or "").strip()
    if provider == "claude-code" and (requested in ("opus", "sonnet", "haiku") or requested.startswith("claude-")):
        return requested
    if provider == "codex" and requested.startswith("gpt-"):
        return requested
    return DEFAULT_MODELS[provider]


def call_cli(provider: str, model: str, prompt: str, timeout: float, runner: Runner | None = None) -> str:
    runner = runner or _run
    env = subscription_env()
    if provider == "claude-code":
        exe = shutil.which("claude") or "claude"
        return runner([exe, "-p", "--output-format", "text", "--model", model], prompt, env, timeout)
    if provider == "codex":
        exe = shutil.which("codex") or "codex"
        with tempfile.TemporaryDirectory(prefix="ingester-router-") as tmp:
            out = Path(tmp) / "last.md"
            runner([exe, "exec", "--skip-git-repo-check", "--ephemeral", "-s", "read-only", "-C", tmp,
                    "-m", model, "-o", str(out), "-"], prompt, env, timeout)
            return out.read_text(encoding="utf-8") if out.exists() else ""
    raise RouterError(f"unknown provider {provider!r}; expected one of {', '.join(PROVIDERS)}")


def _single_text_concept(request: dict[str, Any]) -> str | None:
    """The concept id when the schema asks for exactly one concept holding a ``text`` string."""
    concepts = ((request.get("output_schema") or {}).get("concepts") or {})
    if len(concepts) != 1:
        return None
    concept_id, schema = next(iter(concepts.items()))
    return concept_id if "text" in ((schema or {}).get("properties") or {}) else None


def _draft_text(draft: Any) -> str:
    if isinstance(draft, str):
        return draft
    if not isinstance(draft, dict):
        return ""
    value = draft.get("value")
    if isinstance(value, dict):
        value = value.get("text")
    if isinstance(value, str):
        return value
    return draft.get("text") if isinstance(draft.get("text"), str) else ""


def to_drafts(reply: str, request: dict[str, Any]) -> list[dict[str, Any]]:
    """Drafts from the model reply.

    For a one-text-concept request (such as replication.generate) the result is always that
    concept's text: taken from the reply's JSON drafts whatever concept id or shape the model
    used, else the reply itself. Other requests pass the model's JSON drafts through.
    """
    text = reply.strip()
    parsed = None
    for candidate in [text] + [m.group(1) for m in _FENCE.finditer(text)]:
        try:
            obj = json.loads(candidate)
        except (json.JSONDecodeError, ValueError):
            continue
        if isinstance(obj, dict) and isinstance(obj.get("drafts"), list):
            parsed = obj["drafts"]
        elif isinstance(obj, list):
            parsed = obj
        elif isinstance(obj, dict) and isinstance(obj.get("text"), str):
            parsed = [obj]
        if parsed is not None:
            break
    concept = _single_text_concept(request)
    if concept is None:
        if parsed is not None:
            return parsed
        raise RouterError("model reply was not JSON drafts and the request has no single text concept to fill")
    sample = "\n\n".join(t.strip() for t in map(_draft_text, parsed) if t.strip()) if parsed is not None else text
    if not sample.strip():
        raise RouterError("model returned no text for the requested sample")
    spans = request.get("spans") or []
    evidence = [{"span_id": spans[0]["span_id"]}] if spans and spans[0].get("span_id") else []
    return [{"concept_id": concept, "key": "sample", "value": {"text": sample.strip()}, "evidence": evidence}]


def _allowed(envelope: dict[str, Any]) -> list[str] | None:
    """Router providers the envelope's provider_policy permits (None: no policy)."""
    policy = envelope.get("provider_policy")
    if not isinstance(policy, dict) or policy.get("allowed_providers") is None:
        return None
    names = {str(n).strip().removeprefix("agent-os-router/") for n in policy.get("allowed_providers") or []}
    return [p for p in PROVIDERS if p in names]


def handle(envelope: dict[str, Any], provider: str | None = None, runner: Runner | None = None,
           timeout: float = 600.0) -> dict[str, Any]:
    if envelope.get("kind") != "ingester.analysis":
        raise RouterError(f"unsupported envelope kind {envelope.get('kind')!r}")
    provider = provider or os.environ.get("AGENT_OS_INGESTER_ROUTER_PROVIDER") or "claude-code"
    if provider not in PROVIDERS:
        raise RouterError(f"unknown provider {provider!r}; expected one of {', '.join(PROVIDERS)}")
    allowed = _allowed(envelope)
    if allowed is not None and provider not in allowed:
        if not allowed:
            raise RouterError("provider_policy allows none of this router's providers "
                              f"({', '.join(PROVIDERS)})")
        provider = allowed[0]
    allowance = envelope.get("allowance")
    if isinstance(allowance, dict) and allowance.get("max_cost_units") is not None:
        try:
            if float(allowance["max_cost_units"]) < 0:
                raise RouterError("allowance.max_cost_units is negative")
        except (TypeError, ValueError) as exc:
            raise RouterError(f"allowance.max_cost_units is not a number: {exc}") from exc
    model = _model_for(provider, envelope.get("model"))
    prompt = str(envelope.get("prompt") or "")
    reply = call_cli(provider, model, prompt, timeout, runner)
    drafts = to_drafts(reply, envelope.get("request") or {})
    return {
        "drafts": drafts,
        "provider": f"agent-os-router/{provider}",
        "model": model,
        # Subscription use has no per-call price; tokens are a length estimate (4 chars ~ 1 token).
        "usage": {"input_tokens": max(1, len(prompt) // 4), "output_tokens": max(1, len(reply) // 4), "cost_units": 0},
    }


def main(argv: list[str] | None = None) -> int:
    timeout = float(os.environ.get("AGENT_OS_INGESTER_ROUTER_TIMEOUT", "600"))
    try:
        envelope = json.loads(sys.stdin.read())
        result = handle(envelope, timeout=timeout)
    except (RouterError, json.JSONDecodeError, subprocess.TimeoutExpired, OSError) as exc:
        print(f"ingester_router: {exc}", file=sys.stderr)
        return 2
    sys.stdout.write(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
