"""Direct HTTP API adapters (Anthropic Messages, OpenAI-compatible Chat
Completions), stdlib only, disabled until a key is configured (DEC-0009).

Why: every Claude Code / Codex CLI call carries a fixed context overhead
(measured 14k-19k input tokens for a trivial prompt, docs/simple-mode.md).
For self-contained single-shot tasks -- classification, extraction,
summarization of content included in the prompt -- a direct API call costs
only the prompt. These workers have **no repository tools**, so they register
with ``roles: ["inline"]``: the engine's coding roles never select them, and
``orchestrate delegate --role inline`` uses them for prompts that carry their
own context.

Keys: environment variable (``ANTHROPIC_API_KEY`` / ``OPENAI_API_KEY``) or the
OS keyring (service ``agent-os``, user ``anthropic-api`` / ``openai-api``),
set with ``agent-os orchestrate api-key set <provider>``. Keys are never
written to the registry, run records or logs. ``base_url`` lets the
OpenAI-compatible adapter target local servers (vLLM, Ollama, LM Studio),
which need no key.

LiteLLM would cover this but was compromised on PyPI in 2026-03 and is a very
heavy dependency (prior art PA-litellm); the needed subset is small.
"""

from __future__ import annotations

import json
import os
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from ...timestamps import utc_now_iso
from ..retry import RetryableError, RetryPolicy, RETRYABLE_STATUS, parse_retry_after
from ..usage import unavailable
from .base import AgentLaunchRequest, AgentProcessStatus, AgentResult, InvocationPlan, ProviderStatus, RunningAgent, extract_structured

KEYRING_SERVICE = "agent-os"
_LIVE: dict[str, dict[str, Any]] = {}
_LOCK = threading.Lock()


def read_key(env_var: str, keyring_user: str) -> str | None:
    value = os.environ.get(env_var)
    if value:
        return value.strip()
    try:
        import keyring  # the project's existing dependency

        stored = keyring.get_password(KEYRING_SERVICE, keyring_user)
        return stored.strip() if stored else None
    except Exception:
        return None


def store_key(keyring_user: str, secret: str) -> None:
    import keyring

    keyring.set_password(KEYRING_SERVICE, keyring_user, secret)


def _price_cost(model: str, input_tokens: int | None, cached: int | None, output_tokens: int | None) -> float | None:
    """USD from model_value price evidence (per million tokens), when known."""
    try:
        from ..model_value import load_evidence

        price = (load_evidence().get("models", {}).get(model) or {}).get("price") or {}
        if not all(isinstance(price.get(key), (int, float)) for key in ("input", "output")) or input_tokens is None or output_tokens is None:
            return None
        cached = cached or 0
        cached_rate = price.get("cached_input", price["input"])
        return round(((input_tokens - cached) * price["input"] + cached * cached_rate + output_tokens * price["output"]) / 1_000_000, 6)
    except Exception:
        return None


class HttpApiAdapter:
    """Shared machinery: in-process worker thread, retries, usage mapping."""

    adapter_id = "http_api"
    adapter_version = "http_api/1"
    env_var = ""
    keyring_user = ""
    default_base_url = ""
    needs_key = True

    def __init__(self, provider: dict[str, Any], opener=None) -> None:
        self.provider = provider
        self.options = provider.get("options") or {}
        self.opener = opener or urllib.request.urlopen

    # -- configuration ----------------------------------------------------
    def base_url(self) -> str:
        return str(self.options.get("base_url") or self.default_base_url).rstrip("/")

    def key(self) -> str | None:
        return read_key(self.options.get("key_env") or self.env_var, self.options.get("keyring_user") or self.keyring_user)

    def probe(self) -> ProviderStatus:
        if self.needs_key and not self.options.get("base_url") and not self.key():
            return ProviderStatus(self.provider["id"], False, reason=f"no API key ({self.env_var} or keyring {KEYRING_SERVICE}/{self.keyring_user})")
        return ProviderStatus(self.provider["id"], True, executable=self.base_url(), version=self.adapter_version)

    def resolve_invocation(self, request: AgentLaunchRequest) -> InvocationPlan:
        return InvocationPlan(executable=self.base_url(), argv=[], cwd=request.cwd, env={}, stdin_path=request.prompt_path, provider=self.provider["id"],
                              model=request.model, effort=request.provider_effort, adapter_version=self.adapter_version, display=f"POST {self.base_url()} model={request.model}")

    # -- HTTP -------------------------------------------------------------
    def _post(self, url: str, body: dict[str, Any], headers: dict[str, str], timeout: int) -> dict[str, Any]:
        data = json.dumps(body).encode()
        request = urllib.request.Request(url, data=data, headers={"content-type": "application/json", "user-agent": "agent-os/1", **headers}, method="POST")
        try:
            with self.opener(request, timeout=timeout) as response:
                return json.loads(response.read().decode())
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode(errors="replace")[:300] if hasattr(exc, "read") else ""
            if exc.code in RETRYABLE_STATUS:
                raise RetryableError(f"HTTP {exc.code}: {detail}", status=exc.code, retry_after=parse_retry_after(exc.headers.get("retry-after") if exc.headers else None)) from exc
            raise RuntimeError(f"HTTP {exc.code}: {detail}") from exc
        except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
            raise RetryableError(f"network: {exc}") from exc

    def request_body(self, request: AgentLaunchRequest, prompt: str) -> tuple[str, dict[str, Any], dict[str, str]]:  # pragma: no cover - abstract
        raise NotImplementedError

    def parse(self, payload: dict[str, Any], model: str) -> tuple[str, dict[str, Any]]:  # pragma: no cover - abstract
        raise NotImplementedError

    # -- lifecycle (same contract as other adapters) ----------------------
    def start(self, request: AgentLaunchRequest) -> RunningAgent:
        out = Path(request.output_dir)
        out.mkdir(parents=True, exist_ok=True)
        prompt = Path(request.prompt_path).read_text(encoding="utf-8")
        token = f"{self.provider['id']}-{time.monotonic_ns()}"
        state: dict[str, Any] = {"done": False, "result": None}
        policy = RetryPolicy(max_attempts=int(self.options.get("max_attempts", 4)), deadline=float(request.timeout_seconds))

        def work() -> None:
            started = time.monotonic()
            try:
                url, body, headers = self.request_body(request, prompt)
                payload = policy.call(lambda: self._post(url, body, headers, int(self.options.get("request_timeout", 600))))
                text, usage = self.parse(payload, request.model)
                (out / "last-message.md").write_text(text, encoding="utf-8")
                result = AgentResult(outcome="completed", summary=text[-600:], structured=extract_structured(text), usage=usage,
                                     duration_ms=int((time.monotonic() - started) * 1000)) if text.strip() else AgentResult(outcome="failed", failure_kind="malformed", detail="empty response")
            except RetryableError as exc:
                kind = "quota" if exc.status == 429 else "unavailable"
                result = AgentResult(outcome="failed", failure_kind=kind, detail=str(exc)[:400])
            except Exception as exc:
                text = str(exc)
                kind = "auth" if "HTTP 401" in text or "HTTP 403" in text else "invalid_model" if "HTTP 404" in text else "failed"
                result = AgentResult(outcome="failed", failure_kind=kind, detail=text[:400])
            state.update(done=True, result=result)

        thread = threading.Thread(target=work, daemon=True)
        with _LOCK:
            _LIVE[token] = state
        thread.start()
        return RunningAgent(provider_id=self.provider["id"], node_id=request.node_id, pid=None, started_monotonic=time.monotonic(), started_at=utc_now_iso(),
                            stdout_path=str(out / "stdout.log"), stderr_path=str(out / "stderr.log"), result_path=str(out / "last-message.md"),
                            display=self.resolve_invocation(request).display, token=token)

    def poll(self, handle: RunningAgent) -> AgentProcessStatus:
        state = _LIVE.get(handle.token or "")
        if state is None:
            return AgentProcessStatus(running=False, returncode=None)
        return AgentProcessStatus(running=not state["done"], returncode=0 if state["done"] else None)

    def cancel(self, handle: RunningAgent) -> None:
        with _LOCK:
            _LIVE.pop(handle.token or "", None)

    def collect(self, handle: RunningAgent) -> AgentResult:
        with _LOCK:
            state = _LIVE.pop(handle.token or "", None)
        if not state or not state["done"]:
            return AgentResult(outcome="failed", failure_kind="interrupted", detail="API worker was lost or cancelled")
        return state["result"]


class AnthropicApiAdapter(HttpApiAdapter):
    adapter_id = "anthropic_api"
    adapter_version = "anthropic_api/1"
    env_var = "ANTHROPIC_API_KEY"
    keyring_user = "anthropic-api"
    default_base_url = "https://api.anthropic.com"

    def request_body(self, request: AgentLaunchRequest, prompt: str) -> tuple[str, dict[str, Any], dict[str, str]]:
        body: dict[str, Any] = {"model": request.model, "max_tokens": int(self.options.get("max_tokens", 8192)),
                                "messages": [{"role": "user", "content": prompt}]}
        system = self.options.get("system")
        if system:
            # Prompt caching for a stable system prefix (cache reads bill at a fraction of input).
            body["system"] = [{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}]
        headers = {"x-api-key": self.key() or "", "anthropic-version": str(self.options.get("api_version", "2023-06-01"))}
        return f"{self.base_url()}/v1/messages", body, headers

    def parse(self, payload: dict[str, Any], model: str) -> tuple[str, dict[str, Any]]:
        text = "".join(block.get("text", "") for block in payload.get("content") or [] if block.get("type") == "text")
        raw = payload.get("usage") or {}
        uncached = raw.get("input_tokens")
        cache_read = raw.get("cache_read_input_tokens") or 0
        cache_write = raw.get("cache_creation_input_tokens") or 0
        total = (uncached or 0) + cache_read + cache_write if uncached is not None else None
        resolved = payload.get("model") or model
        usage = {"input_tokens": total, "uncached_input_tokens": uncached, "cache_read_tokens": cache_read, "cache_write_tokens": cache_write,
                 "output_tokens": raw.get("output_tokens"), "reasoning_tokens": None, "cached_tokens": cache_read, "turns": 1, "tool_calls": 0,
                 "cost_usd": _price_cost(resolved, total, cache_read, raw.get("output_tokens")), "accuracy": "exact" if raw else "unavailable",
                 "source": self.adapter_id, "model_resolved": resolved}
        return text, usage


class OpenAiCompatibleAdapter(HttpApiAdapter):
    adapter_id = "openai_api"
    adapter_version = "openai_api/1"
    env_var = "OPENAI_API_KEY"
    keyring_user = "openai-api"
    default_base_url = "https://api.openai.com"

    def request_body(self, request: AgentLaunchRequest, prompt: str) -> tuple[str, dict[str, Any], dict[str, str]]:
        body: dict[str, Any] = {"model": request.model, "messages": [{"role": "user", "content": prompt}]}
        if request.provider_effort and self.options.get("send_reasoning_effort", True):
            body["reasoning_effort"] = request.provider_effort
        key = self.key()
        headers = {"authorization": f"Bearer {key}"} if key else {}
        return f"{self.base_url()}/v1/chat/completions", body, headers

    def parse(self, payload: dict[str, Any], model: str) -> tuple[str, dict[str, Any]]:
        choices = payload.get("choices") or [{}]
        text = str(((choices[0] or {}).get("message") or {}).get("content") or "")
        raw = payload.get("usage") or {}
        cached = ((raw.get("prompt_tokens_details") or {}).get("cached_tokens")) or 0
        reasoning = (raw.get("completion_tokens_details") or {}).get("reasoning_tokens")
        resolved = payload.get("model") or model
        usage = {"input_tokens": raw.get("prompt_tokens"), "uncached_input_tokens": (raw.get("prompt_tokens") - cached) if raw.get("prompt_tokens") is not None else None,
                 "cache_read_tokens": cached, "cache_write_tokens": 0, "output_tokens": raw.get("completion_tokens"), "reasoning_tokens": reasoning,
                 "cached_tokens": cached, "turns": 1, "tool_calls": 0, "cost_usd": _price_cost(resolved, raw.get("prompt_tokens"), cached, raw.get("completion_tokens")),
                 "accuracy": "exact" if raw else "unavailable", "source": self.adapter_id, "model_resolved": resolved}
        return text, usage


# Suggested registry entries: enabled only when a key (or local base_url) exists.
ANTHROPIC_MODELS = {"fast": "claude-haiku-4-5-20251001", "balanced": "claude-sonnet-5", "reasoning": "claude-opus-5-5", "frontier": "claude-fable-5-1"}
OPENAI_MODELS = {"fast": "gpt-6-luna", "balanced": "gpt-5.6-terra", "reasoning": "gpt-6-sol", "frontier": "gpt-6-astra"}


def _suggest(provider_id: str, adapter: type[HttpApiAdapter], models: dict[str, str]) -> dict[str, Any]:
    entry = {"id": provider_id, "adapter": adapter.adapter_id, "models": dict(models), "roles": ["inline"],
             "costs": {"fast": 0.5, "balanced": 1.5, "reasoning": 4.0, "frontier": 8.0},
             "effort_map": {"none": None, "low": "low", "medium": "medium", "high": "high"}, "max_concurrency": 4, "options": {}}
    entry["enabled"] = adapter(entry).probe().available
    return entry


def suggested_anthropic(_: str | None = None) -> dict[str, Any]:
    return _suggest("anthropic-api", AnthropicApiAdapter, ANTHROPIC_MODELS)


def suggested_openai(_: str | None = None) -> dict[str, Any]:
    return _suggest("openai-api", OpenAiCompatibleAdapter, OPENAI_MODELS)
