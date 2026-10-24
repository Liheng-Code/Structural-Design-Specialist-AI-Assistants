#!/usr/bin/env python3
"""Recalculate an anchorage workbook with LibreOffice and verify it. Exit 0 = all verification checks passed.

Usage: python 04_tools/xlsxgen/verify_workbook.py <file.xlsx> [--results CALC-ANCH-001.json] [--no-recalc]

Checks:
  1. recalculation succeeds (LibreOffice 'soffice' required) - file rewritten in place with cached values
  2. zero formula errors (#REF!, #NAME?, #VALUE!, #DIV/0!, #N/A) on any sheet
  3. Calc sheet: every non-empty cell is a formula or a label; formulas contain no numeric literals other than 0, 1, 4
  4. Checks sheet: every hand-calculated test is PASS (N/A is reported, not counted as pass)
  5. data validation present on Inputs
  6. tie-out: workbook results equal the report's results JSON (if given)
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

from openpyxl import load_workbook

ERRORS = ("#REF!", "#NAME?", "#VALUE!", "#DIV/0!", "#N/A", "#NUM!", "#NULL!")
ALLOWED_LITERALS = {"0", "1", "4"}
REF_RE = re.compile(r"(?:'[^']+'|[A-Za-z_][A-Za-z0-9_]*)!\$?[A-Z]{1,3}\$?\d+(?::\$?[A-Z]{1,3}\$?\d+)?|\$?[A-Z]{1,3}\$?\d+(?::\$?[A-Z]{1,3}\$?\d+)?")
STR_RE = re.compile(r'"[^"]*"')


def recalc(path: pathlib.Path) -> None:
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if not soffice:
        raise RuntimeError("LibreOffice (soffice) not found - cannot recalculate")
    tmp = pathlib.Path(tempfile.mkdtemp())
    subprocess.run([soffice, "--headless", "--convert-to", "xlsx:Calc MS Excel 2007 XML", "--outdir", str(tmp), str(path)],
                   check=True, capture_output=True, timeout=180)
    out = tmp / path.name
    if not out.exists():
        raise RuntimeError("recalculation produced no file")
    shutil.copyfile(out, path)


def literals_in(formula: str) -> list[str]:
    body = STR_RE.sub("", formula.lstrip("="))
    body = REF_RE.sub("", body)
    return [n for n in re.findall(r"(?<![A-Za-z_])\d+(?:\.\d+)?", body) if n not in ALLOWED_LITERALS]


def verify(path: pathlib.Path, results: dict | None = None, do_recalc: bool = True) -> dict:
    problems, notes = [], []
    if do_recalc:
        recalc(path)
    wf = load_workbook(path)                    # formulas
    wv = load_workbook(path, data_only=True)    # cached values

    n_formulas = 0
    for ws in wf.worksheets:
        for row in ws.iter_rows():
            for c in row:
                if isinstance(c.value, str) and c.value.startswith("="):
                    n_formulas += 1
                v = wv[ws.title][c.coordinate].value
                if isinstance(v, str) and v in ERRORS:
                    problems.append(f"{ws.title}!{c.coordinate} shows {v}")
                if isinstance(c.value, str) and c.value.startswith("=") and v is None and ws.title != "Calc":
                    pass  # empty-string results read back as None; only Calc/Outputs numbers matter below

    calc = wf["Calc"]
    for row in calc.iter_rows(min_row=3):
        for c in row:
            if c.value is None:
                continue
            if isinstance(c.value, (int, float)):
                problems.append(f"Calc!{c.coordinate} is a typed number ({c.value}); move it to Inputs")
            elif isinstance(c.value, str) and c.value.startswith("="):
                lit = literals_in(c.value)
                if lit:
                    problems.append(f"Calc!{c.coordinate} contains numeric literal(s) {lit}: {c.value}")

    ck = wv["Checks"]
    passed = failed = na = 0
    r = 5
    while ck[f"A{r}"].value:
        res = ck[f"G{r}"].value
        if res == "PASS":
            passed += 1
        elif res == "FAIL":
            failed += 1
            problems.append(f"Checks!{ck[f'A{r}'].value} FAILS: expected {ck[f'C{r}'].value}, workbook {ck[f'D{r}'].value}")
        else:
            na += 1
        r += 1
    if failed == 0 and passed == 0:
        notes.append("hand checks not applicable: inputs differ from the checked baseline")

    if not wf["Inputs"].data_validations.dataValidation:
        problems.append("Inputs sheet has no data validation")

    if results:
        calc_v = wv["Calc"]
        lb_g, lb_p, lap = results["results"]["lb_rqd_good"], results["results"]["lb_rqd_poor"], results["results"]["lap_basic_good"]
        for i, (a, b, c3) in enumerate(zip(lb_g, lb_p, lap)):
            row = 10 + i
            for col, exp in (("E", a), ("F", b), ("G", c3)):
                got = calc_v[f"{col}{row}"].value
                if got is None or abs(got - exp) > 0.06:  # results JSON is rounded to 0.1 mm
                    problems.append(f"tie-out: Calc!{col}{row} = {got} but report JSON = {exp}")
        notes.append(f"tie-out with report results checked for {len(lb_g)} bars")

    status = wv["Cover"]["B15"].value
    return {"formulas": n_formulas, "checks_passed": passed, "checks_failed": failed, "checks_na": na,
            "cover_status": status, "problems": problems, "notes": notes, "ok": not problems}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("xlsx")
    ap.add_argument("--results")
    ap.add_argument("--no-recalc", action="store_true")
    ns = ap.parse_args(argv)
    res = json.load(open(ns.results, encoding="utf-8")) if ns.results else None
    try:
        out = verify(pathlib.Path(ns.xlsx), res, not ns.no_recalc)
    except RuntimeError as e:
        print(f"VERIFICATION NOT POSSIBLE: {e}", file=sys.stderr)
        return 2
    print(json.dumps(out, indent=2))
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
