#!/usr/bin/env python3
"""Validate the redraft DXF with the company validator, accepting the PROPOSED 05-04c layers; plus a text-overlap screen."""
import json, pathlib, sys, math
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import common as c, validate_dxf as v, redraft_2f_pt as r
import ezdxf

dxf, std = sys.argv[1], pathlib.Path(sys.argv[2])
r.layers_with_extensions_orig = r.layers_with_extensions
c.load_layers = lambda d: r.layers_with_extensions_orig(pathlib.Path(d))
res = v.validate(dxf, std)
print(json.dumps({k: res[k] for k in ("ok", "errors", "warnings", "entities")}, indent=1)[:3000])
doc = ezdxf.readfile(dxf); boxes = []
for e in doc.modelspace().query("TEXT"):
    h = e.dxf.height; w = 0.64 * h * len(e.dxf.text); rot = e.dxf.get("rotation", 0)
    x, y = e.dxf.insert.x, e.dxf.insert.y; al = e.dxf.get("halign", 0); va = e.dxf.get("valign", 0)
    # approximate anchor: use align_point when set
    if e.dxf.hasattr("align_point"): x, y = e.dxf.align_point.x, e.dxf.align_point.y
    dx0 = {0: 0, 1: -w / 2, 2: -w, 4: -w / 2}.get(al, 0)
    dy0 = {0: 0, 1: 0, 2: -h / 2, 3: -h, 0: 0}.get(va, 0)
    if al == 4: dy0 = -h / 2
    if rot == 90: bx = (x - h + dy0 * 0, x, y + dx0, y + dx0 + w)
    else: bx = (x + dx0, x + dx0 + w, y + dy0, y + dy0 + h)
    boxes.append((bx, e.dxf.text))
bad = []
for i in range(len(boxes)):
    for j in range(i + 1, len(boxes)):
        a, b = boxes[i][0], boxes[j][0]
        if a[0] < b[1] - 0.2 and b[0] < a[1] - 0.2 and a[2] < b[3] - 0.2 and b[2] < a[3] - 0.2: bad.append((boxes[i][1], boxes[j][1]))
print("text overlaps (approx):", len(bad)); [print("  ", b) for b in bad[:40]]
