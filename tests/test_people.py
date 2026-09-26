from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agent_os.people import PeopleStore, bootstrap_from_sanitized_context


class PeopleStoreTests(unittest.TestCase):
    def test_same_alias_does_not_merge_people(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with PeopleStore(Path(tmp) / "people.sqlite3") as store:
                partner = store.upsert_person("Olivia", person_id="person:partner", domain="personal", identity_confidence=1.0)
                workplace = store.upsert_person("Olivia", person_id="person:work-olivia", domain="work", identity_confidence=0.6)
                store.add_alias(partner, "Olivia", source_ref="direct-user", identity_confidence=1.0)
                store.add_alias(workplace, "Olivia", source_ref="work-mail", identity_confidence=0.6)
                matches = store.alias_candidates("Olivia")
                self.assertEqual({item["person_id"] for item in matches}, {partner, workplace})

    def test_identity_and_relationship_confidence_are_separate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with PeopleStore(Path(tmp) / "people.sqlite3") as store:
                subject = store.upsert_person("User", person_id="person:user", identity_confidence=1.0)
                other = store.upsert_person("Example", person_id="person:example", identity_confidence=0.95)
                edge = store.add_relationship(
                    subject,
                    "knows",
                    object_id=other,
                    identity_confidence=0.95,
                    relationship_confidence=0.4,
                )
                row = store.conn.execute(
                    "SELECT identity_confidence,relationship_confidence FROM relationships WHERE edge_id=?",
                    (edge,),
                ).fetchone()
                self.assertEqual(row["identity_confidence"], 0.95)
                self.assertEqual(row["relationship_confidence"], 0.4)

    def test_evidence_requires_explicit_actor_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with PeopleStore(Path(tmp) / "people.sqlite3") as store:
                person = store.upsert_person("Example")
                with self.assertRaises(ValueError):
                    store.add_evidence(
                        "person",
                        person,
                        source_type="chat",
                        source_ref="x",
                        source_actor="owner_means_user",
                    )

    def test_evidence_keeps_actor_and_subject_separate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with PeopleStore(Path(tmp) / "people.sqlite3") as store:
                person = store.upsert_person("Applicant", person_id="person:applicant", domain="work")
                evidence = store.add_evidence(
                    "person",
                    person,
                    source_type="mail",
                    source_ref="msg:test",
                    source_actor="user",
                    subject_relation="third_party",
                    confidence=0.9,
                )
                row = store.conn.execute(
                    "SELECT source_actor,subject_relation FROM evidence WHERE evidence_id=?",
                    (evidence,),
                ).fetchone()
                self.assertEqual(row["source_actor"], "user")
                self.assertEqual(row["subject_relation"], "third_party")


    def test_bootstrap_from_sanitized_context_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            context = root / "relationship-context.json"
            context.write_text(
                """{
                  "updated_at": "2026-09-25",
                  "durable_relationship_context": {
                    "partner": {
                      "person_id": "person:olivia",
                      "display_name": "Olivia",
                      "identity_confidence": "stated",
                      "relationship_type": "romantic_partner",
                      "relationship_confidence": "stated"
                    },
                    "family": {
                      "sibling_structure": "User is the oldest of five siblings."
                    }
                  },
                  "unresolved_identity_candidates": [
                    {"label": "Olivia (workplace context)", "domain": "work", "reason": "same-name collision"}
                  ]
                }""",
                encoding="utf-8",
            )
            db = root / "people.sqlite3"
            first = bootstrap_from_sanitized_context(context, db_path=db)
            second = bootstrap_from_sanitized_context(context, db_path=db)
            self.assertEqual(first["stats"]["people"], 2)
            self.assertEqual(second["stats"]["people"], 2)
            self.assertEqual(second["stats"]["relationships"], 2)
            self.assertEqual(second["stats"]["identity_candidates"], 1)


    def test_person_temporal_bounds_expand_without_resetting(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with PeopleStore(Path(tmp) / "people.sqlite3") as store:
                pid = store.upsert_person(
                    "Example",
                    person_id="person:example",
                    first_seen="2025-01-01",
                    last_seen="2025-06-01",
                )
                store.upsert_person(
                    "Example",
                    person_id=pid,
                    first_seen="2024-12-01",
                    last_seen="2025-05-01",
                )
                row = store.conn.execute(
                    "SELECT first_seen,last_seen FROM people WHERE person_id=?",
                    (pid,),
                ).fetchone()
                self.assertEqual(row["first_seen"], "2024-12-01")
                self.assertEqual(row["last_seen"], "2025-06-01")

    def test_professional_role_edges_are_separate_from_personal_relationships(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with PeopleStore(Path(tmp) / "people.sqlite3") as store:
                person = store.upsert_person("Regina", person_id="person:regina-work", domain="work")
                org = store.upsert_organization("Example Org", org_id="org:example", domain="work")
                edge = store.link_person_organization_role(
                    person,
                    org,
                    role_label="HR contact",
                    process_context="onboarding",
                    valid_from="2026-04",
                    relationship_confidence=0.8,
                )
                roles = store.organization_roles_for(person)
                self.assertEqual(len(roles), 1)
                self.assertEqual(roles[0]["role_edge_id"], edge)
                self.assertEqual(roles[0]["organization_name"], "Example Org")
                self.assertEqual(store.relationships_for(person), [])


if __name__ == "__main__":
    unittest.main()
