"""Local HTTP server for the Executive window.

Modelled on the orchestrator control GUI server: it binds to loopback only,
checks the Host header against DNS rebinding, and requires a per-process
session token (header ``X-Agent-OS-Token``, injected into the served HTML) on
every POST. Consequential actions only ever execute through ``/api/confirm``,
which redeems a one-time confirm token created when the preview was made.
"""

from __future__ import annotations

import json
import os
import secrets
import shutil
import subprocess
import threading
import webbrowser
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from ...paths import ROOT
from ...orchestrator import cloud_lane, plan_extras, usage_hub
from .. import chat_hub, projects_view
from ..keep_awake import KeepAwake
from . import actions_openings, model_bridge
from .confirm import ItemState, PendingStore, _write_json, window_home
from .rescue_view import rescue_view

GUI_DIR = ROOT / "gui"
STATIC_FILES = {
    "/": ("executive.html", "text/html; charset=utf-8"),
    "/executive.html": ("executive.html", "text/html; charset=utf-8"),
    "/executive.js": ("executive.js", "text/javascript; charset=utf-8"),
    "/style.css": ("style.css", "text/css; charset=utf-8"),
}
TOKEN_PLACEHOLDERS = (b"{{TOKEN}}", b"__AGENT_OS_TOKEN__")
LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1"}
MAX_BODY = 1_000_000


def _first(body: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = body.get(key)
        if value not in (None, ""):
            return value
    return None


def _known_projects() -> list[dict]:
    from agent_os.registry import canonical_projects

    return [{"id": p.get("id"), "aliases": p.get("aliases", [])} for p in canonical_projects()]


class Api:
    def __init__(self, registry: Any, bridge: Any, home: Path, transport: Any = None,
                 gateway_factory: Any = None, *, orchestrator_url: str | None = None,
                 remote_hosts: tuple[str, ...] = (), wake: Any = None,
                 usage_home: Path | None = None) -> None:
        self.registry = registry
        if transport is None:
            from .transport import default_transport

            transport = default_transport()
        if gateway_factory is None:
            from .actions_executive import _default_gateway as gateway_factory
        self.transport = transport
        self.gateway_factory = gateway_factory
        self.bridge = bridge
        self.home = home
        self.pending = PendingStore(home)
        self.state = ItemState(home)
        self.orchestrator_url = orchestrator_url
        self.remote_hosts = list(remote_hosts)
        self.usage_home = usage_home if usage_home is not None else usage_hub._home()
        try:
            config = json.loads((home / "config.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            config = {}
        enabled = config.get("keep_awake", True) is True if isinstance(config, dict) else True
        self.wake = wake or KeepAwake(enabled=enabled)

    # -- helpers --------------------------------------------------------------

    def _item(self, item_id: Any) -> dict[str, Any]:
        if not item_id:
            raise ValueError("item_id is required")
        for item in self.registry.outstanding().get("items", []):
            if str(item.get("id")) == str(item_id):
                return item
        raise KeyError(f"unknown item: {item_id}")

    def _action(self, action_id: Any) -> dict[str, Any]:
        for action in self.registry.actions():
            if action.get("id") == action_id:
                return action
        raise KeyError(f"unknown action: {action_id}")

    def _previews(self) -> list[dict[str, Any]]:
        out = []
        for record in self.pending.list():
            item = record.get("item") or {}
            out.append({
                "id": record["token"],
                "confirm_token": record["token"],
                "action_id": record.get("action_id"),
                "item_id": item.get("id"),
                "title": f"{record.get('action_id')}: {item.get('title') or item.get('id') or ''}",
                "content": json.dumps(record.get("preview"), indent=2, default=str, ensure_ascii=False),
                "created_at": record.get("created_at"),
            })
        return out

    def _pending_view(self) -> dict[str, Any]:
        return {"pending": self.pending.list(), "previews": self._previews()}

    def _model(self, conversation_id: Any, text: str) -> dict[str, Any]:
        with self.wake.request():
            result = dict(self.bridge.send(str(conversation_id or "default"), text) or {})
        result["message"] = result.get("reply") or result.get("error") or ""
        result["previews"] = self._previews()
        return result

    def _opening_event(self, event: dict[str, Any]) -> dict[str, Any]:
        """Preview a chat-stated opening event; it only applies through /api/confirm."""
        item = {"id": f"county:{event['county']}", "kind": "county_openings"}
        try:
            self.registry.invoke("openings.event", item, dict(event), self.pending)
        except Exception as exc:
            return {"message": f"Could not preview the openings change: {type(exc).__name__}: {exc}"[:600],
                    "previews": self._previews(), "opening_event": event}
        return {"message": "Confirm to update openings", "previews": self._previews(), "opening_event": event}

    # -- routes ---------------------------------------------------------------

    def get(self, path: str, query: dict[str, list[str]]) -> Any:
        if path == "/api/usage":
            return usage_hub.summary(home=self.usage_home)
        if path == "/api/chat/providers":
            return chat_hub.providers()
        if path == "/api/chat/conversations":
            return chat_hub.conversations(self.home)
        if path == "/api/chat/conversation":
            return chat_hub.conversation(self.home, (query.get("id") or [""])[0])
        if path == "/api/projects":
            return projects_view.projects(state_home=self.usage_home)
        if path == "/api/config":
            return {"orchestrator_url": self.orchestrator_url, "keep_awake": self.wake.enabled,
                    "remote_hosts": self.remote_hosts}
        if path == "/api/items":
            tab = (query.get("tab") or [None])[0] or None
            return self.registry.outstanding(tab, state=self.state)
        if path == "/api/actions":
            return {"actions": self.registry.actions()}
        if path == "/api/pending":
            return self._pending_view()
        if path == "/api/rescue":
            tab = (query.get("tab") or [None])[0] or None
            if tab is not None and tab not in ("work", "personal"):
                raise ValueError("tab must be work or personal")
            try:
                horizon_days = int((query.get("horizon_days") or ["1"])[0])
            except ValueError:
                raise ValueError("horizon_days must be an integer") from None
            return rescue_view(self.registry, tab, state=self.state, horizon_days=horizon_days)
        raise KeyError(path)

    def post(self, path: str, body: dict[str, Any]) -> Any:
        if path == "/api/config":
            enabled = body.get("keep_awake")
            if not isinstance(enabled, bool):
                raise ValueError("keep_awake must be a boolean")
            _write_json(self.home / "config.json", {"keep_awake": enabled})
            self.wake.configure(enabled)
            return self.get(path, {})
        if path == "/api/extras":
            return plan_extras.set_status(self.usage_home, str(body.get("id") or ""), str(body.get("status") or ""))
        if path == "/api/open-url":
            value = body.get("url")
            if not isinstance(value, str) or any(ord(c) <= 32 for c in value) or "\\" in value:
                raise ValueError("invalid URL")
            url = urlparse(value)
            if (url.scheme != "https" or url.hostname not in {"claude.ai", "chatgpt.com", "nano-gpt.com", "openrouter.ai", "github.com"}
                    or url.username is not None or url.password is not None or url.port not in (None, 443)):
                raise ValueError("URL is not an allowed HTTPS vendor URL")
            return {"opened": bool(webbrowser.open(value))}
        if path == "/api/chat/send":
            with self.wake.request():
                result = chat_hub.send(str(body.get("conversation_id") or ""), str(body.get("provider") or body.get("provider_id") or ""),
                                       str(body.get("model") or ""), body.get("text"), project=body.get("project") or None, home=self.home)
            return {**result, "previews": self._previews()}
        if path == "/api/chat/delete":
            return chat_hub.delete(self.home, str(body.get("id") or body.get("conversation_id") or ""))
        if path == "/api/projects/resume":
            project = str(body.get("project") or "")
            repo = projects_view.project_path(project)
            kind = str(body.get("kind") or "")
            sid = str(body.get("session_id") or "")
            # Only allow sessions actually associated with the selected checkout.
            row = next((p for p in projects_view.projects(state_home=self.usage_home) if p["id"] == project), None)
            field = {"claude": "claude_sessions", "codex": "codex_sessions", "cloud": "cloud_sessions"}.get(kind)
            if not row or not field or not any(s.get("id", s.get("session_id")) == sid for s in row[field]):
                raise ValueError("session does not belong to this project")
            return projects_view.resume_command(kind, sid, repo)
        if path == "/api/cloud/preview":
            project = str(body.get("project") or "")
            task = str(body.get("task") or "").strip()
            if not task:
                raise ValueError("task is required")
            repo = projects_view.project_path(project)
            from ...orchestrator.model_profile import is_sensitive

            if is_sensitive({}, str(repo), self.usage_home):
                raise ValueError("sensitive projects cannot use cloud sessions")
            info = cloud_lane.preflight(repo)
            preview = {**info, "project": project, "task": task}
            token = self.pending.create("command-center.cloud", {"id": project, "title": project},
                                        {"project": project, "repo": str(repo), "task": task, "branch": info.get("branch")}, preview)
            return {"status": "needs_confirmation", "preview": preview, "confirm_token": token}
        if path == "/api/brain-dump":
            text = str(_first(body, "text", "message") or "").strip()
            if not text:
                raise ValueError("text is required")
            from .brain_dump_store import BrainDumpStore
            from agent_os.executive import brain_dump

            store = BrainDumpStore(self.home)
            result = brain_dump.process(text, known_projects=_known_projects(), existing_ids=store.existing_ids())
            added = store.add(result, tab=body.get("tab"))  # the store falls back to "work"
            return {**result, "added": added, "refresh": True,
                    "message": f"Captured {len(added)} item(s); {len(result['clarifications'])} need a project; {len(result['duplicates'])} duplicate(s)."}
        if path == "/api/pending":
            return self._pending_view()
        if path == "/api/act":
            item = self._item(body.get("item_id"))
            params = body.get("params") or {}
            if not isinstance(params, dict):
                raise ValueError("params must be an object")
            return self.registry.invoke(str(body.get("action_id") or ""), item, params, self.pending)
        if path == "/api/confirm":
            token = _first(body, "confirm_token", "preview_id", "token")
            if not token:
                raise ValueError("confirm_token is required")
            record = next((r for r in self.pending.list() if r["token"] == str(token)), None)
            if record and record["action_id"] == "command-center.cloud":
                record = self.pending.take(str(token))
                params = record["params"]
                repo = projects_view.project_path(params["project"])
                from ...orchestrator.model_profile import is_sensitive

                if str(repo) != params["repo"] or is_sensitive({}, str(repo), self.usage_home):
                    raise ValueError("project path or privacy policy changed; make a new preview")
                info = cloud_lane.preflight(repo)
                if info.get("branch") != params.get("branch"):
                    raise ValueError("project branch changed; make a new preview")
                with self.wake.request():
                    try:
                        result = cloud_lane.submit(repo, params["task"], home=self.usage_home)
                    except cloud_lane.CloudLaneError as exc:
                        # The lane's own messages (untrusted folder, dirty tree, no link) carry no secrets.
                        self.pending.audit({"action_id": "command-center.cloud", "item_id": params["project"], "status": "failed"})
                        raise ValueError(f"cloud submission failed: {exc}") from None
                    except Exception:
                        self.pending.audit({"action_id": "command-center.cloud", "item_id": params["project"], "status": "failed"})
                        raise ValueError("cloud submission failed") from None
                self.pending.audit({"action_id": "command-center.cloud", "item_id": params["project"],
                                    "session_id": result.get("session_id"), "status": "done"})
            else:
                result = self.registry.confirm(str(token), self.pending)
            return {"status": "done", "result": result, "message": "Done."}
        if path == "/api/dismiss":
            return self.dismiss(body)
        if path == "/api/chat":
            text = str(_first(body, "text", "message") or "").strip()
            if not text:
                raise ValueError("text is required")
            event = actions_openings.parse_opening_event(text)
            if event is not None:
                return self._opening_event(event)
            return self._model(body.get("conversation_id"), text)
        if path == "/api/send":
            return self.send(body)
        if path == "/api/option":
            item = self._item(body.get("item_id"))
            action = self._action(body.get("action_id"))
            build = getattr(self.bridge, "option_prompt", None) or model_bridge.option_prompt
            return self._model(body.get("conversation_id"), build(item, action))
        raise KeyError(path)

    def send(self, body: dict[str, Any]) -> dict[str, Any]:
        """Send the composed email through the transport; only reachable via the Send click."""
        to = str(body.get("to") or "").strip()
        subject = str(body.get("subject") or "").strip()
        text = str(body.get("body") or "")
        kind = str(body.get("kind") or "").strip()
        ref = str(body.get("applicant_ref") or "").strip() or None
        if not to:
            raise ValueError("To is required")
        if not subject:
            raise ValueError("Subject is required")
        if not text.strip():
            raise ValueError("Body is required")
        if not kind:
            raise ValueError("kind is required")
        result = self.transport.send(to, subject, text, from_account=body.get("from_account") or None,
                                     in_reply_to=body.get("in_reply_to") or None)
        sent = bool(getattr(result, "sent", False))
        error = getattr(result, "error", None)
        warning = getattr(result, "warning", None)
        event: dict[str, Any] = {"to": to, "subject": subject, "kind": kind, "applicant_ref": ref,
                                 "county": body.get("county") or None, "sent": sent}
        if not sent:
            error = str(error or "NOT SENT")
            if not error.startswith("NOT SENT"):
                error = f"NOT SENT: {error}"
            event["error"] = error
            self.pending.audit({"send": event})
            return {"sent": False, "error": error}
        out: dict[str, Any] = {"sent": True, "message_id": getattr(result, "message_id", None)}
        if warning:
            out["warning"] = warning
            event["warning"] = warning
        if ref:
            try:
                self.gateway_factory().record_applicant_sent(ref, kind, to, subject)
                out["status_recorded"] = True
            except Exception as exc:
                out["status_recorded"] = False
                out["error"] = f"Sent, but the applicant status was not updated: {type(exc).__name__}: {exc}"[:600]
            event["status_recorded"] = out["status_recorded"]
        self.pending.audit({"send": event})
        return out

    def dismiss(self, body: dict[str, Any]) -> dict[str, Any]:
        """Decline pending previews (by token, else every preview for item_id) without executing."""
        token = _first(body, "confirm_token", "preview_id", "token")
        if token:
            tokens = [str(token)]
        else:
            item_id = body.get("item_id")
            if not item_id:
                raise ValueError("confirm_token or item_id is required")
            tokens = [r["token"] for r in self.pending.list() if str((r.get("item") or {}).get("id")) == str(item_id)]
        declined = []
        for value in tokens:
            record = self.pending.take(value)
            item = record.get("item") or {}
            self.pending.audit({
                "action_id": record.get("action_id"),
                "item_id": item.get("id"),
                "params": record.get("params") or {},
                "declined": True,
            })
            declined.append(value)
        return {"status": "declined", "declined": declined}


def make_handler(api: Api, token: str, allowed_hosts: set[str]):
    class Handler(BaseHTTPRequestHandler):
        server_version = "AgentOSExecutive/1"

        def log_message(self, format: str, *args: Any) -> None:  # quiet by default
            return

        def _host_ok(self) -> bool:
            return (self.headers.get("Host") or "").casefold() in allowed_hosts

        def _send(self, status: int, payload: Any, content_type: str = "application/json; charset=utf-8") -> None:
            data = payload if isinstance(payload, bytes) else json.dumps(payload, default=str, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            self.end_headers()
            self.wfile.write(data)

        def _authorized(self) -> bool:
            supplied = self.headers.get("X-Agent-OS-Token") or ""
            return bool(supplied) and secrets.compare_digest(supplied, token)

        def _call(self, fn, *args: Any) -> None:
            try:
                self._send(HTTPStatus.OK, fn(*args))
            except KeyError as exc:
                self._send(HTTPStatus.NOT_FOUND, {"error": f"not found: {exc}"})
            except Exception as exc:
                self._send(HTTPStatus.BAD_REQUEST, {"error": f"{type(exc).__name__}: {exc}"[:600]})

        def do_GET(self) -> None:
            if not self._host_ok():
                self._send(HTTPStatus.FORBIDDEN, {"error": "unexpected Host header"})
                return
            url = urlparse(self.path)
            if not url.path.startswith("/api/"):
                self._static(url.path)
                return
            self._call(api.get, url.path, parse_qs(url.query))

        def do_POST(self) -> None:
            url = urlparse(self.path)
            length = int(self.headers.get("Content-Length") or 0)
            if length > MAX_BODY:
                self.close_connection = True
                self._send(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, {"error": "request too large"})
                return
            # Read the body before any rejection: replying and closing with unread
            # request bytes lets Windows reset the connection, so the client sees
            # an error instead of the 403.
            raw = self.rfile.read(length) if length else b""
            if not self._host_ok():
                self._send(HTTPStatus.FORBIDDEN, {"error": "unexpected Host header"})
                return
            # Token only from the header for writes: a cross-site form cannot set it.
            if not self._authorized():
                self._send(HTTPStatus.FORBIDDEN, {"error": "missing or invalid session token"})
                return
            try:
                body = json.loads(raw or b"{}")
                if not isinstance(body, dict):
                    raise ValueError("request body must be a JSON object")
            except ValueError as exc:
                self._send(HTTPStatus.BAD_REQUEST, {"error": str(exc)[:600]})
                return
            self._call(api.post, url.path, body)

        def _static(self, path: str) -> None:
            entry = STATIC_FILES.get(path)
            target = GUI_DIR / entry[0] if entry else None
            if target is None or not target.is_file():
                self._send(HTTPStatus.NOT_FOUND, {"error": "not found"})
                return
            data = target.read_bytes()
            if target.suffix == ".html":
                for placeholder in TOKEN_PLACEHOLDERS:
                    data = data.replace(placeholder, token.encode("ascii"))
            self._send(HTTPStatus.OK, data, entry[1])

    return Handler


class _ExclusiveServer(ThreadingHTTPServer):
    """Never share a port. ThreadingHTTPServer sets allow_reuse_address, which
    on Windows lets a second process bind a port already in use, so requests
    silently reached another app (an older prototype on 8770) and the window
    rendered empty. Bind exclusively instead."""

    allow_reuse_address = False

    def server_bind(self) -> None:
        import socket

        if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        super().server_bind()


def _bind_exclusive(host: str, port: int, handler: Any, attempts: int = 20) -> ThreadingHTTPServer:
    """Bind ``port``; if another program holds it, use the next free port."""
    last: OSError | None = None
    for candidate in ([port] if port == 0 else range(port, port + attempts)):
        try:
            return _ExclusiveServer((host, candidate), handler)
        except OSError as exc:
            last = exc
    raise OSError(f"no free port in {port}-{port + attempts - 1}: {last}")


def build_server(host: str = "127.0.0.1", port: int = 0, registry: Any = None, bridge: Any = None,
                 home: Path | str | None = None, transport: Any = None,
                 gateway_factory: Any = None, *, orchestrator_url: str | None = None,
                 remote_hosts: tuple[str, ...] = (), wake: Any = None,
                 usage_home: Path | None = None) -> tuple[ThreadingHTTPServer, str]:
    if host not in LOOPBACK_HOSTS:
        raise ValueError("the Executive window only binds to loopback")
    home_path = window_home(home)
    if registry is None:
        from .builtin import default_registry

        registry = default_registry()
    if bridge is None:
        bridge = model_bridge.ChatBridge(home_path)
    token = secrets.token_urlsafe(24)
    remote_hosts = tuple(_remote_host(value) for value in remote_hosts)
    api = Api(registry, bridge, home_path, transport=transport, gateway_factory=gateway_factory,
              orchestrator_url=orchestrator_url, remote_hosts=remote_hosts, wake=wake, usage_home=usage_home)
    server = _bind_exclusive(host, port, make_handler(api, token, set()))
    actual = server.server_address[1]
    allowed = {f"{name}:{actual}".casefold() for name in ("127.0.0.1", "localhost", "[::1]")}
    allowed.update(remote_hosts)
    server.RequestHandlerClass = make_handler(api, token, allowed)
    server.daemon_threads = True
    server.api = api  # type: ignore[attr-defined]
    server.token = token  # type: ignore[attr-defined]
    return server, token


def _remote_host(value: str) -> str:
    """An exact Host authority, never a URL, wildcard, credential or path."""
    if not isinstance(value, str) or not value or any(c.isspace() for c in value) or any(c in value for c in "/\\@?#*"):
        raise ValueError("remote host must be host[:port]")
    parsed = urlparse("//" + value)
    if not parsed.hostname or parsed.port is not None and not 0 < parsed.port <= 65535:
        raise ValueError("invalid remote host")
    return value.casefold()


def _find_edge() -> str | None:
    found = shutil.which("msedge")
    if found:
        return found
    for base in (os.environ.get("ProgramFiles(x86)"), os.environ.get("ProgramFiles"), os.environ.get("LOCALAPPDATA")):
        if base:
            candidate = Path(base) / "Microsoft" / "Edge" / "Application" / "msedge.exe"
            if candidate.is_file():
                return str(candidate)
    return None


def open_app_window(url: str) -> None:
    edge = _find_edge()
    if edge:
        try:
            subprocess.Popen([edge, f"--app={url}"])
            return
        except OSError:
            pass
    webbrowser.open(url)


def serve(port: int = 0, open_window: bool = True, host: str = "127.0.0.1", home: Path | str | None = None) -> int:
    server, _token = build_server(host, port, home=home)
    url = f"http://{host}:{server.server_address[1]}/"
    print(json.dumps({"executive_window": url, "note": "Ctrl+C closes the server"}), flush=True)
    if open_window:
        threading.Timer(0.5, lambda: open_app_window(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


def _runs_active() -> bool:
    from ...orchestrator import service

    return any(run.get("state") in {"PLANNING", "RUNNING", "VALIDATING", "REVIEWING", "INTEGRATING"}
               for run in service.list_runs())


def serve_app(port: int = 0, open_window: bool = True, remote_hosts: tuple[str, ...] = (),
              home: Path | str | None = None, *, orchestrator_builder: Any = None,
              executive_builder: Any = None, opener: Any = None, active: Any = None) -> int:
    """Serve the existing control GUI alongside the Executive in one process."""
    from ...orchestrator import server as control_server

    control, _ = (orchestrator_builder or control_server.build_server)(host="127.0.0.1", port=0)
    executive = None
    stop = threading.Event()
    threads: list[threading.Thread] = []
    try:
        orchestrator_url = f"http://127.0.0.1:{control.server_address[1]}/"
        executive, _ = (executive_builder or build_server)(port=port, home=home,
                         orchestrator_url=orchestrator_url, remote_hosts=tuple(remote_hosts))
        control.api.start_model_checks()
        try:
            from ...orchestrator import foreman_deploy

            foreman_deploy.manager().resume()
        except Exception:
            print(json.dumps({"foreman_resume_error": "Foreman could not resume; inspect it in Runs"}), flush=True)
        worker = threading.Thread(target=control.serve_forever, name="agent-os-control", daemon=True)
        worker.start()
        threads.append(worker)
        monitor = threading.Thread(target=executive.api.wake.monitor, args=(stop, active or _runs_active),
                                   name="agent-os-keep-awake", daemon=True)
        monitor.start()
        threads.append(monitor)
        url = f"http://127.0.0.1:{executive.server_address[1]}/"
        print(json.dumps({"app": url, "orchestrator": orchestrator_url, "note": "Ctrl+C closes the app servers"}), flush=True)
        if open_window:
            (opener or open_app_window)(url)
        try:
            executive.serve_forever()
        except KeyboardInterrupt:
            pass
    finally:
        stop.set()
        if threads:
            control.shutdown()
        control.server_close()
        if executive is not None:
            executive.server_close()
        for thread in threads:
            thread.join(timeout=5)
    return 0
