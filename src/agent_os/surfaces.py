"""Integration health for the client surfaces that reach Agent OS.

P0.0 requires Agent OS to be the default routing layer for every client the user
works through, and to be honest about the clients where it is not. A *surface*
is one such client. Surfaces are described declaratively in
`surfaces/registry.json`; this module probes the local machine and reports, per
surface, whether it is registered, reachable, automatically preflighted, able to
emit handoffs and candidates, and what is missing.

Surfaces stay thin: nothing here is provider-specific beyond the file locations
each vendor happens to use, and no client gets its own fork of the core. Path
expansion is delegated to `machine.resolve_user_path`.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .connectors import REGISTRY_SCHEMA as CONNECTOR_REGISTRY_SCHEMA
from .connectors import load_connector_registry
from .launcher import LAUNCHER_PATH
from .launcher import status as launcher_status
from .machine import resolve_user_path
from .paths import ROOT
from .registry import get_project
from .storage import load_json


SURFACE_REGISTRY_PATH = ROOT / "surfaces" / "registry.json"
SURFACE_REGISTRY_SCHEMA = "personal-agent/surface-registry/v1"

TIERS = ("unintegrated", "bridged", "routed")
TIER_LABELS = {
    "routed": "fully routed",
    "bridged": "partially bridged",
    "unintegrated": "not yet integrated",
}

MCP_SERVER_KEYS = ("mcpServers", "mcp_servers")
ENTRY_POINT_NAMES = ("agent.py", LAUNCHER_PATH.name)


def surfaces() -> list[dict[str, Any]]:
    """Canonical surface descriptions exactly as stored in Git."""
    registry = load_json(SURFACE_REGISTRY_PATH)
    if registry.get("schema") != SURFACE_REGISTRY_SCHEMA:
        raise ValueError(f"unsupported surface registry schema: {registry.get('schema')}")
    return registry["surfaces"]


def _canonical_checkout() -> Path:
    return Path(get_project("personal-agent-os")["path"]).resolve()


def _is_checkout(path: Path) -> bool:
    return (path / "agent.py").is_file() and (path / "src" / "agent_os").is_dir()


def _json_registration(data: Any, server_keys: tuple[str, ...]) -> dict[str, Any] | None:
    """Find an Agent OS server entry anywhere in a client configuration tree."""
    if isinstance(data, dict):
        for key, value in data.items():
            if key in MCP_SERVER_KEYS and isinstance(value, dict):
                for name, entry in value.items():
                    if name in server_keys and isinstance(entry, dict):
                        return {"server": name, "command": entry.get("command"), "args": list(entry.get("args") or [])}
            found = _json_registration(value, server_keys)
            if found:
                return found
    elif isinstance(data, list):
        for item in data:
            found = _json_registration(item, server_keys)
            if found:
                return found
    return None


def _toml_registration(text: str, server_keys: tuple[str, ...]) -> dict[str, Any] | None:
    """Read one `[mcp_servers.<name>]` table without a TOML dependency."""
    for name in server_keys:
        pattern = re.compile(
            r"^\[mcp_servers\." + re.escape(name) + r"\]\s*$(?P<body>.*?)(?=^\[|\Z)",
            re.MULTILINE | re.DOTALL,
        )
        match = pattern.search(text)
        if not match:
            continue
        body = match.group("body")
        command = re.search(r"^command\s*=\s*['\"](?P<value>[^'\"]*)['\"]", body, re.MULTILINE)
        args = re.search(r"^args\s*=\s*\[(?P<value>.*?)\]", body, re.MULTILINE | re.DOTALL)
        values = re.findall(r"['\"]([^'\"]*)['\"]", args.group("value")) if args else []
        return {"server": name, "command": command.group("value") if command else None, "args": values}
    return None


def _read_registration(path: Path, server_keys: tuple[str, ...]) -> dict[str, Any] | None:
    try:
        text = path.read_text(encoding="utf-8-sig")
    except OSError:
        return None
    if path.suffix.casefold() == ".toml":
        return _toml_registration(text, server_keys)
    try:
        return _json_registration(json.loads(text), server_keys)
    except json.JSONDecodeError:
        return None


def _entry_point(registration: dict[str, Any]) -> Path | None:
    """The script a registered command would actually run."""
    wanted = {name.casefold() for name in ENTRY_POINT_NAMES}
    for value in [*registration.get("args", []), registration.get("command")]:
        if not value:
            continue
        candidate = Path(str(value))
        if candidate.name.casefold() in wanted:
            return candidate
    return None


def _checkout_for(entry_point: Path) -> tuple[Path | None, bool]:
    """Resolve an entry point to the checkout it serves, and whether it is stable.

    The stable launcher resolves its own checkout at run time, so a registration
    pointing at it survives a repository move; a registration that embeds
    `agent.py` is pinned to one directory.
    """
    if entry_point.name.casefold() == LAUNCHER_PATH.name.casefold():
        configured = launcher_status().get("configured_repository_path")
        return (Path(configured).expanduser().resolve() if configured else None), True
    return entry_point.expanduser().resolve().parent, False


def _probe_invocation(surface: dict[str, Any]) -> dict[str, Any]:
    spec = surface["invocation"]
    kind = spec["kind"]
    result: dict[str, Any] = {
        "kind": kind,
        "registered": False,
        "reachable": False,
        "canonical_checkout": False,
        "stable_launcher": False,
        "source": None,
        "checkout": None,
        "detail": spec.get("reason"),
    }
    if kind == "none":
        return result
    if kind == "server_entrypoint":
        launcher = launcher_status()
        checkout = _canonical_checkout()
        result["registered"] = bool(launcher["installed"] and launcher["matches_template"])
        result["stable_launcher"] = result["registered"]
        result["source"] = launcher["launcher"]
        result["reachable"] = result["registered"] and _is_checkout(checkout)
        result["canonical_checkout"] = result["reachable"]
        result["checkout"] = str(checkout)
        result["detail"] = "server entry point only; no individual client registration is tracked"
        return result

    server_keys = tuple(spec.get("server_keys") or [])
    for location in spec.get("registrations", []):
        registration = _read_registration(resolve_user_path(location), server_keys)
        if not registration:
            continue
        result["registered"] = True
        result["source"] = str(resolve_user_path(location))
        result["detail"] = "registered as '" + str(registration["server"]) + "'"
        entry_point = _entry_point(registration)
        if entry_point is None:
            result["detail"] = result["detail"] + " with an unrecognized command"
            break
        checkout, stable = _checkout_for(entry_point)
        result["stable_launcher"] = stable
        result["checkout"] = str(checkout) if checkout else None
        if checkout and _is_checkout(checkout):
            result["reachable"] = True
            result["canonical_checkout"] = checkout == _canonical_checkout()
        break
    return result


def _probe_instruction(surface: dict[str, Any], invocation: dict[str, Any]) -> dict[str, Any]:
    spec = surface["instruction"]
    kind = spec["kind"]
    result: dict[str, Any] = {"kind": kind, "preflighted": False, "source": None, "detail": spec.get("reason")}
    if kind == "none":
        return result
    marker = str(spec.get("marker") or "Agent OS")
    if kind == "server_instructions":
        from .mcp_server import INSTRUCTIONS

        # Server instructions only preflight a client that actually connects.
        result["preflighted"] = marker in INSTRUCTIONS and invocation["reachable"]
        result["source"] = "mcp initialize instructions"
        result["detail"] = (
            "carried by the server handshake, not by a client-side file"
            if result["preflighted"]
            else "the server handshake would carry the preflight once this client connects"
        )
        return result
    for location in spec.get("locations", []):
        path = resolve_user_path(location)
        try:
            text = path.read_text(encoding="utf-8-sig")
        except OSError:
            continue
        if marker.casefold() in text.casefold():
            result["preflighted"] = True
            result["source"] = str(path)
            result["detail"] = None
            break
        result["source"] = str(path)
        result["detail"] = "present but does not mention '" + marker + "'"
    return result


def _cli_commands() -> set[str]:
    from .cli import parser  # imported lazily: the CLI imports this module

    for action in parser()._subparsers._group_actions:
        return set(action.choices)
    return set()


def _probe_capture(surface: dict[str, Any], invocation: dict[str, Any]) -> dict[str, Any]:
    spec = surface["capture"]
    kind = spec["kind"]
    result: dict[str, Any] = {
        "kind": kind,
        "automatic": bool(spec.get("automatic")),
        "handoffs": False,
        "candidates": False,
        "detail": None,
    }
    if kind == "mcp_tools":
        from .mcp_server import methods

        available = set(methods())
        missing = [tool for tool in spec.get("tools", []) if tool not in available]
        if missing:
            result["detail"] = "server does not advertise " + ", ".join(missing)
        elif not invocation["reachable"]:
            result["detail"] = "capture tools exist but the client cannot reach the server"
        else:
            result["handoffs"] = result["candidates"] = True
    elif kind == "cli_bridge":
        commands = _cli_commands()
        missing = [command for command in spec.get("commands", []) if command not in commands]
        if missing:
            result["detail"] = "the CLI does not provide " + ", ".join(missing)
        else:
            result["handoffs"] = result["candidates"] = True
            if not result["automatic"]:
                result["detail"] = "captured locally through the CLI after the conversation"
    else:
        result["detail"] = spec.get("reason") or "no capture path"
    return result


def _tier(invocation: dict[str, Any], instruction: dict[str, Any]) -> str:
    """Fully routed means the client both reaches canonical Agent OS and is preflighted."""
    if invocation["reachable"] and invocation["canonical_checkout"] and instruction["preflighted"]:
        return "routed"
    if invocation["registered"] or invocation["reachable"] or instruction["preflighted"]:
        return "bridged"
    return "unintegrated"


def _missing(
    surface: dict[str, Any],
    invocation: dict[str, Any],
    instruction: dict[str, Any],
    capture: dict[str, Any],
) -> list[str]:
    gaps: list[str] = []
    if invocation["kind"] != "none":
        if not invocation["registered"]:
            gaps.append("no Agent OS MCP server is registered with this client")
        elif not invocation["reachable"]:
            gaps.append(f"the registered command does not resolve to an Agent OS checkout ({invocation['checkout'] or 'unknown'})")
        elif not invocation["canonical_checkout"]:
            gaps.append(f"the registration points at a non-canonical checkout ({invocation['checkout']})")
        if invocation["reachable"] and surface["invocation"].get("prefers_stable_launcher") and not invocation["stable_launcher"]:
            gaps.append(f"the registration embeds a checkout path; point it at the stable launcher ({LAUNCHER_PATH})")
    if instruction["kind"] == "none":
        gaps.append("no automatic preflight instruction is available for this client")
    elif not instruction["preflighted"]:
        gaps.append(instruction["detail"] or "no Agent OS preflight instruction was found for this client")
    if not (capture["handoffs"] and capture["candidates"]):
        gaps.append(capture["detail"] or "cannot emit handoffs or durable candidates")
    elif not capture["automatic"]:
        gaps.append("handoffs and candidates require a manual step in this client")
    return gaps


def health(surface_id: str | None = None) -> dict[str, Any]:
    """Report which client surfaces are fully routed, bridged, or not yet integrated."""
    selected = surfaces()
    if surface_id:
        selected = [item for item in selected if item["id"].casefold() == surface_id.casefold()]
        if not selected:
            raise KeyError(f"Unknown client surface: {surface_id}")

    reports: list[dict[str, Any]] = []
    for surface in selected:
        invocation = _probe_invocation(surface)
        instruction = _probe_instruction(surface, invocation)
        capture = _probe_capture(surface, invocation)
        tier = _tier(invocation, instruction)
        expected = surface["expected_tier"]
        reports.append(
            {
                "id": surface["id"],
                "name": surface["name"],
                "vendor": surface["vendor"],
                "mechanism": surface["mechanism"],
                "summary": surface["summary"],
                "registered": invocation["registered"],
                "reachable": invocation["reachable"],
                "tier": tier,
                "tier_label": TIER_LABELS[tier],
                "expected_tier": expected,
                "meets_expectation": TIERS.index(tier) >= TIERS.index(expected),
                "automatic_preflight": instruction["preflighted"],
                "emits_handoffs": capture["handoffs"],
                "emits_candidates": capture["candidates"],
                "invocation": invocation,
                "instruction": instruction,
                "capture": capture,
                "missing": _missing(surface, invocation, instruction, capture),
            }
        )

    counts = {tier: sum(1 for item in reports if item["tier"] == tier) for tier in reversed(TIERS)}
    connector_registry = load_connector_registry()
    connector_reports = []
    for connector in connector_registry["connectors"]:
        registrations = connector["registrations"]
        registration_states = {item["surface_id"].casefold(): item["state"] for item in registrations}
        surface_readiness = []
        for surface in reports:
            state = registration_states.get(surface["id"].casefold())
            reasons = []
            if not surface["reachable"]:
                reasons.append("client cannot reach Agent OS")
            if state is None:
                reasons.append("no connector registration is declared for this client")
            elif state != "registered":
                reasons.append(f"connector registration is {state}")
            health_status = connector["health"]["status"]
            if health_status != "healthy":
                reasons.append(f"provider health is {health_status}")
            registry_ready = not reasons
            surface_readiness.append(
                {
                    "surface_id": surface["id"],
                    "surface_reachable": surface["reachable"],
                    "registration_state": state or "not_registered",
                    "registry_ready": registry_ready,
                    "status": "declared_ready_unverified" if registry_ready else "blocked",
                    "reasons": reasons or ["registry checks pass; provider invocation has not been verified"],
                }
            )
        connector_reports.append(
            {
                "id": connector["id"],
                "provider": connector["provider"],
                "health": connector["health"],
                "privacy_domain": connector["privacy_domain"],
                "registrations": registrations,
                "surface_readiness": surface_readiness,
            }
        )
    return {
        "schema": SURFACE_REGISTRY_SCHEMA,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "counts": counts,
        "degraded": [item["id"] for item in reports if not item["meets_expectation"]],
        "ok": all(item["meets_expectation"] for item in reports),
        "surfaces": reports,
        "connector_providers": {
            "schema": CONNECTOR_REGISTRY_SCHEMA,
            "count": len(connector_reports),
            "connectors": connector_reports,
        },
    }
