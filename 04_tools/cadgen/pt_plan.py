#!/usr/bin/env python3
"""Data-driven PT tendon LAYOUT PLAN (BONDED post-tensioning) -> A3 DXF + script-rendered preview PDF + tendon schedule CSV.

Usage:
  python 04_tools/cadgen/pt_plan.py --data <pt_plan_data.json> --standards 01_standards --out <dir> [--no-pdf]

Everything project specific is in the data file (schema: .claude/skills/pt-drawings/references/pt-plan-data.md):
grid, columns, slab / drop-panel outlines, tendon lines, tendon marks and schedule, labels, dimensions, notes, title block.
This script contains no project values. It never invents a value: a tendon with a missing field stops the build.
Layers come from the approved standard (05-04, 05-04a, 05-04b) plus 05-04c if present (PROPOSED: S-PT-TENDON, S-CONC-DROP).
Output is a DXF written by script (not a DWG) and a rendered preview (not a CTB plot). Nothing here is approved.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import pathlib
import sys

from ezdxf.enums import TextEntityAlignment as A

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import build_sheets as bs  # noqa: E402
import common as c  # noqa: E402

ALIGN = {"LEFT": A.LEFT, "RIGHT": A.RIGHT, "MIDDLE_CENTER": A.MIDDLE_CENTER, "MIDDLE_LEFT": A.MIDDLE_LEFT, "MIDDLE_RIGHT": A.MIDDLE_RIGHT,
         "BOTTOM_CENTER": A.BOTTOM_CENTER}
SYMBOL_NOTE = "symbol for {n} strands is not defined in the company legend (see PT-OI-12 in the PT basis)"


class PlanDataError(Exception):
    pass


def load_layers(standards: pathlib.Path) -> dict:
    """05-04 + approved 05-04a/b, plus PROPOSED 05-04c when present (flagged status 'proposed')."""
    L = c.load_layers(standards)
    p = pathlib.Path(standards) / "05-drafting-styles" / "05-04c-layer-extensions-proposed.csv"
    if p.exists():
        with open(p, newline="", encoding="utf-8-sig") as fh:
            for r in csv.DictReader(fh):
                L[r["Layer Name"].strip()] = {"color": int(r["Colour"]), "linetype": c.LINETYPE_MAP.get(r["Linetype"].strip(), r["Linetype"].strip().upper()),
                                              "lineweight": int(round(float(r["Lineweight"].strip()) * 100)), "plot": r["Plot"].strip().lower() == "yes",
                                              "description": r["Description"].strip(), "status": "proposed"}
    return L


def cluster_boxes(lines, gap=250.0):
    """Merge nearby hatch lines into rectangles. Used by the redraft converter only (kept here so it is tested with the generator)."""
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


class Plan:
    def __init__(self, data: dict, layers: dict):
        self.d = data
        self.sc = float(data["scale_den"])
        self.ox, self.oy = data["origin_paper_mm"]
        self.doc = bs.new_doc(layers)
        bs.define_titleblock(self.doc)
        self.msp = self.doc.modelspace()

    # ---- coordinate helpers
    def PX(self, x): return self.ox + x / self.sc
    def PY(self, y): return self.oy + y / self.sc

    def txt(self, s, x, y, style="TEXT_2.0", layer="S-ANNO-TEXT", align=A.LEFT, rot=0.0):
        e = bs.txt(self.msp, s, x, y, style, layer, align)
        if rot:
            e.dxf.rotation = rot
        return e

    def ln(self, p1, p2, layer): return self.msp.add_line(p1, p2, dxfattribs={"layer": layer})

    def poly(self, pts, layer, closed=False):
        return self.msp.add_lwpolyline([(self.PX(x), self.PY(y)) for x, y in pts], close=closed, dxfattribs={"layer": layer})

    def arrow(self, tip, direction, layer="S-ANNO-DIMS", size=2.5, width=0.8):
        dx, dy = direction
        n = math.hypot(dx, dy); dx, dy = dx / n, dy / n
        bx, by = tip[0] - dx * size, tip[1] - dy * size
        px, py = -dy * width / 2, dx * width / 2
        self.msp.add_solid([tip, (bx + px, by + py), (bx - px, by - py), (bx - px, by - py)], dxfattribs={"layer": layer})

    def symbol(self, x, y, strands, layer="S-PT-TENDON", s=1.6):
        """Strand-count symbol from the company PT legend: 2 circle, 3 triangle, 4 square, 5 diamond. Anything else is refused (PT-OI-12)."""
        m = self.msp
        if strands == 4:
            m.add_lwpolyline([(x - s / 2, y - s / 2), (x + s / 2, y - s / 2), (x + s / 2, y + s / 2), (x - s / 2, y + s / 2)], close=True, dxfattribs={"layer": layer})
        elif strands == 3:
            m.add_lwpolyline([(x - s / 2, y - s / 2), (x + s / 2, y - s / 2), (x, y + s / 2)], close=True, dxfattribs={"layer": layer})
        elif strands == 2:
            m.add_circle((x, y), s / 2, dxfattribs={"layer": layer})
        elif strands == 5:
            m.add_lwpolyline([(x, y - s * 0.7), (x + s * 0.7, y), (x, y + s * 0.7), (x - s * 0.7, y)], close=True, dxfattribs={"layer": layer})
        else:
            raise PlanDataError(SYMBOL_NOTE.format(n=strands))

    def dim_h(self, y, xs_paper, labels):
        ln = self.ln
        ln((xs_paper[0], y), (xs_paper[-1], y), "S-ANNO-DIMS")
        for x in xs_paper:
            ln((x, y - 1.5), (x, y + 1.5), "S-ANNO-DIMS")
        for a, b, lab in zip(xs_paper, xs_paper[1:], labels):
            self.arrow((a, y), (-1, 0)); self.arrow((b, y), (1, 0))
            self.txt(lab, (a + b) / 2, y + 1.0, "TEXT_2.0", "S-ANNO-DIMS", A.BOTTOM_CENTER)

    def dim_v(self, x, ys_paper, labels):
        ln = self.ln
        ln((x, ys_paper[0]), (x, ys_paper[-1]), "S-ANNO-DIMS")
        for y in ys_paper:
            ln((x - 1.5, y), (x + 1.5, y), "S-ANNO-DIMS")
        for a, b, lab in zip(ys_paper, ys_paper[1:], labels):
            self.arrow((x, a), (0, -1)); self.arrow((x, b), (0, 1))
            self.txt(lab, x - 1.0, (a + b) / 2, "TEXT_2.0", "S-ANNO-DIMS", A.BOTTOM_CENTER, rot=90)

    def bubble(self, x, y, label):
        self.msp.add_circle((x, y), 4.0, dxfattribs={"layer": "S-ANNO-LEADER"})
        self.txt(label, x, y, "TEXT_3.5", "S-ANNO-TEXT", A.MIDDLE_CENTER)

    def hatch_rect(self, x0, y0, x1, y1, pattern="ANSI31", scale=1.2):
        pts = [(self.PX(x0), self.PY(y0)), (self.PX(x1), self.PY(y0)), (self.PX(x1), self.PY(y1)), (self.PX(x0), self.PY(y1))]
        h = self.msp.add_hatch(dxfattribs={"layer": "S-HATCH-CONC"})
        h.set_pattern_fill(pattern, color=256, scale=scale, angle=0)
        h.paths.add_polyline_path(pts, is_closed=True)
        self.msp.add_lwpolyline(pts, close=True, dxfattribs={"layer": "S-DETAIL-THIN"})


def check_data(d: dict) -> None:
    for k in ("scale_den", "origin_paper_mm", "title_block", "grid", "tendons"):
        if k not in d:
            raise PlanDataError(f"data file lacks '{k}'")
    keys = set()
    for t in d["tendons"]:
        for f in ("group", "mark", "strands", "first", "last", "length_m", "dir"):
            if t.get(f) in (None, ""):
                raise PlanDataError(f"tendon {t.get('group')} / {t.get('mark')}: field '{f}' missing - not guessed")
        if t["group"] in keys:
            raise PlanDataError(f"duplicate tendon group number {t['group']}")
        keys.add(t["group"])
        if t["dir"] == "X" and not all(k in t for k in ("y", "side")):
            raise PlanDataError(f"X tendon group {t['group']} needs 'y' and 'side'")
        if t["dir"] == "Y" and "anchor" not in t:
            raise PlanDataError(f"Y tendon group {t['group']} needs 'anchor'")
        if int(t["last"]) - int(t["first"]) + 1 != int(t["strands"]):
            raise PlanDataError(f"tendon group {t['group']} {t['mark']}: strand numbers {t['first']}-{t['last']} do not match {t['strands']} strands")


def schedule_rows(d: dict):
    X = sorted([t for t in d["tendons"] if t["dir"] == "X"], key=lambda t: t["group"])
    Y = sorted([t for t in d["tendons"] if t["dir"] == "Y"], key=lambda t: t["anchor"][0])
    return X, Y


def build(d: dict, standards: pathlib.Path, out: pathlib.Path):
    check_data(d)
    P = Plan(d, load_layers(standards))
    PX, PY, txt, ln, msp = P.PX, P.PY, P.txt, P.ln, P.msp
    bs.place_titleblock(msp, d["title_block"])
    for t in d.get("titles", []):
        txt(t["text"], t["x"], t["y"], t.get("style", "TEXT_2.0"))

    # grid
    gx = d["grid"]["x"]; gy = d["grid"]["y"]
    xmin, xmax = min(g["pos"] for g in gx), max(g["pos"] for g in gx)
    ymin, ymax = min(g["pos"] for g in gy), max(g["pos"] for g in gy)
    gs = {"x_bottom": 17.0, "x_top": 4.0, "x_bubble": 36.0, "x_stub": 32.0, "y_ext_model": 1500.0, "y_bubble_x": 14.0, "y_leader": [18.0, 26.0], **d["grid"].get("style", {})}
    for g in gx:
        ln((PX(g["pos"]), PY(ymin) - gs["x_bottom"]), (PX(g["pos"]), PY(ymax) + gs["x_top"]), "S-GRID")
        P.bubble(PX(g["pos"]), PY(ymin) - gs["x_bubble"], g["name"])
        ln((PX(g["pos"]), PY(ymin) - gs["x_stub"]), (PX(g["pos"]), PY(ymin) - gs["x_bottom"]), "S-GRID")
    for g in gy:
        ln((PX(xmin - gs["y_ext_model"]), PY(g["pos"])), (PX(xmax + gs["y_ext_model"]), PY(g["pos"])), "S-GRID")
        ln((gs["y_leader"][0] + 0.0, PY(g["pos"])), (gs["y_leader"][1], PY(g["pos"])), "S-ANNO-LEADER")
        P.bubble(gs["y_bubble_x"], PY(g["pos"]), g["name"])

    # outlines (slab, walls, voids, drop panels / thickened bands)
    for o in d.get("outlines", []):
        P.poly(o["pts"], o.get("layer", "S-CONC-OUTLINE"), o.get("closed", False))
    for b in d.get("blockouts", []):
        P.hatch_rect(*b)
    for col in d.get("columns", []):
        h = col["size"] / 2; x, y = col["x"], col["y"]
        sq = [(PX(x - h), PY(y - h)), (PX(x + h), PY(y - h)), (PX(x + h), PY(y + h)), (PX(x - h), PY(y + h))]
        msp.add_lwpolyline(sq, close=True, dxfattribs={"layer": "S-CONC-OUTLINE"})
        ht = msp.add_hatch(dxfattribs={"layer": "S-HATCH-CONC"})
        ht.set_pattern_fill("SOLID", color=256)
        ht.paths.add_polyline_path(sq, is_closed=True)
    for cb in d.get("cross_boxes", []):
        x0, y0, x1, y1 = cb["bbox"]
        ln((PX(x0), PY(y0)), (PX(x1), PY(y1)), "S-DETAIL-THIN"); ln((PX(x0), PY(y1)), (PX(x1), PY(y0)), "S-DETAIL-THIN")
        txt(cb["label"], PX((x0 + x1) / 2), PY(y1) + cb.get("label_dy_mm", -3.0), "TEXT_2.0", "S-ANNO-TEXT", A.MIDDLE_CENTER)
    for tl in d.get("tendon_lines", []):
        P.poly(tl, "S-PT-TENDON", False)

    X_t, Y_t = schedule_rows(d)
    tg = {"y_model": None, "y_off_mm": -3.0, "pitch_mm": 3.2, **d.get("tags_below", {})}
    side_off = d.get("side_offset_model", 600.0)

    # Y tendon tags below the slab (fan-out so labels keep a minimum pitch)
    if Y_t:
        if tg["y_model"] is None:
            raise PlanDataError("tags_below.y_model is required when Y tendons exist")
        desired = [PX(t["anchor"][0]) for t in Y_t]
        pos = list(desired); pitch = tg["pitch_mm"]
        for _ in range(400):
            moved = False
            for i in range(len(pos) - 1):
                gap = pos[i + 1] - pos[i]
                if gap < pitch:
                    dd = (pitch - gap) / 2
                    pos[i] -= dd; pos[i + 1] += dd; moved = True
            if not moved:
                break
        y_sym = PY(tg["y_model"]) + tg["y_off_mm"]
        for t, px, pp in zip(Y_t, desired, pos):
            yb = PY(t["anchor"][1])
            if abs(pp - px) > 0.2:
                ln((px, yb), (px, yb - 1.2), "S-ANNO-LEADER"); ln((px, yb - 1.2), (pp, y_sym + 1.2), "S-ANNO-LEADER")
            else:
                ln((px, yb), (pp, y_sym + 1.2), "S-ANNO-LEADER")
            P.symbol(pp, y_sym, t["strands"])
            txt(f"{t['mark']} G{t['group']}", pp + 1.0, y_sym - 1.4, "TEXT_2.0", "S-ANNO-TEXT", A.RIGHT, rot=90)

    # X tendon labels in left / right columns (fan-out leaders)
    for side in ("L", "R"):
        items = sorted([t for t in X_t if t["side"] == side], key=lambda t: -t["y"])
        ys = [PY(t["y"]) for t in items]
        pos = []
        for i, y in enumerate(ys):
            pos.append(y if i == 0 else min(y, pos[-1] - 3.2))
        for t, y, p in zip(items, ys, pos):
            label = f"{t['mark']} G{t['group']} {t['first']}-{t['last']}"
            if side == "L":
                xe = PX(xmin - side_off)
                ln((xe, y), (xe - 3.0, y), "S-ANNO-LEADER"); ln((xe - 3.0, y), (xe - 6.0, p), "S-ANNO-LEADER")
                P.symbol(xe - 7.2, p, t["strands"])
                txt(label, xe - 8.6, p, "TEXT_2.0", "S-ANNO-TEXT", A.MIDDLE_RIGHT)
            else:
                xe = PX(xmax + side_off)
                ln((xe, y), (xe + 3.0, y), "S-ANNO-LEADER"); ln((xe + 3.0, y), (xe + 6.0, p), "S-ANNO-LEADER")
                P.symbol(xe + 7.2, p, t["strands"])
                txt(label, xe + 8.6, p, "TEXT_2.0", "S-ANNO-TEXT", A.MIDDLE_LEFT)

    # free labels anchored in the model with a paper offset (notes on the plan, member marks, column tags)
    for lb in d.get("labels", []):
        txt(lb["text"], PX(lb["x"]) + lb.get("dx_mm", 0.0), PY(lb["y"]) + lb.get("dy_mm", 0.0), "TEXT_2.0", "S-ANNO-TEXT",
            ALIGN[lb.get("align", "LEFT")], rot=lb.get("rot", 0.0))
    for lm in d.get("level_marks", []):
        lx, ly = PX(lm["x"]), PY(lm["y"])
        msp.add_lwpolyline([(lx - 1.5, ly + 2.6), (lx + 1.5, ly + 2.6), (lx, ly)], close=True, dxfattribs={"layer": "S-ANNO-LEADER"})
        ln((lx + 1.5, ly + 2.6), (lx + 9.0, ly + 2.6), "S-ANNO-LEADER")
        txt(lm["text"], lx + 2.5, ly + 3.2, "TEXT_2.0", "S-ANNO-TEXT", A.LEFT)
    bo_label = d.get("blockout_label", "B/O")
    for bx in d.get("blockouts", []):
        wide = (bx[2] - bx[0]) > (bx[3] - bx[1])
        txt(bo_label, PX((bx[0] + bx[2]) / 2) + (0.0 if wide else 3.2), PY((bx[1] + bx[3]) / 2) + (-3.0 if wide else 0.0), "TEXT_2.0", "S-ANNO-TEXT",
            A.MIDDLE_CENTER, rot=0 if wide else 90)

    # dimensions
    for dm in d.get("dims", []):
        if dm["dir"] == "h":
            y = PY(dm["ref_model"]) + dm["offset_mm"]
            P.dim_h(y, [PX(x) for x in dm["positions"]], dm["labels"])
        else:
            x = dm["paper"] if "paper" in dm else PX(dm["ref_model"]) + dm["offset_mm"]
            P.dim_v(x, [PY(y) for y in dm["positions"]], dm["labels"])

    # tendon schedule (derived from the tendon list - plan tag and schedule cannot disagree)
    S = {"x0": 334.0, "top": 258.0, "row_h": 3.35, "col_dx": [0.0, 9.5, 22.0, 30.5, 52.0], "right_dx": 75.0,
         "title": "POST-TENSION TENDON SCHEDULE", "check_note": None, "legend": [], "sections": {"X": "X / EX DIRECTION", "Y": "Y DIRECTION"}, **d.get("schedule", {})}
    x0, top, rh = S["x0"], S["top"], S["row_h"]
    cx = [x0 + k for k in S["col_dx"]]; xr = x0 + S["right_dx"]
    body = [(S["sections"]["X"], None)] + [((t["group"], t["mark"], t["strands"], f"{t['first']}-{t['last']}", f"{t['length_m']:.2f}"), t) for t in X_t]
    body += [(S["sections"]["Y"], None)] + [((t["group"], t["mark"], t["strands"], f"{t['first']}-{t['last']}", f"{t['length_m']:.2f}"), t) for t in Y_t]
    txt(S["title"], x0, top + 2.5, "TEXT_2.5", "S-ANNO-TEXT")
    if S["check_note"]:
        txt(f"({S['check_note']})", x0, top - 0.5, "TEXT_2.0", "S-ANNO-TEXT")
    ytab = top - 4.0
    nrows = 1 + len(body); ybot = ytab - rh * nrows
    for i in range(nrows + 1):
        ln((x0 - 1.0, ytab - rh * i), (xr + 1.0, ytab - rh * i), "S-ANNO-TABLE")
    for xx in [x0 - 1.0] + cx[1:] + [xr + 1.0]:
        ln((xx, ytab), (xx, ybot), "S-ANNO-TABLE")
    for xx, h in zip(cx, ["GRP", "MARK", "STR", "STRAND NOS.", "LENGTH m"]):
        txt(h, xx + 0.8, ytab - rh / 2, "TEXT_2.0", "S-ANNO-TEXT", A.MIDDLE_LEFT)
    for i, (r, _) in enumerate(body, 1):
        yc = ytab - rh * (i + 0.5)
        if isinstance(r, str):
            txt(r, cx[0] + 0.8, yc, "TEXT_2.0", "S-ANNO-TEXT", A.MIDDLE_LEFT)
        else:
            for xx, v in zip(cx, [str(r[0]), r[1], str(r[2]), r[3], r[4]]):
                txt(v, xx + 0.8, yc, "TEXT_2.0", "S-ANNO-TEXT", A.MIDDLE_LEFT)
    ky = ybot - 5.0
    for k, s in enumerate(S["legend"]):
        txt(s, x0, ky - 3.4 * k, "TEXT_2.0", "S-ANNO-TEXT")

    # notes
    N = d.get("notes", {"x": 12.0, "y": 82.0, "pitch": 3.6, "lines": []})
    yy = N["y"]
    for it in N["lines"]:
        if isinstance(it, dict) and "gap" in it:
            yy -= N["pitch"] * it["gap"]
        else:
            txt(it if isinstance(it, str) else it["text"], N["x"], yy, "TEXT_2.0", "S-ANNO-TEXT")
            yy -= N["pitch"]

    out.mkdir(parents=True, exist_ok=True)
    path = out / f"{d['file_name']}.dxf"
    P.doc.saveas(path)
    with open(out / f"{d['file_name']}_schedule.csv", "w", newline="") as fh:
        w = csv.writer(fh); w.writerow(["group", "mark", "direction", "strands", "first_strand", "last_strand", "length_m"])
        for t in X_t + Y_t:
            w.writerow([t["group"], t["mark"], t["dir"], t["strands"], t["first"], t["last"], f"{t['length_m']:.2f}"])
    return path


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True); ap.add_argument("--standards", required=True); ap.add_argument("--out", required=True)
    ap.add_argument("--no-pdf", action="store_true")
    ns = ap.parse_args(argv)
    d = json.load(open(ns.data, encoding="utf-8"))
    try:
        p = build(d, pathlib.Path(ns.standards), pathlib.Path(ns.out))
    except (PlanDataError, bs.MissingInput) as e:
        print(f"BUILD STOPPED: {e}", file=sys.stderr)
        return 1
    pdf = None
    if not ns.no_pdf:
        pdf = pathlib.Path(ns.out) / f"{d['file_name']}_preview.pdf"
        bs.plot_pdf([p], pdf)
    print(json.dumps({"dxf": str(p), "preview_pdf": str(pdf) if pdf else None, "schedule_csv": str(pathlib.Path(ns.out) / f"{d['file_name']}_schedule.csv"),
                      "note": "DXF written by script (not DWG); PDF is a script-rendered preview; not approved"}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
