from __future__ import annotations

import json
import re
import sys
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os import rtec_applicants
from agent_os.executive import applicants as ex
from agent_os.executive import brain
from agent_os.executive.gateway import SyntheticDashboardGateway
from agent_os.executive.outbox import OutboxStore

NOW = datetime(2026, 10, 1, 12, 0)
SLOT = datetime(2026, 10, 5, 9)

RESTRICTED = {
    "aa_pdf_path": "EEO_LEAK_AAPDF_7731",
    "self_id": "EEO_LEAK_SELFID_7731",
    "self_identification": {"EEO_LEAK_SELFIDMAP_7731": "x"},
    "race": "EEO_LEAK_RACE_7731",
    "sex": "EEO_LEAK_SEX_7731",
    "gender": "EEO_LEAK_GENDER_7731",
    "veteran": "EEO_LEAK_VETERAN_7731",
    "veteran_status": "EEO_LEAK_VETSTAT_7731",
    "disability": "EEO_LEAK_DISABILITY_7731",
    "disability_status": "EEO_LEAK_DISSTAT_7731",
    "source": "EEO_LEAK_SOURCE_7731",
    "source_key": "EEO_LEAK_SOURCEKEY_7731",
    "applicant_key": "EEO_LEAK_APPKEY_7731",
}
FORBIDDEN_VALUES = [
    v for value in RESTRICTED.values() for v in ([value] if isinstance(value, str) else list(value))
]
FORBIDDEN_NAMES = list(RESTRICTED)
TECH = {"match": "Tech", "pending": False, "alternates": [], "reasons": ["County fit"]}
REFS = ("ref-a", "ref-b")
EMAILS = {"ref-a": "ann@example.test", "ref-b": "bo@example.test"}


def _applicant(ref, name):
    return {
        "agent_ref": ref, "name": name, "position": "Tech", "submitted": "2026-09-20",
        "status": "New", "county_preference": "Kent", "email": EMAILS[ref], "match": dict(TECH),
        **RESTRICTED,
    }


def _review(score):
    result = {"summary": "Relevant work", "strengths": ["Experience"], "concerns": [],
              "criteria": [{"criterion": "License", "met": True, "evidence": "Held", **RESTRICTED}],
              **RESTRICTED}
    return {"score": score, "recommendation": "interview", "result_json": result, **RESTRICTED}


class MemStore:
    def __init__(self):
        self.data = {}
        self.saves = []

    def save(self, batch):
        self.data[batch["batch_id"]] = json.loads(json.dumps(batch))
        self.saves.append(json.loads(json.dumps(batch)))

    def load(self, batch_id):
        return json.loads(json.dumps(self.data[batch_id]))


def _leaks(text):
    found = [v for v in FORBIDDEN_VALUES if v in text]
    found += [n for n in FORBIDDEN_NAMES if re.search(rf"(?<![A-Za-z0-9_]){re.escape(n)}(?![A-Za-z0-9_])", text, re.I)]
    return found


def _create_guard_patches(fail_fn):
    """Create patches for guards that should not be triggered during brain operations."""
    return [
        patch("agent_os.executive.gateway.LocalDashboardGateway", side_effect=fail_fn),
        patch.object(rtec_applicants, "_project_root", side_effect=fail_fn),
        patch.object(rtec_applicants, "_connect_readonly", side_effect=fail_fn),
        patch("socket.create_connection", side_effect=fail_fn),
        patch("socket.socket.connect", side_effect=fail_fn),
        patch("agent_os.executive.gateway.importlib.import_module", side_effect=fail_fn),
    ]


class EeoFirewallTests(unittest.TestCase):
    def test_restricted_fields_never_leave_the_gateway(self):
        audits = []
        roster = [{"agent_ref": r, "name": n, "position": "Tech", "submitted": "2026-09-20",
                   "status": "New", "county": "Kent", "city": "Dover", **RESTRICTED}
                  for r, n in zip(REFS, ("Ann", "Bo"))]
        gateway = SyntheticDashboardGateway(
            applicants=[_applicant(r, n) for r, n in zip(REFS, ("Ann", "Bo"))],
            reviews={"ref-a": _review(90), "ref-b": _review(70)},
            managers={r: "Manager One" for r in REFS},
            calendar={"Manager One": [SLOT, SLOT + timedelta(hours=2), SLOT + timedelta(hours=4)]},
        )
        store = MemStore()
        visible = []

        def fail(*_a, **_k):
            raise AssertionError("real Dashboard, Outlook or network access")

        patches = _create_guard_patches(fail) + [
            patch.object(ex.rtec_applicants, "list_applicants",
                         side_effect=lambda status=None, limit=50, offset=0: {
                             "count": 0, "results": [dict(r) for r in roster if r["status"] == status][offset:offset + limit]}),
            patch.object(ex.rtec_applicants, "get_summary",
                         side_effect=lambda ref: {"applicant_ref": ref, "email": EMAILS[ref], **RESTRICTED}),
            patch.object(ex.rtec_applicants, "pending_actions",
                         return_value={"results": [{
                             "applicant_ref": "ref-a", "name": "Ann", "position": "Tech", "status": "New",
                             "submitted": "2026-09-20", "administrative_action": "human_review_pending",
                             **RESTRICTED}]}),
            patch.object(ex.rtec_applicants, "_audit_access",
                         side_effect=lambda action, applicant_ref=None, metadata=None: audits.append(
                             (action, applicant_ref, dict(metadata or {})))),
        ]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)

        sug = ex.suggestions("Tech", gateway=gateway)
        self.assertEqual(sug["count"], 2)
        visible.append(sug)

        batch = ex.plan_outreach(list(REFS), "Tech", "phone", "Office", 30,
                                 gateway=gateway, store=store, now=NOW)
        visible.append(batch)
        approved = ex.approve_batch(batch["batch_id"], {"ref-a": "confirm", "ref-b": "confirm"},
                                    gateway=gateway, store=store, now=NOW)
        visible.append(approved)
        dry = ex.send_batch(batch["batch_id"], gateway=gateway, store=store, now=NOW)
        self.assertTrue(dry["dry_run"])
        visible.append(dry)
        sent = ex.send_batch(batch["batch_id"], confirm=True, gateway=gateway, store=store, now=NOW)
        self.assertEqual(sent["sent"], list(REFS))
        visible.append(sent)

        # Persisted outbox files, written under a temp dir.
        with tempfile.TemporaryDirectory() as tmp:
            outbox = OutboxStore(tmp)
            created = outbox.create([
                {"applicant_ref": i["applicant_ref"], "name": i["name"], "opening": "Tech",
                 "manager": i["manager"], "interview_type": "phone", "location": "Office",
                 "duration_minutes": 30, "proposed_slots": [s["start"] for s in i["slots"]],
                 "subject": i["subject"], "body": i["body"]}
                for i in approved["items"]])
            outbox.approve(created["batch_id"], {r: [SLOT.isoformat()] for r in REFS})
            outbox.record_send_result(created["batch_id"], "ref-a", True, "email-1")
            files = [p.read_text(encoding="utf-8") for p in Path(tmp).rglob("*") if p.is_file()]
        self.assertTrue(files)

        # Brain briefing and prompt construction.
        executive = brain.ExecutiveBrain(gateway=gateway, store=store)
        briefing = executive.briefing("Tech", batch_ids=[batch["batch_id"]], now=NOW)
        prompt = brain.build_prompt(briefing, question="Who should I call first?")
        self.assertIn("ref-a", prompt)
        visible += [briefing, prompt, created]

        text = "\n".join([
            json.dumps(visible, default=str), json.dumps(store.saves, default=str),
            json.dumps(audits, default=str), "\n".join(files),
            repr(gateway.calls), repr(gateway.drafts), repr(gateway.sent),
        ])
        self.assertEqual(_leaks(text), [])
        self.assertTrue([a for a in audits if a[0] == "executive.outreach_send"])

    def test_brain_prompt_filters_restricted_fields(self):
        """Verify brain.build_prompt and batch_status filter restricted fields even when poisoned."""
        def fail(*_a, **_k):
            raise AssertionError("real Dashboard, Outlook or network access")

        # Roster for _reviewable_applicants() to find our test refs.
        roster = [{"agent_ref": r, "name": n, "position": "Tech", "submitted": "2026-09-20",
                   "status": "New", "county": "Kent", "city": "Dover", **RESTRICTED}
                  for r, n in zip(REFS, ("Ann", "Bo"))]

        patches = _create_guard_patches(fail) + [
            patch.object(ex.rtec_applicants, "list_applicants",
                         side_effect=lambda status=None, limit=50, offset=0: {
                             "count": 0, "results": [dict(r) for r in roster if r["status"] == status][offset:offset + limit]}),
            patch.object(ex.rtec_applicants, "pending_actions",
                         return_value={"results": [{
                             "applicant_ref": "ref-c", "name": "Charlie", "position": "Tech", "status": "New",
                             "submitted": "2026-09-20", "administrative_action": "human_review_pending",
                             **RESTRICTED}]}),
            patch.object(ex.rtec_applicants, "_audit_access",
                         side_effect=lambda action, applicant_ref=None, metadata=None: None),
        ]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)

        # Set up poisoned gateway for real flow test.
        gateway = SyntheticDashboardGateway(
            applicants=[_applicant(r, n) for r, n in zip(REFS, ("Ann", "Bo"))],
            reviews={"ref-a": _review(90), "ref-b": _review(70)},
            managers={r: "Manager One" for r in REFS},
            calendar={"Manager One": [SLOT, SLOT + timedelta(hours=2), SLOT + timedelta(hours=4)]},
        )
        store = MemStore()

        # Test 1: Real flow - plan_outreach + approve_batch on poisoned gateway.
        batch = ex.plan_outreach(list(REFS), "Tech", "phone", "Office", 30,
                                 gateway=gateway, store=store, now=NOW)
        approved = ex.approve_batch(batch["batch_id"], {"ref-a": "confirm", "ref-b": "confirm"},
                                    gateway=gateway, store=store, now=NOW)

        # Create briefing from real batch via ExecutiveBrain.
        executive = brain.ExecutiveBrain(gateway=gateway, store=store)
        real_briefing = executive.briefing("Tech", batch_ids=[batch["batch_id"]], now=NOW)
        real_prompt = brain.build_prompt(real_briefing, question="Who should I call first?")
        self.assertIn("ref-a", real_prompt)

        # Test 2: Hand-craft a poisoned batch with restricted fields embedded.
        poisoned_batch = {
            "batch_id": "poisoned-batch-1",
            "state": "APPROVED",
            "opening": "Tech",
            "created_at": "2026-10-01T09:00:00",
            "items": [
                {
                    "applicant_ref": "ref-a",
                    "name": "Ann",
                    "state": "APPROVED",
                    "body": "Interview scheduled",
                    # Inject restricted fields; should be filtered from output
                    **RESTRICTED,
                },
                {
                    "applicant_ref": "ref-b",
                    "name": "Bo",
                    "state": "APPROVED",
                    "body": "Interview scheduled",
                    **RESTRICTED,
                },
            ],
            "excluded": [],
            # Inject restricted fields at batch level
            **RESTRICTED,
        }

        # Hand-craft a poisoned needs_action briefing.
        poisoned_needs = {
            "groups": [
                {
                    "reason": "human_review_pending",
                    "count": 1,
                    "next_step": "Review.",
                    "items": [
                        {
                            "applicant_ref": "ref-c",
                            "name": "Charlie",
                            "age_days": 5,
                            # Inject restricted fields
                            **RESTRICTED,
                        }
                    ],
                }
            ]
        }

        # Hand-craft a poisoned suggestions briefing.
        poisoned_suggestions = {
            "label": "Advisory",
            "opening": "Tech",
            "unreviewed_matching_count": 1,
            "suggestions": [
                {
                    "applicant_ref": "ref-d",
                    "name": "Dana",
                    "position": "Tech",
                    "score": 85,
                    "recommendation": "interview",
                    # Inject restricted fields
                    **RESTRICTED,
                }
            ],
        }

        # Create a briefing with poisoned data at all levels.
        poisoned_briefing = {
            "needs_action": poisoned_needs,
            "suggestions": poisoned_suggestions,
            "batches": [brain.batch_status(poisoned_batch)],
        }

        # Test build_prompt filters restricted fields.
        poisoned_prompt = brain.build_prompt(poisoned_briefing, question="Who should I interview?")
        self.assertIn("ref-c", poisoned_prompt)
        self.assertIn("ref-d", poisoned_prompt)
        self.assertIn("Who should I interview?", poisoned_prompt)

        # Test batch_status output doesn't leak restricted fields.
        status = brain.batch_status(poisoned_batch)
        self.assertEqual(status["batch_id"], "poisoned-batch-1")
        self.assertEqual(status["state"], "APPROVED")
        self.assertEqual(status["item_count"], 2)

        # Verify no leaks in brain outputs: prompts and batch_status filter restricted fields
        # even when the input briefing/batch was poisoned. The briefing from ExecutiveBrain
        # (real_briefing) is produced deterministically from needs_action and batch_status.
        brain_outputs = [
            json.dumps(real_briefing, default=str),
            real_prompt,
            poisoned_prompt,  # Output of build_prompt on poisoned input should filter
            json.dumps(status, default=str),  # batch_status output on poisoned batch should filter
        ]
        text = "\n".join(brain_outputs)
        leaked = _leaks(text)
        self.assertEqual(leaked, [], f"Restricted fields leaked: {leaked}")


if __name__ == "__main__":
    unittest.main()
