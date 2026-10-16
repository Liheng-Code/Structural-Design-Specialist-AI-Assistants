#!/usr/bin/env python3
"""ONE-OFF converter: the 2F redraft (hard-coded tables + heuristics on PDF-extracted lines) -> explicit pt_plan_data JSON.

Usage: python convert_plan_to_pt_data.py --plan plan_2F_PT.json --out pt_plan_data_2F.json
It runs the redraft script's own detection rules once and writes the result as plain data, so tools/cadgen/pt_plan.py
(which has no project values and no PDF heuristics) can redraw the same sheet. Nothing is added or corrected here.
"""
import argparse, json, pathlib, sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent / "tools" / "cadgen"))
import redraft_2f_pt as r  # noqa: E402  (the original redraft; supplies the transcribed tables)
from pt_plan import cluster_boxes  # noqa: E402


def convert(plan: dict) -> dict:
    SC = r.SC
    d = {"schema": "pt_plan_data/1", "scale_den": SC, "origin_paper_mm": [r.GX0, r.P0], "file_name": "2F_PT_Layout_Plan_REDRAFT",
         "title_block": {"PROJ_REFERENCE": "TBC", "DRAWING_NAME": "2F PT LAYOUT PLAN (REDRAFT)", "REVISION": "TBC", "DRAWN_BY": "CLAUDE (DRAFT)",
                         "DRAWING_NUMBER": "TBC", "DRAWING_STAGE": "REDRAFT FOR REVIEW", "CLIENT": "TBC", "SCALE": "1:200", "ISSUE_DATE": "16-OCT-2026"},
         "titles": [{"text": "2F POST-TENSION LAYOUT PLAN (REDRAFT)  -  LEVEL +3.100", "x": 12, "y": 257.5, "style": "TEXT_3.5"},
                    {"text": "SCALE 1:200  |  NET AREA = 829.05 SQ.M. (AS SOURCE)  |  REDRAFT FOR REVIEW - NOT FOR CONSTRUCTION", "x": 12, "y": 252.0, "style": "TEXT_2.0"}],
         "grid": {"x": [{"name": str(i), "pos": x} for i, x in enumerate(r.GRID_X, 1)], "y": [{"name": k, "pos": v} for k, v in r.GRID_Y.items()]}}
    out = [{"pts": pts, "closed": bool(cl), "layer": "S-CONC-OUTLINE"} for pts, cl in plan["red"]]
    out += [{"pts": pts, "closed": bool(cl), "layer": "S-CONC-DROP"} for pts, cl in plan["cyan"]]
    d["outlines"] = out
    boxes = [b for b in cluster_boxes(plan["redhatch"]) if (b[2] - b[0]) > 300 and (b[3] - b[1]) > 300]
    d["blockouts"] = boxes
    d["columns"] = [{"tag": tag, "size": size, "x": x, "y": y} for tag, size, pts in r.COLUMNS for (x, y) in pts]
    labels = []
    # lifts (cross boxes) and stairs (labels) - the redraft's coordinate rules, applied once
    def rng(pts, k): return min(q[k] for q in pts), max(q[k] for q in pts)
    zone = lambda pts: 21000 < min(p[1] for p in pts) and max(p[1] for p in pts) < 24500
    lifts = sorted([pts for pts, cl in plan["red"] if cl and len(pts) in (4, 5) and zone(pts) and 1500 < (rng(pts, 0)[1] - rng(pts, 0)[0]) < 3000],
                   key=lambda p: rng(p, 0)[0])
    d["cross_boxes"] = []
    for i, pts in enumerate(lifts[:4]):
        (x0, x1), (y0, y1) = rng(pts, 0), rng(pts, 1)
        d["cross_boxes"].append({"bbox": [x0, y0, x1, y1], "label": r.LIFTS[i], "label_dy_mm": -3.0})
    stairs = sorted([pts for pts, cl in plan["red"] if cl and len(pts) in (4, 5) and zone(pts) and 3000 <= (rng(pts, 0)[1] - rng(pts, 0)[0]) < 8000],
                    key=lambda p: rng(p, 0)[0])
    for i, pts in enumerate(stairs[:2]):
        (x0, x1), (y0, y1) = rng(pts, 0), rng(pts, 1)
        labels.append({"text": f"ST-{i + 1}", "x": (x0 + x1) / 2, "y": (y0 + y1) / 2, "align": "MIDDLE_CENTER"})
    d["tendon_lines"] = [pts for pts, t in plan["green"] if max(p[1] for p in pts) >= 3000]
    # tendons: Y anchors from the vertical source stubs, paired left-to-right with the transcribed table (as the redraft did)
    verts = []
    for pts, t in plan["green"]:
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        if max(xs) - min(xs) < 30 and max(ys) - min(ys) > 7000:
            verts.append((sum(xs) / len(xs), min(ys)))
    verts.sort()
    assert len(verts) == len(r.Y_TENDONS)
    ten = []
    for (g, mark, n, a, b, L, ym, side) in r.X_TENDONS:
        ten.append({"group": g, "mark": mark, "dir": "X", "strands": n, "first": a, "last": b, "length_m": L, "y": ym, "side": side})
    for (g, mark, n, a, b, L), (vx, vy) in zip(r.Y_TENDONS, verts):
        ten.append({"group": g, "mark": mark, "dir": "Y", "strands": n, "first": a, "last": b, "length_m": L, "anchor": [vx, vy]})
    d["tendons"] = ten
    d["tags_below"] = {"y_model": 3300, "y_off_mm": -3.0, "pitch_mm": 3.2}
    for x, y in ((24000, 17600), (5300, 10400), (42700, 10400)):
        for k, line in enumerate(["PTS. 0.25 M.THK.", "SDL=250 KSM.", "LL=500 KSM."]):
            labels.append({"text": line, "x": x, "y": y, "dy_mm": -k * 3.0, "align": "MIDDLE_CENTER"})
    for pts, cl in plan["cyan"]:
        if not cl:
            continue
        (x0, x1), (y0, y1) = rng(pts, 0), rng(pts, 1); w, h = x1 - x0, y1 - y0
        if w > 9000:
            labels.append({"text": "BB2", "x": (x0 + x1) / 2, "y": y0, "dy_mm": 2.0, "align": "MIDDLE_CENTER"})
        elif h > 5000 and w < 2500:
            labels.append({"text": "BB1", "x": (x0 + x1) / 2, "y": (y0 + y1) / 2, "align": "MIDDLE_CENTER", "rot": 90})
        elif y1 > 22000:
            labels.append({"text": "DP", "x": x0, "y": y0, "dx_mm": 1.2, "dy_mm": 1.2, "align": "LEFT"})
        else:
            labels.append({"text": "DP", "x": x0, "y": y1, "dx_mm": 1.2, "dy_mm": -3.0, "align": "LEFT"})
    for tag, size, pts in r.COLUMNS:
        for (x, y) in pts:
            if tag == "C1" and y == 24300:
                continue
            labels.append({"text": tag, "x": x, "y": y, "dx_mm": size / 2 / SC + 0.6, "dy_mm": size / 2 / SC + 0.4, "align": "LEFT"})
    d["labels"] = labels
    d["level_marks"] = [{"x": 23000, "y": 12500, "text": "+3.100"}]
    d["dims"] = [{"dir": "h", "ref_model": 0, "offset_mm": -22.0, "positions": r.GRID_X, "labels": ["10000", "9000", "9000", "9000", "10000"]},
                 {"dir": "h", "ref_model": 0, "offset_mm": -28.0, "positions": [0, 47000], "labels": ["47000"]},
                 {"dir": "v", "paper": 26.0, "positions": [0, 4300, 6300, 14800, 19800, 24300], "labels": ["4300", "2000", "8500", "5000", "4500"]},
                 {"dir": "h", "ref_model": 16404, "offset_mm": 2.0, "positions": [8498, 11500], "labels": ["3000"]},
                 {"dir": "v", "ref_model": 11500, "offset_mm": 3.0, "positions": [13302, 16404], "labels": ["3100"]}]
    d["schedule"] = {"check_note": r.CHECK_NOTE, "legend": ["STR: 4 = SQUARE, 3 = TRIANGLE, 2 = CIRCLE", "LABEL LENGTH = DRAWN LENGTH + ~0.5 m (SOURCE)"]}
    d["notes"] = {"x": 12.0, "y": 82.0, "pitch": 3.6, "lines": list(r.REDRAFT_NOTES) + [{"gap": 0.6}] + list(r.SOURCE_NOTES)}
    return d


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--plan", required=True); ap.add_argument("--out", required=True)
    ns = ap.parse_args()
    data = convert(json.load(open(ns.plan)))
    json.dump(data, open(ns.out, "w", encoding="utf-8"), indent=1)
    print("written", ns.out, "tendons:", len(data["tendons"]), "labels:", len(data["labels"]))
