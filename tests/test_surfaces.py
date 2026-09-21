from __future__ import annotations

import json
import shutil
import sys
import unittest
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os import surfaces as surface_module
from agent_os.cli import parser
from agent_os.launcher import LAUNCHER_PATH
from agent_os.machine import resolve_user_path
from agent_os.paths import ROOT
from agent_os.surfaces import (
    SURFACE_REGISTRY_PATH,
    SURFACE_REGISTRY_SCHEMA,
    TIERS,
    health,
    surfaces,
)


def _scratch() -> Path:
    path = ROOT / ".tmp" / f"surfaces-{uuid.uuid4()}"
    path.mkdir(parents=True)
    return path


def _fake_checkout(root: Path) -> Path:
    (root / "src" / "agent_os").mkdir(parents=True)
    (root / "agent.py").write_text("# stand-in entry point\n", encoding="utf-8")
    return root


def _registration_file(path: Path, command: str, args: list[str], server: str = "agent-os") -> Path:
    path.write_text(
        json.dumps({"mcpServers": {server: {"type": "stdio", "command": command, "args": args}}}),
        encoding="utf-8",
    )
    return path


def _surface(**overrides: object) -> dict:
    surface = {
        "id": "probe",
        "name": "Probe",
        "vendor": "test",
        "mechanism": "mcp_stdio",
        "expected_tier": "routed",
        "summary": "synthetic surface",
        "invocation": {"kind": "mcp_stdio", "server_keys": ["agent-os"], "registrations": [], "prefers_stable_launcher": True},
        "instruction": {"kind": "instruction_file", "locations": [], "marker": "Agent OS"},
        "capture": {"kind": "mcp_tools", "tools": ["agent.capture_candidates", "agent.latest_handoff"], "automatic": True},
    }
    surface.update(overrides)
    return surface


class SurfaceRegistryTests(unittest.TestCase):
    def test_registry_uses_the_supported_schema_with_unique_ids(self) -> None:
        registry = json.loads(SURFACE_REGISTRY_PATH.read_text(encoding="utf-8"))
        self.assertEqual(registry["schema"], SURFACE_REGISTRY_SCHEMA)
        ids = [item["id"] for item in registry["surfaces"]]
        self.assertEqual(len(ids), len(set(ids)))

    def test_claude_code_is_a_first_class_registered_surface(self) -> None:
        surface = next(item for item in surfaces() if item["id"] == "claude-code")
        self.assertEqual(surface["expected_tier"], "routed")
        self.assertEqual(surface["invocation"]["kind"], "mcp_stdio")
        self.assertTrue(surface["invocation"]["prefers_stable_launcher"])
        self.assertTrue(surface["instruction"]["locations"])

    def test_registry_stores_no_machine_specific_paths(self) -> None:
        text = SURFACE_REGISTRY_PATH.read_text(encoding="utf-8")
        self.assertNotIn(":\\\\", text)
        self.assertNotIn("/Users/", text)

    def test_declared_locations_resolve_through_the_machine_layer(self) -> None:
        for surface in surfaces():
            locations = [*surface["invocation"].get("registrations", []), *surface["instruction"].get("locations", [])]
            for location in locations:
                with self.subTest(surface=surface["id"], location=location):
                    resolved = resolve_user_path(location)
                    self.assertTrue(resolved.is_absolute(), f"{location} did not resolve to an absolute path")

    def test_repository_locations_exist(self) -> None:
        for surface in surfaces():
            for location in surface["instruction"].get("locations", []):
                if location.startswith("repo/"):
                    with self.subTest(location=location):
                        self.assertTrue(resolve_user_path(location).exists())

    def test_unsupported_schema_is_rejected(self) -> None:
        original = surface_module.load_json
        surface_module.load_json = lambda path: {"schema": "other/v9", "surfaces": []}
        try:
            with self.assertRaises(ValueError):
                surfaces()
        finally:
            surface_module.load_json = original


class TierDerivationTests(unittest.TestCase):
    def _tier(self, registered: bool, reachable: bool, canonical: bool, preflighted: bool) -> str:
        invocation = {"registered": registered, "reachable": reachable, "canonical_checkout": canonical}
        return surface_module._tier(invocation, {"preflighted": preflighted})

    def test_fully_routed_requires_canonical_reachability_and_preflight(self) -> None:
        self.assertEqual(self._tier(True, True, True, True), "routed")

    def test_invocation_without_preflight_is_only_bridged(self) -> None:
        self.assertEqual(self._tier(True, True, True, False), "bridged")

    def test_preflight_without_invocation_is_only_bridged(self) -> None:
        self.assertEqual(self._tier(False, False, False, True), "bridged")

    def test_registration_that_cannot_be_reached_is_only_bridged(self) -> None:
        self.assertEqual(self._tier(True, False, False, True), "bridged")

    def test_reachable_but_non_canonical_checkout_is_only_bridged(self) -> None:
        self.assertEqual(self._tier(True, True, False, True), "bridged")

    def test_nothing_present_is_not_integrated(self) -> None:
        self.assertEqual(self._tier(False, False, False, False), "unintegrated")

    def test_tier_order_runs_from_unintegrated_to_routed(self) -> None:
        self.assertEqual(TIERS, ("unintegrated", "bridged", "routed"))


class SurfaceProbeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.scratch = _scratch()
        self.addCleanup(shutil.rmtree, self.scratch, True)

    def _instruction(self, text: str = "Consult Agent OS before substantial work.\n") -> Path:
        path = self.scratch / "INSTRUCTION.md"
        path.write_text(text, encoding="utf-8")
        return path

    def test_canonical_registration_with_preflight_is_fully_routed(self) -> None:
        config = _registration_file(self.scratch / "client.json", "python", [str(ROOT / "agent.py"), "mcp"])
        surface = _surface(
            invocation={"kind": "mcp_stdio", "server_keys": ["agent-os"], "registrations": [str(config)], "prefers_stable_launcher": False},
            instruction={"kind": "instruction_file", "locations": [str(self._instruction())], "marker": "Agent OS"},
        )
        invocation = surface_module._probe_invocation(surface)
        instruction = surface_module._probe_instruction(surface, invocation)
        self.assertTrue(invocation["registered"])
        self.assertTrue(invocation["reachable"])
        self.assertTrue(invocation["canonical_checkout"])
        self.assertEqual(surface_module._tier(invocation, instruction), "routed")

    def test_registration_pointing_at_a_missing_checkout_is_unreachable(self) -> None:
        config = _registration_file(self.scratch / "client.json", "python", [str(self.scratch / "gone" / "agent.py"), "mcp"])
        surface = _surface(invocation={"kind": "mcp_stdio", "server_keys": ["agent-os"], "registrations": [str(config)]})
        invocation = surface_module._probe_invocation(surface)
        self.assertTrue(invocation["registered"])
        self.assertFalse(invocation["reachable"])
        gaps = surface_module._missing(surface, invocation, {"kind": "none", "preflighted": False}, {"handoffs": False, "candidates": False, "automatic": True, "detail": None})
        self.assertTrue(any("does not resolve" in gap for gap in gaps))

    def test_registration_pointing_at_another_checkout_is_not_canonical(self) -> None:
        other = _fake_checkout(self.scratch / "other-checkout")
        config = _registration_file(self.scratch / "client.json", "python", [str(other / "agent.py"), "mcp"])
        surface = _surface(invocation={"kind": "mcp_stdio", "server_keys": ["agent-os"], "registrations": [str(config)]})
        invocation = surface_module._probe_invocation(surface)
        self.assertTrue(invocation["reachable"])
        self.assertFalse(invocation["canonical_checkout"])
        gaps = surface_module._missing(surface, invocation, {"kind": "none", "preflighted": False}, {"handoffs": True, "candidates": True, "automatic": True, "detail": None})
        self.assertTrue(any("non-canonical checkout" in gap for gap in gaps))

    def test_unregistered_client_is_not_integrated(self) -> None:
        surface = _surface(
            invocation={"kind": "mcp_stdio", "server_keys": ["agent-os"], "registrations": [str(self.scratch / "absent.json")]},
            instruction={"kind": "instruction_file", "locations": [str(self.scratch / "absent.md")], "marker": "Agent OS"},
        )
        invocation = surface_module._probe_invocation(surface)
        instruction = surface_module._probe_instruction(surface, invocation)
        self.assertFalse(invocation["registered"])
        self.assertFalse(instruction["preflighted"])
        self.assertEqual(surface_module._tier(invocation, instruction), "unintegrated")

    def test_stable_launcher_registration_is_recognized_as_stable(self) -> None:
        config = _registration_file(self.scratch / "client.json", "python", [str(LAUNCHER_PATH)])
        surface = _surface(invocation={"kind": "mcp_stdio", "server_keys": ["agent-os"], "registrations": [str(config)], "prefers_stable_launcher": True})
        invocation = surface_module._probe_invocation(surface)
        self.assertTrue(invocation["stable_launcher"])

    def test_embedded_checkout_path_is_reported_as_an_unstable_registration(self) -> None:
        config = _registration_file(self.scratch / "client.json", "python", [str(ROOT / "agent.py"), "mcp"])
        surface = _surface(invocation={"kind": "mcp_stdio", "server_keys": ["agent-os"], "registrations": [str(config)], "prefers_stable_launcher": True})
        invocation = surface_module._probe_invocation(surface)
        self.assertFalse(invocation["stable_launcher"])
        gaps = surface_module._missing(surface, invocation, {"kind": "none", "preflighted": False}, {"handoffs": True, "candidates": True, "automatic": True, "detail": None})
        self.assertTrue(any("stable launcher" in gap for gap in gaps))

    def test_toml_registrations_are_read_without_a_toml_dependency(self) -> None:
        config = self.scratch / "config.toml"
        config.write_text(
            "[mcp_servers.node_repl]\ncommand = \"node\"\n\n"
            f"[mcp_servers.agent-os]\ncommand = \"python\"\nargs = ['{ROOT / 'agent.py'}', \"mcp\"]\n\n"
            "[other]\nvalue = 1\n",
            encoding="utf-8",
        )
        surface = _surface(invocation={"kind": "mcp_stdio", "server_keys": ["agent-os"], "registrations": [str(config)]})
        invocation = surface_module._probe_invocation(surface)
        self.assertTrue(invocation["registered"])
        self.assertTrue(invocation["canonical_checkout"])

    def test_instruction_file_without_the_marker_is_not_a_preflight(self) -> None:
        surface = _surface(instruction={"kind": "instruction_file", "locations": [str(self._instruction("Unrelated guidance.\n"))], "marker": "Agent OS"})
        instruction = surface_module._probe_instruction(surface, {"reachable": False})
        self.assertFalse(instruction["preflighted"])
        self.assertIn("does not mention", instruction["detail"])

    def test_server_instructions_only_preflight_a_client_that_can_connect(self) -> None:
        surface = _surface(instruction={"kind": "server_instructions", "marker": "agent.context"})
        self.assertFalse(surface_module._probe_instruction(surface, {"reachable": False})["preflighted"])
        self.assertTrue(surface_module._probe_instruction(surface, {"reachable": True})["preflighted"])

    def test_bridge_document_preflights_a_client_that_cannot_invoke(self) -> None:
        surface = _surface(
            mechanism="manual_bridge",
            expected_tier="bridged",
            invocation={"kind": "none", "reason": "the host cannot start a local stdio server"},
            instruction={"kind": "bridge_document", "locations": ["repo/skills/regular-chat-router/SKILL.md"], "marker": "Agent OS"},
            capture={"kind": "cli_bridge", "commands": ["capture-candidates", "handoff"], "automatic": False},
        )
        invocation = surface_module._probe_invocation(surface)
        instruction = surface_module._probe_instruction(surface, invocation)
        capture = surface_module._probe_capture(surface, invocation)
        self.assertFalse(invocation["registered"])
        self.assertTrue(instruction["preflighted"])
        self.assertTrue(capture["handoffs"] and capture["candidates"])
        self.assertEqual(surface_module._tier(invocation, instruction), "bridged")


class CaptureCapabilityTests(unittest.TestCase):
    def test_mcp_capture_requires_a_reachable_server(self) -> None:
        surface = _surface()
        unreachable = surface_module._probe_capture(surface, {"reachable": False})
        self.assertFalse(unreachable["handoffs"])
        self.assertFalse(unreachable["candidates"])
        self.assertIn("cannot reach", unreachable["detail"])
        reachable = surface_module._probe_capture(surface, {"reachable": True})
        self.assertTrue(reachable["handoffs"] and reachable["candidates"])

    def test_missing_capture_tools_are_named(self) -> None:
        surface = _surface(capture={"kind": "mcp_tools", "tools": ["agent.not_a_tool"], "automatic": True})
        capture = surface_module._probe_capture(surface, {"reachable": True})
        self.assertFalse(capture["candidates"])
        self.assertIn("agent.not_a_tool", capture["detail"])

    def test_cli_bridge_capture_is_checked_against_the_real_cli(self) -> None:
        surface = _surface(capture={"kind": "cli_bridge", "commands": ["capture-candidates", "handoff"], "automatic": False})
        capture = surface_module._probe_capture(surface, {"reachable": False})
        self.assertTrue(capture["handoffs"] and capture["candidates"])
        self.assertFalse(capture["automatic"])

    def test_cli_bridge_reports_a_command_the_cli_does_not_provide(self) -> None:
        surface = _surface(capture={"kind": "cli_bridge", "commands": ["not-a-command"], "automatic": True})
        capture = surface_module._probe_capture(surface, {"reachable": True})
        self.assertFalse(capture["handoffs"])
        self.assertIn("not-a-command", capture["detail"])

    def test_a_surface_with_no_capture_path_emits_nothing(self) -> None:
        surface = _surface(capture={"kind": "none", "automatic": False, "reason": "read-only client"})
        capture = surface_module._probe_capture(surface, {"reachable": True})
        self.assertFalse(capture["handoffs"] or capture["candidates"])
        self.assertEqual(capture["detail"], "read-only client")


class IntegrationHealthReportTests(unittest.TestCase):
    def setUp(self) -> None:
        self.report = health()

    def test_report_covers_every_registered_surface(self) -> None:
        self.assertEqual([item["id"] for item in self.report["surfaces"]], [item["id"] for item in surfaces()])
        self.assertEqual(sum(self.report["counts"].values()), len(self.report["surfaces"]))

    def test_every_surface_reports_the_required_health_fields(self) -> None:
        required = {"id", "name", "mechanism", "registered", "reachable", "tier", "tier_label", "expected_tier", "automatic_preflight", "emits_handoffs", "emits_candidates", "missing"}
        for surface in self.report["surfaces"]:
            with self.subTest(surface=surface["id"]):
                self.assertTrue(required.issubset(surface), f"missing {sorted(required - set(surface))}")
                self.assertIn(surface["tier"], TIERS)
                self.assertIsInstance(surface["missing"], list)

    def test_counts_use_the_roadmap_tier_vocabulary(self) -> None:
        self.assertEqual(set(self.report["counts"]), set(TIERS))
        labels = {surface["tier_label"] for surface in self.report["surfaces"]}
        self.assertTrue(labels.issubset({"fully routed", "partially bridged", "not yet integrated"}))

    def test_claude_code_reports_as_a_reachable_routed_surface(self) -> None:
        surface = next(item for item in self.report["surfaces"] if item["id"] == "claude-code")
        self.assertTrue(surface["registered"], "Claude Code has no Agent OS MCP registration on this machine")
        self.assertTrue(surface["reachable"])
        self.assertEqual(surface["tier"], "routed")
        self.assertTrue(surface["emits_handoffs"] and surface["emits_candidates"])

    def test_a_surface_below_its_expected_tier_is_listed_as_degraded(self) -> None:
        degraded = set(self.report["degraded"])
        for surface in self.report["surfaces"]:
            with self.subTest(surface=surface["id"]):
                self.assertEqual(surface["id"] in degraded, not surface["meets_expectation"])
                if not surface["meets_expectation"]:
                    self.assertTrue(surface["missing"], "a degraded surface must say what is missing")
        self.assertEqual(self.report["ok"], not degraded)

    def test_a_surface_can_be_reported_on_its_own(self) -> None:
        single = health("claude-code")
        self.assertEqual(len(single["surfaces"]), 1)
        self.assertEqual(single["surfaces"][0]["id"], "claude-code")

    def test_an_unknown_surface_is_rejected(self) -> None:
        with self.assertRaises(KeyError):
            health("no-such-client")


class IntegrationHealthCommandTests(unittest.TestCase):
    def test_command_parses_with_its_filters(self) -> None:
        args = parser().parse_args(["integration-health", "--surface", "claude-code", "--strict"])
        self.assertEqual(args.command, "integration-health")
        self.assertEqual(args.surface, "claude-code")
        self.assertTrue(args.strict)

    def test_command_defaults_to_a_report_over_every_surface(self) -> None:
        args = parser().parse_args(["integration-health"])
        self.assertIsNone(args.surface)
        self.assertFalse(args.strict)


if __name__ == "__main__":
    unittest.main()
