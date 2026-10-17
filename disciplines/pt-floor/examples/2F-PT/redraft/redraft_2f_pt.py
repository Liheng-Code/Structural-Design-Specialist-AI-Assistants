#!/usr/bin/env python3
"""Redraft of the 2F post-tension layout plan (source: Success Design & Build, sheets 14-16, Rev 01, 22-AUG-2023).

Geometry comes from the vector data of the source drawing (plan.json, millimetres, origin = grid 1 / grid A).
Annotation text and the tendon schedule are TRANSCRIBED from the source drawing by reading it; they are not computed
and must be checked against the source. No engineering value is invented: anything not on the source is marked TBC.

Usage: python redraft_2f_pt.py --plan plan.json --standards <Structural-Drawing-Standards> --out <dir>
Output: DXF (paper-space millimetres, 1:200, company layers + PROPOSED 05-04c) and a script-rendered preview PDF.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import pathlib
import sys

import ezdxf
from ezdxf.enums import TextEntityAlignment as A

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import build_sheets as bs  # noqa: E402
import common as c  # noqa: E402

SC = 200.0                      # plan scale 1:200 -> 1 paper mm = 200 model mm
GX0, P0 = 62.0, 122.0           # paper position of grid 1 (x) and grid A (y)
GRID_X = [0, 10000, 19000, 28000, 37000, 47000]
GRID_Y = {"A": 0, "B": 4300, "C": 6300, "D": 14800, "E": 19800, "F": 24300}
CHECK_NOTE = "TRANSCRIBED FROM SOURCE - VERIFY"


def PX(x): return GX0 + x / SC
def PY(y): return P0 + y / SC


# ---------------------------------------------------------------- transcribed data (from the source drawing, by reading)
# group no., mark, strands, first strand no., last strand no., length (m)   -- Y direction, left to right
Y_TENDONS = [
    (15, "Y1", 4, 54, 57, 9.45), (16, "Y1A", 4, 58, 61, 9.25), (17, "Y1A", 4, 62, 65, 9.25), (18, "Y2", 4, 66, 69, 9.00),
    (19, "Y2", 3, 70, 72, 9.00), (20, "Y3", 2, 73, 74, 8.95), (21, "Y3", 2, 75, 76, 8.95), (22, "Y3", 2, 77, 78, 8.95),
    (23, "Y4", 2, 79, 80, 20.75), (24, "Y5", 4, 81, 84, 18.10), (25, "Y6", 4, 85, 88, 18.60), (26, "Y6", 4, 89, 92, 18.60),
    (27, "Y7", 4, 93, 96, 18.10), (28, "Y8", 2, 97, 98, 18.40), (29, "Y9", 2, 99, 100, 20.70), (30, "Y9A", 2, 101, 102, 21.20),
    (31, "Y10", 4, 103, 106, 20.70), (32, "Y11", 4, 107, 110, 21.70), (33, "Y11", 4, 111, 114, 21.70), (34, "Y12", 4, 115, 118, 18.70),
    (35, "Y12", 2, 119, 120, 18.70), (36, "Y12", 2, 121, 122, 18.70), (37, "Y12", 2, 123, 124, 18.70), (38, "Y12", 4, 125, 128, 18.70),
    (39, "Y11", 4, 129, 132, 21.70), (40, "Y11", 4, 133, 136, 21.70), (41, "Y10", 4, 137, 140, 20.70), (42, "Y9A", 2, 141, 142, 21.20),
    (43, "Y9", 2, 143, 144, 20.70), (44, "Y13", 2, 145, 146, 21.25), (45, "Y7", 4, 147, 150, 18.10), (46, "Y6", 4, 151, 154, 18.60),
    (47, "Y6", 4, 155, 158, 18.60), (48, "Y5", 4, 159, 162, 18.10), (49, "Y4", 2, 163, 164, 20.75), (50, "Y14", 2, 165, 166, 20.75),
    (51, "Y15", 2, 167, 168, 9.45), (52, "Y15", 2, 169, 170, 9.45), (53, "Y16", 3, 171, 173, 9.50), (54, "Y16", 4, 174, 177, 9.50),
    (55, "Y17A", 4, 178, 181, 9.75), (56, "Y17A", 4, 182, 185, 9.75), (57, "Y17", 4, 186, 189, 9.95),
]
# X / EX tendons: group, mark, strands, first, last, length (m), model y of the duct (mm), side of label ("L"/"R")
X_TENDONS = [
    (3, "X1", 4, 8, 11, 21.05, 23903, "L"), (4, "X1", 4, 12, 15, 21.05, 23551, "L"), (5, "X1", 4, 16, 19, 21.05, 23203, "L"),
    (60, "EX1", 3, 196, 198, 14.85, 21400, "L"), (61, "EX1", 2, 199, 200, 14.85, 21100, "L"),
    (6, "X2", 3, 20, 22, 36.05, 15752, "L"), (7, "X2", 4, 23, 26, 36.05, 15353, "L"),
    (8, "X3", 4, 27, 30, 48.90, 12550, "L"), (9, "X3", 4, 31, 34, 48.90, 12150, "L"), (10, "X3", 4, 35, 38, 48.90, 11751, "L"),
    (59, "EX2", 3, 193, 195, 12.95, 7549, "L"),
    (11, "X4", 4, 39, 42, 48.25, 7202, "L"), (12, "X4", 4, 43, 46, 48.25, 6850, "L"),
    (13, "X5", 4, 47, 50, 20.15, 5803, "L"), (14, "X6", 3, 51, 53, 20.65, 4752, "L"),
    (63, "EX3", 3, 203, 205, 14.90, 21400, "R"), (62, "EX3", 2, 201, 202, 14.90, 21100, "R"),
    (58, "EX4", 3, 190, 192, 12.95, 7549, "R"), (2, "X7", 4, 4, 7, 20.15, 5803, "R"), (1, "X8", 3, 1, 3, 20.65, 4752, "R"),
]
LIFTS = ["LIFT 1", "LIFT 2", "LIFT 3", "LIFT 4"]
# columns: (tag, size mm, [(x_mm, y_mm)])   sizes measured from the source vector data
COLUMNS = [
    ("C1", 600, [(0, 24300), (19000, 24300), (28000, 24300), (47000, 24300), (0, 14800), (47000, 14800),
                 (0, 4300), (10000, 4300), (19000, 4300), (28000, 4300), (37000, 4300), (47000, 4300)]),
    ("C3", 800, [(10000, 6300), (19000, 6300), (28000, 6300), (37000, 6300)]),
    ("C4", 1100, [(10000, 14800), (19000, 14800), (28000, 14800), (37000, 14800)]),
]
SOURCE_NOTES = [
    "SOURCE GENERAL NOTES (TRANSCRIBED FROM SOURCE SHEET - NOT VERIFIED):",
    "1. CONCRETE: MIN. fc' = 32 MPa AT 28 DAYS (CYLINDER). MIN. fci = 24 MPa AT TRANSFER (CYLINDER).",
    "    MIN. CONCRETE COVER TO NEAREST REINFORCEMENT = 20 mm.",
    "2. PRESTRESSING: POST-TENSIONING SLAB DESIGN AND SYSTEM SHALL BE BONDED.",
    "    STRAND 12.7 mm NOMINAL DIA., 7-WIRE, STRESS RELIEVED, LOW RELAXATION TO ASTM A416.",
    "3. REINFORCEMENT: DIA. 12 mm AND LARGER = DEFORMED BARS GRADE SD40, fy = 400 MPa.",
    "    DIA. 9 mm AND 6 mm = ROUND BARS GRADE SR24, fy = 240 MPa.",
    "    TOP REINFORCEMENT NOT TO BE INSTALLED UNTIL AFTER TENDONS HAVE BEEN PLACED.",
    "4. SUPPORT SCAFFOLD UNTIL THE CONCRETE HAS THE COMPRESSIVE STRENGTH AS DESIGNED (SOURCE SHEET 15).",
]
REDRAFT_NOTES = [
    "REDRAFT NOTES:",
    "A. REDRAFT FOR REVIEW ONLY - NOT FOR CONSTRUCTION. SOURCE: SUCCESS DESIGN & BUILD CO., LTD, SHEETS 14-16 OF 50, REV 01, 22-AUG-2023.",
    "B. SLAB, WALL, VOID, COLUMN, DROP PANEL AND TENDON GEOMETRY TAKEN FROM THE SOURCE VECTOR DATA (+/-0.3 m). NO DESIGN CHANGE.",
    "C. TENDON MARKS, GROUP NO., STRAND NOS. AND LENGTHS WERE READ FROM THE SOURCE LABELS AND ARE TRANSCRIBED - VERIFY.",
    "D. STRAND COUNT BY SYMBOL: SQUARE = 4, TRIANGLE = 3, CIRCLE = 2 STRANDS. STRESSING / DEAD-END SYMBOLS NOT REDRAWN - TBC.",
    "E. NOT REDRAWN: STAIR TREADS, REINFORCEMENT TABLES, TENDON PROFILES (SOURCE SHEET 16), TYPICAL DETAILS. JACKING FORCE AND LOSSES: TBC.",
    "F. B/O = BLOCKED OUT FOR STRESSING 0.80 m WIDE (SOURCE TEXT SAYS '0.80 CM' - LIKELY TYPO, TBC). HATCHED ON PLAN.",
    "G. DP = DROP PANEL 0.45 M.THK. (3000 x 3100 TYPICAL AT COLUMN LINE D). BB1 / BB2 = BAND BEAM 1 / 2, 0.45 M.THK. CYAN OUTLINES (S-CONC-DROP).",
    "H. COLUMN SIZES FROM SOURCE VECTOR DATA: C1 600 x 600, C3 800 x 800, C4 1100 x 1100 mm. SLAB 0.25 M.THK. (PTS) EXCEPT DP / BB.",
]


# ---------------------------------------------------------------- helpers
_BASE_LOAD = c.load_layers


def layers_with_extensions(standards: pathlib.Path) -> dict:
    L = _BASE_LOAD(standards)
    p = standards / "05_Drafting-Styles" / "05-04c_Layer_Extensions_PROPOSED.csv"
    with open(p, newline="", encoding="utf-8-sig") as fh:
        for r in csv.DictReader(fh):
            lw = r["Lineweight"].strip()
            L[r["Layer Name"].strip()] = {"color": int(r["Colour"]), "linetype": c.LINETYPE_MAP.get(r["Linetype"].strip(), r["Linetype"].strip().upper()),
                                          "lineweight": int(round(float(lw) * 100)), "plot": r["Plot"].strip().lower() == "yes",
                                          "description": r["Description"].strip(), "status": "proposed"}
    return L


def txt(msp, s, x, y, style="TEXT_2.0", layer="S-ANNO-TEXT", align=A.LEFT, rot=0.0):
    e = bs.txt(msp, s, x, y, style, layer, align)
    if rot:
        e.dxf.rotation = rot
    return e


def poly(msp, pts, layer, closed=False):
    return msp.add_lwpolyline([(PX(x), PY(y)) for x, y in pts], close=closed, dxfattribs={"layer": layer})


def ln(msp, p1, p2, layer):
    return msp.add_line(p1, p2, dxfattribs={"layer": layer})


def arrow(msp, tip, direction, layer="S-ANNO-DIMS", size=2.5, width=0.8):
    dx, dy = direction
    n = math.hypot(dx, dy)
    dx, dy = dx / n, dy / n
    bx, by = tip[0] - dx * size, tip[1] - dy * size
    px, py = -dy * width / 2, dx * width / 2
    msp.add_solid([tip, (bx + px, by + py), (bx - px, by - py), (bx - px, by - py)], dxfattribs={"layer": layer})


def symbol(msp, x, y, strands, layer="S-PT-TENDON", s=1.6):
    """Strand-count symbol: square = 4, triangle = 3, circle = 2 (source legend). Paper mm, centred at x, y."""
    if strands == 4:
        msp.add_lwpolyline([(x - s / 2, y - s / 2), (x + s / 2, y - s / 2), (x + s / 2, y + s / 2), (x - s / 2, y + s / 2)], close=True, dxfattribs={"layer": layer})
    elif strands == 3:
        msp.add_lwpolyline([(x - s / 2, y - s / 2), (x + s / 2, y - s / 2), (x, y + s / 2)], close=True, dxfattribs={"layer": layer})
    else:
        msp.add_circle((x, y), s / 2, dxfattribs={"layer": layer})


def dim_h(msp, y, xs_model, labels, ytxt_off=1.0):
    """Horizontal chain dimension at paper y between model x positions."""
    xs = [PX(x) for x in xs_model]
    ln(msp, (xs[0], y), (xs[-1], y), "S-ANNO-DIMS")
    for x in xs:
        ln(msp, (x, y - 1.5), (x, y + 1.5), "S-ANNO-DIMS")
    for a, b, lab in zip(xs, xs[1:], labels):
        arrow(msp, (a, y), (-1, 0)), arrow(msp, (b, y), (1, 0))
        txt(msp, lab, (a + b) / 2, y + ytxt_off, "TEXT_2.0", "S-ANNO-DIMS", A.BOTTOM_CENTER)


def dim_v(msp, x, ys_model, labels):
    ys = [PY(y) for y in ys_model]
    ln(msp, (x, ys[0]), (x, ys[-1]), "S-ANNO-DIMS")
    for y in ys:
        ln(msp, (x - 1.5, y), (x + 1.5, y), "S-ANNO-DIMS")
    for a, b, lab in zip(ys, ys[1:], labels):
        arrow(msp, (x, a), (0, -1)), arrow(msp, (x, b), (0, 1))
        txt(msp, lab, x - 1.0, (a + b) / 2, "TEXT_2.0", "S-ANNO-DIMS", A.BOTTOM_CENTER, rot=90)


def bubble(msp, x, y, label):
    msp.add_circle((x, y), 4.0, dxfattribs={"layer": "S-ANNO-LEADER"})
    txt(msp, label, x, y, "TEXT_3.5", "S-ANNO-TEXT", A.MIDDLE_CENTER)


def hatch_rect(msp, x0, y0, x1, y1, pattern="ANSI31", scale=1.2):
    h = msp.add_hatch(dxfattribs={"layer": "S-HATCH-CONC"})
    h.set_pattern_fill(pattern, color=256, scale=scale, angle=0)
    h.paths.add_polyline_path([(PX(x0), PY(y0)), (PX(x1), PY(y0)), (PX(x1), PY(y1)), (PX(x0), PY(y1))], is_closed=True)
    msp.add_lwpolyline([(PX(x0), PY(y0)), (PX(x1), PY(y0)), (PX(x1), PY(y1)), (PX(x0), PY(y1))], close=True, dxfattribs={"layer": "S-DETAIL-THIN"})


def cluster_boxes(lines, gap=250.0):
    boxes = []
    for pts in lines:
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        b = [min(xs), min(ys), max(xs), max(ys)]
        merged = True
        while merged:
            merged = False
            for o in boxes:
                if b[0] - gap <= o[2] and o[0] - gap <= b[2] and b[1] - gap <= o[3] and o[1] - gap <= b[3]:
                    b = [min(b[0], o[0]), min(b[1], o[1]), max(b[2], o[2]), max(b[3], o[3])]
                    boxes.remove(o); merged = True; break
        boxes.append(b)
    return boxes


# ---------------------------------------------------------------- build
def build(plan: dict, standards: pathlib.Path, out: pathlib.Path):
    layers = layers_with_extensions(standards)
    doc = bs.new_doc(layers)
    bs.define_titleblock(doc)
    msp = doc.modelspace()
    bs.place_titleblock(msp, {
        "PROJ_REFERENCE": "TBC", "DRAWING_NAME": "2F PT LAYOUT PLAN (REDRAFT)", "REVISION": "TBC", "DRAWN_BY": "CLAUDE (DRAFT)",
        "DRAWING_NUMBER": "TBC", "DRAWING_STAGE": "REDRAFT FOR REVIEW", "CLIENT": "TBC", "SCALE": "1:200", "ISSUE_DATE": "16-OCT-2026"})

    # titles
    txt(msp, "2F POST-TENSION LAYOUT PLAN (REDRAFT)  -  LEVEL +3.100", 12, 257.5, "TEXT_3.5")
    txt(msp, "SCALE 1:200  |  NET AREA = 829.05 SQ.M. (AS SOURCE)  |  REDRAFT FOR REVIEW - NOT FOR CONSTRUCTION", 12, 252.0, "TEXT_2.0")

    # grid lines (centre) + bubbles
    gx0, gx1 = PX(-1500), PX(47000 + 1500)
    for n, gx in enumerate(GRID_X, 1):
        ln(msp, (PX(gx), PY(0) - 17), (PX(gx), PY(24300) + 4), "S-GRID")
        bubble(msp, PX(gx), PY(0) - 36 - 0, str(n))
        ln(msp, (PX(gx), PY(0) - 32), (PX(gx), PY(0) - 17), "S-GRID")
    for name, gy in GRID_Y.items():
        ln(msp, (gx0, PY(gy)), (PX(47000 + 1500), PY(gy)), "S-GRID")
        ln(msp, (14.0 + 4, PY(gy)), (26.0, PY(gy)), "S-ANNO-LEADER")
        bubble(msp, 14.0, PY(gy), name)

    # slab / walls / voids (red outlines)
    for pts, cl in plan["red"]:
        poly(msp, pts, "S-CONC-OUTLINE", cl)
    # drop panels and thickened bands (cyan outlines)
    for pts, cl in plan["cyan"]:
        poly(msp, pts, "S-CONC-DROP", cl)
    # block-out strips (hatch lines clustered into rectangles)
    boxes = [b for b in cluster_boxes(plan["redhatch"]) if (b[2] - b[0]) > 300 and (b[3] - b[1]) > 300]
    for b in boxes:
        hatch_rect(msp, *b)
    # columns
    for tag, size, pts in COLUMNS:
        h = size / 2
        for (x, y) in pts:
            msp.add_lwpolyline([(PX(x - h), PY(y - h)), (PX(x + h), PY(y - h)), (PX(x + h), PY(y + h)), (PX(x - h), PY(y + h))], close=True,
                               dxfattribs={"layer": "S-CONC-OUTLINE"})
            ht = msp.add_hatch(dxfattribs={"layer": "S-HATCH-CONC"})
            ht.set_pattern_fill("SOLID", color=256)
            ht.paths.add_polyline_path([(PX(x - h), PY(y - h)), (PX(x + h), PY(y - h)), (PX(x + h), PY(y + h)), (PX(x - h), PY(y + h))], is_closed=True)
    # lift shafts: crosses
    lifts = [pts for pts, cl in plan["red"] if cl and len(pts) in (4, 5) and 21000 < min(p[1] for p in pts) and max(p[1] for p in pts) < 24500
             and 1500 < (max(p[0] for p in pts) - min(p[0] for p in pts)) < 3000]
    lifts.sort(key=lambda p: min(q[0] for q in p))
    for i, pts in enumerate(lifts[:4]):
        x0, x1 = min(q[0] for q in pts), max(q[0] for q in pts); y0, y1 = min(q[1] for q in pts), max(q[1] for q in pts)
        ln(msp, (PX(x0), PY(y0)), (PX(x1), PY(y1)), "S-DETAIL-THIN"); ln(msp, (PX(x0), PY(y1)), (PX(x1), PY(y0)), "S-DETAIL-THIN")
        txt(msp, LIFTS[i], PX((x0 + x1) / 2), PY(y1) - 3.0, "TEXT_2.0", "S-ANNO-TEXT", A.MIDDLE_CENTER)
    stairs = [pts for pts, cl in plan["red"] if cl and len(pts) in (4, 5) and 21000 < min(p[1] for p in pts) and max(p[1] for p in pts) < 24500
              and 3000 <= (max(p[0] for p in pts) - min(p[0] for p in pts)) < 8000]
    stairs.sort(key=lambda p: min(q[0] for q in p))
    for i, pts in enumerate(stairs[:2]):
        x0, x1 = min(q[0] for q in pts), max(q[0] for q in pts); y0, y1 = min(q[1] for q in pts), max(q[1] for q in pts)
        txt(msp, f"ST-{i + 1}", PX((x0 + x1) / 2), PY((y0 + y1) / 2), "TEXT_2.0", "S-ANNO-TEXT", A.MIDDLE_CENTER)

    # tendons: source geometry (lines + curved jogs); Y label stubs (below slab) dropped, tags drawn below
    for pts, t in plan["green"]:
        ys = [p[1] for p in pts]
        if max(ys) < 3000:
            continue
        poly(msp, pts, "S-PT-TENDON", False)

    # Y tendon tags below the slab
    verts = []
    for pts, t in plan["green"]:
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        if max(xs) - min(xs) < 30 and max(ys) - min(ys) > 7000:
            verts.append((sum(xs) / len(xs), min(ys)))
    verts.sort()
    assert len(verts) == len(Y_TENDONS), (len(verts), len(Y_TENDONS))
    desired = [PX(x) for x, _ in verts]
    pos = list(desired)
    for _ in range(400):                      # fan-out: keep tag pitch >= 3.2 mm, move neighbours apart symmetrically
        moved = False
        for i in range(len(pos) - 1):
            gap = pos[i + 1] - pos[i]
            if gap < 3.2:
                d = (3.2 - gap) / 2
                pos[i] -= d; pos[i + 1] += d; moved = True
        if not moved:
            break
    y_sym = PY(3300) - 3.0
    for (x, ybot), (g, mark, n, a, b, L), px, pp in zip(verts, Y_TENDONS, desired, pos):
        yb = PY(ybot)
        if abs(pp - px) > 0.2:
            ln(msp, (px, yb), (px, yb - 1.2), "S-ANNO-LEADER"); ln(msp, (px, yb - 1.2), (pp, y_sym + 1.2), "S-ANNO-LEADER")
        else:
            ln(msp, (px, yb), (pp, y_sym + 1.2), "S-ANNO-LEADER")
        symbol(msp, pp, y_sym, n)
        txt(msp, f"{mark} G{g}", pp + 1.0, y_sym - 1.4, "TEXT_2.0", "S-ANNO-TEXT", A.RIGHT, rot=90)

    # X / EX tendon labels in left and right columns (fan-out leaders)
    def stack(items, side):
        items = sorted(items, key=lambda t: -t[6])
        ys = [PY(t[6]) for t in items]
        pos = []
        for i, y in enumerate(ys):
            pos.append(y if i == 0 else min(y, pos[-1] - 3.2))
        # shift back up if drifted far from target (keep centred)
        drift = (sum(pos) - sum(ys)) / len(pos)
        pos = [p - drift * 0.0 for p in pos]
        return items, ys, pos

    for side in ("L", "R"):
        items = [t for t in X_TENDONS if t[7] == side]
        items, ys, pos = stack(items, side)
        for (g, mark, n, a, b, L, ym, _), y, p in zip(items, ys, pos):
            if side == "L":
                xe = PX(-600)
                ln(msp, (xe, y), (xe - 3.0, y), "S-ANNO-LEADER"); ln(msp, (xe - 3.0, y), (xe - 6.0, p), "S-ANNO-LEADER")
                symbol(msp, xe - 7.2, p, n)
                txt(msp, f"{mark} G{g} {a}-{b}", xe - 8.6, p, "TEXT_2.0", "S-ANNO-TEXT", A.MIDDLE_RIGHT)
            else:
                xe = PX(47600)
                ln(msp, (xe, y), (xe + 3.0, y), "S-ANNO-LEADER"); ln(msp, (xe + 3.0, y), (xe + 6.0, p), "S-ANNO-LEADER")
                symbol(msp, xe + 7.2, p, n)
                txt(msp, f"{mark} G{g} {a}-{b}", xe + 8.6, p, "TEXT_2.0", "S-ANNO-TEXT", A.MIDDLE_LEFT)

    # plan notes (source)
    for x, y in ((24000, 17600), (5300, 10400), (42700, 10400)):
        for k, line in enumerate(["PTS. 0.25 M.THK.", "SDL=250 KSM.", "LL=500 KSM."]):
            txt(msp, line, PX(x), PY(y) - k * 3.0, "TEXT_2.0", "S-ANNO-TEXT", A.MIDDLE_CENTER)
    for pts, cl in plan["cyan"]:
        if not cl:
            continue
        x0, x1 = min(p[0] for p in pts), max(p[0] for p in pts); y0, y1 = min(p[1] for p in pts), max(p[1] for p in pts)
        w, h = x1 - x0, y1 - y0
        if w > 9000:
            txt(msp, "BB2", PX((x0 + x1) / 2), PY(y0) + 2.0, "TEXT_2.0", "S-ANNO-TEXT", A.MIDDLE_CENTER)
        elif h > 5000 and w < 2500:
            txt(msp, "BB1", PX((x0 + x1) / 2), PY((y0 + y1) / 2) , "TEXT_2.0", "S-ANNO-TEXT", A.MIDDLE_CENTER, rot=90)
        else:
            txt(msp, "DP", PX(x0) + 1.2, (PY(y0) + 1.2) if y1 > 22000 else (PY(y1) - 3.0), "TEXT_2.0", "S-ANNO-TEXT", A.LEFT)
    for tag, size, pts in COLUMNS:
        for (x, y) in pts:
            if tag == "C1" and y in (24300,):
                continue
            txt(msp, tag, PX(x) + size / 2 / SC + 0.6, PY(y) + size / 2 / SC + 0.4, "TEXT_2.0", "S-ANNO-TEXT", A.LEFT)
    # level mark
    lx, ly = PX(23000), PY(12500)
    msp.add_lwpolyline([(lx - 1.5, ly + 2.6), (lx + 1.5, ly + 2.6), (lx, ly)], close=True, dxfattribs={"layer": "S-ANNO-LEADER"})
    ln(msp, (lx + 1.5, ly + 2.6), (lx + 9.0, ly + 2.6), "S-ANNO-LEADER")
    txt(msp, "+3.100", lx + 2.5, ly + 3.2, "TEXT_2.0", "S-ANNO-TEXT", A.LEFT)
    # block-out tags
    for bx in boxes:
        wide = (bx[2] - bx[0]) > (bx[3] - bx[1])
        txt(msp, "B/O", PX((bx[0] + bx[2]) / 2) + (0.0 if wide else 3.2), PY((bx[1] + bx[3]) / 2) + (-3.0 if wide else 0.0), "TEXT_2.0", "S-ANNO-TEXT", A.MIDDLE_CENTER,
            rot=0 if wide else 90)

    # dimensions
    yd = PY(0) - 22.0
    dim_h(msp, PY(0) - 22.0 - 0.0, GRID_X, ["10000", "9000", "9000", "9000", "10000"])
    dim_h(msp, PY(0) - 28.0, [0, 47000], ["47000"])
    dim_v(msp, 26.0, [0, 4300, 6300, 14800, 19800, 24300], ["4300", "2000", "8500", "5000", "4500"])
    # typical drop-panel dimensions (measured from source vector data)
    dim_h(msp, PY(16404) + 2.0, [8498, 11500], ["3000"])
    dim_v(msp, PX(11500) + 3.0, [13302, 16404], ["3100"])

    # ---- tendon schedule (right strip)
    x0 = 334.0
    cols = [x0, x0 + 9.5, x0 + 22.0, x0 + 30.5, x0 + 52.0, x0 + 75.0]   # group | mark | strands | strand nos | length
    top = 258.0
    rh = 3.35
    rows = [("G", "MARK", "STR.", "STRAND NOS.", "LENGTH (m)")]
    sec = []
    xl = sorted(X_TENDONS, key=lambda t: t[0])
    body = [("X / EX DIRECTION", None)] + [((g, m, n, f"{a}-{b}", f"{L:.2f}"), None) for (g, m, n, a, b, L, _, _s) in xl]
    body += [("Y DIRECTION", None)] + [((g, m, n, f"{a}-{b}", f"{L:.2f}"), None) for (g, m, n, a, b, L) in Y_TENDONS]
    txt(msp, "POST-TENSION TENDON SCHEDULE", x0, top + 2.5, "TEXT_2.5", "S-ANNO-TEXT")
    txt(msp, f"({CHECK_NOTE})", x0, top - 0.5, "TEXT_2.0", "S-ANNO-TEXT")
    ytab = top - 4.0
    heads = ["GRP", "MARK", "STR", "STRAND NOS.", "LENGTH m"]
    nrows = 1 + len(body)
    ybot = ytab - rh * nrows
    for i in range(nrows + 1):
        ln(msp, (x0 - 1.0, ytab - rh * i), (cols[-1] + 1.0, ytab - rh * i), "S-ANNO-TABLE")
    for xx in [x0 - 1.0] + cols[1:5] + [cols[-1] + 1.0]:
        ln(msp, (xx - (0.0 if xx != x0 - 1.0 else 0.0), ytab), (xx, ybot), "S-ANNO-TABLE")
    cx = [x0, cols[1], cols[2], cols[3], cols[4]]
    for xx, h in zip(cx, heads):
        txt(msp, h, xx + 0.8, ytab - rh / 2, "TEXT_2.0", "S-ANNO-TEXT", A.MIDDLE_LEFT)
    for i, (r, _) in enumerate(body, 1):
        yc = ytab - rh * (i + 0.5)
        if isinstance(r, str):
            txt(msp, r, cx[0] + 0.8, yc, "TEXT_2.0", "S-ANNO-TEXT", A.MIDDLE_LEFT)
        else:
            vals = [str(r[0]), r[1], str(r[2]), r[3], r[4]]
            for xx, v in zip(cx, vals):
                txt(msp, v, xx + 0.8, yc, "TEXT_2.0", "S-ANNO-TEXT", A.MIDDLE_LEFT)
    # legend under table
    ky = ybot - 5.0
    txt(msp, "STR: 4 = SQUARE, 3 = TRIANGLE, 2 = CIRCLE", x0, ky, "TEXT_2.0", "S-ANNO-TEXT")
    txt(msp, "LABEL LENGTH = DRAWN LENGTH + ~0.5 m (SOURCE)", x0, ky - 3.4, "TEXT_2.0", "S-ANNO-TEXT")

    # notes (bottom-left)
    ny = 82.0
    xn = 12.0
    for i, s in enumerate(REDRAFT_NOTES):
        txt(msp, s, xn, ny - 3.6 * i, "TEXT_2.0", "S-ANNO-TEXT")
    for i, s in enumerate(SOURCE_NOTES):
        txt(msp, s, xn, ny - 3.6 * (len(REDRAFT_NOTES) + 0.6 + i), "TEXT_2.0", "S-ANNO-TEXT")
    out.mkdir(parents=True, exist_ok=True)
    path = out / "2F_PT_Layout_Plan_REDRAFT.dxf"
    doc.saveas(path)
    return path


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", required=True)
    ap.add_argument("--standards", required=True)
    ap.add_argument("--out", required=True)
    ns = ap.parse_args(argv)
    plan = json.load(open(ns.plan))
    p = build(plan, pathlib.Path(ns.standards), pathlib.Path(ns.out))
    pdf = pathlib.Path(ns.out) / "2F_PT_Layout_Plan_REDRAFT_preview.pdf"
    bs.plot_pdf([p], pdf)
    print(json.dumps({"dxf": str(p), "preview_pdf": str(pdf)}, indent=2))


if __name__ == "__main__":
    main()
