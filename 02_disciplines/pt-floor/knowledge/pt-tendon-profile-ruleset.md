# PT tendon modelling & profile geometry ruleset - guide

Status: **DRAFT, UNVERIFIED** (imported 24-OCT-2026). No rule is accepted until an engineer reviews it (gap G34).

The rules (IDs, text, parameters, basis, ADAPT profile code, review notes) are in [pt-tendon-profile-ruleset.yaml](pt-tendon-profile-ruleset.yaml). This page explains how to use them. The companion layout and shortening rules are in [pt-master-ruleset.md](pt-master-ruleset.md).

**Source:** the user's Google Doc "Post-Tensioned Tendon Modeling & Profile Geometry Ruleset" (Drive id `1HYU3WhCLvSN3-axo9bZHnPoClLUl_aQk5BirrEeuqxw`). It states that it follows EN 1992-1-1:2004, ADAPT-Builder modelling guidelines and PTI standards. Rule text and numbers were copied as written.

## Rule groups

| IDs | Topic |
|---|---|
| PT-PRF-01 | Principle: profile, balancing load, primary and hyperstatic moments |
| PT-PRF-02 to 08 | Profile shape: reversed parabola, partial parabola, cantilever up / down, harped, straight, extended reversed parabola |
| PT-PRF-09 to 11 | Control points: support high-point CGS, midspan low-point CGS, thickness and soffit steps |
| PT-PRF-12 to 14 | Minimum radius, friction and wobble (bonded / unbonded) |
| PT-PRF-15 to 16 | Checks triggered by the PT system type |

## Profile shape to ADAPT profile type

| Rule | Shape | Use | ADAPT code (INP legend) |
|---|---|---|---|
| PT-PRF-02 | Reversed parabola | Continuous spans (0.10 L inflection; low point 0.50 L interior, 0.40 L end bay) | 1 |
| PT-PRF-03 | Partial parabola | Banded tendons, flat top about 1.2 m over columns | 2 |
| PT-PRF-06 | Harped | Transfer beams, podium slabs, point loads | 3 |
| PT-PRF-04 | Cantilever up | Overhangs | 4 |
| PT-PRF-05 | Cantilever down | Upward tip reaction or heavy edge beam | 7 |
| PT-PRF-07 | Straight | Along shear walls and restrained edges | 8 |
| PT-PRF-08 | Extended reversed parabola | Very unequal adjacent spans | 9 |

The codes come from the legend in ADAPT's own `.INP` export. The 2F export writes 0 and 3 in that column, so the mapping must be confirmed by an import test before a generator relies on it.

## Using the system-type triggers

The PT basis `system.type` (bonded by default) selects the checks and the default friction range:

| `system.type` | Friction range (PT-PRF-13/14) | Checks triggered (PT-PRF-15/16) |
|---|---|---|
| bonded | mu 0.19-0.20, K 0.0033 rad/m | w_k <= 0.2 mm, frequent combination |
| unbonded | mu 0.05-0.07, K 0.0010-0.0014 rad/m | w_k <= 0.3 mm, quasi-permanent combination; M_Rd >= 1.15 M_cr (ACI-style) |

Friction values in a design always come from the PT system's ETA or supplier. These ranges only flag values that look wrong for the system type. For example, the 2F ADAPT model uses mu = 0.07, an unbonded value, while the drawing says bonded.

## Review findings (in the YAML review notes)

- **CGS "standard inputs" contradict their own formulas (PT-PRF-09, PT-PRF-10).** With EN 1992-1-1 cover, a top bar and half the duct height, the CGS ends up about 45-60 mm below the top, not 25-35 mm. Likewise cover plus half a duct already exceeds 30 mm at the soffit. Use the formulas with project values.
- **Clause reference (PT-PRF-13).** The source cites EN 1992-1-1 5.10.6 for friction. Friction losses are in 5.10.5.2.
- **Wobble value (PT-PRF-13).** As I recall, EN 1992-1-1 gives k of about 0.005-0.01 per metre for internal tendons, so 0.0033 rad/m needs checking against the code text.
- **Minimum radius 2.0 m (PT-PRF-12)** is software and practice guidance, not an EN value. The ETA or supplier minimum governs.
- **M_Rd >= 1.15 M_cr (PT-PRF-16)** is ACI-style, not an EN 1992-1-1 requirement.
- **Consistent with the master ruleset:** 0.10 L inflection (PT-LAY-11) and the 1.2 m flat top (PT-LAY-10).

## Rules that tools could apply later

Most of these rules can be applied by tools: shape selection, control-point formulas, minimum-radius check, friction plausibility for the system type, and choosing which checks run. That makes them direct inputs to a future `.INP` / SAFE model builder and to a pre-import model validator. As with the master ruleset, tools would only suggest and flag; values come from the project data, and the engineer confirms.
