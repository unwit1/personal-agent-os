"""Loopback HTTP service for the Agent OS browser bridge."""

from __future__ import annotations

import hashlib
import json
import os
import secrets
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from .browser_bridge import BridgeStore
from .creator_profiles import follow_status as creator_follow_status
from .creator_profiles import upsert_creator_follow
from .paths import INDEX_DIR
from .watching import add_browser_follow


DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8766
TOKEN_PATH = INDEX_DIR / "browser-bridge.token"
MAX_BODY = 8 * 1024 * 1024


def load_or_create_token(path: Path = TOKEN_PATH) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        value = path.read_text(encoding="utf-8").strip()
        if value:
            return value
    value = secrets.token_urlsafe(32)
    path.write_text(value + "\n", encoding="utf-8")
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass
    return value


def make_handler(store: BridgeStore, token: str, allowed_hosts: set[str]):
    class Handler(BaseHTTPRequestHandler):
        server_version = "AgentOSBrowserBridge/1"

        def log_message(self, format: str, *args) -> None:
            return

        def _host_ok(self) -> bool:
            return (self.headers.get("Host") or "").casefold() in allowed_hosts

        def _authorized(self) -> bool:
            supplied = self.headers.get("X-Agent-OS-Token") or ""
            return secrets.compare_digest(supplied, token)

        def _send(self, status: int, payload) -> None:
            data = json.dumps(payload, ensure_ascii=False, default=str).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            if data:
                self.wfile.write(data)

        def do_GET(self) -> None:
            if not self._host_ok():
                self._send(HTTPStatus.FORBIDDEN, {"error": "unexpected host"})
                return
            parsed = urlparse(self.path)
            path = parsed.path
            if path == "/health":
                self._send(HTTPStatus.OK, {"ok": True, "service": "agent-os-browser-bridge"})
                return
            if not self._authorized():
                self._send(HTTPStatus.UNAUTHORIZED, {"error": "unauthorized"})
                return
            if path == "/api/v1/browser/stats":
                self._send(HTTPStatus.OK, store.stats())
                return
            if path == "/api/v1/browser/sessions":
                self._send(HTTPStatus.OK, {"sessions": store.list_sessions()})
                return
            if path == "/api/v1/browser/commands":
                query = parse_qs(parsed.query)
                session_id = str((query.get("session_id") or [""])[0]).strip()
                if not session_id:
                    self._send(HTTPStatus.BAD_REQUEST, {"error": "session_id is required"})
                    return
                self._send(
                    HTTPStatus.OK,
                    {
                        "schema": "agent-os/browser-command-batch/v1",
                        "commands": store.claim_commands(session_id),
                    },
                )
                return
            if path.startswith("/api/v1/browser/commands/"):
                command_id = path.rsplit("/", 1)[-1]
                try:
                    self._send(HTTPStatus.OK, store.command_status(command_id))
                except KeyError as exc:
                    self._send(HTTPStatus.NOT_FOUND, {"error": str(exc)})
                return
            self._send(HTTPStatus.NOT_FOUND, {"error": "not found"})

        def do_POST(self) -> None:
            if not self._host_ok():
                self._send(HTTPStatus.FORBIDDEN, {"error": "unexpected host"})
                return
            if not self._authorized():
                self._send(HTTPStatus.UNAUTHORIZED, {"error": "unauthorized"})
                return
            length = int(self.headers.get("Content-Length") or 0)
            if length < 0 or length > MAX_BODY:
                self._send(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, {"error": "request too large"})
                return
            try:
                body = json.loads(self.rfile.read(length) if length else b"{}")
                if not isinstance(body, dict):
                    raise ValueError("body must be an object")
                path = urlparse(self.path).path
                if path == "/api/v1/browser/batch":
                    events = body.get("events")
                    if not isinstance(events, list):
                        raise ValueError("events must be a list")
                    result = store.ingest(events)
                elif path in {"/api/v1/browser/session", "/api/v1/browser/session/heartbeat"}:
                    result = store.register_session(body)
                elif path == "/api/v1/browser/command-result":
                    command_id = str(body.get("command_id") or "").strip()
                    state = str(body.get("state") or "").strip()
                    result = store.complete_command(
                        command_id,
                        state=state,
                        result=body.get("result"),
                        error=str(body.get("error") or "") or None,
                    )
                elif path == "/api/v1/browser/follow/status":
                    result = {
                        "schema": "agent-os/follow-status/v1",
                        **creator_follow_status(body),
                    }
                elif path == "/api/v1/browser/capture":
                    capture = body
                    source_key = str(
                        capture.get("source_id")
                        or capture.get("canonical_url")
                        or capture.get("url")
                        or ""
                    )
                    identity = json.dumps(
                        [
                            capture.get("site"),
                            capture.get("content_type"),
                            source_key,
                        ],
                        ensure_ascii=False,
                        separators=(",", ":"),
                    )
                    event_id = "capture:" + hashlib.sha256(identity.encode("utf-8")).hexdigest()
                    result = store.ingest([{
                        "event_id": event_id,
                        "source": "browser-capture",
                        "event_type": str(capture.get("content_type") or "web_page"),
                        "source_key": source_key,
                        "occurred_at": capture.get("captured_at"),
                        "device": capture.get("device"),
                        "payload": capture,
                    }])
                    result["event_id"] = event_id
                    if event_id in result.get("duplicates", []):
                        result["status"] = "duplicate"
                    elif event_id in result.get("updated", []):
                        result["status"] = "updated"
                    else:
                        result["status"] = "stored"

                    metadata = dict(capture.get("metadata") or {})
                    if str(capture.get("intent") or "") == "follow":
                        watch = add_browser_follow(capture)
                        result["follow"] = {
                            "watch_id": watch.get("watch_id"),
                            "target_type": watch.get("kind"),
                        }

                        target_type = str(
                            metadata.get("follow_target_type")
                            or capture.get("content_type")
                            or ""
                        )
                        if target_type == "creator":
                            creator = upsert_creator_follow(
                                capture,
                                watch_id=watch.get("watch_id"),
                            )
                            aliases = [
                                str(alias.get("value") or "")
                                for alias in creator.get("aliases") or []
                                if str(alias.get("value") or "").strip()
                            ]
                            discord_matches = store.find_discord_author_matches(aliases)
                            if discord_matches:
                                creator = upsert_creator_follow(
                                    capture,
                                    watch_id=watch.get("watch_id"),
                                    discord_matches=discord_matches,
                                )

                            linked_capture = dict(capture)
                            linked_metadata = dict(metadata)
                            linked_metadata["creator_profile_id"] = creator.get("creator_id")
                            linked_metadata["creator_aliases"] = [
                                alias.get("value")
                                for alias in creator.get("aliases") or []
                                if alias.get("value")
                            ]
                            linked_capture["metadata"] = linked_metadata
                            watch = add_browser_follow(linked_capture)
                            result["follow"]["watch_id"] = watch.get("watch_id")
                            result["follow"]["creator"] = creator
                else:
                    self._send(HTTPStatus.NOT_FOUND, {"error": "not found"})
                    return
                self._send(HTTPStatus.OK, result)
            except ValueError as exc:
                self._send(HTTPStatus.BAD_REQUEST, {"error": str(exc)[:500]})
            except Exception as exc:
                self._send(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": str(exc)[:500]})

    return Handler


def build_server(
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    *,
    store: BridgeStore | None = None,
    token: str | None = None,
):
    if host not in {"127.0.0.1", "localhost", "::1"}:
        raise ValueError("browser bridge only binds to loopback")
    bridge_store = store or BridgeStore()
    bridge_token = token or load_or_create_token()
    server = ThreadingHTTPServer((host, port), make_handler(bridge_store, bridge_token, set()))
    actual = server.server_address[1]
    allowed = {f"{name}:{actual}".casefold() for name in ("127.0.0.1", "localhost", "[::1]")}
    server.RequestHandlerClass = make_handler(bridge_store, bridge_token, allowed)
    server.daemon_threads = True
    return server, bridge_token, bridge_store


def serve(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> int:
    server, token, store = build_server(host, port)
    actual = server.server_address[1]
    print(json.dumps({
        "service": "agent-os-browser-bridge",
        "endpoint": f"http://{host}:{actual}/api/v1/browser/batch",
        "capture_endpoint": f"http://{host}:{actual}/api/v1/browser/capture",
        "follow_status_endpoint": f"http://{host}:{actual}/api/v1/browser/follow/status",
        "session_endpoint": f"http://{host}:{actual}/api/v1/browser/session",
        "command_endpoint": f"http://{host}:{actual}/api/v1/browser/commands",
        "command_result_endpoint": f"http://{host}:{actual}/api/v1/browser/command-result",
        "token": token,
        "database": str(store.path),
    }), flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0
