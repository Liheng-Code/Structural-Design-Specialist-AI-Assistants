"""Repo folder locations - the single place that knows the numbered layout.

    import paths            (with 04_tools/ on sys.path)
    paths.STANDARDS / "05-drafting-styles"

Layout: 01_standards, 02_disciplines, 03_projects, 04_tools, 05_docs, 06_knowledge-pack (see README.md).
"""
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
STANDARDS = ROOT / "01_standards"
DISCIPLINES = ROOT / "02_disciplines"
PROJECTS = ROOT / "03_projects"
TEMPLATES = PROJECTS / "_template"
TOOLS = ROOT / "04_tools"
CODE_REGISTRY = TOOLS / "code_registry"
DOCS = ROOT / "05_docs"
KNOWLEDGE_PACK = ROOT / "06_knowledge-pack"
SKILLS = ROOT / ".claude" / "skills"
TESTS = ROOT / "tests"
