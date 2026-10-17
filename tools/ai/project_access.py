"""Read-only access to this project for AI assistants (Claude, local Ollama models, other MCP clients).

Used by tools/ai/mcp_server.py, tools/ai/ask_local.py and tools/knowledge/build_knowledge_pack.py.
Nothing here writes to the repo. Paths are confined to the repo root; secrets and bulky folders are never served.
"""
from __future__ import annotations

import pathlib
import re
import subprocess
import sys
from typing import Any

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "disciplines" / "manifest.yaml"

TEXT_SUFFIXES = {".md", ".txt", ".yaml", ".yml", ".json", ".csv", ".py", ".toml", ".bat", ".ini", ".cfg"}
# Never served: VCS data, local secrets (webapp/data holds the API key), dependencies and caches.
BLOCKED_PARTS = {".git", "node_modules", ".next", "__pycache__", ".mypy_cache", ".ruff_cache", ".venv", "venv"}
BLOCKED_PREFIXES = ("webapp/data",)
BLOCKED_NAMES = {".env", "probe_result.json"}
MAX_FILE_CHARS = 200_000

RULES = (
    "Rules for any AI working on this project: never invent engineering values, clauses, standards or PASS results; "
    "flag gaps instead. Never mark anything APPROVED - engineer sign-off is human. Design to Eurocodes with CEN "
    "recommended values unless the design basis records a National Annex. design-basis/<PROJECT-CODE>.yaml is the "
    "single source for project code, revision, date, stage, codes, loads and materials. "
    "Structural-Drawing-Standards/ is authoritative; check each file's status header."
)


def load_manifest() -> dict[str, Any]:
    with open(MANIFEST, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def expand(patterns: list[str]) -> list[pathlib.Path]:
    """Expand manifest patterns to existing files, in manifest order, without duplicates."""
    out: list[pathlib.Path] = []
    for pat in patterns:
        for p in sorted(ROOT.glob(pat)):
            if p.is_file() and p not in out:
                out.append(p)
    return out


def rel(p: pathlib.Path) -> str:
    return p.resolve().relative_to(ROOT).as_posix()


def is_allowed(p: pathlib.Path) -> bool:
    try:
        r = p.resolve().relative_to(ROOT)
    except ValueError:
        return False
    posix = r.as_posix()
    if any(part in BLOCKED_PARTS for part in r.parts) or p.name in BLOCKED_NAMES or p.name.startswith(".env"):
        return False
    return not any(posix == b or posix.startswith(b + "/") for b in BLOCKED_PREFIXES)


def resolve_safe(path: str) -> pathlib.Path:
    p = (ROOT / path).resolve()
    if not is_allowed(p):
        raise PermissionError(f"Path not available to assistants: {path}")
    if not p.is_file():
        raise FileNotFoundError(f"No such file in the project: {path}")
    return p


def list_disciplines() -> list[dict[str, Any]]:
    m = load_manifest()
    return [
        {"id": k, "title": v["title"], "skill": v["skill"], "calc_package": v["calc_package"],
         "readme": f"disciplines/{k}/README.md"}
        for k, v in m["disciplines"].items()
    ]


def discipline_files(discipline: str | None) -> list[pathlib.Path]:
    """Core files, plus the discipline's files when one is given ('core' or None gives core only)."""
    m = load_manifest()
    pats = list(m["core"]["files"])
    if discipline and discipline != "core":
        if discipline not in m["disciplines"]:
            raise KeyError(f"Unknown discipline '{discipline}'. Known: {', '.join(m['disciplines'])}")
        pats += m["disciplines"][discipline]["files"]
    return expand(pats)


def read_file(path: str, max_chars: int = MAX_FILE_CHARS) -> str:
    p = resolve_safe(path)
    if p.suffix.lower() not in TEXT_SUFFIXES:
        raise ValueError(f"Not a text file assistants can read: {path} (binary files such as DXF/PDF/DOCX are listed, not read)")
    text = p.read_text(encoding="utf-8", errors="replace")
    if len(text) > max_chars:
        text = text[:max_chars] + f"\n\n[... truncated at {max_chars} of {len(text)} characters]"
    return text


def list_files(folder: str = "", pattern: str = "*") -> list[str]:
    base = (ROOT / folder).resolve()
    if not is_allowed(base) and base != ROOT:
        raise PermissionError(f"Folder not available to assistants: {folder}")
    return [rel(p) for p in sorted(base.rglob(pattern)) if p.is_file() and is_allowed(p)][:500]


def _iter_text_files(scope: list[pathlib.Path] | None) -> list[pathlib.Path]:
    if scope is not None:
        return scope
    return [p for p in ROOT.rglob("*") if p.is_file() and p.suffix.lower() in TEXT_SUFFIXES and is_allowed(p)]


def search(query: str, discipline: str | None = None, max_results: int = 30) -> list[dict[str, Any]]:
    """Case-insensitive search. With a discipline, searches the core + discipline knowledge set; otherwise all text files."""
    rx = re.compile(re.escape(query), re.IGNORECASE)
    scope = discipline_files(discipline) if discipline else None
    hits: list[dict[str, Any]] = []
    for p in _iter_text_files(scope):
        try:
            lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        for n, line in enumerate(lines, 1):
            if rx.search(line):
                hits.append({"path": rel(p), "line": n, "text": line.strip()[:300]})
                if len(hits) >= max_results:
                    return hits
    return hits


def discipline_context(discipline: str) -> str:
    """Short briefing: rules + discipline README + entry skill (what an assistant should read first)."""
    m = load_manifest()
    if discipline not in m["disciplines"]:
        raise KeyError(f"Unknown discipline '{discipline}'. Known: {', '.join(m['disciplines'])}")
    d = m["disciplines"][discipline]
    parts = [f"# {d['title']}", RULES,
             read_file(f"disciplines/{discipline}/README.md"),
             read_file(f".claude/skills/{d['skill']}/SKILL.md")]
    return "\n\n---\n\n".join(parts)


def list_design_bases() -> list[str]:
    return [rel(p) for p in sorted((ROOT / "design-basis").rglob("*.yaml")) if is_allowed(p)]


def validate_design_basis(path: str) -> str:
    """Run the existing validator (read-only) on a design-basis YAML inside design-basis/."""
    p = resolve_safe(path)
    if not rel(p).startswith("design-basis/"):
        raise PermissionError("Only files under design-basis/ can be validated")
    proc = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "design_basis" / "validate_design_basis.py"), str(p)],
        capture_output=True, text=True, cwd=ROOT, timeout=120,
    )
    return f"exit code {proc.returncode}\n{proc.stdout}{proc.stderr}"
