"""EN 1992-1-1 bond and anchorage - reusable calculation logic (no report formatting).

Units: stresses in MPa, lengths in mm. CEN recommended values (no National Annex).
Clause refs: EN 1992-1-1 3.1.6, 8.4.2 (ultimate bond stress), 8.4.3 (basic required anchorage length).

Scope limits: straight bars, alpha factors of 8.4.4 taken as 1.0 (basic length only), eta2 = 1.0 for phi <= 32 mm.
Not covered: lb,min, transverse reinforcement/cover effects (alpha1-alpha5), lap factor alpha6.
"""
from __future__ import annotations

from dataclasses import dataclass

GAMMA_C = 1.5      # EN 1992-1-1 Table 2.1N (persistent/transient)
GAMMA_S = 1.15     # EN 1992-1-1 Table 2.1N
ALPHA_CT = 1.0     # EN 1992-1-1 3.1.6(2)P recommended value

# EN 1992-1-1 Table 3.1: fck -> fctk,0.05 (MPa). Only classes that have been checked are listed.
FCTK_005 = {"C25/30": 1.8, "C30/37": 2.0, "C35/45": 2.2, "C40/50": 2.5}


@dataclass(frozen=True)
class BondResult:
    fctd: float
    eta1: float
    eta2: float
    fbd: float


def fctd(concrete_class: str, fctk005: float | None = None) -> float:
    """Design tensile strength fctd = alpha_ct * fctk,0.05 / gamma_c   (EN 1992-1-1 eq. 3.16)."""
    if fctk005 is None:
        if concrete_class not in FCTK_005:
            raise KeyError(f"fctk,0.05 for {concrete_class} not tabulated here - supply it explicitly")
        fctk005 = FCTK_005[concrete_class]
    return ALPHA_CT * fctk005 / GAMMA_C


def bond_stress(concrete_class: str, good_bond: bool, phi: float, fctk005: float | None = None) -> BondResult:
    """fbd = 2.25 * eta1 * eta2 * fctd   (EN 1992-1-1 eq. 8.2)."""
    if phi <= 0:
        raise ValueError("bar diameter must be positive")
    eta1 = 1.0 if good_bond else 0.7
    eta2 = 1.0 if phi <= 32 else (132 - phi) / 100
    f = fctd(concrete_class, fctk005)
    return BondResult(fctd=f, eta1=eta1, eta2=eta2, fbd=2.25 * eta1 * eta2 * f)


def fyd(fyk: float) -> float:
    return fyk / GAMMA_S


def lb_rqd(phi: float, sigma_sd: float, fbd: float) -> float:
    """Basic required anchorage length lb,rqd = (phi/4) * sigma_sd / fbd   (EN 1992-1-1 eq. 8.3)."""
    if fbd <= 0:
        raise ValueError("fbd must be positive")
    return (phi / 4.0) * sigma_sd / fbd
