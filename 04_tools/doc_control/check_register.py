#!/usr/bin/env python3
"""Check a document register (CSV) against the company drawing-number/revision rules and the design basis.

Usage:  python check_register.py <register.csv> [--design-basis design-basis.yaml]

Register columns (header row required):
  sheet_number, sheet_name, paper, revision, issue_date, stage, status
Rules (derived from WH-STR-SD Drawing Set R00 - see 01_standards/03-drawing-index):
  * sheet_number = <drawing_prefix>-<TYPE>-<NNN>   e.g. WH-STR-SD-101
  * NNN unique; series 001 cover, 002 list, 003-099 general notes, 1xx layouts, 2xx details
  * revision matches R00 / P01 / C01 style; date DD-MMM-YYYY
  * every row in one register shares the project revision stated in the design basis (if given)
Exit 0 = no errors, 1 = errors.
"""
from __future__ import annotations

import argparse
import csv
import re
import sys

try:
    import yaml
except ImportError:  # design-basis cross-check is optional
    yaml = None

NUM_RE = re.compile(r"^(?P<prefix>[A-Z]{2,4}-STR)-(?P<type>[A-Z]{2})-(?P<nnn>\d{3})$")
REV_RE = re.compile(r"^(R|P|C)\d{2}$")
DATE_RE = re.compile(r"^\d{2}-[A-Z]{3}-\d{4}$")
PAPERS = {"A0", "A1", "A2", "A3", "A4"}
COLS = ["sheet_number", "sheet_name", "paper", "revision", "issue_date", "stage", "status"]


def check(rows, db=None):
    out = []
    err = lambda r, m: out.append(("ERROR", r, m))
    warn = lambda r, m: out.append(("WARNING", r, m))
    seen = {}
    for n, row in enumerate(rows, start=2):
        ref = row.get("sheet_number") or f"row {n}"
        m = NUM_RE.match(row.get("sheet_number", ""))
        if not m:
            err(ref, "sheet_number does not match <XX>-STR-<TYPE>-<NNN>")
        else:
            if ref in seen:
                err(ref, f"duplicate of row {seen[ref]}")
            seen[ref] = n
            nnn = int(m["nnn"])
            if nnn == 1 and "COVER" not in row["sheet_name"].upper():
                warn(ref, "sheet 001 is conventionally the cover page")
            if nnn == 2 and "LIST" not in row["sheet_name"].upper() and "INDEX" not in row["sheet_name"].upper():
                warn(ref, "sheet 002 is conventionally the drawing list")
            if db and m["prefix"] != db["project"]["drawing_prefix"]:
                err(ref, f"prefix {m['prefix']} != design basis {db['project']['drawing_prefix']}")
        if not row.get("sheet_name", "").strip():
            err(ref, "sheet_name empty")
        if row.get("paper") not in PAPERS:
            err(ref, f"paper '{row.get('paper')}' not in {sorted(PAPERS)}")
        if not REV_RE.match(row.get("revision", "")):
            err(ref, f"revision '{row.get('revision')}' invalid")
        elif db and row["revision"] != db["project"]["revision"]:
            warn(ref, f"revision {row['revision']} differs from design basis {db['project']['revision']} (ok only if sheet was individually revised)")
        if not DATE_RE.match(row.get("issue_date", "").upper()):
            err(ref, "issue_date must be DD-MMM-YYYY")
        if db and row.get("stage") and row["stage"] != db["project"]["stage"]:
            warn(ref, f"stage '{row['stage']}' differs from design basis '{db['project']['stage']}'")
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("register")
    ap.add_argument("--design-basis")
    a = ap.parse_args(argv)
    with open(a.register, newline="", encoding="utf-8-sig") as fh:
        rd = csv.DictReader(fh)
        missing = [c for c in COLS if c not in (rd.fieldnames or [])]
        if missing:
            print(f"ERROR   header: missing columns {missing}")
            return 1
        rows = list(rd)
    db = None
    if a.design_basis:
        if yaml is None:
            sys.exit("PyYAML needed for --design-basis")
        with open(a.design_basis, encoding="utf-8") as fh:
            db = yaml.safe_load(fh)
    res = check(rows, db)
    for s, r, m in res:
        print(f"{s:7} {r}: {m}")
    errs = sum(1 for s, *_ in res if s == "ERROR")
    print(f"\n{len(rows)} sheet(s), {errs} error(s), {len(res) - errs} warning(s)")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
