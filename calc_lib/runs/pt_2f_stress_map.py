"""2F PT slab - stress utilisation maps on the layout plan (transfer / construction / service).  INDICATIVE.
Usage: python pt_2f_stress_map.py <cadgen_dir> <out_dir>
Strip logic: EN 1992-1-1 Annex I (informative) column / middle strips, panel-average moment x share; local section 0.45 m inside DP/BB
polygons, 0.25 m elsewhere; same force over thicker section (P/A scales with 1/t); precompression local along the strip direction.
"""
import sys, json, copy, pathlib, csv
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
from matplotlib.patches import Polygon as MPoly, Rectangle
from shapely import contains_xy

HERE = pathlib.Path(__file__).resolve().parent
sys.argv = [sys.argv[0]] + sys.argv[1:]
CAD = pathlib.Path(sys.argv[1]); OUT = pathlib.Path(sys.argv[2]); OUT.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(HERE))
import pt_2f_screening as S          # reuses geometry, tendon coverage, loads, balanced load
E = S.E

P = copy.deepcopy(S.BASE)
QC = 1.0        # construction load kPa  ASSUMED (EN 1991-1-6 Qca recommended 1.0) - CONFIRM
geom = S.build_geometry(); plan, outline, voids, slab, cyan, green = geom
X, Y = S.tendon_coverage(green)
prof = json.load(open(CAD / "profiles_2F_PT.json"))
ld = S.loads(P); Pj, Pe, Pt = S.pe_per_strand(P)
sx, sy = S.precompression(X, Y, slab, Pe, P)
A = slab.area / 1e6
q, F, det = S.balanced(prof, None, Pe, P, X, Y, A)
fct_t = E.fctm(P["fci"]); fct_s = E.fctm(P["fck"])

STAGES = [
    ("TRANSFER", "Transfer: self-weight, force at transfer (Pt)", ld["sw"], Pt / Pe, fct_t, 0.6 * P["fci"]),
    ("CONSTRUCTION", f"Construction: self-weight + {QC:.1f} kPa, Pe (lower bound), young concrete limit fctm(fci)", ld["sw"] + QC, 1.0, fct_t, 0.6 * P["fci"]),
    ("SERVICE", "Service: frequent combination, Pe", ld["freq"], 1.0, fct_s, 0.6 * P["fck"]),
]
DIRS = {
    "X": dict(nodes=[-0.6, 0.0, 10.0, 19.0, 28.0, 37.0, 47.0, 47.6], sup=[1, 2, 3, 4, 5, 6], lines=[5.3, 14.8, 24.3], bcs=4.5, Bp=9.0, sec=sx),
    "Y": dict(nodes=[3.7, 4.3, 6.3, 14.8, 24.3, 24.9], sup=[1, 2, 3, 4], lines=[0, 10, 19, 28, 37, 47], bcs=4.25, Bp=9.0, sec=sy),
}
LINE_NAME_Y = {5.3: "B-C band (y 4.3-6.3)", 14.8: "D (y 14.8)", 24.3: "F (y 24.3)"}


def moment_fn(nodes, sup, w):
    sol = E.continuous_strip(nodes, sup, [w] * (len(nodes) - 1), ei=1.0)
    nodes = np.array(nodes)
    def M(c):
        c = np.asarray(c, float); out = np.zeros_like(c)
        for e in range(len(nodes) - 1):
            m = (c >= nodes[e]) & (c <= nodes[e + 1])
            xx = c[m] - nodes[e]
            m0 = sol["M_end"][e][0]; v1 = sol["V_end"][e][0]
            out[m] = m0 + v1 * xx - w * xx ** 2 / 2
        return out
    return M


def sig_fn(sec):
    arr = [(v[0], v[3]) for v in sec if v[3] is not None]
    xs = [a for a, _ in arr]; ys = [b for _, b in arr]
    return lambda c: np.interp(c, xs, ys)


STEP = 0.25
xs = np.arange(-0.6 + STEP / 2, 47.6, STEP); ys = np.arange(3.7 + STEP / 2, 24.9, STEP)
GX, GY = np.meshgrid(xs, ys)
inside = contains_xy(slab, GX * 1000, GY * 1000)
thick = np.zeros_like(inside)
for cp in cyan:
    thick |= contains_xy(cp, GX * 1000, GY * 1000)
T = np.where(thick, P["t_thick"], P["t_slab"])


def zone_ids(dr, coord):
    """Support zone (S) = within 0.15 x adjacent span of an interior/edge column line; else mid-span (M)."""
    nodes = np.array(DIRS[dr]["nodes"]); sup = DIRS[dr]["sup"]
    z = np.empty(coord.shape, dtype=object)
    for e in range(len(nodes) - 1):
        m = (coord >= nodes[e]) & (coord < nodes[e + 1] + (1e-9 if e == len(nodes) - 2 else 0))
        z[m] = f"M{e+1}"
    for i in sup:
        L = max(nodes[i] - nodes[i - 1], nodes[min(i + 1, len(nodes) - 1)] - nodes[i])
        m = np.abs(coord - nodes[i]) <= 0.15 * L
        z[m] = f"S{i}"
    return z


def eval_stage(stage):
    name, lab, w0, fP, lim_t, lim_c = stage
    res = {}
    for dr, D in DIRS.items():
        qb = q[dr][0] * fP
        M = moment_fn(D["nodes"], D["sup"], w0 - qb)
        sg = sig_fn(D["sec"])
        coord = GX if dr == "X" else GY
        perp = GY if dr == "X" else GX
        m_tot = M(coord)
        sig0 = sg(np.clip(coord, 0.25, 46.75 if dr == "X" else 24.8)) * fP
        d_line = np.min(np.abs(perp[..., None] - np.array(D["lines"])[None, None, :]), axis=2)
        col = d_line <= D["bcs"] / 2
        hog = m_tot < 0
        share = np.where(hog, P["share_hog"], P["share_sag"])
        m_loc = np.where(col, share * m_tot * D["Bp"] / D["bcs"], (1 - share) * m_tot * D["Bp"] / (D["Bp"] - D["bcs"]))
        sig = sig0 * P["t_slab"] / T
        s_ = m_loc / (T ** 2 / 6) / 1000.0
        top = sig + s_; bot = sig - s_
        tens = np.maximum(0.0, -np.minimum(top, bot)); comp = np.maximum(top, bot)
        util = np.maximum(tens / lim_t, comp / lim_c)
        util = np.where(inside, util, np.nan)
        res[dr] = dict(util=util, tens=np.where(inside, tens, np.nan), col=col, zone=zone_ids(dr, coord), m=m_loc, sig=sig, hog=hog)
    return res


results = {st[0]: eval_stage(st) for st in STAGES}

# ---------------------------------------------------------------- plotting
COLS = ["#b7dfb0", "#e6e08a", "#f4a460", "#d73027", "#7f0000"]
BINS = [0, 0.8, 1.0, 1.25, 2.0, 99]
cmap = ListedColormap(COLS); norm = BoundaryNorm(BINS, cmap.N)
NAMES = ["<= 0.80 OK", "0.80 - 1.00 near limit", "1.00 - 1.25 NOT OK", "1.25 - 2.00 NOT OK", "> 2.00 NOT OK"]
GRIDX = [0, 10, 19, 28, 37, 47]; GRIDY = {"B": 4.3, "C": 6.3, "D": 14.8, "E": 19.8, "F": 24.3}


def base_plan(ax, title):
    ax.set_aspect("equal"); ax.set_xlim(-2.5, 49.5); ax.set_ylim(2.5, 26.0)
    pts = np.array([(a / 1000, b / 1000) for a, b in outline.exterior.coords])
    ax.add_patch(MPoly(pts, closed=True, fill=False, ec="k", lw=0.8))
    for v in voids:
        pv = np.array([(a / 1000, b / 1000) for a, b in v.exterior.coords])
        ax.add_patch(MPoly(pv, closed=True, fc="white", ec="k", lw=0.5, hatch="///"))
    for cp in cyan:
        pc = np.array([(a / 1000, b / 1000) for a, b in cp.exterior.coords])
        ax.add_patch(MPoly(pc, closed=True, fill=False, ec="#1f4e79", lw=0.5, ls="--"))
    for tag, size, pts_ in S.R.COLUMNS:
        for (cx, cy) in pts_:
            s = size / 1000
            ax.add_patch(Rectangle((cx / 1000 - s / 2, cy / 1000 - s / 2), s, s, fc="k", ec="k", lw=0.3, zorder=5))
    for gx in GRIDX:
        ax.axvline(gx, color="0.55", lw=0.3, ls="-.", zorder=1)
    for k, gy in GRIDY.items():
        ax.axhline(gy, color="0.55", lw=0.3, ls="-.", zorder=1)
        ax.text(-2.3, gy, k, fontsize=5, va="center", color="0.3")
    ax.set_title(title, fontsize=7.5, loc="left", pad=2)
    ax.tick_params(labelsize=5); ax.set_xticks(GRIDX)


def draw(ax, util, title, label=True, dr=None, res=None):
    base_plan(ax, title)
    ax.imshow(util, extent=(xs[0] - STEP / 2, xs[-1] + STEP / 2, ys[0] - STEP / 2, ys[-1] + STEP / 2), origin="lower", cmap=cmap, norm=norm, alpha=0.85, zorder=2, interpolation="nearest")
    if label and res is not None:
        zs = res["zone"]; col = res["col"]
        for zid in np.unique(zs[inside]):
            for ct in (True, False):
                m = inside & (zs == zid) & (col == ct)
                if m.sum() < 8: continue
                u = np.nanmax(util[m])
                if u >= 1.0:
                    # label the cell of max util
                    idx = np.nanargmax(np.where(m, util, -1)); yy, xx = np.unravel_index(idx, util.shape)
                    ax.text(xs[xx], ys[yy], f"{u:.2f}", fontsize=4.8, ha="center", va="center", zorder=6, color="k", bbox=dict(fc="white", ec="none", pad=0.4, alpha=0.7))


def legend(fig, y=0.015):
    from matplotlib.patches import Patch
    fig.legend(handles=[Patch(fc=c, label=n) for c, n in zip(COLS, NAMES)] + [Patch(fc="white", ec="k", hatch="///", label="void"), Patch(fc="none", ec="#1f4e79", ls="--", label="DP / band beam 0.45 m")],
               loc="lower center", ncol=7, fontsize=6.5, frameon=False, bbox_to_anchor=(0.5, y))


NOTE = ("INDICATIVE SCREENING - NOT A SIGN-OFF. Utilisation = max(tension / fctm, compression / 0.6 f_c). EN 1992-1-1 Annex I column / middle strips (hog 80 %, sag 70 % in column strip); "
        "continuous 1 m strips on pinned supports; local precompression; section 0.45 m inside DP/BB else 0.25 m. PT basis ASSUMED (Gr.270, 0.75 fpu, 18 % losses); mild steel not credited. "
        "Numbers = max utilisation of a zone where > 1.00.")

with plt.rc_context({"font.family": "DejaVu Sans"}):
    # page 1: 3 stages x 2 directions
    fig, axes = plt.subplots(3, 2, figsize=(16.54, 11.69))
    for r, st in enumerate(STAGES):
        for c, dr in enumerate(("X", "Y")):
            res = results[st[0]][dr]
            draw(axes[r, c], res["util"], f"{st[0]} - {dr}-direction moments   [{st[1]}]", True, dr, res)
    fig.suptitle("2F PT SLAB - STRESS UTILISATION BY STAGE AND DIRECTION (REDRAFT FOR REVIEW)", fontsize=11, x=0.02, ha="left", y=0.995)
    fig.text(0.02, 0.045, NOTE, fontsize=5.8, ha="left", va="top", wrap=True)
    legend(fig, 0.065)
    fig.subplots_adjust(left=0.02, right=0.99, top=0.95, bottom=0.11, hspace=0.12, wspace=0.05)
    fig.savefig(OUT / "page1_stages.png", dpi=170); fig.savefig(OUT / "page1_stages.pdf")
    plt.close(fig)

    # page 2: governing (all stages, both directions) + service-only X/Y maxima
    gov = np.fmax.reduce([results[s][d]["util"] for s in results for d in ("X", "Y")])
    which = np.zeros(gov.shape, dtype=object)
    fig, axes = plt.subplots(2, 1, figsize=(16.54, 11.69))
    draw(axes[0], gov, "GOVERNING utilisation - worst of transfer, construction, service and both directions", False)
    # label failing zones with stage/dir
    labs = []
    for s in results:
        for d in ("X", "Y"):
            res = results[s][d]
            for zid in np.unique(res["zone"][inside]):
                for ct in (True, False):
                    m = inside & (res["zone"] == zid) & (res["col"] == ct)
                    if m.sum() < 8: continue
                    u = np.nanmax(res["util"][m])
                    if u > 1.0:
                        idx = np.nanargmax(np.where(m, res["util"], -1)); yy, xx = np.unravel_index(idx, res["util"].shape)
                        labs.append((s, d, zid, ct, u, xs[xx], ys[yy]))
    # keep worst label per 3 m cell to avoid clutter
    seen = {}
    for lb in sorted(labs, key=lambda z: -z[4]):
        key = (round(lb[5] / 3), round(lb[6] / 3))
        if key in seen: continue
        seen[key] = lb
        axes[0].text(lb[5], lb[6], f"{lb[4]:.2f}\n{lb[0][:4]} {lb[1]}", fontsize=4.6, ha="center", va="center", zorder=6, bbox=dict(fc="white", ec="none", pad=0.4, alpha=0.75))
    # service only governing
    gs = np.fmax(results["SERVICE"]["X"]["util"], results["SERVICE"]["Y"]["util"])
    draw(axes[1], gs, "SERVICE (frequent) - worst of X and Y directions", False)
    fig.suptitle("2F PT SLAB - WHERE THE STRIPS DO NOT PASS (REDRAFT FOR REVIEW)", fontsize=11, x=0.02, ha="left", y=0.995)
    fig.text(0.02, 0.05, NOTE, fontsize=5.8, ha="left", va="top", wrap=True)
    legend(fig, 0.07)
    fig.subplots_adjust(left=0.02, right=0.99, top=0.95, bottom=0.12, hspace=0.12)
    fig.savefig(OUT / "page2_governing.png", dpi=170); fig.savefig(OUT / "page2_governing.pdf")
    plt.close(fig)

# ---------------------------------------------------------------- table of zones
rows = []
for dr, D in DIRS.items():
    for zid in sorted({z for s in results for z in np.unique(results[s][dr]["zone"][inside])}, key=lambda z: (z[0] != "S", int(z[1:]))):
        for ct in (True, False):
            r = dict(direction=dr, zone=zid, strip="column strip" if ct else "middle strip")
            any_cell = False
            for s in results:
                res = results[s][dr]; m = inside & (res["zone"] == zid) & (res["col"] == ct)
                if m.sum() < 8:
                    r[s] = None; continue
                any_cell = True
                r[s] = float(np.nanmax(res["util"][m]))
                if s == "SERVICE":
                    k = np.nanargmax(np.where(m, res["util"], -1)); yy, xx = np.unravel_index(k, res["util"].shape)
                    r["where_service"] = f"x={xs[xx]:.1f}, y={ys[yy]:.1f}"
            if any_cell:
                nodes = D["nodes"]
                if zid[0] == "S":
                    r["location"] = f"support at {'x' if dr=='X' else 'y'} = {nodes[int(zid[1:])]:.1f} m"
                else:
                    e = int(zid[1:]) - 1
                    r["location"] = f"midspan {'x' if dr=='X' else 'y'} {nodes[e]:.1f} to {nodes[e+1]:.1f} m"
                rows.append(r)
with open(OUT / "strip_zone_utilisation.csv", "w", newline="") as fh:
    w = csv.writer(fh); w.writerow(["direction", "zone", "location", "strip", "TRANSFER", "CONSTRUCTION", "SERVICE", "worst_cell_service"])
    for r in rows:
        w.writerow([r["direction"], r["zone"], r["location"], r["strip"]] + [("" if r[s] is None else f"{r[s]:.2f}") for s in ("TRANSFER", "CONSTRUCTION", "SERVICE")] + [r.get("where_service", "")])
json.dump(rows, open(OUT / "strip_zone_utilisation.json", "w"), indent=1)
print(len(rows), "zones")
for s in results:
    for d in ("X", "Y"):
        u = results[s][d]["util"]; print(s, d, "max util", round(float(np.nanmax(u)), 2), "share of slab area > 1.0:", round(float(np.nansum(u > 1.0) / np.sum(inside)), 3))
