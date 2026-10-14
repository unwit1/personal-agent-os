"""Local conversations over the existing subscription and HTTP adapters.

Routing is fixed per conversation so changing a select cannot leak an earlier
sensitive turn to another provider. Dependencies can be injected for offline tests.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import threading
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ..orchestrator import endpoints, model_profile, secret_refs, usage_hub
from ..orchestrator.router import ProviderRegistry
from .window import model_bridge
from .window.confirm import ENV_HOME, _write_json, window_home

ADAPTERS = frozenset({"claude_code", "codex_cli", "openai_api"})
_ID = re.compile(r"^[A-Za-z0-9_-]{1,100}$")
_LOCK = threading.RLock()
_CONVERSATION_LOCKS: dict[str, threading.RLock] = {}
_QUOTA_LOCK = threading.Lock()


def _conversation_lock(id: str) -> Any:
    with _LOCK:
        return _CONVERSATION_LOCKS.setdefault(str(Path(id).resolve()).casefold(), threading.RLock())


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        # Redirecting a completion could disclose the prompt or Authorization
        # header to a different host. A configured endpoint must answer directly.
        return None


def _entries(registry: Any = None) -> list[dict]:
    entries = [p for p in (registry or ProviderRegistry()).providers
               if p.get("enabled", True) and p.get("adapter") in ADAPTERS]
    if secret_refs.status("secrets://openrouter/default")["configured"]:
        from ..orchestrator.free_dispatch import FreeInputs

        slugs = list(dict.fromkeys(p["slug"] for p in FreeInputs.load_default().catalog.get("models", []) if p.get("slug")))
        entries = [p for p in entries if p["id"] != "openrouter-free"]
        entries.append({"id": "openrouter-free", "adapter": "openai_api", "label": "OpenRouter free",
                        "models": {slug: slug for slug in slugs},
                        "options": {"base_url": "https://openrouter.ai/api/v1", "secret_ref": "secrets://openrouter/default"}})
    return entries


def providers(registry: Any = None) -> list[dict]:
    entries = _entries(registry)
    rows = usage_hub.plans(entries, usage_hub._home())
    states = {pid: row.get("state", "unknown") for row in rows for pid in row["providers"]}
    return [{"id": p["id"], "label": p.get("label") or p["id"], "adapter": p["adapter"],
             "models": list(dict.fromkeys(p.get("models", {}).values())),
             "default_model": p.get("models", {}).get("balanced") or next(iter(p.get("models", {}).values()), None),
             "sensitive_ok": model_profile.sensitive_problem(p) is None, "headroom": states.get(p["id"], "unknown")}
            for p in entries]


def _path(home: Path | str, conversation_id: str) -> Path:
    if not isinstance(conversation_id, str) or not _ID.fullmatch(conversation_id):
        raise ValueError("invalid conversation id")
    path = Path(home) / "chats" / f"{conversation_id}.json"
    if path.is_symlink() or path.parent.resolve() != (Path(home).resolve() / "chats"):
        raise ValueError("invalid conversation path")
    return path


def conversation(home: Path | str, id: str) -> dict:
    try:
        data = json.loads(_path(home, id).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        raise KeyError("unknown conversation") from None
    if not isinstance(data, dict) or data.get("deleted"):
        raise KeyError("unknown conversation")
    return data


def conversations(home: Path | str) -> list[dict]:
    out = []
    for path in (Path(home) / "chats").glob("*.json"):
        try:
            data = conversation(home, path.stem)
        except (KeyError, ValueError):
            continue
        out.append({key: data.get(key) for key in ("id", "title", "provider", "model", "project", "updated_at")})
    return sorted(out, key=lambda p: p.get("updated_at") or "", reverse=True)


def delete(home: Path | str, id: str) -> dict:
    with _conversation_lock(str(_path(home, id))):
        conversation(home, id)
        # Replace with a tombstone rather than deleting repository/local files.
        _write_json(_path(home, id), {"id": id, "deleted": True})
    return {"deleted": id}


def _context(text: str, project: str | None) -> str:
    if not project:
        return ""
    from ..chat import context

    return json.dumps(context(query=text, project_hint=project, token_budget=1500), default=str)


def _redact(value: Any, key: str) -> Any:
    if isinstance(value, str):
        return value.replace(key, "[redacted]")
    if isinstance(value, list):
        return [_redact(item, key) for item in value]
    if isinstance(value, dict):
        return {_redact(k, key): _redact(v, key) for k, v in value.items()}
    return value


def _codex(entry: dict, model: str, messages: list[dict], runner: Any, home: Path) -> dict:
    root = model_bridge.REPO_ROOT
    argv = [entry.get("executable") or "codex", "exec", "--json", "--skip-git-repo-check", "-s", "read-only", "-m", model,
            "-c", f"mcp_servers.agent-os.command={json.dumps(sys.executable)}",
            "-c", f'mcp_servers.agent-os.args={json.dumps([str(root / "agent.py"), "mcp"])}',
            "\n".join(f"{m['role']}: {m['content']}" for m in messages)]
    # Subscription CLIs must not silently use an inherited API credential.
    env = {k: v for k, v in model_bridge._child_env().items() if k not in {"OPENAI_API_KEY", "OPENAI_BASE_URL"}}
    env[ENV_HOME] = str(home)
    done = runner(argv, cwd=str(root), capture_output=True, text=True, encoding="utf-8", timeout=600, env=env)
    if done.returncode:
        return {"error": "Codex request failed"}
    reply, usage = "", {}
    for line in (done.stdout or "").splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        item = event.get("item") or {}
        if event.get("type") == "item.completed" and item.get("type") == "agent_message":
            reply = str(item.get("text") or "")
        if event.get("type") == "turn.completed":
            usage = event.get("usage") or {}
        if event.get("type") in {"error", "turn.failed"}:
            return {"error": "Codex request failed"}
    return {"reply": reply, "usage": usage, "error": None if reply else "Codex returned no final message"}


def send(conversation_id: str, provider_id: str, model: str, text: str, project: str | None = None,
         home: Path | str | None = None, *, registry: Any = None, runner: Any = None, opener: Any = None,
         project_resolver: Any = None, context_builder: Any = None, bridge_factory: Any = None) -> dict:
    """Send one turn, enforcing privacy before context retrieval or any call."""
    home = window_home(home)
    result = {"reply": "", "error": None, "provider": provider_id, "model": model, "usage": {}}
    with _conversation_lock(str(_path(home, conversation_id))):
        target = _path(home, conversation_id)
        if not isinstance(text, str) or not text.strip():
            raise ValueError("text is required")
        entry = next((p for p in _entries(registry) if p["id"] == provider_id), None)
        if not entry or model not in entry.get("models", {}).values():
            return {**result, "error": "Unknown or disabled provider/model"}
        try:
            record = conversation(home, conversation_id)
        except KeyError:
            if target.exists():
                return {**result, "error": "Conversation is deleted or unreadable; start a new conversation"}
            record = {"id": conversation_id, "title": text.strip()[:80], "provider": provider_id,
                      "model": model, "project": project or None, "turns": []}
        if (record["provider"], record["model"], record["project"]) != (provider_id, model, project or None):
            return {**result, "error": "Start a new conversation to change provider, model or project"}
        sensitive = False
        if project:
            if project_resolver is None:
                from ..registry import get_project as project_resolver
            try:
                resolved = project_resolver(project)
            except (KeyError, OSError):
                return {**result, "error": "Unknown project"}
            if not resolved.get("path"):
                return {**result, "error": "Project has no local path"}
            sensitive = model_profile.is_sensitive({}, resolved["path"])
            if sensitive and model_profile.sensitive_problem(entry) is not None:
                return {**result, "error": "Sensitive project is not allowed on this provider"}
        options = entry.get("options") or {}
        if entry["adapter"] == "openai_api":
            url = endpoints.url(options.get("base_url") or "https://api.openai.com", "chat",
                                options.get("path_style", "auto"), options.get("paths"))
            if sensitive and model_profile.sensitive_problem({"adapter": "openai_api", "options": {"base_url": url}}) is not None:
                return {**result, "error": "Sensitive project is not allowed on this endpoint"}
        key = None
        try:
            system = (context_builder or _context)(text, project)
            turns = record["turns"][-(10 if entry["adapter"] == "codex_cli" else 20):]
            messages = ([{"role": "system", "content": system}] if system else [])
            messages += [{"role": t["role"], "content": t["text"]} for t in turns]
            messages.append({"role": "user", "content": text})
            if entry["adapter"] == "claude_code":
                bridge = (bridge_factory or model_bridge.ChatBridge)(home / "chats" / conversation_id,
                            runner=runner or subprocess.run, claude=entry.get("executable") or "claude", pending_home=home)
                reply = bridge.send(conversation_id, (system + "\n\n" if system else "") + text, model=model)
                result.update(reply=reply.get("reply", ""), usage=reply.get("usage") or {},
                              error="Claude request failed" if reply.get("error") else None)
            elif entry["adapter"] == "codex_cli":
                result.update(_codex(entry, model, messages, runner or subprocess.run, home))
            else:
                from ..orchestrator.adapters.http_api import OpenAiCompatibleAdapter

                adapter = OpenAiCompatibleAdapter(entry, opener=opener or urllib.request.build_opener(_NoRedirect()).open)
                key = adapter.key()
                if entry.get("options", {}).get("secret_ref") and not key:
                    return {**result, "error": "Provider secret is not configured"}
                if provider_id == "openrouter-free":
                    from ..orchestrator.free_dispatch import FreeInputs

                    with _QUOTA_LOCK:
                        governor = FreeInputs.load_default().governor
                        allowed, _reason = governor.can_spend(model)
                        if not allowed:
                            return {**result, "error": "Free quota unavailable"}
                        # Reserve before dispatch: concurrent requests cannot
                        # overspend the daily/minute allowance.
                        governor.record({"model": model, "outcome": "success", "lane": "chat"})
                payload = adapter._post(url, {"model": model, "messages": messages},
                                        {"authorization": f"Bearer {key}"} if key else {}, 600)
                reply, usage = adapter.parse(payload, model)
                result.update(reply=reply, usage=usage, error=None if reply else "Provider returned no message")
        except Exception:
            # Never return CLI stderr, HTTP bodies or exception text: they can
            # contain credentials or a complete private request.
            result.update(reply="", error="Provider request failed", usage={})
        if key:
            result = _redact(result, key)
        if result["error"]:
            result["reply"] = ""
            return result
        stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
        record["turns"] += [{"role": "user", "text": text, "at": stamp},
                            {"role": "assistant", "text": result["reply"], "at": stamp}]
        record["updated_at"] = stamp
        if key:
            record = _redact(record, key)
        _write_json(target, record)
    return result
