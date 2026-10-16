#!/usr/bin/env python3
"""Generate the cover page (001) and drawing list (002) as DXF + a preview PDF, and validate them.

Usage:
  python tools/cadgen/build_sheets.py --design-basis <db.yaml> --register <register.csv> --standards <Structural-Drawing-Standards> --out <dir>

Outputs per sheet: <number>_<rev>.dxf. Plus <prefix>-STR-SD_<rev>_preview.pdf (matplotlib plot of the DXF files).
What this is NOT: no DWG is produced, the PDF is a script-rendered preview, not an AutoCAD plot with the company CTB.
Sheet layout measured from WH-STR-SD Drawing Set R00; layers from 05-04 + proposed 05-04a.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import pathlib
import sys

import ezdxf
import yaml
from ezdxf import units
from ezdxf.enums import TextEntityAlignment as A

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import common as c  # noqa: E402

CELLS = [  # tag, label, x0, x1, row (1 top / 2 bottom)
    ("PROJ_REFERENCE", "PROJ. REFERENCE:", "a", "b", 1), ("DRAWING_NAME", "DRAWING NAME:", "b", "d", 1),
    ("REVISION", "REVISION:", "d", "e", 1), ("DRAWN_BY", "DRAWN BY:", "f", "g", 1),
    ("DRAWING_NUMBER", "DRAWING NUMBER:", "a", "b", 2), ("DRAWING_STAGE", "DRAWING STAGE:", "b", "c", 2),
    ("CLIENT", "CLIENT:", "c", "d", 2), ("SCALE", "SCALE:", "d", "e", 2), ("ISSUE_DATE", "ISSUE DATE:", "f", "g", 2),
]


class MissingInput(Exception):
    pass


def new_doc(layers: dict) -> ezdxf.document.Drawing:
    doc = ezdxf.new("R2013", setup=True)
    doc.units = units.MM
    doc.header["$MEASUREMENT"] = 1
    for name, h in c.TEXT_HEIGHTS.items():
        doc.styles.add(name, font=c.FONT_FILE, dxfattribs={"width": 1.0})
    for name, p in layers.items():
        if name == "0":
            continue
        if p["linetype"] not in doc.linetypes:
            raise MissingInput(f"linetype {p['linetype']} for layer {name} not available in the DXF template")
        la = doc.layers.get(name) if name in doc.layers else doc.layers.add(name)
        la.color, la.dxf.linetype = p["color"], p["linetype"]
        if p["lineweight"] is not None:
            la.dxf.lineweight = p["lineweight"]
        la.dxf.plot = 1 if p["plot"] else 0
    return doc


def txt(layout, text, x, y, style, layer, align=A.LEFT, color=None):
    e = layout.add_text(text, height=c.TEXT_HEIGHTS[style], dxfattribs={"style": style, "layer": layer, **({"color": color} if color else {})})
    e.set_placement((x, y), align=align)
    return e


def line(layout, p1, p2, layer):
    return layout.add_line(p1, p2, dxfattribs={"layer": layer})


def define_titleblock(doc):
    blk = doc.blocks.new(c.TB_BLOCK)
    x = c.TB_X
    x0, y0, x1, y1 = c.BORDER
    blk.add_lwpolyline([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], close=True, dxfattribs={"layer": "S-TBLK-BORDER"})
    L = "S-TBLK-LINE"
    line(blk, (x0, c.TB_BOT), (x1, c.TB_BOT), L)
    line(blk, (x0, c.TB_MID), (x["e"], c.TB_MID), L)
    line(blk, (x["f"], c.TB_MID), (x["g"], c.TB_MID), L)
    for k, (ya, yb) in {"b": (c.TB_BOT, c.TB_TOP), "c": (c.TB_BOT, c.TB_MID), "d": (c.TB_BOT, c.TB_TOP), "e": (c.TB_BOT, c.TB_TOP),
                        "f": (c.TB_BOT, c.TB_TOP), "g": (c.TB_BOT, c.TB_TOP)}.items():
        line(blk, (x[k], ya), (x[k], yb), L)
    for tag, label, ka, kb, row in CELLS:
        top, bot = (c.TB_TOP, c.TB_MID) if row == 1 else (c.TB_MID, c.TB_BOT)
        txt(blk, label, x[ka] + 1.2, top - 3.4, "TEXT_2.0", "S-TBLK-TEXT", color=c.GREY)
        ad = blk.add_attdef(tag, (x[ka] + 1.2, bot + 2.6), height=2.5, text="",
                            dxfattribs={"style": "TEXT_2.5", "layer": "S-TBLK-TEXT"})
        ad.dxf.prompt = label.rstrip(":")
    # north arrow and discipline label
    ax = x["arrow"]
    line(blk, (ax, 272.0), (ax, 282.5), "S-TBLK-LINE")
    blk.add_solid([(ax - 1.3, 278.8), (ax + 1.3, 278.8), (ax, 284.5), (ax, 284.5)], dxfattribs={"layer": "S-TBLK-LINE"})
    txt(blk, "N", ax, 287.0, "TEXT_2.5", "S-TBLK-TEXT", A.MIDDLE_CENTER)
    txt(blk, "STRUCTURAL (BIM)", x["g"] + 1.5, c.TB_BOT + 2.4, "TEXT_2.0", "S-TBLK-TEXT")


def place_titleblock(msp, values: dict):
    ref = msp.add_blockref(c.TB_BLOCK, (0, 0), dxfattribs={"layer": "S-TBLK-LINE"})
    ref.add_auto_attribs(values)
    return ref


def iso_points(g):
    """Wireframe of the portal frames from the design-basis geometry (SD-003 A3/A4). Returns line list in 2D iso coords."""
    for k in ("span_m", "length_m", "frames", "eave_level_m", "ridge_level_m"):
        if g.get(k) in (None, ""):
            raise MissingInput(f"design basis geometry.{k} missing")
    # consistency: ridge = eave + (span/2) tan(slope)
    if g.get("roof_slope_deg") is not None:
        calc = g["eave_level_m"] + g["span_m"] / 2 * math.tan(math.radians(g["roof_slope_deg"]))
        if abs(calc - g["ridge_level_m"]) > 0.01:
            raise MissingInput(f"geometry inconsistent: ridge {g['ridge_level_m']} vs eave+tan(slope) {calc:.3f}")
    S, Lm, n, he, hr = g["span_m"], g["length_m"], int(g["frames"]), g["eave_level_m"], g["ridge_level_m"]
    ca, sa = math.cos(math.radians(30)), math.sin(math.radians(30))
    P = lambda x, y, z: ((x - y) * ca, (x + y) * sa + z)
    xs = [i * Lm / (n - 1) for i in range(n)]
    segs = []
    for x in xs:  # frames
        segs += [(P(x, 0, 0), P(x, 0, he)), (P(x, S, 0), P(x, S, he)), (P(x, 0, he), P(x, S / 2, hr)), (P(x, S / 2, hr), P(x, S, he))]
    for (xa, xb) in zip(xs, xs[1:]):  # eave struts + ridge
        segs += [(P(xa, 0, he), P(xb, 0, he)), (P(xa, S, he), P(xb, S, he)), (P(xa, S / 2, hr), P(xb, S / 2, hr))]
    segs += [(P(0, 0, 0), P(Lm, 0, 0)), (P(Lm, 0, 0), P(Lm, S, 0)), (P(Lm, S, 0), P(0, S, 0)), (P(0, S, 0), P(0, 0, 0))]
    return segs


def fit(segs, box):
    xs = [p[0] for s in segs for p in s]
    ys = [p[1] for s in segs for p in s]
    bx0, by0, bx1, by1 = box
    k = min((bx1 - bx0) / (max(xs) - min(xs)), (by1 - by0) / (max(ys) - min(ys)))
    ox = bx0 + ((bx1 - bx0) - k * (max(xs) - min(xs))) / 2 - k * min(xs)
    oy = by0 + ((by1 - by0) - k * (max(ys) - min(ys))) / 2 - k * min(ys)
    return [((ox + k * a[0], oy + k * a[1]), (ox + k * b[0], oy + k * b[1])) for a, b in segs]


def sheet_values(db, row, name, scale):
    P, A_ = db["project"], db["approval"]
    return {"PROJ_REFERENCE": P["code"], "DRAWING_NAME": name, "REVISION": row["revision"], "DRAWN_BY": A_.get("prepared_by") or "",
            "DRAWING_NUMBER": row["sheet_number"], "DRAWING_STAGE": row["stage"], "CLIENT": P["client"], "SCALE": scale,
            "ISSUE_DATE": row["issue_date"]}


def build_cover(db, row, layers, out):
    doc = new_doc(layers)
    define_titleblock(doc)
    msp = doc.modelspace()
    P = db["project"]
    place_titleblock(msp, sheet_values(db, row, row["sheet_name"], "AS-SHOWN"))
    cx = 210.0
    txt(msp, f"{P['code']}_{P['name']}", cx, 215.7, "TEXT_5.0", "S-ANNO-TEXT", A.MIDDLE_CENTER)
    line(msp, (41.5, 206.0), (378.2, 206.0), "S-ANNO-LEADER")
    txt(msp, "STRUCTURAL CONSTRUCTION DRAWING", cx, 190.7, "TEXT_3.5", "S-ANNO-TEXT", A.MIDDLE_CENTER)
    g = db.get("geometry")
    codes = "EUROCODES (EN 1990-1993, EN 1997)"
    if g:
        desc = f"{g['span_m']:.1f} m x {g['length_m']:.1f} m STEEL PORTAL FRAME | DESIGN TO {codes}"
        try:
            for a, b in fit(iso_points(g), (150.0, 50.0, 270.0, 145.0)):
                line(msp, a, b, "S-VIEW-ISO")
        except MissingInput as e:
            txt(msp, f"ISOMETRIC VIEW NOT GENERATED - {e}", cx, 100.0, "TEXT_2.0", "S-ANNO-TEXT", A.MIDDLE_CENTER)
    else:
        desc = f"STRUCTURAL DESCRIPTION TBC | DESIGN TO {codes}"
        txt(msp, "ISOMETRIC VIEW NOT GENERATED - design basis has no geometry section", cx, 100.0, "TEXT_2.0", "S-ANNO-TEXT", A.MIDDLE_CENTER)
    txt(msp, desc, cx, 175.1, "TEXT_2.0", "S-ANNO-TEXT", A.MIDDLE_CENTER)
    txt(msp, f"ISSUE DATE: {row['issue_date']}", cx, 40.0, "TEXT_3.5", "S-ANNO-TEXT", A.MIDDLE_CENTER)
    txt(msp, f"REVISION: {row['revision']}", cx, 30.1, "TEXT_3.5", "S-ANNO-TEXT", A.MIDDLE_CENTER)
    p = out / f"{row['sheet_number']}_{row['revision']}.dxf"
    doc.saveas(p)
    return p


def build_list(db, row, rows, layers, out):
    doc = new_doc(layers)
    define_titleblock(doc)
    msp = doc.modelspace()
    place_titleblock(msp, sheet_values(db, row, row["sheet_name"], "AS-SHOWN"))
    txt(msp, "STRUCTURAL DRAWING LIST", 41.5, 250.0, "TEXT_3.5", "S-ANNO-TEXT")
    xs = [41.5, 81.2, 230.8, 247.7, 279.4, 315.2]
    top, hh, rh = 244.3, 7.0, 6.4
    heads = ["Sheet Number", "Sheet Name", "Paper", "Current Revision", "Sheet Issue Date"]
    nrows = len(rows)
    bottom = top - hh - nrows * rh
    ys = [top, top - hh] + [top - hh - (i + 1) * rh for i in range(nrows)]
    for y in ys:
        line(msp, (xs[0], y), (xs[-1], y), "S-ANNO-TABLE")
    for x in xs:
        line(msp, (x, top), (x, bottom), "S-ANNO-TABLE")
    for i, h in enumerate(heads):
        txt(msp, h, (xs[i] + xs[i + 1]) / 2, top - hh / 2, "TEXT_2.5", "S-ANNO-TEXT", A.MIDDLE_CENTER)
    for r_i, r in enumerate(rows):
        yc = top - hh - rh * (r_i + 0.5)
        vals = [r["sheet_number"], r["sheet_name"], r["paper"], r["revision"], r["issue_date"]]
        for i, v in enumerate(vals):
            if i == 1:
                txt(msp, v, xs[i] + 1.5, yc, "TEXT_2.0", "S-ANNO-TEXT", A.MIDDLE_LEFT)
            else:
                txt(msp, v, (xs[i] + xs[i + 1]) / 2, yc, "TEXT_2.0", "S-ANNO-TEXT", A.MIDDLE_CENTER)
    if bottom < 8:
        raise MissingInput(f"drawing list needs {nrows} rows and does not fit on one A3 sheet - add a continuation sheet")
    p = out / f"{row['sheet_number']}_{row['revision']}.dxf"
    doc.saveas(p)
    return p


def plot_pdf(dxf_paths, pdf_path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_pdf import PdfPages
    from ezdxf.addons.drawing import Frontend, RenderContext, layout
    from ezdxf.addons.drawing.config import Configuration, BackgroundPolicy, ColorPolicy
    from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
    cfg = Configuration(background_policy=BackgroundPolicy.WHITE, color_policy=ColorPolicy.BLACK, lineweight_scaling=72.0 / 25.4, min_lineweight=0.05)  # DXF lineweight mm -> matplotlib points; no 0.25 mm clamp
    with PdfPages(pdf_path) as pdf:
        for p in dxf_paths:
            doc = ezdxf.readfile(p)
            fig = plt.figure(figsize=(c.SHEET_W / 25.4, c.SHEET_H / 25.4))
            ax = fig.add_axes([0, 0, 1, 1])
            ctx = RenderContext(doc)
            Frontend(ctx, MatplotlibBackend(ax), config=cfg).draw_layout(doc.modelspace(), finalize=False)
            ax.set_xlim(0, c.SHEET_W)
            ax.set_ylim(0, c.SHEET_H)
            ax.set_aspect("equal")
            ax.axis("off")
            pdf.savefig(fig)
            plt.close(fig)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--design-basis", required=True)
    ap.add_argument("--register", required=True)
    ap.add_argument("--standards", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--include-notes-details", action="store_true", help="Also generate sheets 003-007 from the Eurocode General Notes & Standard Details library")
    ap.add_argument("--overrides", help="Optional notes_overrides.yaml for project-specific General Notes tables/clauses")
    ap.add_argument("--no-pdf", action="store_true")
    ns = ap.parse_args(argv)
    db = yaml.safe_load(open(ns.design_basis, encoding="utf-8"))
    with open(ns.register, newline="", encoding="utf-8-sig") as fh:
        rows = list(csv.DictReader(fh))
    std_dir = pathlib.Path(ns.standards)
    layers = c.load_layers(std_dir)
    out = pathlib.Path(ns.out)
    out.mkdir(parents=True, exist_ok=True)
    by_no = {r["sheet_number"].rsplit("-", 1)[1]: r for r in rows}
    made = []
    try:
        made.append(build_cover(db, by_no["001"], layers, out))
        made.append(build_list(db, by_no["002"], rows, layers, out))
        if ns.include_notes_details:
            import build_notes_and_details as bnd
            ov = yaml.safe_load(open(ns.overrides, encoding="utf-8")) if ns.overrides and pathlib.Path(ns.overrides).exists() else None
            made.extend(bnd.build_all_notes_and_details(db, rows, layers, out, std_dir, ov))
    except (MissingInput, KeyError) as e:
        print(f"BUILD STOPPED: {e}", file=sys.stderr)
        return 1
    pdf = None
    if not ns.no_pdf:
        pdf = out / f"{db['project']['drawing_prefix']}-SD_{db['project']['revision']}_preview.pdf"
        plot_pdf(made, pdf)
    print(json.dumps({"dxf": [str(m) for m in made], "preview_pdf": str(pdf) if pdf else None,
                      "dwg": None, "note": "DXF generated by script; no DWG; PDF is a script-rendered preview (no AutoCAD/CTB)"}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
