#!/usr/bin/env python3
"""Restandardise an existing DXF sheet set onto the company standards (05-01, 05-04, 05-04a/b). Originals are never modified.

Usage: python tools/cadgen/restandardise.py <src_dir_with_DXFs> --out <dir> --design-basis db.yaml --register reg.csv --standards <Structural-Drawing-Standards>

Per sheet: layers mapped by LAYER_MAP (title-block strip entities and the old border are dropped and replaced by the standard
STR_TITLEBLOCK_A3 block filled from the register / design basis; the old strip's values are compared and differences reported);
text moved to styles TEXT_2.0/2.5/3.5/5.0/7.0 by SNAP rules (text is never made smaller, so it can only grow - overflow is
estimated and reported for manual review); per-entity colours/lineweights reset to ByLayer. Geometry is not edited.
Mapping/snap rules are PROPOSALS (05-04b is PROPOSED). Output is DXF only (no DWG) and has not been seen in AutoCAD.
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
from ezdxf.addons.importer import Importer

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import build_sheets as bs  # noqa: E402
import common as c  # noqa: E402

DROP = "__DROP__"
LAYER_MAP = {"FRAME": DROP, "TEXT": "S-ANNO-TEXT", "NOTE": "S-ANNO-TEXT", "DIM": "S-ANNO-DIMS", "GRID": "S-GRID", "STEEL": "S-STEEL-OUTLINE",
             "RC": "S-CONC-OUTLINE", "HATCH": "S-HATCH-CONC", "REBAR": "S-REBAR", "BRACE": "S-STEEL-BRACE", "BRICK": "S-MASONRY",
             "SOIL": "S-SOIL", "THIN": "S-DETAIL-THIN", "HIDDEN": "S-HIDDEN"}   # TITLE is split by entity type below
STRIP_Y = c.TB_BOT - 0.2


def snap(h: float) -> str:
    if h <= 2.0:
        return "TEXT_2.0"
    if h <= 3.0:
        return "TEXT_2.5"
    if h <= 4.0:
        return "TEXT_3.5"
    if h <= 6.0:
        return "TEXT_5.0"
    return "TEXT_7.0"


def _ys(e):
    t = e.dxftype()
    if t == "TEXT":
        return [e.dxf.insert.y]
    if t == "LINE":
        return [e.dxf.start.y, e.dxf.end.y]
    if t == "LWPOLYLINE":
        return [p[1] for p in e.get_points()]
    return []


def in_strip(e):
    ys = _ys(e)
    return bool(ys) and min(ys) >= STRIP_Y


def text_boxes(msp):
    out = []
    for e in msp.query("TEXT"):
        bb = bbox.extents([e])
        if bb.has_data:
            out.append((bb.extmin.x, bb.extmin.y, bb.extmax.x, bb.extmax.y))
    return out


def overlaps(boxes, tol=0.3):
    n = 0
    for i in range(len(boxes)):
        a = boxes[i]
        for j in range(i + 1, len(boxes)):
            b = boxes[j]
            if min(a[2], b[2]) - max(a[0], b[0]) > tol and min(a[3], b[3]) - max(a[1], b[1]) > tol:
                n += 1
    return n


def restandardise(src, out_dir, db, reg_rows, layers):
    src = pathlib.Path(src)
    name = src.stem
    row = next((r for r in reg_rows if r["sheet_number"] == name), None)
    if row is None:
        return {"sheet": name, "error": "not in register - skipped"}
    sdoc = ezdxf.readfile(src)
    sm = sdoc.modelspace()
    before = overlaps(text_boxes(sm))
    old = {}
    strip_texts = sorted(((round(e.dxf.insert.x, 1), round(e.dxf.insert.y, 1), e.dxf.text) for e in sm.query("TEXT") if in_strip(e)), key=lambda t: (-t[1], t[0]))
    keep, dropped, moved, snapped = [], 0, {}, 0
    for e in list(sm):
        lay = e.dxf.layer
        if lay == "FRAME" or (lay in ("TITLE", "THIN") and in_strip(e)):
            dropped += 1
            continue
        if lay == "TITLE":
            new = "S-ANNO-TEXT" if e.dxftype() == "TEXT" else "S-ANNO-TABLE"
        elif lay in LAYER_MAP:
            new = LAYER_MAP[lay]
        elif lay == "0":
            new = "S-DETAIL-THIN"
        else:
            return {"sheet": name, "error": f"layer {lay} has no mapping"}
        moved[f"{lay}->{new}"] = moved.get(f"{lay}->{new}", 0) + 1
        e.dxf.layer = new
        for att in ("color", "lineweight"):
            if e.dxf.hasattr(att):
                e.dxf.discard(att)
        keep.append(e)
    scale = next((t[2] for t in strip_texts if ":" in t[2] and t[2].split(":")[0].strip().isdigit()), "AS-SHOWN")
    scale = scale if scale else "AS-SHOWN"

    for lname in {e.dxf.layer for e in keep}:
        if lname not in sdoc.layers:
            sdoc.layers.add(lname)   # so the importer finds the (already renamed) layers; real definitions come from the standards
    ddoc = bs.new_doc(layers)
    bs.define_titleblock(ddoc)
    imp = Importer(sdoc, ddoc)
    imp.import_entities(keep, ddoc.modelspace())
    imp.finalize()
    dm = ddoc.modelspace()
    for e in dm.query("TEXT"):
        st = snap(e.dxf.height)
        if abs(c.TEXT_HEIGHTS[st] - e.dxf.height) > 1e-9:
            snapped += 1
        e.dxf.style, e.dxf.height = st, c.TEXT_HEIGHTS[st]
        e.dxf.discard("width") if e.dxf.hasattr("width") else None
    recoded = 0
    old_code, new_code = "PRJ-" + db["project"]["code"].split("-", 1)[1], db["project"]["code"]
    for e in dm.query("TEXT"):
        if old_code in e.dxf.text and old_code != new_code:
            e.dxf.text = e.dxf.text.replace(old_code, new_code)   # user confirmed PJR prefix 14-OCT-2026
            recoded += 1
    vals = bs.sheet_values(db, row, row["sheet_name"], scale)
    bs.place_titleblock(dm, vals)
    expect = {"PROJ_REFERENCE": vals["PROJ_REFERENCE"], "DRAWING_NAME": vals["DRAWING_NAME"], "REVISION": vals["REVISION"], "DRAWN_BY": vals["DRAWN_BY"],
              "DRAWING_NUMBER": vals["DRAWING_NUMBER"], "DRAWING_STAGE": vals["DRAWING_STAGE"], "CLIENT": vals["CLIENT"], "ISSUE_DATE": vals["ISSUE_DATE"]}
    texts = {t[2] for t in strip_texts}
    mism = {k: v for k, v in expect.items() if v not in texts}
    after = overlaps(text_boxes(dm))
    dst = pathlib.Path(out_dir) / f"{name}_{row['revision']}.dxf"
    # AutoCAD rejects a DXF whose entities name a linetype not in the LTYPE table: fall back to BYLAYER (S-HIDDEN is dashed by layer)
    defined = {l.dxf.name.upper() for l in ddoc.linetypes}
    lt_fixed = 0
    for e in ddoc.modelspace():
        if e.dxf.hasattr("linetype") and e.dxf.linetype.upper() not in defined | {"BYLAYER", "BYBLOCK"}:
            e.dxf.linetype = "BYLAYER"; lt_fixed += 1
    ddoc.saveas(dst)
    return {"sheet": name, "file": dst.name, "entities_in": len(sm), "entities_kept": len(keep), "title_strip_dropped": dropped, "layer_moves": moved,
            "linetype_undefined_set_bylayer": lt_fixed, "text_resized_up": snapped, "project_code_text_corrected_PRJ_to_PJR": recoded, "text_overlaps_before": before, "text_overlaps_after": after, "scale_read": scale,
            "old_title_block_values_not_matching_register_or_design_basis": mism}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("--out", required=True)
    ap.add_argument("--design-basis", required=True)
    ap.add_argument("--register", required=True)
    ap.add_argument("--standards", required=True)
    ns = ap.parse_args(argv)
    with open(ns.design_basis, encoding="utf-8") as fh:
        db = yaml.safe_load(fh)
    with open(ns.register, newline="", encoding="utf-8-sig") as fh:
        reg = list(csv.DictReader(fh))
    layers = c.load_layers(pathlib.Path(ns.standards))
    out = pathlib.Path(ns.out)
    out.mkdir(parents=True, exist_ok=True)
    res = [restandardise(p, out, db, reg, layers) for p in sorted(pathlib.Path(ns.src).glob("*.dxf"))]
    (out / "restandardise_report.json").write_text(json.dumps(res, indent=2), encoding="utf-8")
    bad = [r for r in res if "error" in r]
    print(json.dumps({"sheets": len(res), "errors": bad}, indent=2))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
