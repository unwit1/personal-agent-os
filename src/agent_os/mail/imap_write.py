"""IMAP mover for organization plans: MOVE, or COPY plus keyword flag. Never deletes.

Implements ``organize_apply.Mover`` over an injected ``connect(account)`` that
returns an authenticated imaplib-like client. Every client call goes through
``ImapMover._send``, which refuses anything outside a small allow-list, so no
STORE \\Deleted, EXPUNGE, CLOSE, DELETE, RENAME or APPEND can be issued and
every operation leaves a copy that can be undone.
"""
from __future__ import annotations

import imaplib
import re
import ssl
from typing import Any, Callable

from . import accounts as accounts_mod
from .imap import _quote

KEYWORD = "$AgentOSOrganized"
_COPYUID = re.compile(rb"COPYUID\s+(\d+)\s+([\d:,]+)\s+([\d:,]+)", re.I)
_UIDVALIDITY = re.compile(rb"UIDVALIDITY\s+(\d+)", re.I)
_LIST_LINE = re.compile(rb'\)\s+(?:"(?P<delim>(?:[^"\\]|\\.)*)"|NIL)\s+(?P<name>.*)$')
_STORE_FLAGS = {"+FLAGS.SILENT", "-FLAGS.SILENT"}
_ALLOWED = {"CAPABILITY", "LIST", "CREATE", "SUBSCRIBE", "SELECT", "LOGOUT",
            "UID FETCH", "UID SEARCH", "UID MOVE", "UID COPY", "UID STORE"}


class MoveRefused(RuntimeError):
    pass


class WriteViolation(RuntimeError):
    """A command outside the reversible-move allow-list was requested."""


def _as_bytes(item: Any) -> bytes:
    if isinstance(item, tuple):
        item = item[0]
    if isinstance(item, str):
        return item.encode("utf-8", "replace")
    return bytes(item) if isinstance(item, (bytes, bytearray)) else b""


def _expand(spec: bytes) -> list[str]:
    out: list[str] = []
    for part in spec.decode("ascii", "replace").split(","):
        if ":" in part:
            low, high = part.split(":", 1)
            out.extend(str(n) for n in range(int(low), int(high) + 1))
        elif part:
            out.append(part)
    return out


class ImapMover:
    def __init__(self, account: Any, connect: Callable[[Any], Any]) -> None:
        if not getattr(account, "allow_organize", False):
            raise MoveRefused("account is not enabled for moves (allow_organize is off)")
        self.account = account
        self.client = connect(account)
        self.mailbox: str | None = None
        self._caps: set[str] | None = None

    # -- helpers -----------------------------------------------------------
    def _send(self, command: str, *args: Any, **kwargs: Any) -> Any:
        """The only path to the client: refuses everything outside the allow-list."""
        name = " ".join(command.upper().split())
        if name not in _ALLOWED:
            raise WriteViolation(f"IMAP command refused: {name}")
        if name == "UID STORE":
            parts = [str(a) for a in args]
            if len(parts) != 3 or parts[1].upper() not in _STORE_FLAGS or parts[2] != f"({KEYWORD})":
                raise WriteViolation("UID STORE is limited to the organize keyword")
        if name == "UID FETCH" and "PEEK" not in " ".join(str(a) for a in args).upper():
            raise WriteViolation("UID FETCH must use BODY.PEEK")
        if name == "UID MOVE" and hasattr(self.client, "_simple_command"):
            return self.client._simple_command("UID", "MOVE", *args)  # imaplib.uid() rejects MOVE
        if name.startswith("UID "):
            return self.client.uid(name[4:], *args)
        return getattr(self.client, name.lower())(*args, **kwargs)

    def _check(self, result: Any, what: str) -> list[Any]:
        typ, data = result[0], result[1]
        if str(typ).upper() != "OK":
            raise RuntimeError(f"IMAP {what} failed: {typ}")
        return list(data or [])

    def _capability_set(self) -> set[str]:
        if self._caps is None:
            data = self._check(self._send("CAPABILITY"), "CAPABILITY")
            text = b" ".join(_as_bytes(d) for d in data).decode("ascii", "replace").upper()
            self._caps = set(text.split())
        return self._caps

    def _uid_set(self, uids: list[str]) -> str:
        return ",".join(str(int(u)) for u in uids)

    def _copyuid(self, data: list[Any]) -> dict[str, str]:
        blobs = [_as_bytes(d) for d in data]
        untagged = getattr(self.client, "untagged_responses", None) or {}
        for values in untagged.values():
            blobs.extend(_as_bytes(v) for v in values)
        mapping: dict[str, str] = {}
        for blob in blobs:
            match = _COPYUID.search(blob)
            if match:
                mapping.update(zip(_expand(match.group(2)), _expand(match.group(3))))
        return mapping

    def _clear_untagged(self) -> None:
        untagged = getattr(self.client, "untagged_responses", None)
        if isinstance(untagged, dict):
            untagged.clear()

    # -- Mover protocol ----------------------------------------------------
    def capabilities(self, mailbox: str) -> dict[str, Any]:
        flags: list[str] = []
        try:
            _, data = self.client.response("PERMANENTFLAGS")
            for item in data or []:
                match = re.search(rb"\(([^)]*)\)", _as_bytes(item))
                if match:
                    flags.extend(match.group(1).decode("ascii", "replace").split())
        except Exception:
            pass
        return {"move": "MOVE" in self._capability_set(), "permanent_flags": flags}

    def resolve_folder(self, logical_name: str, names: set[str], delimiter: str) -> str:
        """Map a logical ``/``-separated name to the server's real name."""
        if logical_name in names:
            return logical_name
        real = delimiter.join(p for p in logical_name.split("/") if p)
        if not real.upper().startswith("INBOX") and any(n.startswith(f"INBOX{delimiter}") for n in names):
            real = f"INBOX{delimiter}{real}"
        return real

    def ensure_folder(self, logical_name: str) -> str:
        names: set[str] = set()
        delimiter = ""
        for item in self._check(self._send("LIST"), "LIST"):
            match = _LIST_LINE.search(_as_bytes(item))
            if match:
                names.add(match.group("name").strip().strip(b'"').decode("utf-8", "replace"))
                delimiter = delimiter or (match.group("delim") or b"").decode("ascii", "replace")
        delimiter = delimiter or "/"
        real = self.resolve_folder(logical_name, names, delimiter)
        parts = real.split(delimiter)
        for depth in range(1, len(parts) + 1):
            level = delimiter.join(parts[:depth])
            if level in names:
                continue
            typ, data = self._send("CREATE", _quote(level))[:2]
            text = b" ".join(_as_bytes(d) for d in data or []).upper()
            if str(typ).upper() != "OK" and b"ALREADYEXISTS" not in text:
                raise RuntimeError(f"IMAP CREATE failed: {typ}")
            try:
                self._send("SUBSCRIBE", _quote(level))
            except Exception:
                pass  # subscription is cosmetic
        return real

    def select(self, mailbox: str) -> str:
        self._clear_untagged()
        self._check(self._send("SELECT", _quote(mailbox), readonly=False), "SELECT")
        self.mailbox = mailbox
        _, data = self.client.response("UIDVALIDITY")
        for item in data or []:
            raw = _as_bytes(item)
            match = _UIDVALIDITY.search(raw) or re.match(rb"\s*(\d+)", raw)
            if match:
                return match.group(1).decode("ascii")
        return ""

    def message_ids(self, uids: list[str]) -> dict[str, str]:
        out: dict[str, str] = {}
        if not uids:
            return out
        data = self._check(self._send(
            "UID FETCH", self._uid_set(uids), "(BODY.PEEK[HEADER.FIELDS (MESSAGE-ID)])"), "FETCH")
        for item in data:
            if not isinstance(item, tuple):
                continue
            uid = re.search(rb"UID\s+(\d+)", _as_bytes(item[0]), re.I)
            header = re.search(rb"message-id:\s*(\S+)", _as_bytes(item[1]), re.I)
            if uid and header:
                out[uid.group(1).decode()] = header.group(1).decode("utf-8", "replace")
        return out

    def move(self, uids: list[str], target: str) -> dict[str, str | None]:
        if not uids:
            return {}
        if "MOVE" not in self._capability_set():
            raise MoveRefused("server lacks MOVE; use copy_flag so undo cannot duplicate the original")
        self._clear_untagged()
        data = self._check(self._send("UID MOVE", self._uid_set(uids), _quote(target)), "MOVE")
        mapping = self._copyuid(data)
        return {str(u): mapping.get(str(u)) for u in uids}

    def copy_flag(self, uids: list[str], target: str) -> dict[str, str | None]:
        if not uids:
            return {}
        self._clear_untagged()
        data = self._check(self._send("UID COPY", self._uid_set(uids), _quote(target)), "COPY")
        mapping = self._copyuid(data)
        self._check(self._send("UID STORE", self._uid_set(uids), "+FLAGS.SILENT", f"({KEYWORD})"), "STORE")
        return {str(u): mapping.get(str(u)) for u in uids}

    def unflag(self, uids: list[str]) -> None:
        if uids:
            self._check(self._send("UID STORE", self._uid_set(uids), "-FLAGS.SILENT", f"({KEYWORD})"), "STORE")

    def find(self, mailbox: str, rfc_message_id: str) -> str | None:
        self.select(mailbox)
        needle = str(rfc_message_id).strip()
        if not needle.startswith("<"):
            needle = f"<{needle}>"
        data = self._check(self._send("UID SEARCH", "HEADER", "Message-ID", _quote(needle)), "SEARCH")
        found = b" ".join(_as_bytes(d) for d in data).split()
        return found[-1].decode("ascii") if found else None

    def undo(self, entry: dict[str, Any]) -> str | None:
        """Move the destination UID of a journal entry back to its source folder.

        Acts only when the mailbox UIDVALIDITY still matches the journal.
        """
        source, target = entry["from"], entry["to"]
        if entry.get("method") == "copy_flag":
            validity = self.select(source["mailbox"])
            if str(validity) != str(source.get("uidvalidity")):
                return None
            self.unflag([str(source["uid"])])
            return None
        validity = self.select(target["mailbox"])
        if str(validity) != str(target.get("uidvalidity")):
            return None
        uid = str(target.get("uid") or "")
        if not uid:
            return None
        self.move([uid], source["mailbox"])
        return uid

    def close(self) -> None:
        try:
            self._send("LOGOUT")  # LOGOUT only: no CLOSE, which would expunge
        except Exception:
            pass


def _default_connector(account: Any) -> Any:
    context = ssl.create_default_context()
    if account.tls == "starttls":
        client = imaplib.IMAP4(account.host, account.port, timeout=60)
        client.starttls(ssl_context=context)
    else:
        client = imaplib.IMAP4_SSL(account.host, account.port, ssl_context=context, timeout=60)
    client.login(account.login_name, accounts_mod.get_secret(account))
    return client


def connect_write(account: Any, *, factory: Callable[[Any], Any] | None = None) -> ImapMover:
    """Build a mover for an account the operator enabled with allow_organize."""
    return ImapMover(account, factory or _default_connector)
