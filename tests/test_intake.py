"""Intake queue: scoped items, per-consumer deliveries, spam skipped visibly, changes re-queued."""

import pytest

from agent_os.intake import Item, Queue


def _item(ref, flag="work", content="a", scope="work"):
    return Item(source="mail", kind="email", scope=scope, ref=ref, path=f"{ref}.md", content_hash=content, flag=flag)


def test_deliveries_by_flag_and_requeue_on_change(tmp_path):
    with Queue("work", tmp_path / "q.sqlite3") as q:
        assert q.upsert(_item("m1")) == "new"
        assert q.upsert(_item("m2", flag="spam")) == "new"
        assert q.upsert(_item("m3", flag="review")) == "new"
        assert q.upsert(_item("m1")) == "same"
        stats = q.stats()["deliveries"]
        assert stats["engine"] == {"pending": 2, "skipped": 1}
        assert stats["classify"] == {"pending": 1}
        assert stats["promote"] == {"pending": 1}
        done = [r["item_id"] for r in q.pending("engine")]
        q.finish(done, "engine", "done")
        assert q.pending("engine") == []
        assert q.upsert(_item("m1", content="b")) == "changed"
        assert [r["ref"] for r in q.pending("engine")] == ["m1"]
        assert q.upsert(_item("m3", flag="work")) == "reflagged"  # model/rules decided: no longer a review item
        assert q.stats()["deliveries"]["classify"] == {"skipped": 1}


def test_scopes_never_mix(tmp_path):
    with Queue("personal", tmp_path / "p.sqlite3") as q:
        with pytest.raises(ValueError):
            q.upsert(_item("m1"))
        assert q.upsert(_item("p1", flag="personal", scope="personal")) == "new"
        assert "promote" not in q.stats()["deliveries"]


def test_executive_window_shows_queue_per_tab():
    from agent_os.executive.window.providers_intake import intake_items

    items = intake_items(lambda: {"work": {"deliveries": {"engine": {"pending": 5, "skipped": 2}, "classify": {"pending": 1}}},
                                  "personal": {"deliveries": {}}})
    assert [i["tab"] for i in items] == ["work"]
    assert "5 waiting" in items[0]["why"] and "1 need a spam/work decision" in items[0]["why"]


def test_drain_ingests_into_a_real_engine_root(tmp_path, monkeypatch):
    import subprocess
    import sys

    import agent_os.intake as intake

    root = tmp_path / "kb"
    subprocess.run([sys.executable, "-m", "ingester_engine", "init", str(root), "--profile", "general-v1",
                    "--privacy", "standard-private", "--project-id", "kbtest", "--confirm-consent"],
                   check=True, capture_output=True, stdin=subprocess.DEVNULL, timeout=120)
    monkeypatch.setattr(intake, "LOCAL", tmp_path / "intake")
    monkeypatch.setattr(intake, "settings", lambda: {"scopes": {"work": {"engine_root": str(root)}}, "engine_batch": 10})
    doc = tmp_path / "a.md"
    doc.write_text("# Synthetic\n\nA synthetic note about the leave request process.\n", encoding="utf-8")
    with Queue("work", tmp_path / "intake" / "work" / "queue.sqlite3") as q:
        q.upsert(Item(source="folder:test", kind="document", scope="work", ref="a", path=str(doc), content_hash="1", flag="work"))
        q.upsert(Item(source="folder:test", kind="document", scope="work", ref="b", path=str(doc), content_hash="2", flag="spam"))
    result = intake.drain_engine("work")
    assert result["ingested"] == 1 and result["failed"] == 0, result
    with Queue("work", tmp_path / "intake" / "work" / "queue.sqlite3") as q:
        assert q.stats()["deliveries"]["engine"] == {"done": 1, "skipped": 1}
    assert not (tmp_path / "intake" / "work" / "drain.lock").exists()


def test_new_consumers_backfill_and_not_work_skips_engine(tmp_path):
    with Queue("work", tmp_path / "q.sqlite3") as q:
        q.upsert(_item("m1"))
        screened = _item("m1")
        screened.meta = {"screen": True}
        assert q.upsert(screened) == "same"
        assert q.stats()["deliveries"]["classify"] == {"pending": 1}
        assert q.upsert(_item("m1", flag="not_work")) == "reflagged"
        stats = q.stats()["deliveries"]
        assert stats["engine"] == {"skipped": 1}
        assert stats["promote"] == {"skipped": 1}


def test_classifier_writes_overrides_from_model_answer(tmp_path, monkeypatch):
    import json
    import sqlite3

    from agent_os.intake import classify
    from agent_os.mail import config as mail_config

    monkeypatch.setattr(mail_config, "LOCAL_DIR", tmp_path / "mail")
    db = mail_config.db_for("work")
    db.parent.mkdir(parents=True)
    with sqlite3.connect(db) as conn:
        conn.execute("CREATE TABLE mail_messages (id TEXT, sender TEXT, recipients TEXT, subject TEXT, body TEXT)")
        conn.execute("INSERT INTO mail_messages VALUES ('msg_1','a@gmail.com','hr@example.org','Family reunion','SSN 123-45-6789 see you')")
    monkeypatch.setattr(classify, "Queue", lambda scope: Queue(scope, tmp_path / "q.sqlite3"))
    with Queue("work", tmp_path / "q.sqlite3") as q:
        q.upsert(Item(source="mail", kind="email", scope="work", ref="msg_1", path="x.md", content_hash="h", flag="review"))
    sent = []

    def fake_model(prompt):
        sent.append(prompt)
        return 'Sure: [{"id": "msg_1", "flag": "not_work", "reason": "family event"}]'

    result = classify.classify("work", runner=fake_model)
    assert result["decided"] == 1
    assert "123-45-6789" not in sent[0]  # numbers are masked before leaving the PC
    assert json.loads(classify.overrides_path("work").read_text())["msg_1"]["flag"] == "not_work"


def test_promote_screen_rejects_pii_and_former_staff():
    from agent_os.intake.promote import screen

    current, others = {"jane doe"}, {"john roe"}
    assert screen("Benefit enrollment closes November 15 each year.", current, others) is None
    assert screen("Jane Doe, HR Director, approves leave requests.", current, others) is None
    assert screen("John Roe handled the claim.", current, others) == "names a person who is not current staff"
    assert screen("Call 606-555-1234 for COBRA.", current, others) is not None
    assert screen("Send forms to hr@example.org.", current, others) is not None


def test_phone_log_folds_missed_call_emails_and_names_applicants(tmp_path, monkeypatch):
    import sqlite3

    from agent_os.intake import phone_log

    mail = tmp_path / "mail.sqlite3"
    with sqlite3.connect(mail) as conn:
        conn.execute("CREATE TABLE mail_messages (subject TEXT, date_utc TEXT, body TEXT)")
        conn.executemany("INSERT INTO mail_messages VALUES (?,?,?)", [
            ("New missed call from SEXTON ALLEN:Main Number 6065550100", "2026-10-06T14:00:30+00:00",
             'Ringing: "00:21"'),
            ("New missed call from Pat Doe Ext.244", "2026-10-07T12:00:00+00:00", 'Ringing: "00:12"'),
            ("New missed call from WIRELESS CALLER:Main Number 6065550199", "2026-10-08T12:00:00+00:00", "")])
    ambient = tmp_path / "ambient.sqlite3"
    with sqlite3.connect(ambient) as conn:
        conn.execute("CREATE TABLE call_sessions (session_id TEXT, ringing_at TEXT, dialing_at TEXT, "
                     "created_at TEXT, direction TEXT, remote_number TEXT, remote_name TEXT, status TEXT, "
                     "source_system TEXT, reconciliation_confidence REAL)")
        conn.execute("INSERT INTO call_sessions VALUES ('s1','2026-10-06T14:00:00+00:00',NULL,'x','inbound',"
                     "'6065550100',NULL,'failed','3cx',NULL)")
    emails = phone_log.missed_call_emails(mail)
    assert [(e["name"], e["internal"], e["ring_s"]) for e in emails] == [
        ("Sexton Allen", False, 21), ("Pat Doe", True, 12), (None, False, None)]
    monkeypatch.setattr(phone_log, "AMBIENT_DB", ambient)
    monkeypatch.setattr(phone_log, "CALL_DOCS", tmp_path / "none")
    monkeypatch.setattr(phone_log, "VOICEMAILS", tmp_path / "none")
    monkeypatch.setattr(phone_log, "missed_call_emails", lambda: emails)
    monkeypatch.setattr(phone_log, "applicants", lambda: [
        {"key": "A1", "name": "Allen Sexton", "status": "Offered", "position": "Transit Driver", "phone": ""}])
    conf = {"scopes": {"work": {"correspondence_dir": str(tmp_path / "HR" / "Correspondence")}}}
    result = phone_log.build(conf)
    assert result["calls"] == 3                       # the logged call and its missed-call email are one call
    assert result["applicants"] == 1                  # caller ID "SEXTON ALLEN" is applicant Allen Sexton
    day = (tmp_path / "HR" / "Phone Log" / "2026-10-06.md").read_text(encoding="utf-8")
    assert "Allen Sexton (applicant: Offered, Transit Driver)" in day and "missed (rang 21s)" in day


def test_usage_limit_pauses_classification_without_using_up_attempts(tmp_path, monkeypatch):
    import sqlite3

    from agent_os.intake import classify
    from agent_os.mail import config as mail_config

    monkeypatch.setattr(mail_config, "LOCAL_DIR", tmp_path / "mail")
    db = mail_config.db_for("work")
    db.parent.mkdir(parents=True)
    with sqlite3.connect(db) as conn:
        conn.execute("CREATE TABLE mail_messages (id TEXT, sender TEXT, recipients TEXT, subject TEXT, body TEXT)")
        conn.execute("INSERT INTO mail_messages VALUES ('msg_1','a@x.org','hr@x.org','Hi','body')")
    monkeypatch.setattr(classify, "Queue", lambda scope: Queue(scope, tmp_path / "q.sqlite3"))
    with Queue("work", tmp_path / "q.sqlite3") as q:
        q.upsert(Item(source="mail", kind="email", scope="work", ref="msg_1", path="x.md", content_hash="h", flag="review"))

    def limited(prompt):
        raise RuntimeError('{"api_error_status":429,"result":"You\'ve hit your session limit"}')

    result = classify.classify("work", runner=limited)
    assert result["paused"] == "usage limit"
    with Queue("work", tmp_path / "q.sqlite3") as q:
        row = q.conn.execute("SELECT state, attempts FROM deliveries WHERE consumer='classify'").fetchone()
    assert tuple(row) == ("pending", 0)
