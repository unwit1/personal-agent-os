"""Headless Firefox for Agent OS automation (ADP reports and other unattended browser work).

Runs a second Firefox on its own profile, with the Agent OS extension installed,
so automation never touches the everyday browser. Pages built from web
components (ADP Workforce Now) only render in a tab Firefox considers visible;
a headless window always is.

    python tools/automation_profile.py setup             # create/refresh the profile, install the signed extension
    python tools/automation_profile.py start [--visible] [URL ...]
    python tools/automation_profile.py stop
    python tools/automation_profile.py status
    python tools/automation_profile.py adp-login [--visible]   # (re)start and run the ADP sign-in test once

--visible opens a normal window instead, for one-time steps a person must do
(for example an ADP verification code the first time ADP sees this profile).
The profile lives in .agent-os/firefox-automation-profile (gitignored) and
keeps its cookies, so a sign-in lasts as long as ADP allows.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

EXT_DIR = Path(__file__).resolve().parents[1]
REPO = EXT_DIR.parents[1]
PROFILE = REPO / ".agent-os" / "firefox-automation-profile"
EXTENSION_ID = "agent-os@unwit1.local"
# Fixed so the extension's own pages (the ADP sign-in test) have a known address in this profile.
EXTENSION_UUID = "5d0c5d6e-2f43-4a7e-9a0e-7f3b8e7a0a51"
FIREFOX = Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "Mozilla Firefox" / "firefox.exe"
WINDOW_SIZE = "1600,1000"
ADP_LOGIN_URL = f"moz-extension://{EXTENSION_UUID}/adp/login.html?autostart=1"
WARM_UP_SECONDS = 15

PREFS = {
    "extensions.autoDisableScopes": 0,  # enable the extension installed in the profile folder
    "extensions.enabledScopes": 15,
    "extensions.webextensions.uuids": json.dumps({EXTENSION_ID: EXTENSION_UUID}),
    "browser.shell.checkDefaultBrowser": False,
    "browser.startup.homepage_override.mstone": "ignore",
    "browser.aboutwelcome.enabled": False,
    "startup.homepage_welcome_url": "",
    "startup.homepage_welcome_url.additional": "",
    "datareporting.policy.dataSubmissionEnabled": False,
    "toolkit.telemetry.reportingpolicy.firstRun": False,
    "browser.sessionstore.resume_from_crash": False,
    "browser.tabs.warnOnClose": False,
    "signon.rememberSignons": False,
    "app.update.auto": False,
}


def pref_line(name: str, value: object) -> str:
    return f"user_pref({json.dumps(name)}, {json.dumps(value)});"


def manifest_version() -> str:
    return json.loads((EXT_DIR / "src" / "manifest.json").read_text(encoding="utf-8-sig"))["version"]


def latest_signed_xpi() -> Path:
    def key(path: Path) -> tuple[int, ...]:
        match = re.search(r"-(\d+(?:\.\d+)*)\.xpi$", path.name)
        return tuple(int(p) for p in match.group(1).split(".")) if match else ()

    signed = sorted((EXT_DIR / "dist" / "signed").glob("*.xpi"), key=key)
    if not signed:
        raise SystemExit("no signed build in dist/signed; run python tools/build.py --sign")
    return signed[-1]


def setup() -> dict:
    PROFILE.mkdir(parents=True, exist_ok=True)
    (PROFILE / "user.js").write_text("\n".join(pref_line(k, v) for k, v in PREFS.items()) + "\n", encoding="utf-8")
    xpi = latest_signed_xpi()
    target = PROFILE / "extensions" / f"{EXTENSION_ID}.xpi"
    target.parent.mkdir(exist_ok=True)
    if running():
        staged = PROFILE / "extensions" / "staged" / f"{EXTENSION_ID}.xpi"
        staged.parent.mkdir(exist_ok=True)
        shutil.copyfile(xpi, staged)
        installed = f"{staged} (applies on next start)"
    else:
        shutil.copyfile(xpi, target)
        installed = str(target)
    return {"profile": str(PROFILE), "extension": xpi.name, "installed_to": installed, "manifest_version": manifest_version()}


def running() -> list[int]:
    """PIDs of Firefox processes started on the automation profile (never the everyday browser)."""
    script = (
        "Get-CimInstance Win32_Process -Filter \"Name='firefox.exe'\" | "
        "Select-Object ProcessId, CommandLine | ConvertTo-Json -Compress"
    )
    out = subprocess.run(["powershell", "-NoProfile", "-Command", script], capture_output=True, text=True).stdout.strip()
    if not out:
        return []
    rows = json.loads(out)
    rows = rows if isinstance(rows, list) else [rows]
    needle = str(PROFILE).lower()
    return [int(r["ProcessId"]) for r in rows if needle in str(r.get("CommandLine") or "").lower()]


def start(urls: list[str], visible: bool = False) -> dict:
    if not (PROFILE / "user.js").exists():
        setup()
    if running():
        return {"started": False, "reason": "already running", "pids": running()}
    args = [str(FIREFOX), "--no-remote", "--profile", str(PROFILE)]
    if not visible:
        args += ["--headless", "--window-size", WINDOW_SIZE]
    args += urls or ["about:blank"]
    flags = getattr(subprocess, "DETACHED_PROCESS", 0) | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
    with open(PROFILE / "firefox.log", "ab") as log:
        subprocess.Popen(args, close_fds=True, creationflags=flags, stdout=log, stderr=log, stdin=subprocess.DEVNULL)
    return {"started": True, "headless": not visible, "urls": urls, "log": str(PROFILE / "firefox.log")}


def stop() -> dict:
    pids = running()
    for pid in pids:
        subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], capture_output=True)
    return {"stopped": pids}


def adp_login(visible: bool = False) -> dict:
    """Restart and run the ADP sign-in test once.

    A warm-up start lets a newly installed extension finish starting; otherwise
    its sign-in page can load before the extension is ready and do nothing.
    """
    stop()
    start(["about:blank"], visible)
    time.sleep(WARM_UP_SECONDS)
    stop()
    time.sleep(2)  # the profile lock is released after the process exits
    # The sign-in page and its test tab close themselves when done; the first tab keeps Firefox running.
    return start(["about:blank", ADP_LOGIN_URL], visible)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", choices=["setup", "start", "stop", "status", "adp-login"])
    parser.add_argument("urls", nargs="*")
    parser.add_argument("--visible", action="store_true", help="normal window instead of headless")
    args = parser.parse_args()
    if args.command == "setup":
        result = setup()
    elif args.command == "start":
        result = start(args.urls, args.visible)
    elif args.command == "stop":
        result = stop()
    elif args.command == "status":
        result = {"profile": str(PROFILE), "exists": PROFILE.exists(), "pids": running()}
    else:
        result = adp_login(args.visible)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
