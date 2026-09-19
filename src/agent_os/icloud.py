from __future__ import annotations

import base64
import ctypes
import getpass
import imaplib
import json
import os
import smtplib
from ctypes import wintypes
from pathlib import Path

from .paths import ROOT


LOCAL_DIR = ROOT / ".agent-local"
CONFIG_PATH = LOCAL_DIR / "icloud.json"


class _DataBlob(ctypes.Structure):
    _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_ubyte))]


def _blob(data: bytes) -> tuple[_DataBlob, ctypes.Array[ctypes.c_char]]:
    buffer = ctypes.create_string_buffer(data)
    return _DataBlob(len(data), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_ubyte))), buffer


def protect_secret(secret: str) -> str:
    """Encrypt a secret for the current Windows account using DPAPI."""
    if os.name != "nt":
        raise OSError("iCloud credential storage currently requires Windows DPAPI")
    source, source_buffer = _blob(secret.encode("utf-8"))
    encrypted = _DataBlob()
    crypt32 = ctypes.windll.crypt32
    kernel32 = ctypes.windll.kernel32
    if not crypt32.CryptProtectData(
        ctypes.byref(source),
        "Personal Agent OS iCloud Mail",
        None,
        None,
        None,
        0,
        ctypes.byref(encrypted),
    ):
        raise ctypes.WinError()
    try:
        payload = ctypes.string_at(encrypted.pbData, encrypted.cbData)
        return base64.b64encode(payload).decode("ascii")
    finally:
        kernel32.LocalFree(encrypted.pbData)
        del source_buffer


def unprotect_secret(encoded: str) -> str:
    """Decrypt a DPAPI value for the current Windows account."""
    if os.name != "nt":
        raise OSError("iCloud credential storage currently requires Windows DPAPI")
    source, source_buffer = _blob(base64.b64decode(encoded, validate=True))
    decrypted = _DataBlob()
    crypt32 = ctypes.windll.crypt32
    kernel32 = ctypes.windll.kernel32
    if not crypt32.CryptUnprotectData(
        ctypes.byref(source), None, None, None, None, 0, ctypes.byref(decrypted)
    ):
        raise ctypes.WinError()
    try:
        return ctypes.string_at(decrypted.pbData, decrypted.cbData).decode("utf-8")
    finally:
        kernel32.LocalFree(decrypted.pbData)
        del source_buffer


def _test_imap(email: str, password: str) -> None:
    try:
        with imaplib.IMAP4_SSL("imap.mail.me.com", 993, timeout=20) as client:
            client.login(email, password)
            client.logout()
    except imaplib.IMAP4.error as exc:
        raise ValueError("iCloud IMAP authentication failed; check the email and app-specific password") from exc


def _test_smtp(email: str, password: str) -> None:
    try:
        with smtplib.SMTP("smtp.mail.me.com", 587, timeout=20) as client:
            client.ehlo()
            client.starttls()
            client.ehlo()
            client.login(email, password)
    except smtplib.SMTPException as exc:
        raise ValueError("iCloud SMTP authentication failed; check the email and app-specific password") from exc


def _prompt_password() -> str:
    """Use a Windows dialog so Ctrl+V works without echoing the password."""
    if os.name == "nt":
        try:
            import tkinter as tk
            from tkinter import simpledialog

            root = tk.Tk()
            root.withdraw()
            root.attributes("-topmost", True)
            password = simpledialog.askstring(
                "Personal Agent OS",
                "Apple app-specific password:",
                show="*",
                parent=root,
            )
            root.destroy()
            if password is None:
                raise ValueError("iCloud setup cancelled")
            return password.strip()
        except ValueError:
            raise
        except Exception:
            pass
    return getpass.getpass("Apple app-specific password: ").strip()


def setup() -> dict[str, object]:
    print("\n=== Personal Agent OS - iCloud Mail Setup ===\n")
    email = input("iCloud email address: ").strip()
    if not email or "@" not in email:
        raise ValueError("Enter a valid iCloud email address")
    password = _prompt_password()
    if not password:
        raise ValueError("The app-specific password cannot be empty")

    print("\nTesting iCloud IMAP...")
    _test_imap(email, password)
    print("OK - IMAP connected")
    print("Testing iCloud SMTP authentication (no message will be sent)...")
    _test_smtp(email, password)
    print("OK - SMTP connected")

    config = {
        "version": 1,
        "email": email,
        "encrypted_password": protect_secret(password),
        "protection": "windows-dpapi-current-user",
        "imap_host": "imap.mail.me.com",
        "imap_port": 993,
        "smtp_host": "smtp.mail.me.com",
        "smtp_port": 587,
        "smtp_sending_requires_approval": True,
    }
    LOCAL_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    print(f"\nOK - Credentials saved for this Windows account in {CONFIG_PATH}")
    print("SMTP sending remains approval-gated.")
    return {
        "configured": True,
        "email": email,
        "config_path": str(CONFIG_PATH),
        "protection": config["protection"],
        "smtp_sending_requires_approval": True,
    }


def status() -> dict[str, object]:
    if not CONFIG_PATH.exists():
        return {"configured": False, "config_path": str(CONFIG_PATH)}
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    return {
        "configured": True,
        "email": config.get("email"),
        "config_path": str(CONFIG_PATH),
        "protection": config.get("protection"),
        "smtp_sending_requires_approval": config.get("smtp_sending_requires_approval", True),
    }
