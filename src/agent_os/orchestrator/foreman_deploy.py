"""Session foreman: deploy a Hugging Face model on a rented GPU and let it plan runs.

The operator gives a Hugging Face link and a budget for the job (GUI
"Session foreman" panel, or ``orchestrate foreman deploy``). Everything after
that is automatic:

1. **plan** -- read the model's metadata from the Hugging Face API (exact
   revision, parameter count and dtypes, gating, licence), estimate the GPU
   memory vLLM needs, and pick the cheapest RunPod GPU offer (compute.py
   inventory) that fits the model *and* leaves at least ``MIN_RUNTIME_HOURS``
   of runtime inside the job budget;
2. **provision** -- create a pod running the official ``vllm/vllm-openai``
   image, pinned to that revision, guarded by a fresh random API key kept in
   the OS keyring (``secrets://foreman/endpoint``);
3. **load** -- poll the pod's OpenAI-compatible ``/v1/models`` until the
   model is served;
4. **register** -- add the endpoint to the machine provider registry with
   ``roles: ["planner", "inline"]`` and make it the planner for every run
   created while it is live (engine.create_run stamps ``record["foreman"]``;
   a run created while the model is still loading waits for it, see
   ``planner_hold``);
5. **meter and tear down** -- a watchdog appends the pod's actual cost to the
   spend ledger (budget.py) every ``TICK_SECONDS`` and deletes the pod when
   the next tick would cross the job budget or the remaining project budget,
   when every attached run has finished planning and the foreman has been
   idle for ``idle_minutes``, or when the operator presses Stop. The provider
   entry is removed at teardown so nothing routes to a dead endpoint.

Sources: the session foreman can instead be one of your subscription models
(``use("claude")`` -> the registered Claude Code provider, ``use("chatgpt")`` ->
the registered Codex provider, optionally pinned to one model) or a model you
already serve locally (``use("local", base_url=...)``, any OpenAI-compatible
server: Ollama, LM Studio, llama.cpp, vLLM), or any eligible provider already
in the registry (``use("registered", provider=<id>)``, see ``eligible_foremen``;
paid ones are gated by the run's allow_paid_spend like any paid provider).
Those need no GPU rental, so no budget, metering or teardown applies; they stay the planner until you stop
them or pick another foreman. Picking a new foreman replaces the current one
(a rented pod is deleted first).

Budget safety: setting the budget is an operator action (budget.set_budget);
a deployment is refused unless the machine budget is approved and the
chosen GPU fits the cap for ``MIN_RUNTIME_HOURS``. The deadline is persisted
(``~/.agent-os/foreman/deployment.json``) and enforced again whenever the GUI
starts (``resume``). Limit: the watchdog runs inside the GUI process, so if
this computer is off, the pod keeps billing until the GUI next starts -- it is
then deleted at once if past its deadline.

Operator authority (DEC-0030 addendum): shadow mode (foreman.py) remains the
evaluation path; this module is the operator's explicit opt-in to give a model
planner authority for runs in this session. Its plans are still data --
planner.expand validates the DAG, scopes and commands exactly as for any
planner.
"""

from __future__ import annotations

import json
import math
import os
import re
import secrets as token_lib
import threading
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path
from typing import Any, Callable

from ..timestamps import utc_now_iso
from . import budget, endpoints

RUNPOD_REST = "https://rest.runpod.io/v1"
HF_API = "https://huggingface.co/api/models"
RUNPOD_SECRET = "secrets://runpod/default"
HF_SECRET = "secrets://huggingface/default"
ENDPOINT_SECRET = "secrets://foreman/endpoint"
IMAGE = "vllm/vllm-openai:latest"
PORT = 8000
TICK_SECONDS = 30
MIN_RUNTIME_HOURS = 0.5
STOP_FRACTION = 0.95  # stop once 95% of the cap is spent: one tick + teardown fit in the rest
LOAD_TIMEOUT_MINUTES = 45
DEFAULT_IDLE_MINUTES = 15
MAX_CONTEXT = 32768
PRICE_FACTOR = 1.5
NETWORK_RETRY_TICKS = 20  # ~10 minutes of network trouble before giving up on a live pod
DELETE_ATTEMPTS = 6  # then teardown_pending: resume / stop / GUI start keep retrying
PENDING = "teardown_pending"
REAP_AFTER_SECONDS = 6 * TICK_SECONDS  # watchdog silent this long -> it died with its process
# vLLM tool-call parser per model family: needed for a coding agent (tool use).
TOOL_PARSERS = {"qwen2": "hermes", "qwen2_moe": "hermes", "qwen3": "hermes", "qwen3_moe": "hermes", "llama": "llama3_json",
                "mistral": "mistral", "mixtral": "mistral"}
AGENT_SUFFIX = "-agent"
GPU_KEY_ENV = "AGENT_OS_GPU_KEY"
CRASH_LOG = "agent-os-crash.log"
# Runs vLLM; if it exits, serves the redacted tail of its log on the same port
# so the manager can report the real error instead of waiting on a crash loop.
WRAPPER = (
    'python3 -m vllm.entrypoints.openai.api_server "$@" 2>&1 | tee /tmp/vllm.log; code=${PIPESTATUS[0]}; '
    'mkdir -p /tmp/agent-os && { echo "vLLM exited with code $code"; tail -n 80 /tmp/vllm.log; } '
    '| sed "s|${VLLM_API_KEY:-no-key}|***|g; s|${HF_TOKEN:-no-token}|***|g" > /tmp/agent-os/' + CRASH_LOG + '; '
    'cd /tmp/agent-os && exec python3 -m http.server ' + str(PORT)
)
ACTIVE = ("planning", "provisioning", "loading", "ready")
SOURCES = ("claude", "chatgpt", "openrouter", "local", "huggingface", "registered")
NOT_RENTED = ("claude", "chatgpt", "openrouter", "local", "registered")
FOREMAN_ADAPTERS = ("openai_api", "anthropic_api", "claude_code", "codex_cli")
OPENROUTER_BASE = "https://openrouter.ai/api"
OPENROUTER_SECRET = "secrets://openrouter/default"
OPENROUTER_PROVIDER = "foreman-openrouter"
SUBSCRIPTION_ADAPTERS = {"claude": "claude_code", "chatgpt": "codex_cli"}
LOCAL_PROVIDER = "foreman-local"
BYTES_PER_PARAM = {"BF16": 2, "F16": 2, "F32": 2, "F8_E4M3": 1, "F8_E5M2": 1, "I8": 1, "U8": 1, "I32": 4, "I16": 2, "F64": 2}
_REPO = re.compile(r"^[A-Za-z0-9][\w.-]{0,95}/[\w.-]{1,96}$")


# ---------------------------------------------------------------------------
# Pure helpers (no network)
# ---------------------------------------------------------------------------


def parse_hf_link(link: str) -> dict[str, str | None]:
    """``https://huggingface.co/org/name[/tree/<rev>]``, ``hf.co/org/name`` or
    ``org/name`` -> ``{"repo": "org/name", "revision": rev|None}``."""
    text = str(link or "").strip()
    text = re.sub(r"^https?://", "", text)
    text = re.sub(r"^(www\.)?(huggingface\.co|hf\.co)/", "", text)
    text = text.split("?", 1)[0].split("#", 1)[0].strip("/")
    parts = text.split("/")
    if len(parts) >= 2 and parts[0] in {"datasets", "spaces"}:
        raise ValueError("that link is a dataset or space, not a model")
    if len(parts) < 2:
        raise ValueError(f"not a Hugging Face model link: {link!r}")
    repo = "/".join(parts[:2])
    if not _REPO.match(repo):
        raise ValueError(f"not a Hugging Face model id: {repo!r}")
    revision = parts[3] if len(parts) >= 4 and parts[2] in {"tree", "blob", "resolve"} else None
    return {"repo": repo, "revision": revision}


def summarize_info(info: dict[str, Any], config: dict[str, Any] | None = None) -> dict[str, Any]:
    """The fields deployment needs from a Hugging Face ``/api/models/<repo>``
    payload plus the repo's ``config.json`` (the API omits context length and
    attention shape)."""
    safetensors = info.get("safetensors") or {}
    by_dtype = safetensors.get("parameters") or {}
    params = safetensors.get("total") or sum(int(v) for v in by_dtype.values() if isinstance(v, (int, float))) or None
    weight_bytes = sum(int(count) * BYTES_PER_PARAM.get(str(dtype).upper(), 2) for dtype, count in by_dtype.items()) or (params * 2 if params else None)
    config = {**(info.get("config") or {}), **(config or {})}
    text = config.get("text_config") or config
    heads = text.get("num_attention_heads")
    kv_bytes_per_token = None
    if text.get("num_hidden_layers") and heads and text.get("hidden_size"):
        head_dim = text.get("head_dim") or text["hidden_size"] // heads
        kv_bytes_per_token = 2 * 2 * int(text["num_hidden_layers"]) * int(text.get("num_key_value_heads") or heads) * int(head_dim)
    tags = [str(tag) for tag in info.get("tags") or []]
    files = [str((item or {}).get("rfilename") or "") for item in info.get("siblings") or []]
    return {
        "repo": info.get("id") or info.get("modelId"),
        "sha": info.get("sha"),
        "gated": bool(info.get("gated")),
        "private": bool(info.get("private")),
        "pipeline": info.get("pipeline_tag"),
        "license": next((tag.split(":", 1)[1] for tag in tags if tag.startswith("license:")), None),
        "model_type": config.get("model_type"),
        "params": params,
        "weight_gb": round(weight_bytes / 1e9, 2) if weight_bytes else None,
        "has_safetensors": any(name.endswith(".safetensors") for name in files) or bool(by_dtype),
        "gguf_only": any(name.endswith(".gguf") for name in files) and not any(name.endswith((".safetensors", ".bin")) for name in files),
        "max_position_embeddings": _context_length(config),
        "kv_bytes_per_token": kv_bytes_per_token,
        "attention_heads": heads,
        "refusal_hint": "abliterated" if any(word in str(info.get("id") or "").lower() for word in ("abliterat", "uncensor")) else "unknown",
    }


def _context_length(config: dict[str, Any]) -> int | None:
    for source in (config, config.get("text_config") or {}):
        for key in ("max_position_embeddings", "max_sequence_length", "seq_length", "n_positions"):
            if isinstance(source.get(key), int):
                return int(source[key])
    return None


def deployable_problem(model: dict[str, Any]) -> str | None:
    if model.get("gguf_only"):
        return "this repository only has GGUF files; vLLM needs safetensors weights (pick the original or an AWQ/GPTQ repo)"
    if model.get("pipeline") not in (None, "text-generation", "image-text-to-text", "conversational"):
        return f"pipeline {model.get('pipeline')!r} is not a text-generation model"
    if not model.get("weight_gb"):
        return "the Hugging Face API did not report the model size; cannot size a GPU safely"
    return None


AGENT_CONTEXT = 65536  # Codex CLI's own instructions + tools exceed 32k tokens (measured live)
YARN_FAMILIES = {"qwen2", "qwen2_moe", "qwen3", "qwen3_moe"}


def agent_capable(model: dict[str, Any]) -> bool:
    """Opted in (deploy --coding-agent) and a family with a known tool-call parser."""
    return bool(model.get("agent")) and str(model.get("model_type") or "") in TOOL_PARSERS


def context_for(model: dict[str, Any]) -> int:
    """Served context: 32k for planning; 64k when the pod also hosts a coding
    agent (native window, or YaRN-extended for families that support it)."""
    native = model.get("max_position_embeddings") or MAX_CONTEXT
    if agent_capable(model) and (native >= AGENT_CONTEXT or str(model.get("model_type")) in YARN_FAMILIES):
        return AGENT_CONTEXT
    return min(native, MAX_CONTEXT)


def rope_override(model: dict[str, Any]) -> dict[str, Any] | None:
    """YaRN scaling when the served context exceeds the native window."""
    native = model.get("max_position_embeddings") or MAX_CONTEXT
    target = context_for(model)
    if target <= native:
        return None
    return {"rope_scaling": {"rope_type": "yarn", "factor": round(target / native, 3), "original_max_position_embeddings": native},
            "max_position_embeddings": target}


def vram_needed_gb(model: dict[str, Any]) -> float:
    """Weights + runtime overhead + KV cache for one ``context_for`` sequence,
    divided by vLLM's 0.90 memory utilization. Deliberately generous: an
    out-of-memory pod wastes the whole startup cost."""
    weights = float(model["weight_gb"])
    if model.get("kv_bytes_per_token"):
        kv = max(1.0, model["kv_bytes_per_token"] * context_for(model) / 1e9 * 1.5)  # 1.5x: a few concurrent sequences
    else:
        kv = max(2.0, weights * 0.15) * (context_for(model) / MAX_CONTEXT)
    return round((weights * 1.1 + kv + 2.0) / 0.90, 1)


def choose_gpu(offers: list[dict[str, Any]], need_gb: float, cap_usd: float, *, min_hours: float = MIN_RUNTIME_HOURS,
               counts: tuple[int, ...] = (1, 2, 4, 8), heads: int | None = None) -> dict[str, Any]:
    """Cheapest (offer, GPU count) whose total VRAM covers ``need_gb`` and whose
    hourly price leaves ``min_hours`` of runtime inside ``cap_usd``. Returns
    ``{"choice": ..., "alternatives": [...]}`` or ``{"error": ...}``."""
    fits = []
    for offer in offers:
        vram = float(offer.get("vram_gb") or 0)
        for count in counts:
            if heads and heads % count:
                continue  # vLLM tensor parallelism needs heads divisible by the GPU count
            if vram * count >= need_gb:
                fits.append({**offer, "gpu_count": count, "hourly_usd": round(float(offer["usd_per_hour"]) * count, 4)})
                break
    if not fits:
        return {"error": f"no RunPod GPU (up to 8 per pod) has the {need_gb} GB this model needs"}
    fits.sort(key=lambda item: (item["hourly_usd"], item["tier"] != "secure"))
    affordable = [item for item in fits if item["hourly_usd"] * min_hours <= cap_usd]
    if not affordable:
        cheapest = fits[0]
        return {"error": f"the cheapest GPU that fits ({cheapest['gpu_count']}x {cheapest['name']}, ${cheapest['hourly_usd']:.2f}/h) "
                         f"needs ${cheapest['hourly_usd'] * min_hours:.2f} for {min_hours} h; the job budget is ${cap_usd:.2f}"}
    for item in affordable:
        item["max_hours"] = round(cap_usd * STOP_FRACTION / item["hourly_usd"], 2)
    return {"choice": affordable[0], "alternatives": affordable[1:]}


def attempt_groups(candidates: list[dict[str, Any]], limit: int = 6, price_factor: float = PRICE_FACTOR) -> list[list[dict[str, Any]]]:
    """Affordable offers grouped by (GPU count, cloud tier), cheapest group
    first. One pod request per group lists the GPU types in it in price
    order, so RunPod takes a type that has capacity right now. Types priced
    above ``price_factor`` x the group's cheapest are left out: RunPod does not
    always honour the order, and a sold-out cheap card must not turn into a
    card at twice the price."""
    groups: dict[tuple[int, str], list[dict[str, Any]]] = {}
    for item in candidates:
        group = groups.setdefault((item["gpu_count"], item["tier"]), [])
        if not group or item["hourly_usd"] <= group[0]["hourly_usd"] * price_factor:
            group.append(item)
    ordered = sorted(groups.values(), key=lambda group: group[0]["hourly_usd"])
    return ordered[:limit]


def pod_request(model: dict[str, Any], choice: dict[str, Any] | list[dict[str, Any]], endpoint_key: str, hf_token: str | None, name: str) -> dict[str, Any]:
    """RunPod ``POST /v1/pods`` body: vLLM's OpenAI server, pinned revision.
    ``choice`` may be a group of same-count, same-tier offers (attempt_groups)."""
    group = choice if isinstance(choice, list) else [choice]
    choice = group[0]
    args = ["--model", model["repo"], "--served-model-name", model["repo"], "--host", "0.0.0.0", "--port", str(PORT),
            "--max-model-len", str(context_for(model)), "--gpu-memory-utilization", "0.90",
            "--tensor-parallel-size", str(choice["gpu_count"])]
    if model.get("sha"):
        args += ["--revision", model["sha"]]
    if agent_capable(model):  # lets a coding CLI drive the model with tools (Responses API)
        args += ["--enable-auto-tool-choice", "--tool-call-parser", TOOL_PARSERS[str(model["model_type"])]]
    rope = rope_override(model)
    if rope:
        args += ["--hf-overrides", json.dumps(rope, separators=(",", ":"))]
    env = {"VLLM_API_KEY": endpoint_key}  # env, not argv: vLLM logs its arguments
    if hf_token and (model.get("gated") or model.get("private")):
        env["HF_TOKEN"] = hf_token  # only sent when the repo needs it
    return {
        "name": name[:191],
        "imageName": IMAGE,
        "gpuTypeIds": [item["gpu_id"] for item in group],
        "gpuTypePriority": "custom",  # in the order given: cheapest first
        "gpuCount": int(choice["gpu_count"]),
        "cloudType": "COMMUNITY" if choice.get("tier") == "community" else "SECURE",
        "containerDiskInGb": int(math.ceil(float(model["weight_gb"]) * 1.3)) + 20,
        "volumeInGb": 0,
        "ports": [f"{PORT}/http"],
        "env": env,
        "dockerEntrypoint": ["bash", "-c", WRAPPER, "agent-os-vllm"],
        "dockerStartCmd": args,
    }


def endpoint_url(pod_id: str) -> str:
    return f"https://{pod_id}-{PORT}.proxy.runpod.net"


# ---------------------------------------------------------------------------
# Network clients (injectable opener for tests)
# ---------------------------------------------------------------------------


def _http(opener: Callable[..., Any] | None, method: str, url: str, *, headers: dict[str, str] | None = None,
          body: dict[str, Any] | None = None, timeout: int = 30) -> tuple[int, Any]:
    data = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(url, data=data, method=method, headers={"user-agent": "agent-os/1", "content-type": "application/json", **(headers or {})})
    try:
        with (opener or urllib.request.urlopen)(request, timeout=timeout) as response:
            raw = response.read().decode(errors="replace") or "null"
            try:
                return int(getattr(response, "status", 200)), json.loads(raw)
            except ValueError:
                return int(getattr(response, "status", 200)), raw
    except urllib.error.HTTPError as exc:
        try:
            detail = exc.read().decode(errors="replace")[:400]
        except Exception:
            detail = ""
        finally:
            exc.close()
        return exc.code, {"error": detail or exc.reason}


def hf_model(repo: str, revision: str | None = None, *, token: str | None = None, opener=None) -> dict[str, Any]:
    url = f"{HF_API}/{repo}" + (f"/revision/{revision}" if revision else "")
    status, payload = _http(opener, "GET", url, headers={"authorization": f"Bearer {token}"} if token else None)
    if status == 401 or status == 403:
        raise ValueError(f"Hugging Face refused access to {repo} (gated or private: accept its licence on huggingface.co and set secrets://huggingface/default)")
    if status == 404:
        raise ValueError(f"Hugging Face has no model {repo}" + (f" at revision {revision}" if revision else ""))
    if status >= 400 or not isinstance(payload, dict):
        raise ValueError(f"Hugging Face API error {status}: {str(payload)[:200]}")
    return payload


def hf_config(repo: str, revision: str, *, token: str | None = None, opener=None) -> dict[str, Any]:
    """The repo's config.json at the pinned revision; {} when absent."""
    try:
        status, payload = _http(opener, "GET", f"https://huggingface.co/{repo}/resolve/{revision}/config.json",
                                headers={"authorization": f"Bearer {token}"} if token else None)
    except Exception:
        return {}
    return payload if status == 200 and isinstance(payload, dict) else {}


class RunPod:
    def __init__(self, api_key: str, opener=None) -> None:
        self.headers = {"authorization": f"Bearer {api_key}"}
        self.opener = opener

    def create(self, body: dict[str, Any]) -> dict[str, Any]:
        status, payload = _http(self.opener, "POST", f"{RUNPOD_REST}/pods", headers=self.headers, body=body, timeout=60)
        if status >= 400 or not isinstance(payload, dict) or not payload.get("id"):
            raise RuntimeError(f"RunPod refused the pod ({status}): {str(payload)[:300]}")
        return payload

    def get(self, pod_id: str) -> dict[str, Any] | None:
        status, payload = _http(self.opener, "GET", f"{RUNPOD_REST}/pods/{pod_id}", headers=self.headers)
        if status == 404:
            return None
        if status >= 400:
            raise RuntimeError(f"RunPod status error ({status}): {str(payload)[:200]}")
        return payload if isinstance(payload, dict) else None

    def find(self, name: str) -> list[str]:
        """Ids of pods with this exact name (orphan recovery)."""
        status, payload = _http(self.opener, "GET", f"{RUNPOD_REST}/pods", headers=self.headers)
        if status >= 400 or not isinstance(payload, list):
            return []
        return [str(item["id"]) for item in payload if isinstance(item, dict) and item.get("name") == name and item.get("id")]

    def uptime(self, pod_id: str) -> int | None:
        """Container uptime in seconds (GraphQL runtime); a drop means it restarted."""
        query = 'query { pod(input: {podId: "%s"}) { runtime { uptimeInSeconds } } }' % re.sub(r"[^A-Za-z0-9]", "", pod_id)
        try:
            status, payload = _http(self.opener, "POST", "https://api.runpod.io/graphql", headers=self.headers, body={"query": query})
            runtime = (((payload or {}).get("data") or {}).get("pod") or {}).get("runtime") if status == 200 and isinstance(payload, dict) else None
            return int(runtime["uptimeInSeconds"]) if runtime and runtime.get("uptimeInSeconds") is not None else None
        except Exception:
            return None

    def delete(self, pod_id: str) -> bool:
        status, payload = _http(self.opener, "DELETE", f"{RUNPOD_REST}/pods/{pod_id}", headers=self.headers)
        if status >= 400 and status != 404:
            raise RuntimeError(f"RunPod delete failed ({status}): {str(payload)[:200]}")
        return True


METRICS = {"vllm:num_requests_running": "running", "vllm:num_requests_waiting": "waiting", "vllm:prompt_tokens_total": "prompt_tokens",
           "vllm:generation_tokens_total": "generation_tokens", "vllm:request_success_total": "requests"}


def parse_metrics(text: str) -> dict[str, float]:
    """Sum the vLLM Prometheus series we use (labels ignored)."""
    out: dict[str, float] = {}
    for line in (text or "").splitlines():
        if not line or line.startswith("#"):
            continue
        name = line.split("{", 1)[0].split(" ", 1)[0]
        key = METRICS.get(name)
        if key:
            try:
                out[key] = out.get(key, 0.0) + float(line.rsplit(" ", 1)[1])
            except (IndexError, ValueError):
                continue
    return out


def vllm_metrics(base_url: str, opener=None) -> dict[str, float] | None:
    try:
        status, payload = _http(opener, "GET", f"{base_url}/metrics", timeout=10)
    except Exception:
        return None
    return parse_metrics(payload) if status == 200 and isinstance(payload, str) else None


def utilization_view(state: dict[str, Any]) -> dict[str, Any] | None:
    """Cost per unit of a rented foreman: busy share, $/request, $/Mtok, idle $."""
    usage = state.get("usage") or {}
    ticks = usage.get("ticks") or 0
    if not ticks:
        return None
    spent = float(state.get("spent_usd") or 0)
    busy = usage.get("busy_ticks", 0) / ticks
    generated = usage.get("generation_tokens", 0.0)
    requests = usage.get("requests", 0.0)
    return {
        "busy_pct": round(100 * busy, 1),
        "requests": int(requests),
        "prompt_tokens": int(usage.get("prompt_tokens", 0.0)),
        "generation_tokens": int(generated),
        "usd_per_request": round(spent / requests, 4) if requests else None,
        "usd_per_mtok_generated": round(spent / generated * 1e6, 2) if generated else None,
        "idle_usd": round(spent * (1 - busy), 4),
        "sampled_minutes": round(ticks * TICK_SECONDS / 60, 1),
    }


def crash_report(base_url: str, opener=None) -> str | None:
    """The wrapper's crash log when vLLM has exited, else None."""
    try:
        status, payload = _http(opener, "GET", f"{base_url}/{CRASH_LOG}", timeout=15)
    except Exception:
        return None
    return payload if status == 200 and isinstance(payload, str) and payload.startswith("vLLM exited") else None


def served(base_url: str, repo: str, key: str, opener=None) -> bool:
    try:
        status, payload = _http(opener, "GET", f"{base_url}/v1/models", headers={"authorization": f"Bearer {key}"}, timeout=15)
    except Exception:
        return False
    return status == 200 and any((item or {}).get("id") == repo for item in (payload or {}).get("data") or [])


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------


def home(override: Path | None = None) -> Path:
    if override:
        return Path(override)
    if os.environ.get("AGENT_OS_FOREMAN_HOME"):
        return Path(os.environ["AGENT_OS_FOREMAN_HOME"])
    return budget._home(None) / "foreman"


def state_path(base: Path | None = None) -> Path:
    return home(base) / "deployment.json"


def load_state(base: Path | None = None) -> dict[str, Any]:
    try:
        data = json.loads(state_path(base).read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def _save_state(state: dict[str, Any], base: Path | None = None) -> None:
    from ..storage import write_json

    write_json(state_path(base), state)
    with (home(base) / "history.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps({"at": utc_now_iso(), "id": state.get("id"), "status": state.get("status"), "detail": state.get("detail")}) + "\n")


def active(base: Path | None = None) -> dict[str, Any] | None:
    state = load_state(base)
    return state if state.get("status") in ACTIVE else None


def planner_hold(record: dict[str, Any], base: Path | None = None, unavailable: set[str] | None = None) -> dict[str, Any]:
    """Engine hook before a planner launches in a run that has a foreman.

    ``{"wait": reason}`` while the model is still deploying; ``{"provider":
    id}`` when it is ready (the caller applies it as the planner override);
    ``{"fallback": reason}`` when the deployment ended or failed -- the run
    then plans with its normal planner instead of waiting forever.

    Backup foreman: when the foreman's provider is ``unavailable`` (usage
    limit cooldown, breaker open, not installed), the first backup that is
    available plans instead (``backup_for`` says whom it replaces). When every
    foreman is unavailable the planner waits for the earliest reset rather
    than falling back to a planner that is limited too."""
    wanted = record.get("foreman") or {}
    state = load_state(base)
    if not wanted or state.get("id") != wanted.get("deployment_id"):
        return {"fallback": "the session foreman this run was waiting for is gone"}
    status = state.get("status")
    if status == "ready":
        unavailable = unavailable or set()
        if state["provider_id"] not in unavailable:
            return {"provider": state["provider_id"], "model": state["model"]["repo"], "override_model": state.get("override_model")}
        for backup in state.get("backups") or []:
            if backup.get("provider") and backup["provider"] not in unavailable:
                return {"provider": backup["provider"], "model": backup.get("model") or backup["provider"], "override_model": backup.get("model"),
                        "backup_for": state["provider_id"]}
        return {"wait": f"waiting for the session foreman: {state['provider_id']} and its backups are at their usage limits or unavailable"}
    if status in ("planning", "provisioning", "loading"):
        return {"wait": f"waiting for the session foreman {state['model'].get('repo') if state.get('model') else ''} to finish deploying ({status})"}
    return {"fallback": f"the session foreman {status}: {state.get('detail') or ''}".strip()}


def subscription_choices(registry=None) -> dict[str, dict[str, Any]]:
    """Registered Claude / ChatGPT (Codex) providers and the models each offers."""
    if registry is None:
        from .router import ProviderRegistry

        registry = ProviderRegistry()
    out: dict[str, dict[str, Any]] = {}
    for kind, adapter in SUBSCRIPTION_ADAPTERS.items():
        entry = next((item for item in registry.providers if item.get("adapter") == adapter and item.get("enabled", True)), None)
        if entry:
            models = entry.get("models") or {}
            out[kind] = {"provider": entry["id"], "default": models.get("reasoning") or next(iter(models.values()), None),
                         "models": list(dict.fromkeys(models.get(tier) for tier in ("reasoning", "frontier", "balanced", "fast") if models.get(tier)))}
    return out


def default_backups(primary_provider: str, registry=None) -> list[dict[str, Any]]:
    """Every other subscription foreman, Claude first then ChatGPT; each at its
    default planner model."""
    return [{"kind": kind, "provider": choice["provider"], "model": None}
            for kind, choice in subscription_choices(registry).items() if choice["provider"] != primary_provider]


def _probe_available(entry: dict[str, Any]) -> bool:
    from .adapters import get_adapter

    try:
        return bool(get_adapter(entry).probe().available)
    except Exception:
        return False


def _session_foreman_ids(registry) -> set[str]:
    """Ids the session foreman registered itself (``session_foreman`` key).
    The normalized registry drops that key, so read the raw file too."""
    ids = {str(item["id"]) for item in registry.providers if item.get("session_foreman")}
    path = getattr(registry, "path", None)
    if path and path != "<inline>":
        from ..capabilities import load_providers

        raw = load_providers(Path(path))
        ids |= {str(item.get("id")) for item in raw["providers"] if isinstance(item, dict) and item.get("session_foreman")}
    return ids


def foreman_problem(entry: dict[str, Any], *, session_ids: set[str] = frozenset(),
                    probe: Callable[[dict[str, Any]], bool] | None = None) -> str | None:
    """Why a registered provider cannot be the session foreman; None when it can."""
    if not entry.get("enabled", True):
        return f"provider {entry['id']} is disabled"
    if entry.get("adapter") not in FOREMAN_ADAPTERS:
        return f"provider {entry['id']} uses adapter {entry.get('adapter')!r}; a foreman needs one of {', '.join(FOREMAN_ADAPTERS)}"
    roles = entry.get("roles")
    if roles is not None and "planner" not in roles:
        return f"provider {entry['id']} is not allowed the planner role (roles: {', '.join(roles) or 'none'})"
    if entry.get("session_foreman") or entry["id"] in session_ids:
        return f"provider {entry['id']} is a session-foreman entry itself; pick its source instead"
    if not (probe or _probe_available)(entry):
        return f"provider {entry['id']} is not available (probe failed: not installed, signed out or missing its key)"
    return None


def eligible_foremen(registry=None, probe: Callable[[dict[str, Any]], bool] | None = None) -> list[dict[str, Any]]:
    """Registered providers that can be the session foreman as they are: enabled,
    an API or coding-CLI adapter, allowed to plan, available, and not a
    session-foreman entry. ``paid`` follows model_profile.is_paid, so the
    engine's paid gate (allow_paid_spend) applies to them unchanged."""
    from .model_profile import allowance_summary, is_paid, normalize_profile

    if registry is None:
        from .router import ProviderRegistry

        registry = ProviderRegistry()
    session_ids = _session_foreman_ids(registry)
    out = []
    for entry in registry.providers:
        if foreman_problem(entry, session_ids=session_ids, probe=probe):
            continue
        profile = entry.get("profile") or normalize_profile(None, entry.get("adapter"), entry.get("options"))
        billing = profile.get("billing") if isinstance(profile.get("billing"), dict) else None
        out.append({"provider": entry["id"], "adapter": entry.get("adapter"), "models": dict(entry.get("models") or {}),
                    "deployment": profile.get("deployment"), "paid": is_paid(entry),
                    "billing": allowance_summary(profile) or (billing.get("mode") if billing else None),
                    "refusal_profile": profile.get("refusal_profile")})
    return out


def openrouter_models(opener=None) -> list[dict[str, Any]]:
    """OpenRouter's public model list with per-token prices (USD per million
    tokens), text models only, cheapest input first. No key needed."""
    status, payload = _http(opener, "GET", f"{OPENROUTER_BASE}/v1/models", timeout=30)
    if status != 200 or not isinstance(payload, dict):
        raise ValueError(f"OpenRouter model list unavailable (HTTP {status})")
    out = []
    for item in payload.get("data") or []:
        pricing = item.get("pricing") or {}
        modality = str((item.get("architecture") or {}).get("output_modalities") or ["text"])
        try:
            price_in, price_out = float(pricing.get("prompt") or 0) * 1e6, float(pricing.get("completion") or 0) * 1e6
        except (TypeError, ValueError):
            continue
        if price_in < 0 or price_out < 0 or "text" not in modality:
            continue
        out.append({"id": item.get("id"), "name": item.get("name"), "usd_per_mtok_in": round(price_in, 4), "usd_per_mtok_out": round(price_out, 4),
                    "context": item.get("context_length"), "tools": "tools" in (item.get("supported_parameters") or [])})
    out.sort(key=lambda row: (row["usd_per_mtok_in"] + 0.25 * row["usd_per_mtok_out"], row["id"]))
    return out


# A foreman plan, measured live (Qwen2.5-14B / Opus / gpt-6-astra medians): tokens per plan.
PLAN_TOKENS = {"in": 1700, "out": 500}
LOAD_HOURS = 0.2  # measured deploy-to-ready incl. image pull and weights: 3-20 min


_SIZE_TOKEN = re.compile(r"(?<![\d.])(\d+(?:\.\d+)?)b\b")


def _family(repo: str) -> str:
    name = repo.split("/")[-1].lower()
    return re.sub(r"[^a-z0-9]", "", re.sub(r"-(instruct|chat|it|hf)$", "", name))


def api_alternatives(repo: str, listing: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """The same model family on OpenRouter (e.g. Qwen/Qwen2.5-14B-Instruct ->
    qwen/qwen-2.5-14b-instruct), cheapest first, with its cost per foreman plan."""
    family = _family(repo)
    vendor = repo.split("/")[0].lower()
    size = _SIZE_TOKEN.search(repo.lower())
    exact, similar = [], []
    for row in listing:
        if not row.get("id") or ":free" in row["id"]:
            continue
        per_plan = (PLAN_TOKENS["in"] * row["usd_per_mtok_in"] + PLAN_TOKENS["out"] * row["usd_per_mtok_out"]) / 1e6
        item = {**row, "usd_per_plan": round(per_plan, 6)}
        if _family(row["id"]) == family or _family(row["id"]).startswith(family):
            exact.append({**item, "match": "same model"})
        elif size and row["id"].lower().startswith(vendor + "/") and re.search(rf"(?<![\d.]){re.escape(size.group(1))}b\b", row["id"].lower()):
            similar.append({**item, "match": f"same vendor and size ({size.group(1)}B), different version"})
    key = lambda row: row["usd_per_plan"]
    return sorted(exact, key=key) + sorted(similar, key=key)


def rent_or_api(hourly_usd: float, api_per_plan: float | None, plans_per_hour: float | None = None) -> dict[str, Any]:
    """Break-even between renting a pod and paying per token."""
    if not api_per_plan:
        return {"advice": "no per-token API serves this model or a same-size sibling: renting is the way to run it"}
    break_even = hourly_usd / api_per_plan
    result = {"break_even_plans_per_hour": round(break_even), "api_usd_per_plan": api_per_plan,
              "pod_load_usd": round(hourly_usd * LOAD_HOURS, 3)}
    if plans_per_hour is not None:
        result["pod_usd_per_plan"] = round((hourly_usd + hourly_usd * LOAD_HOURS) / max(plans_per_hour, 1e-9), 5)
    result["advice"] = (f"a per-token API is cheaper unless this pod serves more than ~{round(break_even):,} plans an hour "
                        "(or you need custom weights, training, or no third-party API)")
    return result


def local_models(base_url: str, key: str | None = None, opener=None, path_style: str = "auto") -> list[str]:
    """Model ids listed by an OpenAI-compatible server."""
    models_url = endpoints.url(base_url, "models", path_style)
    try:
        status, payload = _http(opener, "GET", models_url, headers={"authorization": f"Bearer {key}"} if key else None, timeout=10)
    except OSError as exc:
        raise ValueError(f"nothing answered at {base_url}: start your local server (e.g. Ollama or LM Studio) and load a model first") from exc
    if status != 200 or not isinstance(payload, dict):
        raise ValueError(f"no OpenAI-compatible server answered at {base_url} (HTTP {status})")
    return [str(item.get("id")) for item in payload.get("data") or [] if isinstance(item, dict) and item.get("id")]


# ---------------------------------------------------------------------------
# Manager: deploy thread + watchdog
# ---------------------------------------------------------------------------


class ForemanManager:
    """One deployment at a time, per machine. Thread-safe; all state is persisted."""

    def __init__(self, *, base: Path | None = None, budget_home: Path | None = None, opener=None, resolve=None,
                 store_secret=None, register=None, unregister=None, run_loader=None, clock: Callable[[], float] = time.time,
                 sleep: Callable[[float], None] = time.sleep, inventory=None, registry=None,
                 probe: Callable[[dict[str, Any]], bool] | None = None) -> None:
        from . import secret_refs

        self.registry = registry
        self.probe = probe
        self.base = base
        self.budget_home = budget_home
        self.opener = opener
        self.resolve = resolve or secret_refs.resolve
        self.store_secret = store_secret or secret_refs.store
        self.register = register or _register_provider
        self.unregister = unregister or _unregister_provider
        self.run_loader = run_loader or _load_run
        self.clock = clock
        self.sleep = sleep
        self.inventory = inventory
        self._lock = threading.RLock()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    # -- views ------------------------------------------------------------

    def status(self) -> dict[str, Any]:
        state = load_state(self.base)
        view = {key: state.get(key) for key in ("id", "kind", "status", "detail", "provider_id", "override_model", "backups", "pod_id", "base_url", "hourly_usd", "cap_usd",
                                               "spent_usd", "deadline_epoch", "started_at", "ready_at", "ended_at", "runs", "idle_minutes")}
        if view["status"] and not view["kind"]:
            view["kind"] = "huggingface"
        try:
            view["choices"] = subscription_choices(self.registry)
        except Exception:
            view["choices"] = {}
        view["model"] = state.get("model")
        view["gpu"] = state.get("gpu")
        view["utilization"] = utilization_view(state)
        try:
            from . import foreman_strategy

            host = foreman_strategy.host_models()
            view["host"] = host
            live = view["status"] in ACTIVE
            view["recommendation"] = foreman_strategy.recommend(host, view["kind"] if live else None,
                                                                (state.get("model") or {}).get("repo") if live else None, self.registry)
            if live and state.get("model"):
                model = state.get("override_model") or state["model"]["repo"]
                view["strategy"] = {key: value for key, value in foreman_strategy.strategy_for(model).items() if key != "planner_addendum"}
        except Exception:
            view["host"], view["recommendation"] = None, None
        if state.get("deadline_epoch") and state.get("status") in ACTIVE:
            view["minutes_left"] = max(0, round((state["deadline_epoch"] - self.clock()) / 60))
        view["budget"] = budget.show(self.budget_home)
        view["watching"] = bool(self._thread and self._thread.is_alive())
        return view

    def preview(self, link: str, cap_usd: float, coding_agent: bool = False) -> dict[str, Any]:
        """Plan only: model facts, VRAM need and the GPU that would be rented. No spend."""
        parsed = parse_hf_link(link)
        token = self.resolve(HF_SECRET)
        info = hf_model(parsed["repo"], parsed["revision"], token=token, opener=self.opener)
        config = hf_config(info.get("id") or parsed["repo"], info.get("sha") or parsed["revision"] or "main", token=token, opener=self.opener)
        model = summarize_info(info, config)
        if coding_agent:
            model["agent"] = True
            if str(model.get("model_type") or "") not in TOOL_PARSERS:
                return {"model": model, "error": f"no known tool-call parser for model family {model.get('model_type')!r}; deploy it as a planner only"}
        problem = deployable_problem(model)
        if not problem and (model["gated"] or model["private"]) and not config:
            problem = (f"{model['repo']} is gated and your Hugging Face token cannot read it: accept its licence on huggingface.co "
                       "with the account whose token is in secrets://huggingface/default")
        if problem:
            return {"model": model, "error": problem}
        need = vram_needed_gb(model)
        offers = self._offers()
        chosen = choose_gpu(offers, need, cap_usd, heads=model.get("attention_heads"))
        result = {"model": model, "vram_needed_gb": need, "context": context_for(model), **chosen}
        try:  # rent-vs-API: the same family per token, when OpenRouter serves it
            alternatives = api_alternatives(model["repo"], openrouter_models(self.opener))[:3]
        except Exception:
            alternatives = None
        if alternatives is not None and chosen.get("choice"):
            result["api_alternatives"] = alternatives
            result["rent_or_api"] = rent_or_api(chosen["choice"]["hourly_usd"], alternatives[0]["usd_per_plan"] if alternatives else None)
        return result

    def _offers(self) -> list[dict[str, Any]]:
        if self.inventory is not None:
            return self.inventory()
        from . import compute

        result = compute.runpod_inventory(opener=self.opener)
        if not result.get("offers") and result.get("error"):
            raise RuntimeError(f"RunPod GPU prices unavailable: {result['error']}")
        return result["offers"]

    # -- operator actions -------------------------------------------------

    def _replace_current(self, reason: str) -> None:
        with self._lock:
            current = active(self.base)
            if current:
                self._stop.set()
                self._teardown(current, "stopped", reason)
                if self._thread and self._thread.is_alive() and self._thread is not threading.current_thread():
                    self._thread.join(5)
            self._stop.clear()

    def _backups(self, primary_provider: str, backups: list[str] | None) -> list[dict[str, Any]]:
        """``None`` = automatic (every other subscription); ``[]`` = no backup;
        or explicit kinds in order, e.g. ["chatgpt"]."""
        if backups is None:
            return default_backups(primary_provider, self.registry)
        choices = subscription_choices(self.registry)
        return [{"kind": kind, "provider": choices[kind]["provider"], "model": None}
                for kind in backups if kind in choices and choices[kind]["provider"] != primary_provider]

    def use(self, kind: str, *, model: str | None = None, base_url: str | None = None, secret_ref: str | None = None,
            backups: list[str] | None = None, provider: str | None = None) -> dict[str, Any]:
        """Make a subscription model (claude / chatgpt), a locally served model or
        any eligible registered provider (``registered``, ``provider=<id>``) the
        session foreman. No rental, so it is ready at once."""
        if kind not in NOT_RENTED:
            raise ValueError(f"source must be claude, chatgpt, openrouter, local or registered (huggingface uses deploy), got {kind!r}")
        if kind == "registered":
            if not provider:
                raise ValueError("pick a registered provider id (see GET foreman/eligible, or the GUI's Registered provider list)")
            registry = self.registry
            if registry is None:
                from .router import ProviderRegistry

                registry = ProviderRegistry()
            entry = registry.get(provider)
            if entry is None:
                raise ValueError(f"provider {provider!r} is not registered (see orchestrate providers)")
            problem = foreman_problem(entry, session_ids=_session_foreman_ids(registry), probe=self.probe)
            if problem:
                raise ValueError(problem)
            models = entry.get("models") or {}
            offered = list(dict.fromkeys(str(value) for value in models.values() if value))
            if model and model not in offered:
                raise ValueError(f"{provider} offers {', '.join(offered) or 'no models'}; got {model!r}")
            default = models.get("reasoning") or (offered[0] if offered else provider)
            fields = {"provider_id": provider, "override_model": model, "registered": False,
                      "model": {"repo": model or default}, "detail": f"registered provider {provider}; no rental"}
        elif kind == "openrouter":
            if not self.resolve(OPENROUTER_SECRET):
                raise ValueError("OpenRouter API key missing: orchestrate secrets setup (openrouter.ai > Keys; set a credit limit on the key)")
            if not model:
                raise ValueError("pick an OpenRouter model id, e.g. qwen/qwen3-235b-a22b-2507 (see the model list)")
            listed = {row["id"]: row for row in openrouter_models(self.opener)}
            if model not in listed:
                raise ValueError(f"OpenRouter does not list {model!r}")
            row = listed[model]
            fields = {"provider_id": OPENROUTER_PROVIDER, "base_url": OPENROUTER_BASE, "secret_ref": OPENROUTER_SECRET, "deployment": "api",
                      "model": {"repo": model, "usd_per_mtok_in": row["usd_per_mtok_in"], "usd_per_mtok_out": row["usd_per_mtok_out"],
                                "context": row["context"]},
                      "registered": True, "detail": f"OpenRouter per-token: ${row['usd_per_mtok_in']}/M in, ${row['usd_per_mtok_out']}/M out; no rental"}
        elif kind == "local":
            if not base_url:
                raise ValueError("a local model needs its server URL, e.g. http://127.0.0.1:11434 (Ollama) or http://127.0.0.1:8000 (vLLM)")
            key = self.resolve(secret_ref) if secret_ref else None
            served_models = local_models(base_url, key, self.opener)
            if not served_models:
                raise ValueError(f"the server at {base_url} lists no models")
            model = model or served_models[0]
            if model not in served_models:
                raise ValueError(f"{base_url} does not serve {model!r}; it serves {', '.join(served_models[:8])}")
            fields = {"provider_id": LOCAL_PROVIDER, "base_url": base_url.rstrip("/"), "secret_ref": secret_ref, "deployment": None,
                      "model": {"repo": model}, "registered": True, "detail": f"your local server {base_url.rstrip('/')}; no rental"}
        else:
            choice = subscription_choices(self.registry).get(kind)
            if not choice:
                raise ValueError(f"no {kind} provider is registered and enabled (see orchestrate providers)")
            if model and model not in choice["models"]:
                raise ValueError(f"{kind} offers {', '.join(choice['models'])}; got {model!r}")
            fields = {"provider_id": choice["provider"], "override_model": model, "registered": False,
                      "model": {"repo": model or choice["default"]}, "detail": "your subscription; no GPU rental"}
        self._replace_current(f"replaced by the {kind} foreman")
        with self._lock:
            state = {"id": f"FMN-{uuid.uuid4().hex[:8]}", "kind": kind, "status": "ready", "runs": [], "started_at": utc_now_iso(),
                     "ready_at": utc_now_iso(), "last_needed_epoch": self.clock(), "spent_usd": 0.0, **fields,
                     "backups": self._backups(fields["provider_id"], backups)}
            if state["registered"]:
                self.register(state)
            _save_state(state, self.base)
        return self.status()

    def deploy(self, link: str, *, job_cap_usd: float | None = None, idle_minutes: int = DEFAULT_IDLE_MINUTES,
               background: bool = True, backups: list[str] | None = None, coding_agent: bool = False) -> dict[str, Any]:
        """Start an autonomous deployment. Refuses when one is active, the budget
        is not approved, or the RunPod key is missing."""
        parse_hf_link(link)  # fail fast on a bad link, before anything is replaced
        if not self.resolve(RUNPOD_SECRET):
            raise ValueError("RunPod API key missing: orchestrate secrets setup (needs read/write to create pods)")
        if not budget.effective(None, self.budget_home)["approved"]:
            raise ValueError("no approved compute budget: set a project budget and job budget first")
        self._replace_current("replaced by a Hugging Face foreman")
        with self._lock:
            effective = budget.effective({"job_hard_cap_usd": job_cap_usd} if job_cap_usd else None, self.budget_home)
            if not effective["approved"]:
                raise ValueError("no approved compute budget: set a project budget and job budget first")
            caps = [value for value in (effective.get("job_hard_cap_usd"), effective.get("project_usd")) if value is not None]
            cap = min(caps) if caps else 0.0
            if cap <= 0:
                raise ValueError("the budget has nothing left for this job")
            if not self.resolve(RUNPOD_SECRET):
                raise ValueError("RunPod API key missing: orchestrate secrets setup (needs read/write to create pods)")
            parse_hf_link(link)  # fail fast on a bad link, before any thread starts
            state = {"id": f"FMN-{uuid.uuid4().hex[:8]}", "kind": "huggingface", "status": "planning", "detail": "reading the model from Hugging Face",
                     "link": link, "cap_usd": round(cap, 4), "spent_usd": 0.0, "idle_minutes": int(idle_minutes), "runs": [],
                     "backups": self._backups("", backups), "coding_agent": bool(coding_agent),
                     "started_at": utc_now_iso(), "model": None}
            _save_state(state, self.base)
            self._stop.clear()
        if background:
            self._thread = threading.Thread(target=self._run, args=(state["id"],), name="agent-os-foreman", daemon=True)
            self._thread.start()
        else:
            self._run(state["id"])
        return self.status()

    def stop(self, reason: str = "stopped by operator") -> dict[str, Any]:
        self._stop.set()
        with self._lock:
            state = load_state(self.base)
            if state.get("status") in ACTIVE or state.get("status") == PENDING:
                self._teardown(state, "stopped", reason if state.get("status") != PENDING else state.get("detail", reason))
        return self.status()

    def attach(self, run_id: str) -> dict[str, Any] | None:
        """Called by engine.create_run: tie a new run to the live foreman."""
        with self._lock:
            state = active(self.base)
            if not state:
                return None
            if run_id not in state["runs"]:
                state["runs"].append(run_id)
            state["last_needed_epoch"] = self.clock()
            _save_state(state, self.base)
            return {"deployment_id": state["id"], "model": (state.get("model") or {}).get("repo"), "attached_at": utc_now_iso()}

    def reap(self) -> dict[str, Any]:
        """Run from outside the watchdog's process (Task Scheduler, a later
        session): a rented pod whose watchdog has been silent for
        REAP_AFTER_SECONDS lost its process (closed window, reboot, memory
        pressure) -- delete it. Never touches a subscription/local foreman."""
        state = load_state(self.base)
        if state.get("status") == PENDING:
            self._teardown(state, state.get("pending_status") or "stopped", "pod delete retried by the reaper")
            return {**self.status(), "reaped": True}
        if state.get("status") not in ACTIVE or not state.get("pod_id") or state.get("kind") in NOT_RENTED:
            return {**self.status(), "reaped": False}
        beat = float(state.get("watchdog_epoch") or state.get("pod_created_epoch") or 0)
        silent = self.clock() - beat
        if silent <= REAP_AFTER_SECONDS:
            return {**self.status(), "reaped": False, "watchdog_seconds_ago": round(silent)}
        self._teardown(state, "stopped", f"watchdog silent for {round(silent / 60, 1)} min (its process ended); pod deleted by the reaper")
        return {**self.status(), "reaped": True}

    def resume(self) -> dict[str, Any]:
        """On GUI start: enforce a passed deadline at once, else keep watching."""
        state = load_state(self.base)
        if state.get("status") == PENDING:
            self._teardown(state, state.get("pending_status") or "stopped", "pod delete retried after a restart")
            return self.status()
        if state.get("status") not in ACTIVE or state.get("kind") in NOT_RENTED:
            return self.status()  # nothing rented: nothing to meter or enforce
        if not state.get("pod_id"):
            # Interrupted between "create pod" and saving its id: delete any pod with our name.
            orphans = []
            if state.get("status") == "provisioning" and self.resolve(RUNPOD_SECRET):
                client = RunPod(self.resolve(RUNPOD_SECRET) or "", self.opener)
                for pod_id in client.find(_pod_name(state)):
                    client.delete(pod_id)
                    orphans.append(pod_id)
            self._teardown(state, "failed", "interrupted before the pod was recorded" + (f"; deleted orphan pod(s) {', '.join(orphans)}" if orphans else ""))
            return self.status()
        if not (self._thread and self._thread.is_alive()):
            self._stop.clear()
            self._thread = threading.Thread(target=self._run, args=(state["id"],), name="agent-os-foreman", daemon=True)
            self._thread.start()
        return self.status()

    # -- worker -----------------------------------------------------------

    def _update(self, state: dict[str, Any], **fields: Any) -> dict[str, Any]:
        with self._lock:
            current = load_state(self.base)
            if current.get("id") != state["id"] or current.get("status") not in ACTIVE:
                raise _Superseded()  # stopped (possibly by another process) or replaced
            state.update({key: value for key, value in current.items() if key == "runs"}, **fields)
            _save_state(state, self.base)
            return state

    def _run(self, deployment_id: str) -> None:
        state = load_state(self.base)
        if state.get("id") != deployment_id:
            return
        network_failures = 0
        while True:
            try:
                if not state.get("pod_id"):
                    state = self._provision(state)
                if state["status"] == "loading":
                    state = self._await_ready(state)
                self._watch(state)
                return
            except _Superseded:
                return
            except OSError as exc:  # DNS / connection / timeout: this machine's network, not the pod
                network_failures += 1
                state = load_state(self.base)
                if state.get("id") != deployment_id or state.get("status") not in ACTIVE:
                    return
                if network_failures > NETWORK_RETRY_TICKS:
                    self._teardown(state, "failed", f"network unreachable for {network_failures} ticks: {str(exc)[:200]}")
                    return
                try:
                    if state.get("pod_id"):
                        state = self._meter(state)  # spend keeps counting while the network is down
                    state = self._update(state, detail=f"network problem, retrying ({network_failures}/{NETWORK_RETRY_TICKS}): {str(exc)[:160]}")
                except _Superseded:
                    return
                self.sleep(TICK_SECONDS)
            except Exception as exc:  # every other failure ends with the pod deleted
                self._teardown(load_state(self.base), "failed", f"{type(exc).__name__}: {str(exc)[:300]}")
                return

    def _provision(self, state: dict[str, Any]) -> dict[str, Any]:
        plan = self.preview(state["link"], state["cap_usd"], coding_agent=bool(state.get("coding_agent")))
        if plan.get("error"):
            raise RuntimeError(plan["error"])
        model, choice = plan["model"], plan["choice"]
        state = self._update(state, model=model, gpu=choice, vram_needed_gb=plan["vram_needed_gb"], status="provisioning",
                             detail=f"renting {choice['gpu_count']}x {choice['name']} ({choice['tier']}) at ${choice['hourly_usd']:.2f}/h")
        endpoint_key = token_lib.token_urlsafe(32)
        self.store_secret(ENDPOINT_SECRET, endpoint_key)
        client = RunPod(self.resolve(RUNPOD_SECRET) or "", self.opener)
        for leftover in client.find(_pod_name(state)):  # a create whose response was lost: never run two
            client.delete(leftover)
        last_error = None
        tried = []
        for group in attempt_groups([choice, *plan.get("alternatives", [])]):
            candidate = group[0]
            tried.append(f"{candidate['gpu_count']}x {'/'.join(item['name'] for item in group)} ({candidate['tier']})")
            body = pod_request(model, group, endpoint_key, self.resolve(HF_SECRET), _pod_name(state))
            try:
                pod = client.create(body)
            except RuntimeError as exc:  # usually "no capacity" for that GPU type; try the next one
                last_error = exc
                continue
            rented = next((item for item in group if item["gpu_id"] == ((pod.get("machine") or {}).get("gpuTypeId") or (pod.get("gpu") or {}).get("id"))), None)
            candidate = rented or {**candidate, "name": "/".join(item["name"] for item in group), "hourly_usd": max(item["hourly_usd"] for item in group)}
            # RunPod's costPerHr is authoritative; without it assume the priciest type in the group
            hourly = float(pod.get("costPerHr") or candidate["hourly_usd"])
            now = self.clock()
            max_hours = state["cap_usd"] * STOP_FRACTION / hourly
            return self._update(state, gpu=candidate, pod_id=pod["id"], base_url=endpoint_url(pod["id"]), hourly_usd=hourly,
                                pod_created_epoch=now, billed_until_epoch=now, deadline_epoch=now + max_hours * 3600,
                                status="loading", detail=f"pod {pod['id']} is downloading {model['repo']} and starting vLLM")
        raise RuntimeError(f"no GPU could be rented (tried {'; '.join(tried)}): {last_error}")

    def _await_ready(self, state: dict[str, Any]) -> dict[str, Any]:
        key = self.resolve(ENDPOINT_SECRET) or ""
        client = RunPod(self.resolve(RUNPOD_SECRET) or "", self.opener)
        limit = state["pod_created_epoch"] + LOAD_TIMEOUT_MINUTES * 60
        polls, restarts, last_uptime = 0, 0, None
        while not self._stop.is_set():
            state = self._meter(state)
            if state["status"] not in ACTIVE:
                raise _Superseded()
            report = crash_report(state["base_url"], self.opener)
            if report:
                raise RuntimeError("vLLM failed to start: " + " | ".join(line for line in report.splitlines()[-12:] if line.strip())[:900])
            uptime = client.uptime(state["pod_id"])
            if uptime is not None and last_uptime is not None and uptime + TICK_SECONDS < last_uptime:
                restarts += 1
                if restarts >= 2:
                    raise RuntimeError("the container keeps restarting before vLLM starts (crash loop)")
            last_uptime = uptime if uptime is not None else last_uptime
            if served(state["base_url"], state["model"]["repo"], key, self.opener):
                state = self._update(state, status="ready", ready_at=utc_now_iso(), last_needed_epoch=self.clock(), registered=True,
                                     provider_id=_provider_id(state), detail="serving; new runs use it as their planner")
                self.register(state)
                return state
            polls += 1
            if polls % 6 == 0:  # every ~3 minutes: is the pod still alive?
                pod = client.get(state["pod_id"])
                if pod is None or pod.get("desiredStatus") in ("EXITED", "TERMINATED"):
                    raise RuntimeError(f"the pod stopped while loading ({(pod or {}).get('lastStatusChange') or 'deleted'})")
            if self.clock() > limit:
                raise RuntimeError(f"the model was not served within {LOAD_TIMEOUT_MINUTES} minutes")
            self.sleep(TICK_SECONDS)
        raise _Superseded()

    def _sample(self, state: dict[str, Any]) -> dict[str, Any]:
        """One utilization sample from the pod's vLLM /metrics (counters are cumulative)."""
        metrics = vllm_metrics(state["base_url"], self.opener)
        if metrics is None:
            return state
        usage = dict(state.get("usage") or {})
        usage["ticks"] = usage.get("ticks", 0) + 1
        if metrics.get("running", 0) + metrics.get("waiting", 0) > 0:
            usage["busy_ticks"] = usage.get("busy_ticks", 0) + 1
        for key in ("prompt_tokens", "generation_tokens", "requests"):
            usage[key] = max(usage.get(key, 0.0), metrics.get(key, 0.0))
        return self._update(state, usage=usage)

    def _watch(self, state: dict[str, Any]) -> None:
        while not self._stop.is_set():
            state = self._meter(state)
            if state["status"] not in ACTIVE:
                return
            state = self._sample(state)
            if self._idle(state):
                self._teardown(state, "stopped", f"every attached run has planned and the foreman was idle for {state['idle_minutes']} min")
                return
            self.sleep(TICK_SECONDS)

    def _meter(self, state: dict[str, Any]) -> dict[str, Any]:
        """Record spend since the last tick; tear down before the cap is crossed."""
        now = self.clock()
        state = self._update(state, watchdog_epoch=now)  # heartbeat for the reaper
        amount = state["hourly_usd"] * max(now - state["billed_until_epoch"], 0) / 3600
        if amount > 0:
            budget.record_spend(amount, job_id=state["id"], provider="runpod", note=f"pod {state['pod_id']}", home=self.budget_home)
            state = self._update(state, spent_usd=round(state["spent_usd"] + amount, 4), billed_until_epoch=now)
        next_tick = state["hourly_usd"] * (2 * TICK_SECONDS) / 3600
        left = budget.remaining(self.budget_home)
        if now >= state["deadline_epoch"] or state["spent_usd"] + next_tick >= state["cap_usd"] * STOP_FRACTION:
            self._teardown(state, "stopped", f"job budget reached (${state['spent_usd']:.2f} of ${state['cap_usd']:.2f})")
            return load_state(self.base)
        if left is not None and left <= next_tick:
            self._teardown(state, "stopped", "project budget exhausted")
            return load_state(self.base)
        return state

    def _idle(self, state: dict[str, Any]) -> bool:
        if state.get("status") != "ready":
            return False
        busy = False
        for run_id in state.get("runs") or []:
            try:
                record = self.run_loader(run_id)
            except Exception:
                continue
            planner = (record.get("nodes") or {}).get("plan")
            if record.get("state") not in ("COMPLETE", "FAILED") and (planner is None or planner.get("state") not in ("PASSED", "FAILED_FINAL", "CANCELLED")):
                busy = True
        if busy:
            self._update(state, last_needed_epoch=self.clock())
            return False
        return self.clock() - float(state.get("last_needed_epoch") or 0) > state["idle_minutes"] * 60

    def _teardown(self, state: dict[str, Any], status: str, detail: str) -> None:
        with self._lock:
            if not state or (state.get("status") not in ACTIVE and state.get("status") != PENDING):
                return
            problems = []
            if state.get("base_url") and state.get("status") == "ready":
                metrics = vllm_metrics(state["base_url"], self.opener)  # final totals: work since the last tick counts too
                if metrics:
                    usage = dict(state.get("usage") or {})
                    for key in ("prompt_tokens", "generation_tokens", "requests"):
                        usage[key] = max(usage.get(key, 0.0), metrics.get(key, 0.0))
                    usage.setdefault("ticks", 1)
                    state["usage"] = usage
            if state.get("pod_id"):
                deleted, error = False, None
                for attempt in range(DELETE_ATTEMPTS):
                    self._bill_tail(state)
                    try:
                        RunPod(self.resolve(RUNPOD_SECRET) or "", self.opener).delete(state["pod_id"])
                        deleted = True
                        break
                    except Exception as exc:
                        error = exc
                        if attempt + 1 < DELETE_ATTEMPTS:
                            self.sleep(TICK_SECONDS)
                if not deleted:
                    # Keep the pod on record so resume / stop / GUI start retry until RunPod confirms.
                    state.update(status=PENDING, pending_status=status, detail=f"{detail}; POD STILL RUNNING, delete not confirmed yet "
                                 f"(will retry; or delete pod {state['pod_id']} in the RunPod console): {str(error)[:160]}")
                    _save_state(state, self.base)
                    return
                self._bill_tail(state)
            if state.get("provider_id") and state.get("registered", bool(state.get("pod_id"))):
                try:
                    self.unregister(state)
                except Exception as exc:
                    problems.append(f"provider entry not removed: {exc}")
            status = state.pop("pending_status", None) or status
            state.update(status="failed" if problems and status != "failed" else status, ended_at=utc_now_iso(),
                         detail="; ".join([detail, *problems]))
            _save_state(state, self.base)

    def _bill_tail(self, state: dict[str, Any]) -> None:
        """Record spend from the last metered tick to now (the pod bills until deleted)."""
        now = self.clock()
        tail = state["hourly_usd"] * max(now - state.get("billed_until_epoch", now), 0) / 3600
        if tail > 0:
            budget.record_spend(tail, job_id=state["id"], provider="runpod", note=f"pod {state['pod_id']} final", home=self.budget_home)
            state["spent_usd"] = round(state.get("spent_usd", 0) + tail, 4)
            state["billed_until_epoch"] = now


class _Superseded(Exception):
    """The deployment was stopped or replaced while this thread worked."""


def _pod_name(state: dict[str, Any]) -> str:
    return f"agent-os-foreman-{state['id']}"


def _provider_id(state: dict[str, Any]) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", state["model"]["repo"].split("/")[-1].lower()).strip("-")[:32]
    return f"foreman-{slug or 'model'}"


def _register_provider(state: dict[str, Any]) -> None:
    from .model_profile import endpoint_entry
    from .service import add_model_endpoint

    model = state["model"]
    kind = state.get("kind")
    local, api = kind == "local", kind == "openrouter"
    entry = endpoint_entry(state["provider_id"], base_url=state["base_url"], model=model["repo"], classes=["fast", "balanced", "reasoning", "frontier"],
                           refusal_profile=model.get("refusal_hint") or "unknown", deployment="api" if api else None if local else "gpu_pod",
                           open_weights=None if (local or api) else True, license=model.get("license"), revision=model.get("sha"),
                           context_window=model.get("context") if api else None if local else context_for(model),
                           secret_ref=state.get("secret_ref") if (local or api) else ENDPOINT_SECRET,
                           cost=0.05 if api else 0.25, max_concurrency=4 if not local else 2, roles=["planner", "inline"])
    if api:
        entry["options"]["request_timeout"] = 600
    entry["options"]["request_timeout"] = 900
    entry["session_foreman"] = state["id"]
    result = add_model_endpoint(entry, write=True, force=True)
    if result.get("error"):
        raise RuntimeError(result["error"])
    agent = agent_entry(state)
    if agent:
        add_model_endpoint(agent, write=True, force=True)


def agent_entry(state: dict[str, Any]) -> dict[str, Any] | None:
    """A Codex CLI worker driving the rented model with Codex's own repository
    tools, through a custom Responses-API provider. Priced far below the
    subscriptions so fast implementation tasks try the GPU first and escalate
    on failure. None when the model family has no known tool-call parser."""
    model = state.get("model") or {}
    if not agent_capable(model) or state.get("kind") not in (None, "huggingface"):
        return None
    name = "agentosgpu"
    return {
        "id": state["provider_id"] + AGENT_SUFFIX,
        "adapter": "codex_cli",
        "enabled": True,
        "models": {"fast": model["repo"], "balanced": model["repo"]},
        "costs": {"fast": 0.1, "balanced": 0.3},
        "roles": ["implementer", "test_author", "repairer"],
        "max_concurrency": 4,
        "options": {
            "use_user_config": False,
            "extra_config": {"model_provider": name, f"model_providers.{name}.name": "Agent OS GPU",
                             f"model_providers.{name}.base_url": endpoints.api_root(state['base_url']), f"model_providers.{name}.env_key": GPU_KEY_ENV,
                             f"model_providers.{name}.wire_api": "responses"},
            "secret_env": {GPU_KEY_ENV: ENDPOINT_SECRET},
        },
        "profile": {"deployment": "gpu_pod", "open_weights": True, "refusal_profile": model.get("refusal_hint") or "unknown"},
        "session_foreman": state.get("id"),
    }


def _unregister_provider(state: dict[str, Any]) -> None:
    from ..capabilities import registry_path
    from ..storage import write_json

    path = registry_path()
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return
    ours = {state["provider_id"], state["provider_id"] + AGENT_SUFFIX}
    providers = [item for item in data.get("providers") or [] if not (isinstance(item, dict) and item.get("id") in ours)]
    if len(providers) != len(data.get("providers") or []):
        data["providers"] = providers
        write_json(path, data)
    try:
        from .service import engine

        engine().reload_providers()
    except Exception:
        pass


def _load_run(run_id: str) -> dict[str, Any]:
    from .service import engine

    return engine().load(run_id)


_MANAGER: ForemanManager | None = None
_MANAGER_LOCK = threading.Lock()


def manager() -> ForemanManager:
    global _MANAGER
    with _MANAGER_LOCK:
        if _MANAGER is None:
            _MANAGER = ForemanManager()
        return _MANAGER
