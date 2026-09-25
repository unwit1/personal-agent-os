from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agent_os.people import PeopleStore


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


if __name__ == "__main__":
    unittest.main()
