"""M1 tests: structural layout DXF -> GeometryModel. Run: python -m unittest discover -s tests -v

The drawing is synthetic, built here with ezdxf; its sizes are made up for testing and are not project values.
It holds one of each case the reader must handle: a legend with sample shapes on the structural layers (to be
excluded) and a legend key (hatch -> thickness), a core drawn as two nested outlines, a rectangular and an L wall,
labelled band beam and drop panel, an opening with its X, a grid block whose bubbles sit away from their own insertion
point, a label that matches nothing, and an entity on a layer the layer map does not name.
"""
import pathlib
import sys
import tempfile
import unittest

import ezdxf
from pydantic import ValidationError

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "04_tools"))
from calc_lib.core import schemas as s  # noqa: E402
from model_builder import dxf_geometry as dg  # noqa: E402

LAYER_MAP = {
    "units": "mm",
    "elements": {"column": {"layers": ["COL"]}, "wall": {"layers": ["WALL"]}, "slab_edge": {"layers": ["SLAB"]},
                 "opening": {"layers": ["OPEN"]}, "drop_panel": {"layers": ["DP"]}, "band_beam": {"layers": ["BB"]},
                 "grid": {"block": "GRID"}},
    "labels": {"layers": ["LABEL"]},
    "ignore": {"layers": ["HATCH"]},
    "exclude_regions": [{"name": "legend", "frame": {"layer": "TXT", "near_text": "LEGEND"}}],
}


def rect(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def make_dxf(path, insunits=4):
    doc = ezdxf.new("R2010")
    doc.header["$INSUNITS"] = insunits
    msp = doc.modelspace()

    def pline(pts, layer, closed=True):
        msp.add_lwpolyline(pts, close=closed, dxfattribs={"layer": layer})

    def hatch(pts, layer, pattern):
        h = msp.add_hatch(dxfattribs={"layer": layer})
        h.set_pattern_fill(pattern, scale=1)
        h.paths.add_polyline_path(pts, is_closed=True)

    def text(s_, x, y, layer="LABEL"):
        msp.add_text(s_, dxfattribs={"layer": layer, "height": 200, "insert": (x, y)})

    # plan
    pline(rect(0, 0, 20000, 10000), "SLAB")
    hatch(rect(0, 0, 20000, 10000), "HATCH", "ANSI31")
    pline(rect(4700, 4700, 5300, 5300), "COL")
    pline(rect(14700, 4700, 15300, 5300), "COL")
    pline(rect(13800, 3800, 16200, 6200), "DP")
    hatch(rect(13800, 3800, 16200, 6200), "DP", "SACNCR")
    text("DROP PANEL 1", 14000, 5800)
    text("450mm THK", 14000, 5400)
    pline(rect(6000, 4250, 13000, 5750), "BB")
    text("BB1 (1500x350)", 9000, 4900)
    pline(rect(2000, 7000, 6000, 9600), "WALL")                     # core: outer
    pline(rect(2300, 7300, 5700, 9300), "WALL")                     # core: inner, 300 mm ring
    pline(rect(8000, 7000, 8200, 9000), "WALL")                     # 200 mm wall
    pline([(10000, 7000), (10000, 9000), (10250, 9000), (10250, 7250), (12000, 7249), (12000, 7000)], "WALL")  # L
    pline(rect(17000, 7000, 18000, 8000), "OPEN")
    pline([(17000, 7000), (18000, 8000)], "OPEN", closed=False)     # the X inside the opening
    pline([(17000, 8000), (18000, 7000)], "OPEN", closed=False)
    text("BB9 (900x350)", 60000, 60000)                             # matches nothing
    msp.add_line((0, -3000), (5000, -3000), dxfattribs={"layer": "JUNK"})

    # legend: open frame, samples on the structural layers, key rows
    pline([(30000, 0), (40000, 0), (40000, 8000), (30000, 8000), (30000, 0)], "TXT", closed=False)
    text("LEGEND", 31000, 7500, "TXT")
    pline(rect(31000, 5000, 33000, 6000), "SLAB")
    hatch(rect(31000, 5000, 33000, 6000), "HATCH", "ANSI31")
    text("PT SLAB", 33300, 5700)
    text("THK: 200mm", 33300, 5200)
    pline(rect(31000, 2000, 33000, 3000), "DP")
    hatch(rect(31000, 2000, 33000, 3000), "DP", "SACNCR")
    text("DROP PANEL", 33300, 2700)
    text("THK: 450mm", 33300, 2200)
    pline(rect(36000, 1000, 36600, 1600), "COL")

    # grid block: lines, and bubble inserts whose own insertion point is far away but whose attribute is at the bubble
    bub = doc.blocks.new("BUB")
    bub.add_attdef("G", (0, 0))
    grid = doc.blocks.new("GRID")
    grid.add_line((5000, -2000), (5000, 12000))
    grid.add_line((-2000, 5000), (22000, 5000))
    for label, pos in (("A", (5000, 12300)), ("1", (-2300, 5000))):
        ins = grid.add_blockref("BUB", (-250000, 80000))
        ins.add_attrib("G", label, insert=pos)
    msp.add_blockref("GRID", (0, 0))
    doc.saveas(path)


class Reader(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.dxf = pathlib.Path(cls.tmp.name) / "plan.dxf"
        make_dxf(cls.dxf)
        cls.g = dg.Reader(cls.dxf, LAYER_MAP, "TEST-001", "3F").read().model
        cls.codes = [i.code for i in cls.g.issues]

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_legend_samples_excluded(self):
        self.assertEqual(len(self.g.columns), 2)
        self.assertEqual(len(self.g.slabs), 1)
        self.assertEqual(len(self.g.drop_panels), 1)

    def test_slab_thickness_from_legend_key(self):
        self.assertEqual(self.g.slabs[0].thickness.to("mm").magnitude, 200)

    def test_labels(self):
        dp, bb = self.g.drop_panels[0], self.g.band_beams[0]
        self.assertEqual((dp.label, dp.depth.to("mm").magnitude), ("DROP PANEL 1", 450))
        self.assertEqual(bb.label, "BB1 (1500x350)")
        self.assertEqual((bb.width.to("mm").magnitude, bb.depth.to("mm").magnitude), (1500, 350))
        self.assertIn("LABEL_UNMATCHED", self.codes)

    def test_walls_ring_rectangle_and_l(self):
        t = sorted(w.thickness.to("mm").magnitude for w in self.g.walls)
        self.assertEqual(t, [200, 250, 300, 300, 300, 300])
        self.assertNotIn("WALL_SHAPE", self.codes)

    def test_columns(self):
        c = self.g.columns[0]
        self.assertEqual((c.centre.x, c.centre.y, c.b.to("mm").magnitude, c.h.to("mm").magnitude),
                         (5000, 5000, 600, 600))

    def test_opening_and_its_x(self):
        self.assertEqual(len(self.g.openings), 1)
        self.assertNotIn("OPEN_POLYLINE", self.codes)

    def test_grid_labels_from_attributes(self):
        got = {(gr.label, gr.axis, gr.offset) for gr in self.g.grids}
        self.assertEqual(got, {("A", "X", 5000), ("1", "Y", 5000)})

    def test_unmapped_layer_reported(self):
        self.assertIn("UNMAPPED_LAYER", self.codes)
        self.assertFalse([i for i in self.g.issues if i.severity == "ERROR"])

    def test_units_checked(self):
        bad = pathlib.Path(self.tmp.name) / "bad.dxf"
        make_dxf(bad, insunits=0)
        with self.assertRaises(ValueError):
            dg.Reader(bad, LAYER_MAP, "T", "3F").read()
        with self.assertRaises(ValueError):
            dg.Reader(self.dxf, {**LAYER_MAP, "units": "m"}, "T", "3F").read()

    def test_run_writes_files_and_is_repeatable(self):
        lm = pathlib.Path(self.tmp.name) / "layer-map.yaml"
        lm.write_text(__import__("yaml").safe_dump(LAYER_MAP), encoding="utf-8")
        out = pathlib.Path(self.tmp.name) / "out"
        h1 = s.content_hash(dg.run(self.dxf, lm, "TEST-001", "3F", out).model)
        h2 = s.content_hash(dg.run(self.dxf, lm, "TEST-001", "3F", out).model)
        self.assertEqual(h1, h2)
        for name in ("geometry.json", "geometry-review.md", "geometry-preview.pdf"):
            self.assertTrue((out / name).stat().st_size > 0, name)
        again = s.GeometryModel.model_validate_json((out / "geometry.json").read_text(encoding="utf-8"))
        self.assertEqual(s.content_hash(again), h1)


class Helpers(unittest.TestCase):
    def test_l_wall_tolerates_1mm_slop(self):
        _, t = dg.l_wall([(0, 0), (0, 2900), (2575, 2899), (2575, 2650), (250, 2650), (250, 0)])
        self.assertAlmostEqual(t, 250, delta=1)
        self.assertIsNone(dg.l_wall([(0, 0), (0, 2900), (2575, 2900), (2575, 2500), (250, 2500), (250, 0)]))

    def test_ring_needs_uniform_gap(self):
        self.assertIsNotNone(dg.ring_walls(rect(0, 0, 1000, 1000), rect(100, 100, 900, 900)))
        self.assertIsNone(dg.ring_walls(rect(0, 0, 1000, 1000), rect(100, 200, 900, 900)))

    def test_confirmed_geometry_must_be_complete(self):
        slab = {"id": "S1", "source": "extracted_from_cad", "outline": [{"x": 0, "y": 0}, {"x": 1, "y": 0},
                                                                       {"x": 1, "y": 1}]}
        s.GeometryModel(project_code="P", floor_label="3F", slabs=[slab])          # unreviewed: missing is allowed
        review = {"state": "CONFIRMED", "reviewed_by": "X", "reviewed_at": "2026-10-25T10:00:00"}
        with self.assertRaises(ValidationError):
            s.GeometryModel(project_code="P", floor_label="3F", slabs=[slab], review=review)
        err = {"severity": "ERROR", "code": "WALL_SHAPE", "message": "m"}
        with self.assertRaises(ValidationError):
            s.GeometryModel(project_code="P", floor_label="3F", issues=[err], review=review)


if __name__ == "__main__":
    unittest.main()
