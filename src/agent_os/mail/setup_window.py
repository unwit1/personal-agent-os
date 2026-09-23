"""A small window for adding a mail account and its password.

Opened by ``agent-os mail setup`` (or ``python agent.py mail setup``). The
password goes from a masked entry box straight to the OS keyring; it is never
printed, logged, written to a file, or shown again. The sign-in test and the
first sync run on a worker thread so the window stays responsive.

``save_account`` holds the logic and has no UI, so it is testable without a
display.
"""

from __future__ import annotations

import threading
from typing import Any, Callable

from . import accounts as accounts_lib

ERROR_HELP = {
    "auth_failed": "The email or password was not accepted. Check both and try again.",
    "credential_missing": "No password was saved. Enter it and try again.",
    "connection_failed": "Could not reach the mail server. Check your internet connection and try again.",
    "timeout": "The mail server took too long to answer. Try again in a minute.",
}


def _account_id_for(provider: str, email: str, existing: list[accounts_lib.Account]) -> str:
    base = provider
    taken = {account.id for account in existing}
    if base not in taken:
        return base
    number = 2
    while f"{base}-{number}" in taken:
        number += 1
    return f"{base}-{number}"


def save_account(provider: str, email: str, secret: str, *, folders: list[str] | None = None,
                 test: Callable[[accounts_lib.Account], dict[str, Any]] | None = None) -> dict[str, Any]:
    """Add the account (or reuse the one with this email), store the password,
    and test the sign-in. Returns a plain summary; never includes the secret."""
    email = str(email or "").strip()
    if provider not in accounts_lib.PROVIDERS:
        return {"ok": False, "message": "Choose EarthLink or iCloud."}
    if "@" not in email:
        return {"ok": False, "message": "Enter the full email address, like name@earthlink.net."}
    if not secret:
        return {"ok": False, "message": "Enter the password."}
    existing = accounts_lib.load_accounts()
    account = next((item for item in existing if item.provider == provider and item.email.lower() == email.lower()), None)
    created = account is None
    if created:
        account = accounts_lib.add_account(provider, _account_id_for(provider, email, existing), email, folders=folders)
    try:
        accounts_lib.set_secret(account.id, secret)
    except accounts_lib.AccountError as exc:
        return {"ok": False, "account_id": account.id, "message": str(exc)}
    if test is None:
        from .engine import health

        test = health
    result = test(account)
    if result.get("ok"):
        return {"ok": True, "account_id": account.id, "created": created, "message": f"Signed in to {email}. The password is saved in Windows Credential Manager."}
    category = result.get("error") or "unknown"
    return {"ok": False, "account_id": account.id, "created": created, "error": category,
            "message": ERROR_HELP.get(category, f"Sign-in did not work ({category}).") + " The account is saved; just re-enter the password to retry."}


def run() -> int:
    import tkinter as tk
    from tkinter import ttk

    root = tk.Tk()
    root.title("Agent OS - Add mail account")
    root.resizable(False, False)
    frame = ttk.Frame(root, padding=16)
    frame.grid(sticky="nsew")
    frame.columnconfigure(1, weight=1)

    provider = tk.StringVar(value="earthlink")
    email = tk.StringVar()
    password = tk.StringVar()
    status = tk.StringVar(value="Mail is read-only: Agent OS can search your mail but never sends, deletes, or moves anything.")

    ttk.Label(frame, text="Mail service").grid(row=0, column=0, sticky="w", pady=4)
    choices = ttk.Frame(frame)
    choices.grid(row=0, column=1, sticky="w")
    for value, text in (("earthlink", "EarthLink"), ("icloud", "iCloud")):
        ttk.Radiobutton(choices, text=text, value=value, variable=provider).pack(side="left", padx=(0, 12))

    ttk.Label(frame, text="Email address").grid(row=1, column=0, sticky="w", pady=4)
    email_entry = ttk.Entry(frame, textvariable=email, width=38)
    email_entry.grid(row=1, column=1, sticky="ew")

    password_label = ttk.Label(frame)
    password_label.grid(row=2, column=0, sticky="w", pady=4)
    password_entry = ttk.Entry(frame, textvariable=password, show="•", width=38)
    password_entry.grid(row=2, column=1, sticky="ew")
    shown = tk.BooleanVar(value=False)
    ttk.Checkbutton(frame, text="Show password", variable=shown,
                    command=lambda: password_entry.configure(show="" if shown.get() else "•")).grid(row=3, column=1, sticky="w")

    hint = ttk.Label(frame, wraplength=380, foreground="#555")
    hint.grid(row=4, column=0, columnspan=2, sticky="w", pady=(6, 8))

    def on_provider(*_: Any) -> None:
        defaults = accounts_lib.PROVIDERS[provider.get()]
        password_label.configure(text=defaults["credential_label"].replace("mailbox ", "").capitalize())
        hint.configure(text=defaults["credential_help"])

    provider.trace_add("write", on_provider)
    on_provider()

    buttons = ttk.Frame(frame)
    buttons.grid(row=5, column=0, columnspan=2, sticky="e")
    save_button = ttk.Button(buttons, text="Save and test")
    sync_button = ttk.Button(buttons, text="Get my mail now")
    close_button = ttk.Button(buttons, text="Close", command=root.destroy)
    save_button.pack(side="left", padx=4)
    close_button.pack(side="left", padx=4)

    ttk.Label(frame, textvariable=status, wraplength=380).grid(row=6, column=0, columnspan=2, sticky="w", pady=(12, 0))

    def in_background(work: Callable[[], Any], done: Callable[[Any], None]) -> None:
        def target() -> None:
            try:
                outcome = work()
            except Exception as exc:  # shown to the user; never contains the secret
                outcome = {"ok": False, "message": f"Something went wrong: {type(exc).__name__}: {exc}"}
            root.after(0, lambda: done(outcome))

        threading.Thread(target=target, daemon=True).start()

    def on_save() -> None:
        chosen, address, secret = provider.get(), email.get(), password.get()
        save_button.configure(state="disabled")
        status.set("Saving and signing in...")

        def done(outcome: dict[str, Any]) -> None:
            save_button.configure(state="normal")
            status.set(outcome["message"])
            if outcome.get("account_id"):
                password.set("")
            if outcome.get("ok"):
                sync_button.pack(side="left", padx=4, before=close_button)
                save_button.configure(text="Add another")
                email.set("")
                status.set(outcome["message"] + " Press \"Get my mail now\" to download recent mail, or add another account.")

        in_background(lambda: save_account(chosen, address, secret), done)

    def on_sync() -> None:
        from . import sync

        sync_button.configure(state="disabled")
        status.set("Getting your newest mail. This can take a minute...")

        def done(outcome: dict[str, Any]) -> None:
            sync_button.configure(state="normal")
            if "accounts" in outcome:
                new = outcome.get("indexed_new", 0)
                status.set(f"Done. {new} new message{'s' if new != 1 else ''} indexed." if outcome.get("complete") else
                           f"Partly done ({new} new). Some folders had problems; try again later.")
            else:
                status.set(outcome.get("message", "Sync finished."))

        in_background(lambda: sync(), done)

    save_button.configure(command=on_save)
    sync_button.configure(command=on_sync)
    root.bind("<Return>", lambda _event: on_save())
    email_entry.focus_set()
    root.mainloop()
    return 0
