"""Parse RFC822 messages into normalized fields, fingerprints and attachment
metadata. Pure functions; no I/O except what the caller passes in."""

from __future__ import annotations

import email
import hashlib
import html
import re
from dataclasses import dataclass, field
from email.header import decode_header
from email.message import Message
from email.utils import getaddresses, parsedate_to_datetime
from typing import Any

MAX_BODY_CHARS = 200_000
MAX_ATTACHMENT_TEXT = 20_000
TEXT_ATTACHMENT_TYPES = frozenset({"text/plain", "text/csv", "text/markdown", "text/html"})
_MSGID = re.compile(r"<([^<>\s]+)>")
_SUBJECT_PREFIX = re.compile(r"^\s*((re|fw|fwd|aw|sv|antw)\s*(\[\d+\])?\s*:\s*)+", re.IGNORECASE)
_TAGS = re.compile(r"<[^>]+>")
_SPACE = re.compile(r"\s+")


def decode(value: str | None) -> str:
    if not value:
        return ""
    parts = []
    for chunk, charset in decode_header(value):
        if isinstance(chunk, bytes):
            try:
                parts.append(chunk.decode(charset or "utf-8", errors="replace"))
            except LookupError:
                parts.append(chunk.decode("utf-8", errors="replace"))
        else:
            parts.append(chunk)
    return "".join(parts).strip()


def _payload_text(part: Message) -> str:
    data = part.get_payload(decode=True) or b""
    try:
        return data.decode(part.get_content_charset() or "utf-8", errors="replace")
    except LookupError:
        return data.decode("utf-8", errors="replace")


def html_to_text(value: str) -> str:
    text = re.sub(r"(?is)<(script|style).*?</\1>", " ", value)
    text = re.sub(r"(?i)<br\s*/?>|</p>|</div>|</li>", "\n", text)
    return html.unescape(_TAGS.sub(" ", text))


def body_text(msg: Message) -> str:
    """The text/plain body, or text from text/html when there is no plain part."""
    plain = html_part = None
    for part in msg.walk() if msg.is_multipart() else [msg]:
        if part.is_multipart() or _is_attachment(part):
            continue
        kind = part.get_content_type()
        if kind == "text/plain" and plain is None:
            plain = _payload_text(part)
        elif kind == "text/html" and html_part is None:
            html_part = _payload_text(part)
    text = plain if plain is not None else (html_to_text(html_part) if html_part else "")
    return text[:MAX_BODY_CHARS]


def _is_attachment(part: Message) -> bool:
    disposition = (part.get("Content-Disposition") or "").lower()
    return "attachment" in disposition or (bool(part.get_filename()) and not part.get_content_type().startswith("multipart/"))


def normalize_message_id(value: str | None) -> str | None:
    match = _MSGID.search(value or "")
    text = match.group(1) if match else (value or "").strip().strip("<>")
    return text.lower() if text and "@" in text else None


def message_ids(value: str | None) -> list[str]:
    return [item.lower() for item in _MSGID.findall(value or "") if "@" in item]


def normalize_subject(value: str) -> str:
    return _SPACE.sub(" ", _SUBJECT_PREFIX.sub("", value or "")).strip().casefold()


def _addresses(value: str) -> str:
    return ", ".join(address.lower() for _, address in getaddresses([value]) if address)


def _date(value: str) -> str | None:
    try:
        parsed = parsedate_to_datetime(value)
    except (TypeError, ValueError, IndexError):
        return None
    if parsed is None:
        return None
    if parsed.tzinfo is None:
        from datetime import timezone

        parsed = parsed.replace(tzinfo=timezone.utc)
    from datetime import timezone

    return parsed.astimezone(timezone.utc).isoformat()


@dataclass
class Attachment:
    filename: str
    mime_type: str
    size: int
    content_hash: str
    text: str | None = None


@dataclass
class ParsedMessage:
    subject: str
    sender: str
    to: str
    cc: str
    date_header: str
    date_utc: str | None
    rfc_message_id: str | None
    in_reply_to: str | None
    references: list[str]
    body: str
    attachments: list[Attachment] = field(default_factory=list)
    content_hash: str = ""
    composite_key: str = ""
    raw_hash: str = ""

    def addresses(self) -> dict[str, str]:
        return {"sender": _addresses(self.sender), "to": _addresses(self.to), "cc": _addresses(self.cc)}


def _attachments(msg: Message) -> list[Attachment]:
    found = []
    for part in msg.walk():
        if part.is_multipart() or not _is_attachment(part):
            continue
        data = part.get_payload(decode=True) or b""
        kind = part.get_content_type()
        text = None
        if kind in TEXT_ATTACHMENT_TYPES:
            decoded = _payload_text(part)
            text = (html_to_text(decoded) if kind == "text/html" else decoded)[:MAX_ATTACHMENT_TEXT]
        found.append(Attachment(decode(part.get_filename()) or "(unnamed)", kind, len(data), hashlib.sha256(data).hexdigest(), text))
    return found


def _norm(text: str) -> str:
    return _SPACE.sub(" ", (text or "").strip()).casefold()


def parse(raw: bytes) -> ParsedMessage:
    msg = email.message_from_bytes(raw)
    subject, sender = decode(msg.get("Subject")), decode(msg.get("From"))
    to, cc = decode(msg.get("To")), decode(msg.get("Cc"))
    date_header = decode(msg.get("Date"))
    parsed = ParsedMessage(
        subject=subject,
        sender=sender,
        to=to,
        cc=cc,
        date_header=date_header,
        date_utc=_date(date_header),
        rfc_message_id=normalize_message_id(msg.get("Message-ID")),
        in_reply_to=normalize_message_id(msg.get("In-Reply-To")),
        references=message_ids(msg.get("References")),
        body=body_text(msg),
        attachments=_attachments(msg),
        raw_hash=hashlib.sha256(raw).hexdigest(),
    )
    addresses = parsed.addresses()
    # Normalized content: what a person would call "the same email", whatever
    # the transport added (Received headers, flags, folder).
    content = "\n".join([_norm(subject), addresses["sender"], addresses["to"], addresses["cc"], parsed.date_utc or _norm(date_header), _norm(parsed.body)])
    parsed.content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
    parsed.composite_key = hashlib.sha256("\n".join([(parsed.date_utc or "")[:16], addresses["sender"], addresses["to"], normalize_subject(subject), _norm(parsed.body)[:2000]]).encode("utf-8")).hexdigest()
    return parsed


def summary(parsed: ParsedMessage) -> dict[str, Any]:
    return {"subject": parsed.subject, "from": parsed.sender, "date": parsed.date_utc or parsed.date_header, "message_id": parsed.rfc_message_id}
