"""Cross-check: ADAPT-Builder calculation report (15 runs, 131 pages, NTS Post&Design, Oct 2019) vs 2F PT drawing data.
Usage: python check_vs_calc_note.py <cadgen_dir> <calc_pdf> <out_json>
All calc-note numbers are parsed from the PDF text (page-cited). Drawing strand counts come from the redrafted plan data
(tendon_coverage) - INDICATIVE, frame mapping is inferred from spans / column pattern."""
import sys, re, json, pathlib
CAD, PDF, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
sys.argv = [sys.argv[0], CAD, "/tmp/_u.json"]
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import pymupdf
import pt_2f_screening as S

doc = pymupdf.open(PDF)
pages = [p.get_text() for p in doc]
clean = lambda t: re.sub(r"\s*\n\s*", " ; ", re.sub(r"Project Name:.*?\n|File Name:.*?\n|email:.*?\n|1733 Woodside.*?\n", "", t))
starts = [i + 1 for i, t in enumerate(pages) if "1 - USER SPECIFIED GENERAL ANALYSIS" in t] + [len(pages) + 1]
runs = []
def seg(x, a, b):
    i = x.find(a)
    if i < 0: return ""
    j = x.find(b, i + len(a)); return x[i:(j if j > 0 else i + 3000)]
for r in range(len(starts) - 1):
    a, b = starts[r], starts[r + 1]
    x = clean("\n".join(pages[a - 1:b - 1])); x = re.sub(r"\d+===== ; \d+ ; ", "", x)
    d = dict(run=r + 1, pages=f"{a}-{b-1}")
    d["fse"] = re.search(r"Fse ; ([\d.]+)", x).group(1)
    d["fc"] = re.search(r"F'c  for BEAMS/SLABS ; ([\d.]+)", x).group(1)
    s72 = seg(x, "7.2 Selected", "Approximate")
    m = re.search(r"Tendon A ; Span ; Force.*?; CL ; (.*?) ; All Tendons", s72)
    forces = []
    if m:
        toks = m.group(1).split(" ; ")
        # rows: span, force, cgsL, cgsC1, cgsC2, cgsR, P/A, Wbal, %DL   (tokens separated by ' ; ')
        i = 0
        row = [t for t in toks]
        # find all 'force' values: token after span id
        forces = [float(row[k + 1]) for k in range(len(row) - 1) if re.fullmatch(r"\d+|CR", row[k]) and re.fullmatch(r"\d+\.\d+", row[k + 1]) and float(row[k + 1]) > 20]
    d["force_T_by_span"] = list(dict.fromkeys(forces))
    s75 = seg(x, "7.5 Service", "7.6 Post")
    s75 = s75[s75.find("kg/cm2 kg/cm2"):]
    vals = [float(v) for v in re.findall(r"(?<![\d.\-])(\d+\.\d\d)(?![\d])", s75)]
    d["max_service_tension_kgcm2"] = max(vals) if vals else None
    s132 = seg(x, "13.2 Critical Section Stresses", "13.3")
    toks = [t for t in s132.split(" ; ")]
    rat = []
    k = 0
    # rows start with a label int followed by layer; take last numeric of each row: split on pattern label ; layer ; cond
    rows = re.split(r" ; (?=\d+ ; (?:\d+|---) ; (?:\d+|---) ; )", s132[s132.find("ratio ; T ; T-m"):])
    for rw in rows:
        t = rw.split(" ; ")
        if len(t) >= 10 and t[1] != "---":
            try: rat.append((int(t[0]), float(t[9]), float(t[8])))      # joint, ratio, allowable
            except: pass
    d["punching"] = rat
    s141 = seg(x, "14.1 Maximum Span", "Note: Deflections")
    ratios = [int(v) for v in re.findall(r"\((\d+)\)", s141)]
    tot = []
    for rw in re.split(r" ; (?=\d+ ; \d|CL ; |CR ; )", s141):
        if rw.startswith(("CL", "CR")): continue
        m2 = re.findall(r"\((\d+|\*+)\)", rw)
        if m2 and m2[-1].isdigit(): tot.append(int(m2[-1]))
    d["worst_total_deflection_L_over"] = min(tot) if tot else None
    runs.append(d)

# ----------------------------- drawing side --------------------------------
geom = S.build_geometry(); X, Y = S.tendon_coverage(geom[5])
ycount = lambda x0, x1, y: sum(t["n"] for t in Y if x0 <= t["x"] <= x1 and t["y0"] <= y <= t["y1"])
xcount = lambda y0, y1, x: sum(t["n"] for t in X if y0 <= t["y"] <= y1 and t["x0"] <= x <= t["x1"])
T1 = 10.8   # T per strand at Fse 10.91 T/cm2 x 0.99 cm2 (calc note)
dw = {}
dw["Y_strip_9m"] = {f"x={xc}": dict(F_D=ycount(xc - 4.5, xc + 4.5, 19.5), D_C=ycount(xc - 4.5, xc + 4.5, 10.5), C_B=ycount(xc - 4.5, xc + 4.5, 5.3)) for xc in (10, 19, 28, 37)}
dw["X_Dline_y10.05_19.05"] = {f"x={x}": xcount(10.05, 19.05, x) for x in (2.8, 7.8, 14.5, 23.5, 32.5, 39.7, 44.2)}
dw["X_Bline_y3.95_9.55"] = {f"x={x}": xcount(3.95, 9.55, x) for x in (5, 14.5, 23.5, 32.5, 42)}
dw["X_Fline_y15.6_24.9"] = {f"x={x}": xcount(15.6, 24.9, x) for x in (5, 14.5, 23.5, 32.5, 42)}
dw["Y_edge_x-0.6_5.35"] = {f"y={y}": ycount(-0.6, 5.35, y) for y in (19.5, 10.5, 5.3)}
dw["T_per_strand"] = T1
json.dump(dict(runs=runs, drawing=dw), open(OUT, "w"), indent=1)
for d in runs: print(d["run"], d["pages"], d["fse"], d["force_T_by_span"], d["max_service_tension_kgcm2"], d["punching"], d["worst_total_deflection_L_over"])
print(json.dumps(dw, indent=1))
