"""Send transport for the Executive window: SMTP submission plus an IMAP Sent copy.

Importable without network. Nothing here uses Outlook, COM or the Applicant
Dashboard's email_sender. ``send`` never raises for delivery or configuration
problems: it returns ``SendResult(sent=False, error="NOT SENT: ...")``. Error
text names the stage and never contains a credential, raw server text or the body.
"""

from __future__ import annotations

import imaplib
import re
import smtplib
import ssl
import time
from dataclasses import dataclass
from email.message import EmailMessage
from email.utils import format_datetime, make_msgid
from datetime import datetime, timezone
from typing import Any, Callable, Protocol

TIMEOUT = 30
SENT_FALLBACKS = ("Sent", "Sent Items", "Sent Mail", "INBOX.Sent")
SENT_WARNING = "Sent, but the copy could not be saved to the Sent folder"


@dataclass(frozen=True)
class SendResult:
    sent: bool
    message_id: str | None
    error: str | None = None
    warning: str | None = None


class SendTransport(Protocol):
    def send(self, to: str, subject: str, body: str, *,
             from_account: str | None = None, in_reply_to: str | None = None) -> SendResult: ...


def _fail(reason: str) -> SendResult:
    return SendResult(False, None, f"NOT SENT: {reason}")


def _default_smtp(host: str, port: int, security: str, context: ssl.SSLContext, timeout: float):
    if security == "ssl":
        return smtplib.SMTP_SSL(host, port, timeout=timeout, context=context)
    client = smtplib.SMTP(host, port, timeout=timeout)
    client.ehlo()
    client.starttls(context=context)
    client.ehlo()
    return client


def _default_imap(host: str, port: int, security: str, context: ssl.SSLContext, timeout: float):
    if security == "ssl":
        return imaplib.IMAP4_SSL(host, port, ssl_context=context, timeout=timeout)
    client = imaplib.IMAP4(host, port, timeout=timeout)
    client.starttls(ssl_context=context)
    return client


def _default_secret(account: Any) -> str:
    from ...mail import accounts as mail_accounts

    return mail_accounts.get_secret(account)


def _special_use_sent(listing: Any) -> str | None:
    for raw in listing or []:
        line = raw.decode("utf-8", "replace") if isinstance(raw, bytes) else str(raw)
        if "\\Sent" in line:
            match = re.search(r'"((?:[^"\\]|\\.)*)"\s*$', line) or re.search(r"(\S+)\s*$", line)
            if match:
                return match.group(1)
    return None


class SmtpImapTransport:
    def __init__(self, *, accounts: Any = None, secret_lookup: Callable[[Any], str] | None = None,
                 smtp_factory: Callable[..., Any] | None = None, imap_factory: Callable[..., Any] | None = None) -> None:
        self._accounts = accounts
        self._secret = secret_lookup or _default_secret
        self._smtp = smtp_factory or _default_smtp
        self._imap = imap_factory or _default_imap

    def _load(self) -> list[Any]:
        if self._accounts is None:
            from ...mail import accounts as mail_accounts

            return list(mail_accounts.load_accounts())
        return list(self._accounts() if callable(self._accounts) else self._accounts)

    def _default_account(self, enabled: list[Any]) -> Any | None:
        work = [a for a in enabled if a.mail_scope == "work"]
        for account in work:
            if account.provider == "earthlink":
                return account
        return work[0] if work else None

    def from_accounts(self) -> list[dict[str, Any]]:
        try:
            enabled = [a for a in self._load() if a.enabled]
        except Exception:
            return []
        default = self._default_account(enabled)
        return [
            {"account_id": a.id, "label": a.label or a.defaults["label"], "email": a.email, "default": a is default}
            for a in enabled
        ]

    def _smtp_settings(self, account: Any) -> tuple[str, int, str]:
        defaults = account.defaults
        domain = str(account.email).rpartition("@")[2].strip().lower()
        hosted = defaults.get("hosted_future_smtp")
        if hosted and domain and domain not in defaults.get("own_domains", []):
            base = hosted
        else:
            base = defaults["future_smtp"]
        host = getattr(account, "smtp_host", None) or base["host"]
        port = int(getattr(account, "smtp_port", None) or base["port"])
        security = getattr(account, "smtp_security", None) or ("ssl" if port == 465 else base["security"])
        return host, port, security

    def send(self, to: str, subject: str, body: str, *,
             from_account: str | None = None, in_reply_to: str | None = None) -> SendResult:
        try:
            return self._send(to, subject, body, from_account, in_reply_to)
        except Exception as exc:  # never raise to the caller
            return _fail(type(exc).__name__)

    def _send(self, to, subject, body, from_account, in_reply_to) -> SendResult:
        to, subject, body = str(to or "").strip(), str(subject or "").strip(), str(body or "")
        if not to or not subject or not body.strip():
            return _fail("To, Subject and Body are all required")
        if any(ch in value for value in (to, subject, in_reply_to or "") for ch in "\r\n"):
            return _fail("line breaks are not allowed in To, Subject or In-Reply-To")
        enabled = [a for a in self._load() if a.enabled]
        if from_account:
            account = next((a for a in enabled if a.id == from_account), None)
            if account is None:
                return _fail(f"unknown mail account {from_account}")
        else:
            account = self._default_account(enabled)
            if account is None:
                return _fail("no default mail account is configured")
        try:
            secret = self._secret(account)
        except Exception:
            secret = None
        if not secret:
            return _fail(f"missing credential for account {account.id}")

        message = EmailMessage()
        message["From"] = account.email
        message["To"] = to
        message["Subject"] = subject
        message["Date"] = format_datetime(datetime.now(timezone.utc))
        message_id = make_msgid(domain=str(account.email).rpartition("@")[2] or None)
        message["Message-ID"] = message_id
        if in_reply_to:
            message["In-Reply-To"] = in_reply_to
            message["References"] = in_reply_to
        message.set_content(body, charset="utf-8")

        context = ssl.create_default_context()
        host, port, security = self._smtp_settings(account)
        client = None
        try:
            client = self._smtp(host, port, security, context, TIMEOUT)
            client.login(account.login_name, secret)
            client.send_message(message)
        except smtplib.SMTPAuthenticationError:
            return _fail("SMTP authentication failed")
        except smtplib.SMTPRecipientsRefused:
            return _fail("recipient refused")
        except (smtplib.SMTPException, OSError):
            return _fail("SMTP connection failed")
        finally:
            if client is not None:
                try:
                    client.quit()
                except Exception:
                    pass

        warning = None
        try:
            self._append_sent(account, secret, message.as_bytes(), context)
        except Exception:
            warning = SENT_WARNING
        return SendResult(True, message_id, None, warning)

    def _append_sent(self, account: Any, secret: str, data: bytes, context: ssl.SSLContext) -> None:
        from ...mail import accounts as mail_accounts

        host, port, security = account.host, account.port, account.tls
        if not account.imap_host:
            host, port, security = mail_accounts.default_server(account.provider, account.email)
            port = account.imap_port or port
            security = account.security or security
        client = self._imap(host, int(port), security, context, TIMEOUT)
        try:
            client.login(account.login_name, secret)
            folder = None
            try:
                status, listing = client.list()
                if status == "OK":
                    folder = _special_use_sent(listing)
            except Exception:
                folder = None
            candidates = [folder] if folder else list(SENT_FALLBACKS)
            last = None
            for name in candidates:
                status, _ = client.append(f'"{name}"', "\\Seen", imaplib.Time2Internaldate(time.time()), data)
                if status == "OK":
                    return
                last = status
            raise RuntimeError(f"append failed: {last}")
        finally:
            try:
                client.logout()
            except Exception:
                pass


class FakeTransport:
    """Records sends; opens no sockets."""

    def __init__(self, results: list[SendResult] | None = None, *, fail_with: str | None = None) -> None:
        self.calls: list[dict[str, Any]] = []
        self._results = list(results or [])
        self._fail_with = fail_with

    def from_accounts(self) -> list[dict[str, Any]]:
        return [{"account_id": "fake-work", "label": "Fake work account", "email": "work@example.invalid", "default": True}]

    def send(self, to: str, subject: str, body: str, *,
             from_account: str | None = None, in_reply_to: str | None = None) -> SendResult:
        self.calls.append({"to": to, "subject": subject, "body": body,
                           "from_account": from_account, "in_reply_to": in_reply_to})
        if self._results:
            return self._results.pop(0)
        if self._fail_with:
            return _fail(self._fail_with)
        return SendResult(True, f"<fake-{len(self.calls)}@example.invalid>")


TRANSPORT_FACTORY: Callable[[], SendTransport] | None = None


def default_transport() -> SendTransport:
    if TRANSPORT_FACTORY is not None:
        return TRANSPORT_FACTORY()
    return SmtpImapTransport()
