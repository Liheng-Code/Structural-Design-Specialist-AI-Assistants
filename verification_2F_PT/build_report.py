import json, sys, datetime
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.section import WD_ORIENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

R = json.load(open(sys.argv[1])); OUT = sys.argv[2]
B = R["variants"]["base"]; P = R["params"]
CH = B["checks"]
d = Document()
sec = d.sections[0]
sec.page_width, sec.page_height = Cm(21.0), Cm(29.7)
for a in ("left_margin", "right_margin"): setattr(sec, a, Cm(1.8))
sec.top_margin = Cm(1.8); sec.bottom_margin = Cm(1.8)
st = d.styles["Normal"]; st.font.name = "Arial"; st.font.size = Pt(9)
st.element.rPr.rFonts.set(qn("w:eastAsia"), "Arial")

def shade(cell, hexcol):
    tcPr = cell._tc.get_or_add_tcPr(); sh = OxmlElement("w:shd")
    sh.set(qn("w:val"), "clear"); sh.set(qn("w:color"), "auto"); sh.set(qn("w:fill"), hexcol); tcPr.append(sh)

def H(txt, lvl=1):
    p = d.add_heading(txt, level=lvl)
    for r in p.runs: r.font.name = "Arial"; r.font.color.rgb = RGBColor(0x1F, 0x2A, 0x44)
    return p

def para(txt, bold=False, italic=False, size=9, color=None):
    p = d.add_paragraph(); r = p.add_run(txt); r.bold = bold; r.italic = italic; r.font.size = Pt(size)
    if color: r.font.color.rgb = RGBColor(*color)
    p.paragraph_format.space_after = Pt(3)
    return p

def bullet(txt):
    p = d.add_paragraph(style="List Bullet"); r = p.add_run(txt); r.font.size = Pt(9); p.paragraph_format.space_after = Pt(1)

def table(head, rows, widths=None, size=8, status_col=None):
    t = d.add_table(rows=1, cols=len(head)); t.style = "Table Grid"
    for i, h in enumerate(head):
        c = t.rows[0].cells[i]; c.text = ""; r = c.paragraphs[0].add_run(h); r.bold = True; r.font.size = Pt(size); shade(c, "D9E1F2")
    for row in rows:
        cells = t.add_row().cells
        for i, v in enumerate(row):
            cells[i].text = ""; r = cells[i].paragraphs[0].add_run(str(v)); r.font.size = Pt(size)
            if status_col is not None and i == status_col:
                s = str(v)
                if s.startswith("NOT OK"): shade(cells[i], "F8CBAD")
                elif s.startswith("NOT CHECKED"): shade(cells[i], "FFE699")
                elif s.startswith("OK"): shade(cells[i], "C6E0B4")
    if widths:
        for row in t.rows:
            for i, w in enumerate(widths): row.cells[i].width = Cm(w)
    d.add_paragraph().paragraph_format.space_after = Pt(2)
    return t

f2 = lambda x: f"{x:.2f}"
f1 = lambda x: f"{x:.1f}"
f0 = lambda x: f"{x:.0f}"

# ------------------------------------------------------------------ cover
t = d.add_paragraph(); r = t.add_run("2F POST-TENSIONED SLAB - INDICATIVE DESIGN VERIFICATION (SCREENING)"); r.bold = True; r.font.size = Pt(15)
para("Source design: Success Design & Build Co., Ltd - sheets 14-16 of 50, Rev 01, 22-Aug-2023 (2F PT layout and tendon profiles). Redrafted by CMED for review.", size=9)
table(["Item", "Value"], [
    ["Report no.", "TBC (project code not assigned in a design basis)"],
    ["Revision / date", f"Draft A / {datetime.date.today().strftime('%d-%b-%Y').upper()}"],
    ["Stage", "INDICATIVE SCREENING - NOT A SIGN-OFF - NOT FOR CONSTRUCTION"],
    ["Prepared by", "Claude (AI-assisted calculation)"],
    ["Checked by / Approved by", "_______________ (human engineer - not completed)"],
    ["Design basis", "No design-basis file exists for this project. Inputs are listed in sections C and D with their status (CONFIRMED / ASSUMED)."],
], widths=[4, 13])
para("Status vocabulary: OK / NOT OK / NOT CHECKED (missing input). 'indicative' means the result depends on at least one ASSUMED input or a simplified method. "
     "Nothing in this report is APPROVED; a 'calculated OK' is not 'engineer approved'.", italic=True, size=8.5)

# ------------------------------------------------------------------ summary
H("1. Answer in brief", 1)
para("Can this design be shown adequate? Not from the information available. Under the stated assumptions the screening finds no single failure that is certain, but it finds several items that do not pass and cannot be cleared without data that is not on the source sheets (mild reinforcement, stressing records, wall/core supports).", bold=True)
def cnt(g, case=None, comb=None):
    L = [c for c in CH if c.get("group") == g and c["util"] is not None and c.get("comb", "QP") != "TRANSFER" and (case is None or c["case"][0] == case) and (comb is None or c.get("comb") == comb)]
    return L
svA = cnt("service", "A"); svB = cnt("service", "B")
bullet("Service stress (tension vs fctm): panel-average strip (case A) exceeds the limit at Y-direction midspan of the 9.5 m span (y 14.8 to 24.3 m) and, under the frequent combination, at the 10 m X-direction end spans. "
       "Utilisations are 1.0 to 1.1 - at the cracking threshold, not far beyond it. Column-strip bracket (case B) is worse (up to 1.7).")
bullet("Support (hogging) regions: pass only if the drop panel / band beam acts as a 0.45 m section; with the 0.25 m slab section they exceed fctm (utilisation 1.4 to 1.6 on the panel average, up to 3.0 on the column strip). The real value lies between; drop-panel width (3.0 m) vs column-strip width (4.25 m) decides it.")
bullet("ULS flexure: the tendons alone cannot carry the ULS moments in several spans and supports. The design therefore relies on mild reinforcement that is not on the sheets supplied. Supplementary steel of about 0.1 to 2.3 x 10^3 mm2/m would be needed (section G4). NOT CHECKED, not 'failed'.")
bullet("Punching: 10 of 20 columns exceed vRd,c on tendon-only reinforcement. Interior C4 columns are marginal (1.02 to 1.10). Edge and corner C1 columns are 1.16 to 2.08 and depend strongly on how much slab they carry; wall/core support around the shafts is not modelled, so these are conservative. Mild steel or punching reinforcement is not given: NOT CHECKED.")
bullet("Deflection: uncracked strip-average deflection is 0.1 to 0.4 of L/250. OK (indicative); it would increase if the slab cracks.")
bullet("Load balancing: tendon profiles as drawn balance 98 % (X) and 86 % (Y) of self-weight - a reasonable range. Total drawn prestress is about 1.1 to 1.2 MPa on average, with local lows of 0.5 to 0.8 MPa.")
bullet("Drawing consistency: for 19 of 32 tendon marks the sheet-16 profile length does not equal the plan length (gap register G24). Until the engineer of record explains this, the profile-based load balancing is itself uncertain.")
bullet("Cracking: the service-stress result (at or just above the tensile strength at midspans) is consistent with cracks appearing under service load, and restrained shrinkage / temperature in a 47 m slab (section G8) can add up to about 3.3 MPa of net tension across the parameter range (G8). The screening cannot separate these causes. See section K.")

# ------------------------------------------------------------------ A-B
H("A. Scope and structure", 2)
para("Level +3.100 slab, bonded PT flat slab 0.25 m thick, drop panels (DP) and band beams (BB1/BB2) 0.45 m thick, 47.0 m x ~21.2 m with 12 voids. Columns: C1 600, C3 800, C4 1100 mm (square assumed). "
     f"Net slab area from the redrafted plan: {R['area_slab_net']:.1f} m2 (source states 829.05 m2; difference {100*(R['area_slab_net']/829.05-1):.1f} %).")
H("B. Codes", 2)
para("EN 1992-1-1 (CEN recommended values; no National Annex is recorded in a design basis), EN 1990 (combinations), EN 1991-1-1 (unit weight 25 kN/m3). Annex I of EN 1992-1-1 (informative) is used for column-strip / middle-strip shares. ACI / PTI are not used.")

H("C. Materials and PT system", 2)
table(["Symbol", "Value", "Unit", "Source", "Status"], [
    ["fck / fci", f"{P['fck']:.0f} / {P['fci']:.0f}", "MPa", "Drawing general note 1", "CONFIRMED"],
    ["Cover (to nearest reinforcement)", "20", "mm", "Drawing note 1", "CONFIRMED"],
    ["Strand", "12.7 mm, 7-wire, low relaxation, ASTM A416; Ap = 98.7", "mm2", "Drawing note 2 (grade not stated); skill reference value", "CONFIRMED / grade ASSUMED"],
    ["fpk (Gr.270)", f"{P['fpk']:.0f}", "MPa", "ASTM A416 Gr.270 typical (your choice)", "ASSUMED - CONFIRM"],
    ["fp0.1k", f"{P['fp01k']:.0f}", "MPa", "0.9 fpk (skill: yield ~1675)", "ASSUMED - CONFIRM"],
    ["Jacking stress", "0.75 fpk", "-", "Typical practice", "ASSUMED - CONFIRM"],
    ["Jacking force per strand", f2(B["Pj"]), "kN", "calc", "derived from assumed"],
    ["Total losses", f"{100*P['loss']:.0f} %  (immediate {100*P['imm_frac']:.0f} %)", "-", "Your choice (typical)", "ASSUMED - CONFIRM"],
    ["Effective force per strand Pe", f2(B["Pe"]), "kN", "calc", "derived from assumed"],
    ["gamma_c / gamma_s", "1.5 / 1.15", "-", "EN 1992-1-1 recommended", "CEN recommended"],
    ["Mild reinforcement", "Not given (general note only: SD40 fy 400 MPa)", "-", "Drawing note 3", "MISSING - quantities unknown"],
    ["Exposure class", "Not given; XC1 assumed for interior", "-", "-", "MISSING"],
    ["Creep coefficient phi", "2.0", "-", "-", "ASSUMED"],
    ["Effective depth d (slab / thick zone)", "0.20 / 0.40", "m", "t - 50 mm", "ASSUMED"],
], widths=[3.6, 4.6, 1.2, 4.6, 3.2], size=7.5)

H("D. Actions", 2)
ld = B["loads"]
table(["Action", "Value (kN/m2)", "Source"], [
    ["Self-weight slab 0.25 m x 25", f2(ld["sw"]), "EN 1991-1-1 Table A.1 (25 kN/m3); DP/BB extra weight not added (small, conservative omission)"],
    ["SDL 250 KSM", f2(ld["sdl"]), "Drawing plan note (1 kg/m2 = 0.00981 kN/m2)"],
    ["LL 500 KSM", f2(ld["ll"]), "Drawing plan note. Note: PT-skill defaults are SDL 4.65 / LL 2.50 - they differ; sensitivity in section J"],
], widths=[5, 3, 9])
H("E. Combinations (EN 1990)", 2)
table(["Combination", "Expression", "q (kN/m2)"], [
    ["ULS (6.10)", "1.35 G + 1.5 Q", f2(ld["uls"])],
    ["SLS frequent", f"G + psi1 Q  (psi1 = {P['psi1']}, ASSUMED category C)", f2(ld["freq"])],
    ["SLS quasi-permanent", f"G + psi2 Q  (psi2 = {P['psi2']}, ASSUMED category C)", f2(ld["qp"])],
    ["Transfer", "Self-weight only, force at transfer", f2(ld["sw"])],
], widths=[4, 9, 3])

H("F. Method and provenance", 2)
for s_ in [
    "Geometry, tendon counts and lengths: transcribed from the source vector data (redraft_2f_pt.py, +/-0.3 m). Tendon profiles: sheet 16 (profiles_2F_PT.json, 683 stations).",
    "Prestress per section: strands crossing each section x Pe, divided by the net slab width at that section and 0.25 m (no credit for thicker zones).",
    "Load balancing: per tendon and span, w = 8 P a / L2 from the drawn profile; two drape definitions give a lower and an upper value (lower used). Each direction carries the full load (equivalent-frame practice); net load = combination minus balanced load.",
    "Strips: 1 m wide continuous strip on pinned supports (column stiffness neglected), Y strip supports at y = 4.3, 6.3, 14.8, 24.3 m; X strip at x = 0, 10, 19, 28, 37, 47 m. Solver verified against hand values (two equal spans: -wL2/8, 9wL2/128).",
    "Two cases bracket the answer: A = panel-average strip (moment on the full panel width); B = EN 1992-1-1 Annex I column strip (80 % hogging / 70 % sagging in a strip 0.25 x span each side), with the thick zone width 3.0-3.1 m at drop panels.",
    "Punching: reaction = q_ULS x tributary area, with the tributary area obtained by assigning every point of the net slab to the nearest column. Voids are excluded. Walls / cores are NOT modelled as supports (not identified on the sheets).",
    "ULS flexure: rectangular block, PT only, tendon stress fp0.1k/gamma_s; hyperstatic prestress moments NOT included.",
    "Calculation code: calc_lib/ec2_pt_screen.py and calc_lib/runs/pt_2f_screening.py, tests in tests/test_ec2_pt_screen.py (5 hand-value tests pass).",
]: bullet(s_)

# ------------------------------------------------------------------ G
H("G. Checks", 1)
H("G1. Prestress and average precompression", 2)
pc = B["precomp"]
table(["Direction", "Strands (total)", "Strands per m (mean)", "sigma_cp min / mean / max (MPa)"], [
    ["X", pc["n_total"]["X"], f2(pc["X"]["n_per_m"]), f"{f2(pc['X']['min'])} / {f2(pc['X']['mean'])} / {f2(pc['X']['max'])}"],
    ["Y", pc["n_total"]["Y"], f2(pc["Y"]["n_per_m"]), f"{f2(pc['Y']['min'])} / {f2(pc['Y']['mean'])} / {f2(pc['Y']['max'])}"],
], widths=[3, 4, 4.5, 5.5])
lowx = [(v[0], v[3]) for v in pc["sx"] if v[3] and v[3] < 0.9]; lowy = [(v[0], v[3]) for v in pc["sy"] if v[3] and v[3] < 0.9]
para("Local lows: X at x = " + ", ".join(f"{a:.1f} ({b:.2f})" for a, b in lowx[:8]) + " m;  Y at y = " + ", ".join(f"{a:.1f} ({b:.2f})" for a, b in lowy[:8]) +
     " m. EN 1992-1-1 does not set a minimum average prestress; these are reported as local lows only. X tendons are banded, so values between bands are lower and values in bands higher than this average.", size=8.5)

H("G2. Load balancing", 2)
rows = []
for c in CH:
    if c["id"].startswith("LB-"):
        rows.append([c["id"][-1], f2(c["demand"]), f"{100*c['pct_sw'][0]:.0f} - {100*c['pct_sw'][1]:.0f} %", f"{100*c['pct_G'][0]:.0f} - {100*c['pct_G'][1]:.0f} %", f"{100*c['pct_qp'][0]:.0f} - {100*c['pct_qp'][1]:.0f} %"])
table(["Direction", "Balanced load (kPa, lower)", "% of self-weight (lo-hi)", "% of G (SW+SDL)", "% of quasi-permanent"], rows, widths=[2, 4, 4, 3.5, 3.5])
para("The profile heights were scaled by plan length / profile length for the 19 marks where they disagree (G24); that scaling is a screening device, not a design value.", size=8.5)

H("G3. Service stresses (tension against fctm = 3.02 MPa; fctk,0.05 = 2.12 MPa)", 2)
para("Tension shown, quasi-permanent / frequent. Utilisation = tension / fctm. Cracking can start below fctm; the 5 % fractile gives utilisations 1.43 times higher.", size=8.5)
rows = []
locs = []
for c in CH:
    if c.get("group") == "service" and c["comb"] == "QP":
        key = (c["dir"], c["loc"], c["case"])
        locs.append((key, c))
for key, c in locs:
    f = next(x for x in CH if x.get("group") == "service" and x["comb"] == "FREQ" and x["id"] == c["id"].replace("-QP-", "-FREQ-"))
    s_ = max(c["status"], f["status"], key=lambda z: (z.startswith("NOT"), z))
    st_ = "NOT OK (indicative)" if (c["util"] > 1 or f["util"] > 1) else "OK (indicative)"
    rows.append([c["dir"], c["loc"], c["case"], f2(c["sig_p"]), f1(c["m"]), f"{f2(c['demand'])} / {f2(f['demand'])}", f"{f2(c['util'])} / {f2(f['util'])}", st_])
table(["Dir", "Location", "Case", "sigma_p MPa", "m kNm/m (QP)", "Tension MPa QP / FREQ", "Util QP / FREQ", "Status"], rows, widths=[0.9, 3.1, 4.0, 1.5, 1.8, 2.4, 2.0, 2.4], size=7, status_col=7)

H("G4. ULS flexure (EN 1992-1-1 6.1), tendons only", 2)
para("MEd from the external ULS load on the strip; hyperstatic prestress moment not included; no mild steel credited. As,req is the supplementary bonded steel (fyd = 348 MPa, z = 0.9 d) needed to close the gap. Because mild reinforcement is not available, utilisations above 1.00 are NOT CHECKED, not failed.", size=8.5)
rows = []
for c in CH:
    if c.get("group") == "uls":
        rows.append([c["dir"], c["loc"], c["case"], f1(c["demand"]), f1(c["cap"]), f2(c["util"]), f0(c["As_req"]), c["status"]])
table(["Dir", "Location", "Case", "MEd kNm/m", "MRd (PT) kNm/m", "Util", "As,req mm2/m", "Status"], rows, widths=[0.9, 3.3, 2.5, 1.9, 2.3, 1.3, 2.2, 3.5], size=7, status_col=7)

H("G5. Punching shear (EN 1992-1-1 6.4)", 2)
para(f"beta = 1.15 / 1.4 / 1.5 (interior / edge / corner, 6.4.3(6) recommended). vRd,c uses bonded PT only for rho_l ({100*B['rho_punch']:.2f} %) and k1 sigma_cp (sigma_cp = {B['sig_cp']:.2f} MPa); no mild steel and no vertical tendon component credited. Square columns assumed. 'rho req' is the longitudinal reinforcement ratio that would make utilisation 1.00.", size=8.5)
rows = []
for c in CH:
    if c.get("group") == "punching" and (c["id"].startswith("PU-") or c["id"].startswith("PUout")):
        rows.append([c["id"].replace("PU-", "").replace("PUout-", "outside DP "), c.get("kind", "interior"), f1(c.get("trib", 0)) if "trib" in c else "", f0(c["V"]), f2(c["demand"]), f2(c["cap"]), f2(c["util"]), f"{100*c['rho_req']:.2f} %", c["status"]])
table(["Column", "Type", "Trib m2", "V kN", "vEd MPa", "vRd,c MPa", "Util", "rho req", "Status"], rows, widths=[3.3, 1.5, 1.3, 1.3, 1.5, 1.7, 1.2, 1.5, 3.7], size=7, status_col=8)
mx = [c for c in CH if c["id"].startswith("PUmax")]
para(f"Face check vEd,u0 / vRd,max: largest utilisation {max(c['util'] for c in mx):.2f} - OK (indicative).", size=8.5)

H("G6. Deflection (EN 1992-1-1 7.4.1)", 2)
rows = [[c["name"].split(",")[0].replace("Deflection ", ""), f1(c["demand"]), c["sign"], f1(c["cap"]), f2(c["util"]), c["status"]] for c in CH if c.get("group") == "deflection"]
table(["Span", "Deflection mm", "Direction", "L/250 mm", "Util", "Status"], rows, widths=[4, 2.5, 2.2, 2.5, 1.5, 4], size=7.5, status_col=5)
para(f"Uncracked, Ec,eff = Ecm/(1+phi) = {B['Ec'] / 1000 / 3.0:.1f} GPa, strip-average, QP net load, column stiffness neglected. Not a cracked-section or two-way plate result; the L/500 after-construction limit (7.4.1(5)) cannot be checked without the partition / finish sequence.", size=8.5)

H("G7. Transfer", 2)
tr = [c for c in CH if c.get("comb") == "TRANSFER"]
para(f"Self-weight with the transfer force (Pt = {B['Pt']:.1f} kN/strand, {100*P['imm_frac']:.0f} % immediate loss ASSUMED, fci = 24 MPa): largest tension utilisation {max(c['util'] for c in tr):.2f} (limit fctm(24) = 2.50 MPa) - OK (indicative). The net load is almost zero or upward in the X strip (net {B['strip_X']['net']['TRANSFER']:.2f} kPa): the tendons nearly balance self-weight at transfer, so check the camber and the stressing sequence.", size=9)

H("G8. Restraint, shrinkage and temperature (parametric - no code values)", 2)
para("A 47 m slab is tied to stiff cores / walls. No wall layout, pour sequence, shrinkage environment or temperature range is available, so strain values are PARAMETERS, not code values. sigma_t = R x eps x Ecm/(1+phi); net = sigma_t - mean X precompression. "
     "EN 1992-1-1 7.3.2 minimum reinforcement for restrained cracking (k = 1.0, kc = 1.0, fct,eff = 3.02 MPa, sigma_s = 400 MPa) is about 1.9 x 10^3 mm2/m (both faces) without prestress credit - cannot be compared as the mild steel is not given: NOT CHECKED.", size=8.5)
rows = []
for x in R["restraint"]:
    rows.append([f"{1000*x['eps']:.1f}", f"{x['R']:.1f}", f2(x["sigma_t"]), f2(x["net"]), "tension > 0" if x["net"] > 0 else "residual compression"])
table(["Free strain (per mille)", "Restraint R", "Restraint tension (MPa)", "Net after precompression (MPa)", "Note"], rows, widths=[3.5, 2.5, 3.5, 4, 3.5], size=7.5)

H("G9. Drawing consistency", 2)
c_ = R["consistency"]
bad = [f"{m} (plan {a}, profile {b} m)" for m, (a, b, ok) in c_["by_mark"].items() if not ok]
para(f"Strand numbers 1 to 205 are continuous (69 X + 136 Y). Marks used on the plan all exist on sheet 16 (32 of 32). For {c_['n_mismatch']} of {c_['n_marks']} marks the profile length differs from plan label length minus 0.5 m by more than 0.3 m (gap register G24):", size=8.5)
para("; ".join(bad), size=7.5)
para("Cover: profile low points of 4 to 6 cm to the tendon centre allow 20 mm cover only if the duct is not deeper than about 40 mm - duct size TBC. High points of 25 to 27 cm occur in a 25 cm slab only inside the 0.45 m DP / BB; confirm on the redrafted plan.", size=8.5)

# ------------------------------------------------------------------ H summary table
H("H. Results summary", 1)
def worst(group, case=None):
    L = [c for c in CH if c.get("group") == group and c["util"] is not None and c.get("comb", "QP") != "TRANSFER" and (case is None or c["case"][0] == case)]
    return max(L, key=lambda c: c["util"]) if L else None
rows = []
for lab, g, cs in [("Service tension - case A (panel average)", "service", "A"), ("Service tension - case B (column strip)", "service", "B"),
                   ("ULS flexure - case A, PT only", "uls", "A"), ("ULS flexure - case B, PT only", "uls", "B"), ("Deflection", "deflection", None)]:
    w = worst(g, cs); rows.append([lab, w["name"][:70], f2(w["util"]), w["status"]])
pu = [c for c in CH if c["id"].startswith("PU-")]; w = max(pu, key=lambda c: c["util"])
rows.append(["Punching u1", w["name"][:70], f2(w["util"]), w["status"]])
pu0 = [c for c in CH if c["id"].startswith("PUmax")]; w = max(pu0, key=lambda c: c["util"])
rows.append(["Punching u0 (vRd,max)", w["name"][:70], f2(w["util"]), w["status"]])
table(["Check", "Governing item", "Max util", "Status"], rows, widths=[4.5, 8, 1.5, 3.5], size=7.5, status_col=3)
para("Overall: ENGINEER REVIEW REQUIRED. Not marked PASS: assumed PT inputs, missing mild reinforcement, simplified strip method.", bold=True)

# ------------------------------------------------------------------ I
H("I. Assumptions to confirm and limitations", 1)
for s_ in [
    "ASSUMED: fpk 1860 MPa, fp0.1k 1674 MPa, jacking 0.75 fpk, total loss 18 % (8 % immediate), creep phi 2.0, psi1 = 0.7 / psi2 = 0.6 (category C), exposure XC1, effective depths t - 50 mm, square columns, typical panel width 9 m. Each needs the engineer-of-record value.",
    "MISSING: stressing records and elongations, pour sequence and dates, mild reinforcement schedule, calculation / design report of the original designer, wall and core layout (support to the slab around the shafts), actual concrete strength test results, ground / environment data, loading from the partition layout.",
    "Method limits: pinned-support strips; no column or wall stiffness; hyperstatic moments omitted; no two-way plate (FE) analysis; column strip shares from an informative annex; thick zone modelled by thickness brackets; tendon profile effects only as load-balanced averages.",
    "The ADAPT / SAFE comparison required by the PT skill (section 34) has not been done; use this report only to choose what to check there.",
    "Sheet-16 profile lengths disagree with the plan for 19 marks (G24) - transcription error or design inconsistency not resolved.",
]: bullet(s_)

# ------------------------------------------------------------------ J sensitivity
H("J. Sensitivity to the assumed inputs", 1)
rows = []
for tag, v in R["variants"].items():
    ch = v["checks"]
    def n_over(group, case=None):
        L = [c for c in ch if c.get("group") == group and c["util"] is not None and c.get("comb", "QP") != "TRANSFER" and (case is None or c["case"][0] == case)]
        return f"{sum(1 for c in L if c['util'] > 1)} / {len(L)}"
    pu_ = [c for c in ch if c["id"].startswith("PU-")]
    rows.append([tag, f1(v["Pe"]), f2(v["loads"]["qp"]), f"{v['qbal']['X'][0]:.1f} / {v['qbal']['Y'][0]:.1f}", n_over("service", "A"), n_over("service", "B"), n_over("uls", "A"), f"{sum(1 for c in pu_ if c['util']>1)} / {len(pu_)}"])
table(["Variant", "Pe kN/strand", "q QP kPa", "q bal X / Y", "Service A >1", "Service B >1", "ULS A >1", "Punching >1"], rows, widths=[5, 1.8, 1.5, 2.2, 1.8, 1.8, 1.6, 1.9], size=7.5)
para("Counts are checks with utilisation above 1.00 out of the checks evaluated. Higher losses or higher loads add failing checks; lower losses remove a few but not the ULS or punching items.", size=8.5)
H("Independent check record", 2)
for s_ in [
    "Pe = 0.75 x 1860 x 98.7 / 1000 x (1 - 0.18) = 112.9 kN - hand value matches.",
    "Y precompression at y = 8 m: 136 strands x 112.9 kN / (47.2 m x 0.25 m) = 1.30 MPa - matches the section table.",
    "C4 at (10, 14.8): V = 19.1 x 97.6 = 1864 kN; u1 = 4 x 1.1 + 2 pi x 0.8 = 9.43 m; vEd = 1.15 x 1864 / (9.43 x 0.40) = 0.57 MPa; vRd,c,min = 0.035 x 1.707^1.5 x 32^0.5 + 0.1 x 1.13 = 0.56 MPa - matches (util 1.02).",
    "Strip solver: two equal spans, support -wL2/8 and sagging 9wL2/128, and a 2 m cantilever -wc2/2 - all pass in tests/test_ec2_pt_screen.py.",
    "Not independently verified: balanced-load values (method UNVERIFIED against ADAPT), Annex I column strip shares, tributary allocation.",
]: bullet(s_)

H("K. What this says about the cracks (not a conclusion)", 1)
para("The screening points to three mechanisms that can each produce the kind of cracking seen, and the available data cannot rank them:", size=9)
for s_ in [
    "Service flexural tension at midspans and at supports where the effective thickness is only 0.25 m (utilisation about 1.0 to 1.5 on the panel-average strip). This is a design-stage cause (prestress level, tendon drape, section).",
    "Restrained shrinkage and temperature movement of a 47 m slab against cores / walls: 0 to 3.3 MPa net tension across the parameter range. PT shortening is also resisted by the same walls, which reduces the precompression that reaches the slab. This depends on the wall layout, pour strips and curing - mostly execution and detailing, partly design.",
    "Construction and stressing issues: low local precompression (0.5 to 0.8 MPa), stressing before the concrete reaches fci, tendon position errors, or the 19 profile / plan discrepancies if the tendons were built to the profile sheet. These need stressing records and as-built tendon levels.",
]: bullet(s_)
para("To decide whether the root cause is the design, the next data needed are: the crack survey overlaid on the plan and these results, the stressing records, the reinforcement schedule and the original design calculation.", size=9)
d.save(OUT)
print("saved", OUT)
