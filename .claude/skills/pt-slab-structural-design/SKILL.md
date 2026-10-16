---
name: pt-slab-structural-design
description: Produce complete post-tensioned (PT) floor slab structural drawing packages to Eurocode 2 (EN 1992-1-1) when a user supplies a draft floor layout. Triggers on PT slab, post-tension, tendon layout, drop panel, Eurocode flat slab design, or requests to generate full PT drawing sets from a sketch or draft plan.
---

# PT Slab Structural Design (Eurocode 2 Standard)

## Overview

Generate a complete, consistent set of construction drawings for post-tensioned flat slabs following the structure, detailing conventions, title-block style and sheet organisation of the reference 8F Hattha Bank package, but fully updated to **EN 1992-1-1 (Eurocode 2)** + relevant National Annex practice.

Always read the project design-basis YAML first (if present) and the company standards in `Structural-Drawing-Standards/`.

## When to Activate

- User provides a draft floor plan (columns, spans, openings, proposed thicknesses, drop panels).
- User asks for PT slab design, tendon layout, beam/drop-panel reinforcement, or full structural package.
- User says “follow the standard PT package” or “prepare drawings like the previous one”.

## Required Output Package (10 sheets, A3 landscape)

Always produce these sheets in this order and numbering scheme:

1. **Concrete Body Layout** – plan showing slab thicknesses (hatched), drop panels, beams, openings, sleeves, grid, overall dimensions.
2. **Beam Reinforcement Details** – cross-sections of all edge/internal beams with stirrups, main bars, clear cover, lap notes.
3. **Drop Panel Reinforcement Details 1** – plan + sections for type-1/2 drop panels + punching shear reinforcement call-outs.
4. **Drop Panel Reinforcement Details 2** – remaining drop-panel types.
5. **Drop Panel Reinforcement Details 3** – shear reinforcement details (links, stirrups around columns).
6. **Slab / Ring Reinforcement Details** – top & bottom mesh / bars, ring beams, typical sections, TF details.
7. **Tendon Layout Plan** – full plan with tendon IDs, number of strands, stressing ends, design notes block.
8–10. **Tendon Profile Details** – elevation profiles (A/B) for every tendon group with chainage and height from soffit to duct bottom.

## Eurocode 2 Material & Design Defaults (lock these unless user overrides or design-basis specifies otherwise)

**Concrete**
- Preferred class: C32/40 or C35/45 (cylinder/cube).
- Minimum for PT floors: C30/37.
- γ_c = 1.50, α_cc = 1.0 (or NA value).

**Reinforcement**
- Characteristic yield f_yk = 500 MPa (B500B / B500C).
- γ_s = 1.15 → f_yd = 435 MPa.
- Clear cover: calculate per EN 1992-1-1 §4.4 + exposure class (default XC1 internal → c_nom ≥ 15–20 mm + Δc_dev, but never less than bar diameter or 20 mm for PT ducts).

**Prestressing steel**
- 7-wire low-relaxation strand, Class 2 (EN 10138).
- Typical: 12.9 mm or 15.7 mm, f_pk = 1860 MPa, f_p0.1k ≈ 0.88–0.90 f_pk.
- Jacking stress limits: σ_p,max ≤ min(0.80 f_pk ; 0.90 f_p0.1k).
- After losses: use values consistent with EN 1992-1-1 §5.10.

**Friction & losses (default design parameters)**
- μ = 0.19 (bonded) or 0.06–0.12 (unbonded – confirm system).
- k = 0.001–0.005 /m (wobble).
- Anchorage set / draw-in: 6–8 mm typical.
- Long-term losses: creep, shrinkage, relaxation per EC2 Annexes.

**Load combinations**
- ULS / SLS per EN 1990 + EN 1991 (project-specific National Annex).
- Prestress secondary effects: include with factor 1.0 at SLS; favourable/unfavourable factors at ULS as per EC2.

**Punching shear**
- Follow EN 1992-1-1 §6.4.
- Always show additional punching reinforcement (links or studs) with clear call-out (“Additional punching shear reinforcement – see detail”).

## Drawing Conventions

- Follow company title-block, layers, text styles and annotation rules from `Structural-Drawing-Standards/`.
- Legend hatches: PT slab thicknesses, drop panels, beams, openings, sleeves.
- Beam labels: RB (rib/edge), BB (band beam).
- Tendon symbols: number of strands, stressing ends, fixed ends, profile height measured from slab soffit to underside of duct.
- Notes block on tendon layout sheet must include:
  - Design codes (EN 1992-1-1, EN 1990, EN 1991, EN 10138)
  - Material properties table
  - Strand properties
  - Friction parameters
  - Cover rules
  - Tendon symbol legend

## Workflow

1. **Receive draft** – extract spans, column positions, openings, proposed thicknesses, any client constraints.
2. **Check & rationalise** – verify span/depth ratios, drop-panel sizes for punching, beam depths, cover, minimum reinforcement.
3. **Select materials** – apply Eurocode defaults above (or values from design-basis YAML).
4. **Produce drawings** – generate the 10-sheet package following the exact sheet order and detailing style of the reference.
5. **Document assumptions** – list all NDPs, friction values, exposure class, fire resistance, and any departures from the standard package.
6. Flag any missing information as “TBC”. Never invent numerical results.

## Honesty rules (same as other skills in this repository)

- Never invent engineering values, clause references or PASS results.
- Mark unconfirmed values “TBC”.
- Distinguish calculated, assumed and user-entered values.
- Do not claim a drawing is “approved” or “ready for construction” — engineer sign-off is human.
