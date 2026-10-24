"""Structure checks for the PT master ruleset (02_disciplines/pt-floor/knowledge/pt-master-ruleset.yaml).
Checks form only - the engineering content is UNVERIFIED until an engineer accepts each rule (gap G33)."""
import pathlib
import re
import unittest

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
RULESET = ROOT / "02_disciplines" / "pt-floor" / "knowledge" / "pt-master-ruleset.yaml"
REQUIRED = ("id", "title", "category", "rule", "basis", "status", "automatable", "review_note")


class TestPtRuleset(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = yaml.safe_load(RULESET.read_text(encoding="utf-8"))
        cls.rules = cls.data["rules"]

    def test_header(self):
        self.assertEqual(self.data["status"], "DRAFT")
        self.assertIn("drive_id", self.data["source"])

    def test_every_rule_has_required_fields(self):
        for r in self.rules:
            with self.subTest(rule=r.get("id")):
                for k in REQUIRED:
                    self.assertIn(k, r)
                self.assertRegex(r["id"], r"^PT-(LAY|SHR)-\d{2}$")
                self.assertIn(r["basis"], ("EC2", "ACI", "practice"))
                self.assertIsInstance(r["automatable"], bool)

    def test_ids_unique(self):
        ids = [r["id"] for r in self.rules]
        self.assertEqual(len(ids), len(set(ids)))

    def test_no_rule_approved_by_ai(self):
        for r in self.rules:
            with self.subTest(rule=r["id"]):
                self.assertNotEqual(r["status"], "APPROVED")
                if r["status"] == "ACCEPTED":
                    self.assertRegex(r.get("accepted_by", ""), r"\S+ \d{4}-\d{2}-\d{2}")

    def test_guide_mentions_every_rule_group(self):
        guide = (RULESET.with_suffix(".md")).read_text(encoding="utf-8")
        for group in sorted({re.match(r"PT-\w+", r["id"]).group(0) for r in self.rules}):
            self.assertIn(group, guide)


if __name__ == "__main__":
    unittest.main()
