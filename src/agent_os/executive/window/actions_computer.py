"""Computer access, Confirm tier: write, move, delete, open and run on the operator's computer.

Each action previews (unified diff, exact argv, source/target) and acts only
through the window's Confirm. The free and automatic tiers (list, read, search,
write_draft) are MCP tools that call agent_os.executive.computer directly.
"""
from __future__ import annotations

from typing import Any

from .. import computer

KIND = "computer_request"


def write_file(item: dict[str, Any], params: dict[str, Any], *, confirm: bool) -> dict[str, Any]:
    if not confirm:
        return computer.preview_write(params.get("path"), params.get("content"))
    if "expect_sha256" in params:
        return computer.write_file(params.get("path"), params.get("content"), expect_sha256=params["expect_sha256"])
    return computer.write_file(params.get("path"), params.get("content"))


def move_file(item: dict[str, Any], params: dict[str, Any], *, confirm: bool) -> dict[str, Any]:
    fn = computer.move_file if confirm else computer.preview_move
    return fn(params.get("source"), params.get("target"))


def delete_file(item: dict[str, Any], params: dict[str, Any], *, confirm: bool) -> dict[str, Any]:
    fn = computer.delete_file if confirm else computer.preview_delete
    return fn(params.get("path"))


def open_path(item: dict[str, Any], params: dict[str, Any], *, confirm: bool) -> dict[str, Any]:
    fn = computer.open_path if confirm else computer.preview_open
    return fn(params.get("path"))


def run_command(item: dict[str, Any], params: dict[str, Any], *, confirm: bool) -> dict[str, Any]:
    fn = computer.run_command if confirm else computer.preview_run
    return fn(params.get("argv"), params.get("cwd"))


_PATH = {"type": "string", "description": "Path under an allowed root"}

ACTIONS = (
    ("computer.write_file", "Write file", write_file,
     "Create or overwrite a file under the allowed roots (backs up an existing file to .bak first); preview shows a unified diff",
     {"type": "object", "properties": {"path": _PATH, "content": {"type": "string"},
                                       "expect_sha256": {"type": ["string", "null"]}},
      "required": ["path", "content"]}),
    ("computer.move_file", "Move file", move_file,
     "Move or rename a file or folder within the allowed roots; never overwrites",
     {"type": "object", "properties": {"source": _PATH, "target": _PATH}, "required": ["source", "target"]}),
    ("computer.delete_file", "Move to trash", delete_file,
     "Move a file or folder to the Agent OS trash (never a hard delete)",
     {"type": "object", "properties": {"path": _PATH}, "required": ["path"]}),
    ("computer.open_path", "Open", open_path,
     "Open a file or folder with its default application",
     {"type": "object", "properties": {"path": _PATH}, "required": ["path"]}),
    ("computer.run_command", "Run command", run_command,
     "Run one program as an argv list (no shell) in a folder under the allowed roots; 120 s timeout, capped output",
     {"type": "object", "properties": {"argv": {"type": "array", "items": {"type": "string"}, "minItems": 1},
                                       "cwd": _PATH},
      "required": ["argv"]}),
)


def register(registry: Any) -> None:
    for action_id, label, handler, description, schema in ACTIONS:
        registry.register_action(action_id, label, [KIND], handler, consequential=True,
                                 description=description, params_schema=schema)
