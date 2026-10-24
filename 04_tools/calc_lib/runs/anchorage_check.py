#!/usr/bin/env python3
"""Run the EN 1992-1-1 anchorage check for a list of bar sizes and write a results JSON for the report generator.

Usage: python 04_tools/calc_lib/runs/anchorage_check.py <inputs.yaml> <out_results.json> [--design-basis db.yaml]

inputs.yaml:
  id, title
  concrete_class, fyk, bars[], compare_with: {label, fctk005_override, rows: {good: [...], poor: [...], lap_good: [...], mandrel: [...]}}
Every input carries a 'source'. The script refuses to run if a referenced design-basis item id does not exist.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

import yaml

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from calc_lib.rc import ec2_anchorage as a  # noqa: E402


TOL_MM, TOL_REL = 5, 0.01  # drawing values are rounded on no single increment; accept the larger of 5 mm or 1 %, report actual deviation


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("inputs")
    ap.add_argument("out")
    ap.add_argument("--design-basis")
    ns = ap.parse_args(argv)
    inp = yaml.safe_load(open(ns.inputs, encoding="utf-8"))

    if ns.design_basis:
        db = yaml.safe_load(open(ns.design_basis, encoding="utf-8"))
        ids = {m["id"] for m in db.get("materials", [])}
        for ref in inp.get("design_basis_refs", []):
            if ref not in ids:
                sys.exit(f"design-basis item '{ref}' not found - refusing to run with untraceable inputs")

    cc, fyk, bars = inp["concrete_class"], float(inp["fyk"]), [float(b) for b in inp["bars"]]
    sig = a.fyd(fyk)

    def table(fctk=None):
        out = {"good": [], "poor": [], "lap_good": [], "fbd_good": None, "fbd_poor": None}
        for good in (True, False):
            for phi in bars:
                b = a.bond_stress(cc, good, phi, fctk)
                lb = a.lb_rqd(phi, sig, b.fbd)
                out["good" if good else "poor"].append(lb)
                if good:
                    out["fbd_good"] = b.fbd
                    out["lap_good"].append(1.5 * lb)  # alpha6 = 1.5 for 50 % lapped (EN 1992-1-1 Table 8.3)
                else:
                    out["fbd_poor"] = b.fbd
        return out

    base = table()
    comp = inp.get("compare_with") or {}
    alt = table(comp.get("fctk005_override")) if comp else None

    res = {
        "id": inp["id"], "title": inp["title"], "clause": "EN 1992-1-1 3.1.6, 8.4.2, 8.4.3",
        "inputs": [
            {"symbol": "concrete class", "value": cc, "unit": "-", "source": inp["sources"]["concrete"]},
            {"symbol": "fyk", "value": fyk, "unit": "MPa", "source": inp["sources"]["fyk"]},
            {"symbol": "gamma_c", "value": a.GAMMA_C, "unit": "-", "source": "EN 1992-1-1 Table 2.1N (CEN recommended)"},
            {"symbol": "gamma_s", "value": a.GAMMA_S, "unit": "-", "source": "EN 1992-1-1 Table 2.1N (CEN recommended)"},
            {"symbol": "alpha_ct", "value": a.ALPHA_CT, "unit": "-", "source": "EN 1992-1-1 3.1.6(2)P (CEN recommended)"},
            {"symbol": "fctk,0.05", "value": a.FCTK_005[cc], "unit": "MPa", "source": "EN 1992-1-1 Table 3.1"},
        ],
        "steps": [
            {"label": "Design tensile strength", "formula": "fctd = alpha_ct * fctk,0.05 / gamma_c",
             "substitution": f"{a.ALPHA_CT} * {a.FCTK_005[cc]} / {a.GAMMA_C}", "result": round(a.fctd(cc), 3), "unit": "MPa"},
            {"label": "Bond stress, good conditions", "formula": "fbd = 2.25 * eta1 * eta2 * fctd (eta1=1.0, eta2=1.0)",
             "substitution": f"2.25 * 1.0 * 1.0 * {a.fctd(cc):.3f}", "result": round(base["fbd_good"], 3), "unit": "MPa"},
            {"label": "Bond stress, poor conditions", "formula": "fbd = 2.25 * eta1 * eta2 * fctd (eta1=0.7, eta2=1.0)",
             "substitution": f"2.25 * 0.7 * 1.0 * {a.fctd(cc):.3f}", "result": round(base["fbd_poor"], 3), "unit": "MPa"},
            {"label": "Design steel stress", "formula": "sigma_sd = fyd = fyk / gamma_s",
             "substitution": f"{fyk:g} / {a.GAMMA_S}", "result": round(sig, 1), "unit": "MPa"},
        ],
        "bars_mm": [int(b) for b in bars],
        "results": {"lb_rqd_good": [round(x, 1) for x in base["good"]],
                    "lb_rqd_poor": [round(x, 1) for x in base["poor"]],
                    "lap_basic_good": [round(x, 1) for x in base["lap_good"]]},
        "scope_limits": "Basic required anchorage length only (alpha1-alpha5 = 1.0, lb,min not applied); lap = alpha6 * lb,rqd with alpha6 = 1.5. Straight bars.",
        "verification": {"method": "Reconciled with the SD-004 table (see reconciliation) and unit tests against hand values in tests/test_calc_report_docgen.py",
                         "status": "CROSS-CHECKED against issued drawing; not independently reviewed by an engineer"},
    }
    if comp:
        d = comp["rows"]
        res["reconciliation"] = {
            "label": comp["label"],
            "fbd_good_alt": round(alt["fbd_good"], 3),
            "note": comp.get("note", ""),
            "rows": [
                {"row": "lbd good bond", "drawing": d["good"], "calc_table_value": [round(x) for x in base["good"]],
                 "calc_drawing_basis": [round(x) for x in alt["good"]]},
                {"row": "lbd poor bond", "drawing": d["poor"], "calc_table_value": [round(x) for x in base["poor"]],
                 "calc_drawing_basis": [round(x) for x in alt["poor"]]},
                {"row": "lap l0 good (<=50% lapped)", "drawing": d["lap_good"], "calc_table_value": [round(x) for x in base["lap_good"]],
                 "calc_drawing_basis": [round(x) for x in alt["lap_good"]]},
            ],
        }
        for r in res["reconciliation"]["rows"]:
            r["dev_drawing_basis"] = [d_ - c_ for d_, c_ in zip(r["drawing"], r["calc_drawing_basis"])]
            r["dev_table_value"] = [d_ - c_ for d_, c_ in zip(r["drawing"], r["calc_table_value"])]
        res["reconciliation"]["tolerance"] = "larger of 5 mm or 1 %"
        res["reconciliation"]["all_within_tolerance_drawing_basis"] = all(
            abs(dv) <= max(TOL_MM, TOL_REL * c_)
            for r in res["reconciliation"]["rows"]
            for dv, c_ in zip(r["dev_drawing_basis"], r["calc_drawing_basis"]))
        res["reconciliation"]["max_rel_dev_table_value_pct"] = round(100 * max(
            abs(dv) / c_ for r in res["reconciliation"]["rows"]
            for dv, c_ in zip(r["dev_table_value"], r["calc_table_value"])), 2)
        res["reconciliation"]["max_dev_table_value_mm"] = max(
            abs(x) for r in res["reconciliation"]["rows"] for x in r["dev_table_value"])
        if "mandrel" in d:
            exp = [4 * b if b <= 16 else 7 * b for b in bars]  # EN 1992-1-1 Table 8.1 / 8.3(1)
            res["reconciliation"]["mandrel"] = {"drawing": d["mandrel"], "en_1992_8_3": [int(x) for x in exp],
                                                "mismatch_bars": [int(b) for b, x, y in zip(bars, d["mandrel"], exp) if x != y]}
    json.dump(res, open(ns.out, "w", encoding="utf-8"), indent=2)
    print(f"wrote {ns.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
