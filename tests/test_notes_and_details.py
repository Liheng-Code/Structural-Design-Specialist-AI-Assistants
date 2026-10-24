"""Unit tests for the reusable Eurocode General Notes & Standard Details library (003-007) and 06-templates exporter."""
import copy
import csv
import pathlib
import sys
import tempfile
import unittest

import ezdxf
import yaml
from ezdxf import bbox

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "04_tools" / "cadgen"))
import build_notes_and_details as bnd  # noqa: E402
import common as c  # noqa: E402
import validate_dxf as vd  # noqa: E402

STD = ROOT / "01_standards"
EX = ROOT / "03_projects" / "PJR-2026-003"
HAVE_STD = (STD / "05-drafting-styles" / "05-04-layer-standards.csv").exists()


def count_overlaps(msp, tol=0.3):
    boxes = []
    for e in msp.query("TEXT"):
        b = bbox.extents([e])
        if b.has_data:
            boxes.append((b.extmin.x, b.extmin.y, b.extmax.x, b.extmax.y))
    n = 0
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            if min(boxes[i][2], boxes[j][2]) - max(boxes[i][0], boxes[j][0]) > tol and min(boxes[i][3], boxes[j][3]) - max(boxes[i][1], boxes[j][1]) > tol:
                n += 1
    return n


@unittest.skipUnless(HAVE_STD, "company standards 05-04 not found")
class EurocodeNotesAndDetailsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = pathlib.Path(tempfile.mkdtemp())
        cls.db = yaml.safe_load((EX / "design-basis.yaml").read_text(encoding="utf-8"))
        with open(EX / "document-register.csv", newline="", encoding="utf-8-sig") as fh:
            cls.reg = list(csv.DictReader(fh))
        cls.ov = yaml.safe_load((EX / "notes-overrides.yaml").read_text(encoding="utf-8"))
        cls.layers = c.load_layers(STD)
        cls.made = bnd.build_all_notes_and_details(cls.db, cls.reg, cls.layers, cls.tmp, STD, cls.ov)

    def test_all_five_sheets_generated_and_validate_with_zero_overlaps(self):
        self.assertEqual(len(self.made), 5)
        for p in self.made:
            res = vd.validate(p, STD, self.db, self.reg)
            self.assertTrue(res["ok"], f"{p.name}: {res['errors']}")
            self.assertEqual(res["warnings"], [])
            doc = ezdxf.readfile(p)
            self.assertEqual(count_overlaps(doc.modelspace()), 0, f"text overlaps on {p.name}")

    def test_ec2_anchorage_table_matches_en1992_and_mandrel_correction(self):
        anch = bnd.compute_ec2_anchorage_table("C30/37", 390, [10, 12, 16, 20, 25], 2.03)
        # Exact EN 1992-1-1 eq. 8.3 rounded to nearest 5 mm (within 5 mm / 1% reconciliation tolerance of SD-004)
        self.assertEqual(anch["good"], ["280", "335", "445", "555", "695"])
        for g_calc, g_dwg in zip([int(x) for x in anch["good"]], [280, 335, 445, 560, 700]):
            self.assertLessEqual(abs(g_calc - g_dwg), 5)
        self.assertEqual(anch["mandrel"], ["40", "48", "64", "140", "175"])

    def test_generic_project_without_overrides_uses_tbc_and_validates(self):
        generic_out = self.tmp / "generic"
        db2 = copy.deepcopy(self.db)
        db2["materials"] = []  # remove materials to ensure TBC fallback without inventing grades
        made_gen = bnd.build_all_notes_and_details(db2, self.reg, self.layers, generic_out, STD, overrides=None)
        self.assertEqual(len(made_gen), 5)
        for p in made_gen:
            res = vd.validate(p, STD, db2, self.reg)
            self.assertTrue(res["ok"], f"{p.name}: {res['errors']}")
            doc = ezdxf.readfile(p)
            self.assertEqual(count_overlaps(doc.modelspace()), 0, f"text overlaps on generic {p.name}")
            texts = " ".join(e.dxf.text for e in doc.modelspace().query("TEXT"))
            if p.name.startswith("WH-STR-SD-004"):
                self.assertIn("TBC", texts)

    def test_templates_library_blocks_and_sheets_exist(self):
        blk_dir = STD / "06-templates" / "blocks"
        sht_dir = STD / "06-templates" / "sheets"
        self.assertTrue((blk_dir / "STR_TITLEBLOCK_A3.dxf").exists())
        self.assertTrue((blk_dir / "BLK_EC2_BENDS_AND_HOOKS.dxf").exists())
        self.assertTrue((blk_dir / "BLK_EC3_BOLT_SPACING_TABLE.dxf").exists())
        self.assertTrue((sht_dir / "TPL-STR-SD-003_R00.dxf").exists())
        self.assertTrue((sht_dir / "TPL-STR-SD-007_R00.dxf").exists())


if __name__ == "__main__":
    unittest.main()
