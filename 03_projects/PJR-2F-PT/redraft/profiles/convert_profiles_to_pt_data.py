#!/usr/bin/env python3
"""ONE-OFF converter: the 2F profile redraft data (traced geometry in profiles_2F_PT.json) -> explicit pt_profile_data JSON.

Usage: python convert_profiles_to_pt_data.py --profiles profiles_2F_PT.json --out pt-profile-data.json
Runs the redraft's own smoothing (median filter, step detection, curve simplification) once and stores the RESULT as plain
section steps and a tendon curve, so 04_tools/cadgen/pt_profiles.py needs no tracing code. Nothing is added or corrected here.
"""
import argparse, json, pathlib, sys
import numpy as np
from scipy.signal import medfilt

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent)); sys.path.insert(0, str(HERE.parents[3] / "04_tools" / "cadgen"))
import redraft_2f_pt as r  # noqa: E402
import redraft_2f_pt_profiles as old  # noqa: E402

NOTES = [
    "NOTES:",
    "1. PROFILES REDRAFTED FROM SOURCE SHEET 16 (SUCCESS DESIGN & BUILD, REV 01, 22-AUG-2023). NO DESIGN CHANGE. FOR REVIEW ONLY.",
    "2. LABELS: ABOVE = DISTANCE FROM PREVIOUS STATION (cm); BELOW = TENDON HEIGHT ABOVE SOFFIT (cm). TRANSCRIBED FROM SOURCE - VERIFY.",
    "3. SECTION OUTLINE AND TENDON CURVE ARE TRACED FROM SOURCE GEOMETRY (+/- 1 cm VERTICAL, +/- 5 cm ALONG). LINES ACROSS SECTION = SUPPORT LINES AS DRAWN.",
    "4. NOT REDRAWN: GRID REFERENCE BUBBLES, SPAN-LENGTH AND SECTION-THICKNESS DIMENSION LABELS, STRESSING / DEAD-END SYMBOLS. TBC.",
    "5. 'VERIFY' = PROFILE LENGTH (SUM OF STATION SPACINGS) IS NOT PLAN LABEL LENGTH - 0.5 m (SOURCE PLAN LABEL = DRAWN LENGTH + ~0.5 m). TO BE CHECKED WITH THE DESIGNER.",
]


def convert(P: dict) -> dict:
    prof = {}
    for kind in "XY":
        for n in old.MARK_ORDER[kind]:
            p = P[n]; st = p["stations"]; g = p["geo"]; ul = st[-1]["u"]
            u = np.array(g["u"]); zs = np.array(g["zs"]); zt = np.array(g["zt"]); zc = np.array(g["zc"])
            o = np.argsort(u); u, zs, zt, zc = u[o], zs[o], zt[o], zc[o]
            zs = medfilt(zs, 9); zt = medfilt(zt, 9)
            ls = old.levels(u, np.round(zs)); lt = old.levels(u, np.round(zt))
            ls[0][0] = lt[0][0] = 0.0; ls[-1][1] = lt[-1][1] = ul
            curve = old.rdp(np.column_stack([np.clip(u, 0, ul), zc]), 0.3)
            prof[n] = {"stations": st, "section": {"soffit": [[float(a) for a in x] for x in ls], "top": [[float(a) for a in x] for x in lt]},
                       "curve": [[float(a), float(b)] for a, b in curve], "supports": p.get("supports", [])}
    plan_len = {}
    for g, mark, n, a, b, L in r.Y_TENDONS:
        plan_len.setdefault(mark, []).append([g, L])
    for g, mark, n, a, b, L, yy, side in r.X_TENDONS:
        plan_len.setdefault(mark, []).append([g, L])
    tb = {"PROJ_REFERENCE": "TBC", "REVISION": "TBC", "DRAWN_BY": "CLAUDE (DRAFT)", "DRAWING_NUMBER": "TBC", "DRAWING_STAGE": "REDRAFT FOR REVIEW",
          "CLIENT": "TBC", "ISSUE_DATE": "16-OCT-2026"}
    sub = "SCALE: ALONG TENDON 1:{den}, HEIGHTS 1:25 (DISTORTED)  |  REDRAFT FOR REVIEW - NOT FOR CONSTRUCTION"
    sheets = []
    for kind, title in (("X", "2F PT TENDON PROFILES - X / EX DIRECTION (REDRAFT)"), ("Y", "2F PT TENDON PROFILES - Y DIRECTION (REDRAFT)")):
        sheets.append({"number": kind, "title": title, "marks": old.MARK_ORDER[kind], "den_candidates": [200, 250, 300, 350, 400],
                       "titles": [{"text": f"{title}  -  SOURCE SHEET 16", "x": 12, "y": 257.5, "style": "TEXT_3.5"}, {"text": sub, "x": 12, "y": 252.0, "style": "TEXT_2.0"}]})
    return {"schema": "pt_profile_data/1", "file_prefix": "2F_PT_Profiles", "v_den": 25, "title_block": tb, "sheets": sheets, "profiles": prof, "plan_lengths": plan_len,
            "labels": {"profile": "SHEET 16 PROFILE L = ", "plan": "PLAN ", "verify": "  - VERIFY", "plan_offset_m": 0.5},
            "notes": {"x": 12, "y": 40.0, "pitch": 3.6, "lines": NOTES}}


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--profiles", required=True); ap.add_argument("--out", required=True)
    ns = ap.parse_args()
    d = convert(json.load(open(ns.profiles)))
    json.dump(d, open(ns.out, "w", encoding="utf-8"), separators=(",", ":"))
    print("written", ns.out, len(d["profiles"]), "profiles")
