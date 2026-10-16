#!/usr/bin/env python3
"""Validate a generated DXF sheet against company standards, the design basis and the document register.

Usage: python tools/cadgen/validate_dxf.py <sheet.dxf> --standards <Structural-Drawing-Standards> [--design-basis db.yaml] [--register reg.csv]
Exit 0 = no ERRORs. Warnings (e.g. layers from PROPOSED extension) do not fail.

Checks: file opens + ezdxf audit clean | units mm | layers only from 05-04/05-04a with matching colour/linetype/lineweight/plot |
text heights from 05-01 and >= 2.0 mm, Arial styles | no per-entity colour/lineweight overrides (except title-block grey) |
all geometry inside the sheet border | title block present with all attributes, matching register and design basis |
sheet-specific content (drawing list lists every register row exactly once; cover carries project name).
This validates the DXF file only. It does not validate a DWG, an AutoCAD plot, fonts installed on a PC, plot styles or xrefs.
"""
from __future__ import annotations

import argparse
import csv
import json
import pathlib
import sys

import ezdxf
import yaml
from ezdxf import bbox

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import common as c  # noqa: E402

TEXT_TYPES = ("TEXT", "MTEXT", "ATTRIB", "ATTDEF")


def _entities(doc):
    for e in doc.modelspace():
        yield "model", e
    for blk in doc.blocks:
        if blk.name.startswith(("*", "_")):  # layouts and built-in dimension arrow blocks (unused template content)
            continue
        for e in blk:
            yield f"block {blk.name}", e


def validate(path, standards_dir, db=None, register=None) -> dict:
    E, W = [], []
    err = lambda m: E.append(m)
    warn = lambda m: W.append(m)
    try:
        doc = ezdxf.readfile(path)
    except Exception as ex:  # noqa: BLE001
        return {"ok": False, "errors": [f"cannot open DXF: {ex}"], "warnings": []}
    std = c.load_layers(pathlib.Path(standards_dir))

    audit = doc.audit()
    for a in audit.errors:
        err(f"audit: {a.message}")

    if doc.header.get("$INSUNITS") != 4:
        err(f"drawing units are not millimetres ($INSUNITS={doc.header.get('$INSUNITS')})")

    used = set()
    for where, e in _entities(doc):
        t = e.dxftype()
        lay = e.dxf.get("layer", "0")
        used.add(lay)
        if lay not in std and lay != "0":
            err(f"{where}: {t} on layer '{lay}' which is in neither 05-04 nor 05-04a")
        elif lay == "0" and t != "INSERT":
            err(f"{where}: {t} on layer 0 - company drawings use named layers")
        col = e.dxf.get("color", 256)
        if col not in (256, c.GREY):
            err(f"{where}: {t} has colour override {col}")
        lw = e.dxf.get("lineweight", -1)
        if lw not in (-1, None):
            err(f"{where}: {t} has lineweight override {lw}")
        if t in TEXT_TYPES:
            h = e.dxf.char_height if t == "MTEXT" else e.dxf.get("height", 0)
            if h < 2.0:
                err(f"{where}: text height {h} mm is below the 2.0 mm minimum")
            elif h not in c.TEXT_HEIGHTS.values():
                err(f"{where}: text height {h} mm is not a company height {sorted(c.TEXT_HEIGHTS.values())}")
            st = e.dxf.get("style", "Standard")
            if st not in c.TEXT_HEIGHTS:
                err(f"{where}: text style '{st}' is not a company style")
            elif abs(c.TEXT_HEIGHTS[st] - h) > 1e-9:
                err(f"{where}: style {st} used with height {h} (style implies {c.TEXT_HEIGHTS[st]})")

    for name in c.TEXT_HEIGHTS:
        if name not in doc.styles:
            err(f"text style {name} missing")
        elif doc.styles.get(name).dxf.font.lower() != c.FONT_FILE:
            err(f"text style {name} font is {doc.styles.get(name).dxf.font}, expected {c.FONT_FILE}")

    for name in used:
        if name in std and name in doc.layers:
            la, s = doc.layers.get(name), std[name]
            if la.color != s["color"]:
                err(f"layer {name}: colour {la.color} != standard {s['color']}")
            if la.dxf.linetype.upper() != s["linetype"]:
                err(f"layer {name}: linetype {la.dxf.linetype} != standard {s['linetype']}")
            if s["lineweight"] is not None and la.dxf.lineweight != s["lineweight"]:
                err(f"layer {name}: lineweight {la.dxf.lineweight} != standard {s['lineweight']}")
            if bool(la.dxf.plot) != s["plot"]:
                err(f"layer {name}: plot flag differs from standard")
            if s["status"] == "proposed":
                warn(f"layer {name} comes from the PROPOSED extension 05-04a (not yet approved)")
        elif name in std:
            err(f"layer {name} is used but not defined in the file")

    # extents inside border
    ext = bbox.extents(doc.modelspace(), fast=False)
    if ext.has_data:
        x0, y0, x1, y1 = c.BORDER
        lo, hi = ext.extmin, ext.extmax
        if lo.x < x0 - 0.05 or lo.y < y0 - 0.05 or hi.x > x1 + 0.05 or hi.y > y1 + 0.05:
            err(f"geometry extents ({lo.x:.1f},{lo.y:.1f})-({hi.x:.1f},{hi.y:.1f}) exceed the sheet border {c.BORDER}")
    else:
        err("drawing is empty")

    # title block
    inserts = [e for e in doc.modelspace().query("INSERT") if e.dxf.name == c.TB_BLOCK]
    if len(inserts) != 1:
        err(f"expected exactly one {c.TB_BLOCK} insert, found {len(inserts)}")
        attribs = {}
    else:
        attribs = {a.dxf.tag: a.dxf.text for a in inserts[0].attribs}
        for tag in c.ATTRIBS:
            if not attribs.get(tag, "").strip():
                err(f"title block attribute {tag} is empty or missing")
    row = None
    if register is not None and attribs.get("DRAWING_NUMBER"):
        row = next((r for r in register if r["sheet_number"] == attribs["DRAWING_NUMBER"]), None)
        if row is None:
            err(f"drawing number {attribs['DRAWING_NUMBER']} is not in the document register")
        else:
            for tag, key in (("DRAWING_NAME", "sheet_name"), ("REVISION", "revision"), ("ISSUE_DATE", "issue_date"), ("DRAWING_STAGE", "stage")):
                if attribs.get(tag) != row[key]:
                    err(f"title block {tag} '{attribs.get(tag)}' != register {key} '{row[key]}'")
    if db is not None:
        P = db["project"]
        if attribs.get("PROJ_REFERENCE") != P["code"]:
            err(f"title block PROJ_REFERENCE '{attribs.get('PROJ_REFERENCE')}' != design basis '{P['code']}'")
        if attribs.get("CLIENT") != P["client"]:
            err(f"title block CLIENT '{attribs.get('CLIENT')}' != design basis '{P['client']}'")
        if attribs.get("DRAWING_NUMBER") and not attribs["DRAWING_NUMBER"].startswith(P["drawing_prefix"] + "-"):
            err(f"drawing number prefix does not match design basis {P['drawing_prefix']}")

    # sheet-specific content
    texts = [e.dxf.text for e in doc.modelspace().query("TEXT")]
    no = attribs.get("DRAWING_NUMBER", "")
    if no.endswith("-002") and register is not None:
        for r in register:
            n = texts.count(r["sheet_number"])
            if n != 1:
                err(f"drawing list shows {r['sheet_number']} {n} time(s), expected 1")
            if r["sheet_name"] not in texts:
                err(f"drawing list is missing sheet name '{r['sheet_name']}'")
        extra = [t for t in texts if t.startswith(db["project"]["drawing_prefix"] + "-") and t not in {r["sheet_number"] for r in register}] if db else []
        for t in extra:
            err(f"drawing list shows {t} which is not in the register")
    if no.endswith("-001") and db is not None:
        want = f"{db['project']['code']}_{db['project']['name']}"
        if want not in texts:
            err(f"cover page does not carry '{want}'")
        if any("NOT GENERATED" in t for t in texts):
            warn("cover page isometric view was not generated (see text on sheet)")

    return {"file": str(path), "ok": not E, "errors": E, "warnings": sorted(set(W)), "entities": sum(1 for _ in _entities(doc)),
            "layers_used": sorted(used), "title_block": attribs}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("dxf")
    ap.add_argument("--standards", required=True)
    ap.add_argument("--design-basis")
    ap.add_argument("--register")
    ns = ap.parse_args(argv)
    db = yaml.safe_load(open(ns.design_basis, encoding="utf-8")) if ns.design_basis else None
    reg = list(csv.DictReader(open(ns.register, newline="", encoding="utf-8-sig"))) if ns.register else None
    res = validate(ns.dxf, ns.standards, db, reg)
    print(json.dumps(res, indent=2))
    return 0 if res["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
