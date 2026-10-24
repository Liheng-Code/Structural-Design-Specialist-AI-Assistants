"""Phase 3 tests. Run from repo root:  python -m unittest discover -s tests -v"""
import copy
import csv
import pathlib
import sys
import unittest

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "04_tools" / "design_basis"))
sys.path.insert(0, str(ROOT / "04_tools" / "doc_control"))
import check_register as cr  # noqa: E402
import validate_design_basis as vdb  # noqa: E402

EX = ROOT / "03_projects" / "PJR-2026-003"


def load():
    return yaml.safe_load((EX / "design-basis.yaml").read_text(encoding="utf-8"))


def sev(issues, level):
    return [i for i in issues if i[0] == level]


class DesignBasis(unittest.TestCase):
    def test_real_draft_has_no_errors_but_flags_unresolved(self):
        issues = vdb.validate(load())
        self.assertEqual(sev(issues, "ERROR"), [])
        msgs = " ".join(m for _, _, m in issues)
        self.assertIn("edition/year not recorded", msgs)   # editions not on drawing
        self.assertIn("open item F1", msgs)

    def test_draft_cannot_be_approved(self):
        db = load()
        db["approval"]["status"] = "APPROVED"
        errs = sev(vdb.validate(db), "ERROR")
        paths = {p for _, p, _ in errs}
        self.assertIn("approval.checked_by", paths)
        self.assertIn("approval.approved_by", paths)
        self.assertTrue(any("open item" in m for _, _, m in errs))

    def test_incomplete_project(self):
        errs = sev(vdb.validate({"project": {"code": "BAD"}}), "ERROR")
        paths = {p for _, p, _ in errs}
        for need in ("standards", "national_annex", "approval", "project.name", "project.code"):
            self.assertIn(need, paths)

    def test_mixed_generations_rejected(self):
        db = load()
        db.pop("mixed_generation_justification")
        db["standards"][0]["generation"] = "1st"
        db["standards"][1]["generation"] = "2nd"
        errs = " ".join(m for _, _, m in sev(vdb.validate(db), "ERROR"))
        self.assertIn("mixed", errs)
        db["mixed_generation_justification"] = "Documented in design basis memo"
        self.assertNotIn("mixed", " ".join(m for _, _, m in sev(vdb.validate(db), "ERROR")))

    def test_conflicting_editions(self):
        db = load()
        db["standards"][0]["edition"] = "2002"
        dup = copy.deepcopy(db["standards"][0]); dup["edition"] = "2023"
        db["standards"].append(dup)
        self.assertTrue(any("conflicting editions" in m for _, _, m in sev(vdb.validate(db), "ERROR")))

    def test_na_rules(self):
        db = load()
        db["national_annex"] = {"mode": "NA", "country": "UK"}
        errs = {p for _, p, _ in sev(vdb.validate(db), "ERROR")}
        self.assertIn("national_annex.references", errs)
        db["national_annex"] = {"mode": "CEN_RECOMMENDED"}
        errs = {p for _, p, _ in sev(vdb.validate(db), "ERROR")}
        self.assertIn("national_annex.basis_note", errs)

    def test_families_not_auto_applied(self):
        db = load()
        db["standards"].append({"id": "EN 1995-1-1", "generation": None, "edition": None, "used_for": "timber"})
        self.assertTrue(any("EN 1995" in m and "no structure type" in m for _, _, m in vdb.validate(db)))
        db["project"]["structure_types"].append("masonry")
        self.assertTrue(any("EN 1996 expected" in m for _, _, m in vdb.validate(db)))

    def test_pjr_prefix_warning(self):
        db = load()
        self.assertFalse(any("PJR-" in m for _, _, m in vdb.validate(db)))
        db["project"]["code"] = "PRJ-2026-003"
        self.assertTrue(any("PJR- prefix" in m for s, _, m in vdb.validate(db) if s == "WARNING"))

    def test_mixed_generation_allowed_but_each_part_must_declare(self):
        db = load()
        self.assertTrue(db.get("mixed_generation_justification"))
        db["standards"][0]["generation"] = "1st"
        db["standards"][1]["generation"] = "2nd"
        self.assertEqual(sev(vdb.validate(db), "ERROR"), [])
        self.assertTrue(any("generation (1st/2nd) not stated" in m for _, _, m in vdb.validate(db)))

    def test_bad_formats(self):
        db = load()
        db["project"].update(revision="Rev A", issue_date="2026-10-13", drawing_prefix="warehouse")
        paths = {p for _, p, _ in sev(vdb.validate(db), "ERROR")}
        self.assertTrue({"project.revision", "project.issue_date", "project.drawing_prefix"} <= paths)


class Register(unittest.TestCase):
    def rows(self):
        with open(EX / "document-register.csv", newline="", encoding="utf-8") as fh:
            return list(csv.DictReader(fh))

    def test_real_register_clean_against_design_basis(self):
        rows = self.rows()
        self.assertEqual(len(rows), 19)
        res = cr.check(rows, load())
        self.assertEqual([r for r in res if r[0] == "ERROR"], [])

    def test_inconsistent_package_detected(self):
        rows = self.rows()
        rows[3]["revision"] = "R01"                     # revision mismatch
        rows[4]["sheet_number"] = "WH-STR-SD-004"       # duplicate number
        rows[5]["sheet_number"] = "OF-STR-SD-006"       # wrong project prefix
        rows[6]["issue_date"] = "2026-10-13"            # bad date
        rows[7]["paper"] = "A5"
        res = cr.check(rows, load())
        text = " ".join(m for _, _, m in res)
        for frag in ("differs from design basis R00", "duplicate", "prefix OF-STR", "DD-MMM-YYYY", "paper"):
            self.assertIn(frag, text)


if __name__ == "__main__":
    unittest.main()
