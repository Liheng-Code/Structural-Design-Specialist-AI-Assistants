#!/usr/bin/env python3
"""SYNTHETIC TEST FIXTURE - NOT FROM ETABS OR SAFE, NOT A REAL MODEL.

Builds a tiny made-up 4-column structure in the *assumed* ETABS 'Export Tables' layout so the importer's checks can be tested.
Numbers are invented but statically consistent (sum of joint reactions = base reaction; combinations = factor-weighted sums).
They carry no engineering meaning and must never be used in a design. The layout is an assumption, not a verified export.

build(out_dir, **defects) writes synthetic_export.xlsx and synthetic_export.csv plus members.csv, expected_cases.yaml,
hand_totals.yaml. Each defect keyword deliberately breaks one thing so a test can confirm the importer catches it.
"""
from __future__ import annotations

import csv
import pathlib

from openpyxl import Workbook

JOINTS = ["1", "2", "3", "4"]
DEAD = [500.0, 520.0, 480.0, 500.0]      # kN, sum 2000
LIVE = [150.0, 160.0, 140.0, 150.0]      # kN, sum 600
WIND = [-30.0, 30.0, -30.0, 30.0]        # kN, sum 0 (FZ), FX 20 each
CASES = {"DEAD": DEAD, "LIVE": LIVE, "WINDX": WIND}
COMBO = {"ULS-1": {"DEAD": 1.35, "LIVE": 1.5}, "ULS-2": {"DEAD": 1.0, "WINDX": 1.5}}
COLS = ["C1", "C2", "C3", "C4"]
HDR_R = ["Story", "Unique Name", "Output Case", "Case Type", "Step Type", "FX", "FY", "FZ", "MX", "MY", "MZ"]
UNITS_R = ["", "", "", "", "", "kN", "kN", "kN", "kN-m", "kN-m", "kN-m"]
HDR_B = ["Output Case", "Case Type", "Step Type", "FX", "FY", "FZ", "MX", "MY", "MZ", "X", "Y", "Z"]
UNITS_B = ["", "", "", "kN", "kN", "kN", "kN-m", "kN-m", "kN-m", "m", "m", "m"]
HDR_F = ["Story", "Column", "Unique Name", "Output Case", "Case Type", "Step Type", "Station", "P", "V2", "V3", "T", "M2", "M3"]
UNITS_F = ["", "", "", "", "", "", "m", "kN", "kN", "kN", "kN-m", "kN-m", "kN-m"]
HDR_C = ["Name", "Load Case/Combo", "Scale Factor"]


def _reaction(case, i):
    fz = CASES[case][i]
    fx = 20.0 if case == "WINDX" else 0.0
    return [fx, 0.0, fz, 0.0, 0.0, 0.0]


def tables(**d):
    cases = dict(CASES)
    combos = {k: dict(v) for k, v in COMBO.items()}
    for name, terms in combos.items():
        cases[name] = [sum(f * CASES[c][i] for c, f in terms.items()) for i in range(4)]
    bump = 60.0 if d.get("break_superposition") else 0.0   # corrupts ULS-1 joint 3 FZ in the reactions table only
    if d.get("wrong_combo_factor"):
        combos["ULS-1"]["LIVE"] = 1.35
    names = list(cases)
    if d.get("drop_case"):
        names.remove("LIVE")
    ctype = lambda n: "Combination" if n in COMBO else "Linear Static"
    R, B, F = [], [], []
    for n in names:
        for i, j in enumerate(JOINTS):
            vals = _reaction(n, i) if n in CASES else [sum(f * _reaction(c, i)[k] for c, f in combos[n].items()) for k in range(6)]
            if n == "ULS-1" and i == 2:
                vals[2] += bump
            R.append(["Base", j, n, ctype(n), "", *vals])
        tot = [sum(r[5 + k] for r in R if r[2] == n) for k in range(6)]
        B.append([n, ctype(n), "", *tot, 0.0, 0.0, 0.0])
        for i, c in enumerate(COLS):
            for st in (0.0, 3.0):
                F.append(["Story1", c, str(i + 1), n, ctype(n), "", st, -cases[n][i], 0.0, 0.0, 0.0, 0.0, 0.0])
    if d.get("scale_base"):   # base reaction no longer equals joint reaction sum
        for b in B:
            b[5] *= 1.05
    if d.get("duplicate_row"):
        F.append(list(F[0]))
    if d.get("empty_cell"):
        R[3][7] = None
    if d.get("extra_member"):
        F.append(["Story1", "C9", "99", names[0], "Linear Static", "", 0.0, -1.0, 0, 0, 0, 0, 0])
    C = [[k, c, f] for k, t in combos.items() for c, f in t.items()]
    T = {"Joint Reactions": (HDR_R, UNITS_R, R), "Base Reactions": (HDR_B, UNITS_B, B),
         "Element Forces - Columns": (HDR_F, UNITS_F, F), "Load Combinations": (HDR_C, None, C),
         "Program Control": (["ProgramName", "Version", "CurrUnits"], None,
                             [["SYNTHETIC TEST FIXTURE - NOT ETABS", "0", "kN, m, C"]])}
    if d.get("units_mm_n"):   # same physical values written in N and mm
        h, u, rows = T["Joint Reactions"]
        T["Joint Reactions"] = (h, ["", "", "", "", "", "N", "N", "N", "N-mm", "N-mm", "N-mm"],
                                [r[:5] + [v * 1000 if v is not None else None for v in r[5:8]] + [x * 1e6 for x in r[8:]] for r in rows])
    if d.get("no_units"):
        h, u, rows = T["Joint Reactions"]
        T["Joint Reactions"] = (h, None, rows)
    if d.get("bad_unit"):
        h, u, rows = T["Joint Reactions"]
        T["Joint Reactions"] = (h, ["", "", "", "", "", "furlong", "kN", "kN", "kN-m", "kN-m", "kN-m"], rows)
    if d.get("drop_column"):
        h, u, rows = T["Joint Reactions"]
        k = h.index("MZ")
        T["Joint Reactions"] = (h[:k], u[:k] if u else None, [r[:k] for r in rows])
    if d.get("extra_table"):
        T["Story Drifts"] = (["Story", "Output Case", "Drift"], None, [["Story1", "WINDX", 0.001]])
    return T


def members():
    return [{"etabs_label": c, "project_member_id": f"COL-{c}", "description": "synthetic"} for c in COLS]


def build(out, **d):
    out = pathlib.Path(out)
    out.mkdir(parents=True, exist_ok=True)
    T = tables(**d)
    wb = Workbook()
    wb.remove(wb.active)
    for name, (h, u, rows) in T.items():
        ws = wb.create_sheet(name[:31])
        ws.append([f"TABLE:  {name}"])
        ws.append(h)
        if u:
            ws.append(u)
        for r in rows:
            ws.append(r)
    wb.save(out / "synthetic_export.xlsx")
    with open(out / "synthetic_export.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        for name, (h, u, rows) in T.items():
            w.writerow([f"TABLE:  {name}"])
            w.writerow(h)
            if u:
                w.writerow(u)
            w.writerows([["" if v is None else v for v in r] for r in rows])
            w.writerow([])
    m = members()
    if d.get("drop_member"):
        m = m + [{"etabs_label": "C7", "project_member_id": "COL-C7", "description": "not in export"}]
    with open(out / "members.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["etabs_label", "project_member_id", "description"])
        w.writeheader()
        w.writerows(m)
    exp = ["# SYNTHETIC TEST FIXTURE", "superposition_tolerance_pct: 0.5", "cases:"] + [f"  - name: {c}" for c in CASES]
    exp += ["combos:"]
    for k, t in COMBO.items():
        exp += [f"  - name: {k}", "    linear: true", "    terms:"] + [f"      {c}: {f}" for c, f in t.items()]
    (out / "expected_cases.yaml").write_text("\n".join(exp) + "\n", encoding="utf-8")
    hand = "# SYNTHETIC TEST FIXTURE\ntolerance_pct: 1.0\nfz_kN:\n  DEAD: 2000.0\n  LIVE: 600.0\n"
    if d.get("bad_hand"):
        hand = hand.replace("2000.0", "1900.0")
    (out / "hand_totals.yaml").write_text(hand, encoding="utf-8")
    return out


if __name__ == "__main__":
    import sys
    print(build(sys.argv[1] if len(sys.argv) > 1 else "synthetic_etabs"))
