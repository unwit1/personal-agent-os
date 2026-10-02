"""IMAP mover for organization plans: MOVE, or COPY plus keyword flag. Never deletes.

Implements ``organize_apply.Mover`` over an injected ``connect(account)`` that
returns an authenticated imaplib-like client. Nothing here issues STORE
\\Deleted or EXPUNGE, so every operation leaves a copy that can be undone.
"""
from __future__ import annotations

import re
from typing import Any, Callable

KEYWORD = "$AgentOSOrganized"
_COPYUID = re.compile(rb"COPYUID\s+(\d+)\s+([\d:,]+)\s+([\d:,]+)", re.I)
_UIDVALIDITY = re.compile(rb"UIDVALIDITY\s+(\d+)", re.I)
_LIST_NAME = re.compile(rb'\)\s+(?:"(?:[^"\\]|\\.)*"|NIL)\s+(.*)$')


class MoveRefused(RuntimeError):
    pass


def _quote(name: str) -> str:
    return '"' + name.replace("\\", "\\\\").replace('"', '\\"') + '"'


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
    def _check(self, result: Any, what: str) -> list[Any]:
        typ, data = result[0], result[1]
        if str(typ).upper() != "OK":
            raise RuntimeError(f"IMAP {what} failed: {typ}")
        return list(data or [])

    def _capability_set(self) -> set[str]:
        if self._caps is None:
            data = self._check(self.client.capability(), "CAPABILITY")
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

    def ensure_folder(self, logical_name: str) -> str:
        names = set()
        for item in self._check(self.client.list(), "LIST"):
            match = _LIST_NAME.search(_as_bytes(item))
            if match:
                names.add(match.group(1).strip().strip(b'"').decode("utf-8", "replace"))
        if logical_name not in names:
            self._check(self.client.create(_quote(logical_name)), "CREATE")
            try:
                self.client.subscribe(_quote(logical_name))
            except Exception:
                pass  # subscription is cosmetic
        return logical_name

    def select(self, mailbox: str) -> str:
        self._clear_untagged()
        self._check(self.client.select(_quote(mailbox), readonly=False), "SELECT")
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
        data = self._check(self.client.uid(
            "FETCH", self._uid_set(uids), "(BODY.PEEK[HEADER.FIELDS (MESSAGE-ID)])"), "FETCH")
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
        command = "MOVE" if "MOVE" in self._capability_set() else "COPY"
        self._clear_untagged()
        data = self._check(self.client.uid(command, self._uid_set(uids), _quote(target)), command)
        mapping = self._copyuid(data)
        return {str(u): mapping.get(str(u)) for u in uids}

    def copy_flag(self, uids: list[str], target: str) -> dict[str, str | None]:
        if not uids:
            return {}
        self._clear_untagged()
        data = self._check(self.client.uid("COPY", self._uid_set(uids), _quote(target)), "COPY")
        mapping = self._copyuid(data)
        self._check(self.client.uid("STORE", self._uid_set(uids), "+FLAGS.SILENT", f"({KEYWORD})"), "STORE")
        return {str(u): mapping.get(str(u)) for u in uids}

    def unflag(self, uids: list[str]) -> None:
        if uids:
            self._check(self.client.uid("STORE", self._uid_set(uids), "-FLAGS.SILENT", f"({KEYWORD})"), "STORE")

    def find(self, mailbox: str, rfc_message_id: str) -> str | None:
        self.select(mailbox)
        needle = str(rfc_message_id).strip()
        if not needle.startswith("<"):
            needle = f"<{needle}>"
        data = self._check(self.client.uid("SEARCH", "HEADER", "Message-ID", _quote(needle)), "SEARCH")
        found = b" ".join(_as_bytes(d) for d in data).split()
        return found[-1].decode("ascii") if found else None

    def undo(self, entry: dict[str, Any]) -> str | None:
        """Move the destination UID of a journal entry back to its source folder."""
        source, target = entry["from"], entry["to"]
        if entry.get("method") == "copy_flag":
            self.select(source["mailbox"])
            self.unflag([str(source["uid"])])
            return None
        self.select(target["mailbox"])
        uid = str(target.get("uid") or "")
        if not uid:
            return None
        self.move([uid], source["mailbox"])
        return uid

    def close(self) -> None:
        try:
            self.client.logout()  # LOGOUT only: no CLOSE, which would expunge
        except Exception:
            pass
