"""Inspect uploaded files: what they are, what can be read from them, and DWG -> DXF conversion.

What each format gets today (stated on screen, never overstated):
- DXF  : parsed with ezdxf (version, units, layers, entity counts, extents) and an SVG preview.
- DWG  : header version read; converted to DXF with AutoCAD accoreconsole if installed, then treated as DXF.
- PDF  : page count and page size; viewed in the browser.
- DWF/DWFX : stored and identified only. They are viewing formats; geometry is not extracted.
- XLSX/XLS/CSV : stored; SAFE/ETABS table import arrives at M1.
- PNG/JPG : stored and shown.
Uploaded files are data. Nothing in them is executed; DWG files are opened only by AutoCAD's console with our script.
"""
from __future__ import annotations

import os
import subprocess
import threading
import zipfile
from collections import Counter
from pathlib import Path
from typing import Any

ACCORE_CANDIDATES = [
    os.environ.get("PT_ACCORECONSOLE", ""),
    r"C:\Program Files\Autodesk\AutoCAD 2023\accoreconsole.exe",
    r"C:\Program Files\Autodesk\AutoCAD 2018\accoreconsole.exe",
]
_convert_lock = threading.Lock()   # one AutoCAD console at a time

KINDS = {
    ".dxf": "drawing", ".dwg": "drawing", ".dwf": "drawing-view", ".dwfx": "drawing-view",
    ".pdf": "document", ".xlsx": "table", ".xls": "table", ".csv": "table",
    ".png": "image", ".jpg": "image", ".jpeg": "image",
}
DWG_VERSIONS = {
    "AC1014": "R14", "AC1015": "AutoCAD 2000", "AC1018": "AutoCAD 2004", "AC1021": "AutoCAD 2007",
    "AC1024": "AutoCAD 2010", "AC1027": "AutoCAD 2013", "AC1032": "AutoCAD 2018",
}
INSUNITS = {0: "unitless", 1: "inches", 2: "feet", 4: "millimetres", 5: "centimetres", 6: "metres"}
MAX_UPLOAD_BYTES = 200 * 1024 * 1024


def accoreconsole() -> str | None:
    for p in ACCORE_CANDIDATES:
        if p and Path(p).is_file():
            return p
    return None


def sniff(path: Path, ext: str) -> str | None:
    """Return an error if the file content doesn't match its extension."""
    head = path.read_bytes()[:16] if path.stat().st_size else b""
    if not head:
        return "file is empty"
    if ext == ".pdf" and not head.startswith(b"%PDF"):
        return "not a PDF (missing %PDF header)"
    if ext == ".dwg" and not head.startswith(b"AC10"):
        return "not a DWG (missing AC10xx header)"
    if ext == ".dwf" and not head.startswith(b"(DWF V"):
        return "not a DWF (missing (DWF V header)"
    if ext in (".dwfx", ".xlsx") and not head.startswith(b"PK"):
        return f"not a {ext[1:].upper()} (not a zip package)"
    return None


def inspect_dxf(path: Path) -> dict[str, Any]:
    import ezdxf
    doc = ezdxf.readfile(path)
    msp = doc.modelspace()
    counts = Counter(e.dxftype() for e in msp)
    info: dict[str, Any] = {
        "dxf_version": doc.dxfversion,
        "units": INSUNITS.get(int(doc.header.get("$INSUNITS", 0)), f"code {doc.header.get('$INSUNITS')}"),
        "layers": sorted(layer.dxf.name for layer in doc.layers),
        "entities": dict(counts.most_common()),
        "entity_total": sum(counts.values()),
        "layouts": [lay.name for lay in doc.layouts if lay.name != "Model"],
    }
    try:
        from ezdxf import bbox
        ext = bbox.extents(msp, fast=True)
        if ext.has_data:
            info["extents"] = {"min": [round(ext.extmin.x, 1), round(ext.extmin.y, 1)],
                               "max": [round(ext.extmax.x, 1), round(ext.extmax.y, 1)]}
    except Exception:  # extents are a convenience, not a requirement
        pass
    return info


def render_svg(dxf_path: Path, out: Path) -> None:
    import ezdxf
    from ezdxf.addons.drawing import Frontend, RenderContext, config, layout, svg
    doc = ezdxf.readfile(dxf_path)
    backend = svg.SVGBackend()
    cfg = config.Configuration(background_policy=config.BackgroundPolicy.WHITE,
                               color_policy=config.ColorPolicy.BLACK)
    Frontend(RenderContext(doc), backend, config=cfg).draw_layout(doc.modelspace())
    out.write_text(backend.get_string(layout.Page(0, 0, layout.Units.mm, margins=layout.Margins.all(5))),
                   encoding="utf-8")


def inspect_pdf(path: Path) -> dict[str, Any]:
    from pypdf import PdfReader
    r = PdfReader(path)
    info: dict[str, Any] = {"pages": len(r.pages)}
    if r.pages:
        box = r.pages[0].mediabox
        info["page_size_mm"] = [round(float(box.width) * 25.4 / 72), round(float(box.height) * 25.4 / 72)]
    return info


def inspect_dwfx(path: Path) -> dict[str, Any]:
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
    return {"package_parts": len(names), "sheets": len([n for n in names if n.lower().endswith(".fpage")])}


def convert_dwg(dwg: Path, timeout_s: int = 120) -> tuple[Path | None, str]:
    """DWG -> DXF with AutoCAD's console. Returns (dxf path or None, message)."""
    acc = accoreconsole()
    if not acc:
        return None, "AutoCAD console not found on this PC; export the drawing as DXF and upload that"
    out = dwg.with_name("converted.dxf")
    script = dwg.with_name("convert.scr")
    # A space in an AutoCAD script is Enter: the path is quoted. The empty line accepts the DXF precision.
    script.write_text(f'_.SAVEAS\nDXF\n\n"{out}"\n_.QUIT\nY\n', encoding="ascii")
    log = dwg.with_name("convert.log")
    with _convert_lock, open(log, "wb") as lf:
        try:
            subprocess.run([acc, "/i", str(dwg), "/s", str(script), "/l", "en-US"], stdout=lf,
                           stderr=subprocess.STDOUT, timeout=timeout_s, check=False)
        except subprocess.TimeoutExpired:
            return None, f"AutoCAD console did not finish within {timeout_s} s"
    if out.is_file() and out.stat().st_size > 0:
        return out, "converted to DXF with AutoCAD 2023 console"
    return None, "AutoCAD console ran but produced no DXF (see convert.log)"


def process(path: Path, ext: str) -> tuple[str, str, dict[str, Any]]:
    """Inspect a stored upload. Returns (status, message, info). Status: ready | stored | failed."""
    bad = sniff(path, ext)
    if bad:
        return "failed", bad, {}
    try:
        if ext == ".dxf":
            info = inspect_dxf(path)
            render_svg(path, path.with_name("preview.svg"))
            return "ready", f"DXF read: {info['entity_total']} entities on {len(info['layers'])} layers", info
        if ext == ".dwg":
            code = path.read_bytes()[:6].decode("ascii", "replace")
            info = {"dwg_version": DWG_VERSIONS.get(code, code)}
            dxf, msg = convert_dwg(path)
            if not dxf:
                return "stored", f"DWG ({info['dwg_version']}) stored; not converted: {msg}", info
            info.update(inspect_dxf(dxf))
            render_svg(dxf, path.with_name("preview.svg"))
            return "ready", f"DWG ({info['dwg_version']}) {msg}: {info['entity_total']} entities", info
        if ext == ".pdf":
            info = inspect_pdf(path)
            return "ready", f"PDF, {info['pages']} page(s)", info
        if ext == ".dwf":
            return "stored", "DWF stored. It is a viewing format: geometry is not extracted; upload DWG or DXF", {}
        if ext == ".dwfx":
            info = inspect_dwfx(path)
            return "stored", "DWFX stored. It is a viewing format: geometry is not extracted; upload DWG or DXF", info
        if KINDS[ext] == "table":
            return "stored", "Table stored. SAFE/ETABS result import arrives at milestone M1", {}
        return "ready", "Image stored", {}
    except Exception as exc:  # report, don't crash the request
        return "failed", f"could not read file: {type(exc).__name__}: {exc}", {}
