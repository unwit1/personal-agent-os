"""Credential setup via masked dialogs: stored in the keyring, never echoed."""

from __future__ import annotations

import json
import os
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.orchestrator import secret_prompt, secret_refs  # noqa: E402


class FakeKeyring:
    def __init__(self) -> None:
        self.store: dict[tuple[str, str], str] = {}

    def get_password(self, service, user):
        return self.store.get((service, user))

    def set_password(self, service, user, value):
        self.store[(service, user)] = value

    def delete_password(self, service, user):
        self.store.pop((service, user), None)


class SetupTests(unittest.TestCase):
    def setUp(self) -> None:
        self.keyring = FakeKeyring()
        patcher = mock.patch.object(secret_refs, "_keyring", return_value=self.keyring)
        patcher.start()
        self.addCleanup(patcher.stop)
        for item in secret_prompt.CREDENTIALS:
            os.environ.pop(secret_refs.env_var(item["ref"]), None)

    def test_stores_entered_values_skips_blank_and_never_returns_them(self) -> None:
        answers = iter(["rp-secret-123", "", None, None])  # runpod, openrouter, huggingface, local endpoint
        prompts = []
        results = secret_prompt.setup(prompt=lambda title, message: prompts.append((title, message)) or next(answers))
        self.assertEqual([r["action"] for r in results], ["stored", "skipped", "skipped", "skipped"])
        self.assertEqual(self.keyring.store[("agent-os", "runpod/default")], "rp-secret-123")
        self.assertNotIn("rp-secret-123", json.dumps(results))
        self.assertIn("Credential Manager", prompts[0][1])
        self.assertIn("Read-only", prompts[0][1])

    def test_configured_credentials_are_kept_unless_reprompted(self) -> None:
        self.keyring.set_password("agent-os", "runpod/default", "old")
        kept = secret_prompt.setup(["secrets://runpod/default"], prompt=lambda *a: self.fail("should not prompt"))
        self.assertEqual(kept[0]["action"], "kept (already configured)")
        replaced = secret_prompt.setup(["secrets://runpod/default"], prompt=lambda *a: "new", skip_configured=False)
        self.assertEqual((replaced[0]["action"], self.keyring.store[("agent-os", "runpod/default")]), ("stored", "new"))

    def test_custom_refs_are_validated(self) -> None:
        with self.assertRaises(ValueError):
            secret_prompt.setup(["not-a-ref"], prompt=lambda *a: "x")
        result = secret_prompt.setup(["secrets://my-endpoint/prod"], prompt=lambda *a: "k")
        self.assertEqual((result[0]["action"], self.keyring.store[("agent-os", "my-endpoint/prod")]), ("stored", "k"))


if __name__ == "__main__":
    unittest.main()
