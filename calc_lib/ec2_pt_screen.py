"""EN 1992-1-1 (CEN recommended values) SCREENING functions for a bonded PT flat slab.

INDICATIVE ONLY - not a sign-off.  Units: m, kN, kPa (kN/m2), MPa, mm2 as stated per function.
Every function is deterministic; no design-basis value is invented here - the caller passes inputs
and is responsible for marking each one CONFIRMED / ASSUMED.
"""
from __future__ import annotations
import math
import numpy as np

KSM_TO_KPA = 9.80665e-3          # 1 kg/m2 -> kN/m2


# ------------------------------------------------------------------ materials (EN 1992-1-1 Table 3.1)
def fctm(fck: float) -> float:
    """Mean tensile strength, MPa (EC2 Table 3.1, fck <= 50)."""
    return 0.30 * fck ** (2.0 / 3.0)


def ecm(fck: float) -> float:
    """Secant modulus, MPa: 22 (fcm/10)^0.3 GPa, fcm = fck + 8 (EC2 Table 3.1)."""
    return 22.0e3 * ((fck + 8.0) / 10.0) ** 0.3


# ------------------------------------------------------------------ continuous strip (pinned supports)
def continuous_strip(nodes_x, support_idx, w_el, ei=1.0):
    """Beam on pinned supports.  nodes_x: ascending node coordinates (m); support_idx: node indices that are
    supports (v=0); w_el: uniform downward load per element (kN/m).  Free tips allowed (cantilevers).
    Returns dict with node moments M_node (kNm, hogging negative, from element end moments), midpoint
    sagging moment per element and midpoint deflection per element (m, for the given ei kNm2)."""
    n = len(nodes_x)
    K = np.zeros((2 * n, 2 * n)); F = np.zeros(2 * n)
    L = np.diff(nodes_x)
    for e in range(n - 1):
        l, w = L[e], w_el[e]
        k = ei / l ** 3 * np.array([[12, 6 * l, -12, 6 * l], [6 * l, 4 * l * l, -6 * l, 2 * l * l],
                                    [-12, -6 * l, 12, -6 * l], [6 * l, 2 * l * l, -6 * l, 4 * l * l]])
        f = w * np.array([l / 2, l * l / 12, l / 2, -l * l / 12])      # downward positive
        idx = [2 * e, 2 * e + 1, 2 * e + 2, 2 * e + 3]
        for a in range(4):
            F[idx[a]] += f[a]
            for b in range(4):
                K[idx[a], idx[b]] += k[a, b]
    fixed = [2 * i for i in support_idx]
    free = [i for i in range(2 * n) if i not in fixed]
    d = np.zeros(2 * n)
    d[free] = np.linalg.solve(K[np.ix_(free, free)], F[free])
    Mend, Mmid, dmid, Vend = [], [], [], []
    for e in range(n - 1):
        l, w = L[e], w_el[e]
        idx = [2 * e, 2 * e + 1, 2 * e + 2, 2 * e + 3]
        k = ei / l ** 3 * np.array([[12, 6 * l, -12, 6 * l], [6 * l, 4 * l * l, -6 * l, 2 * l * l],
                                    [-12, -6 * l, 12, -6 * l], [6 * l, 2 * l * l, -6 * l, 4 * l * l]])
        f = w * np.array([l / 2, l * l / 12, l / 2, -l * l / 12])
        r = k @ d[idx] - f                       # end actions on element (V1,M1,V2,M2), upward/ccw positive
        V1, M1, V2, M2 = r
        V1 = -V1                                  # reaction of nodes on element (upward +)
        xs = np.linspace(0, l, 201)
        Mx = V1 * xs - w * xs ** 2 / 2 + M1       # sagging +, hogging -
        Mmid.append((float(Mx.max()), float(Mx.min())))
        Mend.append((float(Mx[0]), float(Mx[-1])))
        Vend.append((float(V1), float(V1 - w * l)))
        # deflection at mid (Hermite) downward positive
        u = d[idx]
        s = 0.5
        N = np.array([1 - 3 * s * s + 2 * s ** 3, l * (s - 2 * s * s + s ** 3), 3 * s * s - 2 * s ** 3, l * (-s * s + s ** 3)])
        dmid.append(float(N @ u))
    return {"M_end": Mend, "M_span_extremes": Mmid, "defl_mid": dmid, "V_end": Vend, "d": d}


# ------------------------------------------------------------------ section stresses (per metre width)
def section_stress(sig_p: float, m_knm_per_m: float, t: float):
    """Top/bottom fibre stresses (MPa, compression +) for 1 m wide section thickness t (m); sagging m>0 puts bottom in tension."""
    z = t * t / 6.0 * 1000.0          # section modulus per m, in 1e3 mm3... -> kNm / (m3) -> kPa
    s = m_knm_per_m / (t * t / 6.0) / 1000.0   # MPa
    return {"top": sig_p + s, "bot": sig_p - s}


# ------------------------------------------------------------------ ULS flexure, bonded tendons, PT only
def mrd_bonded_pt(ap_mm2_per_m: float, d_m: float, fck: float, fpd: float, gc=1.5, alpha_cc=1.0):
    """Rectangular stress block (lambda 0.8, eta 1.0, fck<=50). PT only (no mild steel). kNm/m. Tendon stress taken as fpd (caller's value)."""
    fcd = alpha_cc * fck / gc
    T = ap_mm2_per_m * fpd / 1000.0            # kN/m
    x = T / (0.8 * fcd * 1000.0)               # m   (fcd MPa = 1000 kPa)
    mrd = T * (d_m - 0.4 * x)
    return {"MRd": mrd, "x": x, "x_over_d": x / d_m, "T": T, "fcd": fcd}


# ------------------------------------------------------------------ punching (EN 1992-1-1 6.4)
def punching(V_col_kn, c_m, d_m, kind, fck, sigma_cp, rho_l, beta=None, gc=1.5):
    """Square column c x c.  kind: 'interior' | 'edge' | 'corner' (column flush with edge, simplified perimeters).
    Returns VEd stress at u0 and u1, vRd,c (with rho_l) and vRd,c(min), vRd,max."""
    bmap = {"interior": 1.15, "edge": 1.4, "corner": 1.5}      # EC2 6.4.3(6) recommended
    beta = bmap[kind] if beta is None else beta
    u0 = {"interior": 4 * c_m, "edge": 3 * c_m, "corner": 2 * c_m}[kind]
    r = 2 * d_m
    u1 = {"interior": 4 * c_m + 2 * math.pi * r, "edge": 3 * c_m + math.pi * r, "corner": 2 * c_m + 0.5 * math.pi * r}[kind]
    return _punch_core(V_col_kn, beta, u0, u1, d_m, fck, sigma_cp, rho_l, gc)


def punching_perimeter(V_col_kn, beta, u0, u1, d_m, fck, sigma_cp, rho_l, gc=1.5):
    return _punch_core(V_col_kn, beta, u0, u1, d_m, fck, sigma_cp, rho_l, gc)


def _punch_core(V, beta, u0, u1, d, fck, scp, rho, gc):
    k = min(1 + math.sqrt(0.2 / d), 2.0)               # d in m: sqrt(200/d_mm)
    rho = min(rho, 0.02)
    crd = 0.18 / gc
    k1 = 0.1
    scp = max(0.0, min(scp, 0.2 * fck / gc))
    v_c = crd * k * (100 * rho * fck) ** (1 / 3) + k1 * scp
    vmin = 0.035 * k ** 1.5 * math.sqrt(fck) + k1 * scp
    nu = 0.6 * (1 - fck / 250.0)
    vmax = 0.4 * nu * fck / gc
    ved1 = beta * V / (u1 * d) / 1000.0                 # MPa
    ved0 = beta * V / (u0 * d) / 1000.0
    return {"beta": beta, "u0": u0, "u1": u1, "d": d, "k": k, "vEd_u1": ved1, "vEd_u0": ved0,
            "vRdc_rho": v_c, "vRdc_min": vmin, "vRdc": max(v_c, vmin), "vRdmax": vmax,
            "util_u1": ved1 / max(v_c, vmin), "util_u0": ved0 / vmax}
