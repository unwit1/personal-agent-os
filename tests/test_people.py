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


if __name__ == "__main__":
    unittest.main()
