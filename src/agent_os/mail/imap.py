"""Read-only IMAP access for any provider.

``ReadOnlyIMAP`` wraps an ``imaplib`` client and allows only commands that
cannot change a mailbox: LOGIN, CAPABILITY, LIST, SELECT with readonly (IMAP
EXAMINE), STATUS, UID SEARCH, UID FETCH without a store modifier, LOGOUT.
Anything else raises ``ReadOnlyViolation``. Bodies are fetched with
``BODY.PEEK[]`` so fetching never sets \\Seen, even on a server that ignores
EXAMINE semantics.

Errors are mapped to categories (``auth_failed``, ``connection_failed``,
``timeout``, ``mailbox_unavailable``, ``protocol_error``). Server text is not
passed on: some servers echo the login name, and nothing here may echo a
credential.
"""

from __future__ import annotations

import contextlib
import imaplib
import re
import socket
import ssl
from dataclasses import dataclass, field
from typing import Any, Callable

ALLOWED_UID_COMMANDS = frozenset({"search", "fetch"})
FORBIDDEN_FETCH = re.compile(r"(?i)\bBODY\[|\bRFC822\b(?!\.SIZE|\.HEADER)|\bRFC822\.TEXT\b")
_UIDVALIDITY = re.compile(rb"UIDVALIDITY (\d+)")
_UIDNEXT = re.compile(rb"UIDNEXT (\d+)")
_MODSEQ = re.compile(rb"HIGHESTMODSEQ (\d+)")
_FETCH_ITEM = re.compile(rb"UID (\d+)")
_SIZE = re.compile(rb"RFC822\.SIZE (\d+)")
_INTERNALDATE = re.compile(rb'INTERNALDATE "([^"]+)"')
_FLAGS = re.compile(rb"FLAGS \(([^)]*)\)")
_LIST = re.compile(rb'\((?P<flags>[^)]*)\) (?:"(?P<delim>[^"]*)"|NIL) (?P<name>.+)$')


class ReadOnlyViolation(RuntimeError):
    pass


class MailError(RuntimeError):
    """A sanitized, categorized failure. ``str()`` is safe to show and log."""

    def __init__(self, category: str, detail: str = "") -> None:
        self.category = category
        super().__init__(f"{category}: {detail}" if detail else category)


def categorize(exc: BaseException) -> str:
    if isinstance(exc, MailError):
        return exc.category
    if isinstance(exc, ssl.SSLCertVerificationError):
        return "tls_certificate"
    if isinstance(exc, (socket.timeout, TimeoutError)):
        return "timeout"
    if isinstance(exc, (ssl.SSLError, ConnectionError, socket.gaierror, OSError)) and not isinstance(exc, imaplib.IMAP4.error):
        return "connection_failed"
    if isinstance(exc, imaplib.IMAP4.error):
        text = str(exc).lower()
        return "auth_failed" if any(word in text for word in ("auth", "login", "credential", "password")) else "protocol_error"
    return "protocol_error"


@dataclass
class MailboxInfo:
    name: str
    uidvalidity: str | None
    uidnext: int | None
    highestmodseq: int | None
    exists: int | None


@dataclass
class FetchedRecord:
    uid: int
    raw: bytes | None
    size: int | None
    internal_date: str | None
    flags: str
    extra: dict[str, Any] = field(default_factory=dict)


class ReadOnlyIMAP:
    def __init__(self, client: Any) -> None:
        self._client = client
        self.capabilities: set[str] = set()

    # -- allowed --------------------------------------------------------------

    def login(self, user: str, secret: str) -> None:
        try:
            self._client.login(user, secret)
        except Exception as exc:
            raise MailError(categorize(exc) if categorize(exc) != "protocol_error" else "auth_failed") from None
        self.capabilities = self._capabilities()

    def _capabilities(self) -> set[str]:
        try:
            status, data = self._client.capability()
        except Exception:
            return set()
        if status != "OK" or not data:
            return set()
        return {item.upper() for item in b" ".join(part for part in data if isinstance(part, bytes)).decode("ascii", "replace").split()}

    def list_mailboxes(self) -> list[str]:
        status, data = self._client.list()
        if status != "OK":
            raise MailError("protocol_error", "LIST failed")
        names = []
        for line in data or []:
            if not isinstance(line, bytes):
                continue
            match = _LIST.match(line)
            if not match or b"\\noselect" in match.group("flags").lower():
                continue
            names.append(match.group("name").strip().strip(b'"').decode("utf-8", "replace"))
        return names

    def examine(self, mailbox: str) -> MailboxInfo:
        """SELECT read-only (IMAP EXAMINE)."""
        try:
            status, data = self._client.select(_quote(mailbox), readonly=True)
        except imaplib.IMAP4.error:
            raise MailError("mailbox_unavailable") from None
        if status != "OK":
            raise MailError("mailbox_unavailable")
        response = b" ".join(self._responses("UIDVALIDITY") + self._responses("UIDNEXT") + self._responses("HIGHESTMODSEQ"))
        exists = None
        try:
            exists = int((data or [b"0"])[0])
        except (TypeError, ValueError):
            pass
        return MailboxInfo(
            mailbox,
            _first(_UIDVALIDITY, response, lambda raw: raw.decode("ascii")) or _response_value(self._client, "UIDVALIDITY"),
            _first(_UIDNEXT, response, int) or _to_int(_response_value(self._client, "UIDNEXT")),
            _first(_MODSEQ, response, int) or _to_int(_response_value(self._client, "HIGHESTMODSEQ")),
            exists,
        )

    def _responses(self, name: str) -> list[bytes]:
        try:
            _, data = self._client.response(name)
        except Exception:
            return []
        return [f"{name} ".encode() + (item if isinstance(item, bytes) else str(item).encode()) for item in data or [] if item]

    def uid_search_all(self) -> list[int]:
        status, data = self._client.uid("search", None, "ALL")
        if status != "OK":
            raise MailError("protocol_error", "UID SEARCH failed")
        return sorted(int(item) for item in (data[0] or b"").split() if item.isdigit())

    def fetch(self, uids: list[int], *, body: bool, changed_since: int | None = None) -> list[FetchedRecord]:
        if not uids:
            return []
        items = "(UID RFC822.SIZE INTERNALDATE FLAGS BODY.PEEK[])" if body else "(UID RFC822.SIZE INTERNALDATE FLAGS)"
        modifier = f" (CHANGEDSINCE {int(changed_since)})" if changed_since is not None else ""
        status, data = self._client.uid("fetch", _uid_set(uids), items + modifier)
        if status != "OK":
            raise MailError("protocol_error", "UID FETCH failed")
        return parse_fetch(data or [], default_uid=uids[0] if len(uids) == 1 else None)

    def logout(self) -> None:
        try:
            self._client.logout()
        except Exception:
            pass

    # -- everything else is refused ------------------------------------------

    def __getattr__(self, name: str) -> Any:
        raise ReadOnlyViolation(f"IMAP command {name!r} is not allowed: mail access is read-only")

    def uid(self, command: str, *args: Any) -> Any:
        if command.lower() not in ALLOWED_UID_COMMANDS:
            raise ReadOnlyViolation(f"UID {command.upper()} is not allowed: mail access is read-only")
        if command.lower() == "fetch" and len(args) >= 2 and FORBIDDEN_FETCH.search(str(args[1])) and "PEEK" not in str(args[1]).upper():
            raise ReadOnlyViolation("fetching bodies without PEEK could mark messages read")
        return self._client.uid(command, *args)


def connect(host: str, port: int, *, security: str = "ssl", timeout: float = 60, factory: Callable[..., Any] | None = None) -> ReadOnlyIMAP:
    """TLS is always on and always verified: ``ssl`` wraps the connection from
    the start (usually port 993); ``starttls`` upgrades a plain connection
    before anything else is sent (usually port 143)."""
    try:
        if factory is not None or security == "ssl":
            client = (factory or imaplib.IMAP4_SSL)(host, port, ssl_context=ssl.create_default_context(), timeout=timeout)
        elif security == "starttls":
            client = imaplib.IMAP4(host, port, timeout=timeout)
            try:
                client.starttls(ssl_context=ssl.create_default_context())
            except Exception:
                with contextlib.suppress(Exception):
                    client.shutdown()
                raise
        else:
            raise MailError("protocol_error", f"unknown security mode {security!r}")
    except Exception as exc:
        raise MailError(categorize(exc)) from None
    return ReadOnlyIMAP(client)


def parse_fetch(data: list[Any], default_uid: int | None = None) -> list[FetchedRecord]:
    """``default_uid``: a response that omits the UID item is attributed only
    when exactly one UID was requested."""
    records = []
    for item in data:
        if isinstance(item, tuple):
            meta, payload = item[0], item[1]
        elif isinstance(item, bytes) and _FETCH_ITEM.search(item) and _FLAGS.search(item):
            meta, payload = item, None
        else:
            continue
        uid_match = _FETCH_ITEM.search(meta)
        if not uid_match and default_uid is None:
            continue
        flags = _FLAGS.search(meta)
        records.append(FetchedRecord(
            uid=int(uid_match.group(1)) if uid_match else int(default_uid),
            raw=bytes(payload) if payload is not None else None,
            size=_first(_SIZE, meta, int),
            internal_date=_first(_INTERNALDATE, meta, lambda raw: raw.decode("ascii", "replace")),
            flags=flags.group(1).decode("ascii", "replace") if flags else "",
        ))
    return records


def _uid_set(uids: list[int]) -> str:
    """Compact UID set: 1:5,9,12:14."""
    ordered = sorted(set(uids))
    ranges, start, previous = [], ordered[0], ordered[0]
    for uid in ordered[1:]:
        if uid == previous + 1:
            previous = uid
            continue
        ranges.append(f"{start}:{previous}" if start != previous else str(start))
        start = previous = uid
    ranges.append(f"{start}:{previous}" if start != previous else str(start))
    return ",".join(ranges)


def _quote(mailbox: str) -> str:
    return mailbox if re.fullmatch(r"[A-Za-z0-9_./-]+", mailbox) else '"' + mailbox.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _first(pattern: re.Pattern, data: bytes, convert: Callable[[bytes], Any]) -> Any:
    match = pattern.search(data or b"")
    return convert(match.group(1)) if match else None


def _response_value(client: Any, name: str) -> str | None:
    try:
        _, data = client.response(name)
    except Exception:
        return None
    for item in data or []:
        if item:
            return item.decode() if isinstance(item, bytes) else str(item)
    return None


def _to_int(value: str | None) -> int | None:
    try:
        return int(value) if value is not None else None
    except ValueError:
        return None
