from __future__ import annotations

import sys
import json
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

from agent_os.executive.window.providers_applicants import applicant_items, county_items


class ApplicantItemsTests(unittest.TestCase):
    def test_maps_groups_to_items(self):
        """Each needs-action group becomes one work item."""
        def fake_needs_action():
            return {
                "count": 3,
                "groups": [
                    {
                        "reason": "new_reply_unread",
                        "count": 2,
                        "next_step": "Review the application.",
                        "items": [
                            {
                                "applicant_ref": "r1",
                                "name": "Alice",
                                "position": "Engineer",
                                "status": "New",
                                "submitted": "2026-09-20",
                                "age_days": 11,
                            },
                            {
                                "applicant_ref": "r2",
                                "name": "Bob",
                                "position": "Manager",
                                "status": "New",
                                "submitted": "2026-09-28",
                                "age_days": 3,
                            },
                        ],
                    },
                    {
                        "reason": "interview_request_outstanding",
                        "count": 1,
                        "next_step": "Check the reply.",
                        "items": [
                            {
                                "applicant_ref": "r3",
                                "name": "Charlie",
                                "position": "Engineer",
                                "status": "Interview Requested",
                                "submitted": "2026-09-30",
                                "age_days": 1,
                            },
                        ],
                    },
                ],
            }

        items = applicant_items(needs_action=fake_needs_action)
        self.assertEqual(len(items), 2)

    def test_item_shape(self):
        """Items have the required fields."""
        def fake_needs_action():
            return {
                "count": 1,
                "groups": [
                    {
                        "reason": "new_reply_unread",
                        "count": 1,
                        "next_step": "Review it.",
                        "items": [
                            {
                                "applicant_ref": "r1",
                                "name": "Alice",
                                "position": "Engineer",
                                "status": "New",
                                "submitted": "2026-09-20",
                                "age_days": 5,
                            },
                        ],
                    },
                ],
            }

        items = applicant_items(needs_action=fake_needs_action)
        self.assertEqual(len(items), 1)
        item = items[0]

        # Check required fields
        self.assertIn("id", item)
        self.assertIn("tab", item)
        self.assertIn("kind", item)
        self.assertIn("title", item)
        self.assertIn("why", item)
        self.assertIn("source", item)
        self.assertIn("age_days", item)
        self.assertIn("context", item)

    def test_tab_is_work(self):
        """All items have tab='work'."""
        def fake_needs_action():
            return {
                "count": 2,
                "groups": [
                    {
                        "reason": "new_reply_unread",
                        "count": 1,
                        "next_step": "Review.",
                        "items": [
                            {
                                "applicant_ref": "r1",
                                "name": "Alice",
                                "position": "Engineer",
                                "status": "New",
                                "submitted": "2026-09-20",
                                "age_days": 5,
                            },
                        ],
                    },
                    {
                        "reason": "interview_request_outstanding",
                        "count": 1,
                        "next_step": "Check reply.",
                        "items": [
                            {
                                "applicant_ref": "r2",
                                "name": "Bob",
                                "position": "Manager",
                                "status": "Interview Requested",
                                "submitted": "2026-09-25",
                                "age_days": 6,
                            },
                        ],
                    },
                ],
            }

        items = applicant_items(needs_action=fake_needs_action)
        for item in items:
            self.assertEqual(item["tab"], "work")

    def test_stable_ids(self):
        """Item IDs are stable and based on reason."""
        def fake_needs_action():
            return {
                "count": 2,
                "groups": [
                    {
                        "reason": "new_reply_unread",
                        "count": 2,
                        "next_step": "Review.",
                        "items": [
                            {
                                "applicant_ref": "r1",
                                "name": "Alice",
                                "position": "Engineer",
                                "status": "New",
                                "submitted": "2026-09-20",
                                "age_days": 5,
                            },
                            {
                                "applicant_ref": "r2",
                                "name": "Bob",
                                "position": "Manager",
                                "status": "New",
                                "submitted": "2026-09-25",
                                "age_days": 6,
                            },
                        ],
                    },
                    {
                        "reason": "interview_request_outstanding",
                        "count": 1,
                        "next_step": "Check reply.",
                        "items": [
                            {
                                "applicant_ref": "r3",
                                "name": "Charlie",
                                "position": "Engineer",
                                "status": "Interview Requested",
                                "submitted": "2026-09-24",
                                "age_days": 7,
                            },
                        ],
                    },
                ],
            }

        items = applicant_items(needs_action=fake_needs_action)
        ids = [item["id"] for item in items]

        # IDs should be stable (based on reason, not data content)
        self.assertIn("applicants:new_reply_unread", ids)
        self.assertIn("applicants:interview_request_outstanding", ids)

        # Call again, should get same IDs
        items2 = applicant_items(needs_action=fake_needs_action)
        ids2 = [item["id"] for item in items2]
        self.assertEqual(ids, ids2)

    def test_filters_forbidden_keys(self):
        """No forbidden EEO/self-ID keys appear in items."""
        def fake_needs_action():
            return {
                "count": 1,
                "groups": [
                    {
                        "reason": "new_reply_unread",
                        "count": 1,
                        "next_step": "Review it.",
                        "items": [
                            {
                                "applicant_ref": "r1",
                                "name": "Alice",
                                "position": "Engineer",
                                "status": "New",
                                "submitted": "2026-09-20",
                                "age_days": 5,
                                "gender": "FORBIDDEN",
                                "race": "FORBIDDEN",
                                "ethnicity": "FORBIDDEN",
                                "veteran": "FORBIDDEN",
                                "disability": "FORBIDDEN",
                                "eeo": "FORBIDDEN",
                                "self_id": "FORBIDDEN",
                            },
                        ],
                    },
                ],
            }

        items = applicant_items(needs_action=fake_needs_action)
        self.assertEqual(len(items), 1)

        # Serialize to JSON and check for forbidden keys
        serialized = json.dumps(items)
        forbidden_keys = {"gender", "race", "ethnicity", "veteran", "disability", "eeo", "self_id"}
        for forbidden_key in forbidden_keys:
            # Forbidden keys should not appear in the serialized output
            # (checking for the key name specifically, not the value)
            self.assertNotIn(f'"{forbidden_key}"', serialized,
                           f"Forbidden key '{forbidden_key}' found in serialized items")

    def test_age_days_is_maximum(self):
        """age_days in item is the maximum from group items."""
        def fake_needs_action():
            return {
                "count": 3,
                "groups": [
                    {
                        "reason": "new_reply_unread",
                        "count": 3,
                        "next_step": "Review.",
                        "items": [
                            {
                                "applicant_ref": "r1",
                                "name": "Alice",
                                "position": "Engineer",
                                "status": "New",
                                "submitted": "2026-09-20",
                                "age_days": 11,
                            },
                            {
                                "applicant_ref": "r2",
                                "name": "Bob",
                                "position": "Manager",
                                "status": "New",
                                "submitted": "2026-09-25",
                                "age_days": 6,
                            },
                            {
                                "applicant_ref": "r3",
                                "name": "Charlie",
                                "position": "Engineer",
                                "status": "New",
                                "submitted": "2026-09-28",
                                "age_days": 3,
                            },
                        ],
                    },
                ],
            }

        items = applicant_items(needs_action=fake_needs_action)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["age_days"], 11)

    def test_context_has_applicants(self):
        """Context contains list of applicants with whitelisted fields."""
        def fake_needs_action():
            return {
                "count": 2,
                "groups": [
                    {
                        "reason": "new_reply_unread",
                        "count": 2,
                        "next_step": "Review.",
                        "items": [
                            {
                                "applicant_ref": "r1",
                                "name": "Alice",
                                "position": "Engineer",
                                "status": "New",
                                "submitted": "2026-09-20",
                                "age_days": 11,
                            },
                            {
                                "applicant_ref": "r2",
                                "name": "Bob",
                                "position": "Manager",
                                "status": "New",
                                "submitted": "2026-09-25",
                                "age_days": 6,
                            },
                        ],
                    },
                ],
            }

        items = applicant_items(needs_action=fake_needs_action)
        item = items[0]
        context = item["context"]

        self.assertIn("applicants", context)
        applicants = context["applicants"]
        self.assertEqual(len(applicants), 2)

        # Each applicant should have whitelisted fields
        for applicant in applicants:
            self.assertIn("applicant_ref", applicant)
            self.assertIn("name", applicant)
            self.assertIn("position", applicant)
            self.assertIn("status", applicant)
            self.assertIn("submitted", applicant)
            self.assertIn("age_days", applicant)

    def test_empty_groups_skipped(self):
        """Groups with no items are skipped."""
        def fake_needs_action():
            return {
                "count": 0,
                "groups": [
                    {
                        "reason": "new_reply_unread",
                        "count": 0,
                        "next_step": "Review.",
                        "items": [],
                    },
                ],
            }

        items = applicant_items(needs_action=fake_needs_action)
        self.assertEqual(len(items), 0)

    def test_empty_response(self):
        """Empty response from needs_action yields no items."""
        def fake_needs_action():
            return {"count": 0, "groups": []}

        items = applicant_items(needs_action=fake_needs_action)
        self.assertEqual(len(items), 0)

    def test_human_review_pending_filtered_others_stay(self):
        def fake():
            row = {"applicant_ref": "r1", "name": "A", "position": "P", "status": "S",
                   "submitted": "2026-09-20", "age_days": 1}
            return {"count": 2, "groups": [
                {"reason": "human_review_pending", "count": 1, "next_step": "x", "items": [row]},
                {"reason": "interview_request_outstanding", "count": 1, "next_step": "y", "items": [row]},
            ]}

        ids = [i["id"] for i in applicant_items(needs_action=fake)]
        self.assertEqual(ids, ["applicants:interview_request_outstanding"])


class CountyItemsTests(unittest.TestCase):
    def test_shape(self):
        def groups():
            return [
                {"county": "Wake", "open_count": 2, "count": 1, "applicants": [
                    {"applicant_ref": "r1", "name": "Al", "position": "Driver", "status": "New",
                     "submitted": "2026-09-20", "city": "Cary", "score": 80,
                     "recommendation": "Advance", "gender": "FORBIDDEN"}]},
                {"county": "Dare", "open_count": 1, "applicants": []},
            ]

        items = county_items(groups_fn=groups)
        self.assertEqual([i["id"] for i in items], ["county:Wake", "county:Dare"])
        w = items[0]
        self.assertEqual(w["tab"], "work")
        self.assertEqual(w["kind"], "county_openings")
        self.assertEqual(w["title"], "Wake - 2 openings")
        self.assertEqual(w["why"], "1 applicant to review")
        self.assertEqual(w["source"], "applicant_executive")
        self.assertEqual(w["context"]["county"], "Wake")
        self.assertEqual(w["context"]["open_count"], 2)
        self.assertEqual(set(w["context"]["applicants"][0]), {
            "applicant_ref", "name", "position", "status", "submitted", "city", "score", "recommendation"})
        self.assertEqual(items[1]["title"], "Dare - 1 opening")
        self.assertNotIn("FORBIDDEN", json.dumps(items))


if __name__ == "__main__":
    unittest.main()
