"""Tests for 04_tools/cadgen/restandardise.py on a SYNTHETIC old-style sheet (not the user's real set). Needs ezdxf and the 05 standards folder."""
import csv
import pathlib
import shutil
import sys
import tempfile
import unittest

import ezdxf
import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "04_tools" / "cadgen"))
import common as c  # noqa: E402
import restandardise as rs  # noqa: E402
import validate_dxf as vd  # noqa: E402

STD = ROOT / "01_standards"
EX = ROOT / "03_projects" / "PJR-2026-003"
HAVE = (STD / "05-drafting-styles" / "05-04-layer-standards.csv").exists()


def old_sheet(path, name="WH-STR-SD-104", unmapped=False, small=True):
    d = ezdxf.new("R2013")
    for ln in ("FRAME", "TITLE", "TEXT", "RC", "STEEL", "THIN", "REBAR", "DIM", "GRID"):
        d.layers.add(ln)
    m = d.modelspace()
    m.add_lwpolyline([(7, 5), (413, 5), (413, 292), (7, 292)], close=True, dxfattribs={"layer": "FRAME"})
    m.add_text("PRJ-2026-003", height=2.8, dxfattribs={"layer": "TITLE"}).set_placement((6.2, 283.2))
    m.add_text("PROJ. REFERENCE:", height=1.7, dxfattribs={"layer": "THIN"}).set_placement((8, 289))
    m.add_line((7, 266.2), (413, 266.2), dxfattribs={"layer": "TITLE"})
    m.add_text("1:75", height=2.4, dxfattribs={"layer": "TITLE"}).set_placement((240.2, 270.2))
    m.add_lwpolyline([(50, 100), (150, 100), (150, 200)], dxfattribs={"layer": "RC", "color": 3})
    m.add_line((60, 120), (140, 120), dxfattribs={"layer": "REBAR"})
    m.add_text("NOTE ONE", height=1.7 if small else 2.0, dxfattribs={"layer": "TEXT"}).set_placement((60, 150))
    m.add_text("LEVEL", height=2.6, dxfattribs={"layer": "DIM"}).set_placement((60, 160))
    if unmapped:
        d.layers.add("WEIRD")
        m.add_line((0, 0), (10, 10), dxfattribs={"layer": "WEIRD"})
    d.saveas(path)


@unittest.skipUnless(HAVE, "company standards 05-04 not found")
class Restd(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = yaml.safe_load((EX / "design-basis.yaml").read_text(encoding="utf-8"))
        with open(EX / "document-register.csv", newline="", encoding="utf-8") as fh:
            cls.reg = list(csv.DictReader(fh))
        cls.layers = c.load_layers(STD)

    def run_one(self, **kw):
        d = pathlib.Path(tempfile.mkdtemp())
        src = d / "WH-STR-SD-104.dxf"
        old_sheet(src, **kw)
        res = rs.restandardise(src, d, self.db, self.reg, self.layers)
        return d, res

    def test_output_validates_and_original_untouched(self):
        d = pathlib.Path(tempfile.mkdtemp())
        src = d / "WH-STR-SD-104.dxf"
        old_sheet(src)
        before = src.read_bytes()
        res = rs.restandardise(src, d / "out", self.db, self.reg, self.layers) if (d / "out").mkdir() is None else None
        self.assertEqual(src.read_bytes(), before)
        v = vd.validate(d / "out" / res["file"], STD, self.db, self.reg)
        self.assertTrue(v["ok"], v["errors"])

    def test_text_never_smaller_and_standard_styles(self):
        d, res = self.run_one()
        doc = ezdxf.readfile(d / res["file"])
        hs = {e.dxf.text: (e.dxf.height, e.dxf.style) for e in doc.modelspace().query("TEXT")}
        self.assertEqual(hs["NOTE ONE"], (2.0, "TEXT_2.0"))
        self.assertEqual(hs["LEVEL"], (2.5, "TEXT_2.5"))
        self.assertGreaterEqual(res["text_resized_up"], 2)

    def test_title_strip_replaced_by_block_and_old_border_dropped(self):
        d, res = self.run_one()
        doc = ezdxf.readfile(d / res["file"])
        ins = [e for e in doc.modelspace().query("INSERT") if e.dxf.name == c.TB_BLOCK]
        self.assertEqual(len(ins), 1)
        att = {a.dxf.tag: a.dxf.text for a in ins[0].attribs}
        self.assertEqual(att["DRAWING_NUMBER"], "WH-STR-SD-104")
        self.assertEqual(att["SCALE"], "1:75")                 # read from the old strip
        self.assertEqual(att["PROJ_REFERENCE"], "PJR-2026-003")
        self.assertIn("PROJ_REFERENCE", res["old_title_block_values_not_matching_register_or_design_basis"])  # old strip said PRJ
        self.assertNotIn("FRAME", {e.dxf.layer for e in doc.modelspace()})

    def test_layers_mapped_and_colour_overrides_removed(self):
        d, res = self.run_one()
        doc = ezdxf.readfile(d / res["file"])
        lays = {e.dxf.layer for e in doc.modelspace()}
        self.assertTrue({"S-CONC-OUTLINE", "S-REBAR", "S-ANNO-TEXT", "S-ANNO-DIMS"} <= lays)
        for e in doc.modelspace().query("LWPOLYLINE"):
            self.assertIn(e.dxf.get("color", 256), (256,))

    def test_unmapped_layer_is_reported_not_guessed(self):
        d, res = self.run_one(unmapped=True)
        self.assertIn("error", res)
        self.assertIn("WEIRD", res["error"])

    def test_sheet_not_in_register_is_skipped(self):
        d = pathlib.Path(tempfile.mkdtemp())
        src = d / "XX-STR-SD-999.dxf"
        old_sheet(src)
        res = rs.restandardise(src, d, self.db, self.reg, self.layers)
        self.assertIn("not in register", res["error"])


if __name__ == "__main__":
    unittest.main()
