"""Shared constants and standards loaders for the DXF generator and validator.

Everything geometric about the sheet/title block was measured from the issued drawing set WH-STR-SD R00 (see
01_standards/01-title-block/01-01-title-block.md, PROPOSED). Layers/text come from 05-drafting-styles.
"""
from __future__ import annotations

import csv
import pathlib

SHEET_W, SHEET_H = 420.0, 297.0                     # A3 landscape, mm
BORDER = (7.0, 5.0, 413.0, 292.0)                   # x0, y0, x1, y1
TB_TOP, TB_MID, TB_BOT = 292.0, 278.9, 266.2        # title block rows
TB_X = {"a": 7.0, "b": 56.5, "c": 94.0, "d": 238.5, "e": 272.2, "f": 319.7, "g": 365.2, "h": 413.0, "arrow": 402.8}

TEXT_HEIGHTS = {"TEXT_2.0": 2.0, "TEXT_2.5": 2.5, "TEXT_3.5": 3.5, "TEXT_5.0": 5.0, "TEXT_7.0": 7.0}   # 05-01
FONT_FILE, FONT_NAME = "arial.ttf", "Arial"
LINETYPE_MAP = {"Continuous": "CONTINUOUS", "Centre": "CENTER", "Phantom": "PHANTOM", "Dashed": "DASHED"}
GREY = 8                                              # ACI grey used for title block labels / concrete hatch
TB_BLOCK = "STR_TITLEBLOCK_A3"
ATTRIBS = ["PROJ_REFERENCE", "DRAWING_NAME", "REVISION", "DRAWN_BY", "DRAWING_NUMBER", "DRAWING_STAGE", "CLIENT", "SCALE", "ISSUE_DATE"]


def load_layers(standards_dir: pathlib.Path) -> dict[str, dict]:
    """Layers from 05-04 (approved) plus 05-04a / 05-04b (approved by the user 14-OCT-2026; file names keep _PROPOSED). Raises if 05-04 is missing."""
    d = pathlib.Path(standards_dir) / "05-drafting-styles"
    main = d / "05-04-layer-standards.csv"
    if not main.exists():
        raise FileNotFoundError(f"company layer standard not found: {main}")
    layers: dict[str, dict] = {}
    for fname, status in (("05-04-layer-standards.csv", "approved"), ("05-04a-layer-extensions-proposed.csv", "approved"), ("05-04b-layer-extensions-proposed.csv", "approved")):
        p = d / fname
        if not p.exists():
            continue
        with open(p, newline="", encoding="utf-8-sig") as fh:
            for r in csv.DictReader(fh):
                lw = r["Lineweight"].strip()
                layers[r["Layer Name"].strip()] = {
                    "color": int(r["Colour"]),
                    "linetype": LINETYPE_MAP.get(r["Linetype"].strip(), r["Linetype"].strip().upper()),
                    "lineweight": None if lw.lower() == "default" else int(round(float(lw) * 100)),
                    "plot": r["Plot"].strip().lower() == "yes",
                    "description": r["Description"].strip(), "status": status,
                }
    return layers
