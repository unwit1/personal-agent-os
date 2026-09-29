"""Windows-friendly credential setup: masked pop-up dialogs -> OS keyring.

``orchestrate secrets setup`` walks the credentials Model Infrastructure can
use, one masked dialog each (tkinter, stdlib). Values go straight to the OS
keyring through secret_refs.store -- on Windows that is Credential Manager,
entries named ``agent-os`` / ``<provider>/<profile>`` -- and are never
printed, logged, written to files or returned. Leaving a dialog empty (or
pressing Cancel) skips that credential. Only presence/source is reported.
"""

from __future__ import annotations

from typing import Any, Callable

from . import secret_refs

# ref -> (label, what it unlocks, where to get it). Keep scopes minimal.
CREDENTIALS: list[dict[str, str]] = [
    {"ref": "secrets://runpod/default", "label": "RunPod API key",
     "why": "Authenticated RunPod inventory now; pod provisioning later, only after you approve a budget with a job hard cap.",
     "where": "RunPod console > Settings > API Keys > Create API Key. Read-only permission is enough until provisioning is approved."},
    {"ref": "secrets://huggingface/default", "label": "Hugging Face access token",
     "why": "Model Research Radar: higher rate limits and metadata for gated repos. Optional; scans work without it.",
     "where": "huggingface.co > Settings > Access Tokens > New token, type 'Read'."},
    {"ref": "secrets://local-abliterated/default", "label": "Your model endpoint's API key",
     "why": "Only if the server you run the abliterated model on requires a key (e.g. vLLM started with --api-key). Skip otherwise.",
     "where": "The key you chose when starting the server. Register the endpoint with: orchestrate model-add ... --secret-ref secrets://local-abliterated/default"},
]


def tk_prompt(title: str, message: str) -> str | None:
    """One masked input dialog; returns None on Cancel/close."""
    import tkinter as tk
    from tkinter import simpledialog

    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    try:
        return simpledialog.askstring(title, message, show="*", parent=root)
    finally:
        root.destroy()


def setup(refs: list[str] | None = None, *, prompt: Callable[[str, str], str | None] = tk_prompt,
          skip_configured: bool = True) -> list[dict[str, Any]]:
    """Prompt for each credential (or only ``refs``); store non-empty values."""
    wanted = [item for item in CREDENTIALS if not refs or item["ref"] in refs]
    wanted += [{"ref": ref, "label": ref, "why": "", "where": ""} for ref in refs or [] if ref not in {item["ref"] for item in CREDENTIALS}]
    results = []
    for item in wanted:
        secret_refs.parse(item["ref"])
        before = secret_refs.status(item["ref"])
        if skip_configured and before["configured"]:
            results.append({**before, "action": "kept (already configured)"})
            continue
        message = f"{item['label']}\n\n{item['why']}\n\nWhere: {item['where']}\n\nStored in Windows Credential Manager as {before['keyring']}.\nLeave empty or press Cancel to skip."
        value = prompt(f"Agent OS - {item['label']}", message)
        if value and value.strip():
            results.append({**secret_refs.store(item["ref"], value), "action": "stored"})
        else:
            results.append({**before, "action": "skipped"})
    return results
