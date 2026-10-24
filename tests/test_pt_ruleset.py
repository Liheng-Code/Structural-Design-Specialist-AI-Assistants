"""Structure checks for every PT ruleset (02_disciplines/pt-floor/knowledge/*-ruleset.yaml).
Checks form only - the engineering content is UNVERIFIED until an engineer accepts each rule (gaps G33, G34)."""
import pathlib
import re
import unittest

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
KNOWLEDGE = ROOT / "02_disciplines" / "pt-floor" / "knowledge"
RULESETS = sorted(KNOWLEDGE.glob("*-ruleset.yaml"))
REQUIRED = ("id", "title", "category", "rule", "basis", "status", "automatable", "review_note")


class TestPtRulesets(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sets = {p: yaml.safe_load(p.read_text(encoding="utf-8")) for p in RULESETS}

    def test_rulesets_found(self):
        self.assertGreaterEqual(len(self.sets), 2)

    def test_header(self):
        for p, d in self.sets.items():
            with self.subTest(file=p.name):
                self.assertEqual(d["status"], "DRAFT")
                self.assertIn("drive_id", d["source"])

    def test_every_rule_has_required_fields(self):
        for p, d in self.sets.items():
            for r in d["rules"]:
                with self.subTest(file=p.name, rule=r.get("id")):
                    for k in REQUIRED:
                        self.assertIn(k, r)
                    self.assertRegex(r["id"], r"^PT-[A-Z]{3}-\d{2}$")
                    self.assertIn(r["basis"], ("EC2", "ACI", "practice"))
                    self.assertIsInstance(r["automatable"], bool)

    def test_ids_unique_across_rulesets(self):
        ids = [r["id"] for d in self.sets.values() for r in d["rules"]]
        self.assertEqual(len(ids), len(set(ids)))

    def test_related_ids_exist(self):
        ids = {r["id"] for d in self.sets.values() for r in d["rules"]}
        for d in self.sets.values():
            for r in d["rules"]:
                for ref in r.get("related", []):
                    with self.subTest(rule=r["id"], ref=ref):
                        self.assertIn(ref, ids)

    def test_no_rule_approved_by_ai(self):
        for d in self.sets.values():
            for r in d["rules"]:
                with self.subTest(rule=r["id"]):
                    self.assertNotEqual(r["status"], "APPROVED")
                    if r["status"] == "ACCEPTED":
                        self.assertRegex(r.get("accepted_by", ""), r"\S+ \d{4}-\d{2}-\d{2}")

    def test_guide_mentions_every_rule_group(self):
        for p, d in self.sets.items():
            guide = p.with_suffix(".md").read_text(encoding="utf-8")
            for group in sorted({re.match(r"PT-[A-Z]+", r["id"]).group(0) for r in d["rules"]}):
                with self.subTest(file=p.name, group=group):
                    self.assertIn(group, guide)


if __name__ == "__main__":
    unittest.main()
