"""Local MCP server: lets any MCP client (Claude Code, Claude Desktop, Open WebUI via mcpo, Continue, Cline, ...) read this project.

Read-only by design (ADR-010): no tool writes files, approves, issues or changes a check result.
Run:  python 04_tools/ai/mcp_server.py          (stdio transport; the client starts it)
Setup for each client: 05_docs/ai-access.md
"""
from __future__ import annotations

import functools
import json
import pathlib
import sys
from typing import Any, Callable

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

try:  # mcp >= 2
    from mcp.server.mcpserver import MCPServer as Server
except ImportError:  # mcp 1.x
    from mcp.server.fastmcp import FastMCP as Server  # type: ignore[no-redef]

import project_access as pa

server = Server(
    "structural-project",
    instructions=(
        "Structural design specialist project with three disciplines: pt-floor (bonded post-tensioned floors), "
        "steel (steel structures) and rc-works (reinforced concrete works). Start with list_disciplines, then "
        "get_discipline_context for the discipline in question, then read or search files. " + pa.RULES
    ),
)


def _readable_errors(fn: Callable[..., str]) -> Callable[..., str]:
    """Return refusals and missing files as a readable message instead of a generic tool failure."""
    @functools.wraps(fn)
    def wrapper(*args: Any, **kwargs: Any) -> str:
        try:
            return fn(*args, **kwargs)
        except (PermissionError, FileNotFoundError, KeyError, ValueError) as exc:
            return f"ERROR: {exc}"
    return wrapper


@server.tool()
@_readable_errors
def list_disciplines() -> str:
    """List the three disciplines with their entry skill, calculation package and README path."""
    return json.dumps(pa.list_disciplines(), indent=1)


@server.tool()
@_readable_errors
def get_discipline_context(discipline: str) -> str:
    """Project rules + the discipline README + its entry skill. discipline: 'pt-floor', 'steel' or 'rc-works'."""
    return pa.discipline_context(discipline)


@server.tool()
@_readable_errors
def list_knowledge_files(discipline: str = "core") -> str:
    """Files in the knowledge set: 'core' (shared standards and skills) or core + one discipline."""
    return "\n".join(pa.rel(p) for p in pa.discipline_files(discipline))


@server.tool()
@_readable_errors
def read_project_file(path: str, max_chars: int = 60000) -> str:
    """Read a text file by repo-relative path (e.g. '01_standards/00-gap-register.md')."""
    return pa.read_file(path, max_chars=max_chars)


@server.tool()
@_readable_errors
def list_project_files(folder: str = "", pattern: str = "*") -> str:
    """List files under a repo folder (glob pattern, recursive). Binary files are listed but cannot be read."""
    return "\n".join(pa.list_files(folder, pattern))


@server.tool()
@_readable_errors
def search_project(query: str, discipline: str = "", max_results: int = 30) -> str:
    """Case-insensitive text search. Give a discipline to search only the core + that discipline's knowledge set."""
    return json.dumps(pa.search(query, discipline or None, max_results), indent=1)


@server.tool()
@_readable_errors
def list_design_bases() -> str:
    """List project design-basis YAML files (the single source for project data)."""
    return "\n".join(pa.list_design_bases())


@server.tool()
@_readable_errors
def validate_design_basis(path: str) -> str:
    """Run the design-basis validator on a YAML under 03_projects/ and return its report (read-only)."""
    return pa.validate_design_basis(path)


if __name__ == "__main__":
    server.run()
