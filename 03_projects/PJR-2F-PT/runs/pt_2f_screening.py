"""2F PT slab - indicative screening run (EN 1992-1-1, CEN recommended values).  See report for assumptions.
Usage: python pt_2f_screening.py <redraft_data_dir> <out_json>
"""
import sys, json, math, copy, pathlib
import numpy as np
from shapely.geometry import Polygon, LineString, box
from shapely.ops import unary_union

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "04_tools"))
from calc_lib.pt import ec2_pt_screen as E

CAD = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else HERE.parent / "redraft"
sys.path.insert(0, str(CAD))
import redraft_2f_pt as R            # transcribed tendon + column data

BASE = dict(
    fck=32.0, fci=24.0, gc=1.5, gs=1.15,                       # CONFIRMED (drawing note 1); gc/gs CEN recommended
    fpk=1860.0, fp01k=1674.0, Ap=98.7, jack=0.75, loss=0.18,   # ASSUMED (ASTM A416 Gr.270 typical)
    imm_frac=0.08,                                             # ASSUMED split of total loss (immediate)
    t_slab=0.25, t_thick=0.45, cover=0.020,                    # CONFIRMED
    sdl_ksm=250.0, ll_ksm=500.0,                               # CONFIRMED (plan note)
    gam_c=25.0,                                                # EC1-1 Table A.1
    psi1=0.7, psi2=0.6,                                        # ASSUMED (EN 1990 A1.1 cat C)
    phi=2.0,                                                   # ASSUMED creep coefficient
    d_slab=0.20, d_thick=0.40,                                 # ASSUMED effective depths (t - 50 mm)
    share_hog=0.80, share_sag=0.70,                            # EN 1992-1-1 Annex I Table I.1 upper bounds (informative annex)
    area_src=829.05,
)


def build_geometry():
    plan = json.load(open(CAD / "plan_2F_PT.json"))
    red = [(pts, cl[0] if cl else False) for pts, *cl in plan["red"]]
    polys = []
    for pts, closed in red:
        if len(pts) < 4:
            continue
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        polys.append((Polygon(pts).buffer(0), (min(xs), max(xs), min(ys), max(ys)), closed))
    outline = max(polys, key=lambda p: p[0].area)[0]
    voids = [p for p, b, c in polys if c and p.area > 1e6 and p is not outline and min(b[1] - b[0], b[3] - b[2]) > 1500]
    slab = outline.difference(unary_union(voids))
    cyan = []
    for pts, cl in plan["cyan"]:
        if cl and len(pts) >= 4:
            cyan.append(Polygon(pts).buffer(0))
    green = plan["green"]
    return plan, outline, voids, slab, cyan, green


def tendon_coverage(green):
    """Y: from vertical polylines paired with Y_TENDONS (sorted by x, as in the redraft).  X: flat/jog polylines matched by y."""
    verts = []
    for pts, t in green:
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        if max(xs) - min(xs) < 30 and max(ys) - min(ys) > 7000:
            verts.append((sum(xs) / len(xs), min(ys), max(ys)))
    verts.sort()
    Y = []
    for (x, y0, y1), (g, mark, n, a, b, L) in zip(verts, R.Y_TENDONS):
        Y.append(dict(group=g, mark=mark, n=n, x=x / 1000, y0=y0 / 1000, y1=y1 / 1000, L=L))
    H = []
    for pts, t in green:
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        if max(xs) - min(xs) > 3000:
            H.append((min(xs), max(xs), min(ys), max(ys)))
    X = []
    used = set()
    for (g, mark, n, a, b, L, my, side) in R.X_TENDONS:
        segs = []
        for i, (x0, x1, y0, y1) in enumerate(H):
            flat = abs(y0 - my) < 5 and abs(y1 - y0) < 5
            jog = 190 < (y0 - my) < 320 and (y1 - y0) > 1000
            if flat or jog:
                segs.append((i, x0, x1))
        if not segs:
            raise RuntimeError(f"no plan line for {mark} G{g}")
        # shared y (X5/X7, X6/X8, EX1/EX3, EX2/EX4): choose by side
        if len({s[0] for s in segs}) > 1 and all(abs(H[s[0]][2] - my) < 5 for s in segs):
            segs = sorted(segs, key=lambda s: s[1])
            segs = [segs[0]] if side == "L" else [segs[-1]]
        X.append(dict(group=g, mark=mark, n=n, x0=min(s[1] for s in segs) / 1000, x1=max(s[2] for s in segs) / 1000, y=my / 1000, side=side, L=L))
    return X, Y


def loads(p):
    sw = p["t_slab"] * p["gam_c"]
    sdl = p["sdl_ksm"] * E.KSM_TO_KPA
    ll = p["ll_ksm"] * E.KSM_TO_KPA
    G = sw + sdl
    return dict(sw=sw, sdl=sdl, ll=ll, G=G,
                uls=1.35 * G + 1.5 * ll, char=G + ll, freq=G + p["psi1"] * ll, qp=G + p["psi2"] * ll)


def pe_per_strand(p):
    Pj = p["jack"] * p["fpk"] * p["Ap"] / 1000.0
    return Pj, Pj * (1 - p["loss"]), Pj * (1 - p["imm_frac"])


def precompression(X, Y, slab, Pe, p):
    xs = np.arange(0.25, 47.0, 0.5); ys = np.arange(3.8, 24.9, 0.5)
    sx, sy = [], []
    for x in xs:
        n = sum(t["n"] for t in X if t["x0"] <= x <= t["x1"])
        w = LineString([(x * 1000, 0), (x * 1000, 30000)]).intersection(slab).length / 1000
        sx.append((x, n, w, n * Pe / w / p["t_slab"] / 1000 if w > 0.5 else None))
    for y in ys:
        n = sum(t["n"] for t in Y if t["y0"] <= y <= t["y1"])
        w = LineString([(-1000, y * 1000), (48000, y * 1000)]).intersection(slab).length / 1000
        sy.append((y, n, w, n * Pe / w / p["t_slab"] / 1000 if w > 0.5 else None))
    return sx, sy


def balanced(prof, marks_plan_len, Pe, p, X, Y, area):
    """Upward load-balancing force per tendon from the sheet-16 profiles.  hi: drape from support-height chord;
    lo: inflection-point approach (heights at 0.1L from supports, effective span 0.8L).  Scaled by plan/profile length."""
    out = {"X": [0, 0], "Y": [0, 0]}
    detail = []
    for t, kind in [(t, "X") for t in X] + [(t, "Y") for t in Y]:
        pr = prof[t["mark"]]
        st = pr["stations"]; u = np.array([s["u"] for s in st]) / 100; h = np.array([s["h"] for s in st]) / 100
        edges = [0.0] + sorted(s / 100 for s in pr["supports"]) + [u[-1]]
        fhi = flo = 0.0
        for a, b in zip(edges[:-1], edges[1:]):
            L = b - a
            if L < 3.0:
                continue
            m = (u >= a) & (u <= b)
            hmin = h[m].min()
            ha, hb = np.interp(a, u, h), np.interp(b, u, h)
            a1 = (ha + hb) / 2 - hmin
            ha2, hb2 = np.interp(a + 0.1 * L, u, h), np.interp(b - 0.1 * L, u, h)
            a2 = (ha2 + hb2) / 2 - hmin
            P = t["n"] * Pe
            fhi += max(0.0, 8 * P * a1 / L)
            flo += max(0.0, 8 * P * a2 / (0.8 * L))
        scale = (t["L"] - 0.5) / u[-1]
        out[kind][0] += flo * min(scale, 1.0) if False else flo * scale
        out[kind][1] += fhi * scale
        detail.append((t["mark"], t["group"], t["n"], round(u[-1], 2), round(t["L"] - 0.5, 2), round(scale, 2)))
    q = {k: (v[0] / area, v[1] / area) for k, v in out.items()}      # kPa  (lo, hi)
    return q, out, detail


def strip_model(direction):
    if direction == "Y":      # y of supports (columns), cantilever tips
        return [3.7, 4.3, 6.3, 14.8, 24.3, 24.9], [1, 2, 3, 4]
    return [-0.6, 0.0, 10.0, 19.0, 28.0, 37.0, 47.0, 47.6], [1, 2, 3, 4, 5, 6]


def classify(util, missing=False):
    if util is None:
        return "NOT CHECKED"
    if util <= 1.0:
        return "OK (indicative)"
    return "NOT CHECKED (missing input)" if missing else "NOT OK (indicative)"


def voronoi_trib(cols, slab, step=0.25):
    minx, miny, maxx, maxy = slab.bounds
    from shapely.geometry import Point
    from shapely import contains_xy
    xs = np.arange(minx / 1000 + step / 2, maxx / 1000, step); ys = np.arange(miny / 1000 + step / 2, maxy / 1000, step)
    X, Yg = np.meshgrid(xs, ys)
    inside = contains_xy(slab, X * 1000, Yg * 1000)
    px, py = X[inside], Yg[inside]
    cx = np.array([c["x"] for c in cols]); cy = np.array([c["y"] for c in cols])
    d = (px[:, None] - cx[None, :]) ** 2 + (py[:, None] - cy[None, :]) ** 2
    nearest = d.argmin(axis=1)
    out = [float((nearest == i).sum() * step * step) for i in range(len(cols))]
    return out


def rho_required(vEd, k, scp, fck, gc=1.5):
    need = (vEd - 0.1 * scp) / (0.18 / gc * k)
    return max(need, 0.0) ** 3 / (100 * fck)


def run(p, geom, cov, prof, tag="base"):
    from shapely.geometry import Point
    plan, outline, voids, slab, cyan, green = geom
    X, Y = cov
    A = slab.area / 1e6
    ld = loads(p)
    Pj, Pe, Pt = pe_per_strand(p)
    sx, sy = precompression(X, Y, slab, Pe, p)
    q, F, det = balanced(prof, None, Pe, p, X, Y, A)
    res = dict(tag=tag, area=A, loads=ld, Pj=Pj, Pe=Pe, Pt=Pt, qbal=q, Fup={k: tuple(v) for k, v in F.items()}, checks=[])
    sig_x = [v[3] for v in sx if v[3] is not None]; sig_y = [v[3] for v in sy if v[3] is not None]
    nm_x = float(np.mean([v[1] / v[2] for v in sx if v[3] is not None])); nm_y = float(np.mean([v[1] / v[2] for v in sy if v[3] is not None]))
    res["precomp"] = dict(X=dict(min=min(sig_x), max=max(sig_x), mean=float(np.mean(sig_x)), n_per_m=nm_x),
                          Y=dict(min=min(sig_y), max=max(sig_y), mean=float(np.mean(sig_y)), n_per_m=nm_y),
                          n_total=dict(X=sum(t["n"] for t in X), Y=sum(t["n"] for t in Y)), sx=sx, sy=sy)
    fct = E.fctm(p["fck"]); Ec = E.ecm(p["fck"])
    cks = res["checks"]
    # ---- load balancing (per direction; each direction carries the full load - equivalent-frame practice)
    for dr in ("X", "Y"):
        lo, hi = q[dr]
        cks.append(dict(id=f"LB-{dr}", name=f"Load balancing {dr}-direction (balanced load / self-weight)", demand=lo, cap=ld["sw"], util=None,
                        pct_sw=(lo / ld["sw"], hi / ld["sw"]), pct_G=(lo / ld["G"], hi / ld["G"]), pct_qp=(lo / ld["qp"], hi / ld["qp"]),
                        unit="kPa", status="INFO"))
    def sig_at(dr_, coord):
        arr = [(v[0], v[3]) for v in (sx if dr_ == "X" else sy) if v[3] is not None]
        xs_ = [a for a, _ in arr]; ys_ = [b for _, b in arr]
        return float(np.interp(coord, xs_, ys_))
    thick_w = {("Y", 6.3): 4.25, ("Y", 14.8): 3.0, ("X", 10.0): 3.1, ("X", 19.0): 3.1, ("X", 28.0): 3.1, ("X", 37.0): 3.1}
    fpd = p["fp01k"] / p["gs"]
    for dr in ("Y", "X"):
        nodes, sup = strip_model(dr)
        qb = q[dr][0]
        nspan = len(nodes) - 1
        sp = [nodes[i + 1] - nodes[i] for i in range(nspan)]
        Bp = 9.0; Lmin = 8.5 if dr == "Y" else 9.0
        bcs = 0.5 * min(Bp, Lmin)
        sig = res["precomp"][dr]["mean"]
        nm = res["precomp"][dr]["n_per_m"]
        ap = nm * p["Ap"]
        cases = {"QP": ld["qp"] - qb, "FREQ": ld["freq"] - qb, "TRANSFER": ld["sw"] - qb * Pt / Pe}
        res[f"strip_{dr}"] = dict(nodes=nodes, spans=sp, qbal_used=qb, net=cases, bcs=bcs, Bp=Bp)
        for k, wnet in cases.items():
            s = E.continuous_strip(nodes, sup, [wnet] * nspan, ei=1.0)
            fT = (Pt / Pe if k == "TRANSFER" else 1.0)
            lim = fct if k != "TRANSFER" else E.fctm(p["fci"])
            for ie in range(nspan):
                if sp[ie] < 3.0:
                    continue
                msag = s["M_span_extremes"][ie][0]
                sg = sig_at(dr, 0.5 * (nodes[ie] + nodes[ie + 1])) * fT
                for lab, m_ in (("A avg-strip", msag), ("B col-strip", p["share_sag"] * msag * Bp / bcs)):
                    st = E.section_stress(sg, m_, p["t_slab"])
                    tens = max(0.0, -min(st["top"], st["bot"]))
                    cks.append(dict(id=f"SV-{dr}-{k}-mid{ie+1}-{lab[0]}", group="service", dir=dr, comb=k, loc=f"midspan {ie+1} ({sp[ie]:.1f} m)", case=lab, t=p["t_slab"],
                                    name=f"{k} tension, {dr}-dir midspan {ie+1} ({sp[ie]:.1f} m), {lab}, t=0.25", demand=tens, cap=lim, util=tens / lim, unit="MPa",
                                    m=m_, sig_p=sg, top=st["top"], bot=st["bot"], util_k05=tens / (0.7 * lim), status=classify(tens / lim)))
            for node_i in sup[1:-1]:
                m_n = s["M_end"][node_i - 1][1]
                key = (dr, round(nodes[node_i], 1))
                sg = sig_at(dr, nodes[node_i]) * fT
                for lab, mm, tt in (("A avg-strip t=0.25", m_n, p["t_slab"]), ("A avg-strip t=0.45", m_n, p["t_thick"]),
                                    ("B col-strip, thick zone", p["share_hog"] * m_n * Bp / min(bcs, thick_w.get(key, bcs)), p["t_thick"]),
                                    ("B col-strip, t=0.25", p["share_hog"] * m_n * Bp / bcs, p["t_slab"])):
                    st = E.section_stress(sg * p["t_slab"] / tt, mm, tt)      # same force over thicker section: P/A scales with 1/t
                    tens = max(0.0, -min(st["top"], st["bot"]))
                    cks.append(dict(id=f"SV-{dr}-{k}-sup{node_i}-{lab.replace(' ','')}", group="service", dir=dr, comb=k, loc=f"support {nodes[node_i]:.1f} m", case=lab, t=tt,
                                    name=f"{k} tension at support {nodes[node_i]:.1f} m, {dr}-dir, {lab}", demand=tens, cap=lim, util=tens / lim, unit="MPa",
                                    m=mm, sig_p=sg * p["t_slab"] / tt, top=st["top"], bot=st["bot"], util_k05=tens / (0.7 * lim), status=classify(tens / lim)))
        # deflection
        s = E.continuous_strip(nodes, sup, [cases["QP"]] * nspan, ei=1.0)
        I = p["t_slab"] ** 3 / 12; Ee = Ec / (1 + p["phi"]) * 1000.0
        for ie in range(nspan):
            if sp[ie] < 3.0:
                continue
            dm = s["defl_mid"][ie] / (Ee * I) * 1000
            cks.append(dict(id=f"DEF-{dr}-span{ie+1}", group="deflection", name=f"Deflection {dr}-dir span {ie+1} ({sp[ie]:.1f} m), QP net, strip-average uncracked, Ec,eff",
                            demand=abs(dm), sign="down" if dm > 0 else "up", cap=sp[ie] * 1000 / 250, util=abs(dm) / (sp[ie] * 1000 / 250), unit="mm", status=classify(abs(dm) / (sp[ie] * 1000 / 250))))
        # ULS - PT only, hyperstatic omitted; required supplementary As
        ext = E.continuous_strip(nodes, sup, [ld["uls"]] * nspan, ei=1.0)
        fyd = 400.0 / 1.15
        def uls(lab, med_avg, d, loc, share):
            mr = E.mrd_bonded_pt(ap, d, p["fck"], fpd, p["gc"])
            for cs_lab, med in (("A avg-strip", abs(med_avg)), ("B col-strip", share * abs(med_avg) * Bp / bcs)):
                u = med / mr["MRd"]
                as_req = max(0.0, (med - mr["MRd"]) * 1e6 / (fyd * 0.9 * d * 1000.0))
                cks.append(dict(id=f"ULS-{dr}-{lab}-{cs_lab[0]}", group="uls", dir=dr, loc=loc, case=cs_lab,
                                name=f"ULS {lab}, {dr}-dir {loc}, {cs_lab}, PT only", demand=med, cap=mr["MRd"], util=u, unit="kNm/m", Ap=ap, xd=mr["x_over_d"], d=d,
                                As_req=as_req, status=classify(u, missing=True)))
        for node_i in sup[1:-1]:
            m_n = ext["M_end"][node_i - 1][1]
            uls(f"hog@{nodes[node_i]:.1f}", m_n, p["d_thick"], f"support {nodes[node_i]:.1f} m", p["share_hog"])
        for ie in range(nspan):
            if sp[ie] < 3.0:
                continue
            uls(f"sag{ie+1}", ext["M_span_extremes"][ie][0], 0.20, f"span {ie+1} ({sp[ie]:.1f} m)", p["share_sag"])
    # ---- punching with Voronoi tributary areas
    cols = []
    for tag_, size, pts in R.COLUMNS:
        for (x, y) in pts:
            cols.append(dict(tag=tag_, c=size / 1000, x=x / 1000, y=y / 1000))
    tr = voronoi_trib(cols, slab)
    res["punch_trib_total"] = sum(tr); res["slab_area"] = A
    sig_cp = 0.5 * (res["precomp"]["X"]["mean"] + res["precomp"]["Y"]["mean"])
    rho = 0.5 * (nm_x + nm_y) * p["Ap"] / (1e6 * 0.2)
    for c, t_ in zip(cols, tr):
        c["trib"] = t_
        edge_x = c["x"] in (0, 47); edge_y = c["y"] in (4.3, 24.3)
        c["kind"] = "corner" if edge_x and edge_y else ("edge" if edge_x or edge_y else "interior")
        pt = Point(c["x"] * 1000, c["y"] * 1000)
        inth = [cp for cp in cyan if cp.buffer(50).contains(pt)]
        c["thick"] = bool(inth); tp = inth[0] if inth else None
        d = p["d_thick"] if c["thick"] else p["d_slab"]
        V = ld["uls"] * t_
        r = E.punching(V, c["c"], d, c["kind"], p["fck"], sig_cp, rho, gc=p["gc"])
        rq = rho_required(r["vEd_u1"], r["k"], sig_cp, p["fck"], p["gc"])
        cks.append(dict(id=f"PU-{c['tag']}@({c['x']:.0f},{c['y']:.1f})", group="punching", name=f"Punching u1, {c['tag']} {c['c']*1000:.0f} mm at ({c['x']:.0f}, {c['y']:.1f}), {c['kind']}, {'thick zone' if c['thick'] else 'slab'}, d={d}",
                        demand=r["vEd_u1"], cap=r["vRdc"], util=r["util_u1"], unit="MPa", V=V, trib=t_, kind=c["kind"], d=d, rho_req=rq, status=classify(r["util_u1"], missing=True), rd=r))
        cks.append(dict(id=f"PUmax-{c['tag']}@({c['x']:.0f},{c['y']:.1f})", group="punching", name=f"Punching u0 (vRd,max), {c['tag']} at ({c['x']:.0f}, {c['y']:.1f})",
                        demand=r["vEd_u0"], cap=r["vRdmax"], util=r["util_u0"], unit="MPa", status=classify(r["util_u0"])))
        if c["thick"] and tp is not None and tp.area > 3e6 and c["kind"] == "interior":
            bx = tp.bounds; wdp, hdp = (bx[2] - bx[0]) / 1000, (bx[3] - bx[1]) / 1000
            uo = 2 * (wdp + hdp) + 2 * math.pi * 2 * p["d_slab"]
            r2 = E.punching_perimeter(V, 1.15, uo, uo, p["d_slab"], p["fck"], sig_cp, rho, p["gc"])
            cks.append(dict(id=f"PUout-{c['tag']}@({c['x']:.0f},{c['y']:.1f})", group="punching", name=f"Punching outside drop panel ({wdp:.1f} x {hdp:.1f} m), u={uo:.1f} m, d={p['d_slab']}",
                            demand=r2["vEd_u1"], cap=r2["vRdc"], util=r2["util_u1"], unit="MPa", V=V, rho_req=rho_required(r2["vEd_u1"], r2["k"], sig_cp, p["fck"], p["gc"]), status=classify(r2["util_u1"], missing=True)))
    res["columns"] = [{k: v for k, v in c.items()} for c in cols]
    res["Ec"] = Ec; res["fctm"] = fct; res["sig_cp"] = sig_cp; res["rho_punch"] = rho
    res["balance_detail"] = det
    return res


def restraint(p, sigx_mean, Ec):
    out = []
    fct = E.fctm(p["fck"])
    for eps in (0.0002, 0.0003, 0.0004, 0.0005):
        for R_ in (0.3, 0.5, 0.8):
            s = R_ * eps * Ec / (1 + p["phi"])
            out.append(dict(eps=eps, R=R_, sigma_t=s, net=s - sigx_mean, util_vs_fct=(s - sigx_mean) / fct))
    return out


def main():
    geom = build_geometry()
    cov = tendon_coverage(geom[5])
    prof = json.load(open(CAD / "profiles_2F_PT.json"))
    plan, outline, voids, slab, cyan, green = geom
    X, Y = cov
    # consistency: profile vs plan length
    cons = []
    for t in X + Y:
        pl = t["L"] - 0.5
        pr = prof[t["mark"]]["stations"][-1]["u"] / 100
        cons.append((t["mark"], t["group"], round(pl, 2), round(pr, 2), abs(pl - pr) <= 0.3))
    marks = {}
    for m, g, a, b, ok in cons:
        marks.setdefault(m, (a, b, ok))
    n_mis = sum(1 for v in marks.values() if not v[2])
    variants = {
        "base": {},
        "skill-default loads (SDL 4.65 / LL 2.5)": dict(sdl_ksm=4.65 / E.KSM_TO_KPA, ll_ksm=2.5 / E.KSM_TO_KPA),
        "losses 25%": dict(loss=0.25),
        "losses 12%": dict(loss=0.12),
        "d (punching) +10 mm": dict(d_slab=0.21, d_thick=0.41),
    }
    allres = {}
    for tag, mod in variants.items():
        p = copy.deepcopy(BASE); p.update(mod)
        allres[tag] = run(p, geom, cov, prof, tag)
    base = allres["base"]
    pbase = BASE
    rs = restraint(pbase, base["precomp"]["X"]["mean"], base["Ec"])
    out = dict(params=BASE, variants=allres, restraint=rs, consistency=dict(by_mark=marks, n_mismatch=n_mis, n_marks=len(marks)),
               area_slab_net=slab.area / 1e6, area_outline=outline.area / 1e6, n_voids=len(voids),
               strands=dict(X=sum(t["n"] for t in X), Y=sum(t["n"] for t in Y)),
               tendons=dict(X=X, Y=Y))
    def clean(o):
        if isinstance(o, dict): return {str(k): clean(v) for k, v in o.items()}
        if isinstance(o, (list, tuple)): return [clean(v) for v in o]
        if isinstance(o, (np.floating, np.integer)): return float(o)
        if isinstance(o, (bool, np.bool_)): return bool(o)
        return o
    json.dump(clean(out), open(sys.argv[2] if len(sys.argv) > 2 else "results.json", "w"), indent=1)
    return out


if __name__ == "__main__":
    main()
