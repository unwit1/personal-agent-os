"""Firefox native-messaging host for the Agent OS extension.

Firefox starts this process on demand and only for the extension ID listed in
the host manifest (see tools/install_native_host.py). It lets the extension
pair with the local browser bridge without the token ever being typed or
bundled, and keeps the bridge running.

Protocol: 4-byte little-endian length + UTF-8 JSON, one request per message.

Commands:
  {"cmd": "hello"}                          -> {"ok": true, "version": ...}
  {"cmd": "bridge_config", "ensure": true}  -> {"ok": true, "endpoint", "token", "running", "started"}
  {"cmd": "routines_tick"}                  -> starts due AI browser routines in the background
  {"cmd": "routines_list"} / {"cmd": "routine_runs", "routine_id"?}
  {"cmd": "routine_save", "routine": {...}} / {"cmd": "routine_delete", "routine_id"}
  {"cmd": "routine_run", "routine_id"}      -> {"ok": true, "run_id"}
  {"cmd": "credential_set", "task_id", "username"?, "password"?}  -> scheduled-task login into
      Windows Credential Manager (empty fields keep the saved value)
  {"cmd": "credential_get", "task_id", "field"}  -> {"ok": true, "value"} (username|password)
  {"cmd": "credential_status", "task_id"} / {"cmd": "credential_delete", "task_id"}
"""

from __future__ import annotations

import json
import os
import struct
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

HOST_VERSION = "1.2.0"
REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "src"))

from agent_os.browser_bridge_server import load_or_create_token  # noqa: E402
from agent_os.paths import INDEX_DIR  # noqa: E402

# Extension settings managed on this machine (gitignored), e.g. the Google
# Sheet receiver URL, so they never live in the published extension.
MANAGED_SETTINGS_PATH = INDEX_DIR / "browser-extension-settings.json"
MANAGED_SETTING_KEYS = {"sheetEndpoint", "sheetToken", "sheetMirrorEnabled"}


def managed_settings() -> dict:
    try:
        data = json.loads(MANAGED_SETTINGS_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    if not isinstance(data, dict):
        return {}
    return {key: value for key, value in data.items() if key in MANAGED_SETTING_KEYS}

BRIDGE_HOST = "127.0.0.1"
BRIDGE_PORT = 8766
CREATE_BREAKAWAY_FROM_JOB = 0x01000000


def read_message() -> dict | None:
    header = sys.stdin.buffer.read(4)
    if len(header) < 4:
        return None
    (length,) = struct.unpack("<I", header)
    if length > 1024 * 1024:
        return None
    body = sys.stdin.buffer.read(length)
    return json.loads(body.decode("utf-8"))


def send_message(payload: dict) -> None:
    data = json.dumps(payload).encode("utf-8")
    sys.stdout.buffer.write(struct.pack("<I", len(data)))
    sys.stdout.buffer.write(data)
    sys.stdout.buffer.flush()


def bridge_running(token: str) -> bool:
    request = urllib.request.Request(
        f"http://{BRIDGE_HOST}:{BRIDGE_PORT}/api/v1/browser/stats",
        headers={"X-Agent-OS-Token": token},
    )
    try:
        with urllib.request.urlopen(request, timeout=2) as response:
            return response.status == 200
    except urllib.error.HTTPError as exc:
        # Something answers on the port; a 401 means another token is in use.
        return exc.code != 404
    except OSError:
        return False


def start_bridge() -> None:
    python = Path(sys.executable)
    pythonw = python.with_name("pythonw.exe")
    interpreter = str(pythonw if pythonw.exists() else python)
    log_dir = REPO_ROOT / ".agent-os"
    log_dir.mkdir(parents=True, exist_ok=True)
    log = open(log_dir / "browser-bridge.log", "ab")
    command = [interpreter, str(REPO_ROOT / "agent.py"), "browser-bridge", "--host", BRIDGE_HOST, "--port", str(BRIDGE_PORT)]
    if os.name != "nt":
        subprocess.Popen(command, cwd=str(REPO_ROOT), stdin=subprocess.DEVNULL, stdout=log, stderr=log,
                         start_new_session=True, close_fds=True)
        return
    # Firefox runs native hosts in a kill-on-close job object, so a plain
    # child would die with this host. Break away from the job; if the job
    # forbids that, have WMI start the bridge outside the job entirely.
    flags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS | subprocess.CREATE_NO_WINDOW
    try:
        subprocess.Popen(command, cwd=str(REPO_ROOT), stdin=subprocess.DEVNULL, stdout=log, stderr=log,
                         creationflags=flags | CREATE_BREAKAWAY_FROM_JOB, close_fds=True)
        return
    except OSError:
        pass
    line = subprocess.list2cmdline(command)
    script = (
        "Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments "
        f"@{{CommandLine='{line.replace(chr(39), chr(39) * 2)}'; CurrentDirectory='{str(REPO_ROOT).replace(chr(39), chr(39) * 2)}'}} | Out-Null"
    )
    subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", script],
                   stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                   creationflags=subprocess.CREATE_NO_WINDOW, timeout=20, check=False)


def bridge_config(ensure: bool) -> dict:
    token = load_or_create_token()
    running = bridge_running(token)
    started = False
    if ensure and not running:
        start_bridge()
        started = True
        for _ in range(30):
            time.sleep(0.25)
            if bridge_running(token):
                running = True
                break
    return {
        "ok": True,
        "endpoint": f"http://{BRIDGE_HOST}:{BRIDGE_PORT}/api/v1/browser/batch",
        "token": token,
        "running": running,
        "started": started,
        "managed_settings": managed_settings(),
    }


def routines(message: dict, cmd: str) -> dict:
    from agent_os import browser_routines as br

    if cmd == "routines_tick":
        due = br.due_routines()
        if due:
            br.spawn_detached(["tick"])
        return {"ok": True, "due": [r["id"] for r in due]}
    if cmd == "routines_list":
        return {"ok": True, "routines": [br.summary(r) | {"instructions": r.get("instructions")} for r in br.list_routines()]}
    if cmd == "routine_runs":
        keys = ("run_id", "routine_id", "routine_name", "status", "summary", "findings", "started_at", "finished_at", "error")
        runs = br.list_runs(int(message.get("limit") or 15), message.get("routine_id") or None)
        return {"ok": True, "runs": [{k: run.get(k) for k in keys} for run in runs]}
    if cmd == "routine_save":
        return {"ok": True, "routine": br.summary(br.save_routine(dict(message.get("routine") or {})))}
    if cmd == "routine_delete":
        return {"ok": True, "deleted": br.delete_routine(str(message.get("routine_id") or ""))}
    if cmd == "routine_run":
        return {"ok": True, "run_id": br.start_run(str(message.get("routine_id") or ""), trigger="extension")}
    return {"ok": False, "error": f"unknown command: {cmd}"}


KEYRING_SERVICE = os.environ.get("AGENT_OS_TASKS_KEYRING_SERVICE", "agent-os-browser-tasks")
CREDENTIAL_FIELDS = ("username", "password")


def _task_key(message: dict, field: str) -> str:
    task_id = str(message.get("task_id") or "").strip()
    if not task_id or len(task_id) > 120:
        raise ValueError("task_id is required")
    if field not in CREDENTIAL_FIELDS:
        raise ValueError("field must be username or password")
    return f"{task_id}:{field}"


def credentials(message: dict, cmd: str) -> dict:
    import keyring
    from keyring.errors import PasswordDeleteError

    if cmd == "credential_set":
        saved = []
        for field in CREDENTIAL_FIELDS:
            value = message.get(field)
            if isinstance(value, str) and value:
                keyring.set_password(KEYRING_SERVICE, _task_key(message, field), value)
                saved.append(field)
        return {"ok": True, "saved": saved}
    if cmd == "credential_get":
        field = str(message.get("field") or "")
        value = keyring.get_password(KEYRING_SERVICE, _task_key(message, field))
        if value is None:
            return {"ok": False, "error": f"no saved {field} for this task"}
        return {"ok": True, "value": value}
    if cmd == "credential_status":
        return {"ok": True, **{
            f"has_{field}": keyring.get_password(KEYRING_SERVICE, _task_key(message, field)) is not None
            for field in CREDENTIAL_FIELDS
        }}
    if cmd == "credential_delete":
        for field in CREDENTIAL_FIELDS:
            try:
                keyring.delete_password(KEYRING_SERVICE, _task_key(message, field))
            except PasswordDeleteError:
                pass
        return {"ok": True}
    return {"ok": False, "error": f"unknown command: {cmd}"}


def handle(message: dict) -> dict:
    cmd = str(message.get("cmd") or "")
    if cmd == "hello":
        return {"ok": True, "version": HOST_VERSION, "repo": str(REPO_ROOT)}
    if cmd == "bridge_config":
        return bridge_config(bool(message.get("ensure")))
    if cmd.startswith("credential_"):
        try:
            return credentials(message, cmd)
        except ValueError as exc:
            return {"ok": False, "error": str(exc)}
    if cmd.startswith("routine"):
        try:
            return routines(message, cmd)
        except (KeyError, ValueError) as exc:
            return {"ok": False, "error": str(exc).strip("'\"")}
    return {"ok": False, "error": f"unknown command: {cmd}"}


def main() -> int:
    while True:
        try:
            message = read_message()
        except (ValueError, OSError):
            return 1
        if message is None:
            return 0
        try:
            send_message(handle(message))
        except Exception as exc:  # report instead of dying silently
            send_message({"ok": False, "error": f"{type(exc).__name__}: {exc}"})


if __name__ == "__main__":
    raise SystemExit(main())
