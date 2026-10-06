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
from . import actions_openings, model_bridge
from .confirm import ItemState, PendingStore, window_home

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
                 gateway_factory: Any = None) -> None:
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
        if path == "/api/items":
            tab = (query.get("tab") or [None])[0] or None
            return self.registry.outstanding(tab, state=self.state)
        if path == "/api/actions":
            return {"actions": self.registry.actions()}
        if path == "/api/pending":
            return self._pending_view()
        raise KeyError(path)

    def post(self, path: str, body: dict[str, Any]) -> Any:
        if path == "/api/brain-dump":
            text = str(_first(body, "text", "message") or "").strip()
            if not text:
                raise ValueError("text is required")
            tab = body.get("tab") if body.get("tab") in ("work", "personal") else "work"
            from .brain_dump_store import BrainDumpStore

            store = BrainDumpStore(self.home)
            from agent_os.executive import brain_dump

            result = brain_dump.process(text, known_projects=_known_projects(), existing_ids=store.existing_ids())
            added = store.add(result, tab=tab)
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
                 gateway_factory: Any = None) -> tuple[ThreadingHTTPServer, str]:
    if host not in LOOPBACK_HOSTS:
        raise ValueError("the Executive window only binds to loopback")
    home_path = window_home(home)
    if registry is None:
        from .builtin import default_registry

        registry = default_registry()
    if bridge is None:
        bridge = model_bridge.ChatBridge(home_path)
    token = secrets.token_urlsafe(24)
    api = Api(registry, bridge, home_path, transport=transport, gateway_factory=gateway_factory)
    server = _bind_exclusive(host, port, make_handler(api, token, set()))
    actual = server.server_address[1]
    allowed = {f"{name}:{actual}".casefold() for name in ("127.0.0.1", "localhost", "[::1]")}
    server.RequestHandlerClass = make_handler(api, token, allowed)
    server.daemon_threads = True
    server.api = api  # type: ignore[attr-defined]
    server.token = token  # type: ignore[attr-defined]
    return server, token


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
