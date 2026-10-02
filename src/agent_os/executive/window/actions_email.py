"""Email actions for the Executive window: reply drafts and sending."""
from __future__ import annotations

import email.utils
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .confirm import window_home
from .registry import register_action

TRANSPORT: Any = None


def _format_eml(to: str, subject: str, body: str, in_reply_to: str | None = None) -> str:
    """Format an email message as EML (RFC 822) text."""
    msg = email.message_from_string("")
    msg["To"] = to
    msg["Subject"] = subject
    msg["Date"] = email.utils.formatdate(localtime=False)
    msg["Message-ID"] = email.utils.make_msgid()
    if in_reply_to:
        msg["In-Reply-To"] = in_reply_to
    msg.set_payload(body)
    return str(msg)


def _save_draft(to: str, subject: str, body: str, in_reply_to: str | None = None) -> str:
    """Save a draft email as an .eml file and return its path."""
    home = window_home()
    drafts_dir = home / "drafts"
    drafts_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    draft_path = drafts_dir / f"draft-{timestamp}.eml"
    eml_content = _format_eml(to, subject, body, in_reply_to)
    draft_path.write_text(eml_content, encoding="utf-8")
    return str(draft_path)


def email_reply_draft(item: dict[str, Any], params: dict[str, Any], *, confirm: bool) -> dict[str, Any]:
    """Draft a reply to a mail thread.

    Item context must contain thread data with messages. Builds reply from the
    first message's sender and subject, optionally using the provided body.
    """
    context = item.get("context", {})
    thread = context.get("thread", {})
    messages = thread.get("messages", [])

    if not messages:
        raise ValueError("Thread context missing messages")

    first_msg = messages[0]
    body = params.get("body", "")

    subject = first_msg.get("subject", "")
    if subject and not subject.lower().startswith("re:"):
        subject = f"Re: {subject}"

    to = first_msg.get("sender", "")
    in_reply_to = first_msg.get("message_id")

    draft = {
        "to": to,
        "subject": subject,
        "in_reply_to": in_reply_to,
        "body": body,
    }

    _save_draft(to, subject, body, in_reply_to)

    return draft


def email_send(item: dict[str, Any], params: dict[str, Any], *, confirm: bool) -> dict[str, Any]:
    """Send an email or return a preview for confirmation.

    Params: to, subject, body, in_reply_to (optional)
    With confirm=False, returns a preview without sending.
    With confirm=True, calls TRANSPORT if available, else saves as draft.
    """
    to = params.get("to", "")
    subject = params.get("subject", "")
    body = params.get("body", "")
    in_reply_to = params.get("in_reply_to")

    if not confirm:
        return {
            "to": to,
            "subject": subject,
            "body": body,
        }

    if TRANSPORT is None:
        draft_path = _save_draft(to, subject, body, in_reply_to)
        return {
            "sent": False,
            "reason": "no outbound mail transport configured",
            "draft_path": draft_path,
        }

    TRANSPORT(to, subject, body, in_reply_to)
    return {"sent": True}


def register(registry: Any) -> None:
    """Register email actions with the given registry."""
    registry.register_action(
        "email.reply_draft",
        "Reply to thread",
        ["mail_thread"],
        email_reply_draft,
        consequential=False,
        description="Draft a reply to a mail thread",
        params_schema={
            "type": "object",
            "properties": {
                "body": {"type": "string", "description": "Reply body text"}
            },
        },
    )
    registry.register_action(
        "email.send",
        "Send email",
        "*",
        email_send,
        consequential=True,
        description="Send an email (requires confirmation)",
        params_schema={
            "type": "object",
            "properties": {
                "to": {"type": "string", "description": "Recipient email address"},
                "subject": {"type": "string", "description": "Email subject"},
                "body": {"type": "string", "description": "Email body"},
                "in_reply_to": {"type": "string", "description": "Message ID to reply to (optional)"},
            },
            "required": ["to", "subject", "body"],
        },
    )
