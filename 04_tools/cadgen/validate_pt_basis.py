#!/usr/bin/env python3
"""Validate a PT basis file (03_projects/<CODE>/pt-basis.yaml): bonded (company default) or unbonded PT.

Usage: python 04_tools/cadgen/validate_pt_basis.py <pt_basis.yaml> [--design-basis <project design basis yaml>] [--json]
Exit 0 = no ERRORs (WARNINGs allowed). 1 = ERRORs. 2 = file unreadable.

The validator never fills or fixes a value. It reports what is missing or contradictory.
Calculated comparisons are reported as numbers, never as PASS/FAIL approval: engineer sign-off is human.
EN 1992-1-1 5.10.2.1 limit uses the CEN recommended k1 = 0.8 and k2 = 0.9 (recorded national annex: none for Cambodia).
"""
from __future__ import annotations

import argparse
import json
import re
import sys

import yaml

BS_RE = re.compile(r"\bBS\s?(EN\s?)?\d{3,5}\b", re.I)
REQUIRED = ["codes.actions", "codes.concrete", "codes.national_annex_note", "concrete.class_28d", "concrete.fck_mpa",
            "concrete.fck_cube_28d_mpa", "concrete.max_aggregate_mm", "reinforcement.main.fyk_mpa", "reinforcement.cover_mm",
            "strand.standard", "strand.type", "strand.diameter_mm", "strand.area_mm2", "strand.fpk_mpa", "strand.jacking_force_kn",
            "tendon.mu", "tendon.k", "tendon.draw_in_mm"]


def get(d, dotted):
    for p in dotted.split("."):
        if not isinstance(d, dict) or p not in d:
            return None
        d = d[p]
    return d


def num(v):
    try:
        return float(str(v).replace(",", "").strip())
    except (TypeError, ValueError):
        return None


def strings(o, path=""):
    if isinstance(o, dict):
        for k, v in o.items():
            yield from strings(v, f"{path}.{k}" if path else k)
    elif isinstance(o, list):
        for i, v in enumerate(o):
            yield from strings(v, f"{path}[{i}]")
    elif isinstance(o, str):
        yield path, o


def validate(b: dict, db: dict | None = None) -> dict:
    E, W, I = [], [], []
    if not isinstance(b, dict):
        return {"ok": False, "errors": ["file is not a mapping"], "warnings": [], "info": []}
    system = str(get(b, "system.type") or "").strip().lower()
    if not system:
        W.append("system.type: not set - BONDED (company default) is assumed; confirm")
        system = "bonded"
    elif system not in ("bonded", "unbonded"):
        E.append(f"system.type must be 'bonded' or 'unbonded' (found {get(b, 'system.type')!r})")
    else:
        I.append(f"system.type: {system}" + (" (company default)" if system == "bonded" else " (not the company default - confirm)"))
    for path, s in strings({k: v for k, v in b.items() if k not in ("open_items",)}):
        if system == "bonded" and path != "system.type" and re.search(r"unbonded|mono-?strand", s, re.I):
            E.append(f"{path}: refers to an unbonded / mono-strand system but system.type is bonded ('{s}')")
        if BS_RE.search(s):
            E.append(f"{path}: British Standard reference '{BS_RE.search(s).group(0)}' - the PT notes are Eurocode only")
    for k in REQUIRED:
        if get(b, k) in (None, ""):
            W.append(f"{k}: not set (prints TBC)")
    if get(b, "concrete.fck_cube_transfer_mpa") in (None, ""):
        W.append("concrete.fck_cube_transfer_mpa: strength at stressing not set - engineer decision")
    ap, fpk, F = num(get(b, "strand.area_mm2")), num(get(b, "strand.fpk_mpa")), num(get(b, "strand.min_breaking_load_kn"))
    if ap and fpk and F:
        calc = ap * fpk / 1000.0
        if abs(calc - F) / F > 0.01:
            W.append(f"strand.min_breaking_load_kn {F} kN differs from Ap x fpk = {calc:.1f} kN by more than 1 %")
        else:
            I.append(f"Ap x fpk = {calc:.1f} kN vs stated breaking load {F} kN (within 1 %)")
    P = num(get(b, "strand.jacking_force_kn"))
    if P and ap and fpk:
        s = P * 1000.0 / ap
        lim1 = 0.8 * fpk
        msg = f"jacking stress {s:.0f} MPa; EN 1992-1-1 5.10.2.1 limit 0.8 fpk = {lim1:.0f} MPa"
        f01 = num(get(b, "strand.fp01k_mpa"))
        if f01:
            lim2 = 0.9 * f01
            msg += f"; 0.9 fp0.1k = {lim2:.0f} MPa"
            (E if s > min(lim1, lim2) else I).append(msg + (" - EXCEEDED" if s > min(lim1, lim2) else ""))
        else:
            (E if s > lim1 else I).append(msg + (" - EXCEEDED" if s > lim1 else "; fp0.1k not set so the 0.9 fp0.1k limit is NOT checked"))
    if num(get(b, "strand.yield_mpa")) and not num(get(b, "strand.fp01k_mpa")):
        W.append("strand.fp01k_mpa not set: source 'yield strength' is not the EN 0.1 % proof stress")
    if db:
        code = (db.get("project") or {}).get("code")
        if b.get("project_code") and code and b["project_code"] != code:
            E.append(f"project_code {b['project_code']} differs from design basis {code}")
        na = (db.get("national_annex") or {}).get("mode")
        note = str(get(b, "codes.national_annex_note") or "").upper()
        if na == "CEN_RECOMMENDED" and "CEN RECOMMENDED" not in note:
            W.append("design basis uses CEN recommended values but codes.national_annex_note does not say so")
        if na == "NA" and "CEN RECOMMENDED" in note:
            E.append("design basis records a National Annex but the note says CEN recommended values")
    for o in b.get("open_items") or []:
        if not isinstance(o, dict) or not {"id", "status", "description"} <= set(o):
            E.append(f"open_items entry malformed: {o}")
    return {"ok": not E, "errors": E, "warnings": W, "info": I}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("pt_basis")
    ap.add_argument("--design-basis")
    ap.add_argument("--json", action="store_true")
    ns = ap.parse_args(argv)
    try:
        b = yaml.safe_load(open(ns.pt_basis, encoding="utf-8"))
        db = yaml.safe_load(open(ns.design_basis, encoding="utf-8")) if ns.design_basis else None
    except (OSError, yaml.YAMLError) as e:
        print(f"cannot read: {e}", file=sys.stderr)
        return 2
    r = validate(b, db)
    if ns.json:
        print(json.dumps(r, indent=2))
    else:
        for tag in ("errors", "warnings", "info"):
            for m in r[tag]:
                print(f"{tag[:-1].upper() if tag != 'info' else 'INFO'}: {m}")
        print("RESULT:", "no errors" if r["ok"] else "ERRORS FOUND")
    return 0 if r["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
