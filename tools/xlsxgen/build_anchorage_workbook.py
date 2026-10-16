#!/usr/bin/env python3
"""Build the EN 1992-1-1 anchorage/lap calculation workbook (XLSX) with live formulas.

Usage: python tools/xlsxgen/build_anchorage_workbook.py <inputs.yaml> --design-basis <db.yaml> --out <file.xlsx>
Then:  python tools/xlsxgen/verify_workbook.py <file.xlsx> [--results CALC-ANCH-001.json]   (recalculates + checks)

Structure (company workbook rules, brief section 5):
  Cover   - control block, status (formula-driven), colour legend
  Inputs  - ONLY place with typed numbers: units, source, status, data validation
  Calc    - formulas only; no numeric literals except 0, 1 and the /4 of EN 1992-1-1 eq. 8.3
  Outputs - results + reconciliation with the drawing table (formulas)
  Checks  - independent hand-calculated expected values vs workbook results (PASS/FAIL formulas)
  Log     - change log
The workbook never labels itself 'validated'. Best automatic status is CROSS-CHECKED - NOT ENGINEER-REVIEWED.
"""
from __future__ import annotations

import argparse
import pathlib
import sys

import yaml
from openpyxl import Workbook
from openpyxl.comments import Comment
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.worksheet.properties import PageSetupProperties

FONT = "Arial"
BLUE = "0000FF"
INPUT_FILL = PatternFill("solid", fgColor="FFF2CC")
HEAD_FILL = PatternFill("solid", fgColor="D9D9D9")
SEC_FILL = PatternFill("solid", fgColor="EDEDED")
THIN = Side(style="thin", color="999999")
BOX = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
MAX_BARS = 8

# Hand-calculated expected values for the baseline inputs (C30/37, fyk 390, gamma_c 1.5, gamma_s 1.15, alpha_ct 1.0).
# Worked independently of the workbook formulas (see tests/test_phase5.py, which also cross-checks calc_lib):
#   fctd = 2.0/1.5 = 1.333333 ; fbd_good = 2.25*1.0*1.0*1.333333 = 3.000000 ; fbd_poor = 0.7*3.0 = 2.100000
#   fyd = 390/1.15 = 339.130435 ; lb_good(phi12) = (12/4)*339.130435/3.0 = 339.130435
#   lb_poor(phi12) = 3*339.130435/2.1 = 484.472050 ; lap_good(phi12) = 1.5*339.130435 = 508.695652
#   lb_good(phi25) = (25/4)*339.130435/3.0 = 706.521739 ; eta2(phi<=32)=1.0
HAND = [
    ("T1", "fctd, C30/37", 1.333333, 1e-5, "Calc!C5", "2.0 / 1.5"),
    ("T2", "fyd, fyk = 390 MPa", 339.130435, 1e-4, "Calc!C6", "390 / 1.15"),
    ("T3", "fbd good bond, phi 12 (MPa)", 3.0, 1e-5, "Calc!C11", "2.25 x 1.0 x 1.0 x 1.333333"),
    ("T4", "fbd poor bond, phi 12 (MPa)", 2.1, 1e-5, "Calc!D11", "0.7 x 3.000"),
    ("T5", "lb,rqd good, phi 12 (mm)", 339.130435, 1e-3, "Calc!E11", "(12/4) x 339.1304 / 3.000"),
    ("T6", "lb,rqd poor, phi 12 (mm)", 484.472050, 1e-3, "Calc!F11", "(12/4) x 339.1304 / 2.100"),
    ("T7", "lap l0 good, phi 12 (mm)", 508.695652, 1e-3, "Calc!G11", "1.5 x 339.1304"),
    ("T8", "lb,rqd good, phi 25 (mm)", 706.521739, 1e-3, "Calc!E14", "(25/4) x 339.1304 / 3.000"),
]


def f(ws, ref, value=None, *, bold=False, size=10, color=None, fill=None, fmt=None, wrap=False, border=False, italic=False, align=None):
    c = ws[ref]
    if value is not None:
        c.value = value
    c.font = Font(name=FONT, size=size, bold=bold, italic=italic, color=color)
    if fill:
        c.fill = fill
    if fmt:
        c.number_format = fmt
    if wrap or align:
        c.alignment = Alignment(wrap_text=wrap, vertical="top", horizontal=align)
    if border:
        c.border = BOX
    return c


def header(ws, row, labels, start_col=1):
    for i, lab in enumerate(labels):
        c = ws.cell(row=row, column=start_col + i, value=lab)
        c.font = Font(name=FONT, size=10, bold=True)
        c.fill = HEAD_FILL
        c.border = BOX
        c.alignment = Alignment(wrap_text=True, vertical="center")


def build(inp: dict, db: dict, out: pathlib.Path) -> dict:
    P, A = db["project"], db["approval"]
    wb = Workbook()
    cov, ws_in, ws_c, ws_o, ws_k, ws_l = (wb.active, wb.create_sheet("Inputs"), wb.create_sheet("Calc"),
                                          wb.create_sheet("Outputs"), wb.create_sheet("Checks"), wb.create_sheet("Log"))
    cov.title = "Cover"
    for ws, widths in ((cov, (30, 70, 20)), (ws_in, (22, 46, 14, 10, 52, 12)), (ws_c, (34, 12, 14, 14, 16, 16, 16, 16, 16, 16, 16)),
                       (ws_o, (10, 14, 14, 14, 12, 12, 10, 12, 12, 10, 12, 12, 10)), (ws_k, (6, 34, 14, 14, 12, 10, 18, 34)),
                       (ws_l, (14, 70, 20))):
        for i, w in enumerate(widths):
            ws.column_dimensions[chr(65 + i)].width = w

    # ------------------------------------------------------------------ Inputs
    f(ws_in, "A1", "INPUTS - EN 1992-1-1 anchorage and lap lengths", bold=True, size=12)
    f(ws_in, "A2", "Blue cells on yellow are the only cells to edit. Every value has a unit, source and status.", italic=True)
    header(ws_in, 3, ["Symbol", "Description", "Value", "Unit", "Source", "Status"])
    rows = {}

    def sec(r, title):
        for col in "ABCDEF":
            ws_in[f"{col}{r}"].fill = SEC_FILL
        f(ws_in, f"A{r}", title, bold=True, fill=SEC_FILL)

    def inp_row(r, key, sym, desc, val, unit, src, status, fmt=None):
        rows[key] = f"Inputs!$C${r}"
        f(ws_in, f"A{r}", sym, border=True)
        f(ws_in, f"B{r}", desc, wrap=True, border=True)
        f(ws_in, f"C{r}", val, color=BLUE, fill=INPUT_FILL, fmt=fmt, border=True)
        f(ws_in, f"D{r}", unit, border=True)
        f(ws_in, f"E{r}", src, wrap=True, border=True)
        f(ws_in, f"F{r}", status, border=True)

    sec(4, "Material inputs")
    inp_row(5, "cls", "concrete class", "Concrete strength class", inp["concrete_class"], "-", inp["sources"]["concrete"], "confirmed")
    inp_row(6, "fyk", "fyk", "Characteristic yield strength of reinforcement", inp["fyk"], "MPa", inp["sources"]["fyk"], "confirmed", "0.0")
    inp_row(7, "ovr", "fctk,0.05 override", "Leave BLANK to use EN 1992-1-1 Table 3.1 (table below)", None, "MPa", "User option", "-", "0.00")
    inp_row(8, "alt", "fctk,0.05 drawing basis", "Value implied by SD-004 (fbd = 3.04 MPa): 0.7 x fctm, fctm = 2.9 MPa", inp["compare_with"]["fctk005_override"], "MPa",
            "WH-STR-SD-004 section C note; EN 1992-1-1 Table 3.1 (fctm)", "confirmed", "0.00")
    sec(9, "Partial factors and coefficients (CEN recommended values, no National Annex)")
    inp_row(10, "gc", "gamma_c", "Partial factor, concrete", 1.5, "-", "EN 1992-1-1 Table 2.1N (CEN recommended)", "confirmed", "0.00")
    inp_row(11, "gs", "gamma_s", "Partial factor, reinforcing steel", 1.15, "-", "EN 1992-1-1 Table 2.1N (CEN recommended)", "confirmed", "0.00")
    inp_row(12, "act", "alpha_ct", "Long-term effects coefficient on tensile strength", 1.0, "-", "EN 1992-1-1 3.1.6(2)P (CEN recommended)", "confirmed", "0.00")
    inp_row(13, "a6", "alpha_6", "Lap factor, 50 % of bars lapped in the section", 1.5, "-", "EN 1992-1-1 Table 8.3", "confirmed", "0.00")
    sec(15, "Expression constants (EN 1992-1-1 eq. 8.2 and 3.1)")
    inp_row(16, "k", "2.25", "Coefficient in fbd = 2.25 x eta1 x eta2 x fctd", 2.25, "-", "EN 1992-1-1 eq. 8.2", "confirmed", "0.00")
    inp_row(17, "e1g", "eta1 good", "Bond condition coefficient, good", 1.0, "-", "EN 1992-1-1 8.4.2(2)", "confirmed", "0.0")
    inp_row(18, "e1p", "eta1 poor", "Bond condition coefficient, poor", 0.7, "-", "EN 1992-1-1 8.4.2(2)", "confirmed", "0.0")
    inp_row(19, "e2l", "eta2 limit", "Bar diameter up to which eta2 = 1.0", 32, "mm", "EN 1992-1-1 8.4.2(2)", "confirmed", "0")
    inp_row(20, "e2a", "eta2 a", "eta2 = (a - phi)/b for phi above the limit: a", 132, "mm", "EN 1992-1-1 8.4.2(2)", "confirmed", "0")
    inp_row(21, "e2b", "eta2 b", "eta2 = (a - phi)/b: b", 100, "-", "EN 1992-1-1 8.4.2(2)", "confirmed", "0")
    sec(23, "EN 1992-1-1 Table 3.1: fctk,0.05 by class (extend only with values read from the standard)")
    classes = {"C25/30": 1.8, "C30/37": 2.0, "C35/45": 2.2, "C40/50": 2.5}
    for i, (k_, v) in enumerate(classes.items()):
        r = 24 + i
        f(ws_in, f"A{r}", k_, border=True)
        f(ws_in, f"B{r}", "fctk,0.05", border=True)
        f(ws_in, f"C{r}", v, color=BLUE, fill=INPUT_FILL, fmt="0.0", border=True)
        f(ws_in, f"D{r}", "MPa", border=True)
        f(ws_in, f"E{r}", "EN 1992-1-1 Table 3.1", border=True)
        f(ws_in, f"F{r}", "confirmed", border=True)
    sec(29, "Bar diameters (up to 8; leave unused rows blank)")
    bars = inp["bars"]
    for i in range(MAX_BARS):
        r = 30 + i
        f(ws_in, f"A{r}", f"bar {i + 1}", border=True)
        f(ws_in, f"B{r}", "Bar diameter", border=True)
        f(ws_in, f"C{r}", bars[i] if i < len(bars) else None, color=BLUE, fill=INPUT_FILL, fmt="0", border=True)
        f(ws_in, f"D{r}", "mm", border=True)
        f(ws_in, f"E{r}", "Project reinforcement schedule" if i < len(bars) else "", border=True)
        f(ws_in, f"F{r}", "confirmed" if i < len(bars) else "", border=True)
    sec(39, "Drawing values for reconciliation: WH-STR-SD-004 section C (leave blank to skip)")
    header(ws_in, 40, ["Bar", "", "lbd good (mm)", "lbd poor (mm)", "lap l0 good (mm)", "mandrel (mm)"])
    d = inp["compare_with"]["rows"]
    for i in range(MAX_BARS):
        r = 41 + i
        f(ws_in, f"A{r}", f"bar {i + 1}", border=True)
        for col, key in (("C", "good"), ("D", "poor"), ("E", "lap_good"), ("F", "mandrel")):
            val = d[key][i] if i < len(d[key]) else None
            f(ws_in, f"{col}{r}", val, color=BLUE, fill=INPUT_FILL, fmt="0", border=True)
    sec(50, "Reconciliation tolerance (drawing values are rounded on no single increment)")
    inp_row(51, "tmm", "tol_abs", "Absolute tolerance", 5, "mm", "Engineering judgement set in this workbook - confirm", "assumed", "0")
    inp_row(52, "trel", "tol_rel", "Relative tolerance (larger of the two applies)", 0.01, "-", "Engineering judgement set in this workbook - confirm", "assumed", "0.0%")

    # data validation
    dv_cls = DataValidation(type="list", formula1="=$A$24:$A$27", allow_blank=False, showErrorMessage=True,
                            errorTitle="Concrete class", error="Pick a class listed in the Table 3.1 block.")
    dv_fyk = DataValidation(type="decimal", operator="between", formula1="200", formula2="700", showErrorMessage=True,
                            errorTitle="fyk", error="fyk must be 200-700 MPa.")
    dv_fct = DataValidation(type="decimal", operator="between", formula1="0.5", formula2="5", allow_blank=True, showErrorMessage=True,
                            errorTitle="fctk,0.05", error="Enter 0.5-5 MPa or leave blank.")
    dv_fac = DataValidation(type="decimal", operator="between", formula1="0.5", formula2="3", showErrorMessage=True,
                            errorTitle="Factor", error="Factor must be 0.5-3.")
    dv_bar = DataValidation(type="decimal", operator="between", formula1="6", formula2="50", allow_blank=True, showErrorMessage=True,
                            errorTitle="Bar diameter", error="Bar diameter must be 6-50 mm or blank.")
    for dv, rng in ((dv_cls, "C5"), (dv_fyk, "C6"), (dv_fct, "C7:C8"), (dv_fac, "C10:C13"), (dv_bar, "C30:C37")):
        ws_in.add_data_validation(dv)
        dv.add(rng)
    ws_in["C6"].comment = Comment("Source: design basis M-REBAR (user-confirmed drawing value).", "Claude")
    ws_in.freeze_panes = "A4"

    R = rows
    # ------------------------------------------------------------------ Calc
    f(ws_c, "A1", "CALC - formulas only (no typed numbers)", bold=True, size=12)
    f(ws_c, "A2", "Clause references in the last column. Stresses MPa, lengths mm.", italic=True)
    header(ws_c, 3, ["Quantity", "", "Value", "Unit", "Expression / clause"])
    f(ws_c, "A4", "fctk,0.05 used", border=True)
    f(ws_c, "C4", f'=IF({R["ovr"]}<>"",{R["ovr"]},INDEX(Inputs!$C$24:$C$27,MATCH({R["cls"]},Inputs!$A$24:$A$27,0)))', fmt="0.000", border=True)
    f(ws_c, "D4", "MPa"); f(ws_c, "E4", "Table 3.1, or override")
    f(ws_c, "A5", "fctd", border=True)
    f(ws_c, "C5", f'={R["act"]}*C4/{R["gc"]}', fmt="0.000", border=True)
    f(ws_c, "D5", "MPa"); f(ws_c, "E5", "EN 1992-1-1 eq. 3.16: alpha_ct x fctk,0.05 / gamma_c")
    f(ws_c, "A6", "fyd = sigma_sd", border=True)
    f(ws_c, "C6", f'={R["fyk"]}/{R["gs"]}', fmt="0.0", border=True)
    f(ws_c, "D6", "MPa"); f(ws_c, "E6", "fyk / gamma_s")
    f(ws_c, "A7", "fctd, drawing basis", border=True)
    f(ws_c, "C7", f'={R["act"]}*{R["alt"]}/{R["gc"]}', fmt="0.000", border=True)
    f(ws_c, "D7", "MPa"); f(ws_c, "E7", "as above with fctk,0.05 = drawing basis")
    header(ws_c, 9, ["Bar phi (mm)", "eta2", "fbd good (MPa)", "fbd poor (MPa)", "lb,rqd good (mm)", "lb,rqd poor (mm)",
                     "lap l0 good (mm)", "lb good, dwg basis", "lb poor, dwg basis", "lap good, dwg basis"])
    f(ws_c, "A8", "eq. 8.2: fbd = 2.25 x eta1 x eta2 x fctd;  eq. 8.3: lb,rqd = (phi/4) x sigma_sd / fbd;  lap = alpha_6 x lb,rqd", italic=True)
    for i in range(MAX_BARS):
        r, ri = 10 + i, 30 + i
        g = f'IF($A{r}="","",'
        f(ws_c, f"A{r}", f'=IF(Inputs!$C${ri}="","",Inputs!$C${ri})', fmt="0", border=True)
        f(ws_c, f"B{r}", f'={g}IF($A{r}<={R["e2l"]},1,({R["e2a"]}-$A{r})/{R["e2b"]}))', fmt="0.00", border=True)
        f(ws_c, f"C{r}", f'={g}{R["k"]}*{R["e1g"]}*B{r}*$C$5)', fmt="0.000", border=True)
        f(ws_c, f"D{r}", f'={g}{R["k"]}*{R["e1p"]}*B{r}*$C$5)', fmt="0.000", border=True)
        f(ws_c, f"E{r}", f'={g}$A{r}/4*$C$6/C{r})', fmt="0.0", border=True)
        f(ws_c, f"F{r}", f'={g}$A{r}/4*$C$6/D{r})', fmt="0.0", border=True)
        f(ws_c, f"G{r}", f'={g}{R["a6"]}*E{r})', fmt="0.0", border=True)
        f(ws_c, f"H{r}", f'={g}$A{r}/4*$C$6/({R["k"]}*{R["e1g"]}*B{r}*$C$7))', fmt="0.0", border=True)
        f(ws_c, f"I{r}", f'={g}$A{r}/4*$C$6/({R["k"]}*{R["e1p"]}*B{r}*$C$7))', fmt="0.0", border=True)
        f(ws_c, f"J{r}", f'={g}{R["a6"]}*H{r})', fmt="0.0", border=True)
    f(ws_c, "A19", "Scope: basic required length only (alpha_1 to alpha_5 = 1.0, lb,min not applied); straight bars; CEN recommended values.", italic=True)
    ws_c.freeze_panes = "A10"

    # ------------------------------------------------------------------ Outputs
    f(ws_o, "A1", "OUTPUTS", bold=True, size=12)
    f(ws_o, "A2", "Results on the selected basis, and reconciliation with the drawing table on the drawing's own basis.", italic=True)
    header(ws_o, 4, ["Bar (mm)", "lb good (mm)", "lb poor (mm)", "lap good (mm)", "Dwg lbd good", "Dev (dwg-calc)", "Within tol?",
                     "Dwg lbd poor", "Dev", "Within tol?", "Dwg lap good", "Dev", "Within tol?"])
    for i in range(MAX_BARS):
        r, cr, ir = 5 + i, 10 + i, 41 + i
        show = f'IF(Calc!$A{cr}="","",'
        f(ws_o, f"A{r}", f"=Calc!A{cr}", fmt="0", border=True)
        f(ws_o, f"B{r}", f"=Calc!E{cr}", fmt="0", border=True)
        f(ws_o, f"C{r}", f"=Calc!F{cr}", fmt="0", border=True)
        f(ws_o, f"D{r}", f"=Calc!G{cr}", fmt="0", border=True)
        spec = (("E", "F", "G", "C", "H"), ("H", "I", "J", "D", "I"), ("K", "L", "M", "E", "J"))  # (drawing col, dev col, ok col, Inputs col, Calc dwg-basis col)
        for dcol, vcol, ocol, icol, ccol in spec:
            f(ws_o, f"{dcol}{r}", f'=IF(Inputs!${icol}${ir}="","",Inputs!${icol}${ir})', fmt="0", border=True)
            f(ws_o, f"{vcol}{r}", f'=IF(OR({dcol}{r}="",Calc!$A{cr}=""),"",{dcol}{r}-Calc!${ccol}{cr})', fmt="+0.0;-0.0;0.0", border=True)
            f(ws_o, f"{ocol}{r}", f'=IF({vcol}{r}="","",IF(ABS({vcol}{r})<=MAX({R["tmm"]},{R["trel"]}*Calc!${ccol}{cr}),"YES","NO"))', border=True, align="center")
    f(ws_o, "A14", "All drawing values within tolerance (drawing basis)?", bold=True)
    f(ws_o, "F14", '=IF(COUNTIF(G5:G12,"NO")+COUNTIF(J5:J12,"NO")+COUNTIF(M5:M12,"NO")=0,"YES","NO")', bold=True, border=True, align="center")
    f(ws_o, "A15", "Dev columns compare the drawing with the calculation on the drawing basis (fctk,0.05 = Inputs C8); "
                   "columns B-D use the basis selected on Inputs (Table 3.1 unless overridden).", italic=True)
    f(ws_o, "A17", "Mandrel check (EN 1992-1-1 8.3(1)): 4 phi for phi <= 16 mm, 7 phi above", bold=True)
    header(ws_o, 18, ["Bar (mm)", "EN mandrel (mm)", "Drawing (mm)", "Matches?"])
    for i in range(MAX_BARS):
        r, cr, ir = 19 + i, 10 + i, 41 + i
        f(ws_o, f"A{r}", f"=Calc!A{cr}", fmt="0", border=True)
        f(ws_o, f"B{r}", f'=IF(A{r}="","",IF(A{r}<=16,4,7)*A{r})', fmt="0", border=True)
        f(ws_o, f"C{r}", f'=IF(Inputs!$F${ir}="","",Inputs!$F${ir})', fmt="0", border=True)
        f(ws_o, f"D{r}", f'=IF(OR(A{r}="",C{r}=""),"",IF(B{r}=C{r},"YES","NO - CHECK"))', border=True, align="center")
    f(ws_o, "A28", "Mandrel rule values 16 / 4 / 7 are EN 1992-1-1 Table 8.1 constants; they are the only typed numbers outside Inputs and are not design inputs.", italic=True)

    # ------------------------------------------------------------------ Checks
    f(ws_k, "A1", "CHECKS - independent hand calculations vs workbook results", bold=True, size=12)
    f(ws_k, "A2", "Expected values were worked by hand for the baseline inputs below. If inputs change, checks show N/A (they no longer apply).", italic=True)
    f(ws_k, "B3", "Baseline inputs in use?", bold=True)
    f(ws_k, "C3", f'=IF(AND({R["cls"]}="C30/37",{R["fyk"]}=390,{R["ovr"]}="",{R["gc"]}=1.5,{R["gs"]}=1.15,{R["act"]}=1,{R["a6"]}=1.5,'
                  f'Inputs!$C$30=10,Inputs!$C$31=12,Inputs!$C$32=16,Inputs!$C$33=20,Inputs!$C$34=25),"YES","NO")', bold=True, border=True)
    header(ws_k, 4, ["ID", "Test", "Expected (hand)", "Workbook", "Difference", "Tolerance", "Result", "Hand calculation"])
    for i, (tid, desc, exp, tol, ref, how) in enumerate(HAND):
        r = 5 + i
        f(ws_k, f"A{r}", tid, border=True)
        f(ws_k, f"B{r}", desc, wrap=True, border=True)
        f(ws_k, f"C{r}", exp, color=BLUE, fmt="0.000000", border=True)
        f(ws_k, f"D{r}", f"={ref}", fmt="0.000000", border=True)
        f(ws_k, f"E{r}", f"=D{r}-C{r}", fmt="0.000000", border=True)
        f(ws_k, f"F{r}", tol, color=BLUE, fmt="0.000000", border=True)
        f(ws_k, f"G{r}", f'=IF($C$3<>"YES","N/A - inputs changed",IF(ABS(E{r})<=F{r},"PASS","FAIL"))', bold=True, border=True)
        f(ws_k, f"H{r}", how, border=True)
    last = 5 + len(HAND) - 1

    # ------------------------------------------------------------------ Cover
    f(cov, "A1", "CALCULATION WORKBOOK - ANCHORAGE AND LAP LENGTHS", bold=True, size=14)
    f(cov, "A2", f'{P["code"]}_{P["name"]}', size=11)
    ctrl = [("Workbook number", f'{P["drawing_prefix"]}-WB-001'), ("Project", f'{P["code"]} {P["name"]}'), ("Client", P["client"]),
            ("Stage", P["stage"]), ("Revision", P["revision"]), ("Issue date", P["issue_date"]),
            ("Design basis status", A["status"]), ("Prepared by", A.get("prepared_by") or ""), ("Checked by", None), ("Approved by", None)]
    for i, (k_, v) in enumerate(ctrl):
        r = 4 + i
        f(cov, f"A{r}", k_, bold=True, border=True)
        f(cov, f"B{r}", v, border=True, color=BLUE if k_ in ("Checked by", "Approved by") else None,
          fill=INPUT_FILL if k_ in ("Checked by", "Approved by") else None)
    f(cov, "A15", "STATUS", bold=True, size=11)
    f(cov, "B15", f'=IF(COUNTIF(Checks!G5:G{last},"FAIL")>0,"CHECKS FAILING - DO NOT USE",IF(COUNTIF(Checks!G5:G{last},"PASS")=0,'
                  f'"UNVERIFIED - inputs differ from the checked baseline",IF(B12="","CROSS-CHECKED - NOT ENGINEER-REVIEWED","REVIEWED BY "&B12)))',
      bold=True, size=11, border=True, color="C00000")
    f(cov, "A16", "Stamp", bold=True)
    f(cov, "B16", '=IF(B10="APPROVED","","DRAFT - NOT FOR ISSUE")', bold=True, color="C00000")
    f(cov, "A18", "Colour legend", bold=True)
    f(cov, "A19", "Blue text on yellow", color=BLUE, fill=INPUT_FILL); f(cov, "B19", "Input - the only cells to edit (Inputs sheet, plus Checked/Approved by above)")
    f(cov, "A20", "Black text"); f(cov, "B20", "Formula or fixed label - do not overwrite")
    f(cov, "A22", "Sheets", bold=True)
    for i, (s, t) in enumerate((("Inputs", "all typed values with unit, source, status"), ("Calc", "formulas only"),
                                ("Outputs", "results and reconciliation with SD-004"), ("Checks", "hand-calculated tests"), ("Log", "change log"))):
        f(cov, f"A{23 + i}", s); f(cov, f"B{23 + i}", t)
    f(cov, "A29", "Limits: one check only (basic anchorage/lap length). Not a complete design. Status is never 'validated' without a named reviewer.", italic=True, wrap=True)
    cov.merge_cells("A29:B29")
    cov.row_dimensions[29].height = 30

    # ------------------------------------------------------------------ Log
    header(ws_l, 1, ["Date", "Change", "By"])
    f(ws_l, "A2", P["issue_date"], border=True)
    f(ws_l, "B2", "Workbook generated by tools/xlsxgen/build_anchorage_workbook.py; recalculated and verified by verify_workbook.py", wrap=True, border=True)
    f(ws_l, "C2", "Claude (generator)", border=True)

    for ws in wb.worksheets:  # print setup: landscape, one page wide
        ws.page_setup.orientation = "landscape"
        ws.page_setup.paperSize = ws.PAPERSIZE_A4
        ws.page_setup.fitToWidth, ws.page_setup.fitToHeight = 1, 0
        ws.sheet_properties.pageSetUpPr = PageSetupProperties(fitToPage=True)
    out.parent.mkdir(parents=True, exist_ok=True)
    wb.save(out)
    return {"path": str(out), "checks": len(HAND)}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("inputs")
    ap.add_argument("--design-basis", required=True)
    ap.add_argument("--out", required=True)
    ns = ap.parse_args(argv)
    inp = yaml.safe_load(open(ns.inputs, encoding="utf-8"))
    db = yaml.safe_load(open(ns.design_basis, encoding="utf-8"))
    print(build(inp, db, pathlib.Path(ns.out)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
