"""Serving-throughput evidence (IMP-0015): measured tokens/s per model x GPU x engine.

Quotes for GPU pods are only as good as their throughput input (EVR-0017 used
an assumed 1,500 tok/s). This module stores *measured* numbers and lets
``orchestrate quote --gpu-from`` use them per GPU offer instead of a guess.

* ``measure`` benchmarks a registered OpenAI-compatible endpoint (vLLM,
  Ollama, llama.cpp, TGI -- e.g. an abliterated model on a RunPod pod) with N
  concurrent requests and computes aggregate completion tokens per wall-clock
  second from the server's reported usage. It is a real call against the
  operator's own endpoint; it never touches third-party paid APIs unless the
  operator points it at one.
* ``record`` appends one observation to ``<home>/throughput.jsonl``; ``best``
  returns the most recent measured rate for a model (and GPU name) so quotes
  prefer evidence; ``lookup`` adapts that to compute.gpu_options.
"""

from __future__ import annotations

import json
import threading
import time
from pathlib import Path
from typing import Any, Callable

from ..timestamps import utc_now_iso
from .store import orchestrator_home

KINDS = ("generation", "training")
DEFAULT_PROMPT = ("Write a detailed, well-structured technical explanation of how a hash map handles collisions, "
                  "including open addressing and chaining, with a short Python example.")


def path(home: Path | None = None) -> Path:
    return Path(home or orchestrator_home()) / "throughput.jsonl"


def _norm(text: Any) -> str:
    return " ".join(str(text or "").lower().replace("-", " ").split())


def record(*, model: str, gpu: str, tokens_per_second: float, kind: str = "generation", engine: str | None = None, revision: str | None = None,
           concurrency: int | None = None, source: str = "measured", notes: str | None = None, home: Path | None = None) -> dict[str, Any]:
    if kind not in KINDS:
        raise ValueError(f"kind must be one of {KINDS}")
    if not model or not gpu:
        raise ValueError("model and gpu are required")
    if not tokens_per_second or tokens_per_second <= 0:
        raise ValueError("tokens_per_second must be > 0")
    if source not in {"measured", "benchmark", "assumed"}:
        raise ValueError("source must be measured, benchmark or assumed")
    entry = {"at": utc_now_iso(), "model": model, "revision": revision, "gpu": gpu, "engine": engine, "kind": kind,
             "tokens_per_second": round(float(tokens_per_second), 2), "concurrency": concurrency, "source": source, "notes": notes}
    target = path(home)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return entry


def load(home: Path | None = None) -> list[dict[str, Any]]:
    target = path(home)
    if not target.exists():
        return []
    rows = []
    for line in target.read_text(encoding="utf-8").splitlines():
        try:
            item = json.loads(line)
        except ValueError:
            continue
        if isinstance(item, dict):
            rows.append(item)
    return rows


def best(model: str, gpu: str | None = None, kind: str = "generation", home: Path | None = None) -> dict[str, Any] | None:
    """Most recent observation for the model (and GPU), preferring measured
    over benchmark over assumed evidence."""
    rank = {"measured": 0, "benchmark": 1, "assumed": 2}
    rows = [row for row in load(home) if row.get("kind") == kind and _norm(row.get("model")) == _norm(model)
            and (gpu is None or _norm(row.get("gpu")) == _norm(gpu))]
    if not rows:
        return None
    rows.sort(key=lambda row: row.get("at") or "", reverse=True)  # newest first...
    rows.sort(key=lambda row: rank.get(row.get("source"), 3))       # ...within each evidence rank (stable)
    return rows[0]


def lookup(model: str, kind: str = "generation", home: Path | None = None) -> Callable[[dict[str, Any]], float | None]:
    """Per-offer rate function for compute.gpu_options: matches the offer's
    GPU display name or id."""
    def rate(offer: dict[str, Any]) -> float | None:
        for name in (offer.get("name"), offer.get("gpu_id")):
            hit = best(model, name, kind, home) if name else None
            if hit:
                return float(hit["tokens_per_second"])
        return None
    return rate


def measure(provider: dict[str, Any], model: str, *, requests: int = 8, concurrency: int = 4, max_tokens: int = 256,
            prompt: str = DEFAULT_PROMPT, timeout: int = 300, adapter_factory: Callable[..., Any] | None = None,
            clock: Callable[[], float] = time.monotonic) -> dict[str, Any]:
    """Aggregate completion tokens/s for one endpoint under ``concurrency``
    parallel requests. Uses the provider's OpenAI-compatible adapter."""
    from types import SimpleNamespace

    from .adapters.http_api import OpenAiCompatibleAdapter

    if requests < 1 or concurrency < 1:
        raise ValueError("requests and concurrency must be >= 1")
    adapter = (adapter_factory or OpenAiCompatibleAdapter)(provider)
    results: list[dict[str, Any]] = []
    lock = threading.Lock()
    pending = list(range(requests))

    def worker() -> None:
        while True:
            with lock:
                if not pending:
                    return
                pending.pop()
            call = SimpleNamespace(model=model, provider_effort=None)
            url, body, headers = adapter.request_body(call, prompt)
            body["max_tokens"] = max_tokens
            body["temperature"] = 0
            started = clock()
            try:
                payload = adapter._post(url, body, headers, timeout)
                tokens = int(((payload.get("usage") or {}).get("completion_tokens")) or 0)
                item = {"ok": tokens > 0, "tokens": tokens, "seconds": clock() - started}
            except Exception as exc:
                item = {"ok": False, "tokens": 0, "seconds": clock() - started, "error": f"{type(exc).__name__}: {str(exc)[:120]}"}
            with lock:
                results.append(item)

    wall_start = clock()
    threads = [threading.Thread(target=worker, daemon=True) for _ in range(min(concurrency, requests))]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    wall = max(clock() - wall_start, 1e-9)
    ok = [item for item in results if item["ok"]]
    total = sum(item["tokens"] for item in ok)
    return {"model": model, "provider": provider.get("id"), "requests": requests, "succeeded": len(ok), "concurrency": concurrency,
            "completion_tokens": total, "wall_seconds": round(wall, 3), "tokens_per_second": round(total / wall, 2) if ok else None,
            "per_request_tps": round(sum(item["tokens"] / item["seconds"] for item in ok if item["seconds"] > 0) / len(ok), 2) if ok else None,
            "errors": [item["error"] for item in results if item.get("error")][:5]}
