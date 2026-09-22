"""Local HTTP API + event stream for the control GUI.

The server is a thin client of ``service``/``engine``: every button in the GUI
maps to one engine call. It binds to loopback, checks the Host header against
DNS rebinding, and requires a per-process session token on every API call so
other web pages open in the same browser cannot drive a run.

Background driving is honest: a run is driven only by a thread in this server
process. The status payload reports whether that thread is alive; when the
process exits, nothing keeps working and the run resumes from persisted state
the next time anything drives it.
"""

from __future__ import annotations

import json
import secrets
import threading
import time
import webbrowser
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from ..paths import ROOT
from . import roadmap, service, simple


GUI_DIR = ROOT / "gui"
STATIC_TYPES = {".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8", ".css": "text/css; charset=utf-8", ".svg": "image/svg+xml"}
MAX_BODY = 1_000_000


class Drivers:
    """Per-run background driver threads owned by this server process."""

    def __init__(self) -> None:
        self._threads: dict[str, threading.Thread] = {}
        self._errors: dict[str, str] = {}
        self._lock = threading.Lock()

    def alive(self, run_id: str) -> bool:
        thread = self._threads.get(run_id)
        return bool(thread and thread.is_alive())

    def error(self, run_id: str) -> str | None:
        return self._errors.get(run_id)

    def ensure(self, run_id: str) -> bool:
        with self._lock:
            if self.alive(run_id):
                return False
            self._errors.pop(run_id, None)

            def drive() -> None:
                try:
                    service.engine().run_loop(run_id, owner="gui")
                except Exception as exc:  # surfaced in status, never swallowed
                    self._errors[run_id] = str(exc)[:400]

            thread = threading.Thread(target=drive, name=f"agent-os-driver-{run_id}", daemon=True)
            self._threads[run_id] = thread
            thread.start()
            return True


class Api:
    def __init__(self, drivers: Drivers, default_project: str | None = None, default_repository: str | None = None) -> None:
        self.drivers = drivers
        self.default_repository = default_repository
        self.campaigns = roadmap.CampaignThreads()
        self.preps: dict[str, roadmap.Preparation] = {}
        self.default_project = default_project
        self._providers_cache: tuple[float, list[dict[str, Any]]] | None = None

    def _status(self, run_id: str) -> dict[str, Any]:
        summary = service.status(run_id)
        summary["gui_driver"] = {"alive": self.drivers.alive(run_id), "error": self.drivers.error(run_id)}
        return summary

    def _redrive(self, run_id: str) -> None:
        """Keep a run moving after a control action: through its campaign when
        it is part of Auto Continue Until Done, otherwise on its own."""
        record = service.engine().load(run_id)
        origin = record.get("origin") or {}
        if origin.get("auto_until_done") and record.get("project"):
            self.campaigns.ensure(service.engine(), record["project"])
        else:
            self.drivers.ensure(run_id)

    def _stop_campaign(self, run_id: str) -> None:
        record = service.engine().load(run_id)
        if record.get("project"):
            self.campaigns.request_stop(record["project"])

    # -- Simple Mode ----------------------------------------------------------

    def _providers(self) -> list[dict[str, Any]]:
        """Probing CLIs takes a moment; the home screen reuses a result for a minute."""
        if self._providers_cache and time.monotonic() - self._providers_cache[0] < 60:
            return self._providers_cache[1]
        try:
            rows = [
                {"id": item["id"], "enabled": item.get("enabled", True), "probe": item.get("probe") or {}}
                for item in service.providers().get("providers", [])
            ]
        except Exception as exc:
            rows = [{"id": "unknown", "enabled": False, "probe": {"available": False, "reason": str(exc)[:200]}}]
        self._providers_cache = (time.monotonic(), rows)
        return rows

    def _project(self, query_or_body: dict[str, Any]) -> str | None:
        value = query_or_body.get("project")
        if isinstance(value, list):
            value = value[0] if value else None
        return value or self.default_project

    def _driving(self, run_id: str, project: str | None) -> bool:
        engine = service.engine()
        return self.drivers.alive(run_id) or (bool(project) and self.campaigns.alive(project)) or bool(engine.store.driver(run_id).get("active"))

    def _latest_prep(self, keys: set[str | None]) -> dict[str, Any] | None:
        mine = [prep for prep in self.preps.values() if getattr(prep, "project", None) in keys]
        return mine[-1].view() if mine else None

    def home(self, project: str | None) -> dict[str, Any]:
        engine = service.engine()
        overview = roadmap.overview(engine, project, None if project else self.default_repository)
        key = overview["project"] or overview["repository"]
        overview["providers"] = self._providers()
        run_id = None
        campaign = overview.get("campaign") or {}
        if campaign.get("current_run") and engine.store.exists(campaign["current_run"]):
            if not (engine.load(campaign["current_run"]).get("origin") or {}).get("abandoned"):
                run_id = campaign["current_run"]
        if run_id is None and overview["unfinished_runs"]:
            run_id = overview["unfinished_runs"][0]["run_id"]
        prep = self._latest_prep({overview["project"], overview["repository"], self.default_repository} - {None})
        view = self.simple(run_id, key, dirty=overview["dirty"], prep=prep) if run_id else None
        overview["current_run"] = view
        overview["prep"] = prep
        overview["campaign_driver"] = {"alive": self.campaigns.alive(key), "error": self.campaigns.errors.get(key)}
        overview["advice"] = simple.advise(overview, view, prep if prep and prep.get("state") == "running" else None)
        overview["projects"] = [item["id"] for item in _registered_projects()]
        return overview

    def simple(self, run_id: str, project: str | None = None, dirty: bool | None = None, prep: dict[str, Any] | None = None) -> dict[str, Any]:
        engine = service.engine()
        summary = self._status(run_id)
        key = project or summary.get("project")
        events, _ = engine.ledger.read(run_id)
        report = engine.efficiency(run_id)
        origin = summary.get("origin") or {}
        if prep is None or (prep.get("result") or {}).get("run_id") not in {None, run_id}:
            prep = self.preps[origin["prep"]].view() if origin.get("prep") in self.preps else None
        view = simple.run_view(summary, events, report, self._providers(), driving=self._driving(run_id, key), prep=prep, git_dirty=dirty)
        view["advice"] = simple.advise({"next_stage": None}, view)
        return view

    def start_continue(self, body: dict[str, Any]) -> dict[str, Any]:
        """Return at once; the preparation runs on a thread and reports each step."""
        engine = service.engine()
        project = self._project(body)
        prep = roadmap.Preparation()
        prep.project = project or body.get("repository") or self.default_repository  # type: ignore[attr-defined]
        self.preps[prep.id] = prep
        for stale in list(self.preps)[:-20]:
            del self.preps[stale]
        auto_until_done = bool(body.get("auto_until_done"))

        def work() -> None:
            result = roadmap.continue_roadmap(
                engine, project, body.get("repository") or (None if project else self.default_repository),
                auto_until_done=auto_until_done, preference=body.get("preference") or None,
                fresh=bool(body.get("fresh")), prep=prep,
            )
            if result["action"] in {"started", "resumed"}:
                if auto_until_done and project:
                    self.campaigns.ensure(engine, project)
                else:
                    self.drivers.ensure(result["run_id"])

        threading.Thread(target=work, name=f"agent-os-{prep.id}", daemon=True).start()
        return {"prep": prep.view()}

    def get(self, path: str, query: dict[str, list[str]]) -> Any:
        parts = [part for part in path.split("/") if part][1:]  # drop "api"
        if parts == ["home"]:
            return self.home(self._project(query))
        if len(parts) == 2 and parts[0] == "prep":
            prep = self.preps.get(parts[1])
            if prep is None:
                raise KeyError(parts[1])
            return prep.view()
        if len(parts) == 3 and parts[0] == "runs" and parts[2] == "simple":
            return self.simple(parts[1])
        if len(parts) == 3 and parts[0] == "runs" and parts[2] == "efficiency":
            return service.engine().efficiency(parts[1])
        if parts == ["providers"]:
            return service.providers()
        if parts == ["runs"]:
            return service.list_runs()
        if len(parts) == 2 and parts[0] == "runs":
            return self._status(parts[1])
        if len(parts) == 3 and parts[0] == "runs" and parts[2] == "events":
            return service.events(parts[1], int((query.get("after") or ["0"])[0]))
        if len(parts) == 3 and parts[0] == "runs" and parts[2] == "result":
            return service.result(parts[1])
        raise KeyError(path)

    def post(self, path: str, body: dict[str, Any]) -> Any:
        parts = [part for part in path.split("/") if part][1:]
        if parts == ["roadmap", "continue"]:
            return self.start_continue(body)
        if parts == ["providers", "suggest"]:
            return service.suggest_providers(write=bool(body.get("write")), force=bool(body.get("force")))
        if parts == ["runs"]:
            recommended = bool(body.get("start_recommended"))
            auto = bool(body.get("auto_continue", recommended))
            policy = dict(body.get("policy") or {})
            validators = [line.strip() for line in str(body.get("validators") or "").splitlines() if line.strip()]
            if validators:
                policy["default_validators"] = [{"kind": "command", "command": command} for command in validators]
            if body.get("preference"):
                policy["preference"] = body["preference"]
            policy["auto_continue"] = auto
            summary = service.create(
                str(body.get("goal") or ""),
                repository=body.get("repository") or None,
                project=body.get("project") or None,
                tasks=body.get("tasks") or None,
                policy=policy,
                overrides=body.get("overrides") or None,
                start=recommended,
                auto_continue=auto if recommended else None,
                background=False,  # this server drives its runs on its own threads
            )
            if recommended:
                self.drivers.ensure(summary["run_id"])
            return self._status(summary["run_id"])
        if len(parts) == 3 and parts[0] == "runs":
            run_id, action = parts[1], parts[2]
            engine = service.engine()
            if action == "start":
                engine.start(run_id, body.get("auto_continue"))
                self._redrive(run_id)
            elif action == "drive":
                self._redrive(run_id)
            elif action == "step":
                engine.step(run_id)
            elif action == "pause":
                self._stop_campaign(run_id)
                engine.pause(run_id)
            elif action == "resume":
                engine.resume(run_id)
                self._redrive(run_id)
            elif action == "stop":
                self._stop_campaign(run_id)
                engine.stop(run_id)
            elif action == "fresh":
                record = engine.load(run_id)
                roadmap._abandon(engine, run_id, "set aside by user (Start Fresh)")
                return self.start_continue({"project": record.get("project"), "auto_until_done": (record.get("origin") or {}).get("auto_until_done")})
            elif action == "auto-continue":
                engine.set_auto_continue(run_id, bool(body.get("enabled")))
                if body.get("enabled"):
                    self._redrive(run_id)
            elif action == "decide":
                engine.decide(run_id, str(body["gate_id"]), bool(body.get("approve")), body.get("note"))
                self._redrive(run_id)
            elif action == "retry":
                engine.retry(run_id, str(body["node_id"]))
                self._redrive(run_id)
            elif action == "reassign":
                engine.reassign(run_id, str(body["node_id"]), str(body["provider"]), body.get("model") or None, body.get("effort") or None)
                self._redrive(run_id)
            elif action == "review-again":
                engine.review_again(run_id, str(body["node_id"]))
                self._redrive(run_id)
            elif action == "override":
                engine.set_override(
                    run_id,
                    provider=body.get("provider") or None,
                    model=body.get("model") or None,
                    effort=body.get("effort") or None,
                    role=body.get("role") or None,
                    node=body.get("node") or None,
                    clear=bool(body.get("clear")),
                )
            else:
                raise KeyError(action)
            return self._status(run_id)
        raise KeyError(path)


def make_handler(api: Api, token: str, allowed_hosts: set[str]):
    class Handler(BaseHTTPRequestHandler):
        server_version = "AgentOSOrchestrator/1"

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

        def _authorized(self, query: dict[str, list[str]]) -> bool:
            supplied = self.headers.get("X-Agent-OS-Token") or (query.get("token") or [""])[0]
            return secrets.compare_digest(supplied, token)

        def do_GET(self) -> None:
            if not self._host_ok():
                self._send(HTTPStatus.FORBIDDEN, {"error": "unexpected Host header"})
                return
            url = urlparse(self.path)
            query = parse_qs(url.query)
            if not url.path.startswith("/api/"):
                self._static(url.path)
                return
            if not self._authorized(query):
                self._send(HTTPStatus.UNAUTHORIZED, {"error": "missing or invalid session token"})
                return
            if url.path.endswith("/stream"):
                self._stream(url.path.split("/")[3])
                return
            try:
                self._send(HTTPStatus.OK, api.get(url.path, query))
            except KeyError as exc:
                self._send(HTTPStatus.NOT_FOUND, {"error": f"not found: {exc}"})
            except Exception as exc:
                self._send(HTTPStatus.BAD_REQUEST, {"error": str(exc)[:600]})

        def do_POST(self) -> None:
            if not self._host_ok():
                self._send(HTTPStatus.FORBIDDEN, {"error": "unexpected Host header"})
                return
            url = urlparse(self.path)
            length = int(self.headers.get("Content-Length") or 0)
            if length > MAX_BODY:
                self.close_connection = True
                self._send(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, {"error": "request too large"})
                return
            raw = self.rfile.read(length) if length else b""
            # Token only from the header for writes: a cross-site form cannot set it.
            if not self.headers.get("X-Agent-OS-Token") or not self._authorized({}):
                self._send(HTTPStatus.UNAUTHORIZED, {"error": "missing or invalid session token"})
                return
            try:
                body = json.loads(raw or b"{}")
                if not isinstance(body, dict):
                    raise ValueError("request body must be a JSON object")
                self._send(HTTPStatus.OK, api.post(url.path, body))
            except KeyError as exc:
                self._send(HTTPStatus.NOT_FOUND, {"error": f"not found: {exc}"})
            except Exception as exc:
                self._send(HTTPStatus.BAD_REQUEST, {"error": str(exc)[:600]})

        def _static(self, path: str) -> None:
            name = "index.html" if path in {"", "/"} else path.lstrip("/")
            target = (GUI_DIR / name).resolve()
            if GUI_DIR.resolve() not in target.parents or not target.is_file() or target.suffix not in STATIC_TYPES:
                self._send(HTTPStatus.NOT_FOUND, {"error": "not found"})
                return
            data = target.read_bytes()
            if target.name == "index.html":
                data = data.replace(b"__AGENT_OS_TOKEN__", token.encode("ascii"))
            self._send(HTTPStatus.OK, data, STATIC_TYPES[target.suffix])

        def _stream(self, run_id: str) -> None:
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            last_seq = 0
            last_state = None
            try:
                for _ in range(3600):
                    events = service.events(run_id, last_seq)
                    if events:
                        last_seq = int(events[-1]["seq"])
                        self.wfile.write(f"event: events\ndata: {json.dumps(events, default=str)}\n\n".encode("utf-8"))
                    status = api._status(run_id)
                    fingerprint = (status["state"], status["updated_at"] if "updated_at" in status else None, json.dumps(status["progress"]), last_seq)
                    if fingerprint != last_state:
                        last_state = fingerprint
                        self.wfile.write(f"event: status\ndata: {json.dumps(status, default=str)}\n\n".encode("utf-8"))
                    else:
                        self.wfile.write(b": keep-alive\n\n")
                    self.wfile.flush()
                    time.sleep(1.0)
            except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError, OSError):
                return
            except Exception as exc:  # the run vanished or could not be read
                try:
                    self.wfile.write(f"event: error\ndata: {json.dumps(str(exc)[:200])}\n\n".encode("utf-8"))
                except OSError:
                    pass

    return Handler


def _registered_projects() -> list[dict[str, Any]]:
    try:
        from ..registry import projects

        return projects()
    except Exception:
        return []


def _default_project() -> str | None:
    """The project this checkout belongs to, else the first registered one."""
    try:
        from ..registry import identify_project

        found = identify_project(Path.cwd())
        if found:
            return found["id"]
    except Exception:
        pass
    registered = _registered_projects()
    return registered[0]["id"] if registered else None


def build_server(host: str = "127.0.0.1", port: int = 8765, project: str | None = None, repository: str | None = None) -> tuple[ThreadingHTTPServer, str]:
    if host not in {"127.0.0.1", "localhost", "::1"}:
        raise ValueError("the control GUI only binds to loopback")
    token = secrets.token_urlsafe(24)
    drivers = Drivers()
    api = Api(drivers, project or (None if repository else _default_project()), repository)
    server = ThreadingHTTPServer((host, port), make_handler(api, token, set()))
    actual = server.server_address[1]
    allowed = {f"{name}:{actual}".casefold() for name in ("127.0.0.1", "localhost", "[::1]")}
    server.RequestHandlerClass = make_handler(api, token, allowed)
    server.daemon_threads = True
    server.drivers = drivers  # type: ignore[attr-defined]
    server.api = api  # type: ignore[attr-defined]
    return server, token


def serve(host: str = "127.0.0.1", port: int = 8765, open_browser: bool = True, project: str | None = None, repository: str | None = None) -> int:
    server, token = build_server(host, port, project, repository)
    url = f"http://{host}:{server.server_address[1]}/"
    print(json.dumps({"gui": url, "note": "runs are driven only while this process is running; Ctrl+C stops driving (state is kept)"}), flush=True)
    if open_browser:
        threading.Timer(0.5, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0
