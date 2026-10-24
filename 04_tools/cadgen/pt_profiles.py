#!/usr/bin/env python3
"""Data-driven PT tendon PROFILE sheets (BONDED post-tensioning): section outline + tendon curve + station labels -> A3 DXF, preview PDF, station CSV.

Usage:
  python 04_tools/cadgen/pt_profiles.py --data <pt_profile_data.json> --standards 01_standards --out <dir> [--no-pdf]

Data file (schema: .claude/skills/pt-drawings/references/pt-profile-data.md), per tendon mark:
  stations : [{u: chainage cm, sp: spacing from previous station cm, h: tendon height above soffit cm}, ...]
  section  : {soffit: [[u0, u1, z_cm], ...], top: [[u0, u1, z_cm], ...]}     (steps in the section)
  curve    : [[u, z_cm], ...]   optional; when absent the curve is the polyline soffit(u) + h through the stations
  supports : [u, ...]           optional support lines
Nothing is computed that is not in the data: the generator draws what it is given. A profile whose station spacings do not add up to
the last chainage stops the build. This script contains no project values.
Output is a DXF written by script (not a DWG) and a rendered preview (not a CTB plot). Nothing here is approved.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import pathlib
import sys

import numpy as np
from ezdxf.enums import TextEntityAlignment as A

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import build_sheets as bs  # noqa: E402
import pt_plan  # noqa: E402

X0, X1 = 12.0, 408.0          # usable width of the sheet
Y_TOP, Y_BOT = 247.0, 46.0    # usable height for profile blocks (notes below)
HDR, GAP = 4.2, 3.0
TIER_A, TIER_B = 5.4, 6.6     # label tier pitch above (spacing) and below (height)
MIN_PITCH = 2.5               # minimum x pitch between rotated 2.0 mm labels in one tier


class ProfileDataError(Exception):
    pass


def tiers(xs, pitch=MIN_PITCH):
    last, out = [], []
    for x in xs:
        for k, lx in enumerate(last):
            if x - lx >= pitch:
                last[k] = x; out.append(k); break
        else:
            last.append(x); out.append(len(last) - 1)
    return out


def soffit_at(levels, u):
    for u0, u1, z in levels:
        if u0 - 1e-6 <= u <= u1 + 1e-6:
            return z
    return levels[-1][2] if u > levels[-1][1] else levels[0][2]


def check_profile(name: str, p: dict) -> None:
    st = p.get("stations") or []
    if len(st) < 2 or "section" not in p:
        raise ProfileDataError(f"{name}: needs stations (>= 2) and section")
    tot = sum(float(s.get("sp") or 0) for s in st)
    if abs(tot - st[-1]["u"]) > 1.0:
        raise ProfileDataError(f"{name}: station spacings add to {tot:.1f} cm but the last chainage is {st[-1]['u']:.1f} cm - not guessed")
    for key in ("soffit", "top"):
        if not p["section"].get(key):
            raise ProfileDataError(f"{name}: section.{key} missing")


def prep(name, p, hs, vs):
    check_profile(name, p)
    st = p["stations"]
    ul = st[-1]["u"]
    ls = [list(x) for x in p["section"]["soffit"]]; lt = [list(x) for x in p["section"]["top"]]
    if "curve" in p and p["curve"]:
        curve = np.array(p["curve"], float)
    else:
        curve = np.array([[s["u"], soffit_at(ls, s["u"]) + s["h"]] for s in st], float)
    xs = [s["u"] * hs for s in st]
    ta = tiers(xs); tb = tiers(xs)
    zmax = max(l[2] for l in lt); zmin = min(l[2] for l in ls)
    nA, nB = max(ta) + 1, max(tb) + 1
    hsec = (zmax - zmin) * vs
    H = HDR + 2.6 + nA * TIER_A + hsec + nB * TIER_B + GAP
    return dict(name=name, p=p, ul=ul, ls=ls, lt=lt, curve=curve, ta=ta, tb=tb, nA=nA, nB=nB, zmin=zmin, zmax=zmax, hsec=hsec, H=H, W=max(ul * hs + 6.0, 52.0))


def pack(blocks):
    rows, cur, w = [], [], 0.0
    for b in blocks:
        if cur and w + b["W"] > X1 - X0:
            rows.append(cur); cur, w = [], 0.0
        cur.append(b); w += b["W"]
    rows.append(cur)
    return rows, sum(max(b["H"] for b in row) for row in rows)


def txt(msp, s, x, y, style="TEXT_2.0", layer="S-ANNO-TEXT", align=A.LEFT, rot=0.0):
    e = bs.txt(msp, s, x, y, style, layer, align)
    if rot:
        e.dxf.rotation = rot
    return e


def draw_block(msp, b, x0, ytop, hs, vs, D):
    name, p = b["name"], b["p"]
    st = p["stations"]
    L = {"profile": "PROFILE L = ", "plan": "PLAN ", "verify": "  - VERIFY", "plan_offset_m": 0.5, **D.get("labels", {})}
    ys = ytop - HDR + 1.0
    pl = D.get("plan_lengths", {}).get(name)
    plan_txt = L["plan"] + ", ".join(sorted({f"{Lx:.2f}" for _, Lx in pl})) + " m" if pl else L["plan"] + "-"
    diff = bool(pl) and all(abs(b["ul"] / 100 - (Lx - L["plan_offset_m"])) > 0.15 for _, Lx in pl)
    txt(msp, name, x0, ys + 0.6, "TEXT_3.5")
    txt(msp, f"{L['profile']}{b['ul'] / 100:.2f} m", x0 + 3.2 * len(name) + 3.0, ys + 1.6)
    txt(msp, plan_txt + (L["verify"] if diff else ""), x0 + 3.2 * len(name) + 3.0, ys - 1.0)
    ysec_top = ytop - HDR - 2.6 - b["nA"] * TIER_A
    dat = ysec_top - b["hsec"] - b["zmin"] * vs
    X = lambda u: x0 + u * hs
    Y = lambda z: dat + z * vs
    pts = []
    for u0, u1, z in b["ls"]:
        pts += [(X(u0), Y(z)), (X(u1), Y(z))]
    for u0, u1, z in reversed(b["lt"]):
        pts += [(X(u1), Y(z)), (X(u0), Y(z))]
    clean = [pts[0]]
    for q in pts[1:]:
        if abs(q[0] - clean[-1][0]) > 1e-6 or abs(q[1] - clean[-1][1]) > 1e-6:
            clean.append(q)
    msp.add_lwpolyline(clean, close=True, dxfattribs={"layer": "S-CONC-OUTLINE"})
    for us in p.get("supports", []):
        if 0 < us < b["ul"]:
            msp.add_line((X(us), Y(b["zmin"]) - 1.0), (X(us), Y(b["zmax"]) + 1.0), dxfattribs={"layer": "S-GRID"})
    msp.add_lwpolyline([(X(u), Y(z)) for u, z in b["curve"]], dxfattribs={"layer": "S-PT-TENDON"})
    cu, cz = b["curve"][:, 0], b["curve"][:, 1]
    for s in st:
        zz = float(np.interp(s["u"], cu, cz)); px, py = X(s["u"]), Y(zz)
        for d in ((0.6, 0.6), (0.6, -0.6)):
            msp.add_line((px - d[0], py - d[1]), (px + d[0], py + d[1]), dxfattribs={"layer": "S-DETAIL-THIN"})
    ytop_sec = Y(b["zmax"]); ybot_sec = Y(b["zmin"])
    for s, ta, tb in zip(st, b["ta"], b["tb"]):
        x = X(s["u"])
        txt(msp, f"{int(s['sp'] or 0)}" if s is not st[0] else "0", x + 1.0, ytop_sec + 1.0 + ta * TIER_A, align=A.LEFT, rot=90)
        txt(msp, f"{s['h']:.1f}", x + 1.0, ybot_sec - 1.0 - tb * TIER_B, align=A.RIGHT, rot=90)
    return dat


def build_sheet(sh, D, standards, out, den):
    doc = bs.new_doc(pt_plan.load_layers(standards)); bs.define_titleblock(doc); msp = doc.modelspace()
    vs = 10.0 / D.get("v_den", 25)                    # mm of paper per cm of section height (V 1:25 -> 0.4)
    hs = 10.0 / den
    tbv = {**D["title_block"], "DRAWING_NAME": sh["title"], "SCALE": f"H 1:{den} / V 1:{D.get('v_den', 25)}"}
    bs.place_titleblock(msp, tbv)
    for t in sh.get("titles", []):
        txt(msp, t["text"].replace("{den}", str(den)), t["x"], t["y"], t.get("style", "TEXT_2.0"))
    blocks = [prep(n, D["profiles"][n], hs, vs) for n in sh["marks"]]
    rows, tot = pack(blocks)
    y = Y_TOP
    for row in rows:
        rh = max(b["H"] for b in row); x = X0
        for b in row:
            draw_block(msp, b, x + 1.0, y, hs, vs, D); x += b["W"]
        y -= rh
    N = D.get("notes", {"x": 12, "y": 40.0, "pitch": 3.6, "lines": []})
    for i, s in enumerate(N["lines"]):
        txt(msp, s, N["x"], N["y"] - N["pitch"] * i)
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"{D['file_prefix']}_{sh['number']}.dxf"
    doc.saveas(path)
    return path, y, tot


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True); ap.add_argument("--standards", required=True); ap.add_argument("--out", required=True)
    ap.add_argument("--no-pdf", action="store_true")
    ns = ap.parse_args(argv)
    D = json.load(open(ns.data, encoding="utf-8")); out = pathlib.Path(ns.out); std = pathlib.Path(ns.standards)
    paths = []
    try:
        for sh in D["sheets"]:
            chosen = None
            for den in sh.get("den_candidates", [200, 250, 300, 350, 400]):
                hs = 10.0 / den; vs = 10.0 / D.get("v_den", 25)
                rows, tot = pack([prep(n, D["profiles"][n], hs, vs) for n in sh["marks"]])
                chosen = den
                if tot <= Y_TOP - Y_BOT:
                    break
            else:
                raise ProfileDataError(f"sheet {sh['number']}: profiles do not fit on one A3 sheet at the smallest scale - split the sheet")
            p, yend, tot = build_sheet(sh, D, std, out, chosen)
            paths.append(p); print(sh["number"], "scale 1:%d" % chosen, "rows", len(rows), "height used", round(tot, 1), "of", Y_TOP - Y_BOT)
    except (ProfileDataError, bs.MissingInput, KeyError) as e:
        print(f"BUILD STOPPED: {e}", file=sys.stderr)
        return 1
    pdf = None
    if not ns.no_pdf:
        pdf = out / f"{D['file_prefix']}_preview.pdf"
        bs.plot_pdf(paths, pdf)
    with open(out / f"{D['file_prefix']}_stations.csv", "w", newline="") as fh:
        w = csv.writer(fh); w.writerow(["mark", "station_no", "chainage_cm", "spacing_from_previous_cm", "height_above_soffit_cm"])
        for sh in D["sheets"]:
            for n in sh["marks"]:
                for i, s in enumerate(D["profiles"][n]["stations"], 1):
                    w.writerow([n, i, int(s["u"]), int(s["sp"] or 0), s["h"]])
    print(json.dumps({"dxf": [str(p) for p in paths], "pdf": str(pdf) if pdf else None, "note": "DXF written by script (not DWG); preview is not a CTB plot; not approved"}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
