from pathlib import Path

from agent_os import mail


def test_decode_header():
    assert mail._decode("Hello") == "Hello"


def test_body_plain_text():
    import email
    msg = email.message_from_string("Content-Type: text/plain; charset=utf-8\n\nhello")
    assert mail._body(msg) == "hello"


def test_mail_paths_are_local_and_gitignored():
    assert ".agent-local" in str(mail.LOCAL_DIR)
    ignore = (Path(__file__).resolve().parents[1] / ".gitignore").read_text(encoding="utf-8")
    assert ".agent-local/" in ignore
