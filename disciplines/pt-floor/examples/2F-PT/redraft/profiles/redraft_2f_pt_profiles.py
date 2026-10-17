#!/usr/bin/env python3
"""Redraft of the 2F post-tension tendon PROFILES (source: Success Design & Build, sheet 16 of 50, Rev 01, 22-AUG-2023).

Data (profiles_2F_PT.json) was extracted from the source PDF: station spacings and tendon heights are the source's own
labels (read from its vector text); section outlines and tendon curves are traced from the source geometry
(+/- 1 cm vertical, +/- 5 cm along the tendon). Nothing is designed or invented; unreadable items are not drawn.

Usage: python redraft_2f_pt_profiles.py --profiles profiles_2F_PT.json --standards <Structural-Drawing-Standards> --out <dir>
Output: two DXF sheets (X/EX and Y direction) + a combined script-rendered preview PDF + a CSV of all stations.
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
import redraft_2f_pt as r  # noqa: E402

VS = 0.4                      # vertical scale 1:25 -> mm per cm of section / tendon height
X0, X1 = 12.0, 408.0          # usable width of the sheet
Y_TOP, Y_BOT = 247.0, 46.0    # usable height for profile blocks (notes below)
HDR, GAP = 4.2, 3.0
TIER_A, TIER_B = 5.4, 6.6     # label tier pitch above (spacing, 3 digits) and below (height, 4 chars)
MIN_PITCH = 2.5               # minimum x pitch between rotated 2.0 mm labels in one tier
MARK_ORDER = {"X": ["X1", "X2", "X3", "X4", "X5", "X6", "X7", "X8", "EX1", "EX2", "EX3", "EX4"],
              "Y": ["Y1", "Y1A", "Y2", "Y3", "Y4", "Y5", "Y6", "Y7", "Y8", "Y9", "Y9A", "Y10", "Y11", "Y12", "Y13", "Y14", "Y15", "Y16", "Y17", "Y17A"]}


def plan_lengths():
    d = {}
    for g, mark, n, a, b, L in r.Y_TENDONS:
        d.setdefault(mark, []).append((g, L))
    for g, mark, n, a, b, L, yy, side in r.X_TENDONS:
        d.setdefault(mark, []).append((g, L))
    return d


def levels(u, z, tol=0.8):
    segs, cur = [], [(u[0], z[0])]
    for uu, zz in zip(u[1:], z[1:]):
        lv = float(np.median([q[1] for q in cur]))
        if abs(zz - lv) <= tol:
            cur.append((uu, zz))
        else:
            segs.append([cur[0][0], cur[-1][0], float(np.median([q[1] for q in cur]))]); cur = [(uu, zz)]
    segs.append([cur[0][0], cur[-1][0], float(np.median([q[1] for q in cur]))])
    out = []
    for s in segs:
        if out and abs(s[2] - out[-1][2]) <= tol:
            out[-1][1] = s[1]
        else:
            out.append(s)
    changed = True
    while changed and len(out) > 1:               # absorb segments shorter than 12 cm into the longer neighbour
        changed = False
        for i, sg in enumerate(out):
            if sg[1] - sg[0] < 12:
                j = i - 1 if (i > 0 and (i == len(out) - 1 or out[i - 1][1] - out[i - 1][0] >= out[i + 1][1] - out[i + 1][0])) else i + 1
                lo, hi = sorted((i, j)); out[lo] = [out[lo][0], out[hi][1], out[j][2]]; del out[hi]; changed = True; break
    for i in range(len(out) - 1):                # steps sit midway between samples; snap to 5 cm
        m = round((out[i][1] + out[i + 1][0]) / 2 / 5) * 5
        out[i][1] = out[i + 1][0] = m
    return out


def rdp(P, eps):
    P = np.asarray(P, float)
    if len(P) < 3:
        return P
    a, b = P[0], P[-1]; d = b - a; n = math.hypot(*d)
    dist = np.hypot(*(P - a).T) if n == 0 else np.abs(d[0] * (P[:, 1] - a[1]) - d[1] * (P[:, 0] - a[0])) / n
    i = int(dist.argmax())
    if dist[i] > eps:
        return np.vstack([rdp(P[:i + 1], eps)[:-1], rdp(P[i:], eps)])
    return np.vstack([a, b])


def tiers(xs, pitch=MIN_PITCH):
    last, out = [], []
    for x in xs:
        for k, lx in enumerate(last):
            if x - lx >= pitch:
                last[k] = x; out.append(k); break
        else:
            last.append(x); out.append(len(last) - 1)
    return out


def prep(name, p, hs):
    st = p["stations"]; g = p["geo"]
    ul = st[-1]["u"]
    u = np.array(g["u"]); zs = np.array(g["zs"]); zt = np.array(g["zt"]); zc = np.array(g["zc"])
    o = np.argsort(u); u, zs, zt, zc = u[o], zs[o], zt[o], zc[o]
    from scipy.signal import medfilt
    zs = medfilt(zs, 9); zt = medfilt(zt, 9)
    ls = levels(u, np.round(zs)); lt = levels(u, np.round(zt))
    ls[0][0] = lt[0][0] = 0.0; ls[-1][1] = lt[-1][1] = ul
    curve = rdp(np.column_stack([np.clip(u, 0, ul), zc]), 0.3)
    xs = [s["u"] * hs for s in st]
    ta = tiers(xs); tb = tiers(xs)
    zmax = max(l[2] for l in lt); zmin = min(l[2] for l in ls)
    nA, nB = max(ta) + 1, max(tb) + 1
    hsec = (zmax - zmin) * VS
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


def draw_block(msp, b, x0, ytop, hs, plan):
    name, p = b["name"], b["p"]
    st = p["stations"]
    # header
    ys = ytop - HDR + 1.0
    pl = plan.get(name)
    plan_txt = "PLAN LABEL: " + ", ".join(sorted({f"{L:.2f}" for _, L in pl})) + " m" if pl else "PLAN LABEL: -"
    diff = bool(pl) and all(abs(b["ul"] / 100 - (L - 0.5)) > 0.15 for _, L in pl)
    r.txt(msp, name, x0, ys + 0.6, "TEXT_3.5", "S-ANNO-TEXT")
    r.txt(msp, f"SHEET 16 PROFILE L = {b['ul'] / 100:.2f} m", x0 + 3.2 * len(name) + 3.0, ys + 1.6, "TEXT_2.0", "S-ANNO-TEXT")
    r.txt(msp, plan_txt.replace("PLAN LABEL: ", "PLAN ") + ("  - VERIFY" if diff else ""), x0 + 3.2 * len(name) + 3.0, ys - 1.0, "TEXT_2.0", "S-ANNO-TEXT")
    ysec_top = ytop - HDR - 2.6 - b["nA"] * TIER_A          # top of tallest section
    dat = ysec_top - b["hsec"] - b["zmin"] * VS        # y of z = 0
    X = lambda u: x0 + u * hs
    Y = lambda z: dat + z * VS
    # outline (soffit left->right, end cap, top right->left)
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
    # supports (as drawn in the source: grey lines across the section)
    for us in p.get("supports", []):
        if 0 < us < b["ul"]:
            msp.add_line((X(us), Y(b["zmin"]) - 1.0), (X(us), Y(b["zmax"]) + 1.0), dxfattribs={"layer": "S-GRID"})
    # tendon curve and station ticks
    msp.add_lwpolyline([(X(u), Y(z)) for u, z in b["curve"]], dxfattribs={"layer": "S-PT-TENDON"})
    cu, cz = b["curve"][:, 0], b["curve"][:, 1]
    for s in st:
        zz = float(np.interp(s["u"], cu, cz)); px, py = X(s["u"]), Y(zz)
        for d in ((0.6, 0.6), (0.6, -0.6)):
            msp.add_line((px - d[0], py - d[1]), (px + d[0], py + d[1]), dxfattribs={"layer": "S-DETAIL-THIN"})
    # labels: spacing above (start at bottom, reads upward), heights below (end at top, hangs down)
    ytop_sec = Y(b["zmax"]); ybot_sec = Y(b["zmin"])
    for s, ta, tb in zip(st, b["ta"], b["tb"]):
        x = X(s["u"])
        r.txt(msp, f"{int(s['sp'] or 0)}" if s is not st[0] else "0", x + 1.0, ytop_sec + 1.0 + ta * TIER_A, "TEXT_2.0", "S-ANNO-TEXT", A.LEFT, rot=90)
        r.txt(msp, f"{s['h']:.1f}", x + 1.0, ybot_sec - 1.0 - tb * TIER_B, "TEXT_2.0", "S-ANNO-TEXT", A.RIGHT, rot=90)
    return dat


def build_sheet(kind, profiles, plan, standards, out, hs_den, title, number):
    layers = r.layers_with_extensions(standards)
    doc = bs.new_doc(layers); bs.define_titleblock(doc); msp = doc.modelspace()
    bs.place_titleblock(msp, {"PROJ_REFERENCE": "TBC", "DRAWING_NAME": title, "REVISION": "TBC", "DRAWN_BY": "CLAUDE (DRAFT)", "DRAWING_NUMBER": "TBC",
                              "DRAWING_STAGE": "REDRAFT FOR REVIEW", "CLIENT": "TBC", "SCALE": f"H 1:{hs_den} / V 1:25", "ISSUE_DATE": "16-OCT-2026"})
    r.txt(msp, f"{title}  -  SOURCE SHEET 16", 12, 257.5, "TEXT_3.5")
    r.txt(msp, f"SCALE: ALONG TENDON 1:{hs_den}, HEIGHTS 1:25 (DISTORTED)  |  REDRAFT FOR REVIEW - NOT FOR CONSTRUCTION", 12, 252.0, "TEXT_2.0")
    hs = 10.0 / hs_den        # mm per cm along the tendon
    blocks = [prep(n, profiles[n], hs) for n in MARK_ORDER[kind]]
    rows, tot = pack(blocks)
    y = Y_TOP
    for row in rows:
        rh = max(b["H"] for b in row); x = X0
        for b in row:
            draw_block(msp, b, x + 1.0, y, hs, plan); x += b["W"]
        y -= rh
    notes = [
        "NOTES:",
        "1. PROFILES REDRAFTED FROM SOURCE SHEET 16 (SUCCESS DESIGN & BUILD, REV 01, 22-AUG-2023). NO DESIGN CHANGE. FOR REVIEW ONLY.",
        "2. LABELS: ABOVE = DISTANCE FROM PREVIOUS STATION (cm); BELOW = TENDON HEIGHT ABOVE SOFFIT (cm). TRANSCRIBED FROM SOURCE - VERIFY.",
        "3. SECTION OUTLINE AND TENDON CURVE ARE TRACED FROM SOURCE GEOMETRY (+/- 1 cm VERTICAL, +/- 5 cm ALONG). LINES ACROSS SECTION = SUPPORT LINES AS DRAWN.",
        "4. NOT REDRAWN: GRID REFERENCE BUBBLES, SPAN-LENGTH AND SECTION-THICKNESS DIMENSION LABELS, STRESSING / DEAD-END SYMBOLS. TBC.",
        "5. 'VERIFY' = PROFILE LENGTH (SUM OF STATION SPACINGS) IS NOT PLAN LABEL LENGTH - 0.5 m (SOURCE PLAN LABEL = DRAWN LENGTH + ~0.5 m). TO BE CHECKED WITH THE DESIGNER.",
    ]
    ny = Y_BOT - 6 if y > Y_BOT - 6 else y - 6
    for i, s in enumerate(notes):
        r.txt(msp, s, 12, 40.0 - 3.6 * i, "TEXT_2.0", "S-ANNO-TEXT")
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"2F_PT_Profiles_{number}_REDRAFT.dxf"
    doc.saveas(path)
    return path, y, tot


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--profiles", required=True); ap.add_argument("--standards", required=True); ap.add_argument("--out", required=True)
    ns = ap.parse_args(argv)
    P = json.load(open(ns.profiles)); plan = plan_lengths(); out = pathlib.Path(ns.out); std = pathlib.Path(ns.standards)
    paths = []
    for kind, title, number in (("X", "2F PT TENDON PROFILES - X / EX DIRECTION (REDRAFT)", "X"), ("Y", "2F PT TENDON PROFILES - Y DIRECTION (REDRAFT)", "Y")):
        for den in (200, 250, 300, 350, 400):
            hs = 10.0 / den
            rows, tot = pack([prep(n, P[n], hs) for n in MARK_ORDER[kind]])
            if tot <= Y_TOP - Y_BOT:
                break
        p, yend, tot = build_sheet(kind, P, plan, std, out, den, title, number)
        paths.append(p); print(kind, "scale 1:%d" % den, "rows", len(rows), "height used", round(tot, 1), "of", Y_TOP - Y_BOT)
    pdf = out / "2F_PT_Profiles_REDRAFT_preview.pdf"
    bs.plot_pdf(paths, pdf)
    with open(out / "2F_PT_Profiles_stations_TRANSCRIBED.csv", "w", newline="") as fh:
        w = csv.writer(fh); w.writerow(["mark", "station_no", "chainage_cm", "spacing_from_previous_cm", "height_above_soffit_cm"])
        for kind in "XY":
            for n in MARK_ORDER[kind]:
                for i, s in enumerate(P[n]["stations"], 1):
                    w.writerow([n, i, int(s["u"]), int(s["sp"] or 0), s["h"]])
    print(json.dumps({"dxf": [str(p) for p in paths], "pdf": str(pdf)}, indent=1))


if __name__ == "__main__":
    main()
