from __future__ import annotations

import shutil
import unittest
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os import changes, forms, improvements
from agent_os.chat import resolve_project
from agent_os.compiler import compile_context
from agent_os.mcp_server import _handle_mcp, methods
from agent_os.registry import get_project
from agent_os.storage import write_json


class CaptureSystemTests(unittest.TestCase):
    def setUp(self) -> None:
        scratch = Path(__file__).resolve().parents[1] / ".tmp"
        scratch.mkdir(exist_ok=True)
        self.root = scratch / f"capture-system-{uuid.uuid4()}"
        self.root.mkdir()
        self.original_change_root = changes.ROOT
        self.original_improvement_root = improvements.ROOT
        changes.ROOT = self.root
        improvements.ROOT = self.root

    def tearDown(self) -> None:
        changes.ROOT = self.original_change_root
        improvements.ROOT = self.original_improvement_root
        shutil.rmtree(self.root)

    def test_change_lifecycle_dedupe_projection_and_promotion_gate(self) -> None:
        supplied = {
            "title": "Keep change context compact",
            "request_summary": "Return only task-relevant change summaries.",
            "change_type": "performance",
            "components": ["context compiler"],
            "google_eligible": True,
            "reusable_candidate": True,
        }
        created = changes.capture_change("personal-agent-os", **supplied)
        duplicate = changes.capture_change("personal-agent-os", **supplied)
        self.assertTrue(created["created"])
        self.assertEqual(duplicate["duplicate_of"], created["record"]["change_id"])
        change_id = created["record"]["change_id"]
        changes.update_change("personal-agent-os", change_id, status="ANALYZED", diagnosis_summary="Full records consumed unnecessary context.")
        changes.update_change("personal-agent-os", change_id, status="PROPOSED", fix_summary="Use compact scored summaries.", reusable_lesson="Budget durable context before loading details.")
        changes.update_change("personal-agent-os", change_id, status="IMPLEMENTED", implementation={"files_changed": ["src/agent_os/compiler.py"], "tests": ["unit tests passed"]})
        verified = changes.update_change("personal-agent-os", change_id, status="VERIFIED", validation_summary="Context remained inside its budget.")
        self.assertEqual(verified["status"], "VERIFIED")
        projection = changes.google_safe_projection("personal-agent-os", change_id)
        self.assertTrue(projection["allowed"])
        self.assertNotIn("repository_files", projection["projection"])

    def test_change_privacy_gate_rejects_personal_data(self) -> None:
        with self.assertRaises(ValueError):
            changes.capture_change("personal-agent-os", "Unsafe", "Contact person@example.com for the source file")

    def test_improvement_dedupe_search_and_transition(self) -> None:
        supplied = {
            "title": "Avoid loading unmatched skills",
            "category": "performance",
            "observation": "Skill bodies add context even when they do not match the task.",
            "suggested_direction": "Retrieve metadata first and load one selected skill.",
            "acceptance": ["Unmatched skill bodies are absent from context."],
            "evidence": ["context measurement"],
        }
        created = improvements.capture_improvement("personal-agent-os", **supplied)
        duplicate = improvements.capture_improvement("personal-agent-os", **supplied)
        self.assertTrue(created["created"])
        self.assertEqual(duplicate["duplicate_of"], created["record"]["id"])
        found = improvements.search_improvements("personal-agent-os", "unmatched skills")
        self.assertEqual(found[0]["id"], created["record"]["id"])
        ready = improvements.update_improvement("personal-agent-os", created["record"]["id"], status="ready")
        self.assertEqual(ready["status"], "ready")
        self.assertIn(created["record"]["id"], improvements.issue_payload("personal-agent-os", ready["id"])["marker"])
        packet = compile_context("personal-agent-os", "avoid loading unmatched skills", token_budget=1200)
        compact = packet["development_context"]["improvements"][0]
        self.assertEqual(compact["id"], created["record"]["id"])
        self.assertNotIn("observation", compact)
        self.assertTrue(packet["context_measurement"]["within_budget"])

    def test_form_routing_is_sanitized_and_local_only(self) -> None:
        original_registry = forms.FORM_REGISTRY
        try:
            candidate = {
                "source_agent": "codex",
                "classification": {"work_related": True, "form_document": True, "confidence": 0.99},
                "form": {"family": "personnel", "type": "action", "variant": None},
                "fingerprint": {
                    "page_count": 2,
                    "title_tokens": ["Personnel Action"],
                    "section_labels": ["Position Change"],
                    "field_labels": ["Employee Name: Jane Example", "Effective Date"],
                    "features": {"has_checkboxes": True, "has_signature_area": True, "has_table_layout": False},
                },
                "match": {"known_form_id": None, "similarity": 0},
                "candidate_action": "new_form",
            }
            safe = forms.sanitize_form_candidate(candidate)
            self.assertEqual(safe["fingerprint"]["field_labels"][0], "Employee Name")
            registry_path = self.root / "forms" / "registry.json"
            write_json(registry_path, {"schema": "personal-agent/form-registry/v1", "version": 1, "forms": [{"id": "personnel-action-v1", "family": "personnel", "type": "action", "skill_path": "skills/personnel-action/SKILL.md", "page_count_range": [1, 2], "anchors": ["personnel action", "position change", "employee name", "effective date"], "signature": safe["fingerprint"]["signature"]["label_sha256"]}]})
            forms.FORM_REGISTRY = registry_path
            routed = forms.route_form(candidate)
            self.assertEqual(routed["classification"], "known")
            self.assertFalse(routed["persisted"])
            unsafe = dict(candidate)
            unsafe["raw_text"] = "private source"
            with self.assertRaises(ValueError):
                forms.route_form(unsafe)
            skipped = forms.route_form({"classification": {"work_related": False, "form_document": False, "confidence": 0.9}})
            self.assertEqual(skipped["classification"], "not_work_form")
        finally:
            forms.FORM_REGISTRY = original_registry

    def test_scan_renamer_redirect_and_weak_scanner_signal(self) -> None:
        self.assertEqual(get_project("scan-renamer")["id"], "hr-gui")
        self.assertEqual(resolve_project("document renamer")["project"]["id"], "hr-gui")
        self.assertIsNone(resolve_project("scanner")["project"])

    def test_capture_methods_are_available_without_expanding_default_context(self) -> None:
        available = methods()
        for name in ("change.capture", "change.get", "change.update", "change.google_safe_projection", "improvement.capture", "improvement.search", "form.route", "form.issue_payload"):
            self.assertIn(name, available)
        tools = _handle_mcp({"jsonrpc": "2.0", "id": 1, "method": "tools/list"}, available)
        tool_names = {tool["name"] for tool in tools["result"]["tools"]}
        self.assertIn("change.capture", tool_names)
        self.assertIn("improvement.capture", tool_names)
        self.assertIn("form.route", tool_names)


if __name__ == "__main__":
    unittest.main()
