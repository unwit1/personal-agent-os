"""The narrow contract every coding-agent adapter implements.

The scheduler speaks only in ``AgentLaunchRequest`` (structured intent) and
``AgentResult`` (structured outcome). Command lines, flags, output formats, and
failure strings are an adapter's private business.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Protocol

from ...timestamps import utc_now_iso
from ..store import pid_alive, redact


RESULT_FENCE = "agent-os-result"
_RESULT_BLOCK = re.compile(r"```" + RESULT_FENCE + r"\s*(\{.*?\})\s*```", re.DOTALL)
_JSON_BLOCK = re.compile(r"```json\s*(\{.*?\})\s*```", re.DOTALL)

QUOTA_PATTERN = re.compile(
    r"(rate[ _-]?limit|usage limit|quota|too many requests|\b429\b|credit balance|"
    r"session limit|limit reached|out of credits|insufficient[_ ]quota|overloaded)",
    re.IGNORECASE,
)
INVALID_MODEL_PATTERN = re.compile(
    r"(invalid model|unknown model|model[^\n]{0,60}(not found|does not exist|not supported|unavailable|not available))",
    re.IGNORECASE,
)

# Variables a CLI needs to find its own configuration and credentials store.
# Anything else in the parent environment is withheld unless the provider
# registry allows it explicitly.
SYSTEM_ENV_ALLOWLIST = (
    "PATH", "PATHEXT", "SYSTEMROOT", "SYSTEMDRIVE", "WINDIR", "COMSPEC", "OS",
    "HOME", "USERPROFILE", "HOMEDRIVE", "HOMEPATH", "USERNAME", "USER", "LOGNAME",
    "APPDATA", "LOCALAPPDATA", "PROGRAMDATA", "PROGRAMFILES", "PROGRAMFILES(X86)",
    "PROGRAMW6432", "COMMONPROGRAMFILES", "TEMP", "TMP", "TMPDIR", "LANG", "LC_ALL",
    "TERM", "SHELL", "XDG_CONFIG_HOME", "XDG_DATA_HOME", "XDG_CACHE_HOME",
    "NUMBER_OF_PROCESSORS", "PROCESSOR_ARCHITECTURE", "HTTP_PROXY", "HTTPS_PROXY",
    "NO_PROXY", "SSL_CERT_FILE", "REQUESTS_CA_BUNDLE", "NODE_EXTRA_CA_CERTS",
)


@dataclass
class ProviderStatus:
    provider_id: str
    available: bool
    executable: str | None = None
    version: str | None = None
    reason: str | None = None
    features: dict[str, bool] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AgentLaunchRequest:
    run_id: str
    node_id: str
    role: str
    cwd: str
    prompt_path: str
    output_dir: str
    capability_class: str
    effort: str
    model: str
    provider_effort: str | None
    read_only: bool
    timeout_seconds: int = 3600
    allowed_tools: list[str] = field(default_factory=list)
    env_allowlist: list[str] = field(default_factory=list)
    result_schema: dict[str, Any] | None = None


@dataclass
class InvocationPlan:
    executable: str
    argv: list[str]
    cwd: str
    env: dict[str, str]
    stdin_path: str | None
    provider: str
    model: str
    effort: str | None
    adapter_version: str
    display: str
    result_path: str | None = None


@dataclass
class RunningAgent:
    provider_id: str
    node_id: str
    pid: int | None
    started_monotonic: float
    started_at: str
    stdout_path: str
    stderr_path: str
    result_path: str | None
    display: str
    process: Any = None  # live Popen, never persisted
    token: str | None = None  # in-process adapters

    def persisted(self) -> dict[str, Any]:
        return {
            "provider": self.provider_id,
            "pid": self.pid,
            "started_at": self.started_at,
            "stdout_path": self.stdout_path,
            "stderr_path": self.stderr_path,
            "result_path": self.result_path,
            "display": self.display,
            "token": self.token,
        }


@dataclass
class AgentProcessStatus:
    running: bool
    returncode: int | None = None


@dataclass
class AgentResult:
    outcome: str  # "completed" or "failed"
    failure_kind: str | None = None
    summary: str = ""
    structured: dict[str, Any] | None = None
    usage: dict[str, int] = field(default_factory=dict)
    duration_ms: int | None = None
    detail: str | None = None

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["summary"] = redact(self.summary, 600)
        payload["detail"] = redact(self.detail, 400) if self.detail else None
        return payload


class CodingAgentAdapter(Protocol):
    adapter_id: str

    def probe(self) -> ProviderStatus: ...
    def resolve_invocation(self, request: AgentLaunchRequest) -> InvocationPlan: ...
    def start(self, request: AgentLaunchRequest) -> RunningAgent: ...
    def poll(self, handle: RunningAgent) -> AgentProcessStatus: ...
    def cancel(self, handle: RunningAgent) -> None: ...
    def collect(self, handle: RunningAgent) -> AgentResult: ...


def extract_structured(text: str) -> dict[str, Any] | None:
    """Return the last ``agent-os-result`` (or ```json) object in agent output."""
    for pattern in (_RESULT_BLOCK, _JSON_BLOCK):
        for raw in reversed(pattern.findall(text or "")):
            try:
                value = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if isinstance(value, dict):
                return value
    return None


def classify_failure(text: str, returncode: int | None) -> str:
    if INVALID_MODEL_PATTERN.search(text or ""):
        return "invalid_model"
    if QUOTA_PATTERN.search(text or ""):
        return "quota"
    return "process_error"


def build_env(provider_allowlist: list[str], request_allowlist: list[str], prefixes: tuple[str, ...] = ()) -> dict[str, str]:
    wanted = {item.upper() for item in (*SYSTEM_ENV_ALLOWLIST, *provider_allowlist, *request_allowlist)}
    env: dict[str, str] = {}
    for key, value in os.environ.items():
        upper = key.upper()
        if upper in wanted or any(upper.startswith(prefix) for prefix in prefixes):
            env[key] = value
    return env


def _read_tail(path: str | None, limit: int = 200_000) -> str:
    if not path:
        return ""
    try:
        with open(path, "rb") as handle:
            handle.seek(0, os.SEEK_END)
            size = handle.tell()
            handle.seek(max(size - limit, 0))
            return handle.read().decode("utf-8", errors="replace")
    except OSError:
        return ""


def kill_tree(pid: int) -> None:
    if not pid_alive(pid):
        return
    if os.name == "nt":
        subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], capture_output=True, check=False)
    else:
        import signal

        try:
            os.killpg(os.getpgid(pid), signal.SIGTERM)
        except OSError:
            try:
                os.kill(pid, signal.SIGTERM)
            except OSError:
                pass


class SubprocessAdapter:
    """Shared process lifecycle for CLI adapters; subclasses supply syntax."""

    adapter_id = "subprocess"
    adapter_version = "1"
    env_prefixes: tuple[str, ...] = ()
    default_executable = ""

    def __init__(self, provider: dict[str, Any]) -> None:
        self.provider = provider
        self._probe: ProviderStatus | None = None

    # -- discovery ---------------------------------------------------------

    def executable(self) -> str | None:
        configured = self.provider.get("executable") or self.default_executable
        if not configured:
            return None
        if os.path.isabs(configured) and os.path.exists(configured):
            return configured
        return shutil.which(configured)

    def _run_quick(self, argv: list[str], timeout: int = 30) -> tuple[int, str]:
        try:
            completed = subprocess.run(
                argv,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout,
                stdin=subprocess.DEVNULL,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            return 1, str(exc)
        return completed.returncode, (completed.stdout or "") + (completed.stderr or "")

    def probe(self) -> ProviderStatus:
        if self._probe is not None:
            return self._probe
        executable = self.executable()
        if not executable:
            self._probe = ProviderStatus(self.provider["id"], False, reason="executable not found on PATH")
            return self._probe
        code, output = self._run_quick([executable, "--version"])
        version = output.strip().splitlines()[0][:120] if output.strip() else None
        if code != 0:
            self._probe = ProviderStatus(self.provider["id"], False, executable, version, reason="version probe failed")
            return self._probe
        self._probe = ProviderStatus(
            self.provider["id"], True, executable, version, features=self.probe_features(executable)
        )
        return self._probe

    def probe_features(self, executable: str) -> dict[str, bool]:
        return {}

    # -- lifecycle ---------------------------------------------------------

    def resolve_invocation(self, request: AgentLaunchRequest) -> InvocationPlan:  # pragma: no cover - abstract
        raise NotImplementedError

    def start(self, request: AgentLaunchRequest) -> RunningAgent:
        plan = self.resolve_invocation(request)
        output_dir = Path(request.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        stdout_path = output_dir / "stdout.log"
        stderr_path = output_dir / "stderr.log"
        (output_dir / "invocation.json").write_text(
            json.dumps(
                {
                    "display": plan.display,
                    "cwd": plan.cwd,
                    "provider": plan.provider,
                    "model": plan.model,
                    "effort": plan.effort,
                    "adapter_version": plan.adapter_version,
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        stdin_handle = open(plan.stdin_path, "rb") if plan.stdin_path else subprocess.DEVNULL
        creationflags = 0
        start_new_session = False
        if os.name == "nt":
            creationflags = subprocess.CREATE_NEW_PROCESS_GROUP | getattr(subprocess, "CREATE_NO_WINDOW", 0)
        else:
            start_new_session = True
        try:
            with open(stdout_path, "wb") as out, open(stderr_path, "wb") as err:
                process = subprocess.Popen(
                    [plan.executable, *plan.argv],
                    cwd=plan.cwd,
                    env=plan.env,
                    stdin=stdin_handle,
                    stdout=out,
                    stderr=err,
                    creationflags=creationflags,
                    start_new_session=start_new_session,
                )
        finally:
            if stdin_handle is not subprocess.DEVNULL:
                stdin_handle.close()
        return RunningAgent(
            provider_id=self.provider["id"],
            node_id=request.node_id,
            pid=process.pid,
            started_monotonic=time.monotonic(),
            started_at=utc_now_iso(),
            stdout_path=str(stdout_path),
            stderr_path=str(stderr_path),
            result_path=plan.result_path,
            display=plan.display,
            process=process,
        )

    def poll(self, handle: RunningAgent) -> AgentProcessStatus:
        if handle.process is not None:
            code = handle.process.poll()
            return AgentProcessStatus(running=code is None, returncode=code)
        return AgentProcessStatus(running=pid_alive(handle.pid), returncode=None)

    def cancel(self, handle: RunningAgent) -> None:
        if handle.pid:
            kill_tree(handle.pid)
        if handle.process is not None:
            try:
                handle.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                handle.process.kill()

    def collect(self, handle: RunningAgent) -> AgentResult:
        returncode = handle.process.returncode if handle.process is not None else None
        stdout = _read_tail(handle.stdout_path)
        stderr = _read_tail(handle.stderr_path, 20_000)
        duration = int((time.monotonic() - handle.started_monotonic) * 1000)
        result = self.parse_result(handle, returncode, stdout, stderr)
        result.duration_ms = duration
        return result

    def parse_result(self, handle: RunningAgent, returncode: int | None, stdout: str, stderr: str) -> AgentResult:  # pragma: no cover
        raise NotImplementedError

    def failed(self, kind: str, detail: str) -> AgentResult:
        return AgentResult(outcome="failed", failure_kind=kind, detail=redact(detail, 400))
