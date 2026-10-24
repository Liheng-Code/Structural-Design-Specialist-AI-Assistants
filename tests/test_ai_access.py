"""Three-discipline layout, read-only AI access layer (MCP server, local Ollama helper) and NotebookLM knowledge pack."""
import importlib.util
import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "04_tools" / "ai"))
sys.path.insert(0, str(ROOT / "04_tools" / "knowledge"))
import ask_local  # noqa: E402
import build_knowledge_pack as bkp  # noqa: E402
import project_access as pa  # noqa: E402

DISCIPLINES = {"pt-floor", "steel", "rc-works"}


class TestManifestAndLayout(unittest.TestCase):
    def test_three_disciplines(self):
        self.assertEqual({d["id"] for d in pa.list_disciplines()}, DISCIPLINES)

    def test_every_manifest_pattern_matches_a_file(self):
        m = pa.load_manifest()
        groups = [m["core"]] + list(m["disciplines"].values())
        for g in groups:
            for pat in g["files"]:
                with self.subTest(pattern=pat):
                    self.assertTrue(pa.expand([pat]), f"manifest pattern matches nothing: {pat}")

    def test_discipline_folders_skills_and_calc_packages_exist(self):
        for d in pa.list_disciplines():
            with self.subTest(discipline=d["id"]):
                self.assertTrue((ROOT / d["readme"]).is_file())
                self.assertTrue((ROOT / "02_disciplines" / d["id"] / "knowledge").is_dir())
                skill = ROOT / ".claude" / "skills" / d["skill"] / "SKILL.md"
                self.assertTrue(skill.is_file())
                self.assertIn(f"name: {d['skill']}", skill.read_text(encoding="utf-8").split("---")[1])
                self.assertTrue((ROOT / d["calc_package"] / "__init__.py").is_file())

    def test_agent_instruction_files_carry_the_core_rules(self):
        for name in ("AGENTS.md", "CLAUDE.md"):
            text = (ROOT / name).read_text(encoding="utf-8")
            with self.subTest(file=name):
                self.assertIn("APPROVED", text)
                self.assertIn("03_projects/<PROJECT-CODE>/design-basis.yaml", text)
                for folder in ("02_disciplines/pt-floor", "02_disciplines/steel", "02_disciplines/rc-works"):
                    self.assertIn(folder, text)


class TestProjectAccessIsConfined(unittest.TestCase):
    def test_reads_project_text(self):
        self.assertIn("three disciplines", pa.read_file("AGENTS.md"))

    def test_blocks_secrets_vcs_and_escape(self):
        for bad in ("../outside.txt", "webapp/data/settings.json", ".git/config", ".env"):
            with self.subTest(path=bad):
                with self.assertRaises((PermissionError, FileNotFoundError)):
                    pa.read_file(bad)
        self.assertFalse(pa.is_allowed(ROOT / "webapp" / "data" / "projects" / "x.json"))
        self.assertFalse(pa.is_allowed(ROOT.parent))

    def test_binary_files_are_listed_not_read(self):
        dxf = next(p for p in (ROOT / "03_projects" / "PJR-2F-PT").rglob("*.dxf"))
        self.assertIn(pa.rel(dxf), pa.list_files("03_projects/PJR-2F-PT", "*.dxf"))
        with self.assertRaises(ValueError):
            pa.read_file(pa.rel(dxf))

    def test_truncation(self):
        self.assertIn("truncated", pa.read_file("01_standards/00-gap-register.md", max_chars=100))

    def test_search_scoped_to_discipline(self):
        hits = pa.search("EN 1090-2", "steel")
        self.assertTrue(any(h["path"].startswith("02_disciplines/steel/") for h in hits))
        allowed = {pa.rel(p) for p in pa.discipline_files("steel")}
        self.assertTrue(all(h["path"] in allowed for h in hits))

    def test_discipline_context_and_unknown(self):
        ctx = pa.discipline_context("rc-works")
        self.assertIn(pa.RULES, ctx)
        self.assertIn("ec2_anchorage", ctx)
        with self.assertRaises(KeyError):
            pa.discipline_context("timber")

    def test_validate_design_basis_only_under_design_basis(self):
        with self.assertRaises(PermissionError):
            pa.validate_design_basis("AGENTS.md")
        self.assertIn("exit code", pa.validate_design_basis("03_projects/_template/design-basis.yaml"))


class TestKnowledgePack(unittest.TestCase):
    def test_build_writes_one_source_per_discipline_plus_core(self):
        m = pa.load_manifest()
        with tempfile.TemporaryDirectory() as tmp:
            written = bkp.build(pathlib.Path(tmp))
            names = {p.name for p in written}
            self.assertEqual(names, {m["core"]["pack"]} | {d["pack"] for d in m["disciplines"].values()})
            self.assertTrue((pathlib.Path(tmp) / "README.md").is_file())
            for p in written:
                text = p.read_text(encoding="utf-8")
                with self.subTest(pack=p.name):
                    self.assertIn(bkp.DISCLAIMER, text)
                    self.assertGreater(text.count("\n## Source: `"), 0)
            core = (pathlib.Path(tmp) / m["core"]["pack"]).read_text(encoding="utf-8")
            self.assertEqual(core.count("\n## Source: `"), len(pa.expand(m["core"]["files"])))
            self.assertNotIn("## Source: `webapp/data", core)


class TestLocalAssistant(unittest.TestCase):
    def test_retrieval_grounds_on_discipline_text(self):
        labels = [label for label, _ in ask_local.retrieve("execution class EN 1090-2 bolts", "steel")]
        self.assertTrue(any(label.startswith("02_disciplines/steel/") for label in labels))

    def test_prompt_carries_rules_and_sources(self):
        msgs = ask_local.build_messages("anchorage length", "rc-works")
        self.assertEqual(msgs[0]["role"], "system")
        self.assertIn(pa.RULES, msgs[0]["content"])
        self.assertIn("[SOURCE: ", msgs[0]["content"])


@unittest.skipUnless(importlib.util.find_spec("mcp"), "mcp package not installed")
class TestMcpServer(unittest.TestCase):
    def test_server_exposes_read_only_tools(self):
        import mcp_server
        self.assertTrue(callable(mcp_server.read_project_file))
        self.assertTrue(mcp_server.read_project_file("webapp/data/x.json").startswith("ERROR:"))
        self.assertIn("pt-floor", mcp_server.list_disciplines())
        names = {n for n in dir(mcp_server) if not n.startswith("_")}
        for forbidden in ("write", "approve", "issue", "delete"):
            self.assertFalse(any(forbidden in n.lower() for n in names), forbidden)


if __name__ == "__main__":
    unittest.main()
