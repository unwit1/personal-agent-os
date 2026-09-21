"""Optional CLI workers; no vendor SDK or automatic permission bypass."""
from __future__ import annotations

import json
import os
import shutil
import signal
import subprocess
import tempfile
import math
from pathlib import Path
from contextlib import contextmanager

from .contracts import PROVIDER_RESULT
from .paths import ROOT
from .registry import get_project


@contextmanager
def transit_directory(directory):
    with tempfile.TemporaryDirectory(dir=directory) as name:
        yield Path(name)


class ClientFailure(RuntimeError):
    def __init__(self, code=1):
        super().__init__("Client did not return a successful structured result")
        self.exit_code = code if 0 < code < 256 else 1


def _executable(name: str) -> list[str]:
    found = shutil.which(name)
    if not found:
        raise ClientFailure(127)
    path = Path(found)
    if path.suffix.lower() in {".cmd", ".bat", ".ps1"}:
        # Bypass recognized npm launch shims without constructing shell commands.
        module = {"codex": "@openai/codex/bin/codex.js", "claude": "@anthropic-ai/claude-code/cli.js"}[name]
        script = path.parent / "node_modules" / module
        node = shutil.which("node")
        if not script.is_file() or not node:
            raise ClientFailure(127)
        return [node, str(script)]
    return [str(path)]


def _invoke(argv: list[str], packet: dict, cwd: str | None, timeout: float):
    if not argv or Path(argv[0]).suffix.lower() in {".bat", ".cmd", ".ps1"}:
        raise ValueError("Use a native executable or explicit interpreter, not a shell shim")
    process = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                               text=True, encoding="utf-8", errors="replace", cwd=cwd, shell=False,
                               creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
                               start_new_session=os.name != "nt")
    try:
        stdout, _ = process.communicate(json.dumps(packet, ensure_ascii=False), timeout=timeout)
    except BaseException as exc:
        if os.name == "nt":
            subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"], stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW, check=False)
        else:
            os.killpg(process.pid, signal.SIGKILL)
        process.kill()
        process.communicate()
        if isinstance(exc, subprocess.TimeoutExpired):
            raise TimeoutError("Worker execution timed out") from None
        raise
    if process.returncode:
        raise ClientFailure(process.returncode)
    if len(stdout) > 2000000:
        raise ClientFailure()
    return stdout


class CommandProvider:
    """JSON on stdin -> {response, postflight} JSON on stdout."""
    def __init__(self, argv: list[str], timeout: float = 600):
        if not argv or not all(isinstance(item, str) for item in argv):
            raise ValueError("command must be a non-empty string array")
        if not math.isfinite(timeout) or timeout <= 0:
            raise ValueError("timeout must be positive and finite")
        self.argv, self.timeout = argv, timeout

    def execute(self, request: dict) -> dict:
        project = request["envelope"]["routing"]["project"]
        cwd = get_project(project)["path"] if project else None
        return json.loads(_invoke(self.argv, request, cwd, self.timeout))


class CLIProvider:
    def __init__(self, client: str, timeout: float = 600):
        if client not in {"codex", "claude"}:
            raise ValueError("unsupported CLI client")
        if not math.isfinite(timeout) or timeout <= 0:
            raise ValueError("timeout must be positive and finite")
        self.client, self.timeout = client, timeout

    def execute(self, request: dict) -> dict:
        prefix = _executable(self.client)
        project = request["envelope"]["routing"]["project"]
        cwd = get_project(project)["path"] if project else None
        local = ROOT / ".agent-local" / "client-transit"
        local.mkdir(parents=True, exist_ok=True)
        with transit_directory(local) as temp:
            if self.client == "codex":
                schema = Path(temp) / "result.schema.json"
                # Codex strict output schemas require every declared property.
                strict = json.loads(json.dumps(PROVIDER_RESULT))
                def require_all(value):
                    if isinstance(value, dict):
                        if value.get("type") == "object":
                            value["required"] = list(value["properties"])
                        for nested in value.values():
                            require_all(nested)
                    elif isinstance(value, list):
                        for nested in value:
                            require_all(nested)
                require_all(strict)
                schema.write_text(json.dumps(strict), encoding="utf-8")
                output = Path(temp) / "result.json"
                argv = prefix + ["exec", "--ephemeral", "--output-schema", str(schema), "--output-last-message", str(output), "-"]
                _invoke(argv, request, cwd, self.timeout)
                if not output.is_file() or output.stat().st_size > 2000000:
                    raise ClientFailure()
                return json.loads(output.read_text(encoding="utf-8"))
            argv = prefix + ["-p", "--no-session-persistence", "--output-format", "json", "--json-schema", json.dumps(PROVIDER_RESULT)]
            result = json.loads(_invoke(argv, request, cwd, self.timeout))
            if not isinstance(result, dict) or result.get("is_error") or not isinstance(result.get("structured_output"), dict):
                raise ClientFailure()
            return result["structured_output"]
