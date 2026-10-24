"""Phase 7 tests: ETABS/SAFE import on a SYNTHETIC fixture (not a real export). Run: python -m unittest tests.test_etabs_import -v"""
import json
import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "04_tools" / "etabs"))
sys.path.insert(0, str(ROOT / "tests" / "fixtures"))
import etabs_import as ei  # noqa: E402
import make_synthetic_etabs as fx  # noqa: E402


def do(ext="xlsx", assume=None, **defects):
    d = pathlib.Path(tempfile.mkdtemp())
    fx.build(d / "in", **defects)
    i = d / "in"
    log = ei.run([i / f"synthetic_export.{ext}"], d / "out", "SYN-1", members_csv=i / "members.csv", expected_yaml=i / "expected_cases.yaml",
                 hand_yaml=i / "hand_totals.yaml", assume_units=assume)
    return log, d / "out"


def status(log, cid):
    return next(c["status"] for c in log["checks"] if c["id"] == cid)


def fails(log):
    return {c["id"] for c in log["checks"] if c["status"] == ei.FAIL}


class Good(unittest.TestCase):
    def test_xlsx_and_csv_pass(self):
        for ext in ("xlsx", "csv"):
            log, out = do(ext)
            self.assertTrue(log["summary"]["ready_for_calculations"], ext)
            self.assertEqual(log["summary"]["checks_fail"], 0)
            self.assertEqual(log["summary"]["rows_results"], 40)

    def test_outputs_and_provenance(self):
        log, out = do()
        for f in ("analysis_results.csv", "joint_reactions.csv", "base_reactions.csv", "import_log.json", "import_report.md", "analysis_provenance.proposed.yaml"):
            self.assertTrue((out / f).exists(), f)
        raw = out / "raw" / "synthetic_export.xlsx"
        self.assertEqual(log["provenance"]["export_files"][0]["sha256"], ei.sha256(raw))
        self.assertIn("SYNTHETIC", json.dumps(log["provenance"]["program_control"]))
        self.assertIn("does not show the analysis model is correct", log["disclaimer"])
        self.assertIn("PROPOSED", (out / "analysis_provenance.proposed.yaml").read_text())
        self.assertTrue(any("model_file" in i["msg"] for i in log["issues"]), "missing provenance must be flagged")

    def test_unit_conversion(self):
        a, _ = do()
        b, out = do(units_mm_n=True)
        self.assertTrue(b["summary"]["ready_for_calculations"])
        import csv
        rows = list(csv.DictReader(open(out / "joint_reactions.csv")))
        fz = sorted(float(r["FZ"]) for r in rows if r["case_or_combo"] == "DEAD")
        self.assertEqual(fz, [480.0, 500.0, 500.0, 520.0])
        self.assertTrue(any("x0.001" in n for t in b["tables"] for n in t["notes"]))

    def test_c7_not_checked_without_tolerance(self):
        d = pathlib.Path(tempfile.mkdtemp())
        fx.build(d / "in")
        (d / "in" / "hand_totals.yaml").write_text("fz_kN:\n  DEAD: 2000\n")
        log = ei.run([d / "in/synthetic_export.xlsx"], d / "o", "S", hand_yaml=d / "in/hand_totals.yaml")
        self.assertEqual(status(log, "C7"), ei.NOTC)

    def test_not_checked_when_no_inputs(self):
        d = pathlib.Path(tempfile.mkdtemp())
        fx.build(d / "in")
        log = ei.run([d / "in/synthetic_export.xlsx"], d / "o", "S")
        for cid in ("C1", "C2", "C3", "C5", "C7"):
            self.assertEqual(status(log, cid), ei.NOTC, cid)


class Bad(unittest.TestCase):
    def blocked(self, **d):
        log, _ = do(**d)
        self.assertFalse(log["summary"]["ready_for_calculations"], d)
        return log

    def test_missing_case(self):
        self.assertIn("C1", fails(self.blocked(drop_case=True)))

    def test_wrong_combo_factor(self):
        self.assertIn("C2", fails(self.blocked(wrong_combo_factor=True)))

    def test_superposition_mismatch(self):
        self.assertIn("C5", fails(self.blocked(break_superposition=True)))

    def test_non_equilibrium_base(self):
        self.assertIn("C6", fails(self.blocked(scale_base=True)))

    def test_hand_total_mismatch(self):
        self.assertIn("C7", fails(self.blocked(bad_hand=True)))

    def test_unmapped_member(self):
        self.assertIn("C3", fails(self.blocked(extra_member=True)))

    def test_member_without_results_is_warning(self):
        log, _ = do(drop_member=True)
        self.assertEqual(status(log, "C3"), ei.OK)
        self.assertEqual(status(log, "C3b"), ei.WARN)

    def test_duplicate_rows(self):
        self.assertIn("C4", fails(self.blocked(duplicate_row=True)))

    def test_missing_units_rejected(self):
        log = self.blocked(no_units=True)
        self.assertTrue(any(t["status"].startswith("REJECTED") for t in log["tables"]))

    def test_assumed_units_warn_not_pass(self):
        log, _ = do(no_units=True, assume=("kN", "m"))
        self.assertEqual(status(log, "C8"), ei.WARN)
        self.assertTrue(log["summary"]["ready_for_calculations"])

    def test_unknown_unit(self):
        log = self.blocked(bad_unit=True)
        self.assertEqual(status(log, "C8"), ei.FAIL)

    def test_missing_column(self):
        log = self.blocked(drop_column=True)
        self.assertTrue(any("MZ" in i["msg"] for i in log["issues"]))

    def test_empty_cell(self):
        log = self.blocked(empty_cell=True)
        self.assertTrue(any("empty" in i["msg"] for i in log["issues"]))

    def test_unsupported_table_reported_not_imported(self):
        log, _ = do(extra_table=True)
        t = next(t for t in log["tables"] if t["name"] == "Story Drifts")
        self.assertIn("UNSUPPORTED", t["status"])
        self.assertTrue(log["summary"]["ready_for_calculations"])
        self.assertTrue(any(i["level"] == ei.WARN and "Story Drifts" in i["msg"] for i in log["issues"]))

    def test_unit_factor(self):
        self.assertAlmostEqual(ei.unit_factor("N-mm")[0], 1e-6)
        self.assertIsNone(ei.unit_factor("furlong"))


if __name__ == "__main__":
    unittest.main()
