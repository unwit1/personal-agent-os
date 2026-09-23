"""Mail accounts, provider defaults, and local secrets.

Account definitions live in ``.agent-local/mail/accounts.json`` (gitignored).
They hold metadata only: the credential itself is stored in the OS keyring
(Windows Credential Manager, macOS Keychain, Secret Service) under
``personal-agent-os/mail`` with the account ID as the key, or read from an
account-specific environment variable for headless/test use. Nothing in this
module returns, logs, or serializes a secret.

Every account is read-only in this phase; there is no setting to change that.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from ..timestamps import utc_now_iso as now
from . import config

SECRET_SERVICE = "personal-agent-os/mail"
LEGACY_SECRET_SERVICE = "personal-agent-os/icloud-mail"
LEGACY_ENV = "ICLOUD_APP_PASSWORD"
LEGACY_ACCOUNT_ID = "icloud"
_ACCOUNT_ID = re.compile(r"^[a-z0-9][a-z0-9-]{1,39}$")

# Provider defaults (normal configuration metadata, verified 2026-09-23).
# SMTP settings are recorded for a future, approval-gated send design only;
# nothing in Phase 1 connects to them.
PROVIDERS: dict[str, dict[str, Any]] = {
    "icloud": {
        "label": "iCloud Mail",
        "imap_host": "imap.mail.me.com",
        "imap_port": 993,
        "security": "ssl",
        "username": "email",
        "credential_label": "Apple app-specific password",
        "credential_help": "Create one at account.apple.com > Sign-In and Security > App-Specific Passwords. Never enter your Apple Account password here.",
        "future_smtp": {"host": "smtp.mail.me.com", "port": 587, "security": "starttls"},
    },
    "earthlink": {
        "label": "EarthLink Mail",
        "imap_host": "imap.earthlink.net",
        "imap_port": 993,
        "security": "ssl",
        "username": "email",
        "credential_label": "EarthLink mailbox password",
        "credential_help": "The password you use to sign in to this EarthLink mailbox.",
        "future_smtp": {"host": "smtpauth.earthlink.net", "port": 587, "security": "starttls"},
        # Addresses on your own domain hosted by EarthLink (EarthLink Business
        # "hosting"). mail.<yourdomain> points at the same servers, but their
        # TLS certificate names only the hosting.earthlink.net hosts.
        "hosted_imap_host": "securemail.hosting.earthlink.net",
        "hosted_future_smtp": {"host": "smtpauth.hosting.earthlink.net", "port": 587, "security": "starttls"},
        "own_domains": ["earthlink.net", "mindspring.com", "peoplepc.com", "ix.netcom.com", "netcom.com"],
    },
}
SECURITY_MODES = ("ssl", "starttls")


def default_server(provider: str, email: str) -> tuple[str, int, str]:
    """(host, port, security) to suggest for this address."""
    defaults = PROVIDERS[provider]
    domain = str(email or "").rpartition("@")[2].strip().lower()
    host = defaults["imap_host"]
    if defaults.get("hosted_imap_host") and domain and domain not in defaults.get("own_domains", []):
        host = defaults["hosted_imap_host"]
    return host, int(defaults["imap_port"]), defaults["security"]


class AccountError(ValueError):
    pass


@dataclass
class Account:
    id: str
    provider: str
    email: str
    label: str = ""
    username: str | None = None
    enabled: bool = True
    folders: list[str] = field(default_factory=lambda: ["INBOX"])
    exclude_folders: list[str] = field(default_factory=list)
    overlap: int = 100
    imap_host: str | None = None
    imap_port: int | None = None
    security: str | None = None
    legacy: bool = False
    created_at: str | None = None

    @property
    def read_only(self) -> bool:
        return True

    @property
    def defaults(self) -> dict[str, Any]:
        return PROVIDERS[self.provider]

    @property
    def host(self) -> str:
        return self.imap_host or self.defaults["imap_host"]

    @property
    def port(self) -> int:
        return int(self.imap_port or self.defaults["imap_port"])

    @property
    def tls(self) -> str:
        return self.security or self.defaults["security"]

    @property
    def login_name(self) -> str:
        return self.username or self.email

    def public(self) -> dict[str, Any]:
        """Serializable view; never contains a secret."""
        available, source = credential_status(self)
        return {
            "account_id": self.id,
            "provider": self.provider,
            "label": self.label or self.defaults["label"],
            "email": self.email,
            "enabled": self.enabled,
            "read_only": True,
            "imap": {"host": self.host, "port": self.port, "security": self.tls},
            "folders": list(self.folders),
            "exclude_folders": list(self.exclude_folders),
            "credential_available": available,
            "credential_source": source,
            "legacy": self.legacy,
        }


def check_account_id(value: str) -> str:
    text = str(value or "").strip().lower()
    if not _ACCOUNT_ID.match(text):
        raise AccountError("account id: 2-40 characters, lowercase letters, digits and dashes, e.g. work-earthlink")
    return text


# ---------------------------------------------------------------------------
# Config file
# ---------------------------------------------------------------------------


def _read(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {"schema_version": 1, "accounts": []}
    except json.JSONDecodeError as exc:
        raise AccountError(f"{path} is not valid JSON: {exc.msg}") from exc
    if not isinstance(data, dict) or not isinstance(data.get("accounts"), list):
        raise AccountError(f"{path} must contain an accounts list")
    return data


def _write(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(data, indent=2), encoding="utf-8")
    temporary.replace(path)


def _from_dict(item: dict[str, Any]) -> Account:
    provider = str(item.get("provider") or "")
    if provider not in PROVIDERS:
        raise AccountError(f"unknown mail provider {provider!r}; supported: {', '.join(sorted(PROVIDERS))}")
    known = {name for name in Account.__dataclass_fields__}
    values = {key: value for key, value in item.items() if key in known}
    values["id"] = check_account_id(values.get("id", ""))
    return Account(**values)


def load_accounts(path: Path | None = None) -> list[Account]:
    target = path or config.ACCOUNTS_FILE
    if not target.exists():
        migrate_legacy_config(target)
    return [_from_dict(item) for item in _read(target)["accounts"]]


def get_account(account_id: str, path: Path | None = None) -> Account:
    wanted = check_account_id(account_id)
    for account in load_accounts(path):
        if account.id == wanted:
            return account
    raise AccountError(f"no mail account {wanted!r}; add one with: agent-os mail account add")


def save_accounts(accounts: list[Account], path: Path | None = None) -> None:
    items = []
    for account in accounts:
        data = asdict(account)
        items.append({key: value for key, value in data.items() if value not in (None, [], "")} | {"enabled": account.enabled, "legacy": account.legacy})
    _write(path or config.ACCOUNTS_FILE, {"schema_version": 1, "accounts": items})


def add_account(provider: str, account_id: str, email: str, *, label: str = "", username: str | None = None, folders: list[str] | None = None,
                imap_host: str | None = None, imap_port: int | None = None, security: str | None = None, path: Path | None = None) -> Account:
    if provider not in PROVIDERS:
        raise AccountError(f"unknown mail provider {provider!r}; supported: {', '.join(sorted(PROVIDERS))}")
    email = str(email or "").strip()
    if "@" not in email:
        raise AccountError("enter the full email address")
    if security not in (None, *SECURITY_MODES):
        raise AccountError(f"security must be one of {', '.join(SECURITY_MODES)}")
    accounts = load_accounts(path)
    identifier = check_account_id(account_id)
    if any(account.id == identifier for account in accounts):
        raise AccountError(f"a mail account {identifier!r} already exists")
    account = Account(id=identifier, provider=provider, email=email, label=label, username=username or None, folders=folders or ["INBOX"],
                      imap_host=imap_host or None, imap_port=imap_port or None, security=security or None, created_at=now())
    save_accounts([*accounts, account], path)
    return account


def update_account(account_id: str, path: Path | None = None, **changes: Any) -> Account:
    accounts = load_accounts(path)
    identifier = check_account_id(account_id)
    for index, account in enumerate(accounts):
        if account.id == identifier:
            allowed = {"label", "username", "enabled", "folders", "exclude_folders", "overlap", "imap_host", "imap_port", "security"}
            unknown = set(changes) - allowed
            if unknown:
                raise AccountError(f"cannot change {sorted(unknown)} (read-only mode and identity are fixed)")
            if changes.get("security") not in (None, *SECURITY_MODES):
                raise AccountError(f"security must be one of {', '.join(SECURITY_MODES)}")
            for key, value in changes.items():
                setattr(account, key, value)
            accounts[index] = account
            save_accounts(accounts, path)
            return account
    raise AccountError(f"no mail account {identifier!r}")


def remove_account(account_id: str, path: Path | None = None) -> None:
    identifier = check_account_id(account_id)
    accounts = load_accounts(path)
    remaining = [account for account in accounts if account.id != identifier]
    if len(remaining) == len(accounts):
        raise AccountError(f"no mail account {identifier!r}")
    save_accounts(remaining, path)


def migrate_legacy_config(target: Path | None = None) -> Account | None:
    """Turn the single-account ``icloud.json`` into an ``icloud`` account.

    Explicit and reversible: the old file is kept, and deleting
    ``accounts.json`` returns to the legacy state. The legacy keyring entry and
    ``ICLOUD_APP_PASSWORD`` keep working for this account.
    """
    target = target or config.ACCOUNTS_FILE
    legacy = config.LEGACY_CONFIG
    if target.exists() or not legacy.exists():
        return None
    try:
        email = str(json.loads(legacy.read_text(encoding="utf-8")).get("email") or "")
    except (OSError, json.JSONDecodeError):
        return None
    if "@" not in email:
        return None
    account = Account(id=LEGACY_ACCOUNT_ID, provider="icloud", email=email, label="iCloud", legacy=True, created_at=now())
    save_accounts([account], target)
    return account


# ---------------------------------------------------------------------------
# Secrets
# ---------------------------------------------------------------------------


def env_name(account_id: str) -> str:
    return "AGENT_OS_MAIL_SECRET_" + re.sub(r"[^A-Z0-9]", "_", account_id.upper())


def _keyring():
    try:
        import keyring  # type: ignore

        return keyring
    except ImportError:
        return None


def _lookup(account: Account) -> tuple[str | None, str | None]:
    value = os.environ.get(env_name(account.id))
    if value:
        return value, "environment"
    store = _keyring()
    if store is not None:
        try:
            value = store.get_password(SECRET_SERVICE, account.id)
        except Exception:
            value = None
        if value:
            return value, "keyring"
    if account.legacy:
        value = os.environ.get(LEGACY_ENV)
        if value:
            return value, "legacy-environment"
        if store is not None:
            try:
                value = store.get_password(LEGACY_SECRET_SERVICE, account.email)
            except Exception:
                value = None
            if value:
                return value, "legacy-keyring"
    return None, None


def credential_status(account: Account) -> tuple[bool, str | None]:
    value, source = _lookup(account)
    return bool(value), source


def get_secret(account: Account) -> str:
    value, _ = _lookup(account)
    if not value:
        raise AccountError(
            f"no credential for mail account {account.id}; run: agent-os mail account credential {account.id} "
            f"(or set {env_name(account.id)} locally)"
        )
    return value


def set_secret(account_id: str, secret: str) -> str:
    """Store a credential in the OS keyring. Returns where it went.

    Surrounding spaces and line breaks are removed: a pasted password often
    carries a trailing newline, which IMAP servers reject."""
    secret = (secret or "").strip()
    if not secret:
        raise AccountError("empty credential")
    if any(ch in secret for ch in "\r\n\0"):
        raise AccountError("the password contains a line break; enter it on one line")
    store = _keyring()
    if store is None:
        raise AccountError(f"the keyring package is not installed; set {env_name(account_id)} in your local environment instead")
    store.set_password(SECRET_SERVICE, check_account_id(account_id), secret)
    return "keyring"


def delete_secret(account_id: str) -> bool:
    store = _keyring()
    if store is None:
        return False
    try:
        store.delete_password(SECRET_SERVICE, check_account_id(account_id))
        return True
    except Exception:
        return False
