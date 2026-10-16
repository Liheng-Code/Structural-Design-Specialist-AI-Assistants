"""Phase 6 tests: DXF generation + validation. Needs ezdxf and Structural-Drawing-Standards/05_Drafting-Styles/05-04_Layer_Standards.csv."""
import copy
import csv
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest

import ezdxf
import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools" / "cadgen"))
import build_sheets as bs  # noqa: E402
import common as c  # noqa: E402
import validate_dxf as vd  # noqa: E402

STD = ROOT / "Structural-Drawing-Standards"
EX = ROOT / "design-basis" / "examples" / "PRJ-2026-003"
HAVE_STD = (STD / "05_Drafting-Styles" / "05-04_Layer_Standards.csv").exists()


def load():
    db = yaml.safe_load((EX / "design_basis.yaml").read_text(encoding="utf-8"))
    with open(EX / "document_register.csv", newline="", encoding="utf-8") as fh:
        reg = list(csv.DictReader(fh))
    return db, reg


@unittest.skipUnless(HAVE_STD, "company standards 05-04 not found")
class Sheets(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = pathlib.Path(tempfile.mkdtemp())
        cls.db, cls.reg = load()
        cls.layers = c.load_layers(STD)
        cls.rows = {r["sheet_number"].rsplit("-", 1)[1]: r for r in cls.reg}
        cls.cover = bs.build_cover(cls.db, cls.rows["001"], cls.layers, cls.tmp)
        cls.lst = bs.build_list(cls.db, cls.rows["002"], cls.reg, cls.layers, cls.tmp)

    def check(self, path, db=None, reg=None):
        return vd.validate(path, STD, db or self.db, reg or self.reg)

    def mutated(self, base, name, fn):
        doc = ezdxf.readfile(base)
        fn(doc, doc.modelspace())
        p = self.tmp / name
        doc.saveas(p)
        return p

    def has(self, res, frag):
        return any(frag in e for e in res["errors"])

    # ---- good files
    def test_generated_sheets_validate(self):
        for p in (self.cover, self.lst):
            r = self.check(p)
            self.assertTrue(r["ok"], r["errors"])
        self.assertFalse(any("PROPOSED" in w for w in self.check(self.cover)["warnings"]))   # 05-04a/b approved by the user 14-OCT-2026

    def test_layers_loaded_match_company_csv(self):
        names = {k for k, v in self.layers.items() if v["status"] == "approved"}
        self.assertEqual(len(names), 21)   # 10 (05-04) + 5 (05-04a) + 6 (05-04b), the last two approved by the user 14-OCT-2026
        self.assertEqual(sum(1 for k in self.layers if k in {l for l in self.layers if self.layers[l]["status"] == "approved"} and k.startswith("S-")), 20)
        self.assertEqual(self.layers["S-GRID"]["linetype"], "CENTER")
        self.assertEqual(self.layers["S-STEEL-OUTLINE"]["lineweight"], 50)
        self.assertFalse(self.layers["Defpoints"]["plot"])

    def test_title_block_values_from_design_basis_and_register(self):
        a = self.check(self.cover)["title_block"]
        self.assertEqual(a["PROJ_REFERENCE"], "PJR-2026-003")
        self.assertEqual(a["DRAWING_NUMBER"], "WH-STR-SD-001")
        self.assertEqual(a["ISSUE_DATE"], "13-OCT-2026")

    def test_drawing_list_has_every_register_row_once(self):
        doc = ezdxf.readfile(self.lst)
        texts = [e.dxf.text for e in doc.modelspace().query("TEXT")]
        for r in self.reg:
            self.assertEqual(texts.count(r["sheet_number"]), 1)

    def test_isometric_segment_count_and_ridge_consistency(self):
        g = self.db["geometry"]
        self.assertEqual(len(bs.iso_points(g)), g["frames"] * 4 + (g["frames"] - 1) * 3 + 4)
        bad = dict(g, ridge_level_m=13.5)
        with self.assertRaises(bs.MissingInput):
            bs.iso_points(bad)

    # ---- deliberately broken files must be caught
    def test_detects_unknown_layer(self):
        p = self.mutated(self.cover, "m1.dxf", lambda d, m: (d.layers.add("RANDOM"), m.add_line((20, 20), (50, 20), dxfattribs={"layer": "RANDOM"})))
        self.assertTrue(self.has(self.check(p), "neither 05-04 nor 05-04a"))

    def test_detects_small_text(self):
        p = self.mutated(self.cover, "m2.dxf", lambda d, m: m.add_text("x", height=1.5, dxfattribs={"layer": "S-ANNO-TEXT", "style": "TEXT_2.0"}))
        self.assertTrue(self.has(self.check(p), "below the 2.0 mm minimum"))

    def test_detects_wrong_style_height_pair(self):
        p = self.mutated(self.cover, "m2b.dxf", lambda d, m: m.add_text("x", height=3.5, dxfattribs={"layer": "S-ANNO-TEXT", "style": "TEXT_2.0"}))
        self.assertTrue(self.has(self.check(p), "style TEXT_2.0 used with height 3.5"))

    def test_detects_wrong_units(self):
        def f(d, m):
            d.header["$INSUNITS"] = 1
        self.assertTrue(self.has(self.check(self.mutated(self.cover, "m3.dxf", f)), "not millimetres"))

    def test_detects_title_block_revision_mismatch(self):
        def f(d, m):
            ins = [e for e in m.query("INSERT") if e.dxf.name == c.TB_BLOCK][0]
            [a for a in ins.attribs if a.dxf.tag == "REVISION"][0].dxf.text = "R01"
        self.assertTrue(self.has(self.check(self.mutated(self.cover, "m4.dxf", f)), "REVISION"))

    def test_detects_wrong_project_reference(self):
        def f(d, m):
            ins = [e for e in m.query("INSERT") if e.dxf.name == c.TB_BLOCK][0]
            [a for a in ins.attribs if a.dxf.tag == "PROJ_REFERENCE"][0].dxf.text = "PRJ-2026-003"
        self.assertTrue(self.has(self.check(self.mutated(self.cover, "m5.dxf", f)), "PROJ_REFERENCE"))

    def test_detects_geometry_outside_border(self):
        p = self.mutated(self.cover, "m6.dxf", lambda d, m: m.add_line((10, 10), (430, 10), dxfattribs={"layer": "S-VIEW-ISO"}))
        self.assertTrue(self.has(self.check(p), "exceed the sheet border"))

    def test_detects_layer_property_drift(self):
        def f(d, m):
            d.layers.get("S-TBLK-BORDER").dxf.lineweight = 35
        self.assertTrue(self.has(self.check(self.mutated(self.cover, "m7.dxf", f)), "lineweight 35"))

    def test_detects_colour_and_lineweight_overrides(self):
        p = self.mutated(self.cover, "m8.dxf", lambda d, m: m.add_line((20, 20), (50, 20), dxfattribs={"layer": "S-VIEW-ISO", "color": 1, "lineweight": 70}))
        r = self.check(p)
        self.assertTrue(self.has(r, "colour override") and self.has(r, "lineweight override"))

    def test_detects_missing_drawing_list_row(self):
        def f(d, m):
            for e in list(m.query("TEXT")):
                if e.dxf.text == "WH-STR-SD-104":
                    m.delete_entity(e)
        self.assertTrue(self.has(self.check(self.mutated(self.lst, "m9.dxf", f)), "WH-STR-SD-104 0 time"))

    def test_detects_sheet_not_in_register(self):
        reg = [r for r in self.reg if r["sheet_number"] != "WH-STR-SD-001"]
        self.assertTrue(self.has(self.check(self.cover, reg=reg), "not in the document register"))

    def test_detects_wrong_style_font(self):
        def f(d, m):
            d.styles.get("TEXT_2.0").dxf.font = "times.ttf"
        self.assertTrue(self.has(self.check(self.mutated(self.cover, "m10.dxf", f)), "font is times.ttf"))

    def test_unreadable_file(self):
        bad = self.tmp / "bad.dxf"
        bad.write_text("not a dxf")
        self.assertFalse(vd.validate(bad, STD)["ok"])

    # ---- incomplete project / missing inputs
    def test_missing_geometry_gives_visible_note_not_silent_blank(self):
        db = copy.deepcopy(self.db)
        db.pop("geometry")
        (self.tmp / "inc").mkdir(exist_ok=True)
        p = bs.build_cover(db, self.rows["001"], self.layers, self.tmp / "inc")
        r = vd.validate(p, STD, db, self.reg)
        self.assertTrue(r["ok"])
        self.assertTrue(any("not generated" in w for w in r["warnings"]))
        texts = [e.dxf.text for e in ezdxf.readfile(p).modelspace().query("TEXT")]
        self.assertTrue(any("NOT GENERATED" in t for t in texts))

    def test_inconsistent_geometry_not_drawn(self):
        db = copy.deepcopy(self.db)
        db["geometry"]["ridge_level_m"] = 14.0
        (self.tmp / "inc2").mkdir(exist_ok=True)
        p = bs.build_cover(db, self.rows["001"], self.layers, self.tmp / "inc2")
        texts = [e.dxf.text for e in ezdxf.readfile(p).modelspace().query("TEXT")]
        self.assertTrue(any("geometry inconsistent" in t for t in texts))

    def test_missing_company_layer_standard_stops(self):
        with self.assertRaises(FileNotFoundError):
            c.load_layers(self.tmp / "nowhere")

    def test_register_too_long_for_one_sheet_stops(self):
        big = [dict(self.reg[0], sheet_number=f"WH-STR-SD-{i:03d}") for i in range(3, 40)] + self.reg[:2]
        (self.tmp / "big").mkdir(exist_ok=True)
        with self.assertRaises(bs.MissingInput):
            bs.build_list(self.db, self.rows["002"], big, self.layers, self.tmp / "big")

    # ---- plot
    def test_preview_pdf_exists_and_lineweights_follow_standard(self):
        pdf = self.tmp / "p.pdf"
        bs.plot_pdf([self.cover], pdf)
        self.assertGreater(pdf.stat().st_size, 5000)
        if shutil.which("pdftoppm"):
            subprocess.run(["pdftoppm", "-r", "400", "-png", "-f", "1", "-l", "1", str(pdf), str(self.tmp / "pp")], check=True)
            from PIL import Image
            import numpy as np
            Image.MAX_IMAGE_PIXELS = None
            a = np.array(Image.open(next(self.tmp.glob("pp-*.png"))).convert("L")) < 128
            px = lambda x: x * 25.4 / 400
            col = a[:, int(150 / 25.4 * 400)]  # a vertical probe through the border top/title block rows at x = 150 mm
            runs, r = [], 0
            for v in col:
                if v:
                    r += 1
                elif r:
                    runs.append(px(r)); r = 0
            self.assertTrue(any(0.42 <= w <= 0.60 for w in runs), runs)      # 0.50 border present
            self.assertTrue(any(0.20 <= w <= 0.30 for w in runs), runs)      # 0.25 title block line present

    def test_cli_reports_no_dwg(self):
        cp = subprocess.run([sys.executable, str(ROOT / "tools/cadgen/build_sheets.py"), "--design-basis", str(EX / "design_basis.yaml"),
                             "--register", str(EX / "document_register.csv"), "--standards", str(STD), "--out", str(self.tmp / "cli"), "--no-pdf"],
                            capture_output=True, text=True)
        self.assertEqual(cp.returncode, 0, cp.stderr)
        out = json.loads(cp.stdout)
        self.assertIsNone(out["dwg"])
        self.assertTrue(all(p.endswith(".dxf") for p in out["dxf"]))


if __name__ == "__main__":
    unittest.main()
