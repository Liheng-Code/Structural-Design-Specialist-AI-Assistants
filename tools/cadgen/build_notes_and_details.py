#!/usr/bin/env python3
"""Generate reusable Eurocode General Notes (003-005) and Standard Details (006-007) as DXF + preview PDF,
and export standalone reusable CAD blocks and master sheet templates into Structural-Drawing-Standards/06_Templates/.

Usage:
  # Generate project sheets 003-007 from design_basis.yaml + document_register.csv (+ optional notes_overrides.yaml)
  python tools/cadgen/build_notes_and_details.py --design-basis <db.yaml> --register <reg.csv> \
      --standards Structural-Drawing-Standards --out <dir> [--overrides <notes_overrides.yaml>]

  # Export standalone reusable CAD blocks + template sheets to Structural-Drawing-Standards/06_Templates/
  python tools/cadgen/build_notes_and_details.py --export-templates --standards Structural-Drawing-Standards
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import pathlib
import re
import sys
import textwrap

import ezdxf
import yaml
from ezdxf.enums import TextEntityAlignment as A

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT))
import build_sheets as bs  # noqa: E402
import common as c  # noqa: E402
import validate_dxf as vd  # noqa: E402
from calc_lib.rc import ec2_anchorage as ec2  # noqa: E402

DEFAULT_LIB_PATH = ROOT / "Structural-Drawing-Standards" / "04_General-Notes-and-Details" / "04-02_Eurocode_General_Notes_Library.yaml"

# Line spacing for TEXT_2.0 (height 2.0 mm): 2.65 mm vertical step guarantees zero bbox overlap
LINE_DY = 2.65
NOTE_GAP = 0.55
SEC_GAP = 3.8


def load_library(standards_dir: pathlib.Path) -> dict:
    p = pathlib.Path(standards_dir) / "04_General-Notes-and-Details" / "04-02_Eurocode_General_Notes_Library.yaml"
    if not p.exists():
        p = DEFAULT_LIB_PATH
    with open(p, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def wrap_line(text: str, width_mm: float, char_w: float = 1.75) -> list[str]:
    """Wrap text so that rendered uppercase Arial 2.0 mm text fits within width_mm in ezdxf.bbox."""
    max_chars = max(8, int(width_mm / char_w))
    return textwrap.wrap(text.strip(), width=max_chars, break_long_words=False, break_on_hyphens=False) or [""]


def draw_section_heading(layout, title: str, x: float, y: float) -> float:
    """Draw a section heading in TEXT_2.5 and return the next y position below it."""
    bs.txt(layout, title, x, y, "TEXT_2.5", "S-ANNO-TEXT")
    return y - 4.8


def draw_numbered_notes(layout, notes: list[str], x: float, y: float, col_w: float, prefix_fmt: str = "{i}.") -> float:
    """Draw a numbered list of notes at (x, y) within width col_w, returning the new y cursor."""
    num_w = 5.5
    text_w = col_w - num_w - 2.0
    cur_y = y
    for i, note in enumerate(notes, start=1):
        label = prefix_fmt.format(i=i)
        lines = wrap_line(note, text_w)
        bs.txt(layout, label, x, cur_y, "TEXT_2.0", "S-ANNO-TEXT")
        for ln in lines:
            bs.txt(layout, ln, x + num_w, cur_y, "TEXT_2.0", "S-ANNO-TEXT")
            cur_y -= LINE_DY
        cur_y -= NOTE_GAP
    return cur_y


def draw_paragraph_lines(layout, lines_list: list[str], x: float, y: float, col_w: float) -> float:
    """Draw wrapped unnumbered paragraph lines at (x, y) within col_w, returning the new y cursor."""
    cur_y = y
    for para in lines_list:
        for ln in wrap_line(para, col_w - 2.0):
            bs.txt(layout, ln, x, cur_y, "TEXT_2.0", "S-ANNO-TEXT")
            cur_y -= LINE_DY
    return cur_y - NOTE_GAP


def draw_table(
    layout,
    x0: float,
    y_top: float,
    col_widths: list[float],
    headers: list[str],
    rows: list[list[str]],
    center_cols: set[int] | None = None,
    row_h: float = 4.6,
) -> float:
    """Draw a bordered table using S-ANNO-TABLE polylines and TEXT_2.0 cell text with zero overlap."""
    center_cols = center_cols or set()
    xs = [x0]
    for w in col_widths:
        xs.append(xs[-1] + w)

    # Pre-wrap every cell to determine row heights dynamically if any cell wraps to 2+ lines
    all_rows = [headers] + rows
    wrapped_rows: list[list[list[str]]] = []
    row_heights: list[float] = []
    for r_idx, r in enumerate(all_rows):
        w_cells = []
        max_lines = 1
        for c_idx, val in enumerate(r):
            s = str(val) if val is not None else ""
            if r_idx == 0 or c_idx in center_cols:
                w_cells.append([s])
            else:
                lines = wrap_line(s, col_widths[c_idx] - 2.4, char_w=1.72)
                w_cells.append(lines)
                max_lines = max(max_lines, len(lines))
        wrapped_rows.append(w_cells)
        row_heights.append(max(row_h, 1.8 + max_lines * LINE_DY))

    cur_y = y_top
    for r_idx, w_cells in enumerate(wrapped_rows):
        rh = row_heights[r_idx]
        y_bot = cur_y - rh
        for c_idx, lines in enumerate(w_cells):
            xa, xb = xs[c_idx], xs[c_idx + 1]
            layout.add_lwpolyline(
                [(xa, y_bot), (xb, y_bot), (xb, cur_y), (xa, cur_y)],
                close=True,
                dxfattribs={"layer": "S-ANNO-TABLE"},
            )
            if len(lines) == 1:
                ty = y_bot + (rh - 2.0) / 2.0
                if c_idx in center_cols:
                    bs.txt(layout, lines[0], (xa + xb) / 2.0, ty, "TEXT_2.0", "S-ANNO-TEXT", A.BOTTOM_CENTER)
                else:
                    bs.txt(layout, lines[0], xa + 1.2, ty, "TEXT_2.0", "S-ANNO-TEXT")
            else:
                top_baseline = cur_y - 2.7
                for l_i, ln in enumerate(lines):
                    ty = top_baseline - l_i * LINE_DY
                    bs.txt(layout, ln, xa + 1.2, ty, "TEXT_2.0", "S-ANNO-TEXT")
        cur_y = y_bot
    return cur_y - 1.2


def compute_ec2_anchorage_table(
    concrete_class: str = "C30/37",
    fyk: float = 390.0,
    bars: list[int] | None = None,
    fctk005_override: float | None = 2.03,
) -> dict:
    """Compute EN 1992-1-1 section 8.4 / 8.7 anchorage, lap and mandrel rows using calc_lib/rc/ec2_anchorage.py."""
    bars = bars or [10, 12, 16, 20, 25]
    sigma_sd = ec2.fyd(fyk)
    good_row, poor_row, lap_good_row, lap_poor_row, mandrel_row = [], [], [], [], []
    fbd_good = 0.0
    for phi in bars:
        b_good = ec2.bond_stress(concrete_class, True, phi, fctk005=fctk005_override)
        b_poor = ec2.bond_stress(concrete_class, False, phi, fctk005=fctk005_override)
        fbd_good = b_good.fbd
        l_good = ec2.lb_rqd(phi, sigma_sd, b_good.fbd)
        l_poor = ec2.lb_rqd(phi, sigma_sd, b_poor.fbd)
        # Round up to standard 5 mm bar detailing increment matching SD-004 convention
        g_mm = int(round(l_good / 5.0) * 5)
        p_mm = int(round(l_poor / 5.0) * 5)
        lg_mm = int(round((1.5 * g_mm) / 5.0) * 5)
        lp_mm = int(round((1.5 * p_mm) / 5.0) * 5)
        mandrel = int((4 if phi <= 16 else 7) * phi)
        good_row.append(str(g_mm))
        poor_row.append(str(p_mm))
        lap_good_row.append(str(lg_mm))
        lap_poor_row.append(str(lp_mm))
        mandrel_row.append(str(mandrel))
    return {
        "concrete_class": concrete_class,
        "fyk": int(fyk),
        "fbd_good": round(fbd_good, 2),
        "bars": [str(b) for b in bars],
        "good": good_row,
        "poor": poor_row,
        "lap_good": lap_good_row,
        "lap_poor": lap_poor_row,
        "mandrel": mandrel_row,
    }


def extract_db_materials(db: dict) -> dict[str, str]:
    """Extract material grades from design_basis.yaml without inventing values (missing -> TBC)."""
    mats = {m.get("id", ""): m.get("spec", "TBC") for m in (db.get("materials") or [])}
    rc_found = "TBC"
    rc_col = "TBC"
    rebar_fyk = "TBC"
    steel_main = "TBC"
    steel_bolts = "TBC"
    for m in db.get("materials") or []:
        spec = m.get("spec") or ""
        mid = m.get("id") or ""
        mc = re.search(r"C\d{2}/\d{2}", spec)
        if "PILE" in mid or "FOUND" in mid:
            if mc:
                rc_found = mc.group(0)
        if "STUMP" in mid or "COL" in mid:
            if mc:
                rc_col = mc.group(0)
        if "REBAR" in mid:
            mf = re.search(r"(\d{3})\s*MPa", spec)
            if mf:
                rebar_fyk = mf.group(1)
        if "STEEL" in mid:
            steel_main = spec
        if "BOLT" in mid:
            steel_bolts = spec
    if rc_found == "TBC" and rc_col != "TBC":
        rc_found = rc_col
    if rc_col == "TBC" and rc_found != "TBC":
        rc_col = rc_found
    return {
        "rc_foundation_class": rc_found,
        "rc_column_class": rc_col,
        "rc_slab_class": f"C25/30 MIN. ({rc_found} ADOPTED)" if rc_found != "TBC" else "TBC",
        "rebar_fyk": rebar_fyk,
        "anchor_bolt_spec": f"DB24 (GRADE {rebar_fyk}) THREADED, HDG" if rebar_fyk != "TBC" else "TBC",
        "steel_main_spec": steel_main.split("(")[0].strip() + " (EN 10025-2)" if "EN 10025" in steel_main else steel_main,
        "steel_bolts_spec": steel_bolts,
    }


# ==============================================================================
# Reusable CAD Detail Drawing Functions (for Sheet 006 / 007 and 06_Templates/blocks)
# ==============================================================================

def draw_ec2_bends_and_hooks(layout, ox: float = 0.0, oy: float = 0.0, lib: dict | None = None):
    """Draw Detail 1: Standard Bends and Hooks (EN 1992-1-1 8.3, EN 13670) + Mandrel Table."""
    bs.txt(layout, "1  STANDARD BENDS AND HOOKS (EN 1992-1-1 8.3, EN 13670)", ox + 20.0, oy + 251.0, "TEXT_2.5", "S-ANNO-TEXT")
    bs.txt(layout, "90 deg BEND: 10 phi", ox + 22.0, oy + 218.0, "TEXT_2.0", "S-ANNO-TEXT")
    bs.txt(layout, "135 deg HOOK: 10 phi", ox + 85.0, oy + 218.0, "TEXT_2.0", "S-ANNO-TEXT")
    bs.txt(layout, "180 deg HOOK: 5 phi", ox + 150.0, oy + 218.0, "TEXT_2.0", "S-ANNO-TEXT")
    bs.txt(layout, "CLOSED LINK", ox + 215.0, oy + 218.0, "TEXT_2.0", "S-ANNO-TEXT")
    bs.txt(layout, "MANDREL", ox + 64.0, oy + 203.0, "TEXT_2.0", "S-ANNO-TEXT")
    bs.txt(layout, "ALTERNATE HOOKS", ox + 215.0, oy + 183.0, "TEXT_2.0", "S-ANNO-TEXT")

    # 90 deg bend
    layout.add_lwpolyline([(ox + 20.0, oy + 215.0), (ox + 60.0, oy + 215.0), (ox + 60.0, oy + 190.0)], dxfattribs={"layer": "S-REBAR"})
    arc90 = [
        (60.0, 211.0), (60.0, 211.5), (59.9, 212.0), (59.7, 212.5), (59.5, 213.0),
        (59.2, 213.4), (58.8, 213.8), (58.4, 214.2), (58.0, 214.5), (57.5, 214.7),
        (57.0, 214.9), (56.5, 215.0), (56.0, 215.0),
    ]
    layout.add_lwpolyline([(ox + x, oy + y) for x, y in arc90], dxfattribs={"layer": "S-REBAR"})

    # 135 deg hook
    layout.add_lwpolyline([(ox + 85.0, oy + 215.0), (ox + 120.0, oy + 215.0), (ox + 120.0, oy + 190.0)], dxfattribs={"layer": "S-REBAR"})
    bs.line(layout, (ox + 120.0, oy + 190.0), (ox + 113.0, oy + 193.0), "S-REBAR")

    # 180 deg hook
    layout.add_lwpolyline([(ox + 150.0, oy + 215.0), (ox + 185.0, oy + 215.0)], dxfattribs={"layer": "S-REBAR"})
    arc180 = [
        (185.0, 215.0), (186.3, 214.8), (187.5, 214.3), (188.5, 213.5), (189.3, 212.5),
        (189.8, 211.3), (190.0, 210.0), (189.8, 208.7), (189.3, 207.5), (188.5, 206.5),
        (187.5, 205.7), (186.3, 205.2), (185.0, 205.0),
    ]
    layout.add_lwpolyline([(ox + x, oy + y) for x, y in arc180], dxfattribs={"layer": "S-REBAR"})
    bs.line(layout, (ox + 185.0, oy + 205.0), (ox + 160.0, oy + 205.0), "S-REBAR")

    # Closed link with 135 deg hook
    layout.add_lwpolyline(
        [(ox + 215.0, oy + 187.0), (ox + 241.0, oy + 187.0), (ox + 241.0, oy + 213.0), (ox + 215.0, oy + 213.0)],
        close=True,
        dxfattribs={"layer": "S-REBAR"},
    )
    bs.line(layout, (ox + 241.0, oy + 213.0), (ox + 233.0, oy + 205.0), "S-REBAR")

    # Mandrel schedule table
    mt = (lib or {}).get("sheet_006", {}).get("mandrel_table") or {
        "headers": ["BAR phi (mm)", "MIN. MANDREL (HOOKS/BENDS)", "LINKS (phi <= 16)", "BEND FOR LAPS (phi > 16)"],
        "rows": [["8 - 16", "4 phi", "4 phi", "-"], ["20", "7 phi", "-", "7 phi"], ["25", "7 phi", "-", "7 phi"], ["32", "7 phi", "-", "7 phi"]],
    }
    draw_table(layout, ox + 20.0, oy + 180.0, [28.0, 62.0, 42.0, 52.0], mt["headers"], mt["rows"], center_cols={0, 1, 2, 3}, row_h=5.2)


def draw_ec2_lap_splice(layout, ox: float = 0.0, oy: float = 0.0):
    """Draw Detail 2: Lap Splice (Tension) and Anchorage (EN 1992-1-1 8.7)."""
    bs.txt(layout, "2  LAP SPLICE (TENSION) AND ANCHORAGE", ox + 20.0, oy + 141.0, "TEXT_2.5", "S-ANNO-TEXT")
    bs.line(layout, (ox + 20.0, oy + 125.0), (ox + 95.0, oy + 125.0), "S-REBAR")
    bs.line(layout, (ox + 60.0, oy + 121.0), (ox + 135.0, oy + 121.0), "S-REBAR")
    bs.line(layout, (ox + 60.0, oy + 122.0), (ox + 60.0, oy + 111.8), "S-ANNO-DIMS")
    bs.line(layout, (ox + 95.0, oy + 122.0), (ox + 95.0, oy + 111.8), "S-ANNO-DIMS")
    bs.line(layout, (ox + 60.0, oy + 113.0), (ox + 95.0, oy + 113.0), "S-ANNO-DIMS")
    bs.line(layout, (ox + 59.1, oy + 112.1), (ox + 60.9, oy + 113.9), "S-ANNO-DIMS")
    bs.line(layout, (ox + 94.1, oy + 112.1), (ox + 95.9, oy + 113.9), "S-ANNO-DIMS")
    bs.txt(layout, "l0 (LAP)", ox + 77.5, oy + 114.2, "TEXT_2.5", "S-ANNO-DIMS", A.BOTTOM_CENTER)
    bs.txt(
        layout,
        "l0 = alpha6 lbd >= l0,min = max(0.3 alpha6 lb,rqd ; 15 phi ; 200 mm). TRANSVERSE SPACING <= 4 phi OR 50 mm.",
        ox + 20.0,
        oy + 103.0,
        "TEXT_2.0",
        "S-ANNO-TEXT",
    )
    bs.txt(
        layout,
        "LAP LENGTHS: SEE SD-004 TABLE C. NO LAPS WITHIN 2 x h OF BEAM / COLUMN INTERFACES.",
        ox + 20.0,
        oy + 98.0,
        "TEXT_2.0",
        "S-ANNO-TEXT",
    )


def draw_ec2_corner_detail(layout, ox: float = 0.0, oy: float = 0.0, db16_lap_mm: str = "670"):
    """Draw Detail 3: Typical Beam / Wall Corner L-Bar Detail (Plan)."""
    bs.txt(layout, "3  TYPICAL CORNER DETAIL - GB1 / BB1 (PLAN)", ox + 150.0, oy + 86.0, "TEXT_2.5", "S-ANNO-TEXT")
    layout.add_lwpolyline([(ox + 150.0, oy + 72.0), (ox + 210.0, oy + 72.0), (ox + 210.0, oy + 32.0)], dxfattribs={"layer": "S-CONC-OUTLINE"})
    layout.add_lwpolyline([(ox + 156.0, oy + 66.0), (ox + 204.0, oy + 66.0), (ox + 204.0, oy + 32.0)], dxfattribs={"layer": "S-CONC-OUTLINE"})
    layout.add_lwpolyline([(ox + 154.0, oy + 69.0), (ox + 207.0, oy + 69.0), (ox + 207.0, oy + 32.0)], dxfattribs={"layer": "S-REBAR"})
    bs.txt(layout, f"L-BARS (LAP {db16_lap_mm} FOR DB16)", ox + 214.0, oy + 54.0, "TEXT_2.0", "S-ANNO-TEXT")
    bs.txt(layout, "AT EVERY CORNER; LAP 50 phi", ox + 214.0, oy + 50.0, "TEXT_2.0", "S-ANNO-TEXT")


def draw_ec3_bolt_spacing_table(layout, ox: float = 0.0, oy: float = 0.0, lib: dict | None = None):
    """Draw Detail 1 on Sheet 007: Bolt Hole & Spacing Table (EN 1993-1-8 Table 3.3)."""
    bs.txt(layout, "1  BOLT HOLE & SPACING TABLE (EN 1993-1-8 T3.3)", ox + 14.0, oy + 258.0, "TEXT_2.5", "S-ANNO-TEXT")
    bt = (lib or {}).get("sheet_007", {}).get("bolt_table") or {
        "headers": ["BOLT", "d0 (HOLE)", "e1 (EDGE)", "p1 (PITCH)", "TIGHTENING", "NOTE"],
        "rows": [
            ["M12", "14", ">= 1.2 d0 = 17", ">= 2.2 d0 = 31", "SNUG", "SECONDARY"],
            ["M16", "18", ">= 22", ">= 40", "SNUG", "GIRT CLEATS"],
            ["M20", "22", ">= 27", ">= 49", "SNUG (8.8)", "BRACING, FIN PL"],
            ["M24", "26", ">= 31 (40 SPEC.)", ">= 57 (70 SPEC.)", "PRELOAD 10.9 (220 kN)", "PRIMARY JOINTS"],
        ],
    }
    draw_table(layout, ox + 14.0, oy + 254.0, [16.0, 22.0, 32.0, 32.0, 42.0, 34.0], bt["headers"], bt["rows"], center_cols={0, 1}, row_h=5.2)


def draw_ec3_weld_symbols(layout, ox: float = 0.0, oy: float = 0.0, lib: dict | None = None):
    """Draw Detail 2 on Sheet 007: Weld Symbols / Sizes Table with clean CAD vector symbols."""
    bs.txt(layout, "2  WELD SYMBOLS / SIZES", ox + 14.0, oy + 222.0, "TEXT_2.5", "S-ANNO-TEXT")
    wt = (lib or {}).get("sheet_007", {}).get("weld_table") or {
        "headers": ["SYMBOL", "DESCRIPTION", "TYPICAL USE"],
        "rows": [
            ["6 [FILLET]", "CONTINUOUS FILLET 6 mm (BOTH SIDES UNLESS NOTED)", "WEB-FLANGE (a = 4.2), STIFFENERS"],
            ["8 [FILLET]", "CONTINUOUS FILLET 8 mm", "BASE PL / COLUMN"],
            ["CJP", "COMPLETE-JOINT-PENETRATION BUTT", "FLANGE SPLICES, END PLATE TO FLANGE"],
            ["[ALL-ROUND]", "ALL-ROUND WELD", "GUSSET, FIN PL"],
            ["FW", "FIELD WELD (ONLY WITH APPROVAL)", "-"],
        ],
    }
    draw_table(layout, ox + 14.0, oy + 218.0, [26.0, 86.0, 66.0], wt["headers"], wt["rows"], center_cols={0}, row_h=5.2)


def draw_ec3_stiffener_finplate(layout, ox: float = 0.0, oy: float = 0.0):
    """Draw Detail 3 on Sheet 007: Typical Stiffener / Fin Plate (Schematic)."""
    bs.txt(layout, "3  TYPICAL STIFFENER / FIN PLATE (SCHEMATIC)", ox + 14.0, oy + 176.0, "TEXT_2.5", "S-ANNO-TEXT")
    # Column flanges & web with stiffener
    layout.add_lwpolyline(
        [(ox + 24.0, oy + 120.0), (ox + 64.0, oy + 120.0), (ox + 64.0, oy + 123.0), (ox + 24.0, oy + 123.0)],
        close=True,
        dxfattribs={"layer": "S-STEEL-OUTLINE"},
    )
    layout.add_lwpolyline(
        [(ox + 24.0, oy + 157.0), (ox + 64.0, oy + 157.0), (ox + 64.0, oy + 160.0), (ox + 24.0, oy + 160.0)],
        close=True,
        dxfattribs={"layer": "S-STEEL-OUTLINE"},
    )
    bs.line(layout, (ox + 44.0, oy + 123.0), (ox + 44.0, oy + 157.0), "S-STEEL-OUTLINE")
    layout.add_lwpolyline(
        [(ox + 43.5, oy + 123.0), (ox + 63.0, oy + 123.0), (ox + 63.0, oy + 157.0), (ox + 43.5, oy + 157.0)],
        close=True,
        dxfattribs={"layer": "S-STEEL-OUTLINE"},
    )
    bs.txt(layout, "STIFFENER PL12 (BOTH SIDES),", ox + 68.0, oy + 158.0, "TEXT_2.0", "S-ANNO-TEXT")
    bs.txt(layout, "CLIPPED 20 x 20 AT CORNERS;", ox + 68.0, oy + 154.0, "TEXT_2.0", "S-ANNO-TEXT")
    bs.txt(layout, "FILLET 6 mm TO WEB AND FLANGE", ox + 68.0, oy + 150.0, "TEXT_2.0", "S-ANNO-TEXT")

    # Fin plate connection
    layout.add_lwpolyline(
        [(ox + 132.0, oy + 120.0), (ox + 135.0, oy + 120.0), (ox + 135.0, oy + 160.0), (ox + 132.0, oy + 160.0)],
        close=True,
        dxfattribs={"layer": "S-STEEL-OUTLINE"},
    )
    layout.add_lwpolyline(
        [(ox + 135.0, oy + 128.0), (ox + 165.0, oy + 128.0), (ox + 165.0, oy + 152.0), (ox + 135.0, oy + 152.0)],
        close=True,
        dxfattribs={"layer": "S-STEEL-OUTLINE"},
    )
    layout.add_circle((ox + 145.0, oy + 136.0), radius=2.0, dxfattribs={"layer": "S-STEEL-OUTLINE"})
    layout.add_circle((ox + 145.0, oy + 144.0), radius=2.0, dxfattribs={"layer": "S-STEEL-OUTLINE"})
    bs.txt(layout, "FIN PL10, 2 x M20 (8.8),", ox + 14.0, oy + 112.0, "TEXT_2.0", "S-ANNO-TEXT")
    bs.txt(layout, "WELD 6 mm ALL ROUND TO FLANGE", ox + 14.0, oy + 108.0, "TEXT_2.0", "S-ANNO-TEXT")


# ==============================================================================
# Sheet Builders (003, 004, 005, 006, 007)
# ==============================================================================

def build_003(db: dict, row: dict, layers: dict, out: pathlib.Path, lib: dict, overrides: dict | None = None) -> pathlib.Path:
    """Build Sheet 003: General Notes - Part 01 (General, Design Basis & Loading)."""
    doc = bs.new_doc(layers)
    bs.define_titleblock(doc)
    msp = doc.modelspace()
    bs.place_titleblock(msp, bs.sheet_values(db, row, row["sheet_name"], "N.T.S."))

    ov = (overrides or {}).get("sheet_003") or {}
    s3 = lib["sheet_003"]
    col1_x, col1_w = 12.0, 186.0
    col2_x, col2_w = 208.0, 198.0

    # Left column: A. GENERAL, B. DESIGN CODES, C. DESIGN BASIS & ACTIONS
    y1 = 259.5
    y1 = draw_section_heading(msp, "A. GENERAL", col1_x, y1)
    if ov.get("general_notes"):
        gen_notes = ov["general_notes"]
    else:
        P = db.get("project") or {}
        g = db.get("geometry") or {}
        desc_note = (
            f"PROJECT DESCRIPTION: {P.get('description') or 'TBC'}. "
            f"SPAN = {g.get('span_m', 'TBC')} m, LENGTH = {g.get('length_m', 'TBC')} m, "
            f"EAVE = +{g.get('eave_level_m', 'TBC')} m, RIDGE = +{g.get('ridge_level_m', 'TBC')} m."
        )
        gen_notes = [s3["general_notes_standard"][0], s3["general_notes_standard"][1], desc_note] + s3["general_notes_standard"][2:]
    y1 = draw_numbered_notes(msp, gen_notes, col1_x, y1, col1_w) - 2.0

    # B. DESIGN CODES
    y1 = draw_section_heading(msp, "B. DESIGN CODES", col1_x, y1)
    code_rows = []
    for st in db.get("standards") or []:
        cid = st.get("id") or "TBC"
        ed = f" ({st['edition']})" if st.get("edition") else ""
        code_rows.append([cid + ed, (st.get("used_for") or "TBC").upper()])
    for sup in s3.get("default_codes_supplement") or []:
        code_rows.append([sup["code"], sup["scope"]])
    y1 = draw_table(msp, col1_x, y1 + 1.5, [62.0, 124.0], ["CODE", "SCOPE"], code_rows, row_h=4.6)
    na_note = ((db.get("national_annex") or {}).get("basis_note") or "NATIONAL ANNEX BASIS: TBC").upper()
    y1 = draw_paragraph_lines(msp, [na_note], col1_x, y1 - 2.0, col1_w) - 2.0

    # C. DESIGN BASIS & ACTIONS (placed in column 2 top if y1 is low, or column 1 if room)
    y2 = 259.5
    y2 = draw_section_heading(msp, "C. DESIGN BASIS & ACTIONS", col2_x, y2)
    if ov.get("actions_table"):
        act_rows = ov["actions_table"]
    else:
        da = db.get("design_assumptions") or {}
        dwl = f"{da['design_working_life_years']} YEARS" if da.get("design_working_life_years") else "TBC"
        cc = da.get("consequence_class") or "TBC"
        act_rows = [
            ["DESIGN WORKING LIFE", dwl, "EN 1990 T2.1"],
            ["CONSEQUENCE CLASS", str(cc), "EN 1990 B"],
        ]
        for ld in db.get("loads") or []:
            val = f"{ld['value']} {ld.get('unit') or ''}".strip() if ld.get("value") is not None else "TBC"
            act_rows.append([(ld.get("description") or "LOAD").upper(), val.upper(), (ld.get("source") or "TBC").upper()])
    y2 = draw_table(msp, col2_x, y2 + 1.5, [92.0, 52.0, 54.0], ["ACTION", "VALUE", "SOURCE"], act_rows, row_h=4.5) - 2.5

    # D. LOAD COMBINATIONS (EN 1990)
    y2 = draw_section_heading(msp, "D. LOAD COMBINATIONS (EN 1990)", col2_x, y2)
    comb_notes = ov.get("combinations_notes") or s3["combinations_standard"]
    y2 = draw_numbered_notes(msp, comb_notes, col2_x, y2, col2_w) - 2.0

    # E. DESIGN RESULTS SUMMARY & F. ASSUMPTIONS TO BE CONFIRMED
    # Place E under B in column 1, and F under D in column 2 so everything fits cleanly above y = 8 mm
    res_heading = ov.get("results_summary_heading") or "E. DESIGN RESULTS SUMMARY"
    y1 = draw_section_heading(msp, res_heading, col1_x, y1)
    res_rows = ov.get("results_summary_table") or [
        ["PRIMARY FRAME / MEMBER UTILISATION", "TBC", "<= 1.00"],
        ["SLS DEFLECTION / LATERAL SWAY", "TBC", "PER EN 1990"],
        ["FOUNDATION / PILE REACTIONS", "TBC", "PER EN 1997-1"],
    ]
    y1 = draw_table(msp, col1_x, y1 + 1.5, [86.0, 52.0, 48.0], ["ITEM", "RESULT", "LIMIT"], res_rows, row_h=4.5)

    y2 = draw_section_heading(msp, "F. ASSUMPTIONS TO BE CONFIRMED", col2_x, y2)
    open_items = db.get("open_items") or []
    if open_items:
        f_notes = [f"{item.get('description', 'TBC').upper()}" for item in open_items]
    else:
        f_notes = ["ALL PROJECT ASSUMPTIONS AND SITE PARAMETERS TO BE CONFIRMED BY THE ENGINEER PRIOR TO CONSTRUCTION ISSUE."]
    draw_numbered_notes(msp, f_notes, col2_x, y2, col2_w, prefix_fmt="F{i}.")

    p = out / f"{row['sheet_number']}_{row['revision']}.dxf"
    doc.saveas(p)
    return p


def build_004(db: dict, row: dict, layers: dict, out: pathlib.Path, lib: dict, overrides: dict | None = None) -> pathlib.Path:
    """Build Sheet 004: General Notes - Part 02 (Concrete & Reinforcement) with live EC2 anchorage calculation."""
    doc = bs.new_doc(layers)
    bs.define_titleblock(doc)
    msp = doc.modelspace()
    bs.place_titleblock(msp, bs.sheet_values(db, row, row["sheet_name"], "N.T.S."))

    ov = (overrides or {}).get("sheet_004") or {}
    s4 = lib["sheet_004"]
    mat_vars = extract_db_materials(db)

    col1_x, col1_w = 12.0, 186.0
    col2_x, col2_w = 208.0, 198.0

    # A. MATERIALS (CONCRETE & REINFORCEMENT)
    y1 = 259.5
    y1 = draw_section_heading(msp, "A. MATERIALS (CONCRETE & REINFORCEMENT)", col1_x, y1)
    raw_mats = ov.get("materials_table") or s4["default_materials_table"]
    mat_rows = []
    for m in raw_mats:
        mat_rows.append([
            m["element"].format(**mat_vars),
            m["class_en206"].format(**mat_vars),
            m["exposure"].format(**mat_vars),
            m["notes"].format(**mat_vars),
        ])
    y1 = draw_table(
        msp,
        col1_x,
        y1 + 1.5,
        [62.0, 56.0, 26.0, 42.0],
        ["ELEMENT", "CLASS (EN 206)", "EXPOSURE", "NOTES"],
        mat_rows,
        center_cols={2},
        row_h=4.8,
    )
    y1 = draw_paragraph_lines(msp, [s4["cement_note"]], col1_x, y1 - 1.5, col1_w) - 1.5

    # B. CONCRETE COVER (EN 1992-1-1 4.4)
    y1 = draw_section_heading(msp, "B. CONCRETE COVER (EN 1992-1-1 4.4)", col1_x, y1)
    cov_rows = [[r["element"], r["cnom"]] for r in (ov.get("cover_table") or s4["default_cover_table"])]
    y1 = draw_table(msp, col1_x, y1 + 1.5, [144.0, 42.0], ["ELEMENT", "Cnom (mm)"], cov_rows, center_cols={1}, row_h=4.6)
    y1 = draw_paragraph_lines(msp, [s4["cover_note"]], col1_x, y1 - 1.5, col1_w) - 1.5

    # C. ANCHORAGE & LAP LENGTHS (computed live from calc_lib/rc/ec2_anchorage.py)
    ac_cfg = (overrides or {}).get("anchorage_calc") or {}
    c_class = ac_cfg.get("concrete_class") or (mat_vars["rc_foundation_class"] if mat_vars["rc_foundation_class"] != "TBC" else "C30/37")
    fyk_val = float(ac_cfg.get("fyk") or (mat_vars["rebar_fyk"] if mat_vars["rebar_fyk"] != "TBC" else 390))
    fctk_ov = ac_cfg.get("fctk005_override", 2.03 if c_class == "C30/37" else None)
    anch = compute_ec2_anchorage_table(c_class, fyk_val, ac_cfg.get("bars"), fctk_ov)

    y1 = draw_section_heading(msp, f"C. ANCHORAGE & LAP LENGTHS ({anch['concrete_class']}, fyk = {anch['fyk']})", col1_x, y1)
    anch_headers = ["BAR phi (mm)"] + anch["bars"]
    anch_rows = [
        ["lbd GOOD BOND (mm)"] + anch["good"],
        ["lbd POOR BOND (mm)"] + anch["poor"],
        ["LAP l0 GOOD, <=50% LAPPED"] + anch["lap_good"],
        ["LAP l0 POOR, <=50% LAPPED"] + anch["lap_poor"],
        ["HOOK / BEND MIN. MANDREL (mm)"] + anch["mandrel"],
    ]
    y1 = draw_table(
        msp,
        col1_x,
        y1 + 1.5,
        [76.0, 22.0, 22.0, 22.0, 22.0, 22.0],
        anch_headers,
        anch_rows,
        center_cols={1, 2, 3, 4, 5},
        row_h=4.6,
    )
    anch_note = (
        f"lb,rqd = (phi/4)(sigma_sd / fbd) ; fbd = 2.25 eta1 eta2 fctd = {anch['fbd_good']:.2f} MPa (GOOD BOND). "
        "eta1 = 0.7 FOR POOR BOND (TOP BARS IN MEMBERS > 250 mm DEEP). alpha_6 = 1.5 (50% LAPPED). "
        "MANDRELS: 4 phi (phi <= 16), 7 phi (phi > 16)."
    )
    draw_paragraph_lines(msp, [anch_note], col1_x, y1 - 1.5, col1_w)

    # Column 2: D. REINFORCEMENT NOTES, E. CONCRETING & CURING, F. EARTHWORKS & GROUND SLAB, G. BRICKWORK
    y2 = 259.5
    y2 = draw_section_heading(msp, "D. REINFORCEMENT NOTES", col2_x, y2)
    r_notes = [n.format(**mat_vars) for n in (ov.get("reinforcement_notes") or s4["reinforcement_notes"])]
    y2 = draw_numbered_notes(msp, r_notes, col2_x, y2, col2_w) - 1.5

    y2 = draw_section_heading(msp, "E. CONCRETING & CURING", col2_x, y2)
    c_notes = ov.get("concreting_notes") or s4["concreting_notes"]
    y2 = draw_numbered_notes(msp, c_notes, col2_x, y2, col2_w) - 1.5

    y2 = draw_section_heading(msp, "F. EARTHWORKS & GROUND SLAB", col2_x, y2)
    e_notes = ov.get("earthworks_notes") or s4["earthworks_notes"]
    y2 = draw_numbered_notes(msp, e_notes, col2_x, y2, col2_w) - 1.5

    y2 = draw_section_heading(msp, "G. BRICKWORK", col2_x, y2)
    b_notes = ov.get("brickwork_notes") or s4["brickwork_notes"]
    draw_numbered_notes(msp, b_notes, col2_x, y2, col2_w)

    p = out / f"{row['sheet_number']}_{row['revision']}.dxf"
    doc.saveas(p)
    return p


def build_005(db: dict, row: dict, layers: dict, out: pathlib.Path, lib: dict, overrides: dict | None = None) -> pathlib.Path:
    """Build Sheet 005: General Notes - Part 03 (Structural Steelwork)."""
    doc = bs.new_doc(layers)
    bs.define_titleblock(doc)
    msp = doc.modelspace()
    bs.place_titleblock(msp, bs.sheet_values(db, row, row["sheet_name"], "N.T.S."))

    ov = (overrides or {}).get("sheet_005") or {}
    s5 = lib["sheet_005"]
    mat_vars = extract_db_materials(db)

    col1_x, col1_w = 12.0, 186.0
    col2_x, col2_w = 208.0, 198.0

    # Column 1: A. MATERIALS, B. SECTIONS ADOPTED, E. ERECTION
    y1 = 259.5
    y1 = draw_section_heading(msp, "A. MATERIALS", col1_x, y1)
    raw_mats = ov.get("materials_table") or s5["default_materials_table"]
    mat_rows = [[m["item"].format(**mat_vars), m["spec"].format(**mat_vars)] for m in raw_mats]
    y1 = draw_table(msp, col1_x, y1 + 1.5, [62.0, 124.0], ["ITEM", "SPECIFICATION"], mat_rows, row_h=5.0) - 2.0

    y1 = draw_section_heading(msp, "B. SECTIONS ADOPTED", col1_x, y1)
    sec_rows = ov.get("sections_table") or [
        ["COL", "STEEL COLUMN SECTION TBC", "PRIMARY COLUMN", "TBC"],
        ["RAF/BM", "STEEL RAFTER / BEAM TBC", "PRIMARY RAFTER / BEAM", "TBC"],
        ["P1 / G1", "COLD-FORMED PURLIN / GIRT TBC", "SECONDARY FRAMING", "-"],
        ["BR", "BRACING MEMBER TBC", "ROOF / WALL BRACING", "-"],
    ]
    y1 = draw_table(msp, col1_x, y1 + 1.5, [24.0, 82.0, 62.0, 18.0], ["MARK", "SECTION", "USE", "CLASS"], sec_rows, center_cols={3}, row_h=5.0) - 2.0

    y1 = draw_section_heading(msp, "E. ERECTION", col1_x, y1)
    er_notes = ov.get("erection_notes") or s5["erection_notes"]
    y1 = draw_numbered_notes(msp, er_notes, col1_x, y1, col1_w)

    # Column 2: C. FABRICATION & WELDING, D. CORROSION PROTECTION, F. CONNECTION DESIGN BASIS
    y2 = 259.5
    y2 = draw_section_heading(msp, "C. FABRICATION & WELDING", col2_x, y2)
    fab_notes = ov.get("fabrication_notes") or s5["fabrication_notes"]
    y2 = draw_numbered_notes(msp, fab_notes, col2_x, y2, col2_w) - 1.5

    y2 = draw_section_heading(msp, "D. CORROSION PROTECTION", col2_x, y2)
    cor_notes = ov.get("corrosion_notes") or s5["corrosion_notes"]
    y2 = draw_numbered_notes(msp, cor_notes, col2_x, y2, col2_w) - 1.5

    y2 = draw_section_heading(msp, "F. CONNECTION DESIGN BASIS", col2_x, y2)
    conn_notes = ov.get("connection_basis_notes") or [
        "BOLTED END-PLATE AND FIN-PLATE CONNECTIONS DESIGNED TO EN 1993-1-8. DETAILS SHOWN ON DRAWINGS ARE INDICATIVE AND SUBJECT TO FABRICATOR'S VERIFICATION AND ENGINEER'S APPROVAL."
    ]
    draw_paragraph_lines(msp, conn_notes, col2_x, y2, col2_w)

    p = out / f"{row['sheet_number']}_{row['revision']}.dxf"
    doc.saveas(p)
    return p


def build_006(db: dict, row: dict, layers: dict, out: pathlib.Path, lib: dict, overrides: dict | None = None) -> pathlib.Path:
    """Build Sheet 006: General Notes - Part 04 (RC Standard Details)."""
    doc = bs.new_doc(layers)
    bs.define_titleblock(doc)
    msp = doc.modelspace()
    bs.place_titleblock(msp, bs.sheet_values(db, row, row["sheet_name"], "N.T.S."))

    s6 = lib["sheet_006"]
    # Compute DB16 lap length dynamically from calc_lib/rc/ec2_anchorage.py (560 mm lbd / 670 mm lap for C30/37, fyk=390)
    ac_cfg = (overrides or {}).get("anchorage_calc") or {}
    mat_vars = extract_db_materials(db)
    c_class = ac_cfg.get("concrete_class") or (mat_vars["rc_foundation_class"] if mat_vars["rc_foundation_class"] != "TBC" else "C30/37")
    fyk_val = float(ac_cfg.get("fyk") or (mat_vars["rebar_fyk"] if mat_vars["rebar_fyk"] != "TBC" else 390))
    fctk_ov = ac_cfg.get("fctk005_override", 2.03 if c_class == "C30/37" else None)
    anch = compute_ec2_anchorage_table(c_class, fyk_val, [10, 12, 16, 20, 25], fctk_ov)
    db16_lbd = anch["good"][2]  # 445 or 560 for DB20; keep SD-006 note accurate

    draw_ec2_bends_and_hooks(msp, 0.0, 0.0, lib)
    draw_ec2_lap_splice(msp, 0.0, 0.0)
    draw_ec2_corner_detail(msp, 0.0, 0.0, db16_lap_mm=anch["good"][3])

    # Detail 4: Reinforcement Notation
    bs.txt(msp, "4  REINFORCEMENT NOTATION", 20.0, 42.0, "TEXT_2.5", "S-ANNO-TEXT")
    draw_paragraph_lines(msp, s6["notation_lines"], 20.0, 36.5, 240.0)

    # Right-hand RC Standard Notes column
    bs.txt(msp, "RC STANDARD NOTES", 275.0, 259.5, "TEXT_2.5", "S-ANNO-TEXT")
    bs.line(msp, (275.0, 255.3), (408.0, 255.3), "S-ANNO-TEXT")
    draw_numbered_notes(msp, s6["rc_standard_notes"], 275.0, 251.5, 133.0)

    p = out / f"{row['sheet_number']}_{row['revision']}.dxf"
    doc.saveas(p)
    return p


def build_007(db: dict, row: dict, layers: dict, out: pathlib.Path, lib: dict, overrides: dict | None = None) -> pathlib.Path:
    """Build Sheet 007: General Notes - Part 05 (Steel Standard Details)."""
    doc = bs.new_doc(layers)
    bs.define_titleblock(doc)
    msp = doc.modelspace()
    bs.place_titleblock(msp, bs.sheet_values(db, row, row["sheet_name"], "N.T.S."))

    s7 = lib["sheet_007"]
    draw_ec3_bolt_spacing_table(msp, 0.0, 0.0, lib)
    draw_ec3_weld_symbols(msp, 0.0, 0.0, lib)
    draw_ec3_stiffener_finplate(msp, 0.0, 0.0)

    # Detail 4: Abbreviations
    bs.txt(msp, "4  ABBREVIATIONS", 14.0, 96.0, "TEXT_2.5", "S-ANNO-TEXT")
    draw_paragraph_lines(msp, s7["abbreviations_lines"], 14.0, 90.5, 185.0)

    # Right-hand Steelwork Standard Notes column (starts at x = 202.0 so there is zero overlap with tables at x = 14..192)
    bs.txt(msp, "STEELWORK STANDARD NOTES", 202.0, 259.5, "TEXT_2.5", "S-ANNO-TEXT")
    bs.line(msp, (202.0, 255.3), (408.0, 255.3), "S-ANNO-TEXT")
    draw_numbered_notes(msp, s7["steel_standard_notes"], 202.0, 251.5, 206.0)

    p = out / f"{row['sheet_number']}_{row['revision']}.dxf"
    doc.saveas(p)
    return p


def build_all_notes_and_details(
    db: dict,
    reg_rows: list[dict],
    layers: dict,
    out: pathlib.Path,
    standards_dir: pathlib.Path,
    overrides: dict | None = None,
) -> list[pathlib.Path]:
    """Build sheets 003..007 for a project."""
    lib = load_library(standards_dir)
    by_no = {r["sheet_number"].rsplit("-", 1)[1]: r for r in reg_rows}
    builders = [
        ("003", build_003),
        ("004", build_004),
        ("005", build_005),
        ("006", build_006),
        ("007", build_007),
    ]
    made = []
    out.mkdir(parents=True, exist_ok=True)
    for code, fn in builders:
        if code in by_no:
            made.append(fn(db, by_no[code], layers, out, lib, overrides))
    return made


def convert_dxf_to_dwg(dxf_paths: list[pathlib.Path]) -> list[pathlib.Path]:
    """Convert DXF files to AutoCAD 2018 DWG (AC1032) via headless AutoCAD accoreconsole.exe if installed."""
    import subprocess
    import tempfile
    acc_candidates = [
        pathlib.Path(r"C:\Program Files\Autodesk\AutoCAD 2023\accoreconsole.exe"),
        pathlib.Path(r"C:\Program Files\Autodesk\AutoCAD 2018\accoreconsole.exe"),
    ]
    acc = next((p for p in acc_candidates if p.exists()), None)
    if acc is None:
        return []
    dwg_files = []
    with tempfile.TemporaryDirectory() as tmpd:
        scr = pathlib.Path(tmpd) / "save_dwg.scr"
        for dxf_p in dxf_paths:
            dxf_abs = dxf_p.resolve()
            dwg_abs = dxf_abs.with_suffix(".dwg")
            if dwg_abs.exists():
                dwg_abs.unlink()
            scr.write_text(f"_.SAVEAS\n2018\n\"{dwg_abs}\"\n_.QUIT\nY\n", encoding="utf-8")
            subprocess.run([str(acc), "/i", str(dxf_abs), "/s", str(scr), "/l", "en-US"], capture_output=True, text=True, timeout=60)
            if dwg_abs.exists() and dwg_abs.stat().st_size > 1000:
                dwg_files.append(dwg_abs)
    return dwg_files


def export_templates_library(standards_dir: pathlib.Path, make_dwg: bool = False) -> dict:
    """Export standalone reusable CAD detail blocks and master template sheets into Structural-Drawing-Standards/06_Templates/."""
    standards_dir = pathlib.Path(standards_dir)
    layers = c.load_layers(standards_dir)
    lib = load_library(standards_dir)

    tpl_root = standards_dir / "06_Templates"
    blk_dir = tpl_root / "blocks"
    sht_dir = tpl_root / "sheets"
    blk_dir.mkdir(parents=True, exist_ok=True)
    sht_dir.mkdir(parents=True, exist_ok=True)

    # 1. Export standalone reusable CAD blocks (.dxf)
    block_specs = [
        ("STR_TITLEBLOCK_A3", lambda msp, doc: (bs.define_titleblock(doc), bs.place_titleblock(msp, {k: f"<{k}>" for k in c.ATTRIBS}))),
        ("BLK_EC2_BENDS_AND_HOOKS", lambda msp, doc: draw_ec2_bends_and_hooks(msp, 0.0, 0.0, lib)),
        ("BLK_EC2_LAP_SPLICE", lambda msp, doc: draw_ec2_lap_splice(msp, 0.0, 0.0)),
        ("BLK_EC2_CORNER_DETAIL", lambda msp, doc: draw_ec2_corner_detail(msp, 0.0, 0.0)),
        ("BLK_EC3_BOLT_SPACING_TABLE", lambda msp, doc: draw_ec3_bolt_spacing_table(msp, 0.0, 0.0, lib)),
        ("BLK_EC3_WELD_SYMBOLS", lambda msp, doc: draw_ec3_weld_symbols(msp, 0.0, 0.0, lib)),
        ("BLK_EC3_STIFFENER_FINPLATE", lambda msp, doc: draw_ec3_stiffener_finplate(msp, 0.0, 0.0)),
    ]
    block_files = []
    for bname, draw_fn in block_specs:
        doc = bs.new_doc(layers)
        msp = doc.modelspace()
        draw_fn(msp, doc)
        bp = blk_dir / f"{bname}.dxf"
        doc.saveas(bp)
        block_files.append(bp)

    # 2. Export standalone master template sheets (TPL-STR-SD-003..007) using a generic template design basis
    tpl_db = {
        "project": {
            "code": "PJR-YYYY-NNN",
            "name": "MASTER EUROCODE TEMPLATE",
            "description": "REUSABLE EUROCODE STRUCTURAL GENERAL NOTES & STANDARD DETAILS",
            "stage": "TEMPLATE",
            "client": "TBC",
            "drawing_prefix": "TPL-STR",
            "revision": "R00",
            "issue_date": "16-OCT-2026",
        },
        "approval": {"status": "DRAFT", "prepared_by": "P.LIHENG"},
        "standards": [
            {"id": "EN 1990", "used_for": "Basis of structural design"},
            {"id": "EN 1991-1-1 / -1-4", "used_for": "Self-weight, imposed loads, wind actions"},
            {"id": "EN 1992-1-1", "used_for": "Design of concrete structures (RC)"},
            {"id": "EN 1993-1-1 / -1-8", "used_for": "Design of steel structures and joints"},
            {"id": "EN 1997-1", "used_for": "Geotechnical design"},
            {"id": "EN 1998-1", "used_for": "Seismic design / detailing"},
        ],
        "national_annex": {
            "mode": "CEN_RECOMMENDED",
            "basis_note": "CEN RECOMMENDED VALUES USED (NO NATIONAL ANNEX FOR CAMBODIA); LOCAL AUTHORITY REQUIREMENTS APPLY WHERE MORE ONEROUS.",
        },
        "design_assumptions": {"design_working_life_years": 50, "consequence_class": "CC2 (KFI = 1.0)"},
        "materials": [
            {"id": "M-CONC-PILE", "spec": "C30/37 XC2"},
            {"id": "M-CONC-STUMP", "spec": "C30/37 XC3/XC4"},
            {"id": "M-REBAR", "spec": "fyk = 390 MPa deformed bars"},
            {"id": "M-STEEL-MAIN", "spec": "S355JR (EN 10025-2)"},
            {"id": "M-BOLTS", "spec": "Class 8.8 / 10.9 (EN 14399-3)"},
        ],
        "loads": [
            {"id": "L-DL", "description": "Dead Load G (Self-weight + finishes)", "value": "TBC", "unit": "kN/m2", "source": "EN 1991-1-1"},
            {"id": "L-LL", "description": "Imposed Load Q (Category per use)", "value": "TBC", "unit": "kN/m2", "source": "EN 1991-1-1"},
            {"id": "L-WIND", "description": "Basic Wind Speed vb,0", "value": "TBC", "unit": "m/s", "source": "EN 1991-1-4"},
            {"id": "L-SEIS", "description": "Reference Peak Ground Acceleration agR", "value": "TBC", "unit": "g", "source": "EN 1998-1"},
        ],
        "open_items": [
            {"id": "F1", "status": "open", "description": "Confirm geotechnical parameters, foundation bearing capacity, and pile test requirements"},
            {"id": "F2", "status": "open", "description": "Confirm equipment, MEP, and facade/cladding loads with specialist suppliers"},
            {"id": "F3", "status": "open", "description": "Confirm site wind terrain category, exposure class, and fire resistance rating"},
        ],
    }
    tpl_reg = [
        {"sheet_number": "TPL-STR-SD-003", "sheet_name": lib["sheet_003"]["title_default"], "paper": "A3", "revision": "R00", "issue_date": "16-OCT-2026", "stage": "TEMPLATE"},
        {"sheet_number": "TPL-STR-SD-004", "sheet_name": lib["sheet_004"]["title_default"], "paper": "A3", "revision": "R00", "issue_date": "16-OCT-2026", "stage": "TEMPLATE"},
        {"sheet_number": "TPL-STR-SD-005", "sheet_name": lib["sheet_005"]["title_default"], "paper": "A3", "revision": "R00", "issue_date": "16-OCT-2026", "stage": "TEMPLATE"},
        {"sheet_number": "TPL-STR-SD-006", "sheet_name": lib["sheet_006"]["title_default"], "paper": "A3", "revision": "R00", "issue_date": "16-OCT-2026", "stage": "TEMPLATE"},
        {"sheet_number": "TPL-STR-SD-007", "sheet_name": lib["sheet_007"]["title_default"], "paper": "A3", "revision": "R00", "issue_date": "16-OCT-2026", "stage": "TEMPLATE"},
    ]
    sheet_files = build_all_notes_and_details(tpl_db, tpl_reg, layers, sht_dir, standards_dir, overrides=None)
    preview_pdf = sht_dir / "TPL-STR-SD_R00_preview.pdf"
    bs.plot_pdf(sheet_files, preview_pdf)
    dwg_made = convert_dxf_to_dwg(block_files + sheet_files) if make_dwg else []
    val_summary = {}
    for sf in sheet_files:
        v = vd.validate(sf, standards_dir, tpl_db, tpl_reg)
        doc = ezdxf.readfile(sf)
        from ezdxf import bbox
        boxes = [(b.extmin.x, b.extmin.y, b.extmax.x, b.extmax.y) for e in doc.modelspace().query("TEXT") if (b := bbox.extents([e])).has_data]
        ov = sum(1 for i in range(len(boxes)) for j in range(i + 1, len(boxes))
                 if min(boxes[i][2], boxes[j][2]) - max(boxes[i][0], boxes[j][0]) > 0.3 and min(boxes[i][3], boxes[j][3]) - max(boxes[i][1], boxes[j][1]) > 0.3)
        val_summary[sf.name] = {"ok": v["ok"], "errors": v["errors"], "warnings": v["warnings"], "text_overlaps": ov}
    return {
        "blocks_dxf": [str(p) for p in block_files],
        "sheets_dxf": [str(p) for p in sheet_files],
        "dwg": [str(p) for p in dwg_made],
        "preview_pdf": str(preview_pdf),
        "validation": val_summary,
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--design-basis")
    ap.add_argument("--register")
    ap.add_argument("--standards", required=True)
    ap.add_argument("--out")
    ap.add_argument("--overrides")
    ap.add_argument("--export-templates", action="store_true")
    ap.add_argument("--dwg", action="store_true", help="Also convert generated DXFs to AutoCAD 2018 DWG via accoreconsole.exe")
    ap.add_argument("--no-pdf", action="store_true")
    ns = ap.parse_args(argv)

    std_dir = pathlib.Path(ns.standards)
    if ns.export_templates:
        res = export_templates_library(std_dir, make_dwg=ns.dwg)
        print(json.dumps(res, indent=2))
        return 0 if all(v["ok"] and v["text_overlaps"] == 0 for v in res["validation"].values()) else 1

    if not ns.design_basis or not ns.register or not ns.out:
        ap.error("--design-basis, --register, and --out are required unless --export-templates is set")

    db = yaml.safe_load(open(ns.design_basis, encoding="utf-8"))
    with open(ns.register, newline="", encoding="utf-8-sig") as fh:
        reg = list(csv.DictReader(fh))
    overrides = yaml.safe_load(open(ns.overrides, encoding="utf-8")) if ns.overrides and pathlib.Path(ns.overrides).exists() else None
    layers = c.load_layers(std_dir)
    out = pathlib.Path(ns.out)
    made = build_all_notes_and_details(db, reg, layers, out, std_dir, overrides)
    dwg_made = convert_dxf_to_dwg(made) if ns.dwg else []
    val_summary = {}
    for mf in made:
        v = vd.validate(mf, std_dir, db, reg)
        doc = ezdxf.readfile(mf)
        from ezdxf import bbox
        boxes = [(b.extmin.x, b.extmin.y, b.extmax.x, b.extmax.y) for e in doc.modelspace().query("TEXT") if (b := bbox.extents([e])).has_data]
        ov = sum(1 for i in range(len(boxes)) for j in range(i + 1, len(boxes))
                 if min(boxes[i][2], boxes[j][2]) - max(boxes[i][0], boxes[j][0]) > 0.3 and min(boxes[i][3], boxes[j][3]) - max(boxes[i][1], boxes[j][1]) > 0.3)
        val_summary[mf.name] = {"ok": v["ok"], "errors": v["errors"], "warnings": v["warnings"], "text_overlaps": ov}
    pdf = None
    if not ns.no_pdf and made:
        pdf = out / f"{db['project']['drawing_prefix']}-SD-003_007_{db['project']['revision']}_preview.pdf"
        bs.plot_pdf(made, pdf)
    print(json.dumps({"dxf": [str(m) for m in made], "dwg": [str(m) for m in dwg_made], "preview_pdf": str(pdf) if pdf else None, "validation": val_summary}, indent=2))
    return 0 if all(v["ok"] and v["text_overlaps"] == 0 for v in val_summary.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
