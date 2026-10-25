#!/usr/bin/env python3
"""M1: structural layout DXF -> GeometryModel for Gate A (Development Plan v2 M1; ADR-012).

Usage:
    python 04_tools/model_builder/dxf_geometry.py --project 03_projects/PJR-2026-004
    python 04_tools/model_builder/dxf_geometry.py --dxf plan.dxf --layer-map layer-map.yaml \
        --project-code PJR-2026-004 --floor 3F --out <folder>

Reads only what the layer map names. Sizes come from the drawing itself:
  - labels next to elements, e.g. "BB2 (900x350)" (width x depth), "DROP PANEL 1", "450mm THK";
  - the legend key: each sample hatch in the legend has a name and a thickness beside it ("PT SLAB / THK: 200mm"),
    and plan areas covered by the same hatch (layer + pattern) take that thickness.
Anything that cannot be matched is listed as an issue; nothing is guessed or defaulted. Everything inside an exclusion
region (the legend frame) is skipped, because legends hold sample shapes drawn on the structural layers.

Writes geometry.json (GeometryModel, review UNREVIEWED), geometry-review.md and geometry-preview.pdf. geometry.json has
no timestamps, so re-running on the same inputs gives the same file and the same content hash.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import math
import pathlib
import re
import sys
from dataclasses import dataclass, field
from typing import Any, Iterable, Optional

import ezdxf
import yaml
from ezdxf import path as ezpath
from ezdxf.math import Matrix44, Vec2, is_point_in_polygon_2d

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from calc_lib.core import schemas as s

Pt = tuple[float, float]
Poly = list[Pt]

INSUNITS_TO_MM = {4: 1.0, 5: 10.0, 6: 1000.0}       # DXF $INSUNITS: mm, cm, m
LABEL_TOL_MM = 1500.0      # a label further than this from every candidate element is reported, not assigned
TIE_MM = 1.0               # two candidates this close in distance are ambiguous
SIZE_TOL_MM = 5.0          # drawn size vs label size
DESCRIPTORS = {"POUR STRIP", "OPEN", "OPENING", "PT SLAB", "PT BEAM", "BEAM", "SLEEVE", "DROP PANEL", "SLAB"}

RE_BB = re.compile(r"^\s*(BB\d+)\s*\(\s*(\d+(?:\.\d+)?)\s*[xX×]\s*(\d+(?:\.\d+)?)\s*\)")
RE_DP = re.compile(r"^\s*DROP\s+PANEL\s*(\d+)\s*$", re.I)
RE_THK = re.compile(r"(\d+(?:\.\d+)?)\s*mm\s*THK|THK\s*:?\s*(\d+(?:\.\d+)?)\s*mm", re.I)
RE_MM = re.compile(r"(\d+(?:\.\d+)?)\s*mm", re.I)


# ------------------------------------------------------------------------------------------------ geometry helpers
def bbox(pts: Iterable[Pt]) -> tuple[float, float, float, float]:
    p = list(pts)
    return min(q[0] for q in p), min(q[1] for q in p), max(q[0] for q in p), max(q[1] for q in p)


def area(poly: Poly) -> float:
    return abs(sum(poly[i][0] * poly[i - 1][1] - poly[i - 1][0] * poly[i][1] for i in range(len(poly)))) / 2


def centroid(poly: Poly) -> Pt:
    x0, y0, x1, y1 = bbox(poly)
    return (x0 + x1) / 2, (y0 + y1) / 2


def inside(p: Pt, poly: Poly) -> bool:
    return is_point_in_polygon_2d(Vec2(p), [Vec2(q) for q in poly]) >= 0


def dist_to_poly(p: Pt, poly: Poly) -> float:
    if inside(p, poly):
        return 0.0
    best = math.inf
    for i in range(len(poly)):
        (ax, ay), (bx, by) = poly[i - 1], poly[i]
        dx, dy = bx - ax, by - ay
        t = 0.0 if dx == dy == 0 else max(0.0, min(1.0, ((p[0] - ax) * dx + (p[1] - ay) * dy) / (dx * dx + dy * dy)))
        best = min(best, math.hypot(p[0] - ax - t * dx, p[1] - ay - t * dy))
    return best


def clean(poly: Poly) -> Poly:
    """Drop a repeated closing vertex and consecutive duplicates."""
    out: Poly = []
    for q in poly:
        if not out or math.hypot(q[0] - out[-1][0], q[1] - out[-1][1]) > 1e-6:
            out.append(q)
    if len(out) > 1 and math.hypot(out[0][0] - out[-1][0], out[0][1] - out[-1][1]) <= 1e-6:
        out.pop()
    return out


@dataclass
class Rect:
    centre: Pt
    long: float
    short: float
    angle: float          # direction of the long side, degrees
    axis_aligned: bool


def as_rect(poly: Poly, tol: float = 1.0) -> Optional[Rect]:
    """A 4-vertex polygon with right angles, else None."""
    if len(poly) != 4:
        return None
    e = [(poly[(i + 1) % 4][0] - poly[i][0], poly[(i + 1) % 4][1] - poly[i][1]) for i in range(4)]
    ln = [math.hypot(*v) for v in e]
    if min(ln) <= tol:
        return None
    for i in range(4):
        a, b = e[i], e[(i + 1) % 4]
        if abs(a[0] * b[0] + a[1] * b[1]) / (ln[i] * ln[(i + 1) % 4]) > 1e-3:
            return None
    i_long = 0 if ln[0] >= ln[1] else 1
    ang = math.degrees(math.atan2(e[i_long][1], e[i_long][0])) % 180.0
    return Rect(centroid(poly), ln[i_long], ln[1 - i_long], ang, min(ang % 90.0, 90.0 - ang % 90.0) < 0.01)


def rect_centreline(r: Rect) -> list[Pt]:
    a = math.radians(r.angle)
    dx, dy = math.cos(a) * r.long / 2, math.sin(a) * r.long / 2
    return [(r.centre[0] - dx, r.centre[1] - dy), (r.centre[0] + dx, r.centre[1] + dy)]


def bbox_centreline(poly: Poly) -> tuple[list[Pt], float]:
    x0, y0, x1, y1 = bbox(poly)
    if x1 - x0 >= y1 - y0:
        ym = (y0 + y1) / 2
        return [(x0, ym), (x1, ym)], y1 - y0
    xm = (x0 + x1) / 2
    return [(xm, y0), (xm, y1)], x1 - x0


def l_wall(poly: Poly, tol: float = SIZE_TOL_MM) -> Optional[tuple[list[Pt], float]]:
    """Path and thickness of an axis-aligned L-shaped wall outline (6 vertices) with equal arm thickness, else None."""
    snap = 2.0      # drafting slop: an edge 1 mm off square still counts as square
    if len(poly) != 6 or any(abs(poly[i][0] - poly[i - 1][0]) > snap and abs(poly[i][1] - poly[i - 1][1]) > snap
                             for i in range(6)):
        return None
    x0, y0, x1, y1 = bbox(poly)
    corners = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    on_poly = [c for c in corners if any(math.hypot(c[0] - q[0], c[1] - q[1]) <= 2 * snap for q in poly)]
    if len(on_poly) != 3:
        return None
    notch = next(c for c in corners if c not in on_poly)
    # the reflex (inner) corner is the one vertex that touches no side of the bounding box
    interior = [q for q in poly
                if min(abs(q[0] - x0), abs(q[0] - x1)) > snap and min(abs(q[1] - y0), abs(q[1] - y1)) > snap]
    if len(interior) != 1:
        return None
    reflex = interior[0]
    t_horizontal = (y1 - y0) - abs(notch[1] - reflex[1])     # thickness of the arm running along x
    t_vertical = (x1 - x0) - abs(notch[0] - reflex[0])       # thickness of the arm running along y
    if abs(t_horizontal - t_vertical) > tol or t_horizontal <= 0:
        return None
    t = (t_horizontal + t_vertical) / 2
    opp = (x0 + x1 - notch[0], y0 + y1 - notch[1])
    sx, sy = math.copysign(1, notch[0] - opp[0]), math.copysign(1, notch[1] - opp[1])
    elbow = (opp[0] + sx * t / 2, opp[1] + sy * t / 2)
    return [(notch[0], elbow[1]), elbow, (elbow[0], notch[1])], t


def ring_walls(outer: Poly, inner: Poly, tol: float = SIZE_TOL_MM) -> Optional[tuple[list[list[Pt]], float]]:
    """Four wall paths along the mid-line of an axis-aligned rectangular ring (outer and inner outline), else None."""
    ro, ri = as_rect(outer), as_rect(inner)
    if not (ro and ri and ro.axis_aligned and ri.axis_aligned):
        return None
    ox0, oy0, ox1, oy1 = bbox(outer)
    ix0, iy0, ix1, iy1 = bbox(inner)
    gaps = [ix0 - ox0, iy0 - oy0, ox1 - ix1, oy1 - iy1]
    if min(gaps) <= 0 or max(gaps) - min(gaps) > tol or max(gaps) > 1000:
        return None
    t = sum(gaps) / 4
    mx0, my0, mx1, my1 = ox0 + t / 2, oy0 + t / 2, ox1 - t / 2, oy1 - t / 2
    return [[(mx0, my0), (mx1, my0)], [(mx1, my0), (mx1, my1)], [(mx1, my1), (mx0, my1)], [(mx0, my1), (mx0, my0)]], t


# ------------------------------------------------------------------------------------------------ hatches
@dataclass
class Hatch:
    layer: str
    pattern: str
    polys: list[Poly]
    box: tuple[float, float, float, float]

    @property
    def key(self) -> tuple[str, str]:
        return self.layer, self.pattern

    def contains(self, p: Pt) -> bool:
        """Even-odd rule over all boundary paths, so islands (holes) are respected."""
        if not (self.box[0] <= p[0] <= self.box[2] and self.box[1] <= p[1] <= self.box[3]):
            return False
        return sum(1 for poly in self.polys if inside(p, poly)) % 2 == 1


def read_hatch(e: Any, scale: float) -> Optional[Hatch]:
    polys = []
    for p in ezpath.from_hatch(e):
        pts = clean([(v.x * scale, v.y * scale) for v in p.flattening(50.0 / scale)])
        if len(pts) >= 3:
            polys.append(pts)
    if not polys:
        return None
    return Hatch(e.dxf.layer, e.dxf.pattern_name, polys, bbox([q for poly in polys for q in poly]))


@dataclass
class LegendEntry:
    name: str
    thickness_mm: Optional[float]
    cast_later: bool
    texts: list[str]


def read_legend(hatches: list[Hatch], texts: list[tuple[Pt, str]], issues: list[s.GeometryIssue]
                ) -> dict[tuple[str, str], LegendEntry]:
    """Legend rows: a sample hatch with its name above and its thickness below, written just to its right."""
    key: dict[tuple[str, str], LegendEntry] = {}
    for h in hatches:
        _, y0, x1, _ = h.box
        near = [(p, t) for p, t in texts if x1 - 1.0 <= p[0] <= x1 + 3000 and y0 - 1.0 <= p[1] <= y0 + 2000]
        if not near:
            continue
        near.sort(key=lambda pt: -pt[0][1])
        words = [t for _, t in near]
        thk = None
        for t in words:
            m = RE_THK.search(t) or RE_MM.search(t)
            if m:
                thk = float(next(g for g in m.groups() if g))
                break
        entry = LegendEntry(words[0], thk, any("CAST LATER" in t.upper() for t in words), words)
        old = key.get(h.key)
        if old and (old.thickness_mm, old.cast_later) != (entry.thickness_mm, entry.cast_later):
            issues.append(s.GeometryIssue(severity="ERROR", code="LEGEND_CONFLICT",
                                          message=f"legend hatch {h.key} appears twice with different meaning: "
                                                  f"{old.texts} / {entry.texts}"))
            continue
        key[h.key] = entry
    return key


# ------------------------------------------------------------------------------------------------ reader
@dataclass
class Shape:
    kind: str
    poly: Poly
    handle: str
    layer: str
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class Result:
    model: s.GeometryModel
    legend: dict[tuple[str, str], LegendEntry]
    sizes: list[dict[str, Any]]


class Reader:
    KINDS = ("column", "wall", "slab_edge", "opening", "drop_panel", "band_beam", "beam", "pour_strip", "sleeve")

    def __init__(self, dxf_path: pathlib.Path, layer_map: dict[str, Any], project_code: str, floor: str) -> None:
        self.path = dxf_path
        self.map = layer_map
        self.project_code = project_code
        self.floor = floor
        self.issues: list[s.GeometryIssue] = []
        self.doc = ezdxf.readfile(str(dxf_path))
        self.msp = self.doc.modelspace()
        self.scale = 1.0

    def issue(self, severity: str, code: str, message: str, handle: Optional[str] = None,
              element_id: Optional[str] = None) -> None:
        self.issues.append(s.GeometryIssue(severity=severity, code=code, message=message,  # type: ignore[arg-type]
                                           cad_handle=handle, element_id=element_id))

    # -- setup
    def check_units(self) -> None:
        ins = self.doc.header.get("$INSUNITS", 0)
        if ins not in INSUNITS_TO_MM:
            raise ValueError(f"DXF $INSUNITS = {ins}: units not mm, cm or m; cannot read lengths safely")
        self.scale = INSUNITS_TO_MM[ins]
        declared = str(self.map.get("units", "")).strip().lower()
        unit_name = {4: "mm", 5: "cm", 6: "m"}[ins]
        if declared and declared != unit_name:
            raise ValueError(f"layer map says units '{declared}' but the DXF header says '{unit_name}'")

    def layers_of(self, kind: str) -> set[str]:
        spec = (self.map.get("elements") or {}).get(kind) or {}
        return set(spec.get("layers") or [])

    def find_exclusions(self) -> list[tuple[float, float, float, float]]:
        boxes = []
        for reg in self.map.get("exclude_regions") or []:
            fr = reg.get("frame") or {}
            want = str(fr.get("near_text", "")).strip().upper()
            texts = [self.pt(t.dxf.insert) for t in self.msp.query("TEXT MTEXT")
                     if (t.dxf.text if t.dxftype() == "TEXT" else t.plain_text()).strip().upper() == want]
            found = None
            for e in self.msp.query("LWPOLYLINE"):
                if e.dxf.layer != fr.get("layer"):
                    continue
                box = bbox(self.poly(e))        # frames are often drawn as open polylines, so use the extent
                if any(box[0] <= p[0] <= box[2] and box[1] <= p[1] <= box[3] for p in texts):
                    found = box
                    break
            if found is None:
                self.issue("WARNING", "EXCLUSION_NOT_FOUND",
                           f"exclusion region '{reg.get('name')}' (frame on '{fr.get('layer')}' around "
                           f"'{want}') not found; nothing excluded for it")
            else:
                boxes.append(found)
        return boxes

    def pt(self, v: Any) -> Pt:
        return float(v[0]) * self.scale, float(v[1]) * self.scale

    def poly(self, e: Any) -> Poly:
        return clean([self.pt(v) for v in e.vertices_in_wcs()])

    # -- main
    def read(self) -> Result:
        self.check_units()
        self.excl = self.find_exclusions()
        excluded = lambda p: any(b[0] <= p[0] <= b[2] and b[1] <= p[1] <= b[3] for b in self.excl)  # noqa: E731

        layer_kind = {lay: k for k in self.KINDS for lay in self.layers_of(k)}
        label_layers = set((self.map.get("labels") or {}).get("layers") or [])
        ignore_layers = set((self.map.get("ignore") or {}).get("layers") or [])
        frame_layers = {(r.get("frame") or {}).get("layer") for r in self.map.get("exclude_regions") or []}
        cast_spec = (self.map.get("elements") or {}).get("cast_later") or {}
        grid_spec = (self.map.get("elements") or {}).get("grid") or {}

        shapes: list[Shape] = []
        open_lines: list[tuple[Shape, str]] = []
        plan_hatches: list[Hatch] = []
        legend_hatches: list[Hatch] = []
        labels: list[tuple[Pt, str, str]] = []
        legend_texts: list[tuple[Pt, str]] = []
        unmapped: collections.Counter[str] = collections.Counter()
        circles: list[tuple[str, Pt, float, str]] = []      # kind, centre, diameter, handle

        for e in self.msp:
            t, lay = e.dxftype(), e.dxf.layer
            if t == "HATCH":
                h = read_hatch(e, self.scale)
                if h:
                    (legend_hatches if excluded(centroid(h.polys[0])) else plan_hatches).append(h)
                continue
            if t in ("TEXT", "MTEXT"):
                p = self.pt(e.dxf.insert)
                txt = (e.dxf.text if t == "TEXT" else e.plain_text()).strip()
                if excluded(p):
                    legend_texts.append((p, txt))
                elif lay in label_layers and txt:
                    labels.append((p, txt, e.dxf.handle))
                continue
            if t == "INSERT":
                self.read_insert(e, cast_spec, grid_spec, shapes, plan_hatches, label_layers, ignore_layers)
                continue
            kind = layer_kind.get(lay)
            if kind is None:
                if lay not in ignore_layers and lay not in frame_layers and lay not in label_layers:
                    unmapped[lay] += 1
                continue
            if t == "LWPOLYLINE":
                poly = self.poly(e)
                if not poly or excluded(poly[0]):
                    continue
                if e.closed and len(poly) >= 3:
                    shapes.append(Shape(kind, poly, e.dxf.handle, lay))
                else:
                    open_lines.append((Shape(kind, poly, e.dxf.handle, lay), lay))
            elif t == "CIRCLE":
                c = self.pt(e.dxf.center)
                if not excluded(c):
                    circles.append((kind, c, 2 * e.dxf.radius * self.scale, e.dxf.handle))
            # arcs, lines and other entities on element layers are symbol parts; they carry no element geometry

        for lay, n in sorted(unmapped.items()):
            self.issue("WARNING", "UNMAPPED_LAYER", f"{n} entities on layer '{lay}', which the layer map does not name")

        legend = read_legend(legend_hatches, legend_texts, self.issues)
        if self.excl and not legend:
            self.issue("WARNING", "LEGEND_EMPTY", "legend frame found but no sample hatch with text beside it")
        self.hatches = [h for h in plan_hatches if h.key in legend]

        openings = [sh for sh in shapes if sh.kind == "opening"]
        for sh, lay in open_lines:
            if sh.kind == "opening" and any(all(dist_to_poly(p, o.poly) <= SIZE_TOL_MM for p in sh.poly)
                                            for o in openings):
                continue        # the X drawn inside an opening
            self.issue("WARNING", "OPEN_POLYLINE", f"open polyline on '{lay}' ignored ({len(sh.poly)} points)",
                       sh.handle)

        self.check_duplicates(shapes)
        return self.build(shapes, circles, labels, legend)

    def read_insert(self, e: Any, cast_spec: dict[str, Any], grid_spec: dict[str, Any], shapes: list[Shape],
                    plan_hatches: list[Hatch], label_layers: set[str], ignore_layers: set[str]) -> None:
        name = e.dxf.name
        if name == cast_spec.get("block"):
            want = set(cast_spec.get("layers") or [])
            for v in e.virtual_entities():
                if v.dxf.layer not in want:
                    continue
                if v.dxftype() == "LWPOLYLINE" and v.closed:
                    shapes.append(Shape("cast_later", self.poly(v), e.dxf.handle, v.dxf.layer))
                elif v.dxftype() == "HATCH":
                    h = read_hatch(v, self.scale)
                    if h:
                        plan_hatches.append(h)
        elif name == grid_spec.get("block"):
            self.grid_insert = e
        elif e.dxf.layer not in label_layers and e.dxf.layer not in ignore_layers:
            self.issue("INFO", "BLOCK_NOT_READ", f"block '{name}' on layer '{e.dxf.layer}' not read", e.dxf.handle)

    def check_duplicates(self, shapes: list[Shape]) -> None:
        seen: dict[tuple[Any, ...], Shape] = {}
        for sh in shapes:
            k = (sh.kind, *(round(v) for v in bbox(sh.poly)))
            if k in seen:
                self.issue("WARNING", "DUPLICATE", f"{sh.kind} drawn twice at the same place (also handle "
                                                   f"{seen[k].handle})", sh.handle)
            else:
                seen[k] = sh

    # -- thickness from the legend key
    def legend_thickness(self, poly: Poly, holes: list[Poly], legend: dict[tuple[str, str], LegendEntry]
                         ) -> tuple[Optional[LegendEntry], str]:
        x0, y0, x1, y1 = bbox(poly)
        step = min(1000.0, max(50.0, min(x1 - x0, y1 - y0) / 3, math.sqrt(max(area(poly), 1.0) / 400)))
        votes: collections.Counter[tuple[str, str]] = collections.Counter()
        n = 0
        y = y0 + step / 2
        while y < y1:
            x = x0 + step / 2
            while x < x1:
                p = (x, y)
                if inside(p, poly) and not any(inside(p, h) for h in holes):
                    n += 1
                    for h in self.hatches:
                        if h.contains(p):
                            votes[h.key] += 1
                x += step
            y += step
        if not votes:
            return None, "no legend hatch covers this area"
        ranked = votes.most_common()
        best, k = ranked[0]
        note = f"legend hatch {best[0]} / {best[1]} on {k} of {n} sample points"
        others = {f"{key[0]} / {key[1]}": v for key, v in ranked[1:] if v >= 0.2 * n}
        if others:          # another legend hatch covers a fifth or more of the area
            note += f"; MIXED with {others}"
        return legend[best], note

    # -- elements
    def build(self, shapes: list[Shape], circles: list[tuple[str, Pt, float, str]], labels: list[tuple[Pt, str, str]],
              legend: dict[tuple[str, str], LegendEntry]) -> Result:
        by_kind: dict[str, list[Shape]] = collections.defaultdict(list)
        for sh in shapes:
            by_kind[sh.kind].append(sh)
        for group in by_kind.values():
            group.sort(key=lambda sh: (-round(centroid(sh.poly)[1] / 100), centroid(sh.poly)[0]))

        mm = lambda v: f"{v:.0f} mm"  # noqa: E731
        src = s.ValueSource.EXTRACTED_FROM_CAD.value
        P = lambda poly: [{"x": round(x, 3), "y": round(y, 3)} for x, y in poly]  # noqa: E731
        sizes: list[dict[str, Any]] = []

        def size_row(eid: str, kind: str, label: Optional[str], size: str, thk: Optional[float], how: str) -> None:
            sizes.append({"id": eid, "kind": kind, "label": label or "", "size": size,
                          "thickness_or_depth_mm": thk, "source": how})

        # columns
        columns = []
        for i, sh in enumerate(by_kind["column"], 1):
            r, eid = as_rect(sh.poly), f"C{i}"
            if not r:
                self.issue("ERROR", "COLUMN_SHAPE", f"column outline is not a rectangle ({len(sh.poly)} points)",
                           sh.handle, eid)
                continue
            if r.axis_aligned:              # b along x, h along y
                x0, y0, x1, y1 = bbox(sh.poly)
                b, h, rot = round(x1 - x0), round(y1 - y0), 0.0
            else:                           # b along the long side, rotated by its angle
                b, h, rot = round(r.long), round(r.short), round(r.angle, 3)
            columns.append({"id": eid, "source": src, "cad_handle": sh.handle, "centre": P([r.centre])[0],
                            "shape": "rectangular", "b": mm(b), "h": mm(h), "rotation_deg": rot})
            size_row(eid, "column", None, f"{b} x {h}", None, "drawn outline")
        for kind, c, d, hd in circles:
            if kind == "column":
                eid = f"C{len(columns) + 1}"
                columns.append({"id": eid, "source": src, "cad_handle": hd, "centre": P([c])[0],
                                "shape": "circular", "diameter": mm(round(d))})
                size_row(eid, "column", None, f"dia {d:.0f}", None, "drawn circle")

        # walls: rings (outer + inner outline) first, then rectangles, then L shapes
        walls: list[dict[str, Any]] = []
        wall_shapes = list(by_kind["wall"])
        used: set[int] = set()
        for a, sa in enumerate(wall_shapes):
            for b_, sb in enumerate(wall_shapes):
                if a == b_ or a in used or b_ in used:
                    continue
                ring = ring_walls(sa.poly, sb.poly)
                if ring:
                    used |= {a, b_}
                    paths, t = ring
                    for path in paths:
                        eid = f"W{len(walls) + 1}"
                        walls.append({"id": eid, "source": src, "cad_handle": sa.handle, "path": P(path),
                                      "thickness": mm(t)})
                    size_row(f"W{len(walls) - 3}-W{len(walls)}", "wall (core ring)", None,
                             f"{bbox(sa.poly)[2] - bbox(sa.poly)[0]:.0f} x {bbox(sa.poly)[3] - bbox(sa.poly)[1]:.0f}"
                             " outer", t, "two nested outlines -> ring of 4 walls")
                    self.issue("INFO", "WALL_RING", f"two nested outlines read as a ring of 4 walls, {t:.0f} mm "
                                                    f"thick (handles {sa.handle}, {sb.handle})", sa.handle)
        for k, sh in enumerate(wall_shapes):
            if k in used:
                continue
            r = as_rect(sh.poly)
            lw = None if r else l_wall(sh.poly)
            eid = f"W{len(walls) + 1}"
            if r:
                walls.append({"id": eid, "source": src, "cad_handle": sh.handle, "path": P(rect_centreline(r)),
                              "thickness": mm(r.short)})
                size_row(eid, "wall", None, f"{r.long:.0f} long", r.short, "drawn outline")
            elif lw:
                path, t = lw
                walls.append({"id": eid, "source": src, "cad_handle": sh.handle, "path": P(path),
                              "thickness": mm(t)})
                size_row(eid, "wall (L)", None, "L-shape", t, "drawn outline, equal arms")
            else:
                self.issue("ERROR", "WALL_SHAPE", f"wall outline with {len(sh.poly)} points is not a rectangle, ring "
                                                  "or equal-arm L; engineer to give its path and thickness",
                           sh.handle)

        # labels -> band beams, drop panels
        bb, dp, bm = by_kind["band_beam"], by_kind["drop_panel"], by_kind["beam"]
        bb_label: dict[int, tuple[str, float, float]] = {}
        dp_label: dict[int, str] = {}
        dp_thk: dict[int, float] = {}

        def nearest(p: Pt, group: list[Shape]) -> tuple[Optional[int], str]:
            d = sorted((dist_to_poly(p, sh.poly), i) for i, sh in enumerate(group))
            if not d or d[0][0] > LABEL_TOL_MM:
                return None, "no element near"
            if len(d) > 1 and d[1][0] - d[0][0] < TIE_MM:
                return None, "two elements equally near"
            return d[0][1], ""

        for p, txt, hd in labels:
            m_bb, m_dp, m_thk = RE_BB.match(txt), RE_DP.match(txt), RE_THK.search(txt)
            if m_bb:
                i, why = nearest(p, bb)
                if i is None:
                    self.issue("WARNING", "LABEL_UNMATCHED", f"label '{txt}': {why}", hd)
                elif i in bb_label:
                    self.issue("WARNING", "LABEL_TWICE", f"label '{txt}': band beam already labelled "
                                                         f"'{bb_label[i][0]}'", hd)
                else:
                    bb_label[i] = (txt, float(m_bb.group(2)), float(m_bb.group(3)))
            elif m_dp:
                i, why = nearest(p, dp)
                if i is None:
                    self.issue("WARNING", "LABEL_UNMATCHED", f"label '{txt}': {why}", hd)
                else:
                    dp_label.setdefault(i, txt)
            elif m_thk:
                val = float(next(g for g in m_thk.groups() if g))
                i, why = nearest(p, dp)
                if i is None:
                    self.issue("WARNING", "LABEL_UNMATCHED", f"thickness label '{txt}': {why} (drop panels)", hd)
                elif i in dp_thk and dp_thk[i] != val:
                    self.issue("WARNING", "LABEL_CONFLICT", f"drop panel has two thickness labels "
                                                            f"({dp_thk[i]:.0f} and {val:.0f} mm)", hd)
                else:
                    dp_thk[i] = val
            elif txt.upper() not in DESCRIPTORS:
                self.issue("INFO", "LABEL_NOT_READ", f"label '{txt}' not used", hd)

        holes_all = [sh.poly for k in ("drop_panel", "band_beam", "beam", "opening", "pour_strip", "column")
                     for sh in by_kind[k]]

        def linear(group: list[Shape], prefix: str, kind: str, label_of: dict[int, tuple[str, float, float]]
                   ) -> list[dict[str, Any]]:
            out = []
            for i, sh in enumerate(group):
                eid, r = f"{prefix}{i + 1}", as_rect(sh.poly)
                if r:
                    cl, width = rect_centreline(r), r.short
                else:
                    cl, width = bbox_centreline(sh.poly)
                    self.issue("WARNING", "NOT_RECTANGLE", f"{kind} outline has {len(sh.poly)} points; centreline "
                                                           "and width taken from its bounding box", sh.handle, eid)
                entry, note = self.legend_thickness(sh.poly, [], legend)
                depth, how, label = None, "", None
                if i in label_of:
                    label, lw, ld = label_of[i]
                    depth, how = ld, f"label '{label}'"
                    if abs(lw - width) > SIZE_TOL_MM:
                        self.issue("WARNING", "SIZE_MISMATCH", f"{kind} label '{label}' says width {lw:.0f} mm; "
                                                               f"drawn width {width:.0f} mm", sh.handle, eid)
                    if entry and entry.thickness_mm is not None and abs(entry.thickness_mm - ld) > SIZE_TOL_MM:
                        self.issue("WARNING", "SIZE_MISMATCH", f"{kind} label depth {ld:.0f} mm; legend hatch "
                                                               f"says {entry.thickness_mm:.0f} mm", sh.handle, eid)
                elif entry and entry.thickness_mm is not None:
                    depth, how = entry.thickness_mm, f"legend '{entry.name}' ({note})"
                if depth is None:
                    self.issue("WARNING", "SIZE_MISSING", f"{kind} depth not found ({note})", sh.handle, eid)
                out.append({"id": eid, "source": src, "cad_handle": sh.handle, "centreline": P(cl),
                            "width": mm(width), "depth": mm(depth) if depth is not None else None, "label": label,
                            "outline": P(sh.poly)})
                size_row(eid, kind, label, f"width {width:.0f}", depth, how or "not found")
            return out

        band_beams = linear(bb, "BB", "band beam", bb_label)
        beams = linear(bm, "B", "beam", {})

        drop_panels = []
        for i, sh in enumerate(dp):
            eid = f"DP{i + 1}"
            entry, note = self.legend_thickness(sh.poly, [], legend)
            depth, how = dp_thk.get(i), "label"
            if depth is not None and entry and entry.thickness_mm is not None \
                    and abs(entry.thickness_mm - depth) > SIZE_TOL_MM:
                self.issue("WARNING", "SIZE_MISMATCH", f"drop panel label {depth:.0f} mm; legend hatch says "
                                                       f"{entry.thickness_mm:.0f} mm", sh.handle, eid)
            if depth is None and entry and entry.thickness_mm is not None:
                depth, how = entry.thickness_mm, f"legend '{entry.name}' ({note})"
            if depth is None:
                self.issue("WARNING", "SIZE_MISSING", f"drop panel depth not found ({note})", sh.handle, eid)
            x0, y0, x1, y1 = bbox(sh.poly)
            drop_panels.append({"id": eid, "source": src, "cad_handle": sh.handle, "outline": P(sh.poly),
                                "depth": mm(depth) if depth is not None else None, "label": dp_label.get(i)})
            size_row(eid, "drop panel", dp_label.get(i), f"{x1 - x0:.0f} x {y1 - y0:.0f}", depth,
                     how if depth is not None else "not found")

        # slabs (incl. cast-later pieces) and pour strips: thickness from the legend key
        slabs = []
        slab_shapes = [("S", sh, False) for sh in by_kind["slab_edge"]] + \
                      [("SC", sh, True) for sh in by_kind["cast_later"]]
        counters: collections.Counter[str] = collections.Counter()
        for prefix, sh, cast in slab_shapes:
            counters[prefix] += 1
            eid = f"{prefix}{counters[prefix]}"
            a = area(sh.poly)
            holes = holes_all + [o.poly for o in by_kind["slab_edge"] if o is not sh and area(o.poly) < a]
            entry, note = self.legend_thickness(sh.poly, holes, legend)
            thk = entry.thickness_mm if entry else None
            if thk is None:
                self.issue("WARNING", "SIZE_MISSING", f"slab thickness not found ({note})", sh.handle, eid)
            if "MIXED" in note:
                self.issue("WARNING", "THICKNESS_MIXED", f"slab area covered by more than one legend hatch: {note}",
                           sh.handle, eid)
            if entry and entry.cast_later != cast:
                self.issue("WARNING", "CAST_LATER_MISMATCH", f"legend says cast later = {entry.cast_later}, "
                                                             f"layer map says {cast}", sh.handle, eid)
            parent = next((o for o in by_kind["slab_edge"] if o is not sh and area(o.poly) > a
                           and all(inside(p, o.poly) for p in sh.poly)), None)
            if parent is not None and not cast:
                self.issue("INFO", "SLAB_ZONE", f"slab outline lies inside another slab outline: read as a "
                                                f"thickness zone ({thk if thk is None else round(thk)} mm)",
                           sh.handle, eid)
            slabs.append({"id": eid, "source": src, "cad_handle": sh.handle, "outline": P(sh.poly),
                          "thickness": mm(thk) if thk is not None else None, "cast_later": cast})
            x0, y0, x1, y1 = bbox(sh.poly)
            size_row(eid, "slab (cast later)" if cast else "slab", entry.name if entry else None,
                     f"{x1 - x0:.0f} x {y1 - y0:.0f}", thk, note)

        pour_strips = []
        for i, sh in enumerate(by_kind["pour_strip"], 1):
            eid = f"PS{i}"
            entry, note = self.legend_thickness(sh.poly, [b.poly for b in bm], legend)
            thk = entry.thickness_mm if entry else None
            if thk is None:
                self.issue("WARNING", "SIZE_MISSING", f"pour strip thickness not found ({note})", sh.handle, eid)
            pour_strips.append({"id": eid, "source": src, "cad_handle": sh.handle, "outline": P(sh.poly),
                                "thickness": mm(thk) if thk is not None else None})
            x0, y0, x1, y1 = bbox(sh.poly)
            size_row(eid, "pour strip", entry.name if entry else None, f"{x1 - x0:.0f} x {y1 - y0:.0f}", thk, note)

        openings = [{"id": f"OP{i}", "source": src, "cad_handle": sh.handle, "outline": P(sh.poly)}
                    for i, sh in enumerate(by_kind["opening"], 1)]
        sleeves = [{"id": f"SL{i}", "source": src, "cad_handle": hd, "centre": P([c])[0], "diameter": mm(round(d))}
                   for i, (c, d, hd) in enumerate(((c, d, hd) for k, c, d, hd in circles if k == "sleeve"), 1)]

        grids = self.read_grid()

        # placement checks
        floor = [sh.poly for k in ("slab_edge", "pour_strip", "drop_panel", "band_beam", "beam") for sh in by_kind[k]]
        for c in columns:
            p = (c["centre"]["x"], c["centre"]["y"])
            if floor and not any(inside(p, f) for f in floor):
                self.issue("WARNING", "OUTSIDE_SLAB", f"column {c['id']} centre is outside every slab outline",
                           c["cad_handle"], c["id"])

        digest = hashlib.sha256(self.path.read_bytes()).hexdigest()
        model = s.GeometryModel(project_code=self.project_code, floor_label=self.floor,
                                source_file={"name": self.path.name, "sha256": digest}, grids=grids,
                                columns=columns, walls=walls, slabs=slabs, band_beams=band_beams, beams=beams,
                                openings=openings, drop_panels=drop_panels, pour_strips=pour_strips,
                                sleeves=sleeves, issues=self.issues)
        return Result(model, legend, sizes)

    def read_grid(self) -> list[dict[str, Any]]:
        ins = getattr(self, "grid_insert", None)
        spec = (self.map.get("elements") or {}).get("grid") or {}
        if ins is None:
            if spec.get("block"):
                self.issue("WARNING", "GRID_NOT_FOUND", f"grid block '{spec['block']}' not inserted in the drawing")
            return []
        m: Matrix44 = ins.matrix44()
        lines: list[tuple[Pt, Pt]] = []
        bubbles: list[tuple[Pt, str]] = []
        for e in self.doc.blocks[ins.dxf.name]:
            if e.dxftype() == "LINE":
                lines.append((self.pt(m.transform(e.dxf.start)), self.pt(m.transform(e.dxf.end))))
            elif e.dxftype() == "INSERT" and e.attribs:
                # the attribute text sits at the bubble; the bubble block's own insertion point can be far away
                a = e.attribs[0]
                bubbles.append((self.pt(m.transform(a.dxf.insert)), a.dxf.text.strip()))
        grids, used = [], set()
        for (a, b) in lines:
            d = sorted((min(math.dist(p, a), math.dist(p, b)), lab) for p, lab in bubbles if lab not in used)
            if not d or d[0][0] > 3000:
                self.issue("WARNING", "GRID_UNLABELLED", f"grid line {a}-{b} has no bubble within 3 m")
                continue
            lab = d[0][1]
            used.add(lab)
            vertical = abs(b[0] - a[0]) < abs(b[1] - a[1])
            grids.append({"label": lab, "axis": "X" if vertical else "Y",
                          "offset": round((a[0] + b[0]) / 2 if vertical else (a[1] + b[1]) / 2, 3)})
        for _, lab in bubbles:
            if lab not in used:
                self.issue("WARNING", "GRID_BUBBLE_ALONE", f"grid bubble '{lab}' has no line")
        return sorted(grids, key=lambda g: (g["axis"], g["offset"]))


# ------------------------------------------------------------------------------------------------ outputs
def write_review(res: Result, out: pathlib.Path) -> None:
    g = res.model
    counts = [("Grid lines", len(g.grids)), ("Columns", len(g.columns)), ("Walls", len(g.walls)),
              ("Slab areas", sum(1 for x in g.slabs if not x.cast_later)),
              ("Cast-later slab pieces", sum(1 for x in g.slabs if x.cast_later)),
              ("Band beams", len(g.band_beams)), ("Beams", len(g.beams)), ("Drop panels", len(g.drop_panels)),
              ("Openings", len(g.openings)), ("Pour strips", len(g.pour_strips)), ("Sleeves", len(g.sleeves))]
    sev = collections.Counter(i.severity for i in g.issues)
    lines = [f"# Gate A geometry review - {g.project_code} {g.floor_label}", "",
             "Generated by `04_tools/model_builder/dxf_geometry.py`. Status: **UNREVIEWED** - the engineer checks the",
             "preview against the drawing and confirms or corrects. Nothing here is approved.", "",
             f"- Source: `{g.source_file.name if g.source_file else '-'}` "
             f"(SHA-256 `{g.source_file.sha256[:16] if g.source_file else '-'}...`)",
             f"- Geometry content hash: `{s.content_hash(g)[:16]}...` (same inputs give the same hash)",
             f"- Issues: {sev['ERROR']} error(s), {sev['WARNING']} warning(s), {sev['INFO']} note(s)", "",
             "## Elements found", "", "| Element | Count |", "|---|---|"]
    lines += [f"| {k} | {n} |" for k, n in counts]
    lines += ["", "## Legend key read from the drawing", "", "| Hatch layer | Pattern | Legend name | Thickness |",
              "|---|---|---|---|"]
    lines += [f"| {k[0]} | {k[1]} | {v.name} | {'-' if v.thickness_mm is None else f'{v.thickness_mm:.0f} mm'}"
              f"{' (cast later)' if v.cast_later else ''} |" for k, v in sorted(res.legend.items())]
    lines += ["", "## Sizes and where they came from", "", "| Id | Element | Label | Size (mm) | Thickness / depth | "
              "Source |", "|---|---|---|---|---|---|"]
    for r in res.sizes:
        t = r["thickness_or_depth_mm"]
        shown = "-" if r["kind"] == "column" else "**not found**" if t is None else f"{t:.0f} mm"
        lines.append(f"| {r['id']} | {r['kind']} | {r['label']} | {r['size']} | {shown} | {r['source']} |")
    lines += ["", "## Issues", "", "| Severity | Code | Element | Message |", "|---|---|---|---|"]
    order = {"ERROR": 0, "WARNING": 1, "INFO": 2}
    for i in sorted(g.issues, key=lambda i: (order[i.severity], i.code)):
        lines.append(f"| {i.severity} | {i.code} | {i.element_id or i.cad_handle or ''} | "
                     f"{i.message.replace('|', '/')} |")
    lines += ["", "## Gate A checklist (engineer)", "",
              "- [ ] Every column, wall and core in the preview matches the drawing (position and size)",
              "- [ ] Slab edge, openings, drop panels, band beams, beams and pour strips match",
              "- [ ] Thickness and depth of every element are right (table above)",
              "- [ ] Every ERROR resolved; every WARNING accepted or corrected",
              "- [ ] Confirmed by (name, date): ____________________", ""]
    (out / "geometry-review.md").write_bytes("\n".join(lines).encode("utf-8"))


def write_preview(res: Result, out: pathlib.Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_pdf import PdfPages
    from matplotlib.patches import Polygon

    g = res.model
    xy = lambda pts: [(p.x / 1000, p.y / 1000) for p in pts]  # noqa: E731
    with PdfPages(out / "geometry-preview.pdf") as pdf:
        fig, ax = plt.subplots(figsize=(16.5, 11.7))
        style = [("slab", "#e8eef7", "#4a6fa5"), ("slab_zone", "#cfd8e6", "#4a6fa5"), ("cast", "#f7d774", "#b08900"),
                 ("pour", "#d9f2d9", "#2e8b57"), ("bb", "#f4d6b0", "#b5651d"), ("beam", "#f2c2c2", "#a83232"),
                 ("dp", "#e3d3f0", "#6a3d9a"), ("open", "white", "#555555"), ("wall", "#9e9e9e", "#333333"),
                 ("col", "#212121", "#000000")]
        colour = {k: (f, e) for k, f, e in style}

        def draw(pts: list[Any], kind: str, text: str, z: float, lw: float = 0.6) -> None:
            f, e = colour[kind]
            ax.add_patch(Polygon(xy(pts), closed=True, facecolor=f, edgecolor=e, lw=lw, zorder=z))
            if text:
                cx = sum(p[0] for p in xy(pts)) / len(pts)
                cy = sum(p[1] for p in xy(pts)) / len(pts)
                ax.text(cx, cy, text, fontsize=4, ha="center", va="center", zorder=20, color=e)

        poly_area = lambda pts: area([(p.x, p.y) for p in pts])  # noqa: E731
        main = max((sl for sl in g.slabs if not sl.cast_later), key=lambda sl: poly_area(sl.outline), default=None)
        main_t = main.thickness if main else None
        for z, sl in enumerate(sorted(g.slabs, key=lambda sl: -poly_area(sl.outline))):   # larger first, zones on top
            kind = "cast" if sl.cast_later else "slab_zone" if sl.thickness != main_t else "slab"
            t = "" if sl.thickness is None else f"{sl.thickness.to('mm').magnitude:.0f}"
            draw(sl.outline, kind, "" if sl.cast_later else f"{sl.id}\n{t}", 6 if sl.cast_later else 1 + z * 0.01)
        for ps in g.pour_strips:
            draw(ps.outline, "pour", ps.id, 3)
        for d in g.drop_panels:
            draw(d.outline, "dp", d.id, 4)
        for b in g.band_beams:
            draw(b.outline or b.centreline, "bb", f"{b.id}\n{b.label or ''}", 4)
        for b in g.beams:
            draw(b.outline or b.centreline, "beam", b.id, 5)
        for o in g.openings:
            draw(o.outline, "open", o.id, 7)
        for w in g.walls:
            t = w.thickness.to("mm").magnitude / 1000
            (x0, y0), (x1, y1) = xy(w.path)[0], xy(w.path)[-1]
            ax.plot([p[0] for p in xy(w.path)], [p[1] for p in xy(w.path)], color="#555555",
                    lw=max(1.0, t * 30), solid_capstyle="butt", zorder=8)
            ax.text((x0 + x1) / 2, (y0 + y1) / 2, w.id, fontsize=4, color="white", ha="center", va="center",
                    zorder=21)
        for c in g.columns:
            b = c.b.to("mm").magnitude / 1000 if c.b is not None else 0.5
            h = c.h.to("mm").magnitude / 1000 if c.h is not None else 0.5
            x, y = c.centre.x / 1000, c.centre.y / 1000
            ax.add_patch(Polygon([(x - b / 2, y - h / 2), (x + b / 2, y - h / 2), (x + b / 2, y + h / 2),
                                  (x - b / 2, y + h / 2)], closed=True, facecolor="#212121", zorder=9))
            ax.text(x, y + h / 2 + 0.25, c.id, fontsize=4, ha="center", zorder=21)
        xs = [p.x / 1000 for sl in g.slabs for p in sl.outline] or [0.0]
        ys = [p.y / 1000 for sl in g.slabs for p in sl.outline] or [0.0]
        for gr in g.grids:
            o = gr.offset / 1000
            if gr.axis == "X":
                ax.plot([o, o], [min(ys) - 2, max(ys) + 2], ls="--", lw=0.4, color="#888888", zorder=0)
                ax.text(o, max(ys) + 2.6, gr.label, ha="center", fontsize=7, fontweight="bold")
            else:
                ax.plot([min(xs) - 2, max(xs) + 2], [o, o], ls="--", lw=0.4, color="#888888", zorder=0)
                ax.text(min(xs) - 2.8, o, gr.label, va="center", fontsize=7, fontweight="bold")
        ax.set_aspect("equal")
        ax.set_xlim(min(xs) - 4, max(xs) + 4)
        ax.set_ylim(min(ys) - 4, max(ys) + 4)
        ax.set_xlabel("x (m)")
        ax.set_ylabel("y (m)")
        sev = collections.Counter(i.severity for i in g.issues)
        src_name = g.source_file.name if g.source_file else ""
        ax.set_title(f"{g.project_code} {g.floor_label} - geometry read from {src_name}  |  UNREVIEWED (Gate A)  |  "
                     f"{sev['ERROR']} errors, {sev['WARNING']} warnings", fontsize=10)
        handles = [Polygon([(0, 0)], facecolor=colour[k][0], edgecolor=colour[k][1], label=n) for k, n in
                   [("slab", "slab"), ("slab_zone", "slab, other thickness"), ("cast", "cast-later slab"),
                    ("pour", "pour strip"), ("dp", "drop panel"),
                    ("bb", "band beam"), ("beam", "beam"), ("open", "opening"), ("wall", "wall"),
                    ("col", "column")]]
        ax.legend(handles=handles, loc="upper left", bbox_to_anchor=(1.01, 1.0), fontsize=7)   # outside the plan
        fig.subplots_adjust(left=0.05, right=0.87)
        pdf.savefig(fig)
        plt.close(fig)

        issues = sorted(g.issues, key=lambda i: ({"ERROR": 0, "WARNING": 1, "INFO": 2}[i.severity], i.code))
        for start in range(0, max(len(issues), 1), 60):
            fig = plt.figure(figsize=(16.5, 11.7))
            fig.text(0.04, 0.96, f"Issues ({len(issues)}) - page {start // 60 + 1}", fontsize=11, fontweight="bold")
            for k, i in enumerate(issues[start:start + 60]):
                ref = i.element_id or i.cad_handle or ""
                fig.text(0.04, 0.93 - k * 0.0148, f"{i.severity:7s} {i.code:20s} {ref:8s} {i.message[:150]}",
                         fontsize=6.5, family="monospace")
            pdf.savefig(fig)
            plt.close(fig)


def run(dxf: pathlib.Path, layer_map: pathlib.Path, project_code: str, floor: str, out: pathlib.Path) -> Result:
    lm = yaml.safe_load(layer_map.read_text(encoding="utf-8")) or {}
    res = Reader(dxf, lm, project_code, floor).read()
    out.mkdir(parents=True, exist_ok=True)
    (out / "geometry.json").write_bytes(res.model.model_dump_json(indent=1).encode("utf-8"))
    write_review(res, out)
    write_preview(res, out)
    return res


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--project", type=pathlib.Path, help="project folder (reads its layer map, design and PT basis)")
    ap.add_argument("--dxf", type=pathlib.Path)
    ap.add_argument("--layer-map", type=pathlib.Path)
    ap.add_argument("--project-code")
    ap.add_argument("--floor")
    ap.add_argument("--out", type=pathlib.Path)
    a = ap.parse_args()
    if a.project:
        lm_path = a.layer_map or a.project / "inputs" / "str-layout" / "layer-map.yaml"
        lm = yaml.safe_load(lm_path.read_text(encoding="utf-8")) or {}
        dxf = a.dxf or lm_path.parent / lm["source_file"]
        db = yaml.safe_load((a.project / "design-basis.yaml").read_text(encoding="utf-8")) or {}
        pb_path = a.project / "pt-basis.yaml"
        pb = yaml.safe_load(pb_path.read_text(encoding="utf-8")) if pb_path.exists() else {}
        code = a.project_code or (db.get("project") or {}).get("code")
        floor = a.floor or (pb or {}).get("floor_label")
        out = a.out or a.project / "model" / "01-geometry"
    else:
        lm_path, dxf, code, floor, out = a.layer_map, a.dxf, a.project_code, a.floor, a.out
    if not all([lm_path, dxf, code, floor, out]):
        ap.error("give --project, or all of --dxf --layer-map --project-code --floor --out")
    res = run(dxf, lm_path, code, floor, out)
    g = res.model
    sev = collections.Counter(i.severity for i in g.issues)
    print(f"{g.project_code} {g.floor_label}: {len(g.columns)} columns, {len(g.walls)} walls, {len(g.slabs)} slab "
          f"areas, {len(g.band_beams)} band beams, {len(g.beams)} beams, {len(g.drop_panels)} drop panels, "
          f"{len(g.openings)} openings, {len(g.pour_strips)} pour strips, {len(g.grids)} grids")
    print(f"issues: {sev['ERROR']} error(s), {sev['WARNING']} warning(s), {sev['INFO']} note(s)")
    print(f"written: {out / 'geometry.json'}, geometry-review.md, geometry-preview.pdf  (hash "
          f"{s.content_hash(g)[:16]})")


if __name__ == "__main__":
    main()
