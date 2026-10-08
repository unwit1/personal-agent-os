"""Register the Agent OS native-messaging host with Firefox (per user).

Writes a launcher and host manifest under %LOCALAPPDATA%\\AgentOS\\native and
points HKCU\\Software\\Mozilla\\NativeMessagingHosts\\agent_os_native at it.
No administrator rights are needed. Re-running is safe.

    python browser/extension/tools/install_native_host.py [--uninstall]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

HOST_NAME = "agent_os_native"
EXTENSION_ID = "agent-os@unwit1.local"
EXTENSION_DIR = Path(__file__).resolve().parents[1]
HOST_SCRIPT = EXTENSION_DIR / "native" / "agent_os_native_host.py"
REG_PATH = rf"Software\Mozilla\NativeMessagingHosts\{HOST_NAME}"


def install_dir() -> Path:
    base = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
    return Path(base) / "AgentOS" / "native"


def install() -> dict:
    target = install_dir()
    target.mkdir(parents=True, exist_ok=True)
    launcher = target / "agent_os_native_host.bat"
    # Firefox launches the .bat; -u keeps stdio unbuffered for the protocol.
    launcher.write_text(
        f'@echo off\r\n"{sys.executable}" -u "{HOST_SCRIPT}" %*\r\n',
        encoding="ascii",
    )
    manifest = target / f"{HOST_NAME}.json"
    manifest.write_text(
        json.dumps(
            {
                "name": HOST_NAME,
                "description": "Agent OS bridge pairing and auto-start",
                "path": str(launcher),
                "type": "stdio",
                "allowed_extensions": [EXTENSION_ID],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    if os.name == "nt":
        import winreg

        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, REG_PATH) as key:
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, str(manifest))
    return {"installed": True, "manifest": str(manifest), "launcher": str(launcher), "registry": "HKCU\\" + REG_PATH}


def uninstall() -> dict:
    if os.name == "nt":
        import winreg

        try:
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, REG_PATH)
        except FileNotFoundError:
            pass
    for name in ("agent_os_native_host.bat", f"{HOST_NAME}.json"):
        path = install_dir() / name
        if path.exists():
            path.unlink()
    return {"installed": False}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--uninstall", action="store_true")
    args = parser.parse_args()
    print(json.dumps(uninstall() if args.uninstall else install(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
