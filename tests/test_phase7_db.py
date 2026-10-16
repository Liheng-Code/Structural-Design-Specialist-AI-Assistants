"""Phase 7b tests: .db model import on a SYNTHETIC fixture, plus the real GDT_CleanV3.db when present (skipped otherwise)."""
import glob
import json
import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools" / "etabs"))
sys.path.insert(0, str(ROOT / "tests" / "fixtures"))
import etabs_db_import as edb  # noqa: E402
import make_synthetic_etabs_db as fx  # noqa: E402

REAL = glob.glob("/root/.claude/uploads/*/*GDT_CleanV3.db") + glob.glob("**/GDT_CleanV3.db", recursive=True)


def do(members=True, expected=True, **d):
    t = pathlib.Path(tempfile.mkdtemp())
    fx.build(str(t / "m.db"), **d)
    (t / "members.csv").write_text(fx.MEMBERS)
    (t / "exp.yaml").write_text(fx.EXPECTED)
    return edb.run(t / "m.db", t / "out", "SYN", t / "members.csv" if members else None, t / "exp.yaml" if expected else None), t / "out"


def st(log, cid):
    return next(c["status"] for c in log["checks"] if c["id"] == cid)


class Good(unittest.TestCase):
    def test_clean_definition_import(self):
        log, out = do()
        self.assertEqual(log["summary"]["checks_fail"], 0, [c for c in log["checks"] if c["status"] == "FAIL"])
        self.assertTrue(log["summary"]["model_definition_usable"])
        self.assertFalse(log["summary"]["ready_for_calculations"])          # definition only: never ready
        self.assertEqual(st(log, "M3"), edb.NOTC)
        for f in ("import_log.json", "import_report.md", "frames.csv", "load_definitions.csv", "model_inventory.json", "analysis_provenance.proposed.yaml"):
            self.assertTrue((out / f).exists(), f)
        self.assertEqual(len(log["provenance"]["sha256"]), 64)
        self.assertTrue((out / "raw" / "m.db").exists())

    def test_lengths_converted_to_m(self):
        _, out = do()
        rows = (out / "frames.csv").read_text().splitlines()
        self.assertTrue(any(",C1,L1,Column,3.0," in r for r in rows), rows)

    def test_no_inputs_means_not_checked(self):
        log, _ = do(members=False, expected=False)
        for cid in ("M8", "M9", "M10"):
            self.assertEqual(st(log, cid), edb.NOTC)

    def test_results_flag_without_known_layout_is_not_imported(self):
        log, _ = do(results_flag=True)
        self.assertEqual(st(log, "M3"), edb.WARN)
        self.assertFalse(log["summary"]["ready_for_calculations"])

    def test_failed_exporter_table_is_reported(self):
        log, _ = do(failed_table=True)
        self.assertEqual(st(log, "M4"), edb.WARN)

    def test_units_mismatch_warned(self):
        log, _ = do()
        self.assertTrue(any("CurrUnits" in i["msg"] for i in log["issues"]))


class Bad(unittest.TestCase):
    def fails(self, **d):
        log, _ = do(**d)
        self.assertFalse(log["summary"]["model_definition_usable"], d)
        return {c["id"] for c in log["checks"] if c["status"] == "FAIL"}

    def test_missing_modelinfo(self):
        self.assertIn("M1", self.fails(no_modelinfo=True))

    def test_unknown_unit(self):
        self.assertIn("M2", self.fails(bad_units=True))

    def test_undefined_section(self):
        self.assertIn("M5", self.fails(missing_section=True))

    def test_undefined_material(self):
        self.assertIn("M5", self.fails(bad_material=True))

    def test_member_on_missing_joint(self):
        self.assertIn("M5", self.fails(bad_joint=True))

    def test_undefined_load_pattern(self):
        self.assertIn("M5", self.fails(undefined_pattern=True))

    def test_combo_term_undefined(self):
        self.assertIn("M5", self.fails(undefined_term=True))

    def test_duplicate_frame_id(self):
        self.assertIn("M6", self.fails(dup_unique=True))

    def test_duplicate_joint_id(self):
        self.assertIn("M6", self.fails(dup_joint=True))

    def test_no_supports(self):
        self.assertIn("M7", self.fails(no_supports=True))

    def test_missing_expected_case(self):
        self.assertIn("M8", self.fails(missing_case=True))

    def test_wrong_combination_factor(self):
        self.assertIn("M9", self.fails(wrong_factor=True))

    def test_project_member_missing_in_model(self):
        t = pathlib.Path(tempfile.mkdtemp())
        fx.build(str(t / "m.db"))
        (t / "members.csv").write_text(fx.MEMBERS + "C9,COL-9\n")
        log = edb.run(t / "m.db", t / "out", "SYN", t / "members.csv")
        self.assertEqual(st(log, "M10"), edb.FAIL)

    def test_source_file_not_modified(self):
        t = pathlib.Path(tempfile.mkdtemp())
        fx.build(str(t / "m.db"))
        before = (t / "m.db").read_bytes()
        edb.run(t / "m.db", t / "out", "SYN")
        self.assertEqual((t / "m.db").read_bytes(), before)


@unittest.skipUnless(REAL, "real GDT_CleanV3.db not available")
class Real(unittest.TestCase):
    def test_real_file(self):
        t = pathlib.Path(tempfile.mkdtemp())
        log = edb.run(REAL[0], t, "GDT-V3", copy_raw=False)
        self.assertTrue(log["summary"]["model_definition_usable"])
        self.assertFalse(log["summary"]["ready_for_calculations"])
        self.assertEqual(log["provenance"]["program"], "ETABS")
        inv = json.loads((t / "model_inventory.json").read_text())
        self.assertEqual(inv["frames"]["Column"], 662)


if __name__ == "__main__":
    unittest.main()
