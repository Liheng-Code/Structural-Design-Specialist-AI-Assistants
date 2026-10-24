#!/usr/bin/env python3
"""Reusable PT general notes (BONDED post-tensioning, Eurocode) -> text/markdown and an A3 DXF sheet.

Usage:
  python 04_tools/cadgen/pt_notes.py --pt-basis 03_projects/<CODE>/pt-basis.yaml --standards 01_standards --out <dir>
        [--template <pt_general_notes.yaml>] [--design-basis 03_projects/<CODE>/design-basis.yaml] [--register <register.csv>]
        [--sheet-number OF-STR-PT-001] [--revision P01] [--stage "PRELIMINARY PT DESIGN"]

Rules (same as the other generators):
- The note wording lives in the YAML template; project values live in the PT basis file. Nothing is typed into this script.
- A value that is missing prints TBC and is listed under "ASSUMPTIONS TO BE CONFIRMED". Nothing is guessed.
- Only a BONDED system is accepted. The builder stops if system.type is anything else.
- Output is a script-written DXF (layers S-ANNO-TEXT / S-ANNO-TABLE from the approved standard) and a text copy.
  A DXF is not a DWG; nothing here is approved. Engineer sign-off is human.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
import textwrap

import yaml
from ezdxf.enums import TextEntityAlignment as A

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import build_sheets as bs  # noqa: E402
import common as c  # noqa: E402

TBC = "TBC"
PH = re.compile(r"\{([A-Za-z0-9_.]+)\}")
DEFAULT_TEMPLATE = pathlib.Path(__file__).resolve().parents[2] / ".claude" / "skills" / "pt-drawings" / "assets" / "pt_general_notes.yaml"

COLS = [(12.0, 205.0), (215.0, 408.0)]       # two text columns on A3 (border 7..413)
Y_TOP, Y_BOT = 259.0, 11.0                    # below the title-block strip, above the border
PITCH = {"TEXT_2.0": 3.5, "TEXT_2.5": 4.2, "TEXT_3.5": 5.6}
CHAR_W = 0.74                                 # estimated uppercase Arial width / text height (conservative)
HANG = 5.5                                    # hanging indent of numbered / dash items


class PTBasisError(Exception):
    pass


def lookup(basis: dict, dotted: str):
    cur = basis
    for part in dotted.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return None
    return cur


def fill(text: str, basis: dict, missing: set) -> str:
    def rep(m):
        v = lookup(basis, m.group(1))
        if v is None or v == "":
            missing.add(m.group(1))
            return TBC
        return str(v)
    return PH.sub(rep, text)


def check_basis(basis: dict) -> None:
    sysd = (basis or {}).get("system") or {}
    if str(sysd.get("type", "")).strip().lower() != "bonded":
        raise PTBasisError(f"system.type must be 'bonded' (found {sysd.get('type')!r}); the company PT standard covers bonded post-tensioning only")


def render(template: dict, basis: dict) -> dict:
    """Return {sections: [...], missing: [...], open_items: [...]}. Pure function: same inputs -> same output."""
    check_basis(basis)
    missing: set = set()
    sections = []
    for sec in template["sections"]:
        items = []
        for it in sec["items"]:
            if it.get("kind") == "table":
                rows = [[fill(cell, basis, missing) for cell in row] for row in it["rows"]]
                items.append({"kind": "table", "widths": it["widths"], "rows": rows})
            else:
                items.append({"kind": it.get("kind", "plain"), "text": fill(it["text"], basis, missing)})
        sections.append({"id": sec["id"], "title": sec["title"], "items": items})
    open_items = [o for o in (basis.get("open_items") or []) if str(o.get("status", "open")).lower() == "open"]
    auto = [{"id": f"AUTO-{i + 1:02d}", "status": "open", "description": f"PARAMETER '{k}' NOT IN THE PT BASIS - SHOWN AS TBC."}
            for i, k in enumerate(sorted(missing))]
    return {"sections": sections, "missing": sorted(missing), "open_items": open_items + auto}


def to_text(r: dict) -> str:
    out = []
    for s in r["sections"]:
        out.append(f"{s['id']}. {s['title']}")
        n = 0
        for it in s["items"]:
            if it["kind"] == "table":
                for row in it["rows"]:
                    out.append("   | " + " | ".join(row))
            elif it["kind"] == "num":
                n += 1
                out.append(f"  {n}. {it['text']}")
            elif it["kind"] == "dash":
                out.append(f"  - {it['text']}")
            else:
                out.append(f"  {it['text']}")
        out.append("")
    out.append("K. ASSUMPTIONS TO BE CONFIRMED")
    for o in r["open_items"]:
        out.append(f"  {o['id']}: {o['description']}")
    return "\n".join(out) + "\n"


# ------------------------------------------------------------------ DXF sheet
_FONTS: dict = {}


def _text_width(text: str, style: str) -> float:
    """Width in mm of single-line text in the sheet font, as ezdxf's bbox (and so validate_dxf) measures it."""
    if style not in _FONTS:
        from ezdxf.fonts import fonts
        _FONTS[style] = fonts.make_font(c.FONT_FILE, cap_height=c.TEXT_HEIGHTS[style])
    return float(_FONTS[style].text_width(text))


class Flow:
    def __init__(self, msp):
        self.msp, self.col, self.y = msp, 0, Y_TOP

    @property
    def x0(self):
        return COLS[self.col][0]

    @property
    def width(self):
        return COLS[self.col][1] - COLS[self.col][0]

    def need(self, h):
        if self.y - h < Y_BOT:
            if self.col + 1 >= len(COLS):
                raise bs.MissingInput("PT general notes do not fit on one A3 sheet - add a continuation sheet (PT-002)")
            self.col += 1
            self.y = Y_TOP

    def heading(self, text):
        self.need(PITCH["TEXT_2.5"] + 2 * PITCH["TEXT_2.0"] + 3)
        self.y -= 2.5
        bs.txt(self.msp, text, self.x0, self.y, "TEXT_2.5", "S-ANNO-TEXT")
        self.y -= PITCH["TEXT_2.5"]

    def para(self, label, text, style="TEXT_2.0"):
        hang = max(HANG, len(label) * c.TEXT_HEIGHTS[style] * CHAR_W + 1.5) if label else 0.0
        chars = max(20, int((self.width - hang) / (c.TEXT_HEIGHTS[style] * CHAR_W)))
        lines = textwrap.wrap(text, chars) or [""]
        # CHAR_W is an average: lines heavy in wide capitals (M, W, N, D) can still overrun. Measure each line with the
        # sheet font (the same measurement validate_dxf uses) and rewrap narrower until every line fits the column.
        while chars > 20 and max(_text_width(ln, style) for ln in lines) > self.width - hang:
            chars -= 1
            lines = textwrap.wrap(text, chars) or [""]
        self.need(PITCH[style] * min(len(lines), 2))
        for i, ln in enumerate(lines):
            self.need(PITCH[style])
            if i == 0 and label:
                bs.txt(self.msp, label, self.x0, self.y, style, "S-ANNO-TEXT")
            bs.txt(self.msp, ln, self.x0 + hang, self.y, style, "S-ANNO-TEXT")
            self.y -= PITCH[style]

    def table(self, widths, rows):
        rh = 4.6
        self.need(rh * len(rows) + 2)
        top = self.y + 0.5
        x0 = self.x0
        xs = [x0]
        for w in widths:
            xs.append(xs[-1] + w)
        n = len(rows)
        for i in range(n + 1):
            bs.line(self.msp, (xs[0], top - i * rh), (xs[-1], top - i * rh), "S-ANNO-TABLE")
        for x in xs:
            bs.line(self.msp, (x, top), (x, top - n * rh), "S-ANNO-TABLE")
        for r_i, row in enumerate(rows):
            yc = top - (r_i + 0.5) * rh
            for k, cell in enumerate(row):
                if r_i == 0 and len(widths) == 3:
                    bs.txt(self.msp, cell, (xs[k] + xs[k + 1]) / 2, yc, "TEXT_2.0", "S-ANNO-TEXT", A.MIDDLE_CENTER)
                else:
                    bs.txt(self.msp, cell, xs[k] + 1.2, yc, "TEXT_2.0", "S-ANNO-TEXT", A.MIDDLE_LEFT)
                    if len(cell) * 2.0 * CHAR_W > widths[k] - 2.0:
                        raise bs.MissingInput(f"table cell too long for its column: {cell!r}")
        self.y = top - n * rh - 4.5


def build_sheet(r: dict, title_values: dict, layers: dict, out: pathlib.Path, name: str) -> pathlib.Path:
    doc = bs.new_doc(layers)
    bs.define_titleblock(doc)
    msp = doc.modelspace()
    bs.place_titleblock(msp, title_values)
    f = Flow(msp)
    for s in r["sections"]:
        f.heading(f"{s['id']}. {s['title']}")
        n = 0
        for it in s["items"]:
            if it["kind"] == "table":
                f.table(it["widths"], it["rows"])
            elif it["kind"] == "num":
                n += 1
                f.para(f"{n}.", it["text"])
            elif it["kind"] == "dash":
                f.para("-", it["text"])
            else:
                f.para("", it["text"])
    f.heading("K. ASSUMPTIONS TO BE CONFIRMED")
    for o in r["open_items"]:
        f.para(o["id"], o["description"])
    out.mkdir(parents=True, exist_ok=True)
    p = out / f"{name}.dxf"
    doc.saveas(p)
    return p


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pt-basis", required=True)
    ap.add_argument("--standards", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--template", default=str(DEFAULT_TEMPLATE))
    ap.add_argument("--design-basis")
    ap.add_argument("--sheet-number", default="TBC")
    ap.add_argument("--revision", default="TBC")
    ap.add_argument("--stage", default="PRELIMINARY PT DESIGN")
    ap.add_argument("--issue-date", default="TBC")
    ap.add_argument("--drawing-name", default="PT GENERAL NOTES AND DESIGN CRITERIA")
    ap.add_argument("--no-pdf", action="store_true")
    ns = ap.parse_args(argv)
    basis = yaml.safe_load(open(ns.pt_basis, encoding="utf-8"))
    template = yaml.safe_load(open(ns.template, encoding="utf-8"))
    try:
        r = render(template, basis)
    except PTBasisError as e:
        print(f"BUILD STOPPED: {e}", file=sys.stderr)
        return 1
    db = yaml.safe_load(open(ns.design_basis, encoding="utf-8")) if ns.design_basis else None
    P = (db or {}).get("project", {})
    tv = {"PROJ_REFERENCE": P.get("code") or basis.get("project_code") or TBC, "DRAWING_NAME": ns.drawing_name,
          "REVISION": P.get("revision") or ns.revision, "DRAWN_BY": ((db or {}).get("approval") or {}).get("prepared_by") or "CLAUDE (DRAFT)",
          "DRAWING_NUMBER": ns.sheet_number, "DRAWING_STAGE": P.get("stage") or ns.stage, "CLIENT": P.get("client") or TBC,
          "SCALE": "NTS", "ISSUE_DATE": P.get("issue_date") or ns.issue_date}
    layers = c.load_layers(pathlib.Path(ns.standards))
    out = pathlib.Path(ns.out)
    try:
        dxf = build_sheet(r, tv, layers, out, f"{ns.sheet_number}_{tv['REVISION']}".replace("/", "-"))
    except bs.MissingInput as e:
        print(f"BUILD STOPPED: {e}", file=sys.stderr)
        return 1
    (out / f"{dxf.stem}_notes.txt").write_text(to_text(r), encoding="utf-8")
    pdf = None
    if not ns.no_pdf:
        pdf = out / f"{dxf.stem}_preview.pdf"
        bs.plot_pdf([dxf], pdf)
    print(json.dumps({"dxf": str(dxf), "preview_pdf": str(pdf) if pdf else None, "text": str(out / f'{dxf.stem}_notes.txt'),
                      "tbc_parameters": r["missing"], "open_items": len(r["open_items"]),
                      "note": "DXF written by script (not DWG); PDF is a script-rendered preview; not approved"}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
