#!/usr/bin/env python3
"""Report which CAD / analysis software and Python libraries are available on THIS computer.

Run it on the PC that has AutoCAD/ETABS:   python 04_tools/cadgen/probe_cad.py
It only looks (PATH and standard install folders); it never launches or modifies anything.
Findings feed Phase 6 (DWG) and Phase 7 (ETABS/SAFE) - until it has been run there, availability is UNKNOWN.
"""
from __future__ import annotations

import glob
import importlib.util
import json
import os
import platform
import shutil

PATTERNS = {
    "AutoCAD (accoreconsole.exe - headless DWG/plot)": [r"C:\Program Files\Autodesk\AutoCAD*\accoreconsole.exe"],
    "AutoCAD (acad.exe)": [r"C:\Program Files\Autodesk\AutoCAD*\acad.exe"],
    "ODA File Converter (DXF<->DWG)": [r"C:\Program Files\ODA\ODAFileConverter*\ODAFileConverter.exe", "/usr/bin/ODAFileConverter*", "/Applications/ODAFileConverter.app"],
    "ETABS": [r"C:\Program Files\Computers and Structures\ETABS*\ETABS.exe"],
    "SAFE": [r"C:\Program Files\Computers and Structures\SAFE*\SAFE.exe"],
    "LibreOffice (PDF / XLSX recalculation)": [r"C:\Program Files\LibreOffice\program\soffice.exe"],
    "Microsoft Excel": [r"C:\Program Files\Microsoft Office\root\Office16\EXCEL.EXE", r"C:\Program Files (x86)\Microsoft Office\root\Office16\EXCEL.EXE"],
}
PATH_TOOLS = ["accoreconsole", "ODAFileConverter", "soffice", "libreoffice", "pdftoppm"]
LIBS = ["ezdxf", "matplotlib", "openpyxl", "docx", "yaml", "numpy", "PIL", "comtypes", "win32com"]


def main() -> int:
    found = {k: sorted(p for pat in v for p in glob.glob(pat)) for k, v in PATTERNS.items()}
    out = {
        "platform": platform.platform(),
        "python": platform.python_version(),
        "installed_software": {k: (v or "NOT FOUND in standard locations") for k, v in found.items()},
        "on_path": {t: shutil.which(t) or "not on PATH" for t in PATH_TOOLS},
        "python_libraries": {m: ("installed" if importlib.util.find_spec(m) else "missing") for m in LIBS},
        "note": "NOT FOUND means not in the standard folders searched; the software may exist elsewhere. DWG output needs AutoCAD or ODA File Converter.",
    }
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
