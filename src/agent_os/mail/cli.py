"""`agent-os mail ...` commands.

Credentials are only ever entered at a hidden prompt (never as an argument,
which would land in shell history and process lists) and go straight to the
OS keyring.
"""

from __future__ import annotations

import argparse
import getpass
import json
import sys
from typing import Any, Callable

from . import accounts as accounts_lib
from . import config


def register(commands: argparse._SubParsersAction) -> None:
    mail = commands.add_parser("mail", help="read-only mail: accounts, sync, search (iCloud, EarthLink)")
    sub = mail.add_subparsers(dest="mail_command", required=True)

    accounts_parser = sub.add_parser("accounts", help="list configured mail accounts (no credentials)")
    accounts_parser.add_argument("--scope", choices=config.SCOPES)
    account = sub.add_parser("account", help="add, change or remove a mail account")
    account_sub = account.add_subparsers(dest="account_command", required=True)
    add = account_sub.add_parser("add")
    add.add_argument("--provider", required=True, choices=sorted(accounts_lib.PROVIDERS))
    add.add_argument("--id", required=True, help="short local name, e.g. work-earthlink")
    add.add_argument("--email", required=True)
    add.add_argument("--label", default="")
    add.add_argument("--username", help="only if the provider needs a login name other than the email address")
    add.add_argument("--folders", default="INBOX", help='comma-separated folders, or "*" for all (default INBOX)')
    add.add_argument("--host", help="incoming IMAP server (default: the provider's; EarthLink-hosted domains get securemail.hosting.earthlink.net)")
    add.add_argument("--port", type=int)
    add.add_argument("--security", choices=accounts_lib.SECURITY_MODES)
    add.add_argument("--scope", choices=config.SCOPES, help="work or personal (default: EarthLink work, iCloud personal)")
    credential = account_sub.add_parser("credential", help="store the account's password in the OS keyring (hidden prompt)")
    credential.add_argument("account_id")
    credential.add_argument("--clear", action="store_true", help="remove the stored credential")
    for name in ("remove", "enable", "disable"):
        account_sub.add_parser(name).add_argument("account_id")
    folders = account_sub.add_parser("folders", help="choose folders to sync")
    folders.add_argument("account_id")
    folders.add_argument("--set", required=True, help='comma-separated folders, or "*" for all')
    folders.add_argument("--exclude", default="", help='with "*": comma-separated folders to skip')

    setup = sub.add_parser("setup", help="open a small window to add a mail account and its password")
    setup.add_argument("provider", nargs="?", choices=("icloud",), help="(older command) set up iCloud at the prompt instead")
    setup.add_argument("--email")

    health = sub.add_parser("health", help="log in to each account (or one) and report")
    health.add_argument("--account")
    status = sub.add_parser("status", help="sync status per account")
    status.add_argument("--account")
    status.add_argument("--scope", choices=config.SCOPES)
    sync = sub.add_parser("sync", help="incremental, read-only sync")
    target = sync.add_mutually_exclusive_group()
    target.add_argument("--account")
    target.add_argument("--all", action="store_true", help="every enabled account (default)")
    sync.add_argument("--mailbox")
    sync.add_argument("--scope", choices=config.SCOPES, help="only this scope's accounts")
    sync.add_argument("--limit", type=int, default=200, help="new messages per mailbox this run")
    sync.add_argument("--backfill", type=int, default=0, help="also index this many older messages per mailbox")
    search = sub.add_parser("search")
    search.add_argument("query")
    search.add_argument("--scope", choices=config.SCOPES, required=True, help="work or personal (separate indexes)")
    search.add_argument("--limit", type=int, default=10)
    search.add_argument("--account", action="append")
    search.add_argument("--provider", action="append")
    search.add_argument("--mailbox", action="append")
    search.add_argument("--source", action="append", help="live_imap or pst_archive")
    search.add_argument("--from", dest="sender")
    search.add_argument("--to", dest="recipient")
    search.add_argument("--after")
    search.add_argument("--before")
    show = sub.add_parser("show", help="one message by id (msg_...)")
    show.add_argument("id")
    show.add_argument("--scope", choices=config.SCOPES, required=True)
    show.add_argument("--body", action="store_true")
    pst = sub.add_parser("import-pst", help="import Outlook PST/OST backups (a file or a folder) into the work index")
    pst.add_argument("path")
    pst.add_argument("--no-ost", action="store_true", help="skip .ost files")
    attach = sub.add_parser("attachments", help="save attachments to Downloads\Mail Attachments (named Date - Sender - Name)")
    attach.add_argument("--enable", action="store_true", help="save attachments from now on (sync and PST import)")
    attach.add_argument("--disable", action="store_true")
    attach.add_argument("--folder", help="where to save (default: Downloads\Mail Attachments)")
    attach.add_argument("--scope", choices=config.SCOPES, help="without --enable/--disable: download attachments of mail already indexed")
    sub.add_parser("split-scopes", help="one-time: split the older combined index into work and personal")
    bench = sub.add_parser("benchmark", help="time sync and search on synthetic mail (no network, no real mail)")
    bench.add_argument("--messages", type=int, default=1000, help="messages per synthetic account (two accounts)")
    thread = sub.add_parser("thread", help="a conversation by thread id (thr_...) or message id")
    thread.add_argument("id")
    thread.add_argument("--scope", choices=config.SCOPES, required=True)
    thread.add_argument("--body", action="store_true")


def dispatch(args: argparse.Namespace, emit: Callable[[Any], None]) -> int:
    from . import (account_status, get_message, get_thread, health, list_accounts, search, setup_icloud, status, sync)

    command = args.mail_command
    if command == "accounts":
        emit(list_accounts(args.scope))
    elif command == "account":
        return _account(args, emit)
    elif command == "setup" and not args.provider:
        from .setup_window import run

        return run()
    elif command == "setup":
        address = args.email or input("iCloud email address: ").strip()
        print(accounts_lib.PROVIDERS["icloud"]["credential_help"], file=sys.stderr)
        emit(setup_icloud(address, getpass.getpass("Apple app-specific password (hidden): ")))
    elif command == "health":
        result = health(args.account)
        emit(result)
        return 0 if all(item.get("ok") for item in result["accounts"]) else 1
    elif command == "status":
        emit(account_status(args.account) if args.account else status(scope=args.scope))
    elif command == "sync":
        result = sync(args.limit, args.mailbox, args.account, args.backfill, scope=args.scope)
        emit(result)
        return 0 if result.get("complete", result.get("status") == "ok") else 1
    elif command == "search":
        emit(search(args.query, args.limit, accounts=args.account, providers=args.provider, mailboxes=args.mailbox, source_kinds=args.source,
                    sender=args.sender, recipient=args.recipient, after=args.after, before=args.before, scope=args.scope))
    elif command == "benchmark":
        from .benchmark import run

        emit(run(args.messages))
    elif command == "show":
        emit(get_message(id=args.id, include_body=args.body, scope=args.scope))
    elif command == "thread":
        emit(get_thread(args.id if args.id.startswith("thr_") else None, args.id if args.id.startswith("msg_") else None, include_body=args.body, scope=args.scope))
    elif command == "import-pst":
        from pathlib import Path

        from . import pst

        target = Path(args.path)

        def report(event: dict) -> None:
            print(json.dumps(event), file=sys.stderr, flush=True)

        from . import attachments

        exporter = attachments.Exporter("work") if attachments.enabled() else None
        try:
            emit(pst.import_pst(target, progress=report, exporter=exporter) if target.is_file()
                 else pst.import_directory(target, progress=report, include_ost=not args.no_ost, exporter=exporter))
        finally:
            if exporter is not None:
                exporter.close()
    elif command == "attachments":
        from . import attachments

        if args.enable or args.disable:
            current = attachments.settings()
            current["export_attachments"] = bool(args.enable)
            if args.folder:
                current["attachments_dir"] = args.folder
            (config.LOCAL_DIR / "settings.json").write_text(json.dumps(current, indent=2), encoding="utf-8")
            emit({"export_attachments": current["export_attachments"], "folder": str(attachments.default_root())})
        else:
            emit([attachments.export_missing_live(scope) for scope in ([args.scope] if args.scope else config.SCOPES)])
    elif command == "split-scopes":
        from .scopes import split_combined_index

        emit(split_combined_index())
    return 0


def _account(args: argparse.Namespace, emit: Callable[[Any], None]) -> int:
    command = args.account_command
    if command == "add":
        folders = [item.strip() for item in args.folders.split(",") if item.strip()]
        host, port, security = accounts_lib.default_server(args.provider, args.email)
        host, port, security = args.host or host, args.port or port, args.security or security
        defaults = accounts_lib.PROVIDERS[args.provider]
        account = accounts_lib.add_account(args.provider, args.id, args.email, label=args.label, username=args.username, folders=folders,
                                           imap_host=host if host != defaults["imap_host"] else None,
                                           imap_port=port if port != defaults["imap_port"] else None,
                                           security=security if security != defaults["security"] else None, scope=args.scope)
        emit({"added": account.public(), "next": f"agent-os mail account credential {account.id}"})
    elif command == "credential":
        account = accounts_lib.get_account(args.account_id)
        if args.clear:
            emit({"account_id": account.id, "credential_removed": accounts_lib.delete_secret(account.id)})
            return 0
        print(f"{account.defaults['credential_label']} for {account.email}", file=sys.stderr)
        print(account.defaults["credential_help"], file=sys.stderr)
        secret = getpass.getpass("Enter it (hidden): ")
        if not secret:
            emit({"account_id": account.id, "stored": False, "reason": "nothing entered"})
            return 1
        stored_in = accounts_lib.set_secret(account.id, secret)
        del secret
        emit({"account_id": account.id, "stored": True, "stored_in": stored_in, "next": f"agent-os mail health --account {account.id}"})
    elif command == "remove":
        accounts_lib.remove_account(args.account_id)
        emit({"removed": args.account_id, "note": "indexed mail stays in the local index; the keyring credential was not removed (use: mail account credential --clear)"})
    elif command in {"enable", "disable"}:
        emit(accounts_lib.update_account(args.account_id, enabled=command == "enable").public())
    elif command == "folders":
        folders = [item.strip() for item in args.set.split(",") if item.strip()]
        exclude = [item.strip() for item in args.exclude.split(",") if item.strip()]
        emit(accounts_lib.update_account(args.account_id, folders=folders, exclude_folders=exclude).public())
    return 0
