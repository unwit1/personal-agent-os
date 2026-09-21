from __future__ import annotations

import json
import shutil
import sys
import unittest
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os import improvements, machine
from agent_os.chat import resolve_project
from agent_os.compiler import _fit, compile_context
from agent_os.inventory import scan
from agent_os.launcher import LAUNCHER_SOURCE, status as launcher_status
from agent_os.mcp_server import SUPPORTED_PROTOCOL_VERSIONS, _handle_mcp, methods, negotiate_protocol_version
from agent_os.paths import ROOT
from agent_os.registry import canonical_projects, get_project, load_state, projects
from agent_os.routing import REPOSITORY_TOKEN, render, status as routing_status
from agent_os.skills import discover
from agent_os.storage import load_json


class PortablePathTests(unittest.TestCase):
    def test_canonical_registry_has_no_machine_specific_paths(self) -> None:
        for project in canonical_projects():
            self.assertNotIn("path", project, f"{project['id']} stores an absolute checkout path in Git")
            self.assertTrue(project.get("directory"), f"{project['id']} has no portable directory identity")

    def test_every_project_resolves_to_a_local_path(self) -> None:
        for project in projects():
            self.assertNotEqual(project["path_source"], "unresolved", f"{project['id']} did not resolve")
            self.assertTrue(Path(project["path"]).is_dir(), f"{project['id']} resolved to a missing directory")

    def test_agent_os_resolves_to_this_checkout_without_configuration(self) -> None:
        project = get_project("personal-agent-os")
        self.assertEqual(Path(project["path"]).resolve(), ROOT.resolve())
        self.assertEqual(project["path_source"], "this_repository")

    def test_local_override_takes_precedence(self) -> None:
        entry = dict(canonical_projects()[1])
        target = ROOT / "tests"
        original = machine.local_config
        machine.local_config = lambda: {"project_paths": {entry["id"]: str(target)}, "search_roots": []}
        try:
            path, source = machine.resolve_path(entry, [])
            self.assertEqual(Path(path).resolve(), target.resolve())
            self.assertEqual(source, "local_override")
        finally:
            machine.local_config = original

    def test_search_roots_are_bounded_and_never_a_drive_root(self) -> None:
        roots = machine.search_roots()
        self.assertTrue(roots)
        for root in roots:
            self.assertNotEqual(root, root.parent, "a drive root would cause an unbounded crawl")


class SkillDiscoveryTests(unittest.TestCase):
    def test_canonical_skill_root_is_never_discovered_twice(self) -> None:
        project = get_project("personal-agent-os")
        state = load_state(project)
        self.assertIn("skills", state["skill_roots"], "this regression needs the overlapping canonical root")
        skills = discover(Path(project["path"]), state["skill_roots"])
        names = [skill.name for skill in skills]
        self.assertEqual(len(names), len(set(names)), f"duplicate skills: {sorted({n for n in names if names.count(n) > 1})}")

    def test_alternate_checkout_of_the_same_repository_does_not_duplicate_skills(self) -> None:
        """A second clone reaches the same skill names by a different path."""
        skills = discover(ROOT, [".agents/skills", "skills", "../personal-agent-os/skills"])
        names = [skill.name for skill in skills]
        self.assertEqual(len(names), len(set(names)))

    def test_project_local_skills_are_still_discovered(self) -> None:
        project = get_project("hr-gui")
        skills = discover(Path(project["path"]), load_state(project)["skill_roots"])
        self.assertTrue(any(skill.source == "project" for skill in skills))
        self.assertTrue(any(skill.source == "agent-os" for skill in skills))

    def test_skill_bodies_are_not_loaded_by_default(self) -> None:
        packet = compile_context("personal-agent-os", "skill discovery", token_budget=1200)
        self.assertFalse(packet["context_policy"]["full_skill_bodies_loaded"])
        for skill in packet.get("matched_skills", []):
            self.assertNotIn("content", skill)


class InventoryTests(unittest.TestCase):
    def test_inventory_spans_every_registered_parent_directory(self) -> None:
        inventory = scan()
        roots = {root.casefold() for root in inventory["projects_roots"]}
        expected = {str(Path(item["path"]).resolve().parent).casefold() for item in projects()}
        self.assertTrue(expected.issubset(roots), f"missing roots: {expected - roots}")
        self.assertGreater(len(roots), 1, "this machine stores projects under more than one parent")

    def test_alternate_checkout_is_attributed_to_its_registered_project(self) -> None:
        inventory = scan()
        alternates = [item for item in inventory["projects"] if item.get("alternate_checkout")]
        for item in alternates:
            self.assertTrue(item["registered_as"])
        self.assertEqual(inventory["unregistered"], [])

    def test_explicit_root_still_scans_only_that_root(self) -> None:
        inventory = scan(ROOT.parent)
        self.assertEqual(inventory["projects_roots"], [str(ROOT.parent.resolve())])


class RoutingTests(unittest.TestCase):
    def test_agent_os_domain_vocabulary_resolves_without_naming_the_project(self) -> None:
        for query in (
            "Why is the JSON RPC stdio server returning an error?",
            "The MCP server handshake fails during stdio startup",
            "Context packet blew past its token budget",
        ):
            with self.subTest(query=query):
                self.assertEqual(resolve_project(query)["project"]["id"], "personal-agent-os")

    def test_generic_coding_requests_do_not_route(self) -> None:
        for query in (
            "Why is my python script returning an error?",
            "How do I write a unit test for a date parser?",
            "What is a good way to structure a server module?",
        ):
            with self.subTest(query=query):
                self.assertIsNone(resolve_project(query)["project"], f"{query} routed to a project")

    def test_explicit_project_names_still_win(self) -> None:
        self.assertEqual(resolve_project("Please review Personal Agent OS context routing")["project"]["id"], "personal-agent-os")
        self.assertEqual(resolve_project("the scan renamer mangles filenames")["project"]["id"], "hr-gui")

    def test_ambiguity_handling_is_preserved(self) -> None:
        resolution = resolve_project("update the readme")
        self.assertTrue(resolution["project"] is None or resolution["confidence"] in {"inferred", "explicit"})


class ContextBudgetTests(unittest.TestCase):
    def _packet(self) -> dict:
        filler = {"summary": "x" * 400, "detail": "y" * 400}
        return {
            "project": "personal-agent-os",
            "task": "avoid loading unmatched skills",
            "latest_agent_os_handoff": {"completed": ["a" * 600], "remaining": ["b" * 600]},
            "state": {
                "summary": "compact summary",
                "current_priorities": ["c" * 600],
                "constraints": ["d" * 400],
                "important_paths": ["e" * 400],
                "validation_commands": ["f" * 400],
            },
            "search_matches": [dict(filler) for _ in range(6)],
            "matched_skills": [dict(filler) for _ in range(3)],
            "development_context": {"improvements": [{"id": "IMP-1", "title": "most relevant"}, {"id": "IMP-2", "title": "less relevant"}]},
        }

    def test_generic_bulk_is_pruned_before_task_relevant_development_context(self) -> None:
        packet, _ = _fit(self._packet(), 400)
        self.assertEqual(packet["development_context"]["improvements"][0]["id"], "IMP-1")
        handoff = packet["latest_agent_os_handoff"]
        self.assertNotIn("completed", handoff, "the previous handoff's finished narrative is generic bulk")
        self.assertNotIn("validation", handoff, "recorded validation output is generic bulk")

    def test_handoff_next_action_outlives_generic_project_state(self) -> None:
        """A handoff's open work is the next action, not verbose history.

        Shedding the whole handoff first also discards what to do next, which
        is among the most actionable context a fresh session can be given.
        """
        packet, _ = _fit(self._packet(), 400)
        self.assertIn("remaining", packet["latest_agent_os_handoff"])
        self.assertFalse(packet["search_matches"], "lexical matches rank below the next action")
        self.assertFalse(packet["matched_skills"], "skill metadata ranks below the next action")

    def test_remaining_work_is_the_last_handoff_field_to_go(self) -> None:
        packet, _ = _fit(self._packet(), 250)
        handoff = packet["latest_agent_os_handoff"]
        if handoff:
            self.assertEqual(set(handoff), {"remaining"})

    def test_state_pruning_keeps_the_summary_longest(self) -> None:
        packet, _ = _fit(self._packet(), 300)
        if packet.get("state"):
            self.assertIn("summary", packet["state"])
            self.assertNotIn("validation_commands", packet["state"])

    def test_top_development_entry_survives_until_the_budget_forces_it_out(self) -> None:
        packet, _ = _fit(self._packet(), 260)
        self.assertFalse(packet["search_matches"])
        self.assertFalse(packet["matched_skills"])

    def test_real_packet_keeps_matched_development_context_within_budget(self) -> None:
        scratch = ROOT / ".tmp"
        scratch.mkdir(exist_ok=True)
        temporary = scratch / f"budget-{uuid.uuid4()}"
        temporary.mkdir()
        original = improvements.ROOT
        improvements.ROOT = temporary
        try:
            created = improvements.capture_improvement(
                "personal-agent-os",
                title="Avoid loading unmatched skills",
                category="performance",
                observation="Skill bodies add context even when they do not match the task.",
                suggested_direction="Retrieve metadata first and load one selected skill.",
                acceptance=["Unmatched skill bodies are absent from context."],
                evidence=["context measurement"],
            )
            packet = compile_context("personal-agent-os", "avoid loading unmatched skills", token_budget=1200)
            self.assertEqual(packet["development_context"]["improvements"][0]["id"], created["record"]["id"])
            self.assertTrue(packet["context_measurement"]["within_budget"])
        finally:
            improvements.ROOT = original
            shutil.rmtree(temporary)

    def test_small_budgets_are_still_respected(self) -> None:
        for budget in (250, 400, 550, 900):
            with self.subTest(budget=budget):
                packet = compile_context("personal-agent-os", "json rpc stdio server error", token_budget=budget)
                self.assertTrue(packet["context_measurement"]["within_budget"])
                self.assertLessEqual(packet["context_measurement"]["estimated_packet_tokens"], max(budget, 250))

    def test_tightest_budget_sheds_generic_core_before_the_task(self) -> None:
        """The last things standing must be the task, not boilerplate.

        A static description of the selection strategy and the project's generic
        summary are the lowest-value fields in the residual core, so a budget
        that cannot fit everything gives those up before truncating the task.
        """
        task = "launcher process exits during the MCP handshake"
        packet = compile_context("personal-agent-os", task, token_budget=250)
        self.assertTrue(packet["context_measurement"]["within_budget"])
        self.assertEqual(packet["task"], task, "the task was cut before generic boilerplate")
        self.assertNotIn("selection", packet["context_policy"])
        self.assertFalse(
            packet["context_policy"]["raw_history_loaded"],
            "the privacy flags must survive every squeeze",
        )

    def test_improvements_survive_the_reported_constrained_budget(self) -> None:
        """The reported failure: a ~1200-token packet dropped improvements."""
        task = "launcher process exits during the MCP handshake"
        if not improvements.compact_improvements("personal-agent-os", task):
            self.skipTest("no improvement matches this task; the fixture test covers the ordering")
        packet = compile_context("personal-agent-os", task, token_budget=1200)
        kept = (packet.get("development_context") or {}).get("improvements") or []
        self.assertTrue(kept, "improvements were pruned entirely at a 1200-token budget")
        self.assertTrue(packet["context_measurement"]["within_budget"])

    def test_raw_history_is_never_loaded(self) -> None:
        packet = compile_context("personal-agent-os", "routing", token_budget=1200)
        self.assertFalse(packet["context_policy"]["raw_history_loaded"])


class McpLifecycleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.available = methods()

    def test_initialize_echoes_a_supported_client_version(self) -> None:
        for version in SUPPORTED_PROTOCOL_VERSIONS:
            with self.subTest(version=version):
                response = _handle_mcp({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": version}}, self.available)
                self.assertEqual(response["result"]["protocolVersion"], version)

    def test_initialize_offers_newest_version_for_unknown_client_version(self) -> None:
        response = _handle_mcp({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "1999-01-01"}}, self.available)
        self.assertEqual(response["result"]["protocolVersion"], SUPPORTED_PROTOCOL_VERSIONS[0])
        self.assertEqual(negotiate_protocol_version(None), SUPPORTED_PROTOCOL_VERSIONS[0])

    def test_initialize_reports_identity_capabilities_and_instructions(self) -> None:
        result = _handle_mcp({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}, self.available)["result"]
        self.assertEqual(result["serverInfo"]["name"], "personal-agent-os")
        self.assertIn("tools", result["capabilities"])
        self.assertIn("agent.context", result["instructions"])

    def test_discovery_alias_agrees_with_initialize(self) -> None:
        initialized = _handle_mcp({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}, self.available)["result"]
        discovered = _handle_mcp({"jsonrpc": "2.0", "id": 2, "method": "server/discover"}, self.available)["result"]
        self.assertEqual(discovered["serverInfo"], initialized["serverInfo"])
        self.assertEqual(discovered["capabilities"], initialized["capabilities"])
        self.assertIn(initialized["protocolVersion"], discovered["supportedVersions"])

    def test_notifications_never_receive_a_response(self) -> None:
        for method in ("notifications/initialized", "notifications/cancelled", "notifications/progress"):
            with self.subTest(method=method):
                self.assertIsNone(_handle_mcp({"jsonrpc": "2.0", "method": method}, self.available))

    def test_ping_is_answered(self) -> None:
        self.assertEqual(_handle_mcp({"jsonrpc": "2.0", "id": 7, "method": "ping"}, self.available)["result"], {})

    def test_unsupported_capability_methods_return_method_not_found(self) -> None:
        response = _handle_mcp({"jsonrpc": "2.0", "id": 8, "method": "resources/list"}, self.available)
        self.assertEqual(response["error"]["code"], -32601)
        self.assertEqual(response["id"], 8)

    def test_tool_call_errors_stay_inside_the_result_envelope(self) -> None:
        response = _handle_mcp({"jsonrpc": "2.0", "id": 9, "method": "tools/call", "params": {"name": "agent.context", "arguments": {}}}, self.available)
        self.assertTrue(response["result"]["isError"])
        self.assertEqual(response["id"], 9)

    def test_unknown_tool_is_reported_without_breaking_the_session(self) -> None:
        response = _handle_mcp({"jsonrpc": "2.0", "id": 10, "method": "tools/call", "params": {"name": "nope"}}, self.available)
        self.assertTrue(response["result"]["isError"])

    def test_every_advertised_tool_is_dispatchable(self) -> None:
        tools = _handle_mcp({"jsonrpc": "2.0", "id": 11, "method": "tools/list"}, self.available)["result"]["tools"]
        for tool in tools:
            self.assertIn(tool["name"], self.available)
            self.assertIn("inputSchema", tool)


class LauncherTests(unittest.TestCase):
    def test_launcher_template_is_self_contained_and_path_independent(self) -> None:
        self.assertNotIn(str(ROOT), LAUNCHER_SOURCE, "the launcher must not embed a checkout path")
        self.assertIn("_discover", LAUNCHER_SOURCE)
        compile(LAUNCHER_SOURCE, "agent_os_mcp_launcher.py", "exec")

    def test_launcher_status_reports_the_current_checkout(self) -> None:
        self.assertEqual(Path(launcher_status()["current_repository_path"]).resolve(), ROOT.resolve())

    def _template_namespace(self) -> dict:
        namespace = {"__file__": str(ROOT / "agent_os_mcp_launcher.py"), "__name__": "launcher_probe"}
        exec(compile(LAUNCHER_SOURCE, "agent_os_mcp_launcher.py", "exec"), namespace)
        return namespace

    def test_discovery_prefers_the_canonically_named_checkout(self) -> None:
        """Several clones can exist; a stale one must not win after a repo move."""
        namespace = self._template_namespace()
        discovered = namespace["_discover"]()
        self.assertIsNotNone(discovered, "no checkout was discovered from the home search roots")
        self.assertEqual(discovered.name, namespace["CANONICAL_DIRECTORY"])

    def test_checkout_detection_rejects_unrelated_directories(self) -> None:
        namespace = self._template_namespace()
        self.assertTrue(namespace["_is_checkout"](ROOT))
        self.assertFalse(namespace["_is_checkout"](ROOT / "tests"))
        self.assertFalse(namespace["_is_checkout"](Path.home()))

    def test_launcher_serves_in_the_process_the_client_spawned(self) -> None:
        """An MCP client watches the process it spawned; that process must serve.

        os.execv does not replace the process image on Windows. It starts a
        second process and exits the first, so the client sees its child die
        mid-handshake while the inherited pipes stay open, and blocks until its
        own timeout. Draining stdout to EOF hides this, so assert the source
        never hands the session to a replacement process.
        """
        self.assertNotIn("os.execv(", LAUNCHER_SOURCE, "the launcher must not exec a replacement process")
        self.assertNotIn("subprocess.", LAUNCHER_SOURCE, "the launcher must not serve from a child process")
        self.assertIn("from agent_os.cli import main", LAUNCHER_SOURCE)

    def test_installed_launcher_stays_alive_across_a_handshake(self) -> None:
        """The end-to-end guard: drive the real launcher and watch it live."""
        import subprocess
        import threading
        import time

        launcher = Path(launcher_status()["launcher"])
        if not launcher.exists():
            self.skipTest("launcher is not installed on this machine")
        process = subprocess.Popen(
            [sys.executable, str(launcher)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        lines: list[str] = []
        threading.Thread(target=lambda: lines.extend(process.stdout), daemon=True).start()
        try:
            request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {},
                    "clientInfo": {"name": "regression", "version": "0"},
                },
            }
            process.stdin.write(json.dumps(request) + chr(10))
            process.stdin.flush()
            deadline = time.monotonic() + 30
            while time.monotonic() < deadline and not lines:
                self.assertIsNone(
                    process.poll(),
                    "the spawned launcher exited before answering initialize; "
                    "an MCP client reads that as the server dying",
                )
                time.sleep(0.05)
            self.assertTrue(lines, "the launcher never answered initialize")
            self.assertIsNone(process.poll(), "the launcher exited instead of holding the session open")
            self.assertEqual(json.loads(lines[0])["result"]["serverInfo"]["name"], "personal-agent-os")
        finally:
            process.stdin.close()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=10)
            process.stdout.close()
            process.stderr.close()


class AdapterPortabilityTests(unittest.TestCase):
    """Canonical adapter text is cloned to other machines; paths must not be."""

    CANONICAL = (
        Path("adapters") / "global" / "AGENTS.md",
        Path(".agents") / "skills" / "personal-agent-os" / "SKILL.md",
    )

    def test_canonical_adapters_carry_no_machine_specific_path(self) -> None:
        for relative in self.CANONICAL:
            with self.subTest(adapter=str(relative)):
                text = (ROOT / relative).read_text(encoding="utf-8")
                self.assertNotIn(str(Path.home()), text, "a home directory leaked into Git")
                self.assertNotRegex(
                    text,
                    r"[A-Za-z]:\\Users",
                    "an absolute Windows user path leaked into canonical adapter text",
                )

    def test_placeholder_resolves_to_this_checkout_on_install(self) -> None:
        for relative in self.CANONICAL:
            with self.subTest(adapter=str(relative)):
                text = (ROOT / relative).read_text(encoding="utf-8")
                self.assertIn(REPOSITORY_TOKEN, text, "the adapter names no checkout at all")
                rendered = render(text)
                self.assertNotIn(REPOSITORY_TOKEN, rendered)
                self.assertIn(str(ROOT), rendered)

    def test_rendering_is_the_comparison_basis_for_installed_copies(self) -> None:
        """A rendered install must not read as drift against canonical source."""
        for item in routing_status():
            with self.subTest(destination=item["destination"]):
                if item["exists"]:
                    self.assertTrue(item["matches"], f"{item['destination']} drifted from canonical source")


class RegistrySchemaTests(unittest.TestCase):
    def test_registry_is_valid_json_with_routing_vocabulary(self) -> None:
        registry = load_json(ROOT / "projects" / "registry.json")
        self.assertGreaterEqual(registry["schema_version"], 2)
        routable = [item for item in registry["projects"] if not item.get("redirect_to")]
        self.assertTrue(all(isinstance(item.get("routing_terms", []), list) for item in routable))
        self.assertTrue(any(item.get("routing_terms") for item in routable))

    def test_registry_file_contains_no_windows_drive_paths(self) -> None:
        text = (ROOT / "projects" / "registry.json").read_text(encoding="utf-8")
        self.assertNotIn(":\\\\", text)
        self.assertNotIn("/Users/", text)
        json.loads(text)


if __name__ == "__main__":
    unittest.main()
